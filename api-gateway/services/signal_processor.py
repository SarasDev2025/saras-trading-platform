"""
Signal Processor Service
Converts algorithm-generated signals into actual trading orders
Multi-broker support: Zerodha (live) and Alpaca (paper/live)
"""
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.trading_service import TradingService
from models import TransactionType, OrderType

logger = logging.getLogger(__name__)


class SignalProcessor:
    """Process trading signals and execute orders through appropriate broker"""

    @staticmethod
    async def process_signals(
        db: AsyncSession,
        algorithm_id: uuid.UUID,
        execution_id: uuid.UUID,
        signals: List[Dict[str, Any]],
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        broker: str,
        trading_mode: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Process list of signals and execute trades

        Args:
            db: Database session
            algorithm_id: Algorithm UUID
            execution_id: Execution UUID
            signals: List of signal dicts
            user_id: User UUID
            portfolio_id: Portfolio UUID
            broker: 'zerodha' or 'alpaca'
            trading_mode: 'paper' or 'live'
            dry_run: If True, validate but don't execute

        Returns:
            Processing results
        """
        processed_count = 0
        executed_count = 0
        failed_count = 0
        results = []

        logger.info(
            f"Processing {len(signals)} signals for algorithm {algorithm_id} "
            f"via {broker} ({trading_mode})"
        )

        for signal in signals:
            try:
                result = await SignalProcessor._process_single_signal(
                    db=db,
                    algorithm_id=algorithm_id,
                    execution_id=execution_id,
                    signal=signal,
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    broker=broker,
                    trading_mode=trading_mode,
                    dry_run=dry_run
                )

                processed_count += 1
                if result['executed']:
                    executed_count += 1

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process signal {signal}: {e}")
                failed_count += 1
                results.append({
                    'signal': signal,
                    'executed': False,
                    'error': str(e)
                })

        # Update execution stats
        await db.execute(text("""
            UPDATE algorithm_executions
            SET
                orders_placed = :orders_placed,
                orders_filled = :orders_filled
            WHERE id = :execution_id
        """), {
            "orders_placed": processed_count,
            "orders_filled": executed_count,
            "execution_id": str(execution_id)
        })

        await db.commit()

        return {
            'processed': processed_count,
            'executed': executed_count,
            'failed': failed_count,
            'results': results
        }

    @staticmethod
    async def _process_single_signal(
        db: AsyncSession,
        algorithm_id: uuid.UUID,
        execution_id: uuid.UUID,
        signal: Dict[str, Any],
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        broker: str,
        trading_mode: str,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Process a single trading signal"""

        # Extract signal details
        symbol = signal.get('symbol')
        signal_type = signal.get('signal_type', '').lower()
        quantity = signal.get('quantity', 0)
        suggested_price = signal.get('suggested_price')
        reason = signal.get('reason', '')

        # Validate signal
        if not symbol or not signal_type or quantity <= 0:
            raise ValueError(f"Invalid signal: {signal}")

        if signal_type not in ['buy', 'sell', 'hold']:
            raise ValueError(f"Invalid signal type: {signal_type}")

        # Skip hold signals
        if signal_type == 'hold':
            return {
                'signal': signal,
                'executed': False,
                'reason': 'Hold signal - no action taken'
            }

        # Get asset ID
        asset_result = await db.execute(text("""
            SELECT id, current_price
            FROM assets
            WHERE symbol = :symbol
            LIMIT 1
        """), {"symbol": symbol})

        asset = asset_result.fetchone()
        if not asset:
            raise ValueError(f"Asset not found: {symbol}")

        asset_id = asset.id
        current_price = float(asset.current_price) if asset.current_price else None

        # Use suggested price or current price
        execution_price = suggested_price or current_price
        if not execution_price:
            raise ValueError(f"No price available for {symbol}")

        # Create signal record
        signal_result = await db.execute(text("""
            INSERT INTO algorithm_signals (
                algorithm_id, execution_id, user_id, portfolio_id, asset_id,
                signal_type, quantity, suggested_price,
                reason, generated_at, executed
            )
            VALUES (
                :algorithm_id, :execution_id, :user_id, :portfolio_id, :asset_id,
                :signal_type, :quantity, :suggested_price,
                :reason, :generated_at, :executed
            )
            RETURNING id
        """), {
            "algorithm_id": str(algorithm_id),
            "execution_id": str(execution_id),
            "user_id": str(user_id),
            "portfolio_id": str(portfolio_id),
            "asset_id": str(asset_id),
            "signal_type": signal_type,
            "quantity": quantity,
            "suggested_price": execution_price,
            "reason": reason,
            "generated_at": datetime.now(timezone.utc),
            "executed": False
        })

        signal_id = signal_result.scalar()

        # If dry run, don't execute
        if dry_run:
            await db.execute(text("""
                UPDATE algorithm_signals
                SET execution_status = 'simulated'
                WHERE id = :signal_id
            """), {"signal_id": str(signal_id)})
            await db.commit()
            return {
                'signal': signal,
                'signal_id': str(signal_id),
                'executed': False,
                'reason': 'Dry run - signal recorded but not executed'
            }

        # Validate buy/sell rules
        validation = await SignalProcessor._validate_signal(
            db, signal_type, quantity, execution_price, portfolio_id, asset_id
        )

        if not validation['valid']:
            # Update signal as rejected
            await db.execute(text("""
                UPDATE algorithm_signals
                SET execution_status = 'rejected'
                WHERE id = :signal_id
            """), {"signal_id": str(signal_id)})

            await db.commit()

            return {
                'signal': signal,
                'signal_id': str(signal_id),
                'executed': False,
                'reason': validation['reason']
            }

        # Execute trade via TradingService
        try:
            transaction_type = TransactionType.BUY if signal_type == 'buy' else TransactionType.SELL

            transaction_data = {
                'user_id': user_id,
                'portfolio_id': portfolio_id,
                'asset_id': asset_id,
                'transaction_type': transaction_type,
                'quantity': Decimal(str(quantity)),
                'price_per_unit': Decimal(str(execution_price)),
                'order_type': OrderType.MARKET,
                'notes': f"Algorithm: {algorithm_id} | {reason}",
                'execution_metadata': {
                    'source': 'algorithm_signal',
                    'algorithm_id': str(algorithm_id),
                    'execution_id': str(execution_id)
                }
            }

            transaction = await TradingService.create_transaction(transaction_data)

            # Update signal with transaction reference
            await db.execute(text("""
                UPDATE algorithm_signals
                SET
                    executed = true,
                    transaction_id = :transaction_id,
                    execution_price = :execution_price,
                    executed_at = :executed_at,
                    execution_status = 'filled'
                WHERE id = :signal_id
            """), {
                "transaction_id": str(transaction.id),
                "execution_price": execution_price,
                "executed_at": datetime.now(timezone.utc),
                "signal_id": str(signal_id)
            })

            await db.commit()

            logger.info(
                f"Executed {signal_type} signal for {symbol}: "
                f"{quantity} @ ${execution_price}"
            )

            return {
                'signal': signal,
                'signal_id': str(signal_id),
                'transaction_id': str(transaction.id),
                'executed': True,
                'execution_price': execution_price
            }

        except Exception as e:
            logger.error(f"Failed to execute signal {signal_id}: {e}")

            # Update signal as failed
            await db.execute(text("""
                UPDATE algorithm_signals
                SET
                    execution_status = 'failed',
                    executed_at = :executed_at
                WHERE id = :signal_id
            """), {
                "executed_at": datetime.now(timezone.utc),
                "signal_id": str(signal_id)
            })

            await db.commit()

            raise

    @staticmethod
    async def _validate_signal(
        db: AsyncSession,
        signal_type: str,
        quantity: float,
        price: float,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Validate if signal can be executed

        Checks:
        - Buy: Sufficient cash
        - Sell: Sufficient holdings
        """
        if signal_type == 'buy':
            # Check cash balance
            portfolio_result = await db.execute(text("""
                SELECT cash_balance
                FROM portfolios
                WHERE id = :portfolio_id
            """), {"portfolio_id": str(portfolio_id)})

            portfolio = portfolio_result.fetchone()
            if not portfolio:
                return {'valid': False, 'reason': 'Portfolio not found'}

            required_cash = Decimal(str(quantity * price))
            available_cash = portfolio.cash_balance

            if available_cash < required_cash:
                return {
                    'valid': False,
                    'reason': f'Insufficient cash: need ${required_cash}, have ${available_cash}'
                }

            return {'valid': True}

        elif signal_type == 'sell':
            # Check holdings
            holdings_result = await db.execute(text("""
                SELECT quantity
                FROM portfolio_holdings
                WHERE portfolio_id = :portfolio_id
                AND asset_id = :asset_id
            """), {
                "portfolio_id": str(portfolio_id),
                "asset_id": str(asset_id)
            })

            holding = holdings_result.fetchone()

            if not holding:
                return {'valid': False, 'reason': 'No holdings to sell'}

            available_qty = float(holding.quantity)
            if available_qty < quantity:
                return {
                    'valid': False,
                    'reason': f'Insufficient quantity: need {quantity}, have {available_qty}'
                }

            return {'valid': True}

        return {'valid': False, 'reason': 'Invalid signal type'}

    @staticmethod
    async def get_pending_signals(
        db: AsyncSession,
        algorithm_id: uuid.UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pending signals for an algorithm"""

        result = await db.execute(text("""
            SELECT
                s.id,
                s.signal_type,
                s.quantity,
                s.suggested_price,
                s.generated_at,
                s.expires_at,
                s.reason,
                a.symbol,
                a.name as asset_name
            FROM algorithm_signals s
            JOIN assets a ON s.asset_id = a.id
            WHERE s.algorithm_id = :algorithm_id
            AND s.executed = false
            AND (s.expires_at IS NULL OR s.expires_at > NOW())
            ORDER BY s.generated_at DESC
            LIMIT :limit
        """), {
            "algorithm_id": str(algorithm_id),
            "limit": limit
        })

        signals = []
        for row in result.fetchall():
            signals.append({
                'id': str(row.id),
                'symbol': row.symbol,
                'asset_name': row.asset_name,
                'signal_type': row.signal_type,
                'quantity': float(row.quantity),
                'suggested_price': float(row.suggested_price) if row.suggested_price else None,
                'generated_at': row.generated_at.isoformat(),
                'expires_at': row.expires_at.isoformat() if row.expires_at else None,
                'reason': row.reason
            })

        return signals
