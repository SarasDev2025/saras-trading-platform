"""
Backtesting Service
Run historical simulations of trading algorithms with multi-broker support
"""
import uuid
import logging
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import pandas as pd
    import numpy as np
    import pandas_ta as ta
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not available - backtesting will be limited")

logger = logging.getLogger(__name__)


class BacktestingService:
    """Service for backtesting trading algorithms"""

    @staticmethod
    async def run_backtest(
        db: AsyncSession,
        algorithm_id: uuid.UUID,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        initial_capital: Decimal,
        backtest_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a backtest for an algorithm

        Args:
            db: Database session
            algorithm_id: Algorithm UUID
            user_id: User UUID
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital amount
            backtest_name: Optional name for this backtest

        Returns:
            Backtest results with performance metrics
        """
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas not installed - backtesting not available")

        try:
            # 1. Get algorithm
            algo_result = await db.execute(text("""
                SELECT
                    id, name, strategy_code, parameters,
                    allowed_regions, target_broker
                FROM trading_algorithms
                WHERE id = :algorithm_id AND user_id = :user_id
            """), {"algorithm_id": str(algorithm_id), "user_id": str(user_id)})

            algo = algo_result.fetchone()
            if not algo:
                raise ValueError(f"Algorithm {algorithm_id} not found")

            # 2. Get user region to determine which market data to use
            user_result = await db.execute(text("""
                SELECT region FROM users WHERE id = :user_id
            """), {"user_id": str(user_id)})

            user = user_result.fetchone()
            region = user.region if user else 'IN'

            # 3. Determine broker for historical data
            broker = algo.target_broker or ('zerodha' if region == 'IN' else 'alpaca')

            logger.info(
                f"Starting backtest for {algo.name} from {start_date} to {end_date} "
                f"with ${initial_capital} initial capital (broker: {broker})"
            )

            # 4. Get historical market data
            historical_data = await BacktestingService._get_historical_data(
                db, broker, region, start_date, end_date
            )

            if not historical_data:
                raise ValueError("No historical data available for the specified date range")

            # 5. Run simulation
            simulation_results = await BacktestingService._run_simulation(
                algorithm_code=algo.strategy_code,
                parameters=algo.parameters or {},
                historical_data=historical_data,
                initial_capital=float(initial_capital),
                start_date=start_date,
                end_date=end_date
            )

            # 6. Calculate performance metrics
            metrics = BacktestingService._calculate_metrics(
                simulation_results['equity_curve'],
                simulation_results['trades'],
                float(initial_capital)
            )

            # 7. Store backtest results
            backtest_result = await db.execute(text("""
                INSERT INTO algorithm_backtest_results (
                    algorithm_id, user_id, backtest_name,
                    start_date, end_date, initial_capital, final_capital,
                    total_return, total_return_pct, annualized_return,
                    sharpe_ratio, sortino_ratio, max_drawdown, max_drawdown_pct, volatility,
                    total_trades, winning_trades, losing_trades, win_rate, profit_factor,
                    avg_win, avg_loss, avg_trade_duration_hours,
                    best_trade, worst_trade, longest_winning_streak, longest_losing_streak,
                    equity_curve, trade_log, parameters
                )
                VALUES (
                    :algorithm_id, :user_id, :backtest_name,
                    :start_date, :end_date, :initial_capital, :final_capital,
                    :total_return, :total_return_pct, :annualized_return,
                    :sharpe_ratio, :sortino_ratio, :max_drawdown, :max_drawdown_pct, :volatility,
                    :total_trades, :winning_trades, :losing_trades, :win_rate, :profit_factor,
                    :avg_win, :avg_loss, :avg_trade_duration_hours,
                    :best_trade, :worst_trade, :longest_winning_streak, :longest_losing_streak,
                    :equity_curve, :trade_log, :parameters
                )
                RETURNING id
            """), {
                "algorithm_id": str(algorithm_id),
                "user_id": str(user_id),
                "backtest_name": backtest_name or f"Backtest {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": float(initial_capital),
                "final_capital": metrics['final_capital'],
                "total_return": metrics['total_return'],
                "total_return_pct": metrics['total_return_pct'],
                "annualized_return": metrics['annualized_return'],
                "sharpe_ratio": metrics['sharpe_ratio'],
                "sortino_ratio": metrics['sortino_ratio'],
                "max_drawdown": metrics['max_drawdown'],
                "max_drawdown_pct": metrics['max_drawdown_pct'],
                "volatility": metrics['volatility'],
                "total_trades": metrics['total_trades'],
                "winning_trades": metrics['winning_trades'],
                "losing_trades": metrics['losing_trades'],
                "win_rate": metrics['win_rate'],
                "profit_factor": metrics['profit_factor'],
                "avg_win": metrics['avg_win'],
                "avg_loss": metrics['avg_loss'],
                "avg_trade_duration_hours": metrics['avg_trade_duration_hours'],
                "best_trade": metrics['best_trade'],
                "worst_trade": metrics['worst_trade'],
                "longest_winning_streak": metrics['longest_winning_streak'],
                "longest_losing_streak": metrics['longest_losing_streak'],
                "equity_curve": json.dumps(simulation_results['equity_curve']),
                "trade_log": json.dumps(simulation_results['trades']),
                "parameters": json.dumps(algo.parameters or {})
            })

            result_id = backtest_result.scalar()
            await db.commit()

            return {
                "success": True,
                "backtest_id": str(result_id),
                "metrics": metrics,
                "equity_curve": simulation_results['equity_curve'],
                "trade_count": len(simulation_results['trades']),
                "broker": broker
            }

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def _get_historical_data(
        db: AsyncSession,
        broker: str,
        region: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical price data for backtesting

        In production, this would fetch from broker APIs
        For now, generates synthetic data based on current prices
        """
        # Get assets for the region
        result = await db.execute(text("""
            SELECT symbol, current_price
            FROM assets
            WHERE region = :region
            AND asset_type = 'STOCK'
            AND current_price > 0
            ORDER BY symbol
            LIMIT 50
        """), {"region": region})

        historical_data = {}

        # Generate synthetic historical data
        # In production, replace with actual API calls to broker
        for row in result.fetchall():
            symbol = row.symbol
            current_price = float(row.current_price)

            # Generate daily prices with random walk
            days = (end_date - start_date).days + 1
            dates = pd.date_range(start=start_date, end=end_date, freq='D')

            # Simple random walk for demo purposes
            np.random.seed(hash(symbol) % 2**32)
            returns = np.random.normal(0.0005, 0.02, days)
            prices = current_price * np.exp(np.cumsum(returns))

            df = pd.DataFrame({
                'date': dates[:len(prices)],
                'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(prices))),
                'high': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
                'low': prices * (1 - np.random.uniform(0, 0.02, len(prices))),
                'close': prices,
                'volume': np.random.randint(100000, 10000000, len(prices))
            })

            historical_data[symbol] = df

        return historical_data

    @staticmethod
    async def _run_simulation(
        algorithm_code: str,
        parameters: Dict[str, Any],
        historical_data: Dict[str, pd.DataFrame],
        initial_capital: float,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Run simulation using algorithm code on historical data

        Returns:
            Dict with equity_curve and trades list
        """
        # Initialize simulation state
        cash = initial_capital
        positions = {}  # symbol -> {'quantity': X, 'avg_price': Y}
        equity_curve = []
        trades = []

        # Get all trading dates
        if not historical_data:
            return {'equity_curve': [], 'trades': []}

        # Get dates from first symbol
        first_symbol = list(historical_data.keys())[0]
        trading_dates = historical_data[first_symbol]['date'].tolist()

        # Simulate each day
        for current_date in trading_dates:
            # Get current prices
            current_prices = {}
            for symbol, df in historical_data.items():
                price_row = df[df['date'] == current_date]
                if not price_row.empty:
                    current_prices[symbol] = float(price_row.iloc[0]['close'])

            # Calculate current portfolio value
            holdings_value = sum(
                positions.get(symbol, {}).get('quantity', 0) * current_prices.get(symbol, 0)
                for symbol in positions.keys()
            )
            total_equity = cash + holdings_value

            # Record equity point
            equity_curve.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'equity': round(total_equity, 2),
                'cash': round(cash, 2),
                'holdings': round(holdings_value, 2)
            })

            # Simple signal generation (placeholder - in production, exec algorithm code)
            # For demo, use basic moving average crossover
            signals = BacktestingService._generate_demo_signals(
                historical_data, current_date, positions, parameters
            )

            # Execute signals
            for signal in signals:
                symbol = signal['symbol']
                signal_type = signal['type']
                quantity = signal['quantity']
                price = current_prices.get(symbol, 0)

                if price == 0:
                    continue

                if signal_type == 'buy':
                    cost = quantity * price
                    if cash >= cost:
                        # Execute buy
                        cash -= cost
                        if symbol not in positions:
                            positions[symbol] = {'quantity': 0, 'avg_price': 0}

                        old_qty = positions[symbol]['quantity']
                        old_avg = positions[symbol]['avg_price']
                        new_qty = old_qty + quantity
                        new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty

                        positions[symbol]['quantity'] = new_qty
                        positions[symbol]['avg_price'] = new_avg

                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'symbol': symbol,
                            'side': 'buy',
                            'quantity': quantity,
                            'price': round(price, 2),
                            'value': round(cost, 2)
                        })

                elif signal_type == 'sell':
                    if symbol in positions and positions[symbol]['quantity'] >= quantity:
                        # Execute sell
                        proceeds = quantity * price
                        cash += proceeds

                        pnl = (price - positions[symbol]['avg_price']) * quantity

                        positions[symbol]['quantity'] -= quantity

                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'symbol': symbol,
                            'side': 'sell',
                            'quantity': quantity,
                            'price': round(price, 2),
                            'value': round(proceeds, 2),
                            'pnl': round(pnl, 2)
                        })

                        # Remove position if fully closed
                        if positions[symbol]['quantity'] == 0:
                            del positions[symbol]

        return {
            'equity_curve': equity_curve,
            'trades': trades
        }

    @staticmethod
    def _generate_demo_signals(
        historical_data: Dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        positions: Dict[str, Dict],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate demo trading signals
        In production, this would exec the actual algorithm code
        """
        signals = []

        # Simple moving average crossover for demo
        sma_short = parameters.get('sma_short', 10)
        sma_long = parameters.get('sma_long', 30)

        for symbol, df in historical_data.items():
            # Get data up to current date
            historical = df[df['date'] <= current_date].copy()

            if len(historical) < sma_long:
                continue

            # Calculate moving averages
            historical['sma_short'] = historical['close'].rolling(window=sma_short).mean()
            historical['sma_long'] = historical['close'].rolling(window=sma_long).mean()

            # Get latest values
            if len(historical) < 2:
                continue

            prev = historical.iloc[-2]
            curr = historical.iloc[-1]

            # Bullish crossover - buy signal
            if (prev['sma_short'] <= prev['sma_long'] and
                curr['sma_short'] > curr['sma_long'] and
                symbol not in positions):

                signals.append({
                    'symbol': symbol,
                    'type': 'buy',
                    'quantity': 10,  # Fixed quantity for demo
                    'reason': f'SMA crossover: {sma_short}/{sma_long}'
                })

            # Bearish crossover - sell signal
            elif (prev['sma_short'] >= prev['sma_long'] and
                  curr['sma_short'] < curr['sma_long'] and
                  symbol in positions):

                signals.append({
                    'symbol': symbol,
                    'type': 'sell',
                    'quantity': positions[symbol]['quantity'],
                    'reason': f'SMA crossover: {sma_short}/{sma_long}'
                })

        return signals

    @staticmethod
    def _calculate_metrics(
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""

        if not equity_curve:
            return BacktestingService._empty_metrics()

        # Convert to arrays
        equity_values = [point['equity'] for point in equity_curve]
        final_capital = equity_values[-1]

        # Returns
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0

        # Annualized return
        days = len(equity_curve)
        years = days / 365.0 if days > 0 else 1
        annualized_return = ((final_capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

        # Drawdown
        peak = equity_values[0]
        max_dd = 0
        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        max_dd_pct = (max_dd / peak * 100) if peak > 0 else 0

        # Volatility & Sharpe
        if len(equity_values) > 1:
            returns = np.diff(equity_values) / equity_values[:-1]
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
            avg_return = np.mean(returns) * 252
            sharpe_ratio = (avg_return / (volatility / 100)) if volatility > 0 else 0

            # Sortino (downside deviation)
            downside_returns = returns[returns < 0]
            downside_std = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
            sortino_ratio = (avg_return / downside_std) if downside_std > 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0
            sortino_ratio = 0

        # Trade statistics
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

        total_trades = len([t for t in trades if 'pnl' in t])
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0

        gross_profit = sum([t['pnl'] for t in winning_trades])
        gross_loss = sum([abs(t['pnl']) for t in losing_trades])
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        # Best/Worst trades
        all_pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        best_trade = max(all_pnls) if all_pnls else 0
        worst_trade = min(all_pnls) if all_pnls else 0

        # Streaks
        streaks = BacktestingService._calculate_streaks([t.get('pnl', 0) for t in trades if 'pnl' in t])

        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'annualized_return': round(annualized_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'max_drawdown': round(max_dd, 2),
            'max_drawdown_pct': round(max_dd_pct, 2),
            'volatility': round(volatility, 2),
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'avg_trade_duration_hours': 24,  # Placeholder
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'longest_winning_streak': streaks['longest_win_streak'],
            'longest_losing_streak': streaks['longest_loss_streak']
        }

    @staticmethod
    def _calculate_streaks(pnls: List[float]) -> Dict[str, int]:
        """Calculate longest winning and losing streaks"""
        if not pnls:
            return {'longest_win_streak': 0, 'longest_loss_streak': 0}

        current_win_streak = 0
        current_loss_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for pnl in pnls:
            if pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif pnl < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)

        return {
            'longest_win_streak': max_win_streak,
            'longest_loss_streak': max_loss_streak
        }

    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'final_capital': 0,
            'total_return': 0,
            'total_return_pct': 0,
            'annualized_return': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'volatility': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_trade_duration_hours': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'longest_winning_streak': 0,
            'longest_losing_streak': 0
        }
