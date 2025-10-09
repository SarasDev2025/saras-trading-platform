"""Service utilities for managing user broker connections and runtime sessions."""
from __future__ import annotations

import os
import uuid
import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from brokers import BaseBroker, BrokerFactory, BrokerType, broker_manager
from models import UserBrokerConnection

logger = logging.getLogger(__name__)


class BrokerConnectionService:
    """High-level helper for user broker connections."""

    @staticmethod
    def _normalize_uuid(value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid identifier supplied") from exc

    @staticmethod
    def connection_name(connection: UserBrokerConnection) -> str:
        """Build the key used for broker_manager storage."""
        return f"{connection.user_id}_{connection.alias}"

    @staticmethod
    async def get_connection_by_alias(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        alias: str
    ) -> Optional[UserBrokerConnection]:
        user_uuid = BrokerConnectionService._normalize_uuid(user_id)

        result = await db.execute(
            select(UserBrokerConnection).where(
                UserBrokerConnection.user_id == user_uuid,
                UserBrokerConnection.alias == alias
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_connections(
        db: AsyncSession,
        user_id: uuid.UUID | str
    ) -> List[UserBrokerConnection]:
        user_uuid = BrokerConnectionService._normalize_uuid(user_id)

        result = await db.execute(
            select(UserBrokerConnection).where(UserBrokerConnection.user_id == user_uuid)
        )
        return list(result.scalars().all())

    @staticmethod
    def _extract_credentials(connection: UserBrokerConnection) -> Tuple[Optional[str], Optional[str]]:
        """Extract credentials from connection or fallback to environment variables."""
        # Try database credentials first
        if connection.api_key and connection.api_secret:
            logger.info(f"Using database credentials for {connection.broker_type}")
            return connection.api_key, connection.api_secret

        credentials = connection.credentials or {}
        db_key = credentials.get("api_key")
        db_secret = credentials.get("api_secret")

        if db_key and db_secret:
            logger.info(f"Using credentials from JSONB for {connection.broker_type}")
            return db_key, db_secret

        # Fallback to environment variables (development mode)
        broker_type = connection.broker_type.upper()
        mode_suffix = "" if connection.paper_trading else "_LIVE"

        env_key_name = f"{broker_type}_API_KEY{mode_suffix}"
        env_secret_name = f"{broker_type}_SECRET_KEY{mode_suffix}"

        env_key = os.getenv(env_key_name)
        env_secret = os.getenv(env_secret_name)

        if env_key and env_secret:
            logger.info(f"Using environment credentials for {connection.broker_type} (paper={connection.paper_trading})")
            logger.info(f"Loaded from env: {env_key_name}, {env_secret_name}")
            return env_key, env_secret

        logger.warning(f"No credentials found for {connection.broker_type} (paper={connection.paper_trading})")
        return None, None

    @staticmethod
    async def ensure_broker_session(
        connection: UserBrokerConnection
    ) -> Tuple[BaseBroker, str]:
        """Ensure there is an authenticated broker instance for this connection."""
        connection_key = BrokerConnectionService.connection_name(connection)
        broker = broker_manager.get_broker(connection_key)
        if broker:
            return broker, connection_key

        api_key, api_secret = BrokerConnectionService._extract_credentials(connection)
        if not api_key or not api_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Broker credentials are not configured for this connection"
            )

        try:
            broker_type = BrokerType(connection.broker_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported broker type '{connection.broker_type}'"
            ) from exc

        broker_instance = BrokerFactory.create_broker(
            broker_type,
            api_key,
            api_secret,
            connection.paper_trading
        )

        success = await broker_manager.add_broker(connection_key, broker_instance)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate with broker"
            )

        return broker_instance, connection_key

    @staticmethod
    async def require_active_connection(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        alias: str
    ) -> UserBrokerConnection:
        connection = await BrokerConnectionService.get_connection_by_alias(db, user_id, alias)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Broker connection '{alias}' not found"
            )

        if connection.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Broker connection '{alias}' is not active"
            )

        return connection

    @staticmethod
    async def get_connection_for_user_trading_mode(
        db: AsyncSession,
        user_id: uuid.UUID | str
    ) -> Optional[UserBrokerConnection]:
        """
        Get active broker connection matching user's current trading mode.
        Returns connection where paper_trading flag matches user's trading_mode.
        """
        user_uuid = BrokerConnectionService._normalize_uuid(user_id)

        # Get user's current trading mode
        user_result = await db.execute(
            text("SELECT trading_mode FROM users WHERE id = :user_id"),
            {"user_id": str(user_uuid)}
        )
        user_mode = user_result.scalar_one_or_none()

        if not user_mode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Determine required paper_trading flag based on user's mode
        requires_paper = (user_mode == 'paper')

        # Get matching broker connection
        result = await db.execute(
            select(UserBrokerConnection).where(
                UserBrokerConnection.user_id == user_uuid,
                UserBrokerConnection.paper_trading == requires_paper,
                UserBrokerConnection.status == 'active'
            ).limit(1)
        )

        return result.scalar_one_or_none()
