"""
Portfolio performance service for tracking and calculating portfolio metrics
"""
import logging
import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, text, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session


logger = logging.getLogger(__name__)


class PortfolioPerformanceService:
    """Service class for portfolio performance tracking and calculations"""

    @staticmethod
    async def refresh_snapshot(
        portfolio_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Ensure the latest daily snapshot exists for the given portfolio.

        Opens a fresh DB session to avoid interfering with active transactions.
        """
        async with get_db_session() as session:
            resolved_portfolio_id = uuid.UUID(str(portfolio_id))

            resolved_user_id = uuid.UUID(str(user_id)) if user_id else None
            if resolved_user_id is None:
                result = await session.execute(
                    text("SELECT user_id FROM portfolios WHERE id = :portfolio_id"),
                    {"portfolio_id": str(resolved_portfolio_id)}
                )
                row = result.fetchone()
                if not row or not row.user_id:
                    return
                resolved_user_id = uuid.UUID(str(row.user_id))

            await PortfolioPerformanceService.calculate_daily_snapshot(
                session,
                resolved_portfolio_id,
                resolved_user_id
            )

    @staticmethod
    async def calculate_daily_snapshot(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        user_id: uuid.UUID,
        snapshot_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate and store daily portfolio value snapshot

        Args:
            db: Database session
            portfolio_id: Portfolio UUID
            user_id: User UUID
            snapshot_date: Date for snapshot (defaults to today)

        Returns:
            Dict with snapshot data
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        # Get portfolio cash balance and deposit tracking
        portfolio_query = await db.execute(
            text("""
                SELECT
                    cash_balance,
                    total_deposits,
                    total_withdrawals,
                    created_at
                FROM portfolios
                WHERE id = :portfolio_id AND user_id = :user_id
            """),
            {"portfolio_id": str(portfolio_id), "user_id": str(user_id)}
        )
        portfolio_row = portfolio_query.fetchone()

        if not portfolio_row:
            raise ValueError(f"Portfolio {portfolio_id} not found for user {user_id}")

        cash_balance = Decimal(str(portfolio_row.cash_balance or 0))
        total_deposits = Decimal(str(portfolio_row.total_deposits or 0))
        total_withdrawals = Decimal(str(portfolio_row.total_withdrawals or 0))

        # Calculate holdings value from portfolio_holdings
        holdings_query = await db.execute(
            text("""
                SELECT COALESCE(SUM(current_value), 0) as holdings_value
                FROM portfolio_holdings
                WHERE portfolio_id = :portfolio_id
                AND (order_status IS NULL OR order_status IN ('filled', 'cancelled'))
            """),
            {"portfolio_id": str(portfolio_id)}
        )
        holdings_row = holdings_query.fetchone()
        holdings_value = Decimal(str(holdings_row.holdings_value or 0))

        # Calculate total value
        total_value = cash_balance + holdings_value

        # Calculate total invested (deposits - withdrawals)
        total_invested = total_deposits - total_withdrawals

        # Calculate total P&L
        total_pnl = total_value - total_invested

        # Get previous snapshot for day change calculation
        prev_snapshot_query = await db.execute(
            text("""
                SELECT total_value
                FROM portfolio_value_snapshots
                WHERE portfolio_id = :portfolio_id
                AND snapshot_date < :snapshot_date
                ORDER BY snapshot_date DESC
                LIMIT 1
            """),
            {"portfolio_id": str(portfolio_id), "snapshot_date": snapshot_date}
        )
        prev_snapshot_row = prev_snapshot_query.fetchone()

        day_change = Decimal('0')
        day_change_percent = Decimal('0')

        if prev_snapshot_row:
            prev_value = Decimal(str(prev_snapshot_row.total_value))
            if prev_value > 0:
                day_change = total_value - prev_value
                day_change_percent = (day_change / prev_value) * 100

        # Insert or update snapshot
        await db.execute(
            text("""
                INSERT INTO portfolio_value_snapshots (
                    portfolio_id, user_id, snapshot_date,
                    total_value, cash_balance, holdings_value,
                    total_invested, total_pnl,
                    day_change, day_change_percent,
                    created_at, updated_at
                )
                VALUES (
                    :portfolio_id, :user_id, :snapshot_date,
                    :total_value, :cash_balance, :holdings_value,
                    :total_invested, :total_pnl,
                    :day_change, :day_change_percent,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (portfolio_id, snapshot_date)
                DO UPDATE SET
                    total_value = EXCLUDED.total_value,
                    cash_balance = EXCLUDED.cash_balance,
                    holdings_value = EXCLUDED.holdings_value,
                    total_invested = EXCLUDED.total_invested,
                    total_pnl = EXCLUDED.total_pnl,
                    day_change = EXCLUDED.day_change,
                    day_change_percent = EXCLUDED.day_change_percent,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {
                "portfolio_id": str(portfolio_id),
                "user_id": str(user_id),
                "snapshot_date": snapshot_date,
                "total_value": float(total_value),
                "cash_balance": float(cash_balance),
                "holdings_value": float(holdings_value),
                "total_invested": float(total_invested),
                "total_pnl": float(total_pnl),
                "day_change": float(day_change),
                "day_change_percent": float(day_change_percent)
            }
        )

        await db.commit()

        return {
            "snapshot_date": snapshot_date.isoformat(),
            "total_value": float(total_value),
            "cash_balance": float(cash_balance),
            "holdings_value": float(holdings_value),
            "total_invested": float(total_invested),
            "total_pnl": float(total_pnl),
            "day_change": float(day_change),
            "day_change_percent": float(day_change_percent)
        }

    @staticmethod
    async def get_performance_data(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        user_id: uuid.UUID,
        timeframe: str = "1D"
    ) -> Dict[str, Any]:
        """
        Get portfolio performance data for specified timeframe

        Args:
            db: Database session
            portfolio_id: Portfolio UUID
            user_id: User UUID
            timeframe: One of: 1D, 1W, 1M, 3M, 1Y, YTD, OPEN, ALL

        Returns:
            Dict with chart data and performance metrics
        """
        # Get portfolio creation date for OPEN/ALL timeframes
        portfolio_query = await db.execute(
            text("""
                SELECT created_at, total_deposits, total_withdrawals
                FROM portfolios
                WHERE id = :portfolio_id AND user_id = :user_id
            """),
            {"portfolio_id": str(portfolio_id), "user_id": str(user_id)}
        )
        portfolio_row = portfolio_query.fetchone()

        if not portfolio_row:
            raise ValueError(f"Portfolio {portfolio_id} not found for user {user_id}")

        portfolio_created = portfolio_row.created_at.date()
        today = date.today()

        # Calculate start date based on timeframe
        if timeframe == "1D":
            start_date = today - timedelta(days=1)
        elif timeframe == "1W":
            start_date = today - timedelta(days=7)
        elif timeframe == "1M":
            start_date = today - timedelta(days=30)
        elif timeframe == "3M":
            start_date = today - timedelta(days=90)
        elif timeframe == "1Y":
            start_date = today - timedelta(days=365)
        elif timeframe == "YTD":
            start_date = date(today.year, 1, 1)
        elif timeframe in ["OPEN", "ALL"]:
            start_date = portfolio_created
        else:
            # Default to 1 day
            start_date = today - timedelta(days=1)

        # Ensure today's snapshot exists so charts include latest data
        try:
            await PortfolioPerformanceService.calculate_daily_snapshot(
                db,
                portfolio_id,
                user_id,
                snapshot_date=today
            )
        except Exception as snapshot_error:
            # Do not fail the performance request if snapshot update fails
            logger.warning(
                "Failed to create today's snapshot for portfolio %s: %s",
                portfolio_id,
                snapshot_error
            )

        # Fetch snapshots for the time period
        snapshots_query = await db.execute(
            text("""
                SELECT
                    snapshot_date,
                    total_value,
                    total_invested,
                    total_pnl,
                    day_change,
                    day_change_percent
                FROM portfolio_value_snapshots
                WHERE portfolio_id = :portfolio_id
                AND snapshot_date >= :start_date
                AND snapshot_date <= :end_date
                ORDER BY snapshot_date ASC
            """),
            {
                "portfolio_id": str(portfolio_id),
                "start_date": start_date,
                "end_date": today
            }
        )
        snapshots = snapshots_query.fetchall()

        # Format chart data
        chart_data = []
        for snapshot in snapshots:
            chart_data.append({
                "date": snapshot.snapshot_date.isoformat(),
                "value": float(snapshot.total_value),
                "invested": float(snapshot.total_invested),
                "pnl": float(snapshot.total_pnl)
            })

        # Calculate metrics
        current_value = Decimal('0')
        period_start_value = Decimal('0')
        period_high = Decimal('0')
        period_low = Decimal('999999999')
        total_invested = Decimal('0')

        if snapshots:
            current_value = Decimal(str(snapshots[-1].total_value))
            period_start_value = Decimal(str(snapshots[0].total_value))
            total_invested = Decimal(str(snapshots[-1].total_invested))

            for snapshot in snapshots:
                value = Decimal(str(snapshot.total_value))
                if value > period_high:
                    period_high = value
                if value < period_low:
                    period_low = value

        # Calculate returns
        period_return = current_value - period_start_value
        period_return_percent = Decimal('0')
        if period_start_value > 0:
            period_return_percent = (period_return / period_start_value) * 100

        # Calculate total return (vs invested)
        total_return = current_value - total_invested
        total_return_percent = Decimal('0')
        if total_invested > 0:
            total_return_percent = (total_return / total_invested) * 100

        return {
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": today.isoformat(),
            "chart_data": chart_data,
            "metrics": {
                "current_value": float(current_value),
                "total_invested": float(total_invested),
                "period_return": float(period_return),
                "period_return_percent": float(period_return_percent),
                "total_return": float(total_return),
                "total_return_percent": float(total_return_percent),
                "period_high": float(period_high) if period_high < 999999999 else float(current_value),
                "period_low": float(period_low) if period_low < 999999999 else float(current_value)
            }
        }

    @staticmethod
    async def backfill_snapshots(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        user_id: uuid.UUID,
        start_date: date = None,
        end_date: date = None
    ) -> int:
        """
        Backfill historical snapshots for a portfolio

        Args:
            db: Database session
            portfolio_id: Portfolio UUID
            user_id: User UUID
            start_date: Start date for backfill (defaults to portfolio creation)
            end_date: End date for backfill (defaults to today)

        Returns:
            Number of snapshots created
        """
        if end_date is None:
            end_date = date.today()

        if start_date is None:
            # Get portfolio creation date
            portfolio_query = await db.execute(
                text("""
                    SELECT created_at
                    FROM portfolios
                    WHERE id = :portfolio_id AND user_id = :user_id
                """),
                {"portfolio_id": str(portfolio_id), "user_id": str(user_id)}
            )
            portfolio_row = portfolio_query.fetchone()
            if portfolio_row:
                start_date = portfolio_row.created_at.date()
            else:
                raise ValueError(f"Portfolio {portfolio_id} not found")

        # Generate snapshots for each day
        snapshots_created = 0
        current_date = start_date

        while current_date <= end_date:
            try:
                await PortfolioPerformanceService.calculate_daily_snapshot(
                    db, portfolio_id, user_id, current_date
                )
                snapshots_created += 1
            except Exception as e:
                print(f"Error creating snapshot for {current_date}: {e}")

            current_date += timedelta(days=1)

        return snapshots_created
