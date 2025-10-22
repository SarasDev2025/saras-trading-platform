"""Service orchestrating paper vs live execution for smallcase rebalancing."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from brokers import OrderSide, OrderStatus as BrokerOrderStatus, OrderType as BrokerOrderType
from models import (
    ExecutionMode,
    ExecutionOrderStatus,
    ExecutionStatus,
    OrderType,
    UserBrokerConnection,
    SmallcaseExecutionOrder,
    SmallcaseExecutionRun,
    TransactionStatus,
    TransactionType,
    TradingTransaction,
    UserSmallcaseInvestment,
)
from services.broker_connection_service import BrokerConnectionService
from services.order_aggregation_service import OrderAggregationService
from services.rebalancing_db_service import RebalancingDBService
from services.trading_service import TradingService


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SmallcaseExecutionService:
    """Encapsulates the workflow for executing (or simulating) a rebalance."""

    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """Recursively serialize objects to be JSON-safe, converting datetime to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: SmallcaseExecutionService._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [SmallcaseExecutionService._serialize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Handle objects with attributes
            return SmallcaseExecutionService._serialize_for_json(obj.__dict__)
        else:
            return obj

    @staticmethod
    def _normalize_uuid(value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid identifier supplied") from exc

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    async def _load_investment(
        db: AsyncSession,
        user_id: uuid.UUID,
        smallcase_id: uuid.UUID
    ) -> UserSmallcaseInvestment:
        result = await db.execute(
            select(UserSmallcaseInvestment)
            .options(
                selectinload(UserSmallcaseInvestment.broker_connection),
                selectinload(UserSmallcaseInvestment.execution_runs)
            )
            .where(
                UserSmallcaseInvestment.user_id == user_id,
                UserSmallcaseInvestment.smallcase_id == smallcase_id,
                UserSmallcaseInvestment.status == "active"
            )
            .order_by(UserSmallcaseInvestment.invested_at.desc())
        )
        investment = result.scalars().first()
        if not investment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active smallcase investment not found for user"
            )
        return investment

    @staticmethod
    async def execute_rebalance(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        smallcase_id: uuid.UUID | str,
        suggestions: List[Dict[str, Any]],
        rebalance_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        user_uuid = SmallcaseExecutionService._normalize_uuid(user_id)
        smallcase_uuid = SmallcaseExecutionService._normalize_uuid(smallcase_id)

        logger.info(
            "[Execution] Starting rebalance: user=%s smallcase=%s suggestions=%d",
            user_uuid,
            smallcase_uuid,
            len(suggestions),
        )

        try:
            investment = await SmallcaseExecutionService._load_investment(db, user_uuid, smallcase_uuid)
            execution_mode = investment.execution_mode or ExecutionMode.PAPER
            broker_connection = investment.broker_connection
            logger.info(
                "[Execution] Investment mode=%s broker_connection_id=%s broker_paper=%s",
                execution_mode,
                broker_connection.id if broker_connection else None,
                broker_connection.paper_trading if broker_connection else None,
            )

            if execution_mode == ExecutionMode.LIVE and not broker_connection:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Live execution requires an active broker connection"
                )

            use_broker = False

            if execution_mode == ExecutionMode.PAPER:
                # Paper mode: Alpaca uses paper API, Zerodha uses simulation
                if broker_connection and broker_connection.broker_type == 'alpaca':
                    use_broker = True  # Use Alpaca paper API
                else:
                    use_broker = False  # Pure simulation for Zerodha
            elif execution_mode == ExecutionMode.LIVE:
                # Live mode: Always use broker API
                use_broker = True

            composition = await RebalancingDBService.get_smallcase_composition(db, smallcase_uuid)
            logger.info(
                "[Execution] Composition totals: stocks=%s weight=%.2f",
                composition.get("total_stocks"),
                composition.get("total_target_weight", 0),
            )
            stock_lookup = {
                uuid.UUID(str(stock["stock_id"])): stock
                for stock in composition.get("stocks", [])
                if stock.get("stock_id")
            }

            run = SmallcaseExecutionRun(
                user_id=investment.user_id,
                investment_id=investment.id,
                broker_connection_id=broker_connection.id if broker_connection else None,
                execution_mode=execution_mode,
                status=ExecutionStatus.PENDING,
                total_orders=len(suggestions),
            )
            logger.info("[Execution] Created run id=%s total_orders=%d", run.id, len(suggestions))
            db.add(run)
            await db.flush()  # Ensure run.id is available

            orders: List[SmallcaseExecutionOrder] = []
            for suggestion in suggestions:
                asset_id = None
                if suggestion.get("stock_id"):
                    try:
                        asset_id = uuid.UUID(str(suggestion["stock_id"]))
                    except (TypeError, ValueError):
                        asset_id = None

                order = SmallcaseExecutionOrder(
                    execution_run_id=run.id,
                    asset_id=asset_id,
                    symbol=suggestion.get("symbol"),
                    action=suggestion.get("action"),
                    current_weight=SmallcaseExecutionService._to_decimal(suggestion.get("current_weight")),
                    suggested_weight=SmallcaseExecutionService._to_decimal(suggestion.get("suggested_weight")),
                    weight_change=SmallcaseExecutionService._to_decimal(suggestion.get("weight_change")),
                    status=ExecutionOrderStatus.PENDING,
                    details=suggestion,
                )
                db.add(order)
                orders.append(order)

            try:
                now = datetime.now(timezone.utc)
                investment.last_rebalanced_at = now

                if not use_broker:
                    summary = await SmallcaseExecutionService._execute_paper_orders(
                        run,
                        orders,
                        investment,
                        stock_lookup,
                        rebalance_summary
                    )
                    run.summary = SmallcaseExecutionService._serialize_for_json(summary)
                    run.completed_at = now
                else:
                    summary = await SmallcaseExecutionService._execute_live_orders(
                        db=db,
                        run=run,
                        orders=orders,
                        investment=investment,
                        broker_connection=broker_connection,
                        stock_lookup=stock_lookup,
                        rebalance_summary=rebalance_summary,
                        connection_is_paper=(execution_mode == ExecutionMode.PAPER)
                    )
                    run.summary = SmallcaseExecutionService._serialize_for_json(summary)
                    logger.info(
                        "[Execution] Live summary: mode=%s submitted=%s completed=%s",
                        summary.get("mode"),
                        summary.get("submitted_orders"),
                        summary.get("completed_orders"),
                    )

                await db.commit()
            except HTTPException:
                logger.exception("[Execution] HTTPException during execution")
                await db.rollback()
                raise
            except Exception:
                logger.exception("[Execution] Unexpected error during execution")
                await db.rollback()
                raise

            logger.info(
                "[Execution] Completed run id=%s status=%s completed_orders=%s",
                run.id,
                run.status,
                run.completed_orders,
            )

            await db.refresh(run)
            await db.refresh(investment)

            # Ensure orders relationship is loaded with latest state
            await db.refresh(run, attribute_names=["orders"])

            return SmallcaseExecutionService._serialize_run(run)

        except HTTPException:
            logger.exception("[Execution] HTTP error during rebalance user=%s smallcase=%s", user_id, smallcase_id)
            raise
        except Exception:
            logger.exception("[Execution] Unexpected error during rebalance user=%s smallcase=%s", user_id, smallcase_id)
            raise

    @staticmethod
    def _serialize_run(run: SmallcaseExecutionRun) -> Dict[str, Any]:
        return {
            "id": str(run.id),
            "user_id": str(run.user_id),
            "investment_id": str(run.investment_id),
            "broker_connection_id": str(run.broker_connection_id) if run.broker_connection_id else None,
            "execution_mode": run.execution_mode.value if hasattr(run.execution_mode, "value") else run.execution_mode,
            "status": run.status.value if hasattr(run.status, "value") else run.status,
            "total_orders": run.total_orders,
            "completed_orders": run.completed_orders,
            "summary": run.summary or {},
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "orders": [SmallcaseExecutionService._serialize_order(order) for order in run.orders],
        }

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_stock_info(
        order: SmallcaseExecutionOrder,
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if order.asset_id and order.asset_id in stock_lookup:
            return stock_lookup[order.asset_id]
        return None

    @staticmethod
    def _calculate_trade_amount(
        order: SmallcaseExecutionOrder,
        stock_info: Dict[str, Any],
        investment: UserSmallcaseInvestment
    ) -> Tuple[Decimal, Decimal, OrderSide]:
        weight_change = SmallcaseExecutionService._to_decimal(order.weight_change)
        if not weight_change or weight_change == Decimal("0"):
            return Decimal("0"), Decimal("0"), OrderSide.BUY

        base_value = investment.current_value or investment.investment_amount
        if base_value is None:
            base_value = Decimal("0")
        base_value = Decimal(str(base_value))

        amount_change = (weight_change / Decimal("100")) * base_value
        current_price = stock_info.get("current_price")
        if current_price is None:
            return Decimal("0"), Decimal("0"), OrderSide.BUY

        price_decimal = Decimal(str(current_price))
        if price_decimal <= 0:
            return Decimal("0"), Decimal("0"), OrderSide.BUY

        quantity = (amount_change / price_decimal).copy_abs()
        quantity = quantity.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        side = OrderSide.BUY if amount_change > 0 else OrderSide.SELL
        return amount_change.copy_abs(), quantity, side

    @staticmethod
    async def _execute_paper_orders(
        run: SmallcaseExecutionRun,
        orders: List[SmallcaseExecutionOrder],
        investment: UserSmallcaseInvestment,
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]],
        rebalance_summary: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        completed = 0
        skipped = 0
        results = []

        for order in orders:
            stock_info = SmallcaseExecutionService._get_stock_info(order, stock_lookup)
            if not stock_info:
                order.status = ExecutionOrderStatus.FAILED
                order.details = {**(order.details or {}), "error": "Missing stock information"}
                skipped += 1
                continue

            amount_change, quantity, side = SmallcaseExecutionService._calculate_trade_amount(
                order, stock_info, investment
            )

            if quantity <= 0:
                order.status = ExecutionOrderStatus.SIMULATED
                order.details = {**(order.details or {}), "note": "No quantity change required"}
                skipped += 1
                continue

            try:
                transaction_type = TransactionType.BUY if side == OrderSide.BUY else TransactionType.SELL
                transaction = await TradingService.create_transaction(
                    {
                        "user_id": str(investment.user_id),
                        "portfolio_id": str(investment.portfolio_id),
                        "asset_id": str(order.asset_id),
                        "transaction_type": transaction_type,
                        "quantity": str(quantity),
                        "price_per_unit": str(stock_info.get("current_price", 0)),
                        "order_type": OrderType.MARKET,
                        "notes": f"Smallcase rebalance run {run.id}",
                        "execution_metadata": {
                            "smallcase_investment_id": str(investment.id),
                            "execution_run_id": str(run.id),
                            "source": "smallcase_rebalance"
                        }
                    }
                )

                order.status = ExecutionOrderStatus.COMPLETED
                order.details = {
                    **(order.details or {}),
                    "transaction_id": str(transaction.id),
                    "amount": str(amount_change),
                    "quantity": str(quantity),
                    "mode": "paper",
                }
                completed += 1
                results.append({
                    "order_id": str(order.id),
                    "transaction_id": str(transaction.id),
                    "status": "completed",
                })
            except Exception as exc:
                order.status = ExecutionOrderStatus.FAILED
                order.details = {
                    **(order.details or {}),
                    "error": str(exc),
                    "mode": "paper",
                }
                results.append({
                    "order_id": str(order.id),
                    "status": "failed",
                    "error": str(exc),
                })

        success_total = completed + skipped
        if success_total == len(orders):
            run.status = ExecutionStatus.COMPLETED
        elif completed > 0:
            run.status = ExecutionStatus.SUBMITTED
        else:
            run.status = ExecutionStatus.FAILED
        run.completed_orders = completed

        return {
            "mode": ExecutionMode.PAPER.value,
            "type": "paper_execution",
            "completed_orders": completed,
            "skipped_orders": skipped,
            "orders": results,
            "rebalance": rebalance_summary or {},
        }

    @staticmethod
    async def _execute_live_orders_aggregated(
        db: AsyncSession,
        runs: List[SmallcaseExecutionRun],
        all_orders: List[SmallcaseExecutionOrder],
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]],
        rebalance_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute orders using aggregation service for efficient bulk trading

        Args:
            db: Database session
            runs: List of execution runs
            all_orders: All orders from all users to be aggregated
            stock_lookup: Stock information lookup
            rebalance_summary: Optional rebalance summary

        Returns:
            Execution summary
        """
        logger.info(f"[Execution] Starting aggregated execution for {len(all_orders)} orders from {len(runs)} users")

        # Build investments lookup by user
        investments_by_user = {}
        for run in runs:
            # Get investment for this run
            result = await db.execute(
                select(UserSmallcaseInvestment)
                .options(selectinload(UserSmallcaseInvestment.broker_connection))
                .where(UserSmallcaseInvestment.id == run.investment_id)
            )
            investment = result.scalar_one_or_none()
            if investment:
                investments_by_user[run.user_id] = investment

        # Use aggregation service to execute orders
        try:
            aggregation_results = await OrderAggregationService.aggregate_and_execute_orders(
                db, all_orders, stock_lookup, investments_by_user
            )

            # Update run statuses based on results
            for run in runs:
                user_orders = [order for order in all_orders if order.execution_run_id == run.id]
                completed_orders = sum(1 for order in user_orders
                                     if order.status == ExecutionOrderStatus.COMPLETED)
                submitted_orders = sum(1 for order in user_orders
                                     if order.status == ExecutionOrderStatus.SUBMITTED)

                run.completed_orders = completed_orders

                if completed_orders == len(user_orders):
                    run.status = ExecutionStatus.COMPLETED
                elif submitted_orders > 0 or completed_orders > 0:
                    run.status = ExecutionStatus.SUBMITTED
                else:
                    run.status = ExecutionStatus.FAILED

                run.completed_at = datetime.now(timezone.utc)

            return {
                "mode": "aggregated_live",
                "type": "aggregated_execution",
                "aggregated_orders_count": aggregation_results['aggregated_orders_count'],
                "total_user_orders": aggregation_results['total_user_orders'],
                "execution_results": aggregation_results['execution_results'],
                "rebalance": rebalance_summary or {},
                "aggregation_summary": aggregation_results['aggregation_summary']
            }

        except Exception as exc:
            logger.error(f"[Execution] Aggregated execution failed: {exc}")
            # Mark all runs as failed
            for run in runs:
                run.status = ExecutionStatus.FAILED
                run.error_message = str(exc)
                run.completed_at = datetime.now(timezone.utc)
            raise

    @staticmethod
    async def execute_multiple_rebalances_aggregated(
        db: AsyncSession,
        rebalance_requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute multiple user rebalances using order aggregation for efficiency

        Args:
            db: Database session
            rebalance_requests: List of rebalance requests containing:
                - user_id: User UUID
                - smallcase_id: Smallcase UUID
                - suggestions: List of rebalance suggestions
                - rebalance_summary: Optional summary

        Returns:
            Aggregated execution results
        """
        logger.info(f"[Execution] Starting aggregated rebalance for {len(rebalance_requests)} users")

        all_runs = []
        all_orders = []

        # Create runs and orders for all users
        for request in rebalance_requests:
            user_uuid = SmallcaseExecutionService._normalize_uuid(request['user_id'])
            smallcase_uuid = SmallcaseExecutionService._normalize_uuid(request['smallcase_id'])
            suggestions = request['suggestions']
            rebalance_summary = request.get('rebalance_summary')

            try:
                investment = await SmallcaseExecutionService._load_investment(db, user_uuid, smallcase_uuid)
                execution_mode = investment.execution_mode or ExecutionMode.PAPER
                broker_connection = investment.broker_connection

                # Only proceed with live execution if we have broker connection
                if execution_mode != ExecutionMode.LIVE or not broker_connection:
                    logger.info(f"[Execution] Skipping aggregation for user {user_uuid} - not live mode or no broker")
                    continue

                # Create execution run
                run = SmallcaseExecutionRun(
                    user_id=investment.user_id,
                    investment_id=investment.id,
                    broker_connection_id=broker_connection.id,
                    execution_mode=execution_mode,
                    status=ExecutionStatus.PENDING,
                    total_orders=len(suggestions),
                )
                db.add(run)
                await db.flush()  # Get run.id
                all_runs.append(run)

                # Create orders for this run
                for suggestion in suggestions:
                    asset_id = None
                    if suggestion.get("stock_id"):
                        try:
                            asset_id = uuid.UUID(str(suggestion["stock_id"]))
                        except (TypeError, ValueError):
                            asset_id = None

                    order = SmallcaseExecutionOrder(
                        execution_run_id=run.id,
                        asset_id=asset_id,
                        symbol=suggestion.get("symbol"),
                        action=suggestion.get("action"),
                        current_weight=SmallcaseExecutionService._to_decimal(suggestion.get("current_weight")),
                        suggested_weight=SmallcaseExecutionService._to_decimal(suggestion.get("suggested_weight")),
                        weight_change=SmallcaseExecutionService._to_decimal(suggestion.get("weight_change")),
                        status=ExecutionOrderStatus.PENDING,
                        details=suggestion,
                    )
                    db.add(order)
                    all_orders.append(order)

                # Update investment timestamp
                investment.last_rebalanced_at = datetime.now(timezone.utc)

            except Exception as exc:
                logger.error(f"[Execution] Failed to prepare rebalance for user {user_uuid}: {exc}")
                continue

        if not all_runs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid rebalance requests for aggregated execution"
            )

        # Get stock composition for all smallcases involved
        smallcase_ids = list(set(run.investment.smallcase_id for run in all_runs
                                if hasattr(run, 'investment') or run.investment_id))

        # For simplicity, get composition for first smallcase - in production,
        # you might need to handle multiple smallcases differently
        composition = await RebalancingDBService.get_smallcase_composition(
            db, smallcase_ids[0] if smallcase_ids else None
        )

        stock_lookup = {
            uuid.UUID(str(stock["stock_id"])): stock
            for stock in composition.get("stocks", [])
            if stock.get("stock_id")
        }

        # Execute aggregated orders
        try:
            summary = await SmallcaseExecutionService._execute_live_orders_aggregated(
                db=db,
                runs=all_runs,
                all_orders=all_orders,
                stock_lookup=stock_lookup,
                rebalance_summary=rebalance_requests[0].get('rebalance_summary') if rebalance_requests else None
            )

            await db.commit()

            # Refresh all runs to get updated data
            for run in all_runs:
                await db.refresh(run)
                await db.refresh(run, attribute_names=["orders"])

            logger.info(f"[Execution] Aggregated execution completed for {len(all_runs)} users")

            return {
                "aggregated_execution": True,
                "total_users": len(all_runs),
                "total_orders": len(all_orders),
                "execution_summary": summary,
                "runs": [SmallcaseExecutionService._serialize_run(run) for run in all_runs]
            }

        except Exception as exc:
            logger.error(f"[Execution] Aggregated execution failed: {exc}")
            await db.rollback()
            raise

    @staticmethod
    async def _execute_live_orders(
        db: AsyncSession,
        run: SmallcaseExecutionRun,
        orders: List[SmallcaseExecutionOrder],
        investment: UserSmallcaseInvestment,
        broker_connection: UserBrokerConnection,
        stock_lookup: Dict[uuid.UUID, Dict[str, Any]],
        rebalance_summary: Optional[Dict[str, Any]],
        connection_is_paper: bool
    ) -> Dict[str, Any]:
        broker, _ = await BrokerConnectionService.ensure_broker_session(broker_connection)

        submitted = 0
        completed = 0
        skipped = 0
        results = []

        for order in orders:
            stock_info = SmallcaseExecutionService._get_stock_info(order, stock_lookup)
            if not stock_info:
                order.status = ExecutionOrderStatus.FAILED
                order.details = {**(order.details or {}), "error": "Missing stock information"}
                results.append({
                    "order_id": str(order.id),
                    "status": "failed",
                    "error": "Missing stock information",
                })
                continue

            amount_change, quantity, side = SmallcaseExecutionService._calculate_trade_amount(
                order, stock_info, investment
            )

            if quantity <= 0:
                order.status = ExecutionOrderStatus.SIMULATED
                order.details = {**(order.details or {}), "note": "No quantity change required", "mode": "live"}
                results.append({
                    "order_id": str(order.id),
                    "status": "skipped",
                    "reason": "No quantity change required",
                })
                skipped += 1
                continue

            try:
                broker_order = await broker.place_order(
                    symbol=stock_info["symbol"],
                    side=side,
                    quantity=quantity,
                    order_type=BrokerOrderType.MARKET,
                )

                submitted += 1
                order.broker_order_id = broker_order.order_id
                if broker_order.status == BrokerOrderStatus.FILLED:
                    order.status = ExecutionOrderStatus.COMPLETED
                    completed += 1
                else:
                    order.status = ExecutionOrderStatus.SUBMITTED

                order.details = {
                    **(order.details or {}),
                    "mode": "live",
                    "quantity": str(quantity),
                    "amount": str(amount_change),
                    "broker_order_status": broker_order.status.value if hasattr(broker_order.status, "value") else broker_order.status,
                    "paper_connection": connection_is_paper,
                }

                trading_txn = TradingTransaction(
                    user_id=investment.user_id,
                    portfolio_id=investment.portfolio_id,
                    asset_id=order.asset_id,
                    broker_connection_id=broker_connection.id,
                    execution_run_id=run.id,
                    transaction_type=TransactionType.BUY if side == OrderSide.BUY else TransactionType.SELL,
                    quantity=quantity,
                    price_per_unit=Decimal(str(stock_info.get("current_price", 0))),
                    total_amount=amount_change,
                    fees=Decimal("0"),
                    net_amount=amount_change,
                    status=TransactionStatus.EXECUTED if order.status == ExecutionOrderStatus.COMPLETED else TransactionStatus.PENDING,
                    order_type=OrderType.MARKET,
                    notes=f"Smallcase rebalance run {run.id}",
                    external_transaction_id=order.broker_order_id,
                    broker_order_id=order.broker_order_id,
                )
                db.add(trading_txn)

                results.append({
                    "order_id": str(order.id),
                    "broker_order_id": broker_order.order_id,
                    "status": order.status.value if hasattr(order.status, "value") else order.status,
                })

            except Exception as exc:
                order.status = ExecutionOrderStatus.FAILED
                order.details = {**(order.details or {}), "error": str(exc), "mode": "live"}
                results.append({
                    "order_id": str(order.id),
                    "status": "failed",
                    "error": str(exc),
                })

        if completed + skipped == len(orders):
            run.status = ExecutionStatus.COMPLETED
        elif submitted > 0:
            run.status = ExecutionStatus.SUBMITTED
        else:
            run.status = ExecutionStatus.FAILED

        run.completed_orders = completed

        return {
            "mode": ExecutionMode.LIVE.value if not connection_is_paper else ExecutionMode.PAPER.value,
            "type": "broker_paper_execution" if connection_is_paper else "live_execution",
            "submitted_orders": submitted,
            "completed_orders": completed,
            "skipped_orders": skipped,
            "rebalance": rebalance_summary or {},
            "orders": results,
            "paper_connection": connection_is_paper,
        }

    @staticmethod
    def _serialize_order(order: SmallcaseExecutionOrder) -> Dict[str, Any]:
        return {
            "id": str(order.id),
            "execution_run_id": str(order.execution_run_id),
            "asset_id": str(order.asset_id) if order.asset_id else None,
            "symbol": order.symbol,
            "action": order.action,
            "current_weight": float(order.current_weight) if order.current_weight is not None else None,
            "suggested_weight": float(order.suggested_weight) if order.suggested_weight is not None else None,
            "weight_change": float(order.weight_change) if order.weight_change is not None else None,
            "status": order.status.value if hasattr(order.status, "value") else order.status,
            "broker_order_id": order.broker_order_id,
            "metadata": order.details or {},
        }
