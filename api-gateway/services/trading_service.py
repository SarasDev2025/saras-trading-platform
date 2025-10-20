"""
Trading service for managing trading transactions
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import (
    TradingTransaction, Portfolio, Asset, PortfolioHolding, 
    TransactionType, TransactionStatus, OrderType
)
from config.database import get_db_session, DatabaseQuery, CacheManager
from services.portfolio_performance_service import PortfolioPerformanceService
from services.trade_execution_service import TradingExecutionService

logger = logging.getLogger(__name__)


class TradingService:
    """Service class for trading-related operations"""

    @staticmethod
    def calculate_fees(amount: Decimal, transaction_type: TransactionType) -> Decimal:
        """Calculate trading fees - 0.1% of transaction amount, minimum $1"""
        fee_percentage = Decimal('0.001')
        calculated_fee = amount * fee_percentage
        return max(calculated_fee, Decimal('1.00'))

    @staticmethod
    async def create_transaction(transaction_data: Dict[str, Any]) -> TradingTransaction:
        """Create and execute a new trading transaction"""
        async with get_db_session() as session:
            # Calculate amounts
            quantity = Decimal(str(transaction_data['quantity']))
            price_per_unit = Decimal(str(transaction_data['price_per_unit']))
            total_amount = quantity * price_per_unit

            fees = TradingService.calculate_fees(total_amount, transaction_data['transaction_type'])
            net_amount = total_amount + fees if transaction_data['transaction_type'] == TransactionType.BUY else total_amount - fees

            # Validate buying power for BUY orders
            if transaction_data['transaction_type'] == TransactionType.BUY:
                await TradingService._validate_buying_power(
                    session,
                    transaction_data['portfolio_id'],
                    net_amount
                )

            # Extract source information from execution_metadata
            execution_metadata = transaction_data.get('execution_metadata', {})
            source_type = None
            source_id = None

            if 'algorithm_id' in execution_metadata:
                source_type = 'algorithm'
                source_id = execution_metadata['algorithm_id']
            elif 'smallcase_investment_id' in execution_metadata:
                source_type = 'smallcase'
                source_id = execution_metadata['smallcase_investment_id']
            else:
                source_type = 'manual'

            # Create transaction
            transaction = TradingTransaction(
                user_id=transaction_data['user_id'],
                portfolio_id=transaction_data['portfolio_id'],
                asset_id=transaction_data['asset_id'],
                transaction_type=transaction_data['transaction_type'],
                quantity=quantity,
                price_per_unit=price_per_unit,
                total_amount=total_amount,
                fees=fees,
                net_amount=net_amount,
                order_type=transaction_data.get('order_type', OrderType.MARKET),
                notes=transaction_data.get('notes'),
                status=TransactionStatus.PENDING
            )

            session.add(transaction)
            await session.flush()  # Get the transaction ID

            # Execute the transaction using existing immediate logic with source tracking
            await TradingService._execute_transaction(
                session,
                transaction,
                source_type=source_type,
                source_id=source_id
            )

            # Normalise finalisation through the shared execution service so
            # that future broker fills can reuse the same flow.
            metadata = transaction_data.get('execution_metadata') or {"source": "manual_trading_service"}
            await TradingExecutionService.finalize_fill(
                session=session,
                transaction=transaction,
                filled_quantity=transaction.quantity,
                fill_price=transaction.price_per_unit,
                fees=transaction.fees or Decimal("0"),
                fill_status=transaction.status,
                fill_metadata=metadata,
                refresh_snapshot=False,
            )

            await session.commit()
            await session.refresh(transaction)

            try:
                await PortfolioPerformanceService.refresh_snapshot(
                    transaction.portfolio_id,
                    transaction.user_id,
                )
            except Exception as snapshot_error:  # pragma: no cover - best effort logging
                logger.warning(
                    "Failed to refresh performance snapshot after transaction %s: %s",
                    transaction.id,
                    snapshot_error,
                )

            return transaction

    @staticmethod
    async def _validate_buying_power(session: AsyncSession, portfolio_id: uuid.UUID, required_cash: Decimal):
        """Validate that portfolio has sufficient cash for the transaction"""
        # Get current cash balance
        portfolio_result = await session.execute(
            select(Portfolio.cash_balance).where(Portfolio.id == portfolio_id)
        )
        portfolio = portfolio_result.first()

        if not portfolio:
            raise ValueError("Portfolio not found")

        cash_balance = portfolio.cash_balance

        if cash_balance < required_cash:
            raise ValueError(
                f"Insufficient buying power. Required: ${required_cash:,.2f}, "
                f"Available: ${cash_balance:,.2f}"
            )

    @staticmethod
    async def _execute_transaction(
        session: AsyncSession,
        transaction: TradingTransaction,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None
    ):
        """Execute a trading transaction - update holdings and portfolio with source tracking"""
        # Update transaction status
        transaction.status = TransactionStatus.EXECUTED
        transaction.settlement_date = datetime.now(timezone.utc)

        # Get existing holding
        holding_result = await session.execute(
            select(PortfolioHolding).where(
                and_(
                    PortfolioHolding.portfolio_id == transaction.portfolio_id,
                    PortfolioHolding.asset_id == transaction.asset_id
                )
            )
        )
        existing_holding = holding_result.scalar_one_or_none()

        if existing_holding:
            await TradingService._update_existing_holding(
                session,
                existing_holding,
                transaction,
                source_type=source_type,
                source_id=source_id
            )
        elif transaction.transaction_type == TransactionType.BUY:
            await TradingService._create_new_holding(
                session,
                transaction,
                source_type=source_type,
                source_id=source_id
            )
        else:
            raise ValueError("Cannot sell asset that is not owned")
        
        # Update portfolio cash balance
        await TradingService._update_portfolio_cash(session, transaction)
        
        # Update portfolio total value
        await TradingService._update_portfolio_values(session, transaction.portfolio_id)

    @staticmethod
    async def _update_existing_holding(
        session: AsyncSession,
        holding: PortfolioHolding,
        transaction: TradingTransaction,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None
    ):
        """Update existing portfolio holding with optional source tracking"""
        if transaction.transaction_type == TransactionType.BUY:
            # Add to position
            new_quantity = holding.quantity + transaction.quantity
            new_total_cost = holding.total_cost + (transaction.quantity * transaction.price_per_unit)
            new_average_cost = new_total_cost / new_quantity if new_quantity > 0 else Decimal('0')

            holding.quantity = new_quantity
            holding.total_cost = new_total_cost
            holding.average_cost = new_average_cost

            # If holding doesn't have source but this transaction does, set it
            if not holding.source_type and source_type:
                holding.source_type = source_type
                holding.source_id = uuid.UUID(source_id) if source_id else None

        else:  # SELL
            if holding.quantity < transaction.quantity:
                raise ValueError("Insufficient quantity to sell")

            new_quantity = holding.quantity - transaction.quantity
            sold_cost = holding.average_cost * transaction.quantity
            new_total_cost = holding.total_cost - sold_cost
            realized_pnl = (transaction.price_per_unit - holding.average_cost) * transaction.quantity

            holding.quantity = new_quantity
            holding.total_cost = new_total_cost if new_quantity > 0 else Decimal('0')
            holding.realized_pnl = (holding.realized_pnl or Decimal('0')) + realized_pnl

            if new_quantity == 0:
                holding.average_cost = Decimal('0')

        holding.last_updated = datetime.now(timezone.utc)

    @staticmethod
    async def _create_new_holding(
        session: AsyncSession,
        transaction: TradingTransaction,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None
    ):
        """Create new portfolio holding with source tracking"""
        total_cost = transaction.quantity * transaction.price_per_unit

        holding = PortfolioHolding(
            portfolio_id=transaction.portfolio_id,
            asset_id=transaction.asset_id,
            quantity=transaction.quantity,
            average_cost=transaction.price_per_unit,
            total_cost=total_cost,
            source_type=source_type,
            source_id=uuid.UUID(source_id) if source_id else None
        )

        session.add(holding)

    @staticmethod
    async def _update_portfolio_cash(session: AsyncSession, transaction: TradingTransaction):
        """Update portfolio cash balance and track cash impact"""
        # Calculate cash impact (negative for BUY, positive for SELL)
        cash_impact = -transaction.net_amount if transaction.transaction_type == TransactionType.BUY else transaction.net_amount

        # Update portfolio cash balance
        await session.execute(
            update(Portfolio)
            .where(Portfolio.id == transaction.portfolio_id)
            .values(
                cash_balance=Portfolio.cash_balance + cash_impact,
                updated_at=datetime.now(timezone.utc)
            )
        )

        # Get updated cash balance
        portfolio_result = await session.execute(
            select(Portfolio.cash_balance).where(Portfolio.id == transaction.portfolio_id)
        )
        updated_portfolio = portfolio_result.first()
        new_cash_balance = updated_portfolio.cash_balance if updated_portfolio else Decimal('0')

        # Update transaction with cash impact
        await session.execute(
            update(TradingTransaction)
            .where(TradingTransaction.id == transaction.id)
            .values(
                cash_impact=cash_impact,
                cash_balance_after=new_cash_balance
            )
        )

    @staticmethod
    async def _update_portfolio_values(session: AsyncSession, portfolio_id: uuid.UUID):
        """Update portfolio holdings current values and total portfolio value"""
        # Update holding values based on current asset prices
        update_holdings_query = text("""
            UPDATE portfolio_holdings 
            SET 
                current_value = portfolio_holdings.quantity * assets.current_price,
                unrealized_pnl = (portfolio_holdings.quantity * assets.current_price) - portfolio_holdings.total_cost,
                last_updated = CURRENT_TIMESTAMP
            FROM assets
            WHERE portfolio_holdings.asset_id = assets.id 
                AND portfolio_holdings.portfolio_id = :portfolio_id
        """)
        
        await session.execute(update_holdings_query, {"portfolio_id": portfolio_id})
        
        # Update portfolio total value
        update_portfolio_query = text("""
            UPDATE portfolios 
            SET 
                total_value = portfolios.cash_balance + COALESCE((
                    SELECT SUM(current_value) 
                    FROM portfolio_holdings 
                    WHERE portfolio_id = :portfolio_id AND quantity > 0
                ), 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :portfolio_id
        """)
        
        await session.execute(update_portfolio_query, {"portfolio_id": portfolio_id})

    @staticmethod
    async def get_transactions_by_user(user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transactions for a user"""
        query = """
        SELECT 
            t.*,
            a.symbol,
            a.name as asset_name,
            a.asset_type,
            p.name as portfolio_name
        FROM trading_transactions t
        JOIN assets a ON t.asset_id = a.id
        JOIN portfolios p ON t.portfolio_id = p.id
        WHERE t.user_id = $1
        ORDER BY t.transaction_date DESC
        LIMIT $2 OFFSET $3
        """
        
        result = await DatabaseQuery.execute_query(query, [user_id, limit, offset])
        return [dict(row) for row in result]

    @staticmethod
    async def get_transactions_by_portfolio(portfolio_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transactions for a portfolio"""
        query = """
        SELECT 
            t.*,
            a.symbol,
            a.name as asset_name,
            a.asset_type
        FROM trading_transactions t
        JOIN assets a ON t.asset_id = a.id
        WHERE t.portfolio_id = $1
        ORDER BY t.transaction_date DESC
        LIMIT $2 OFFSET $3
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id, limit, offset])
        return [dict(row) for row in result]

    @staticmethod
    async def get_transaction_by_id(transaction_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get transaction by ID with related data"""
        query = """
        SELECT 
            t.*,
            a.symbol,
            a.name as asset_name,
            a.asset_type,
            p.name as portfolio_name,
            u.username
        FROM trading_transactions t
        JOIN assets a ON t.asset_id = a.id
        JOIN portfolios p ON t.portfolio_id = p.id
        JOIN users u ON t.user_id = u.id
        WHERE t.id = $1
        """
        
        result = await DatabaseQuery.execute_query(query, [transaction_id], fetch_one=True)
        return dict(result) if result else None

    @staticmethod
    async def cancel_transaction(transaction_id: uuid.UUID, user_id: uuid.UUID) -> Optional[TradingTransaction]:
        """Cancel a pending transaction"""
        async with get_db_session() as session:
            result = await session.execute(
                select(TradingTransaction).where(
                    and_(
                        TradingTransaction.id == transaction_id,
                        TradingTransaction.user_id == user_id,
                        TradingTransaction.status == TransactionStatus.PENDING
                    )
                )
            )
            transaction = result.scalar_one_or_none()
            
            if transaction:
                transaction.status = TransactionStatus.CANCELLED
                transaction.updated_at = datetime.now(timezone.utc)
                await session.commit()
                
            return transaction

    @staticmethod
    async def get_transaction_stats(user_id: uuid.UUID, portfolio_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get transaction statistics"""
        conditions = ["t.user_id = $1", "t.status = 'executed'"]
        params = [user_id]
        
        if portfolio_id:
            conditions.append("t.portfolio_id = $2")
            params.append(portfolio_id)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(CASE WHEN transaction_type = 'buy' THEN 1 END) as buy_transactions,
            COUNT(CASE WHEN transaction_type = 'sell' THEN 1 END) as sell_transactions,
            COALESCE(SUM(CASE WHEN transaction_type = 'buy' THEN total_amount ELSE 0 END), 0) as total_bought,
            COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN total_amount ELSE 0 END), 0) as total_sold,
            COALESCE(SUM(fees), 0) as total_fees,
            COALESCE(AVG(total_amount), 0) as avg_transaction_size
        FROM trading_transactions t
        WHERE {where_clause}
        """
        
        result = await DatabaseQuery.execute_query(query, params, fetch_one=True)
        return dict(result) if result else {}

    @staticmethod
    async def get_recent_activity(user_id: uuid.UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trading activity"""
        query = """
        SELECT 
            t.id,
            t.transaction_type,
            t.quantity,
            t.price_per_unit,
            t.total_amount,
            t.transaction_date,
            t.status,
            a.symbol,
            a.name as asset_name,
            p.name as portfolio_name
        FROM trading_transactions t
        JOIN assets a ON t.asset_id = a.id
        JOIN portfolios p ON t.portfolio_id = p.id
        WHERE t.user_id = $1
        ORDER BY t.transaction_date DESC
        LIMIT $2
        """
        
        result = await DatabaseQuery.execute_query(query, [user_id, limit])
        return [dict(row) for row in result]

    @staticmethod
    async def get_portfolio_performance_history(portfolio_id: uuid.UUID, days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio performance history"""
        query = """
        WITH daily_values AS (
            SELECT 
                DATE(t.transaction_date) as date,
                p.total_value,
                COALESCE(SUM(
                    CASE 
                        WHEN t.transaction_type = 'buy' THEN -t.net_amount 
                        ELSE t.net_amount 
                    END
                ), 0) as daily_flow
            FROM portfolios p
            LEFT JOIN trading_transactions t ON p.id = t.portfolio_id 
                AND t.status = 'executed'
                AND t.transaction_date >= CURRENT_DATE - INTERVAL '%s days'
            WHERE p.id = $1
            GROUP BY DATE(t.transaction_date), p.total_value
            ORDER BY date DESC
        )
        SELECT * FROM daily_values LIMIT $2
        """ % days
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id, days])
        return [dict(row) for row in result]

    @staticmethod
    async def validate_transaction(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction data before execution"""
        errors = []
        
        # Check if portfolio exists and belongs to user
        portfolio_query = """
        SELECT cash_balance 
        FROM portfolios 
        WHERE id = $1 AND user_id = $2
        """
        
        portfolio_result = await DatabaseQuery.execute_query(
            portfolio_query, 
            [transaction_data['portfolio_id'], transaction_data['user_id']], 
            fetch_one=True
        )
        
        if not portfolio_result:
            errors.append("Portfolio not found or access denied")
            return {"valid": False, "errors": errors}
        
        # Check if asset exists and is active
        asset_query = """
        SELECT current_price, is_active 
        FROM assets 
        WHERE id = $1
        """
        
        asset_result = await DatabaseQuery.execute_query(
            asset_query, 
            [transaction_data['asset_id']], 
            fetch_one=True
        )
        
        if not asset_result:
            errors.append("Asset not found")
        elif not asset_result['is_active']:
            errors.append("Asset is not currently tradeable")
        
        # For buy orders, check sufficient cash
        if transaction_data['transaction_type'] == TransactionType.BUY:
            quantity = Decimal(str(transaction_data['quantity']))
            price = Decimal(str(transaction_data['price_per_unit']))
            total_amount = quantity * price
            fees = TradingService.calculate_fees(total_amount, TransactionType.BUY)
            required_cash = total_amount + fees
            
            if portfolio_result['cash_balance'] < required_cash:
                errors.append(f"Insufficient cash. Required: {required_cash}, Available: {portfolio_result['cash_balance']}")
        
        # For sell orders, check sufficient holdings
        elif transaction_data['transaction_type'] == TransactionType.SELL:
            holding_query = """
            SELECT quantity 
            FROM portfolio_holdings 
            WHERE portfolio_id = $1 AND asset_id = $2
            """
            
            holding_result = await DatabaseQuery.execute_query(
                holding_query, 
                [transaction_data['portfolio_id'], transaction_data['asset_id']], 
                fetch_one=True
            )
            
            available_quantity = holding_result['quantity'] if holding_result else Decimal('0')
            required_quantity = Decimal(str(transaction_data['quantity']))
            
            if available_quantity < required_quantity:
                errors.append(f"Insufficient quantity. Required: {required_quantity}, Available: {available_quantity}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "portfolio_cash": float(portfolio_result['cash_balance']),
            "asset_price": float(asset_result['current_price']) if asset_result else 0
        }
