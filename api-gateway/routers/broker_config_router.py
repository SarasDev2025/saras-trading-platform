"""
Broker Configuration Router
Provides broker settings based on user region and trading mode
"""
from typing import Annotated, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from config.database import get_db
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

router = APIRouter(prefix="/broker-config", tags=["broker-configuration"])


class BrokerConfig(BaseModel):
    """Broker configuration response model"""
    broker_name: str
    display_name: str
    description: str | None
    api_url: str
    region: str
    trading_mode: str


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Any | None = None
    message: str | None = None
    error: str | None = None


@router.get("/current", response_model=APIResponse)
async def get_current_broker_config(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get broker configuration for current user based on their region and trading mode

    Returns the appropriate broker configuration matching:
    - User's region (from users.region)
    - User's current trading mode (from users.trading_mode)
    """
    try:
        user_id = current_user["id"]

        # Get user's region and trading mode
        user_query = text("""
            SELECT region, trading_mode
            FROM users
            WHERE id = :user_id
        """)
        user_result = await db.execute(user_query, {"user_id": user_id})
        user_data = user_result.first()

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_region = user_data.region
        user_mode = user_data.trading_mode

        # Get matching broker configuration
        config_query = text("""
            SELECT
                broker_name,
                display_name,
                description,
                api_url,
                region,
                trading_mode
            FROM broker_configurations
            WHERE region = :region
              AND trading_mode = :trading_mode
              AND is_active = true
            ORDER BY sort_order
            LIMIT 1
        """)

        config_result = await db.execute(
            config_query,
            {"region": user_region, "trading_mode": user_mode}
        )
        config = config_result.first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No broker configuration found for region {user_region} and mode {user_mode}"
            )

        broker_config = BrokerConfig(
            broker_name=config.broker_name,
            display_name=config.display_name,
            description=config.description,
            api_url=config.api_url,
            region=config.region,
            trading_mode=config.trading_mode
        )

        return APIResponse(success=True, data=broker_config.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch broker configuration: {str(e)}"
        )


@router.get("/by-region/{region}", response_model=APIResponse)
async def get_broker_configs_by_region(
    region: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available broker configurations for a specific region
    Useful for displaying options or admin purposes
    """
    try:
        if region not in ['IN', 'US', 'GB']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid region: {region}. Must be one of: IN, US, GB"
            )

        query = text("""
            SELECT
                broker_name,
                display_name,
                description,
                api_url,
                region,
                trading_mode
            FROM broker_configurations
            WHERE region = :region
              AND is_active = true
            ORDER BY sort_order, trading_mode
        """)

        result = await db.execute(query, {"region": region})
        configs = []

        for row in result:
            configs.append({
                "broker_name": row.broker_name,
                "display_name": row.display_name,
                "description": row.description,
                "api_url": row.api_url,
                "region": row.region,
                "trading_mode": row.trading_mode
            })

        return APIResponse(success=True, data=configs)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch broker configurations: {str(e)}"
        )
