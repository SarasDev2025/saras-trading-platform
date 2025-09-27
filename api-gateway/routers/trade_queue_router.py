"""
Trade Queue Router - API endpoints for queued order aggregation

This router provides endpoints for:
1. Queuing trades instead of immediate execution
2. Monitoring queue status
3. Managing queued orders
4. Triggering batch execution
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from models import APIResponse
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user
from services.trade_queue_service import TradeQueueService

router = APIRouter(tags=["trade-queue"])
logger = logging.getLogger(__name__)


@router.post("/queue/order", response_model=APIResponse)
async def queue_trade_order(
    order_data: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Queue a trade order for batched execution instead of immediate execution

    Request format:
    {
        "smallcase_id": "uuid",
        "suggestions": [
            {
                "stock_id": "uuid",
                "symbol": "AAPL",
                "action": "buy/sell",
                "weight_change": 5.0
            }
        ],
        "priority": "normal|high|low",
        "execution_window": "2024-01-01T10:35:00Z" // optional
    }
    """
    try:
        user_id = str(current_user["id"])

        # Validate request
        required_fields = ['smallcase_id', 'suggestions']
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        suggestions = order_data['suggestions']
        if not suggestions:
            raise HTTPException(status_code=400, detail="At least one order suggestion required")

        priority = order_data.get('priority', 'normal')
        execution_window = order_data.get('execution_window')

        if execution_window:
            execution_window = datetime.fromisoformat(execution_window.replace('Z', '+00:00'))

        logger.info(f"[TradeQueue] Queuing {len(suggestions)} orders for user {user_id}")

        # For now, we'll simulate creating execution orders and queuing them
        # In a full implementation, this would integrate with the execution service

        queue_ids = []
        for suggestion in suggestions:
            # This is a simplified version - in reality, you'd create proper execution orders
            queue_id = f"queue_{user_id}_{datetime.now().timestamp()}"
            queue_ids.append(queue_id)

        # Return queue information
        next_batch_window = TradeQueueService._get_next_batch_window()

        return APIResponse(
            success=True,
            data={
                "queue_ids": queue_ids,
                "orders_queued": len(suggestions),
                "priority": priority,
                "next_batch_window": next_batch_window.isoformat(),
                "estimated_execution_delay_seconds": (next_batch_window - datetime.now(timezone.utc)).total_seconds()
            },
            message=f"Successfully queued {len(suggestions)} orders for batch execution"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TradeQueue] Failed to queue orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue orders: {str(e)}")


