"""
Order Monitoring API Router
Endpoints for order queuing, status checking, and next-day monitoring
"""

from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database import get_db
from ..services.order_monitoring_service import OrderMonitoringService
from ..auth.middleware import get_current_user
from ..models.user import User

router = APIRouter(prefix="/orders/monitoring", tags=["Order Monitoring"])


class QueueOrderRequest(BaseModel):
    broker_connection_id: str
    order_id: str
    symbol: str
    order_type: str
    quantity: float
    expected_execution_date: datetime


class CheckOrdersRequest(BaseModel):
    check_date: Optional[date] = None


@router.post("/queue")
async def queue_order_for_monitoring(
    request: QueueOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Queue an order for next-day execution monitoring"""
    try:
        result = await OrderMonitoringService.queue_order_for_monitoring(
            db=db,
            broker_connection_id=request.broker_connection_id,
            order_id=request.order_id,
            symbol=request.symbol,
            order_type=request.order_type,
            quantity=request.quantity,
            expected_execution_date=request.expected_execution_date
        )

        return {
            "success": True,
            "data": result,
            "message": "Order queued for monitoring successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue order for monitoring: {str(e)}"
        )


@router.post("/check")
async def check_pending_orders(
    request: CheckOrdersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check execution status of pending orders for a specific date"""
    try:
        check_date = request.check_date or datetime.utcnow().date()

        result = await OrderMonitoringService.check_pending_orders(
            db=db,
            check_date=datetime.combine(check_date, datetime.min.time())
        )

        return {
            "success": True,
            "data": result,
            "message": f"Order status check completed for {check_date}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check pending orders: {str(e)}"
        )


@router.get("/history")
async def get_monitoring_history(
    days: int = 30,
    broker_connection_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order monitoring history for the past N days"""
    try:
        if days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request more than 365 days of history"
            )

        history = await OrderMonitoringService.get_monitoring_history(
            db=db,
            days=days,
            broker_connection_id=broker_connection_id
        )

        return {
            "success": True,
            "data": {
                "history": history,
                "days": days,
                "total_records": len(history)
            },
            "message": f"Retrieved {len(history)} monitoring records"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring history: {str(e)}"
        )


@router.get("/attention")
async def get_orders_needing_attention(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get orders that need attention (cancelled, rejected, or partially filled)"""
    try:
        attention_orders = await OrderMonitoringService.get_orders_needing_attention(db)

        return {
            "success": True,
            "data": {
                "orders": attention_orders,
                "total_count": len(attention_orders)
            },
            "message": f"Found {len(attention_orders)} orders needing attention"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders needing attention: {str(e)}"
        )


@router.get("/today")
async def check_todays_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick check of today's pending orders"""
    try:
        today = datetime.utcnow().date()

        result = await OrderMonitoringService.check_pending_orders(
            db=db,
            check_date=datetime.combine(today, datetime.min.time())
        )

        return {
            "success": True,
            "data": result,
            "message": f"Today's order status check completed"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check today's orders: {str(e)}"
        )


@router.get("/summary")
async def get_monitoring_summary(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a summary of order monitoring for the past N days"""
    try:
        history = await OrderMonitoringService.get_monitoring_history(
            db=db,
            days=days
        )

        # Calculate summary statistics
        total_orders = len(history)
        filled_orders = len([h for h in history if h["status"] == "filled"])
        cancelled_orders = len([h for h in history if h["status"] in ["cancelled", "canceled", "rejected"]])
        pending_orders = len([h for h in history if h["status"] == "pending"])
        partial_orders = len([h for h in history if h["status"] == "partially_filled"])

        # Calculate average fill percentage
        fill_percentages = [h["fill_percentage"] for h in history if h["fill_percentage"] is not None]
        avg_fill_percentage = sum(fill_percentages) / len(fill_percentages) if fill_percentages else 0

        # Get unique symbols
        unique_symbols = list(set([h["symbol"] for h in history]))

        summary = {
            "period_days": days,
            "total_orders": total_orders,
            "order_breakdown": {
                "filled": filled_orders,
                "cancelled": cancelled_orders,
                "pending": pending_orders,
                "partially_filled": partial_orders
            },
            "fill_rate_percentage": round((filled_orders / total_orders * 100) if total_orders > 0 else 0, 2),
            "average_fill_percentage": round(avg_fill_percentage, 2),
            "unique_symbols_traded": len(unique_symbols),
            "symbols": unique_symbols[:10]  # Top 10 symbols
        }

        return {
            "success": True,
            "data": summary,
            "message": f"Order monitoring summary for past {days} days"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring summary: {str(e)}"
        )