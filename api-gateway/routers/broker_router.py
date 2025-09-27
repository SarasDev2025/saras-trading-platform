"""Broker management router - manage persisted broker connections per user."""
import logging
from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from brokers import broker_manager, get_supported_brokers, health_check_all
from config.database import get_db
from models import UserBrokerConnection
from services.broker_connection_service import BrokerConnectionService
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class BrokerConnectionCreateRequest(BaseModel):
    alias: str = Field(..., min_length=2, max_length=50)
    broker_type: str
    api_key: str
    api_secret: str
    paper_trading: bool = True
    metadata: Optional[Dict[str, str]] = None


class BrokerConnectionResponse(BaseModel):
    id: str
    alias: str
    broker_type: str
    paper_trading: bool
    status: str
    created_at: str
    updated_at: str


def _serialize_connection(connection: UserBrokerConnection) -> BrokerConnectionResponse:
    return BrokerConnectionResponse(
        id=str(connection.id),
        alias=connection.alias,
        broker_type=connection.broker_type,
        paper_trading=connection.paper_trading,
        status=connection.status,
        created_at=connection.created_at.isoformat() if connection.created_at else "",
        updated_at=connection.updated_at.isoformat() if connection.updated_at else "",
    )


@router.get("/supported", response_model=List[str])
async def get_supported_broker_types():
    """Return list of supported brokers."""
    return get_supported_brokers()


@router.get("/connections", response_model=List[BrokerConnectionResponse])
async def list_connections(
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    connections = await BrokerConnectionService.list_connections(db, current_user["id"])
    return [_serialize_connection(conn) for conn in connections]


@router.post("/connections", response_model=BrokerConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    request: BrokerConnectionCreateRequest,
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    existing = await BrokerConnectionService.get_connection_by_alias(db, current_user["id"], request.alias)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Broker connection alias '{request.alias}' already exists"
        )

    connection = UserBrokerConnection(
        user_id=BrokerConnectionService._normalize_uuid(current_user["id"]),
        broker_type=request.broker_type,
        alias=request.alias,
        api_key=request.api_key,
        api_secret=request.api_secret,
        credentials={"api_key": request.api_key, "api_secret": request.api_secret},
        paper_trading=request.paper_trading,
        status="active",
        connection_metadata=request.metadata or {}
    )

    db.add(connection)
    await db.flush()

    # Ensure the broker session can be established; raises HTTPException on failure
    await BrokerConnectionService.ensure_broker_session(connection)

    await db.commit()
    await db.refresh(connection)

    return _serialize_connection(connection)


@router.delete("/connections/{alias}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    alias: str,
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    connection = await BrokerConnectionService.require_active_connection(db, current_user["id"], alias)

    connection_name = BrokerConnectionService.connection_name(connection)
    if broker_manager.get_broker(connection_name):
        await broker_manager.remove_broker(connection_name)

    await db.delete(connection)
    await db.commit()
    return None


@router.get("/connections/{alias}", response_model=BrokerConnectionResponse)
async def get_connection(
    alias: str,
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    connection = await BrokerConnectionService.require_active_connection(db, current_user["id"], alias)
    return _serialize_connection(connection)


@router.get("/connections/{alias}/refresh")
async def refresh_connection_status(
    alias: str,
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    connection = await BrokerConnectionService.require_active_connection(db, current_user["id"], alias)
    broker, connection_name = await BrokerConnectionService.ensure_broker_session(connection)
    health = await broker.health_check()

    return {
        "connection": _serialize_connection(connection),
        "health": health
    }


@router.get("/health")
async def check_all_broker_health():
    """Health check for all active brokers in memory."""
    health_status = await health_check_all()
    return {
        "healthy_brokers": sum(1 for status in health_status.values() if status),
        "total_brokers": len(health_status),
        "details": health_status
    }


@router.get("/active")
async def list_active_brokers():
    """List active broker sessions for debugging."""
    active_brokers = broker_manager.list_brokers()
    return {
        "active_brokers": active_brokers,
        "count": len(active_brokers)
    }
