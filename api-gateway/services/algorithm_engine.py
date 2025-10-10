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
                    max_positions, risk_per_trade
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

            # 7. Execute algorithm code
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
                risk_per_trade=algo.risk_per_trade
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
        risk_per_trade: Decimal
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
        market_data = await AlgorithmEngine._get_market_data(db, broker, trading_mode)

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
        trading_mode: str
    ) -> Dict[str, Any]:
        """
        Get market data for algorithm

        In production, this would fetch from broker APIs
        For now, returns basic data from assets table
        """
        # Get top liquid assets for the broker's market
        if broker == 'zerodha':
            # Indian stocks
            region_filter = 'IN'
        else:
            # US stocks
            region_filter = 'US'

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
            market_data[row.symbol] = {
                'name': row.name,
                'price': float(row.current_price) if row.current_price else 0.0,
                'exchange': row.exchange,
                'asset_type': row.asset_type
            }

        return market_data

    @staticmethod
    async def validate_algorithm_code(algorithm_code: str) -> Dict[str, Any]:
        """
        Validate algorithm code for syntax errors and security issues

        Returns:
            Dict with validation results
        """
        try:
            # Basic syntax check
            compile(algorithm_code, '<string>', 'exec')

            # Check for forbidden operations (basic security)
            forbidden_keywords = ['import os', 'import sys', 'open(', '__import__', 'eval(', 'exec(']

            for keyword in forbidden_keywords:
                if keyword in algorithm_code:
                    return {
                        "valid": False,
                        "error": f"Forbidden operation detected: {keyword}"
                    }

            return {
                "valid": True,
                "message": "Algorithm code is valid"
            }

        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
