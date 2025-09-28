"""
Dividend Scheduler Management Router
API endpoints for controlling and monitoring the dividend aggregation scheduler
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Annotated
import logging

# Import enhanced auth dependencies
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

from config.database import get_db
from models import APIResponse
from services.dividend_scheduler import get_dividend_scheduler, initialize_dividend_scheduler

router = APIRouter(tags=["dividend-scheduler"], prefix="/dividends/scheduler")
logger = logging.getLogger(__name__)


@router.get("/status", response_model=APIResponse)
async def get_scheduler_status(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get current dividend scheduler status and statistics"""
    try:
        scheduler = await get_dividend_scheduler()
        status = await scheduler.get_scheduler_status(db)

        return APIResponse(
            success=True,
            data=status,
            message="Dividend scheduler status retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/start", response_model=APIResponse)
async def start_scheduler(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Start the dividend scheduler (admin only)"""
    try:
        # In a real implementation, check for admin privileges
        # For now, allow any authenticated user

        scheduler = await get_dividend_scheduler()
        await scheduler.start()

        return APIResponse(
            success=True,
            data={"status": "started"},
            message="Dividend scheduler started successfully"
        )

    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/stop", response_model=APIResponse)
async def stop_scheduler(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Stop the dividend scheduler (admin only)"""
    try:
        # In a real implementation, check for admin privileges
        # For now, allow any authenticated user

        scheduler = await get_dividend_scheduler()
        await scheduler.stop()

        return APIResponse(
            success=True,
            data={"status": "stopped"},
            message="Dividend scheduler stopped successfully"
        )

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@router.post("/process-upcoming", response_model=APIResponse)
async def process_upcoming_dividends(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger processing of upcoming dividend events"""
    try:
        scheduler = await get_dividend_scheduler()
        await scheduler._process_upcoming_dividends(db)

        return APIResponse(
            success=True,
            data={"status": "processed"},
            message="Upcoming dividends processed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to process upcoming dividends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process upcoming dividends: {str(e)}")


@router.post("/process-drip", response_model=APIResponse)
async def process_pending_drip(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger processing of pending DRIP transactions"""
    try:
        scheduler = await get_dividend_scheduler()
        await scheduler._process_pending_drip_transactions(db)

        return APIResponse(
            success=True,
            data={"status": "processed"},
            message="Pending DRIP transactions processed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to process DRIP transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process DRIP transactions: {str(e)}")


@router.post("/execute-orders", response_model=APIResponse)
async def execute_ready_orders(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger execution of ready bulk orders"""
    try:
        scheduler = await get_dividend_scheduler()
        await scheduler._execute_ready_bulk_orders(db)

        return APIResponse(
            success=True,
            data={"status": "executed"},
            message="Ready bulk orders executed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to execute bulk orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute bulk orders: {str(e)}")


@router.get("/health", response_model=APIResponse)
async def scheduler_health_check(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
):
    """Health check for the dividend scheduler"""
    try:
        scheduler = await get_dividend_scheduler()

        health_status = {
            "scheduler_running": scheduler.is_running,
            "active_tasks": len(scheduler.processing_tasks),
            "check_interval": scheduler.check_interval,
            "health": "healthy" if scheduler.is_running else "stopped"
        }

        return APIResponse(
            success=True,
            data=health_status,
            message="Scheduler health check completed"
        )

    except RuntimeError as e:
        # Scheduler not initialized
        return APIResponse(
            success=False,
            data={"health": "not_initialized", "error": str(e)},
            message="Dividend scheduler not initialized"
        )
    except Exception as e:
        logger.error(f"Scheduler health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")