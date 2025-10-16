"""
Strategy Optimizer Service
Analyzes historical data and suggests optimal trading strategies based on statistical performance
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """Service for analyzing and suggesting trading strategies based on historical data"""

    @staticmethod
    def analyze_and_suggest_strategies(
        df: pd.DataFrame,
        symbol: str,
        style: str = 'balanced',
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze historical data and suggest top-performing strategies

        Args:
            df: DataFrame with OHLCV data and indicators (rsi, sma_20, sma_50, ema_20)
            symbol: Stock symbol
            style: Trading style - 'conservative', 'balanced', or 'aggressive'
            top_n: Number of top strategies to return

        Returns:
            Dictionary with suggestions and analysis metadata
        """
        logger.info(f"Analyzing strategies for {symbol} with style={style}")

        all_strategies = []

        # Test RSI strategies
        all_strategies.extend(StrategyOptimizer._test_rsi_strategies(df))

        # Test SMA crossover strategies
        all_strategies.extend(StrategyOptimizer._test_sma_crossovers(df))

        # Test MACD strategies (if MACD data available)
        # all_strategies.extend(StrategyOptimizer._test_macd_strategies(df))

        # Rank strategies
        ranked_strategies = StrategyOptimizer._rank_strategies(all_strategies, style)

        # Get top N
        top_strategies = ranked_strategies[:top_n]

        return {
            'suggestions': top_strategies,
            'analysis_period': f"{df['date'].iloc[0].strftime('%Y-%m-%d')} to {df['date'].iloc[-1].strftime('%Y-%m-%d')}",
            'data_points': len(df),
            'strategies_tested': len(all_strategies)
        }

    @staticmethod
    def _test_rsi_strategies(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Test various RSI mean reversion strategies"""
        strategies = []

        # RSI thresholds to test
        rsi_configs = [
            (20, 80, "RSI Oversold/Overbought (20/80)", "Aggressive mean reversion with wider bounds"),
            (25, 75, "RSI Oversold/Overbought (25/75)", "Moderate mean reversion strategy"),
            (30, 70, "RSI Oversold/Overbought (30/70)", "Conservative mean reversion approach"),
            (35, 65, "RSI Oversold/Overbought (35/65)", "Very conservative, tighter bounds"),
        ]

        for buy_threshold, sell_threshold, name, description in rsi_configs:
            strategy = StrategyOptimizer._backtest_rsi_strategy(
                df, buy_threshold, sell_threshold, name, description
            )
            if strategy:
                strategies.append(strategy)

        return strategies

    @staticmethod
    def _test_sma_crossovers(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Test various SMA crossover strategies"""
        strategies = []

        # For now, use existing sma_20 and sma_50
        # Later can add more combinations
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            strategy = StrategyOptimizer._backtest_sma_crossover(
                df,
                'sma_20',
                'sma_50',
                "SMA Crossover (20/50)",
                "Short-term SMA crosses long-term SMA for trend following"
            )
            if strategy:
                strategies.append(strategy)

        return strategies

    @staticmethod
    def _backtest_rsi_strategy(
        df: pd.DataFrame,
        buy_threshold: int,
        sell_threshold: int,
        name: str,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """Backtest an RSI-based strategy"""

        if 'rsi' not in df.columns:
            return None

        # Generate signals
        signals = []
        position = None

        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]

            # Skip if RSI is NaN
            if pd.isna(current['rsi']) or current['rsi'] == 0:
                continue

            # Buy signal: RSI crosses below buy_threshold
            if not position and current['rsi'] < buy_threshold:
                signals.append({
                    'type': 'buy',
                    'date': current['date'],
                    'price': current['close'],
                    'rsi': current['rsi']
                })
                position = current['close']

            # Sell signal: RSI crosses above sell_threshold
            elif position and current['rsi'] > sell_threshold:
                signals.append({
                    'type': 'sell',
                    'date': current['date'],
                    'price': current['close'],
                    'rsi': current['rsi']
                })
                position = None

        # Calculate performance metrics
        metrics = StrategyOptimizer._calculate_performance_metrics(signals)

        if metrics['total_signals'] == 0:
            return None

        # Build strategy object
        return {
            'name': name,
            'description': description,
            'entry_conditions': [{
                'type': 'indicator_comparison',
                'indicator': 'RSI',
                'operator': 'below',
                'value': buy_threshold
            }],
            'exit_conditions': [{
                'type': 'indicator_comparison',
                'indicator': 'RSI',
                'operator': 'above',
                'value': sell_threshold
            }],
            'backtest_results': metrics,
            'strategy_type': 'mean_reversion'
        }

    @staticmethod
    def _backtest_sma_crossover(
        df: pd.DataFrame,
        fast_col: str,
        slow_col: str,
        name: str,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """Backtest an SMA crossover strategy"""

        if fast_col not in df.columns or slow_col not in df.columns:
            return None

        signals = []
        position = None

        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]

            # Skip if SMA values are NaN
            if pd.isna(current[fast_col]) or pd.isna(current[slow_col]) or \
               pd.isna(prev[fast_col]) or pd.isna(prev[slow_col]):
                continue

            if current[fast_col] == 0 or current[slow_col] == 0:
                continue

            # Buy signal: fast SMA crosses above slow SMA
            if not position and prev[fast_col] < prev[slow_col] and current[fast_col] > current[slow_col]:
                signals.append({
                    'type': 'buy',
                    'date': current['date'],
                    'price': current['close']
                })
                position = current['close']

            # Sell signal: fast SMA crosses below slow SMA
            elif position and prev[fast_col] > prev[slow_col] and current[fast_col] < current[slow_col]:
                signals.append({
                    'type': 'sell',
                    'date': current['date'],
                    'price': current['close']
                })
                position = None

        metrics = StrategyOptimizer._calculate_performance_metrics(signals)

        if metrics['total_signals'] == 0:
            return None

        # Extract period numbers from column names (e.g., sma_20 -> 20)
        fast_period = int(fast_col.split('_')[-1]) if '_' in fast_col else 20
        slow_period = int(slow_col.split('_')[-1]) if '_' in slow_col else 50

        return {
            'name': name,
            'description': description,
            'entry_conditions': [{
                'type': 'indicator_crossover',
                'indicator1': 'SMA',
                'indicator2': 'SMA',
                'period1': fast_period,
                'period2': slow_period,
                'direction': 'above'
            }],
            'exit_conditions': [{
                'type': 'indicator_crossover',
                'indicator1': 'SMA',
                'indicator2': 'SMA',
                'period1': fast_period,
                'period2': slow_period,
                'direction': 'below'
            }],
            'backtest_results': metrics,
            'strategy_type': 'trend_following'
        }

    @staticmethod
    def _calculate_performance_metrics(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from trade signals"""

        buy_signals = [s for s in signals if s['type'] == 'buy']
        sell_signals = [s for s in signals if s['type'] == 'sell']

        total_signals = len(signals)

        if len(buy_signals) == 0 or len(sell_signals) == 0:
            return {
                'total_signals': total_signals,
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'win_rate': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }

        # Pair up buy and sell signals
        trades = []
        num_trades = min(len(buy_signals), len(sell_signals))

        for i in range(num_trades):
            buy_price = buy_signals[i]['price']
            sell_price = sell_signals[i]['price']
            profit_pct = ((sell_price - buy_price) / buy_price) * 100
            trades.append(profit_pct)

        # Calculate metrics
        winning_trades = [t for t in trades if t > 0]
        losing_trades = [t for t in trades if t <= 0]

        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        total_return = sum(trades) if trades else 0

        # Sharpe ratio (simplified: mean / std)
        sharpe_ratio = 0
        if trades and len(trades) > 1:
            mean_return = np.mean(trades)
            std_return = np.std(trades)
            if std_return > 0:
                sharpe_ratio = mean_return / std_return

        # Max drawdown (simplified)
        max_drawdown = min(trades) if trades else 0

        return {
            'total_signals': total_signals,
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'win_rate': round(win_rate, 1),
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }

    @staticmethod
    def _rank_strategies(strategies: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        """Rank strategies by composite score based on trading style"""

        # Weighting based on style
        weights = {
            'conservative': {'win_rate': 0.5, 'sharpe': 0.3, 'return': 0.1, 'signal_quality': 0.1},
            'balanced': {'win_rate': 0.4, 'sharpe': 0.3, 'return': 0.2, 'signal_quality': 0.1},
            'aggressive': {'win_rate': 0.2, 'sharpe': 0.2, 'return': 0.5, 'signal_quality': 0.1}
        }

        w = weights.get(style, weights['balanced'])

        for strategy in strategies:
            metrics = strategy['backtest_results']

            # Normalize metrics
            win_rate_score = metrics['win_rate'] / 100  # 0-1
            sharpe_score = min(max(metrics['sharpe_ratio'] / 3, 0), 1)  # Normalize to 0-1
            return_score = min(max(metrics['total_return'] / 50, -1), 1)  # Normalize to -1 to 1

            # Signal quality: prefer 5-20 signals
            signal_count = metrics['total_signals']
            if 5 <= signal_count <= 20:
                signal_quality = 1.0
            elif signal_count < 5:
                signal_quality = 0.3
            else:
                signal_quality = 0.7

            # Composite score
            score = (
                win_rate_score * w['win_rate'] +
                sharpe_score * w['sharpe'] +
                return_score * w['return'] +
                signal_quality * w['signal_quality']
            )

            strategy['score'] = round(score, 3)

            # Assign confidence based on signal count and win rate
            if signal_count >= 8 and metrics['win_rate'] >= 55:
                confidence = 'high'
            elif signal_count >= 5 and metrics['win_rate'] >= 45:
                confidence = 'medium'
            else:
                confidence = 'low'

            strategy['confidence'] = confidence

            # Assign rank after sorting
            strategy['rank'] = 0

        # Sort by score
        sorted_strategies = sorted(strategies, key=lambda x: x['score'], reverse=True)

        # Assign ranks
        for i, strategy in enumerate(sorted_strategies):
            strategy['rank'] = i + 1

        return sorted_strategies
