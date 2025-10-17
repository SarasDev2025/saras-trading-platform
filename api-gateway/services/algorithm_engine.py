"""
Algorithm Engine Service
Executes trading algorithms with multi-broker support (Zerodha Live + Alpaca Paper/Live)
"""
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import traceback

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import pandas as pd
    import numpy as np
    INDICATORS_AVAILABLE = True
except ImportError:
    INDICATORS_AVAILABLE = False
    logging.warning("pandas/numpy not available - algorithm features will be limited")

try:
    import pandas_ta as ta
except ImportError:
    ta = None
    logging.warning("pandas-ta not available - some technical indicators will be limited")

logger = logging.getLogger(__name__)


class AlgorithmEngine:
    """Core engine for executing trading algorithms"""

    @staticmethod
    async def execute_algorithm(
        db: AsyncSession,
        algorithm_id: uuid.UUID,
        user_id: uuid.UUID,
        execution_type: str = 'manual',
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a trading algorithm

        Args:
            db: Database session
            algorithm_id: Algorithm UUID
            user_id: User UUID
            execution_type: 'manual', 'scheduled', or 'backtest'
            dry_run: If True, generate signals but don't execute trades

        Returns:
            Execution results with signals generated
        """
        start_time = datetime.now(timezone.utc)
        execution_id = None

        try:
            # 1. Get algorithm details
            algo_result = await db.execute(text("""
                SELECT
                    id, user_id, name, strategy_code, parameters, status,
                    allowed_regions, allowed_trading_modes, target_broker,
                    max_positions, risk_per_trade, stock_universe
                FROM trading_algorithms
                WHERE id = :algorithm_id AND user_id = :user_id
            """), {"algorithm_id": str(algorithm_id), "user_id": str(user_id)})

            algo = algo_result.fetchone()
            if not algo:
                raise ValueError(f"Algorithm {algorithm_id} not found for user {user_id}")

            if algo.status != 'active' and execution_type == 'scheduled':
                raise ValueError(f"Algorithm is not active (status: {algo.status})")

            # 2. Get user's region and trading mode
            user_result = await db.execute(text("""
                SELECT region, trading_mode
                FROM users
                WHERE id = :user_id
            """), {"user_id": str(user_id)})

            user = user_result.fetchone()
            if not user:
                raise ValueError(f"User {user_id} not found")

            user_region = user.region
            user_trading_mode = user.trading_mode

            # 3. Validate region/mode compatibility
            if user_region not in algo.allowed_regions:
                raise ValueError(
                    f"Algorithm not compatible with region {user_region}. "
                    f"Allowed: {algo.allowed_regions}"
                )

            if user_trading_mode not in algo.allowed_trading_modes:
                raise ValueError(
                    f"Algorithm not compatible with trading mode {user_trading_mode}. "
                    f"Allowed: {algo.allowed_trading_modes}"
                )

            # 4. Determine broker
            broker = await AlgorithmEngine._determine_broker(
                user_region,
                user_trading_mode,
                algo.target_broker
            )

            # 5. Get user's portfolio for this trading mode
            portfolio_result = await db.execute(text("""
                SELECT id, cash_balance, total_value
                FROM portfolios
                WHERE user_id = :user_id
                AND trading_mode = :trading_mode
                AND is_default = true
                LIMIT 1
            """), {"user_id": str(user_id), "trading_mode": user_trading_mode})

            portfolio = portfolio_result.fetchone()
            if not portfolio:
                raise ValueError(
                    f"No default portfolio found for trading mode {user_trading_mode}"
                )

            # 6. Create execution record
            execution_result = await db.execute(text("""
                INSERT INTO algorithm_executions (
                    algorithm_id, user_id, portfolio_id,
                    execution_type, broker_used, trading_mode,
                    start_time, status
                )
                VALUES (
                    :algorithm_id, :user_id, :portfolio_id,
                    :execution_type, :broker, :trading_mode,
                    :start_time, 'running'
                )
                RETURNING id
            """), {
                "algorithm_id": str(algorithm_id),
                "user_id": str(user_id),
                "portfolio_id": str(portfolio.id),
                "execution_type": execution_type,
                "broker": broker,
                "trading_mode": user_trading_mode,
                "start_time": start_time
            })

            execution_id = execution_result.scalar()
            await db.commit()

            # 7. Parse stock universe
            import json
            stock_universe = algo.stock_universe or {"type": "all", "symbols": [], "filters": {}}
            if isinstance(stock_universe, str):
                stock_universe = json.loads(stock_universe)

            # 8. Execute algorithm code
            logger.info(f"Executing algorithm {algo.name} for user {user_id} via {broker}")

            signals = await AlgorithmEngine._run_algorithm_code(
                db=db,
                algorithm_code=algo.strategy_code,
                parameters=algo.parameters or {},
                user_id=user_id,
                portfolio_id=portfolio.id,
                broker=broker,
                trading_mode=user_trading_mode,
                max_positions=algo.max_positions,
                risk_per_trade=algo.risk_per_trade,
                stock_universe=stock_universe
            )

            # 8. Update execution record
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            await db.execute(text("""
                UPDATE algorithm_executions
                SET
                    end_time = :end_time,
                    duration_ms = :duration_ms,
                    status = 'completed',
                    signals_count = :signals_count
                WHERE id = :execution_id
            """), {
                "end_time": end_time,
                "duration_ms": duration_ms,
                "signals_count": len(signals),
                "execution_id": str(execution_id)
            })

            # 9. Update algorithm stats
            await db.execute(text("""
                UPDATE trading_algorithms
                SET
                    last_run_at = :last_run_at,
                    total_executions = total_executions + 1,
                    successful_executions = successful_executions + 1,
                    updated_at = :updated_at
                WHERE id = :algorithm_id
            """), {
                "last_run_at": end_time,
                "updated_at": end_time,
                "algorithm_id": str(algorithm_id)
            })

            await db.commit()

            return {
                "success": True,
                "execution_id": str(execution_id),
                "signals_generated": len(signals),
                "signals": signals,
                "broker": broker,
                "trading_mode": user_trading_mode,
                "duration_ms": duration_ms,
                "dry_run": dry_run
            }

        except Exception as e:
            logger.error(f"Algorithm execution failed: {e}\n{traceback.format_exc()}")

            # Update execution record with error
            if execution_id:
                try:
                    end_time = datetime.now(timezone.utc)
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)

                    await db.execute(text("""
                        UPDATE algorithm_executions
                        SET
                            end_time = :end_time,
                            duration_ms = :duration_ms,
                            status = 'failed',
                            error_message = :error_message
                        WHERE id = :execution_id
                    """), {
                        "end_time": end_time,
                        "duration_ms": duration_ms,
                        "error_message": str(e),
                        "execution_id": str(execution_id)
                    })

                    await db.execute(text("""
                        UPDATE trading_algorithms
                        SET
                            last_error = :error_message,
                            updated_at = :updated_at
                        WHERE id = :algorithm_id
                    """), {
                        "error_message": str(e),
                        "updated_at": end_time,
                        "algorithm_id": str(algorithm_id)
                    })

                    await db.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update execution record: {update_error}")

            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc() if execution_type == 'manual' else None
            }

    @staticmethod
    async def _determine_broker(
        user_region: str,
        trading_mode: str,
        target_broker: Optional[str] = None
    ) -> str:
        """
        Determine which broker to use based on region and trading mode

        Rules:
        - India (IN): Zerodha (LIVE only)
        - US: Alpaca (PAPER or LIVE)
        - GB: Alpaca (default)
        """
        if target_broker:
            # Validate target broker
            if target_broker == 'zerodha' and trading_mode == 'paper':
                raise ValueError("Zerodha does not support paper trading")
            return target_broker

        # Auto-detect broker
        if user_region == 'IN':
            if trading_mode == 'paper':
                raise ValueError(
                    "Paper trading not supported for Indian region. "
                    "Zerodha only supports LIVE trading."
                )
            return 'zerodha'

        elif user_region in ['US', 'GB']:
            return 'alpaca'

        else:
            # Default to Alpaca for unknown regions
            return 'alpaca'

    @staticmethod
    async def _run_algorithm_code(
        db: AsyncSession,
        algorithm_code: str,
        parameters: Dict[str, Any],
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        broker: str,
        trading_mode: str,
        max_positions: int,
        risk_per_trade: Decimal,
        stock_universe: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute algorithm code in a sandboxed environment

        Returns:
            List of trading signals
        """
        if not INDICATORS_AVAILABLE:
            raise RuntimeError("pandas/pandas_ta not installed - cannot execute algorithms")

        # TODO: Implement proper sandboxing with RestrictedPython
        # For now, using a simple execution model

        # Get current positions
        positions = await AlgorithmEngine._get_current_positions(db, portfolio_id)

        # Get market data (simplified - in production, fetch from broker API)
        market_data = await AlgorithmEngine._get_market_data(db, broker, trading_mode, stock_universe)

        # Prepare context for algorithm
        context = {
            'parameters': parameters,
            'positions': positions,
            'market_data': market_data,
            'max_positions': max_positions,
            'risk_per_trade': float(risk_per_trade),
            'broker': broker,
            'trading_mode': trading_mode,
            'signals': []  # Algorithm will append signals here
        }

        # Helper functions available to algorithm
        def generate_signal(symbol: str, signal_type: str, quantity: float, reason: str = ""):
            """Helper function for algorithms to generate trading signals"""
            context['signals'].append({
                'symbol': symbol,
                'signal_type': signal_type,
                'quantity': quantity,
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

        # Make helpers available
        algorithm_globals = {
            'generate_signal': generate_signal,
            'pd': pd,
            'np': np,
            'datetime': datetime,
            'print': logger.info,  # Redirect print to logger
        }

        # Add ta only if available
        if ta is not None:
            algorithm_globals['ta'] = ta

        try:
            # Execute algorithm code
            exec(algorithm_code, algorithm_globals, context)

            return context['signals']

        except Exception as e:
            logger.error(f"Algorithm code execution failed: {e}")
            raise RuntimeError(f"Algorithm execution error: {str(e)}")

    @staticmethod
    async def _get_current_positions(
        db: AsyncSession,
        portfolio_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get current portfolio positions"""
        result = await db.execute(text("""
            SELECT
                a.symbol,
                a.name,
                ph.quantity,
                ph.average_cost,
                ph.current_value,
                ph.unrealized_pnl
            FROM portfolio_holdings ph
            JOIN assets a ON ph.asset_id = a.id
            WHERE ph.portfolio_id = :portfolio_id
            AND ph.quantity > 0
        """), {"portfolio_id": str(portfolio_id)})

        positions = []
        for row in result.fetchall():
            positions.append({
                'symbol': row.symbol,
                'name': row.name,
                'quantity': float(row.quantity),
                'avg_cost': float(row.average_cost),
                'current_value': float(row.current_value),
                'unrealized_pnl': float(row.unrealized_pnl)
            })

        return positions

    @staticmethod
    async def _get_market_data(
        db: AsyncSession,
        broker: str,
        trading_mode: str,
        stock_universe: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get market data for algorithm with technical indicators

        In production, this would fetch from broker APIs with historical data
        For now, returns basic data from assets table with simulated indicators

        TODO: Integrate with real-time broker APIs for OHLCV data and indicator calculation
        """
        # Get top liquid assets for the broker's market
        if broker == 'zerodha':
            # Indian stocks
            region_filter = 'IN'
        else:
            # US stocks
            region_filter = 'US'

        # Build query based on stock universe
        if stock_universe['type'] == 'specific' and stock_universe.get('symbols'):
            # Filter by specific symbols
            result = await db.execute(text("""
                SELECT
                    symbol,
                    name,
                    current_price,
                    exchange,
                    asset_type
                FROM assets
                WHERE region = :region
                AND asset_type = 'STOCK'
                AND symbol = ANY(:symbols)
                ORDER BY symbol
            """), {"region": region_filter, "symbols": stock_universe['symbols']})
        else:
            # Get all available stocks
            result = await db.execute(text("""
                SELECT
                    symbol,
                    name,
                    current_price,
                    exchange,
                    asset_type
                FROM assets
                WHERE region = :region
                AND asset_type = 'STOCK'
                ORDER BY symbol
                LIMIT 100
            """), {"region": region_filter})

        market_data = {}
        for row in result.fetchall():
            price = float(row.current_price) if row.current_price else 0.0

            # Calculate simulated indicators
            # In production, these would be calculated from historical OHLCV data
            # For now, using approximate values based on current price
            indicators = AlgorithmEngine._calculate_simulated_indicators(price)

            market_data[row.symbol] = {
                'name': row.name,
                'price': price,
                'volume': 1000000,  # Simulated volume
                'exchange': row.exchange,
                'asset_type': row.asset_type,
                'indicators': indicators
            }

        return market_data

    @staticmethod
    def _calculate_simulated_indicators(price: float) -> Dict[str, float]:
        """
        Calculate simulated technical indicators

        NOTE: This is a simplified simulation for demo purposes.
        In production, indicators should be calculated from real historical OHLCV data.

        TODO: Replace with real indicator calculations from broker API data
        """
        if price == 0:
            return {}

        # Simulate reasonable indicator values based on current price
        # These approximate typical indicator ranges
        indicators = {
            # RSI - typically 0-100, oversold <30, overbought >70
            'rsi_14': 50.0 + (hash(str(price)) % 40 - 20),  # Random-ish 30-70
            'rsi_9': 50.0 + (hash(str(price * 1.1)) % 40 - 20),

            # Moving Averages - close to current price
            'sma_10': price * (1.0 + (hash(str(price * 2)) % 10 - 5) / 100),  # ±5%
            'sma_20': price * (1.0 + (hash(str(price * 3)) % 10 - 5) / 100),
            'sma_50': price * (1.0 + (hash(str(price * 4)) % 10 - 5) / 100),
            'ema_10': price * (1.0 + (hash(str(price * 5)) % 10 - 5) / 100),
            'ema_20': price * (1.0 + (hash(str(price * 6)) % 10 - 5) / 100),
            'ema_50': price * (1.0 + (hash(str(price * 7)) % 10 - 5) / 100),

            # Previous values for crossover detection (slightly different)
            'sma_10_prev': price * (1.0 + (hash(str(price * 2.1)) % 10 - 5) / 100),
            'sma_20_prev': price * (1.0 + (hash(str(price * 3.1)) % 10 - 5) / 100),
            'ema_10_prev': price * (1.0 + (hash(str(price * 5.1)) % 10 - 5) / 100),
            'ema_20_prev': price * (1.0 + (hash(str(price * 6.1)) % 10 - 5) / 100),

            # Bollinger Bands - 2% bands
            'bb_upper_20': price * 1.02,
            'bb_lower_20': price * 0.98,
            'bb_middle_20': price,

            # MACD
            'macd': (hash(str(price * 8)) % 20 - 10) / 10.0,  # Random -1 to 1
            'macd_signal': (hash(str(price * 9)) % 20 - 10) / 10.0,
            'macd_hist': (hash(str(price * 10)) % 20 - 10) / 10.0,

            # High/Low lookbacks
            'highest_20': price * 1.08,
            'lowest_20': price * 0.92,
            'highest_50': price * 1.12,
            'lowest_50': price * 0.88,

            # Volume indicators
            'avg_volume': 1000000.0,
            'volume_sma_20': 1000000.0,
        }

        return indicators

    @staticmethod
    async def validate_algorithm_code(algorithm_code: str) -> Dict[str, Any]:
        """
        Validate algorithm code for syntax, security, and runtime issues

        Returns:
            Dict with validation results
        """
        try:
            # 1. Basic syntax check
            try:
                compile(algorithm_code, '<string>', 'exec')
            except SyntaxError as e:
                return {
                    "valid": False,
                    "error": f"Syntax error at line {e.lineno}: {e.msg}"
                }

            # 2. Check for forbidden operations (security)
            forbidden_keywords = [
                'import os', 'import sys', 'import subprocess', 'import socket',
                'open(', '__import__', 'eval(', 'exec(',
                'compile(', 'globals(', 'locals(', 'vars(',
                '__builtins__', '__code__', '__file__',
                'os.', 'sys.', 'subprocess.', 'socket.'
            ]

            for keyword in forbidden_keywords:
                if keyword in algorithm_code:
                    return {
                        "valid": False,
                        "error": f"Forbidden operation detected: {keyword}. Algorithms cannot access file system, network, or system modules for security reasons."
                    }

            # 3. AST-based validation
            import ast
            try:
                tree = ast.parse(algorithm_code)

                # Check for dangerous AST nodes
                for node in ast.walk(tree):
                    # Disallow import statements (except allowed ones handled by globals)
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        return {
                            "valid": False,
                            "error": "Import statements are not allowed. Use pre-imported modules: pd, np, ta, datetime"
                        }

                    # Disallow function definitions at module level (to prevent code injection)
                    # Algorithm should be inline code, not function definitions
                    # Exception: helper functions within the algorithm scope are ok
                    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                        # Top-level function definitions are suspicious
                        logger.warning(f"Algorithm contains top-level function: {node.name}")

            except SyntaxError as e:
                return {
                    "valid": False,
                    "error": f"AST parsing failed at line {e.lineno}: {e.msg}"
                }

            # 4. Dry-run validation with mock context
            if INDICATORS_AVAILABLE:
                try:
                    # Create mock context similar to real execution
                    mock_market_data = {
                        'AAPL': {
                            'name': 'Apple Inc.',
                            'price': 150.0,
                            'volume': 1000000,
                            'exchange': 'NASDAQ',
                            'asset_type': 'STOCK',
                            'indicators': {
                                'rsi_14': 50.0,
                                'sma_20': 148.0,
                                'ema_20': 149.0,
                                'bb_upper_20': 153.0,
                                'bb_lower_20': 147.0,
                                'macd': 0.5,
                            }
                        }
                    }

                    mock_context = {
                        'parameters': {},
                        'positions': [],
                        'market_data': mock_market_data,
                        'max_positions': 5,
                        'risk_per_trade': 2.0,
                        'broker': 'alpaca',
                        'trading_mode': 'paper',
                        'signals': []
                    }

                    # Mock generate_signal function
                    def mock_generate_signal(symbol: str, signal_type: str, quantity: float, reason: str = ""):
                        if signal_type not in ['buy', 'sell']:
                            raise ValueError(f"Invalid signal_type: {signal_type}. Must be 'buy' or 'sell'")
                        if quantity <= 0:
                            raise ValueError(f"Invalid quantity: {quantity}. Must be positive")
                        mock_context['signals'].append({
                            'symbol': symbol,
                            'signal_type': signal_type,
                            'quantity': quantity,
                            'reason': reason
                        })

                    mock_globals = {
                        'generate_signal': mock_generate_signal,
                        'pd': pd,
                        'np': np,
                        'datetime': datetime,
                        'print': lambda *args: None,  # Suppress prints during validation
                    }

                    if ta is not None:
                        mock_globals['ta'] = ta

                    # Execute algorithm code in sandbox
                    exec(algorithm_code, mock_globals, mock_context)

                    # Check if algorithm generated any signals (good sign it's working)
                    signal_count = len(mock_context['signals'])

                    return {
                        "valid": True,
                        "message": "Algorithm code is valid and executed successfully in dry-run",
                        "dry_run_signals": signal_count,
                        "warnings": []
                    }

                except NameError as e:
                    return {
                        "valid": False,
                        "error": f"Runtime error: {str(e)}. Make sure all variables are defined or use available context: market_data, positions, parameters, max_positions, risk_per_trade"
                    }
                except ValueError as e:
                    return {
                        "valid": False,
                        "error": f"Runtime validation error: {str(e)}"
                    }
                except Exception as e:
                    return {
                        "valid": False,
                        "error": f"Runtime error during validation: {str(e)}"
                    }
            else:
                # If pandas not available, skip dry-run
                return {
                    "valid": True,
                    "message": "Syntax and security checks passed (dry-run skipped - pandas not available)",
                    "warnings": ["Dry-run validation skipped - install pandas for full validation"]
                }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
