"""
Order Monitoring Service
Tracks order execution status and provides next-day order checking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..brokers.base import OrderStatus
from .broker_factory_service import BrokerFactoryService

logger = logging.getLogger(__name__)


class OrderMonitoringService:
    """Service for monitoring order execution and next-day checking"""

    @staticmethod
    async def queue_order_for_monitoring(
        db: AsyncSession,
        broker_connection_id: str,
        order_id: str,
        symbol: str,
        order_type: str,
        quantity: float,
        expected_execution_date: datetime
    ) -> Dict[str, Any]:
        """Queue an order for next-day execution monitoring"""
        try:
            # Store order in monitoring table
            insert_query = text("""
                INSERT INTO order_monitoring (
                    broker_connection_id,
                    order_id,
                    symbol,
                    order_type,
                    quantity,
                    expected_execution_date,
                    status,
                    created_at
                ) VALUES (
                    :broker_connection_id,
                    :order_id,
                    :symbol,
                    :order_type,
                    :quantity,
                    :expected_execution_date,
                    'pending',
                    :created_at
                )
            """)

            await db.execute(insert_query, {
                "broker_connection_id": broker_connection_id,
                "order_id": order_id,
                "symbol": symbol,
                "order_type": order_type,
                "quantity": quantity,
                "expected_execution_date": expected_execution_date,
                "created_at": datetime.utcnow()
            })

            await db.commit()

            logger.info(f"Queued order {order_id} for monitoring on {expected_execution_date}")

            return {
                "success": True,
                "order_id": order_id,
                "expected_execution_date": expected_execution_date,
                "message": "Order queued for monitoring"
            }

        except Exception as e:
            logger.error(f"Failed to queue order for monitoring: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def check_pending_orders(
        db: AsyncSession,
        check_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Check execution status of pending orders for a specific date"""
        if check_date is None:
            check_date = datetime.utcnow().date()

        try:
            # Get pending orders for the specified date
            query = text("""
                SELECT
                    om.id,
                    om.broker_connection_id,
                    om.order_id,
                    om.symbol,
                    om.order_type,
                    om.quantity,
                    om.expected_execution_date,
                    om.status,
                    om.created_at
                FROM order_monitoring om
                WHERE om.status = 'pending'
                  AND DATE(om.expected_execution_date) = :check_date
                ORDER BY om.created_at
            """)

            result = await db.execute(query, {"check_date": check_date})
            pending_orders = result.fetchall()

            if not pending_orders:
                return {
                    "check_date": check_date.isoformat(),
                    "total_orders": 0,
                    "results": [],
                    "summary": "No pending orders found for this date"
                }

            # Group orders by broker connection for efficient checking
            orders_by_broker = {}
            for order in pending_orders:
                broker_id = order[1]  # broker_connection_id
                if broker_id not in orders_by_broker:
                    orders_by_broker[broker_id] = []
                orders_by_broker[broker_id].append(order)

            # Check each broker's orders
            all_results = []
            total_filled = 0
            total_pending = 0
            total_cancelled = 0
            total_failed = 0

            for broker_connection_id, orders in orders_by_broker.items():
                try:
                    # Create broker instance
                    broker = await BrokerFactoryService.create_broker_from_connection(
                        db, broker_connection_id
                    )

                    # Extract order IDs for this broker
                    order_ids = [order[2] for order in orders]  # order_id

                    # Check execution status for all orders
                    execution_results = await broker.check_order_execution_status(order_ids)

                    # Process results and update database
                    for order in orders:
                        monitoring_id = order[0]
                        order_id = order[2]
                        symbol = order[3]
                        expected_qty = order[5]

                        if order_id in execution_results:
                            result = execution_results[order_id]
                            status = result.get("status", "unknown")
                            filled_qty = result.get("filled_quantity", 0)
                            fill_percentage = result.get("fill_percentage", 0)

                            # Update monitoring record
                            await OrderMonitoringService._update_monitoring_record(
                                db, monitoring_id, status, filled_qty, fill_percentage
                            )

                            # Count for summary
                            if status == "filled":
                                total_filled += 1
                            elif status in ["cancelled", "canceled", "rejected"]:
                                total_cancelled += 1
                            else:
                                total_pending += 1

                            all_results.append({
                                "order_id": order_id,
                                "symbol": symbol,
                                "broker_connection_id": broker_connection_id,
                                "status": status,
                                "expected_quantity": expected_qty,
                                "filled_quantity": filled_qty,
                                "fill_percentage": round(fill_percentage, 2),
                                "execution_complete": status == "filled",
                                "needs_attention": status in ["cancelled", "canceled", "rejected"]
                            })
                        else:
                            total_failed += 1
                            all_results.append({
                                "order_id": order_id,
                                "symbol": symbol,
                                "broker_connection_id": broker_connection_id,
                                "status": "error",
                                "error": "Failed to check order status",
                                "needs_attention": True
                            })

                except Exception as e:
                    logger.error(f"Error checking orders for broker {broker_connection_id}: {e}")
                    total_failed += len(orders)
                    for order in orders:
                        all_results.append({
                            "order_id": order[2],
                            "symbol": order[3],
                            "broker_connection_id": broker_connection_id,
                            "status": "error",
                            "error": str(e),
                            "needs_attention": True
                        })

            await db.commit()

            return {
                "check_date": check_date.isoformat(),
                "total_orders": len(pending_orders),
                "summary": {
                    "filled": total_filled,
                    "pending": total_pending,
                    "cancelled": total_cancelled,
                    "failed": total_failed
                },
                "results": all_results
            }

        except Exception as e:
            logger.error(f"Failed to check pending orders: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def _update_monitoring_record(
        db: AsyncSession,
        monitoring_id: int,
        status: str,
        filled_quantity: float,
        fill_percentage: float
    ):
        """Update order monitoring record with execution results"""
        update_query = text("""
            UPDATE order_monitoring
            SET status = :status,
                filled_quantity = :filled_quantity,
                fill_percentage = :fill_percentage,
                checked_at = :checked_at
            WHERE id = :monitoring_id
        """)

        await db.execute(update_query, {
            "monitoring_id": monitoring_id,
            "status": status,
            "filled_quantity": filled_quantity,
            "fill_percentage": fill_percentage,
            "checked_at": datetime.utcnow()
        })

    @staticmethod
    async def get_monitoring_history(
        db: AsyncSession,
        days: int = 30,
        broker_connection_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get order monitoring history for the past N days"""
        try:
            conditions = ["om.created_at >= :start_date"]
            params = {"start_date": datetime.utcnow() - timedelta(days=days)}

            if broker_connection_id:
                conditions.append("om.broker_connection_id = :broker_connection_id")
                params["broker_connection_id"] = broker_connection_id

            where_clause = " AND ".join(conditions)

            query = text(f"""
                SELECT
                    om.id,
                    om.broker_connection_id,
                    om.order_id,
                    om.symbol,
                    om.order_type,
                    om.quantity,
                    om.filled_quantity,
                    om.fill_percentage,
                    om.status,
                    om.expected_execution_date,
                    om.created_at,
                    om.checked_at
                FROM order_monitoring om
                WHERE {where_clause}
                ORDER BY om.created_at DESC
            """)

            result = await db.execute(query, params)
            records = result.fetchall()

            history = []
            for record in records:
                history.append({
                    "id": record[0],
                    "broker_connection_id": record[1],
                    "order_id": record[2],
                    "symbol": record[3],
                    "order_type": record[4],
                    "quantity": record[5],
                    "filled_quantity": record[6],
                    "fill_percentage": record[7],
                    "status": record[8],
                    "expected_execution_date": record[9],
                    "created_at": record[10],
                    "checked_at": record[11]
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get monitoring history: {str(e)}")
            raise

    @staticmethod
    async def get_orders_needing_attention(db: AsyncSession) -> List[Dict[str, Any]]:
        """Get orders that need attention (cancelled, rejected, or failed to execute)"""
        try:
            query = text("""
                SELECT
                    om.id,
                    om.broker_connection_id,
                    om.order_id,
                    om.symbol,
                    om.order_type,
                    om.quantity,
                    om.filled_quantity,
                    om.fill_percentage,
                    om.status,
                    om.expected_execution_date,
                    om.created_at,
                    om.checked_at
                FROM order_monitoring om
                WHERE om.status IN ('cancelled', 'canceled', 'rejected', 'error')
                   OR (om.status = 'partially_filled' AND om.fill_percentage < 90)
                ORDER BY om.created_at DESC
                LIMIT 100
            """)

            result = await db.execute(query)
            records = result.fetchall()

            attention_orders = []
            for record in records:
                attention_orders.append({
                    "id": record[0],
                    "broker_connection_id": record[1],
                    "order_id": record[2],
                    "symbol": record[3],
                    "order_type": record[4],
                    "quantity": record[5],
                    "filled_quantity": record[6] or 0,
                    "fill_percentage": record[7] or 0,
                    "status": record[8],
                    "expected_execution_date": record[9],
                    "created_at": record[10],
                    "checked_at": record[11],
                    "reason": OrderMonitoringService._get_attention_reason(record[8], record[7])
                })

            return attention_orders

        except Exception as e:
            logger.error(f"Failed to get orders needing attention: {str(e)}")
            raise

    @staticmethod
    def _get_attention_reason(status: str, fill_percentage: float) -> str:
        """Get human-readable reason why order needs attention"""
        if status in ["cancelled", "canceled"]:
            return "Order was cancelled"
        elif status == "rejected":
            return "Order was rejected by broker"
        elif status == "error":
            return "Error occurred while checking order status"
        elif status == "partially_filled" and fill_percentage < 90:
            return f"Order only {fill_percentage:.1f}% filled"
        else:
            return "Unknown issue"