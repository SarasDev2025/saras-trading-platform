"""
Broker Selection Service for Multi-User Investment System
Handles broker selection based on user location, regulatory requirements, and preferences
"""

import uuid
from typing import Dict, Any, Optional, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class BrokerSelectionService:
    """Service for intelligent broker selection based on user location and other factors"""

    # Broker configuration by region
    REGIONAL_BROKERS = {
        "IN": {  # India
            "primary": "zerodha",
            "secondary": "upstox",
            "exchanges": ["NSE", "BSE"],
            "supported_assets": ["stocks", "etfs", "mutual_funds"]
        },
        "US": {  # United States
            "primary": "alpaca",
            "secondary": "interactive_brokers",
            "exchanges": ["NASDAQ", "NYSE", "AMEX"],
            "supported_assets": ["stocks", "etfs", "options", "crypto"]
        },
        "GB": {  # United Kingdom
            "primary": "interactive_brokers",
            "secondary": "trading212",
            "exchanges": ["LSE", "AIM"],
            "supported_assets": ["stocks", "etfs", "forex"]
        },
        # Default fallback
        "DEFAULT": {
            "primary": "alpaca",
            "secondary": "interactive_brokers",
            "exchanges": ["NASDAQ", "NYSE"],
            "supported_assets": ["stocks", "etfs"]
        }
    }

    @staticmethod
    async def get_user_broker_preference(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user's broker preference and location information"""
        try:
            # Check if user has existing broker connections
            broker_result = await db.execute(text("""
                SELECT
                    ubc.broker_type,
                    ubc.status,
                    ubc.paper_trading,
                    ubc.created_at
                FROM user_broker_connections ubc
                WHERE ubc.user_id = :user_id
                AND ubc.status = 'active'
                ORDER BY ubc.created_at DESC
                LIMIT 1
            """), {"user_id": user_id})

            existing_broker = broker_result.fetchone()

            # Get user location information (if available)
            # For now, we'll use a simple approach and enhance later
            user_result = await db.execute(text("""
                SELECT email, created_at
                FROM users
                WHERE id = :user_id
            """), {"user_id": user_id})

            user_row = user_result.fetchone()
            if not user_row:
                raise ValueError(f"User {user_id} not found")

            # Determine user's likely region based on email domain (simplified)
            user_email = user_row[0]
            detected_region = BrokerSelectionService._detect_region_from_email(user_email)

            return {
                "user_id": user_id,
                "detected_region": detected_region,
                "existing_broker": {
                    "broker_type": existing_broker[0] if existing_broker else None,
                    "status": existing_broker[1] if existing_broker else None,
                    "paper_trading": existing_broker[2] if existing_broker else None,
                    "is_active": existing_broker[1] == 'active' if existing_broker else False
                } if existing_broker else None,
                "regional_config": BrokerSelectionService.REGIONAL_BROKERS.get(
                    detected_region,
                    BrokerSelectionService.REGIONAL_BROKERS["DEFAULT"]
                )
            }

        except Exception as e:
            logger.error(f"Failed to get user broker preference: {str(e)}")
            # Return default configuration
            return {
                "user_id": user_id,
                "detected_region": "DEFAULT",
                "existing_broker": None,
                "regional_config": BrokerSelectionService.REGIONAL_BROKERS["DEFAULT"]
            }

    @staticmethod
    def _detect_region_from_email(email: str) -> str:
        """Detect user's region based on email domain (simplified approach)"""
        email_lower = email.lower()

        # Common Indian email domains and patterns
        indian_domains = ['.in', 'rediffmail', 'yahoo.in', 'gmail.com']
        indian_keywords = ['india', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai']

        # Common US domains
        us_domains = ['.com', '.org', '.net', 'yahoo.com', 'hotmail.com', 'outlook.com']

        # Common UK domains
        uk_domains = ['.uk', '.co.uk', 'btinternet.com']

        # Check for explicit Indian indicators
        if any(domain in email_lower for domain in indian_domains):
            return "IN"

        if any(keyword in email_lower for keyword in indian_keywords):
            return "IN"

        # Check for UK indicators
        if any(domain in email_lower for domain in uk_domains):
            return "GB"

        # Default to US for .com domains and others
        return "US"

    @staticmethod
    async def select_optimal_broker(
        db: AsyncSession,
        user_id: str,
        asset_symbols: List[str],
        investment_amount: float
    ) -> Dict[str, Any]:
        """Select the optimal broker for a user's investment"""
        try:
            # Get user broker preferences
            user_prefs = await BrokerSelectionService.get_user_broker_preference(db, user_id)

            # If user has an existing active broker connection, prefer it
            if user_prefs["existing_broker"] and user_prefs["existing_broker"]["is_active"]:
                selected_broker = user_prefs["existing_broker"]["broker_type"]
                selection_reason = "existing_connection"
            else:
                # Select based on regional preferences
                regional_config = user_prefs["regional_config"]
                selected_broker = regional_config["primary"]
                selection_reason = "regional_primary"

            # Validate broker supports the assets
            supported_assets = user_prefs["regional_config"]["supported_assets"]

            # For now, assume all assets are stocks (can be enhanced)
            asset_type_supported = "stocks" in supported_assets

            if not asset_type_supported:
                # Fall back to secondary broker
                selected_broker = user_prefs["regional_config"]["secondary"]
                selection_reason = "regional_secondary"

            return {
                "selected_broker": selected_broker,
                "region": user_prefs["detected_region"],
                "selection_reason": selection_reason,
                "supported_exchanges": user_prefs["regional_config"]["exchanges"],
                "broker_config": user_prefs["regional_config"],
                "needs_connection": not (user_prefs["existing_broker"] and
                                       user_prefs["existing_broker"]["is_active"] and
                                       user_prefs["existing_broker"]["broker_type"] == selected_broker)
            }

        except Exception as e:
            logger.error(f"Failed to select optimal broker: {str(e)}")
            # Return safe default
            return {
                "selected_broker": "alpaca",
                "region": "US",
                "selection_reason": "fallback_default",
                "supported_exchanges": ["NASDAQ", "NYSE"],
                "broker_config": BrokerSelectionService.REGIONAL_BROKERS["DEFAULT"],
                "needs_connection": True
            }

    @staticmethod
    async def ensure_broker_connection(
        db: AsyncSession,
        user_id: str,
        broker_name: str
    ) -> Dict[str, Any]:
        """Ensure user has an active broker connection, create if necessary"""
        try:
            # Check existing connection
            existing_result = await db.execute(text("""
                SELECT id, status, paper_trading
                FROM user_broker_connections
                WHERE user_id = :user_id AND broker_type = :broker_name
            """), {"user_id": user_id, "broker_name": broker_name})

            existing = existing_result.fetchone()

            if existing and existing[1] == 'active':  # status = 'active'
                return {
                    "connection_id": str(existing[0]),
                    "status": "existing",
                    "broker_name": broker_name,
                    "account_status": "paper_trading" if existing[2] else "live"
                }

            # Create new connection (simplified - in real implementation would handle broker API keys)
            connection_id = str(uuid.uuid4())

            if existing:
                # Update existing inactive connection
                await db.execute(text("""
                    UPDATE user_broker_connections
                    SET status = 'active', paper_trading = true, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :connection_id
                """), {"connection_id": existing[0]})
                connection_id = str(existing[0])
                status = "reactivated"
            else:
                # Create new connection
                await db.execute(text("""
                    INSERT INTO user_broker_connections
                    (id, user_id, broker_type, alias, status, paper_trading, created_at)
                    VALUES (:id, :user_id, :broker_name, :alias, 'active', true, CURRENT_TIMESTAMP)
                """), {
                    "id": connection_id,
                    "user_id": user_id,
                    "broker_name": broker_name,
                    "alias": f"{broker_name}_primary"
                })
                status = "created"

            await db.commit()

            return {
                "connection_id": connection_id,
                "status": status,
                "broker_name": broker_name,
                "account_status": "paper_trading"
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to ensure broker connection: {str(e)}")
            raise

    @staticmethod
    async def get_broker_capabilities(broker_name: str) -> Dict[str, Any]:
        """Get capabilities and features of a specific broker"""
        broker_capabilities = {
            "zerodha": {
                "supports_fractional_shares": False,
                "min_order_value": 1.0,
                "max_order_value": 1000000.0,
                "supported_order_types": ["market", "limit", "stop_loss"],
                "trading_hours": {"start": "09:15", "end": "15:30"},
                "commission_structure": "per_trade",
                "supports_drip": True,
                "dividend_reinvestment": True
            },
            "alpaca": {
                "supports_fractional_shares": True,
                "min_order_value": 1.0,
                "max_order_value": 10000000.0,
                "supported_order_types": ["market", "limit", "stop", "stop_limit"],
                "trading_hours": {"start": "09:30", "end": "16:00"},
                "commission_structure": "commission_free",
                "supports_drip": True,
                "dividend_reinvestment": True
            },
            "interactive_brokers": {
                "supports_fractional_shares": True,
                "min_order_value": 1.0,
                "max_order_value": 50000000.0,
                "supported_order_types": ["market", "limit", "stop", "stop_limit", "trailing_stop"],
                "trading_hours": {"start": "09:30", "end": "16:00"},
                "commission_structure": "per_share",
                "supports_drip": True,
                "dividend_reinvestment": True
            }
        }

        return broker_capabilities.get(broker_name, {
            "supports_fractional_shares": False,
            "min_order_value": 1.0,
            "max_order_value": 100000.0,
            "supported_order_types": ["market", "limit"],
            "trading_hours": {"start": "09:30", "end": "16:00"},
            "commission_structure": "unknown",
            "supports_drip": False,
            "dividend_reinvestment": False
        })