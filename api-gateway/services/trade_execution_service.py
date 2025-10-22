"""
Centralized execution pipeline for broker-submitted trades.

This module provides a single entrypoint for submitting user orders to any
supported broker (Zerodha, Alpaca, etc.) and for applying broker execution
events back to portfolio state once fills are confirmed.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models import TradingTransaction, TransactionStatus, OrderType, TransactionType
from services.portfolio_performance_service import PortfolioPerformanceService

logger = logging.getLogger(__name__)


class BrokerSubmitter(Protocol):
    """Protocol implemented by broker adapters."""

    async def place_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: OrderType,
        price: Optional[Decimal] = None,
        reference_id: Optional[str] = None,
    ) -> Any:  # pragma: no cover - protocol definition
        ...


@dataclass
class SubmissionResult:
    transaction: TradingTransaction
    broker_order_id: Optional[str]
    status: TransactionStatus
    submitted_at: datetime


class TradingExecutionService:
    """
    Shared trade execution pipeline.

    Current implementation keeps behaviour compatible with the existing system,
    while exposing clear hooks for future broker fill reconciliation.
    """

    @staticmethod
    async def submit_order(
        *,
        session: AsyncSession,
        transaction: TradingTransaction,
        broker: BrokerSubmitter,
        submission_payload: Dict[str, Any],
    ) -> SubmissionResult:
        """
        Submit an order to the broker and update the transaction with submission
        metadata. Portfolio mutations are **not** performed here; those are
        applied once a fill confirmation is processed.
        """
        logger.info(
            "[Execution] Submitting order %s to broker %s",
            transaction.id,
            broker.__class__.__name__,
        )

        broker_response = await broker.place_order(**submission_payload)

        broker_order_id = getattr(broker_response, "order_id", None)
        transaction.status = TransactionStatus.PENDING
        transaction.broker_order_id = broker_order_id
        transaction.external_transaction_id = broker_order_id
        transaction.updated_at = datetime.now(timezone.utc)

        await session.flush()

        return SubmissionResult(
            transaction=transaction,
            broker_order_id=broker_order_id,
            status=transaction.status,
            submitted_at=transaction.updated_at,
        )

    @staticmethod
    async def finalize_fill(
        *,
        session: AsyncSession,
        transaction: TradingTransaction,
        filled_quantity: Decimal,
        fill_price: Decimal,
        fees: Decimal,
        fill_status: TransactionStatus,
        fill_metadata: Optional[Dict[str, Any]] = None,
        refresh_snapshot: bool = True,
    ) -> TradingTransaction:
        """
        Apply a confirmed broker fill to the portfolio.

        This keeps all portfolio mutations behind a single method so manual
        trades, smallcase rebalance fills, or bot-driven executions behave
        consistently.
        """
        if fill_status not in {TransactionStatus.EXECUTED, TransactionStatus.PARTIAL}:
            logger.warning(
                "[Execution] Unexpected fill status %s for transaction %s",
                fill_status,
                transaction.id,
            )

        transaction.quantity = filled_quantity
        transaction.price_per_unit = fill_price
        transaction.total_amount = filled_quantity * fill_price
        transaction.fees = fees
        transaction.net_amount = (
            transaction.total_amount + fees
            if transaction.transaction_type == TransactionType.BUY
            else transaction.total_amount - fees
        )
        transaction.status = fill_status
        transaction.settlement_date = datetime.now(timezone.utc)
        transaction.updated_at = transaction.settlement_date

        if fill_metadata:
            # Persist arbitrary execution context for future reconciliation.
            notes = transaction.notes or ""
            extra = f" | fill: {fill_metadata}"
            transaction.notes = f"{notes}{extra}" if notes else extra

        await session.flush()

        if (
            transaction.status == TransactionStatus.EXECUTED
            and transaction.portfolio_id
            and transaction.asset_id
        ):
            await session.execute(
                text(
                    """
                    UPDATE portfolio_holdings
                    SET order_status = 'filled'
                    WHERE portfolio_id = :portfolio_id
                      AND asset_id = :asset_id
                    """
                ),
                {
                    "portfolio_id": str(transaction.portfolio_id),
                    "asset_id": str(transaction.asset_id),
                },
            )

        if refresh_snapshot:
            await PortfolioPerformanceService.refresh_snapshot(
                transaction.portfolio_id,
                transaction.user_id,
            )

        return transaction
