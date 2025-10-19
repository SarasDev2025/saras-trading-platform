"""
Performance Analytics Service

Comprehensive performance metrics calculation for trading algorithms and portfolios.

Calculates:
- Return metrics (total return, CAGR, daily/monthly returns)
- Risk metrics (Sharpe, Sortino, max drawdown, Calmar ratio, volatility, beta, alpha)
- Trade metrics (win rate, profit factor, expectancy, payoff ratio)
- Equity curve data
- Trade distribution analysis
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PerformanceAnalytics:
    """
    Performance analytics calculator for trading strategies

    Provides comprehensive performance metrics including:
    - Return analysis
    - Risk-adjusted metrics
    - Trade statistics
    - Drawdown analysis
    """

    def __init__(self, db_session_factory):
        """
        Initialize Performance Analytics

        Args:
            db_session_factory: Database session factory
        """
        self.db_session_factory = db_session_factory

    async def calculate_algorithm_performance(
        self,
        algorithm_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        benchmark_symbol: Optional[str] = 'SPY'
    ) -> Dict:
        """
        Calculate comprehensive performance metrics for an algorithm

        Args:
            algorithm_id: Algorithm ID
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
            benchmark_symbol: Benchmark symbol for comparison (default: SPY)

        Returns:
            Dict with comprehensive performance metrics
        """
        try:
            # Fetch algorithm performance snapshots
            snapshots = await self._get_performance_snapshots(
                algorithm_id=algorithm_id,
                start_date=start_date,
                end_date=end_date
            )

            if not snapshots:
                logger.warning(f"No performance data found for algorithm {algorithm_id}")
                return {
                    'error': 'No performance data available',
                    'algorithm_id': algorithm_id
                }

            # Fetch trade history
            trades = await self._get_trade_history(
                algorithm_id=algorithm_id,
                start_date=start_date,
                end_date=end_date
            )

            # Calculate return metrics
            return_metrics = self._calculate_return_metrics(snapshots)

            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(snapshots)

            # Calculate trade metrics
            trade_metrics = self._calculate_trade_metrics(trades)

            # Calculate drawdown metrics
            drawdown_metrics = self._calculate_drawdown_metrics(snapshots)

            # Fetch benchmark data for comparison
            benchmark_metrics = None
            if benchmark_symbol:
                benchmark_metrics = await self._calculate_benchmark_metrics(
                    benchmark_symbol=benchmark_symbol,
                    start_date=snapshots[0]['date'],
                    end_date=snapshots[-1]['date']
                )

            # Calculate alpha and beta vs benchmark
            if benchmark_metrics:
                alpha_beta = self._calculate_alpha_beta(snapshots, benchmark_metrics)
                risk_metrics.update(alpha_beta)

            # Prepare equity curve data
            equity_curve = [
                {
                    'date': snap['date'].isoformat(),
                    'equity': float(snap['total_value']),
                    'cumulative_return': float(snap.get('cumulative_return_pct', 0))
                }
                for snap in snapshots
            ]

            return {
                'algorithm_id': algorithm_id,
                'period': {
                    'start': snapshots[0]['date'].isoformat(),
                    'end': snapshots[-1]['date'].isoformat(),
                    'days': (snapshots[-1]['date'] - snapshots[0]['date']).days
                },
                'return_metrics': return_metrics,
                'risk_metrics': risk_metrics,
                'trade_metrics': trade_metrics,
                'drawdown_metrics': drawdown_metrics,
                'equity_curve': equity_curve,
                'benchmark': benchmark_metrics.get('symbol') if benchmark_metrics else None,
                'total_trades': len(trades)
            }

        except Exception as e:
            logger.error(f"Error calculating performance for algorithm {algorithm_id}: {e}", exc_info=True)
            raise

    async def calculate_portfolio_performance(
        self,
        portfolio_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate performance metrics for a portfolio

        Args:
            portfolio_id: Portfolio ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dict with performance metrics
        """
        try:
            # Fetch portfolio value history
            history = await self._get_portfolio_history(
                portfolio_id=portfolio_id,
                start_date=start_date,
                end_date=end_date
            )

            if not history:
                return {
                    'error': 'No portfolio history available',
                    'portfolio_id': portfolio_id
                }

            # Calculate metrics similar to algorithm performance
            return_metrics = self._calculate_return_metrics(history)
            risk_metrics = self._calculate_risk_metrics(history)
            drawdown_metrics = self._calculate_drawdown_metrics(history)

            return {
                'portfolio_id': portfolio_id,
                'period': {
                    'start': history[0]['date'].isoformat(),
                    'end': history[-1]['date'].isoformat(),
                    'days': (history[-1]['date'] - history[0]['date']).days
                },
                'return_metrics': return_metrics,
                'risk_metrics': risk_metrics,
                'drawdown_metrics': drawdown_metrics
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}", exc_info=True)
            raise

    def _calculate_return_metrics(self, snapshots: List[Dict]) -> Dict:
        """
        Calculate return metrics

        Metrics:
        - Total return
        - Annualized return
        - CAGR (Compound Annual Growth Rate)
        - Average daily/monthly return
        - Best/worst day
        """
        if not snapshots:
            return {}

        try:
            values = np.array([float(s['total_value']) for s in snapshots])
            initial_value = values[0]
            final_value = values[-1]

            # Total return
            total_return = final_value - initial_value
            total_return_pct = (total_return / initial_value) * 100 if initial_value > 0 else 0

            # Calculate daily returns
            daily_returns = np.diff(values) / values[:-1]

            # Annualized return
            days = (snapshots[-1]['date'] - snapshots[0]['date']).days
            years = days / 365.25
            annualized_return_pct = 0
            if years > 0 and initial_value > 0:
                annualized_return_pct = (
                    ((final_value / initial_value) ** (1 / years)) - 1
                ) * 100

            # CAGR (same as annualized return)
            cagr_pct = annualized_return_pct

            # Average daily return
            avg_daily_return_pct = float(np.mean(daily_returns)) * 100 if len(daily_returns) > 0 else 0

            # Best and worst day
            best_day_pct = float(np.max(daily_returns)) * 100 if len(daily_returns) > 0 else 0
            worst_day_pct = float(np.min(daily_returns)) * 100 if len(daily_returns) > 0 else 0

            # Monthly returns (approximate)
            monthly_returns = []
            if len(snapshots) >= 30:
                for i in range(30, len(values), 30):
                    month_return = (values[i] - values[i-30]) / values[i-30]
                    monthly_returns.append(month_return)

            avg_monthly_return_pct = float(np.mean(monthly_returns)) * 100 if monthly_returns else 0

            return {
                'total_return': float(total_return),
                'total_return_pct': float(total_return_pct),
                'annualized_return_pct': float(annualized_return_pct),
                'cagr_pct': float(cagr_pct),
                'avg_daily_return_pct': float(avg_daily_return_pct),
                'avg_monthly_return_pct': float(avg_monthly_return_pct),
                'best_day_pct': float(best_day_pct),
                'worst_day_pct': float(worst_day_pct),
                'initial_value': float(initial_value),
                'final_value': float(final_value)
            }

        except Exception as e:
            logger.error(f"Error calculating return metrics: {e}")
            return {}

    def _calculate_risk_metrics(self, snapshots: List[Dict]) -> Dict:
        """
        Calculate risk metrics

        Metrics:
        - Volatility (annualized standard deviation)
        - Sharpe ratio
        - Sortino ratio
        - Maximum drawdown
        - Calmar ratio
        """
        if not snapshots:
            return {}

        try:
            values = np.array([float(s['total_value']) for s in snapshots])
            daily_returns = np.diff(values) / values[:-1]

            if len(daily_returns) == 0:
                return {}

            # Volatility (annualized)
            daily_volatility = float(np.std(daily_returns))
            annualized_volatility_pct = daily_volatility * np.sqrt(252) * 100

            # Sharpe ratio (assuming 0% risk-free rate for simplicity)
            avg_return = float(np.mean(daily_returns))
            if daily_volatility > 0:
                sharpe_ratio = (avg_return / daily_volatility) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # Sortino ratio (downside deviation)
            downside_returns = daily_returns[daily_returns < 0]
            if len(downside_returns) > 0:
                downside_volatility = float(np.std(downside_returns))
                if downside_volatility > 0:
                    sortino_ratio = (avg_return / downside_volatility) * np.sqrt(252)
                else:
                    sortino_ratio = sharpe_ratio
            else:
                sortino_ratio = sharpe_ratio

            return {
                'volatility_pct': float(annualized_volatility_pct),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio)
            }

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}

    def _calculate_drawdown_metrics(self, snapshots: List[Dict]) -> Dict:
        """
        Calculate drawdown metrics

        Metrics:
        - Maximum drawdown
        - Maximum drawdown duration
        - Current drawdown
        - Calmar ratio
        """
        if not snapshots:
            return {}

        try:
            values = np.array([float(s['total_value']) for s in snapshots])

            # Calculate running maximum
            running_max = np.maximum.accumulate(values)

            # Calculate drawdowns
            drawdowns = (values - running_max) / running_max * 100

            # Maximum drawdown
            max_drawdown_pct = float(np.min(drawdowns))

            # Current drawdown
            current_drawdown_pct = float(drawdowns[-1])

            # Drawdown duration
            max_dd_duration_days = 0
            current_dd_start = None

            for i, dd in enumerate(drawdowns):
                if dd < -0.01:  # In drawdown
                    if current_dd_start is None:
                        current_dd_start = snapshots[i]['date']
                else:  # Not in drawdown
                    if current_dd_start is not None:
                        duration = (snapshots[i]['date'] - current_dd_start).days
                        max_dd_duration_days = max(max_dd_duration_days, duration)
                        current_dd_start = None

            # Calmar ratio (annual return / max drawdown)
            calmar_ratio = 0
            if max_drawdown_pct < 0:
                days = (snapshots[-1]['date'] - snapshots[0]['date']).days
                years = days / 365.25
                if years > 0:
                    total_return_pct = (values[-1] - values[0]) / values[0] * 100
                    annualized_return = total_return_pct / years
                    calmar_ratio = annualized_return / abs(max_drawdown_pct)

            return {
                'max_drawdown_pct': float(max_drawdown_pct),
                'current_drawdown_pct': float(current_drawdown_pct),
                'max_drawdown_duration_days': int(max_dd_duration_days),
                'calmar_ratio': float(calmar_ratio)
            }

        except Exception as e:
            logger.error(f"Error calculating drawdown metrics: {e}")
            return {}

    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate trade performance metrics

        Metrics:
        - Win rate
        - Profit factor
        - Average win vs average loss
        - Expectancy
        - Payoff ratio
        - Consecutive wins/losses
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0
            }

        try:
            wins = []
            losses = []

            for trade in trades:
                pnl = float(trade.get('pnl', 0))
                if pnl > 0:
                    wins.append(pnl)
                elif pnl < 0:
                    losses.append(abs(pnl))

            total_trades = len(trades)
            winning_trades = len(wins)
            losing_trades = len(losses)

            # Win rate
            win_rate_pct = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # Average win/loss
            avg_win = float(np.mean(wins)) if wins else 0
            avg_loss = float(np.mean(losses)) if losses else 0

            # Profit factor (total wins / total losses)
            total_wins = sum(wins)
            total_losses = sum(losses)
            profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

            # Expectancy (average profit per trade)
            expectancy = float(np.mean([float(t.get('pnl', 0)) for t in trades]))

            # Payoff ratio (avg win / avg loss)
            payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0

            # Consecutive wins/losses
            max_consecutive_wins = 0
            max_consecutive_losses = 0
            current_streak = 0
            last_was_win = None

            for trade in trades:
                pnl = float(trade.get('pnl', 0))
                is_win = pnl > 0

                if last_was_win is None or last_was_win == is_win:
                    current_streak += 1
                else:
                    if last_was_win:
                        max_consecutive_wins = max(max_consecutive_wins, current_streak)
                    else:
                        max_consecutive_losses = max(max_consecutive_losses, current_streak)
                    current_streak = 1

                last_was_win = is_win

            # Final streak
            if last_was_win:
                max_consecutive_wins = max(max_consecutive_wins, current_streak)
            else:
                max_consecutive_losses = max(max_consecutive_losses, current_streak)

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate_pct': float(win_rate_pct),
                'profit_factor': float(profit_factor),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'expectancy': float(expectancy),
                'payoff_ratio': float(payoff_ratio),
                'max_consecutive_wins': int(max_consecutive_wins),
                'max_consecutive_losses': int(max_consecutive_losses),
                'total_profit': float(total_wins),
                'total_loss': float(total_losses)
            }

        except Exception as e:
            logger.error(f"Error calculating trade metrics: {e}")
            return {}

    def _calculate_alpha_beta(
        self,
        snapshots: List[Dict],
        benchmark_metrics: Dict
    ) -> Dict:
        """
        Calculate alpha and beta vs benchmark

        Alpha: Excess return vs benchmark
        Beta: Correlation to benchmark movements
        """
        try:
            values = np.array([float(s['total_value']) for s in snapshots])
            returns = np.diff(values) / values[:-1]

            benchmark_returns = benchmark_metrics.get('daily_returns', [])

            if len(returns) != len(benchmark_returns):
                logger.warning("Return series length mismatch, cannot calculate alpha/beta")
                return {'alpha': 0, 'beta': 0}

            # Beta (covariance / variance)
            covariance = np.cov(returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)

            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

            # Alpha (excess return)
            avg_return = float(np.mean(returns))
            avg_benchmark_return = float(np.mean(benchmark_returns))
            alpha = avg_return - (beta * avg_benchmark_return)

            # Annualize alpha
            alpha_annualized = alpha * 252 * 100

            return {
                'alpha_pct': float(alpha_annualized),
                'beta': float(beta)
            }

        except Exception as e:
            logger.error(f"Error calculating alpha/beta: {e}")
            return {'alpha': 0, 'beta': 0}

    async def _get_performance_snapshots(
        self,
        algorithm_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch algorithm performance snapshots from database"""
        try:
            async with self.db_session_factory() as db:
                query = """
                    SELECT
                        snapshot_date as date,
                        total_value,
                        daily_pnl,
                        cumulative_pnl,
                        total_trades,
                        winning_trades,
                        losing_trades
                    FROM algorithm_performance_snapshots
                    WHERE algorithm_id = :algorithm_id
                """

                params = {'algorithm_id': algorithm_id}

                if start_date:
                    query += " AND snapshot_date >= :start_date"
                    params['start_date'] = start_date

                if end_date:
                    query += " AND snapshot_date <= :end_date"
                    params['end_date'] = end_date

                query += " ORDER BY snapshot_date ASC"

                result = await db.execute(text(query), params)
                rows = result.fetchall()

                return [
                    {
                        'date': row.date,
                        'total_value': float(row.total_value),
                        'daily_pnl': float(row.daily_pnl) if row.daily_pnl else 0,
                        'cumulative_pnl': float(row.cumulative_pnl) if row.cumulative_pnl else 0
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error fetching performance snapshots: {e}")
            return []

    async def _get_trade_history(
        self,
        algorithm_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch algorithm trade history"""
        try:
            async with self.db_session_factory() as db:
                query = """
                    SELECT
                        executed_at,
                        symbol,
                        action,
                        quantity,
                        executed_price,
                        total_amount,
                        pnl
                    FROM trades
                    WHERE algorithm_id = :algorithm_id
                    AND status = 'executed'
                """

                params = {'algorithm_id': algorithm_id}

                if start_date:
                    query += " AND executed_at >= :start_date"
                    params['start_date'] = start_date

                if end_date:
                    query += " AND executed_at <= :end_date"
                    params['end_date'] = end_date

                query += " ORDER BY executed_at ASC"

                result = await db.execute(text(query), params)
                rows = result.fetchall()

                return [
                    {
                        'executed_at': row.executed_at,
                        'symbol': row.symbol,
                        'action': row.action,
                        'quantity': float(row.quantity),
                        'executed_price': float(row.executed_price) if row.executed_price else 0,
                        'total_amount': float(row.total_amount) if row.total_amount else 0,
                        'pnl': float(row.pnl) if row.pnl else 0
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            return []

    async def _get_portfolio_history(
        self,
        portfolio_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch portfolio value history"""
        try:
            async with self.db_session_factory() as db:
                # This would fetch from a portfolio_snapshots table (to be created)
                # For now, return empty
                return []

        except Exception as e:
            logger.error(f"Error fetching portfolio history: {e}")
            return []

    async def _calculate_benchmark_metrics(
        self,
        benchmark_symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Calculate benchmark performance for comparison"""
        try:
            async with self.db_session_factory() as db:
                result = await db.execute(text("""
                    SELECT timestamp, close
                    FROM market_data_bars
                    WHERE symbol = :symbol
                    AND timeframe = '1day'
                    AND timestamp >= :start_date
                    AND timestamp <= :end_date
                    ORDER BY timestamp ASC
                """), {
                    'symbol': benchmark_symbol,
                    'start_date': start_date,
                    'end_date': end_date
                })

                rows = result.fetchall()

                if not rows:
                    return {}

                prices = np.array([float(row.close) for row in rows])
                daily_returns = np.diff(prices) / prices[:-1]

                return {
                    'symbol': benchmark_symbol,
                    'daily_returns': daily_returns.tolist(),
                    'total_return_pct': ((prices[-1] - prices[0]) / prices[0]) * 100
                }

        except Exception as e:
            logger.error(f"Error calculating benchmark metrics: {e}")
            return {}


# Singleton instance
_performance_analytics: Optional[PerformanceAnalytics] = None


async def get_performance_analytics(
    db_session_factory=None
) -> PerformanceAnalytics:
    """
    Get or create PerformanceAnalytics singleton

    Args:
        db_session_factory: Database session factory

    Returns:
        PerformanceAnalytics instance
    """
    global _performance_analytics

    if _performance_analytics is None:
        if db_session_factory is None:
            raise ValueError("db_session_factory required for first initialization")

        _performance_analytics = PerformanceAnalytics(
            db_session_factory=db_session_factory
        )

    return _performance_analytics