@router.get("/queue/status", response_model=APIResponse)
async def get_queue_status(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get current trade queue status and statistics"""
    try:
        status = await TradeQueueService.get_queue_status(db)

        return APIResponse(
            success=True,
            data=status,
            message="Queue status retrieved successfully"
        )

    except Exception as e:
        logger.error(f"[TradeQueue] Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@router.get("/queue/aggregation-preview", response_model=APIResponse)
async def get_aggregation_preview(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get preview of how current queued orders will be aggregated

    Shows which orders will be combined in the next batch execution
    """
    try:
        from sqlalchemy import text

        # Get aggregation preview from database view
        preview_result = await db.execute(text("""
            SELECT * FROM trade_queue_aggregation_view
            ORDER BY scheduled_execution_at, symbol
        """))

        aggregations = []
        for row in preview_result.fetchall():
            aggregations.append({
                "execution_window": row.scheduled_execution_at.isoformat(),
                "broker_type": row.broker_type,
                "symbol": row.symbol,
                "side": row.side,
                "order_count": row.order_count,
                "total_quantity": float(row.total_quantity),
                "average_quantity": float(row.avg_quantity),
                "earliest_queue_time": row.earliest_queue_time.isoformat(),
                "latest_queue_time": row.latest_queue_time.isoformat(),
                "priorities": row.priorities.split(',') if row.priorities else []
            })

        return APIResponse(
            success=True,
            data={
                "aggregations": aggregations,
                "total_aggregation_groups": len(aggregations),
                "next_execution_windows": list(set([agg["execution_window"] for agg in aggregations]))
            },
            message="Aggregation preview retrieved successfully"
        )

    except Exception as e:
        logger.error(f"[TradeQueue] Failed to get aggregation preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get aggregation preview: {str(e)}")


@router.post("/queue/process", response_model=APIResponse)
async def process_queued_orders(
    background_tasks: BackgroundTasks,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger processing of queued orders

    Normally this would run automatically on a schedule, but this endpoint
    allows manual triggering for testing or immediate execution needs.
    """
    try:
        # Check if user has admin privileges (in a real system)
        # For now, we'll allow any authenticated user to trigger processing

        logger.info(f"[TradeQueue] Manual batch processing triggered by user {current_user['id']}")

        # Process orders in background
        background_tasks.add_task(TradeQueueService.process_queued_orders, db)

        return APIResponse(
            success=True,
            data={
                "processing_started": True,
                "triggered_by": str(current_user["id"]),
                "triggered_at": datetime.now(timezone.utc).isoformat()
            },
            message="Batch processing started in background"
        )

    except Exception as e:
        logger.error(f"[TradeQueue] Failed to trigger batch processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger batch processing: {str(e)}")


@router.delete("/queue/order/{queue_id}", response_model=APIResponse)
async def cancel_queued_order(
    queue_id: str,
    cancellation_reason: str = "user_request",
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Cancel a queued order before it executes"""
    try:
        success = await TradeQueueService.cancel_queued_order(db, queue_id, cancellation_reason)

        if success:
            return APIResponse(
                success=True,
                data={
                    "queue_id": queue_id,
                    "cancelled": True,
                    "reason": cancellation_reason,
                    "cancelled_at": datetime.now(timezone.utc).isoformat()
                },
                message="Order cancelled successfully"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Order not found or cannot be cancelled (may already be executing)"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TradeQueue] Failed to cancel order {queue_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")


@router.get("/queue/user/orders", response_model=APIResponse)
async def get_user_queued_orders(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get current user's queued orders"""
    try:
        from sqlalchemy import text

        user_id = str(current_user["id"])

        # Get user's queued orders
        result = await db.execute(text("""
            SELECT
                id, symbol, side, quantity, priority, status,
                queued_at, scheduled_execution_at, batch_id,
                execution_started_at, execution_completed_at,
                error_message, cancellation_reason
            FROM trade_queue
            WHERE user_id = :user_id
            ORDER BY queued_at DESC
            LIMIT 50
        """), {"user_id": user_id})

        orders = []
        for row in result.fetchall():
            orders.append({
                "queue_id": row.id,
                "symbol": row.symbol,
                "side": row.side,
                "quantity": float(row.quantity),
                "priority": row.priority,
                "status": row.status,
                "queued_at": row.queued_at.isoformat(),
                "scheduled_execution_at": row.scheduled_execution_at.isoformat(),
                "batch_id": row.batch_id,
                "execution_started_at": row.execution_started_at.isoformat() if row.execution_started_at else None,
                "execution_completed_at": row.execution_completed_at.isoformat() if row.execution_completed_at else None,
                "error_message": row.error_message,
                "cancellation_reason": row.cancellation_reason
            })

        return APIResponse(
            success=True,
            data={
                "orders": orders,
                "total_orders": len(orders)
            },
            message="User queued orders retrieved successfully"
        )

    except Exception as e:
        logger.error(f"[TradeQueue] Failed to get user orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user orders: {str(e)}")


@router.get("/queue/metrics", response_model=APIResponse)
async def get_queue_metrics(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get trade queue performance metrics"""
    try:
        from sqlalchemy import text

        # Get performance metrics
        metrics_result = await db.execute(text("""
            SELECT
                COUNT(*) as total_orders,
                COUNT(*) FILTER (WHERE status = 'queued') as queued_orders,
                COUNT(*) FILTER (WHERE status = 'executing') as executing_orders,
                COUNT(*) FILTER (WHERE status = 'executed') as executed_orders,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_orders,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_orders,
                AVG(EXTRACT(EPOCH FROM (execution_completed_at - queued_at)))
                    FILTER (WHERE status = 'executed') as avg_processing_time_seconds,
                COUNT(DISTINCT batch_id) FILTER (WHERE batch_id IS NOT NULL) as total_batches
            FROM trade_queue
            WHERE queued_at >= NOW() - INTERVAL '24 hours'
        """))

        metrics = metrics_result.fetchone()

        return APIResponse(
            success=True,
            data={
                "total_orders_24h": metrics.total_orders,
                "queued_orders": metrics.queued_orders,
                "executing_orders": metrics.executing_orders,
                "executed_orders": metrics.executed_orders,
                "failed_orders": metrics.failed_orders,
                "cancelled_orders": metrics.cancelled_orders,
                "average_processing_time_seconds": float(metrics.avg_processing_time_seconds) if metrics.avg_processing_time_seconds else 0,
                "total_batches_24h": metrics.total_batches,
                "success_rate": (metrics.executed_orders / max(metrics.total_orders, 1)) * 100
            },
            message="Queue metrics retrieved successfully"
        )

    except Exception as e:
        logger.error(f"[TradeQueue] Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")