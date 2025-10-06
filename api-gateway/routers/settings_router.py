"""
Settings router - User settings management including trading mode
"""
import logging
from typing import Annotated, Dict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from config.database import get_db
from models import User
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class TradingModeUpdateRequest(BaseModel):
    trading_mode: str = Field(..., pattern="^(paper|live)$")


class TradingModeUpdateResponse(BaseModel):
    success: bool
    trading_mode: str
    message: str


class UserSettingsResponse(BaseModel):
    trading_mode: str
    region: str
    email_verified: bool
    kyc_status: str


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get current user settings"""
    try:
        result = await db.execute(
            select(User).where(User.id == current_user["id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserSettingsResponse(
            trading_mode=user.trading_mode,
            region=user.region,
            email_verified=user.email_verified,
            kyc_status=user.kyc_status
        )

    except Exception as e:
        logger.error(f"Error fetching user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user settings"
        )


@router.patch("/settings/trading-mode", response_model=TradingModeUpdateResponse)
async def update_trading_mode(
    request: TradingModeUpdateRequest,
    current_user: Annotated[Dict[str, str], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's trading mode (paper or live)

    When switching modes:
    - Paper mode: Uses virtual money, simulated trades, no real broker connections
    - Live mode: Uses real money, actual trades through broker APIs

    This will affect which portfolios and data are shown in the UI.
    """
    try:
        new_mode = request.trading_mode.lower()

        # Validate mode
        if new_mode not in ['paper', 'live']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid trading mode. Must be 'paper' or 'live'"
            )

        # Update user's trading mode
        result = await db.execute(
            update(User)
            .where(User.id == current_user["id"])
            .values(
                trading_mode=new_mode,
                updated_at=datetime.now(timezone.utc)
            )
            .returning(User.trading_mode)
        )

        updated_mode = result.scalar_one_or_none()

        if not updated_mode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await db.commit()

        mode_name = "Paper Trading" if new_mode == "paper" else "Live Trading"

        logger.info(
            f"User {current_user['id']} switched to {mode_name} mode"
        )

        return TradingModeUpdateResponse(
            success=True,
            trading_mode=new_mode,
            message=f"Trading mode updated to {mode_name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating trading mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trading mode"
        )
