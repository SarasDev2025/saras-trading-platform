# routers/rebalancing_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from config.database import get_db
#from auth_router import get_current_user_id  # Your auth dependency
from models import APIResponse
from models.rebalancing_models import (
    RebalancingRequest,
    RebalancingResponse,
    ApplyRebalancingRequest,
    ApplyRebalancingResult,
    RebalancingStrategy,
    PortfolioComposition
)
from services.rebalancing_service import RebalancingService
from services.rebalancing_db_service import RebalancingDBService

router = APIRouter(prefix="/smallcases", tags=["Rebalancing"])


def get_current_user_id() -> str:
    """Get current user ID - returns demo user for now"""
    return "12345678-1234-1234-1234-123456789012"

@router.get("/{smallcase_id}/composition", response_model=APIResponse)
async def get_smallcase_composition(
    smallcase_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user_id=Depends(get_current_user_id)
):
    """Get smallcase composition with market data for modification/rebalancing"""
    try:
        composition = await RebalancingDBService.get_smallcase_composition(
            db, smallcase_id
        )
        
        return APIResponse(
            success=True,
            data=composition
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )

@router.post("/{smallcase_id}/rebalance/apply", response_model=APIResponse)
async def apply_rebalancing_suggestions(
    smallcase_id: str,
    apply_request: ApplyRebalancingRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_id)
):
    """Apply rebalancing suggestions to smallcase portfolio"""
    try:
        # Optional: Verify user has access to modify this smallcase
        has_access = await RebalancingDBService.verify_user_access_to_smallcase(
            db, smallcase_id, str(current_user.id)
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this smallcase"
            )
        
        # Apply the rebalancing changes to database
        result = await RebalancingDBService.apply_rebalancing_to_database(
            db, smallcase_id, apply_request.suggestions
        )
        
        # Optional: Log the rebalancing activity for audit
        await RebalancingDBService.log_rebalancing_activity(
            db=db,
            smallcase_id=smallcase_id,
            user_id=str(current_user.id),
            strategy="user_applied",  # Could extract from request
            changes_applied=result["total_changes"]
        )
        
        return APIResponse(
            success=True,
            data=result,
            message=f"Successfully rebalanced {result['total_changes']} stocks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply rebalancing: {str(e)}"
        )

@router.get("/rebalancing/strategies", response_model=APIResponse)
async def get_available_rebalancing_strategies():
    """Get list of available rebalancing strategies with descriptions"""
    try:
        strategies = RebalancingService.get_available_strategies()
        
        return APIResponse(
            success=True,
            data=strategies,
            message=f"Retrieved {len(strategies)} available strategies"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch strategies: {str(e)}"
        )

@router.post("/{smallcase_id}/rebalance/suggestions", response_model=APIResponse)
async def generate_rebalancing_suggestions(
    smallcase_id: str,
    request_data: RebalancingRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_id)
):
    """Generate AI-powered rebalancing suggestions based on selected strategy"""
    try:
        # Get current composition
        composition = await RebalancingDBService.get_smallcase_composition(
            db, smallcase_id
        )
        
        # Generate suggestions using the selected strategy
        rebalancing_result = RebalancingService.generate_rebalancing_suggestions(
            stocks=composition["stocks"],
            strategy=request_data.strategy
        )
        
        # Combine with composition data
        rebalancing_data = {
            "smallcase_id": smallcase_id,
            "current_composition": composition,
            **rebalancing_result
        }
        
        return APIResponse(
            success=True,
            data=rebalancing_data,
            message=f"Generated {len(rebalancing_result['suggestions'])} rebalancing suggestions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTP