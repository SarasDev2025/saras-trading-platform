"""
Service for aggregating individual user orders into bulk broker orders
to efficiently manage share pooling across multiple users
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from brokers import OrderSide, OrderStatus as BrokerOrderStatus, OrderType as BrokerOrderType
from models import (
    ExecutionOrderStatus,
    SmallcaseExecutionOrder,
    SmallcaseExecutionRun,
    TransactionStatus,
    TransactionType,
    TradingTransaction,
    UserBrokerConnection,
    UserSmallcaseInvestment,
)
from services.broker_connection_service import BrokerConnectionService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AggregatedOrder:
    """Represents an aggregated order combining multiple user orders"""

    def __init__(self, symbol: str, side: OrderSide, broker_type: str):
        self.symbol = symbol
        self.side = side
        self.broker_type = broker_type
        self.total_quantity = Decimal('0')
        self.weighted_avg_price = Decimal('0')
        self.user_orders: List[Dict[str, Any]] = []
        self.broker_order_id: Optional[str] = None
        self.broker_order_status: Optional[BrokerOrderStatus] = None
        self.created_at = datetime.now(timezone.utc)

    def add_user_order(self, order: SmallcaseExecutionOrder, quantity: Decimal,
                      price: Decimal, user_id: uuid.UUID, investment_id: uuid.UUID):
        """Add a user order to the aggregated order"""
        # Update total quantity
        prev_total = self.total_quantity
        self.total_quantity += quantity

        # Update weighted average price
        if self.total_quantity > 0:
            total_value = (prev_total * self.weighted_avg_price) + (quantity * price)
            self.weighted_avg_price = total_value / self.total_quantity

        # Store user order details for tracking
        self.user_orders.append({
            'order': order,
            'quantity': quantity,
            'price': price,
            'user_id': user_id,
            'investment_id': investment_id,
            'proportion': quantity / self.total_quantity if self.total_quantity > 0 else Decimal('0')
        })

        # Recalculate proportions for all orders
        if self.total_quantity > 0:
            for user_order in self.user_orders:
                user_order['proportion'] = user_order['quantity'] / self.total_quantity

    def get_order_summary(self) -> Dict[str, Any]:
        """Get summary information about the aggregated order"""
        return {
            'symbol': self.symbol,
            'side': self.side.value,
            'broker_type': self.broker_type,
            'total_quantity': float(self.total_quantity),
            'weighted_avg_price': float(self.weighted_avg_price),
            'user_count': len(self.user_orders),
            'broker_order_id': self.broker_order_id,
            'broker_order_status': self.broker_order_status.value if self.broker_order_status else None,
            'created_at': self.created_at.isoformat()
        }


class OrderAggregationService:
    """Service for aggregating user orders into bulk broker orders"""

    @staticmethod
    async def aggregate_and_execute_orders(
        db: AsyncSession,
        orders: List[SmallcaseExecutionOrder],
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]],
        investments_by_user: Dict[uuid.UUID, UserSmallcaseInvestment]
    ) -> Dict[str, Any]:
        """
        Aggregate individual user orders by symbol and broker, then execute bulk orders

        Args:
            db: Database session
            orders: List of execution orders to aggregate
            stock_lookup: Mapping of asset_id to stock information
            investments_by_user: Mapping of user_id to their investment

        Returns:
            Dictionary with aggregation results and execution summary
        """
        logger.info(f"[OrderAggregation] Starting aggregation for {len(orders)} orders")

        # Group orders by broker and symbol
        aggregated_orders = await OrderAggregationService._aggregate_orders_by_symbol(
            orders, stock_lookup, investments_by_user
        )

        # Execute aggregated orders with brokers
        execution_results = await OrderAggregationService._execute_aggregated_orders(
            db, aggregated_orders
        )

        # Update individual order statuses based on broker results
        await OrderAggregationService._update_individual_order_statuses(
            db, aggregated_orders, execution_results
        )

        # Create trading transactions for each user
        await OrderAggregationService._create_user_transactions(
            db, aggregated_orders, execution_results
        )

        return {
            'aggregated_orders_count': len(aggregated_orders),
            'total_user_orders': len(orders),
            'execution_results': execution_results,
            'aggregation_summary': [order.get_order_summary() for order in aggregated_orders]
        }

    @staticmethod
    async def _aggregate_orders_by_symbol(
        orders: List[SmallcaseExecutionOrder],
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]],
        investments_by_user: Dict[uuid.UUID, UserSmallcaseInvestment]
    ) -> List[AggregatedOrder]:
        """
        Group individual orders by symbol and side for bulk execution
        """
        # Group by (symbol, side, broker_type)
        order_groups: Dict[Tuple[str, OrderSide, str], AggregatedOrder] = {}

        for order in orders:
            # Get stock information
            stock_info = stock_lookup.get(order.asset_id) if order.asset_id else None
            if not stock_info:
                logger.warning(f"[OrderAggregation] No stock info for order {order.id}")
                order.status = ExecutionOrderStatus.FAILED
                order.details = {**(order.details or {}), "error": "Missing stock information"}
                continue

            # Get user investment to determine broker
            # For now, we'll use a default broker type - in a real implementation,
            # this would come from the user's broker connection
            execution_run = order.execution_run
            if not execution_run:
                logger.warning(f"[OrderAggregation] No execution run for order {order.id}")
                continue

            investment = investments_by_user.get(execution_run.user_id)
            if not investment:
                logger.warning(f"[OrderAggregation] No investment found for user {execution_run.user_id}")
                continue

            # Determine broker type from investment
            broker_type = "zerodha"  # Default - should come from broker_connection
            if investment.broker_connection:
                broker_type = investment.broker_connection.broker_type

            # Calculate order details
            quantity, side = OrderAggregationService._calculate_order_quantity_and_side(
                order, stock_info, investment
            )

            if quantity <= 0:
                logger.info(f"[OrderAggregation] Skipping order {order.id} - zero quantity")
                order.status = ExecutionOrderStatus.SIMULATED
                order.details = {**(order.details or {}), "note": "No quantity change required"}
                continue

            # Create aggregation key
            symbol = stock_info["symbol"]
            key = (symbol, side, broker_type)

            # Get or create aggregated order
            if key not in order_groups:
                order_groups[key] = AggregatedOrder(symbol, side, broker_type)

            # Add this user order to the aggregated order
            current_price = Decimal(str(stock_info.get("current_price", 0)))
            order_groups[key].add_user_order(
                order, quantity, current_price,
                execution_run.user_id, investment.id
            )

            logger.info(f"[OrderAggregation] Added {symbol} {side.value} {quantity} to aggregate")

        aggregated_orders = list(order_groups.values())
        logger.info(f"[OrderAggregation] Created {len(aggregated_orders)} aggregated orders")

        return aggregated_orders

    @staticmethod
    def _calculate_order_quantity_and_side(
        order: SmallcaseExecutionOrder,
        stock_info: Dict[str, Any],
        investment: UserSmallcaseInvestment
    ) -> Tuple[Decimal, OrderSide]:
        """Calculate the quantity and side for an order"""
        weight_change = order.weight_change
        if not weight_change or weight_change == Decimal("0"):
            return Decimal("0"), OrderSide.BUY

        # Calculate the amount change based on portfolio value
        base_value = investment.current_value or investment.investment_amount or Decimal("0")
        amount_change = (weight_change / Decimal("100")) * base_value

        # Get current price
        current_price = stock_info.get("current_price")
        if not current_price or current_price <= 0:
            return Decimal("0"), OrderSide.BUY

        price_decimal = Decimal(str(current_price))

        # Calculate quantity
        quantity = (amount_change.copy_abs() / price_decimal)
        quantity = quantity.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Determine side
        side = OrderSide.BUY if amount_change > 0 else OrderSide.SELL

        return quantity, side

    @staticmethod
    async def _execute_aggregated_orders(
        db: AsyncSession,
        aggregated_orders: List[AggregatedOrder]
    ) -> Dict[str, Any]:
        """Execute aggregated orders with appropriate brokers"""
        execution_results = {
            'successful_orders': 0,
            'failed_orders': 0,
            'total_value_traded': Decimal('0'),
            'order_details': []
        }

        # Group orders by broker type for batch execution
        orders_by_broker: Dict[str, List[AggregatedOrder]] = defaultdict(list)
        for order in aggregated_orders:
            orders_by_broker[order.broker_type].append(order)

        for broker_type, broker_orders in orders_by_broker.items():
            logger.info(f"[OrderAggregation] Executing {len(broker_orders)} orders for {broker_type}")

            try:
                # Get broker connection - for now using a default admin connection
                # In production, this should use a dedicated admin/master broker account
                broker_connection = await OrderAggregationService._get_master_broker_connection(
                    db, broker_type
                )

                if not broker_connection:
                    logger.error(f"[OrderAggregation] No master broker connection for {broker_type}")
                    for order in broker_orders:
                        order.broker_order_status = BrokerOrderStatus.REJECTED
                        execution_results['failed_orders'] += 1
                    continue

                # Get broker instance
                broker, _ = await BrokerConnectionService.ensure_broker_session(broker_connection)

                # Execute each aggregated order
                for aggregated_order in broker_orders:
                    try:
                        logger.info(
                            f"[OrderAggregation] Placing {aggregated_order.symbol} "
                            f"{aggregated_order.side.value} {aggregated_order.total_quantity}"
                        )

                        # Place the aggregated order with broker
                        broker_order = await broker.place_order(
                            symbol=aggregated_order.symbol,
                            side=aggregated_order.side,
                            quantity=aggregated_order.total_quantity,
                            order_type=BrokerOrderType.MARKET
                        )

                        # Update aggregated order with broker response
                        aggregated_order.broker_order_id = broker_order.order_id
                        aggregated_order.broker_order_status = broker_order.status

                        if broker_order.status == BrokerOrderStatus.FILLED:
                            execution_results['successful_orders'] += 1
                            value_traded = aggregated_order.total_quantity * aggregated_order.weighted_avg_price
                            execution_results['total_value_traded'] += value_traded
                        else:
                            execution_results['failed_orders'] += 1

                        execution_results['order_details'].append({
                            'symbol': aggregated_order.symbol,
                            'side': aggregated_order.side.value,
                            'quantity': float(aggregated_order.total_quantity),
                            'broker_order_id': broker_order.order_id,
                            'status': broker_order.status.value if hasattr(broker_order.status, 'value') else str(broker_order.status),
                            'user_count': len(aggregated_order.user_orders)
                        })

                        logger.info(f"[OrderAggregation] Order placed successfully: {broker_order.order_id}")

                    except Exception as exc:
                        logger.error(f"[OrderAggregation] Failed to place order for {aggregated_order.symbol}: {exc}")
                        aggregated_order.broker_order_status = BrokerOrderStatus.REJECTED
                        execution_results['failed_orders'] += 1

                        execution_results['order_details'].append({
                            'symbol': aggregated_order.symbol,
                            'side': aggregated_order.side.value,
                            'quantity': float(aggregated_order.total_quantity),
                            'error': str(exc),
                            'status': 'rejected',
                            'user_count': len(aggregated_order.user_orders)
                        })

            except Exception as exc:
                logger.error(f"[OrderAggregation] Failed to get broker connection for {broker_type}: {exc}")
                for order in broker_orders:
                    order.broker_order_status = BrokerOrderStatus.REJECTED
                    execution_results['failed_orders'] += 1

        logger.info(
            f"[OrderAggregation] Execution complete: "
            f"{execution_results['successful_orders']} successful, "
            f"{execution_results['failed_orders']} failed"
        )

        return execution_results

    @staticmethod
    async def _get_master_broker_connection(
        db: AsyncSession,
        broker_type: str
    ) -> Optional[UserBrokerConnection]:
        """
        Get the master/admin broker connection for executing aggregated orders

        This should be a dedicated admin account that can execute large volumes
        """
        try:
            # Look for a connection with alias 'master' or 'admin'
            result = await db.execute(
                select(UserBrokerConnection).where(
                    UserBrokerConnection.broker_type == broker_type,
                    UserBrokerConnection.alias.in_(['master', 'admin', 'aggregator'])
                ).limit(1)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                # Fallback to any connection of this broker type
                # In production, you should have dedicated admin accounts
                result = await db.execute(
                    select(UserBrokerConnection).where(
                        UserBrokerConnection.broker_type == broker_type
                    ).limit(1)
                )
                connection = result.scalar_one_or_none()

                if connection:
                    logger.warning(
                        f"[OrderAggregation] Using non-admin connection for {broker_type}. "
                        f"Consider setting up dedicated admin accounts."
                    )

            return connection

        except Exception as exc:
            logger.error(f"[OrderAggregation] Error getting master broker connection: {exc}")
            return None

    @staticmethod
    async def _update_individual_order_statuses(
        db: AsyncSession,
        aggregated_orders: List[AggregatedOrder],
        execution_results: Dict[str, Any]
    ):
        """Update individual user order statuses based on aggregated execution results"""
        for aggregated_order in aggregated_orders:
            # Determine status for individual orders based on aggregated order status
            if aggregated_order.broker_order_status == BrokerOrderStatus.FILLED:
                individual_status = ExecutionOrderStatus.COMPLETED
            elif aggregated_order.broker_order_status in [BrokerOrderStatus.PENDING, BrokerOrderStatus.PARTIALLY_FILLED]:
                individual_status = ExecutionOrderStatus.SUBMITTED
            else:
                individual_status = ExecutionOrderStatus.FAILED

            # Update each user order in this aggregated order
            for user_order_info in aggregated_order.user_orders:
                order = user_order_info['order']
                order.status = individual_status
                order.broker_order_id = aggregated_order.broker_order_id

                # Update order details with aggregation info
                order.details = {
                    **(order.details or {}),
                    'aggregated_order_id': f"{aggregated_order.symbol}_{aggregated_order.side.value}_{aggregated_order.broker_type}",
                    'user_quantity': float(user_order_info['quantity']),
                    'user_proportion': float(user_order_info['proportion']),
                    'total_aggregated_quantity': float(aggregated_order.total_quantity),
                    'aggregated_broker_order_id': aggregated_order.broker_order_id,
                    'broker_order_status': aggregated_order.broker_order_status.value if aggregated_order.broker_order_status else None,
                    'mode': 'aggregated_live'
                }

                logger.info(
                    f"[OrderAggregation] Updated order {order.id} status to {individual_status.value}"
                )

    @staticmethod
    async def _create_user_transactions(
        db: AsyncSession,
        aggregated_orders: List[AggregatedOrder],
        execution_results: Dict[str, Any]
    ):
        """Create individual trading transactions for each user based on their proportion of the aggregated order"""
        for aggregated_order in aggregated_orders:
            if aggregated_order.broker_order_status != BrokerOrderStatus.FILLED:
                continue  # Only create transactions for successful orders

            for user_order_info in aggregated_order.user_orders:
                order = user_order_info['order']
                quantity = user_order_info['quantity']
                price = user_order_info['price']
                user_id = user_order_info['user_id']
                investment_id = user_order_info['investment_id']

                # Calculate transaction amounts
                total_amount = quantity * price

                # Create transaction record
                transaction = TradingTransaction(
                    user_id=user_id,
                    portfolio_id=None,  # Will be set from investment
                    asset_id=order.asset_id,
                    broker_connection_id=None,  # Will be set from master connection
                    execution_run_id=order.execution_run_id,
                    transaction_type=TransactionType.BUY if aggregated_order.side == OrderSide.BUY else TransactionType.SELL,
                    quantity=quantity,
                    price_per_unit=price,
                    total_amount=total_amount,
                    fees=Decimal("0"),  # Calculate based on broker fees
                    net_amount=total_amount,
                    status=TransactionStatus.EXECUTED,
                    notes=f"Aggregated order execution - {aggregated_order.broker_order_id}",
                    external_transaction_id=aggregated_order.broker_order_id,
                    broker_order_id=aggregated_order.broker_order_id,
                )

                db.add(transaction)

                logger.info(
                    f"[OrderAggregation] Created transaction for user {user_id}: "
                    f"{quantity} shares of {aggregated_order.symbol}"
                )