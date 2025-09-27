"""Service for handling smallcase position closures across all execution modes."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from brokers import OrderSide, OrderType as BrokerOrderType
from models import (
    ExecutionMode,
    ExecutionOrderStatus,
    ExecutionStatus,
    SmallcaseExecutionOrder,
    SmallcaseExecutionRun,
    TradingTransaction,
    TransactionType,
    UserBrokerConnection,
    UserSmallcaseInvestment,
    Asset,
)
from services.broker_connection_service import BrokerConnectionService
from services.order_aggregation_service import OrderAggregationService
from services.rebalancing_db_service import RebalancingDBService
from services.trading_service import TradingService

logger = logging.getLogger(__name__)


class SmallcaseClosureService:
    """Service for closing smallcase positions with comprehensive tracking."""

    @staticmethod
    def _normalize_uuid(value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID provided"
            ) from exc

    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """Recursively serialize objects to be JSON-safe, converting datetime to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: SmallcaseClosureService._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [SmallcaseClosureService._serialize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return SmallcaseClosureService._serialize_for_json(obj.__dict__)
        else:
            return obj

    @staticmethod
    async def get_investment_with_holdings(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        investment_id: uuid.UUID | str
    ) -> UserSmallcaseInvestment:
        """Get user's smallcase investment with current holdings."""
        user_uuid = SmallcaseClosureService._normalize_uuid(user_id)
        investment_uuid = SmallcaseClosureService._normalize_uuid(investment_id)

        result = await db.execute(
            select(UserSmallcaseInvestment)
            .options(
                selectinload(UserSmallcaseInvestment.broker_connection),
                selectinload(UserSmallcaseInvestment.smallcase),
                selectinload(UserSmallcaseInvestment.portfolio)
            )
            .where(
                UserSmallcaseInvestment.id == investment_uuid,
                UserSmallcaseInvestment.user_id == user_uuid,
                UserSmallcaseInvestment.status == "active"
            )
        )
        investment = result.scalars().first()
        if not investment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active smallcase investment not found"
            )
        return investment

    @staticmethod
    async def get_current_holdings(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        smallcase_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get current holdings for a smallcase in the portfolio."""
        result = await db.execute(text("""
            SELECT
                ph.id,
                ph.asset_id,
                a.symbol,
                a.name,
                ph.quantity,
                ph.average_cost,
                ph.total_cost,
                ph.current_value,
                ph.unrealized_pnl,
                a.current_price,
                sc.weight_percentage as target_weight
            FROM portfolio_holdings ph
            JOIN assets a ON ph.asset_id = a.id
            JOIN smallcase_constituents sc ON a.id = sc.asset_id
            WHERE ph.portfolio_id = :portfolio_id
            AND sc.smallcase_id = :smallcase_id
            AND sc.is_active = true
            AND ph.quantity > 0
        """), {
            "portfolio_id": str(portfolio_id),
            "smallcase_id": str(smallcase_id)
        })

        holdings = []
        for row in result.fetchall():
            holdings.append({
                "holding_id": row.id,
                "asset_id": row.asset_id,
                "symbol": row.symbol,
                "name": row.name,
                "quantity": float(row.quantity),
                "average_cost": float(row.average_cost),
                "total_cost": float(row.total_cost),
                "current_value": float(row.current_value),
                "unrealized_pnl": float(row.unrealized_pnl),
                "current_price": float(row.current_price) if row.current_price else 0.0,
                "target_weight": float(row.target_weight)
            })

        return holdings

    @staticmethod
    async def preview_closure(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        investment_id: uuid.UUID | str,
        closure_percentage: float = 100.0
    ) -> Dict[str, Any]:
        """Preview the closure of a smallcase position."""
        investment = await SmallcaseClosureService.get_investment_with_holdings(
            db, user_id, investment_id
        )

        holdings = await SmallcaseClosureService.get_current_holdings(
            db, investment.portfolio_id, investment.smallcase_id
        )

        if not holdings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No holdings found for this smallcase investment. This may indicate an issue with the investment creation process."
            )

        # Calculate closure values
        total_current_value = sum(h["current_value"] for h in holdings)
        closure_value = total_current_value * (closure_percentage / 100)

        # Calculate P&L
        investment_amount = float(investment.investment_amount)
        if closure_percentage == 100.0:
            proportional_investment = investment_amount
        else:
            proportional_investment = investment_amount * (closure_percentage / 100)

        estimated_pnl = closure_value - proportional_investment
        roi_percentage = (estimated_pnl / proportional_investment * 100) if proportional_investment > 0 else 0

        # Calculate holding period
        holding_days = (datetime.now(timezone.utc) - investment.invested_at).days

        # Prepare holdings for closure
        closure_holdings = []
        for holding in holdings:
            closure_qty = holding["quantity"] * (closure_percentage / 100)
            closure_value_per_holding = holding["current_value"] * (closure_percentage / 100)

            closure_holdings.append({
                **holding,
                "closure_quantity": closure_qty,
                "closure_value": closure_value_per_holding,
                "estimated_proceeds": closure_qty * holding["current_price"]
            })

        return {
            "investment_id": str(investment.id),
            "smallcase_name": investment.smallcase.name,
            "closure_percentage": closure_percentage,
            "investment_amount": investment_amount,
            "proportional_investment": proportional_investment,
            "current_value": total_current_value,
            "closure_value": closure_value,
            "estimated_pnl": estimated_pnl,
            "roi_percentage": roi_percentage,
            "holding_period_days": holding_days,
            "execution_mode": investment.execution_mode,
            "holdings_to_close": closure_holdings,
            "total_holdings": len(holdings),
            "broker_connection_id": str(investment.broker_connection_id) if investment.broker_connection_id else None
        }

    @staticmethod
    async def close_position(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        investment_id: uuid.UUID | str,
        closure_reason: str = "manual_close",
        closure_percentage: float = 100.0
    ) -> Dict[str, Any]:
        """Close a smallcase position (full or partial)."""
        logger.info(
            f"[Closure] Starting closure for user={user_id} investment={investment_id} "
            f"percentage={closure_percentage}% reason={closure_reason}"
        )

        try:
            # Get investment and preview closure
            preview = await SmallcaseClosureService.preview_closure(
                db, user_id, investment_id, closure_percentage
            )

            investment = await SmallcaseClosureService.get_investment_with_holdings(
                db, user_id, investment_id
            )

            # Determine execution approach
            execution_mode = investment.execution_mode or ExecutionMode.PAPER
            broker_connection = investment.broker_connection
            use_broker = execution_mode == ExecutionMode.LIVE or (broker_connection and broker_connection.paper_trading)

            # Create execution run for tracking
            now = datetime.now(timezone.utc)
            run = SmallcaseExecutionRun(
                user_id=investment.user_id,
                investment_id=investment.id,
                broker_connection_id=investment.broker_connection_id,
                execution_mode=execution_mode,
                status=ExecutionStatus.PENDING,
                total_orders=len(preview["holdings_to_close"]),
                started_at=now
            )
            db.add(run)
            await db.flush()

            # Execute closure orders
            if not use_broker:
                summary = await SmallcaseClosureService._execute_paper_closure(
                    db, run, investment, preview, closure_reason
                )
            else:
                summary = await SmallcaseClosureService._execute_broker_closure(
                    db, run, investment, preview, closure_reason, broker_connection
                )

            # Update execution run
            run.summary = SmallcaseClosureService._serialize_for_json(summary)
            run.completed_at = now
            run.completed_orders = summary.get("completed_orders", 0)

            # Update investment status
            if closure_percentage >= 100.0:
                investment.status = "sold"
                investment.closed_at = now
                investment.exit_value = Decimal(str(preview["closure_value"]))
                investment.realized_pnl = Decimal(str(preview["estimated_pnl"]))
                investment.closure_reason = closure_reason

                # Create position history entry
                await SmallcaseClosureService._create_position_history(db, investment, preview)
            else:
                investment.status = "partial"
                # For partial closures, we might want to track cumulative closure data

            await db.commit()

            logger.info(
                f"[Closure] Completed closure for investment={investment_id} "
                f"status={summary.get('status')} orders={summary.get('completed_orders')}"
            )

            return {
                "success": True,
                "investment_id": str(investment.id),
                "execution_run_id": str(run.id),
                "closure_percentage": closure_percentage,
                "summary": summary,
                "new_status": investment.status
            }

        except Exception as exc:
            await db.rollback()
            logger.error(f"[Closure] Failed to close position: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to close position: {str(exc)}"
            ) from exc

    @staticmethod
    async def _execute_paper_closure(
        db: AsyncSession,
        run: SmallcaseExecutionRun,
        investment: UserSmallcaseInvestment,
        preview: Dict[str, Any],
        closure_reason: str
    ) -> Dict[str, Any]:
        """Execute closure in paper mode."""
        logger.info(f"[Closure] Executing paper closure for investment={investment.id}")

        completed = 0
        failed = 0
        results = []

        for holding in preview["holdings_to_close"]:
            try:
                # Create sell transaction
                transaction = TradingTransaction(
                    user_id=str(investment.user_id),
                    portfolio_id=investment.portfolio_id,
                    asset_id=uuid.UUID(holding["asset_id"]),
                    broker_connection_id=investment.broker_connection_id,
                    execution_run_id=run.id,
                    transaction_type=TransactionType.SELL,
                    quantity=Decimal(str(holding["closure_quantity"])),
                    price_per_unit=Decimal(str(holding["current_price"])),
                    total_amount=Decimal(str(holding["estimated_proceeds"])),
                    fees=Decimal("0"),
                    net_amount=Decimal(str(holding["estimated_proceeds"])),
                    order_type="market",
                    notes=f"Paper closure: {closure_reason}",
                    status="executed"
                )
                db.add(transaction)

                # Create execution order for tracking
                order = SmallcaseExecutionOrder(
                    execution_run_id=run.id,
                    asset_id=uuid.UUID(holding["asset_id"]),
                    symbol=holding["symbol"],
                    action="sell",
                    status=ExecutionOrderStatus.COMPLETED,
                    details={
                        "quantity": holding["closure_quantity"],
                        "price": holding["current_price"],
                        "value": holding["estimated_proceeds"],
                        "mode": "paper_closure",
                        "reason": closure_reason
                    }
                )
                db.add(order)

                completed += 1
                results.append({
                    "symbol": holding["symbol"],
                    "quantity": holding["closure_quantity"],
                    "price": holding["current_price"],
                    "value": holding["estimated_proceeds"],
                    "status": "completed"
                })

            except Exception as exc:
                logger.error(f"[Closure] Failed to create paper transaction for {holding['symbol']}: {exc}")
                failed += 1
                results.append({
                    "symbol": holding["symbol"],
                    "status": "failed",
                    "error": str(exc)
                })

        run.status = ExecutionStatus.COMPLETED if failed == 0 else ExecutionStatus.SUBMITTED

        return {
            "mode": "paper_closure",
            "status": "completed" if failed == 0 else "partial",
            "completed_orders": completed,
            "failed_orders": failed,
            "total_orders": len(preview["holdings_to_close"]),
            "estimated_proceeds": preview["closure_value"],
            "estimated_pnl": preview["estimated_pnl"],
            "closure_reason": closure_reason,
            "results": results
        }

    @staticmethod
    async def _execute_broker_closure(
        db: AsyncSession,
        run: SmallcaseExecutionRun,
        investment: UserSmallcaseInvestment,
        preview: Dict[str, Any],
        closure_reason: str,
        broker_connection: UserBrokerConnection
    ) -> Dict[str, Any]:
        """Execute closure through broker (paper or live)."""
        logger.info(f"[Closure] Executing broker closure for investment={investment.id}")

        # Get broker session
        broker, _ = await BrokerConnectionService.ensure_broker_session(broker_connection)

        completed = 0
        submitted = 0
        failed = 0
        results = []

        for holding in preview["holdings_to_close"]:
            try:
                # Place sell order through broker
                broker_order = await broker.place_order(
                    symbol=holding["symbol"],
                    side=OrderSide.SELL,
                    quantity=Decimal(str(holding["closure_quantity"])),
                    order_type=BrokerOrderType.MARKET
                )

                # Create trading transaction
                transaction = TradingTransaction(
                    user_id=str(investment.user_id),
                    portfolio_id=investment.portfolio_id,
                    asset_id=uuid.UUID(holding["asset_id"]),
                    broker_connection_id=investment.broker_connection_id,
                    execution_run_id=run.id,
                    transaction_type=TransactionType.SELL,
                    quantity=Decimal(str(holding["closure_quantity"])),
                    price_per_unit=Decimal(str(holding["current_price"])),
                    total_amount=Decimal(str(holding["estimated_proceeds"])),
                    fees=Decimal("0"),
                    net_amount=Decimal(str(holding["estimated_proceeds"])),
                    broker_order_id=broker_order.order_id,
                    order_type="market",
                    notes=f"Broker closure: {closure_reason}",
                    status="pending"
                )
                db.add(transaction)

                # Create execution order
                order = SmallcaseExecutionOrder(
                    execution_run_id=run.id,
                    asset_id=uuid.UUID(holding["asset_id"]),
                    symbol=holding["symbol"],
                    action="sell",
                    status=ExecutionOrderStatus.SUBMITTED,
                    broker_order_id=broker_order.order_id,
                    details={
                        "quantity": holding["closure_quantity"],
                        "price": holding["current_price"],
                        "value": holding["estimated_proceeds"],
                        "mode": "broker_closure",
                        "reason": closure_reason,
                        "broker_paper": broker_connection.paper_trading
                    }
                )
                db.add(order)

                if broker_order.status and "filled" in broker_order.status.value.lower():
                    completed += 1
                    order.status = ExecutionOrderStatus.COMPLETED
                    transaction.status = "executed"
                else:
                    submitted += 1

                results.append({
                    "symbol": holding["symbol"],
                    "quantity": holding["closure_quantity"],
                    "broker_order_id": broker_order.order_id,
                    "status": "submitted",
                })

            except Exception as exc:
                logger.error(f"[Closure] Failed to place broker order for {holding['symbol']}: {exc}")
                failed += 1
                results.append({
                    "symbol": holding["symbol"],
                    "status": "failed",
                    "error": str(exc)
                })

        if completed == len(preview["holdings_to_close"]):
            run.status = ExecutionStatus.COMPLETED
        elif submitted > 0 or completed > 0:
            run.status = ExecutionStatus.SUBMITTED
        else:
            run.status = ExecutionStatus.FAILED

        return {
            "mode": "broker_closure",
            "status": "completed" if completed == len(preview["holdings_to_close"]) else "submitted",
            "completed_orders": completed,
            "submitted_orders": submitted,
            "failed_orders": failed,
            "total_orders": len(preview["holdings_to_close"]),
            "estimated_proceeds": preview["closure_value"],
            "estimated_pnl": preview["estimated_pnl"],
            "closure_reason": closure_reason,
            "broker_paper": broker_connection.paper_trading,
            "results": results
        }

    @staticmethod
    async def _create_position_history(
        db: AsyncSession,
        investment: UserSmallcaseInvestment,
        preview: Dict[str, Any]
    ):
        """Create position history entry for closed investment."""
        # Calculate holding period
        holding_days = (datetime.now(timezone.utc) - investment.invested_at).days

        # Calculate ROI
        roi_percentage = (preview["estimated_pnl"] / float(investment.investment_amount) * 100) if investment.investment_amount > 0 else 0

        history_entry = await db.execute(text("""
            INSERT INTO user_smallcase_position_history (
                id, user_id, smallcase_id, portfolio_id,
                investment_amount, units_purchased, purchase_price,
                exit_value, exit_price, realized_pnl,
                holding_period_days, roi_percentage,
                invested_at, closed_at,
                closure_reason, execution_mode, broker_connection_id
            ) VALUES (
                :id, :user_id, :smallcase_id, :portfolio_id,
                :investment_amount, :units_purchased, :purchase_price,
                :exit_value, :exit_price, :realized_pnl,
                :holding_period_days, :roi_percentage,
                :invested_at, :closed_at,
                :closure_reason, :execution_mode, :broker_connection_id
            )
        """), {
            "id": str(uuid.uuid4()),
            "user_id": str(investment.user_id),
            "smallcase_id": str(investment.smallcase_id),
            "portfolio_id": str(investment.portfolio_id),
            "investment_amount": float(investment.investment_amount),
            "units_purchased": float(investment.units_purchased),
            "purchase_price": float(investment.purchase_price),
            "exit_value": preview["closure_value"],
            "exit_price": preview["closure_value"] / float(investment.units_purchased) if investment.units_purchased > 0 else 0,
            "realized_pnl": preview["estimated_pnl"],
            "holding_period_days": holding_days,
            "roi_percentage": roi_percentage,
            "invested_at": investment.invested_at,
            "closed_at": datetime.now(timezone.utc),
            "closure_reason": investment.closure_reason,
            "execution_mode": investment.execution_mode.value if hasattr(investment.execution_mode, 'value') else investment.execution_mode,
            "broker_connection_id": str(investment.broker_connection_id) if investment.broker_connection_id else None
        })

        logger.info(f"[Closure] Created position history for investment={investment.id}")

    @staticmethod
    async def execute_bulk_closures_aggregated(
        db: AsyncSession,
        closure_requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute multiple investment closures using order aggregation for efficiency

        Args:
            db: Database session
            closure_requests: List of closure requests containing:
                - user_id: User UUID
                - investment_id: Investment UUID
                - closure_reason: Reason for closure

        Returns:
            Aggregated closure results
        """
        logger.info(f"[BulkClosure] Starting aggregated closure for {len(closure_requests)} investments")

        all_runs = []
        all_orders = []
        closure_previews = []

        # Prepare closures for all investments
        for request in closure_requests:
            user_uuid = SmallcaseClosureService._normalize_uuid(request['user_id'])
            investment_uuid = SmallcaseClosureService._normalize_uuid(request['investment_id'])
            closure_reason = request.get('closure_reason', 'bulk_closure')

            try:
                # Get investment with holdings
                investment = await SmallcaseClosureService.get_investment_with_holdings(
                    db, user_uuid, investment_uuid
                )

                # Only proceed with live execution if we have broker connection
                if investment.execution_mode != ExecutionMode.LIVE or not investment.broker_connection:
                    logger.info(f"[BulkClosure] Skipping aggregation for investment {investment_uuid} - not live mode")
                    continue

                # Get closure preview
                holdings = await SmallcaseClosureService.get_current_holdings(
                    db, investment.portfolio_id, investment.smallcase_id
                )

                if not holdings:
                    logger.warning(f"[BulkClosure] No holdings found for investment {investment_uuid}")
                    continue

                preview = await SmallcaseClosureService.calculate_closure_preview(
                    db, investment, holdings
                )

                closure_previews.append({
                    'investment': investment,
                    'preview': preview,
                    'closure_reason': closure_reason
                })

                # Create execution run
                run = SmallcaseExecutionRun(
                    user_id=investment.user_id,
                    investment_id=investment.id,
                    broker_connection_id=investment.broker_connection_id,
                    execution_mode=investment.execution_mode,
                    status=ExecutionStatus.PENDING,
                    total_orders=len(preview["holdings_to_close"]),
                )
                db.add(run)
                await db.flush()  # Get run.id
                all_runs.append(run)

                # Create sell orders for each holding
                for holding in preview["holdings_to_close"]:
                    order = SmallcaseExecutionOrder(
                        execution_run_id=run.id,
                        asset_id=uuid.UUID(holding["asset_id"]),
                        symbol=holding["symbol"],
                        action="sell",
                        current_weight=None,
                        suggested_weight=Decimal('0'),  # Target is 0% for closure
                        weight_change=Decimal(str(-holding["current_weight"])),  # Negative for sell
                        status=ExecutionOrderStatus.PENDING,
                        details={
                            "closure_quantity": holding["closure_quantity"],
                            "current_price": holding["current_price"],
                            "estimated_proceeds": holding["estimated_proceeds"],
                            "closure_reason": closure_reason,
                            "mode": "aggregated_closure"
                        }
                    )
                    db.add(order)
                    all_orders.append(order)

            except Exception as exc:
                logger.error(f"[BulkClosure] Failed to prepare closure for investment {investment_uuid}: {exc}")
                continue

        if not all_runs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid closure requests for aggregated execution"
            )

        # Build stock lookup for aggregation service
        stock_lookup = {}
        for preview_data in closure_previews:
            for holding in preview_data['preview']["holdings_to_close"]:
                asset_id = uuid.UUID(holding["asset_id"])
                stock_lookup[asset_id] = {
                    "stock_id": holding["asset_id"],
                    "symbol": holding["symbol"],
                    "current_price": holding["current_price"],
                    "company_name": holding.get("company_name", holding["symbol"])
                }

        # Build investments lookup by user
        investments_by_user = {}
        for preview_data in closure_previews:
            investment = preview_data['investment']
            investments_by_user[investment.user_id] = investment

        # Execute aggregated orders
        try:
            aggregation_results = await OrderAggregationService.aggregate_and_execute_orders(
                db, all_orders, stock_lookup, investments_by_user
            )

            # Update run statuses based on results
            for run in all_runs:
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

            # Update investment statuses for successful closures
            for i, run in enumerate(all_runs):
                if run.status == ExecutionStatus.COMPLETED:
                    preview_data = closure_previews[i]
                    investment = preview_data['investment']

                    # Mark investment as closed
                    investment.status = "sold"
                    investment.closed_at = datetime.now(timezone.utc)
                    investment.closure_reason = preview_data['closure_reason']
                    investment.exit_value = Decimal(str(preview_data['preview']["closure_value"]))
                    investment.realized_pnl = Decimal(str(preview_data['preview']["estimated_pnl"]))

                    # Create position history entry
                    await SmallcaseClosureService._create_position_history(
                        db, investment, preview_data['preview']
                    )

            await db.commit()

            # Refresh all runs to get updated data
            for run in all_runs:
                await db.refresh(run)
                await db.refresh(run, attribute_names=["orders"])

            logger.info(f"[BulkClosure] Aggregated closure completed for {len(all_runs)} investments")

            return {
                "aggregated_closure": True,
                "total_investments": len(all_runs),
                "total_orders": len(all_orders),
                "execution_results": aggregation_results['execution_results'],
                "aggregation_summary": aggregation_results['aggregation_summary'],
                "runs": [SmallcaseClosureService._serialize_run(run) for run in all_runs]
            }

        except Exception as exc:
            logger.error(f"[BulkClosure] Aggregated closure execution failed: {exc}")
            await db.rollback()
            raise

    @staticmethod
    def _serialize_run(run: SmallcaseExecutionRun) -> Dict[str, Any]:
        """Serialize execution run for JSON response"""
        return {
            "id": str(run.id),
            "user_id": str(run.user_id),
            "investment_id": str(run.investment_id),
            "broker_connection_id": str(run.broker_connection_id) if run.broker_connection_id else None,
            "execution_mode": run.execution_mode.value if hasattr(run.execution_mode, "value") else run.execution_mode,
            "status": run.status.value if hasattr(run.status, "value") else run.status,
            "total_orders": run.total_orders,
            "completed_orders": run.completed_orders,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        }