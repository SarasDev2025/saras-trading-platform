"""
Broker management router - Connect and manage multiple brokers
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from brokers import (
    broker_manager, BrokerType, create_broker, get_supported_brokers,
    quick_connect, quick_disconnect, get_broker_status, health_check_all
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response models
class BrokerConnectionRequest(BaseModel):
    broker_type: str
    api_key: str
    secret_key: str
    paper_trading: bool = True
    broker_name: Optional[str] = None

class BrokerConnectionResponse(BaseModel):
    success: bool
    message: str
    broker_name: Optional[str] = None

class BrokerStatusResponse(BaseModel):
    broker_name: str
    status: str
    authenticated: bool
    paper_trading: bool
    broker_type: str

@router.get("/supported", response_model=List[str])
async def get_supported_broker_types():
    """Get list of supported broker types"""
    return get_supported_brokers()

@router.post("/connect", response_model=BrokerConnectionResponse)
async def connect_broker(request: BrokerConnectionRequest, user_id: str = "default_user"):
    """Connect to a broker"""
    try:
        success = await quick_connect(
            broker_type=request.broker_type,
            api_key=request.api_key,
            secret=request.secret_key,
            user_id=user_id,
            broker_name=request.broker_name,
            paper_trading=request.paper_trading
        )
        
        if success:
            broker_name = f"{user_id}_{request.broker_name or request.broker_type}"
            return BrokerConnectionResponse(
                success=True,
                message=f"Successfully connected to {request.broker_type}",
                broker_name=broker_name
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to {request.broker_type}"
            )
    except Exception as e:
        logger.error(f"Error connecting broker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/disconnect/{broker_name}")
async def disconnect_broker(broker_name: str, user_id: str = "default_user"):
    """Disconnect from a broker"""
    try:
        success = await quick_disconnect(user_id=user_id, broker_name=broker_name)
        
        if success:
            return {"success": True, "message": f"Disconnected from {broker_name}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Broker {broker_name} not found"
            )
    except Exception as e:
        logger.error(f"Error disconnecting broker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/status")
async def get_all_broker_status(user_id: str = "default_user"):
    """Get status of all user's brokers"""
    try:
        status_info = get_broker_status(user_id)
        return status_info
    except Exception as e:
        logger.error(f"Error getting broker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/status/{broker_name}")
async def get_specific_broker_status(broker_name: str, user_id: str = "default_user"):
    """Get status of a specific broker"""
    try:
        status_info = get_broker_status(user_id, broker_name)
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=status_info["error"]
            )
        return status_info
    except Exception as e:
        logger.error(f"Error getting broker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/health")
async def check_all_broker_health():
    """Health check for all active brokers"""
    try:
        health_status = await health_check_all()
        return {
            "healthy_brokers": sum(1 for status in health_status.values() if status),
            "total_brokers": len(health_status),
            "details": health_status
        }
    except Exception as e:
        logger.error(f"Error checking broker health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/list")
async def list_active_brokers():
    """List all active broker connections"""
    try:
        active_brokers = broker_manager.list_brokers()
        return {
            "active_brokers": active_brokers,
            "count": len(active_brokers)
        }
    except Exception as e:
        logger.error(f"Error listing brokers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
