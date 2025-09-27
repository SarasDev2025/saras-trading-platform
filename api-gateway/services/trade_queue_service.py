"""
Trade Queue Service - Time-based Order Aggregation

This service implements time-based batching where trades are:
1. Queued when submitted (not executed immediately)
2. Aggregated by symbol during batch windows
3. Executed periodically (e.g., every 5 minutes)
4. Distributed back to individual users

This provides better aggregation efficiency and reduced market impact.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    ExecutionOrderStatus,
    SmallcaseExecutionOrder,
    SmallcaseExecutionRun,
    UserSmallcaseInvestment,
)
from services.order_aggregation_service import OrderAggregationService

logger = logging.getLogger(__name__)


class QueuedOrderStatus(str, Enum):
    QUEUED = "queued"
    BATCHED = "batched"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TradeQueueService:
    """Service for time-based trade aggregation and batched execution"""

    def __init__(self):
        self.batch_interval_seconds = 300  # 5 minutes
        self.max_batch_size = 100  # Maximum orders per batch
        self.running_batches: Set[str] = set()
        self.is_processing = False

    @staticmethod
    async def queue_order(
        db: AsyncSession,
        execution_order: SmallcaseExecutionOrder,
        priority: str = "normal",
        execution_window: Optional[datetime] = None
    ) -> str:
        """
        Queue an order for batched execution instead of immediate execution

        Args:
            db: Database session
            execution_order: The order to queue
            priority: Order priority (high, normal, low)
            execution_window: When to execute (None = next batch)

        Returns:
            Queue ID for tracking
        """
        queue_id = str(uuid.uuid4())

        # Calculate next batch execution time
        if execution_window is None:
            execution_window = TradeQueueService._get_next_batch_window()

        # Insert into trade queue table
        await db.execute(text("""
            INSERT INTO trade_queue (
                id, execution_order_id, user_id, symbol, side, quantity,
                priority, status, queued_at, scheduled_execution_at,
                broker_type, metadata
            ) VALUES (
                :id, :execution_order_id, :user_id, :symbol, :side, :quantity,
                :priority, :status, :queued_at, :scheduled_execution_at,
                :broker_type, :metadata
            )
        """), {
            "id": queue_id,
            "execution_order_id": str(execution_order.id),
            "user_id": str(execution_order.execution_run.user_id),
            "symbol": execution_order.symbol,
            "side": execution_order.action,  # buy/sell
            "quantity": str(execution_order.weight_change),  # Will be calculated properly
            "priority": priority,
            "status": QueuedOrderStatus.QUEUED.value,
            "queued_at": datetime.now(timezone.utc),
            "scheduled_execution_at": execution_window,
            "broker_type": "zerodha",  # Default, should come from user's broker
            "metadata": execution_order.details
        })

        logger.info(f"[TradeQueue] Queued order {queue_id} for execution at {execution_window}")

        # Update original execution order status
        execution_order.status = ExecutionOrderStatus.PENDING
        execution_order.details = {
            **(execution_order.details or {}),
            "queue_id": queue_id,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "execution_mode": "queued_aggregation"
        }

        return queue_id

    @staticmethod
    def _get_next_batch_window() -> datetime:
        """Calculate the next batch execution window"""
        now = datetime.now(timezone.utc)

        # Round up to next 5-minute interval
        # e.g., 10:32 → 10:35, 10:37 → 10:40
        minutes = now.minute
        next_interval = ((minutes // 5) + 1) * 5

        if next_interval >= 60:
            next_window = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            next_window = now.replace(minute=next_interval, second=0, microsecond=0)

        return next_window

    @staticmethod
    async def process_queued_orders(db: AsyncSession) -> Dict[str, Any]:
        """
        Process all queued orders that are ready for execution

        This method should be called periodically (e.g., every minute)
        to check for orders ready to execute.
        """
        logger.info("[TradeQueue] Processing queued orders...")

        # Get orders ready for execution
        now = datetime.now(timezone.utc)

        ready_orders_result = await db.execute(text("""
            SELECT
                id, execution_order_id, user_id, symbol, side, quantity,
                priority, broker_type, metadata, queued_at, scheduled_execution_at
            FROM trade_queue
            WHERE status = :status
            AND scheduled_execution_at <= :now
            ORDER BY priority DESC, queued_at ASC
        """), {
            "status": QueuedOrderStatus.QUEUED.value,
            "now": now
        })

        ready_orders = ready_orders_result.fetchall()

        if not ready_orders:
            logger.info("[TradeQueue] No orders ready for execution")
            return {"processed_batches": 0, "total_orders": 0}

        logger.info(f"[TradeQueue] Found {len(ready_orders)} orders ready for execution")

        # Group orders by execution window and broker
        batches = defaultdict(list)
        for order in ready_orders:
            batch_key = f"{order.scheduled_execution_at}_{order.broker_type}"
            batches[batch_key].append(order)

        processed_batches = 0
        total_processed_orders = 0

        # Process each batch
        for batch_key, batch_orders in batches.items():
            try:
                result = await TradeQueueService._execute_batch(db, batch_orders)
                if result["success"]:
                    processed_batches += 1
                    total_processed_orders += len(batch_orders)
                    logger.info(f"[TradeQueue] Successfully processed batch {batch_key} with {len(batch_orders)} orders")
                else:
                    logger.error(f"[TradeQueue] Failed to process batch {batch_key}: {result.get('error')}")
            except Exception as exc:
                logger.error(f"[TradeQueue] Error processing batch {batch_key}: {exc}")

        return {
            "processed_batches": processed_batches,
            "total_orders": total_processed_orders,
            "execution_time": now.isoformat()
        }

    @staticmethod
    async def _execute_batch(db: AsyncSession, batch_orders: List[Any]) -> Dict[str, Any]:
        """Execute a batch of orders using the aggregation service"""
        try:
            batch_id = str(uuid.uuid4())
            logger.info(f"[TradeQueue] Executing batch {batch_id} with {len(batch_orders)} orders")

            # Mark orders as executing
            order_ids = [order.id for order in batch_orders]
            await db.execute(text("""
                UPDATE trade_queue
                SET status = :status, batch_id = :batch_id, execution_started_at = :started_at
                WHERE id = ANY(:order_ids)
            """), {
                "status": QueuedOrderStatus.EXECUTING.value,
                "batch_id": batch_id,
                "started_at": datetime.now(timezone.utc),
                "order_ids": order_ids
            })

            # Get corresponding execution orders
            execution_orders = []
            stock_lookup = {}
            investments_by_user = {}

            for queued_order in batch_orders:
                # Get the execution order
                execution_order_result = await db.execute(
                    select(SmallcaseExecutionOrder).where(
                        SmallcaseExecutionOrder.id == uuid.UUID(queued_order.execution_order_id)
                    )
                )
                execution_order = execution_order_result.scalar_one_or_none()

                if execution_order:
                    execution_orders.append(execution_order)

                    # Build stock lookup (simplified for this example)
                    if execution_order.asset_id:
                        stock_lookup[execution_order.asset_id] = {
                            "stock_id": str(execution_order.asset_id),
                            "symbol": execution_order.symbol,
                            "current_price": 100.0,  # Should fetch real price
                            "company_name": execution_order.symbol
                        }

                    # Get user investment (simplified)
                    investment_result = await db.execute(
                        select(UserSmallcaseInvestment).where(
                            UserSmallcaseInvestment.id == execution_order.execution_run.investment_id
                        )
                    )
                    investment = investment_result.scalar_one_or_none()
                    if investment:
                        investments_by_user[execution_order.execution_run.user_id] = investment

            # Execute using aggregation service
            if execution_orders:
                aggregation_result = await OrderAggregationService.aggregate_and_execute_orders(
                    db, execution_orders, stock_lookup, investments_by_user
                )

                # Mark orders as executed
                await db.execute(text("""
                    UPDATE trade_queue
                    SET status = :status, execution_completed_at = :completed_at,
                        execution_result = :result
                    WHERE id = ANY(:order_ids)
                """), {
                    "status": QueuedOrderStatus.EXECUTED.value,
                    "completed_at": datetime.now(timezone.utc),
                    "result": str(aggregation_result),
                    "order_ids": order_ids
                })

                return {"success": True, "batch_id": batch_id, "aggregation_result": aggregation_result}
            else:
                # Mark as failed
                await db.execute(text("""
                    UPDATE trade_queue
                    SET status = :status, execution_completed_at = :completed_at,
                        error_message = :error
                    WHERE id = ANY(:order_ids)
                """), {
                    "status": QueuedOrderStatus.FAILED.value,
                    "completed_at": datetime.now(timezone.utc),
                    "error": "No valid execution orders found",
                    "order_ids": order_ids
                })

                return {"success": False, "error": "No valid execution orders found"}

        except Exception as exc:
            logger.error(f"[TradeQueue] Batch execution failed: {exc}")

            # Mark orders as failed
            await db.execute(text("""
                UPDATE trade_queue
                SET status = :status, execution_completed_at = :completed_at,
                    error_message = :error
                WHERE id = ANY(:order_ids)
            """), {
                "status": QueuedOrderStatus.FAILED.value,
                "completed_at": datetime.now(timezone.utc),
                "error": str(exc),
                "order_ids": [order.id for order in batch_orders]
            })

            return {"success": False, "error": str(exc)}

    @staticmethod
    async def get_queue_status(db: AsyncSession) -> Dict[str, Any]:
        """Get current queue status and statistics"""

        # Get queue statistics
        stats_result = await db.execute(text("""
            SELECT
                status,
                COUNT(*) as count,
                MIN(queued_at) as oldest_order,
                MAX(queued_at) as newest_order
            FROM trade_queue
            WHERE status IN ('queued', 'batched', 'executing')
            GROUP BY status
        """))

        stats = {}
        for row in stats_result.fetchall():
            stats[row.status] = {
                "count": row.count,
                "oldest_order": row.oldest_order.isoformat() if row.oldest_order else None,
                "newest_order": row.newest_order.isoformat() if row.newest_order else None
            }

        # Get next batch windows
        next_windows_result = await db.execute(text("""
            SELECT
                scheduled_execution_at,
                COUNT(*) as pending_orders
            FROM trade_queue
            WHERE status = 'queued'
            GROUP BY scheduled_execution_at
            ORDER BY scheduled_execution_at ASC
            LIMIT 5
        """))

        next_windows = []
        for row in next_windows_result.fetchall():
            next_windows.append({
                "execution_time": row.scheduled_execution_at.isoformat(),
                "pending_orders": row.pending_orders
            })

        return {
            "queue_statistics": stats,
            "next_batch_windows": next_windows,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "next_batch_in_seconds": (TradeQueueService._get_next_batch_window() - datetime.now(timezone.utc)).total_seconds()
        }

    @staticmethod
    async def cancel_queued_order(db: AsyncSession, queue_id: str, reason: str = "user_cancellation") -> bool:
        """Cancel a queued order before execution"""

        result = await db.execute(text("""
            UPDATE trade_queue
            SET status = :status, cancellation_reason = :reason, cancelled_at = :cancelled_at
            WHERE id = :queue_id AND status = :queued_status
        """), {
            "status": QueuedOrderStatus.CANCELLED.value,
            "reason": reason,
            "cancelled_at": datetime.now(timezone.utc),
            "queue_id": queue_id,
            "queued_status": QueuedOrderStatus.QUEUED.value
        })

        if result.rowcount > 0:
            logger.info(f"[TradeQueue] Cancelled queued order {queue_id}: {reason}")
            return True
        else:
            logger.warning(f"[TradeQueue] Could not cancel order {queue_id} - may already be executing")
            return False