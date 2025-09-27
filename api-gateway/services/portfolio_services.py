"""
Portfolio service for managing portfolio operations
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Portfolio, PortfolioHolding, Asset, User, TradingTransaction, TransactionStatus
from ..config.database import get_db_session, DatabaseQuery, CacheManager


class PortfolioService:
    """Service class for portfolio-related operations"""

    @staticmethod
    async def create_portfolio(user_id: uuid.UUID, portfolio_data: Dict[str, Any]) -> Portfolio:
        """Create a new portfolio"""
        async with get_db_session() as session:
            portfolio = Portfolio(
                user_id=user_id,
                name=portfolio_data['name'],
                description=portfolio_data.get('description'),
                cash_balance=Decimal(str(portfolio_data.get('initial_cash', 0))),
                total_value=Decimal(str(portfolio_data.get('initial_cash', 0)))
            )
            
            session.add(portfolio)
            await session.commit()
            await session.refresh(portfolio)
            
            return portfolio

    @staticmethod
    async def find_by_id(portfolio_id: uuid.UUID) -> Optional[Portfolio]:
        """Find portfolio by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def find_by_user_id(user_id: uuid.UUID) -> List[Portfolio]:
        """Find all portfolios for a user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Portfolio)
                .where(Portfolio.user_id == user_id)
                .order_by(Portfolio.created_at)
            )
            return result.scalars().all()

    @staticmethod
    async def get_portfolio_with_holdings(portfolio_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get portfolio with all holdings"""
        # Check cache first
        cache_key = f"portfolio:{portfolio_id}"
        cached_data = await CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        query = """
        SELECT 
            p.id, p.user_id, p.name, p.description, p.total_value, 
            p.cash_balance, p.currency, p.is_default, p.created_at, p.updated_at,
            COALESCE(
                json_agg(
                    CASE 
                        WHEN ph.id IS NOT NULL THEN
                            json_build_object(
                                'id', ph.id,
                                'asset_id', ph.asset_id,
                                'symbol', a.symbol,
                                'asset_name', a.name,
                                'asset_type', a.asset_type,
                                'quantity', ph.quantity,
                                'average_cost', ph.average_cost,
                                'total_cost', ph.total_cost,
                                'current_price', a.current_price,
                                'current_value', ph.current_value,
                                'unrealized_pnl', ph.unrealized_pnl,
                                'realized_pnl', ph.realized_pnl,
                                'last_updated', ph.last_updated
                            )
                        ELSE NULL
                    END
                ) FILTER (WHERE ph.id IS NOT NULL), 
                '[]'::json
            ) as holdings
        FROM portfolios p
        LEFT JOIN portfolio_holdings ph ON p.id = ph.portfolio_id AND ph.quantity > 0
        LEFT JOIN assets a ON ph.asset_id = a.id
        WHERE p.id = $1
        GROUP BY p.id
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id], fetch_one=True)
        
        if result:
            portfolio_data = dict(result)
            # Cache for 5 minutes
            await CacheManager.set(cache_key, portfolio_data, 300)
            return portfolio_data
        
        return None

    @staticmethod
    async def get_user_portfolios_with_summary(user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get user's portfolios with summary statistics"""
        query = """
        SELECT 
            p.id, p.name, p.description, p.total_value, p.cash_balance, 
            p.currency, p.is_default, p.created_at, p.updated_at,
            COUNT(ph.id) as holding_count,
            COALESCE(SUM(ph.current_value), 0) as holdings_value,
            COALESCE(SUM(ph.unrealized_pnl), 0) as total_unrealized_pnl,
            COALESCE(SUM(ph.realized_pnl), 0) as total_realized_pnl
        FROM portfolios p
        LEFT JOIN portfolio_holdings ph ON p.id = ph.portfolio_id AND ph.quantity > 0
        WHERE p.user_id = $1
        GROUP BY p.id
        ORDER BY p.is_default DESC, p.created_at
        """
        
        result = await DatabaseQuery.execute_query(query, [user_id])
        return [dict(row) for row in result]

    @staticmethod
    async def update_portfolio_info(portfolio_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[Portfolio]:
        """Update portfolio information"""
        allowed_fields = ['name', 'description']
        
        # Filter updates to only allowed fields
        filtered_updates = {
            key: value for key, value in updates.items() 
            if key in allowed_fields
        }
        
        if not filtered_updates:
            raise ValueError("No valid fields to update")

        async with get_db_session() as session:
            await session.execute(
                update(Portfolio)
                .where(Portfolio.id == portfolio_id)
                .values(**filtered_updates, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            # Clear cache
            await CacheManager.delete(f"portfolio:{portfolio_id}")
            
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def add_cash(portfolio_id: uuid.UUID, amount: Decimal) -> Optional[Portfolio]:
        """Add cash to portfolio"""
        async with get_db_session() as session:
            await session.execute(
                update(Portfolio)
                .where(Portfolio.id == portfolio_id)
                .values(
                    cash_balance=Portfolio.cash_balance + amount,
                    total_value=Portfolio.total_value + amount,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
            
            # Clear cache
            await CacheManager.delete(f"portfolio:{portfolio_id}")
            
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def withdraw_cash(portfolio_id: uuid.UUID, amount: Decimal) -> Portfolio:
        """Withdraw cash from portfolio"""
        async with get_db_session() as session:
            # Check current cash balance
            result = await session.execute(
                select(Portfolio.cash_balance).where(Portfolio.id == portfolio_id)
            )
            current_cash = result.scalar_one_or_none()
            
            if current_cash is None:
                raise ValueError("Portfolio not found")
            
            if current_cash < amount:
                raise ValueError("Insufficient cash balance")
            
            # Update portfolio
            await session.execute(
                update(Portfolio)
                .where(Portfolio.id == portfolio_id)
                .values(
                    cash_balance=Portfolio.cash_balance - amount,
                    total_value=Portfolio.total_value - amount,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
            
            # Clear cache
            await CacheManager.delete(f"portfolio:{portfolio_id}")
            
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one()

    @staticmethod
    async def get_performance_metrics(portfolio_id: uuid.UUID, period: str = "30d") -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        # Calculate date range based on period
        date_filter_map = {
            "7d": "7 days",
            "30d": "30 days", 
            "90d": "90 days",
            "1y": "1 year"
        }
        
        interval = date_filter_map.get(period, "30 days")
        cache_key = f"portfolio:{portfolio_id}:performance:{period}"
        
        # Check cache
        cached_metrics = await CacheManager.get(cache_key)
        if cached_metrics:
            return cached_metrics

        query = f"""
        WITH portfolio_metrics AS (
            SELECT 
                p.id,
                p.total_value,
                p.cash_balance,
                COALESCE(SUM(ph.unrealized_pnl), 0) as total_unrealized_pnl,
                COALESCE(SUM(ph.realized_pnl), 0) as total_realized_pnl,
                COALESCE(SUM(ph.current_value), 0) as holdings_value
            FROM portfolios p
            LEFT JOIN portfolio_holdings ph ON p.id = ph.portfolio_id
            WHERE p.id = $1
            GROUP BY p.id
        ),
        transaction_metrics AS (
            SELECT 
                COUNT(*) as transaction_count,
                COALESCE(SUM(CASE WHEN transaction_type = 'buy' THEN total_amount ELSE 0 END), 0) as total_bought,
                COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN total_amount ELSE 0 END), 0) as total_sold,
                COALESCE(SUM(fees), 0) as total_fees
            FROM trading_transactions 
            WHERE portfolio_id = $1 
                AND status = 'executed' 
                AND transaction_date >= CURRENT_DATE - INTERVAL '{interval}'
        )
        SELECT 
            pm.*,
            tm.*,
            CASE 
                WHEN (tm.total_bought - tm.total_sold) > 0 THEN 
                    ((pm.total_value - (tm.total_bought - tm.total_sold)) / (tm.total_bought - tm.total_sold)) * 100
                ELSE 0 
            END as return_percentage
        FROM portfolio_metrics pm
        CROSS JOIN transaction_metrics tm
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id], fetch_one=True)
        
        if result:
            metrics = dict(result)
            # Cache for 10 minutes
            await CacheManager.set(cache_key, metrics, 600)
            return metrics
        
        return {}

    @staticmethod
    async def get_asset_allocation(portfolio_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get asset allocation breakdown"""
        query = """
        SELECT 
            a.asset_type,
            a.symbol,
            a.name,
            ph.quantity,
            ph.current_value,
            (ph.current_value / NULLIF(p.total_value, 0)) * 100 as allocation_percentage
        FROM portfolio_holdings ph
        JOIN assets a ON ph.asset_id = a.id
        JOIN portfolios p ON ph.portfolio_id = p.id
        WHERE ph.portfolio_id = $1 AND ph.quantity > 0
        ORDER BY ph.current_value DESC
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id])
        return [dict(row) for row in result]

    @staticmethod
    async def get_top_holdings(portfolio_id: uuid.UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top holdings by value"""
        query = """
        SELECT 
            a.symbol,
            a.name,
            ph.quantity,
            ph.average_cost,
            ph.current_value,
            ph.unrealized_pnl,
            CASE 
                WHEN ph.total_cost > 0 THEN 
                    ((ph.current_value - ph.total_cost) / ph.total_cost) * 100
                ELSE 0
            END as return_percentage
        FROM portfolio_holdings ph
        JOIN assets a ON ph.asset_id = a.id
        WHERE ph.portfolio_id = $1 AND ph.quantity > 0
        ORDER BY ph.current_value DESC
        LIMIT $2
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id, limit])
        return [dict(row) for row in result]

    @staticmethod
    async def set_default_portfolio(user_id: uuid.UUID, portfolio_id: uuid.UUID) -> Optional[Portfolio]:
        """Set portfolio as default for user"""
        async with get_db_session() as session:
            # Remove default flag from all user portfolios
            await session.execute(
                update(Portfolio)
                .where(Portfolio.user_id == user_id)
                .values(is_default=False)
            )
            
            # Set the specified portfolio as default
            await session.execute(
                update(Portfolio)
                .where(and_(Portfolio.id == portfolio_id, Portfolio.user_id == user_id))
                .values(is_default=True, updated_at=datetime.now(timezone.utc))
            )
            
            await session.commit()
            
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def delete_portfolio(portfolio_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete portfolio with validation"""
        async with get_db_session() as session:
            # Check if this is the only portfolio
            portfolio_count_result = await session.execute(
                select(func.count()).select_from(Portfolio).where(Portfolio.user_id == user_id)
            )
            portfolio_count = portfolio_count_result.scalar_one()
            
            if portfolio_count <= 1:
                raise ValueError("Cannot delete the only portfolio. Users must have at least one portfolio.")
            
            # Check if portfolio has holdings
            holdings_count_result = await session.execute(
                select(func.count()).select_from(PortfolioHolding)
                .where(and_(PortfolioHolding.portfolio_id == portfolio_id, PortfolioHolding.quantity > 0))
            )
            holdings_count = holdings_count_result.scalar_one()
            
            if holdings_count > 0:
                raise ValueError("Cannot delete portfolio with existing holdings. Please sell all positions first.")
            
            # Check cash balance
            portfolio_result = await session.execute(
                select(Portfolio.cash_balance)
                .where(and_(Portfolio.id == portfolio_id, Portfolio.user_id == user_id))
            )
            portfolio = portfolio_result.first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            if portfolio.cash_balance > 0:
                raise ValueError("Cannot delete portfolio with cash balance. Please withdraw all funds first.")
            
            # Delete the portfolio
            await session.execute(
                delete(Portfolio)
                .where(and_(Portfolio.id == portfolio_id, Portfolio.user_id == user_id))
            )
            
            await session.commit()
            return True

    @staticmethod
    async def refresh_portfolio_values(portfolio_id: uuid.UUID) -> Optional[Portfolio]:
        """Refresh portfolio values based on current asset prices"""
        async with get_db_session() as session:
            # Update holding values based on current asset prices
            update_holdings_query = """
            UPDATE portfolio_holdings 
            SET 
                current_value = ph.quantity * a.current_price,
                unrealized_pnl = (ph.quantity * a.current_price) - ph.total_cost,
                last_updated = CURRENT_TIMESTAMP
            FROM assets a
            WHERE ph.asset_id = a.id AND ph.portfolio_id = $1
            """
            
            await DatabaseQuery.execute_query(update_holdings_query, [portfolio_id], fetch_all=False)
            
            # Update portfolio total value
            update_portfolio_query = """
            UPDATE portfolios 
            SET 
                total_value = cash_balance + COALESCE((
                    SELECT SUM(current_value) 
                    FROM portfolio_holdings 
                    WHERE portfolio_id = $1 AND quantity > 0
                ), 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """
            
            await DatabaseQuery.execute_query(update_portfolio_query, [portfolio_id], fetch_all=False)
            
            # Clear cache
            await CacheManager.delete(f"portfolio:{portfolio_id}")
            
            result = await session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_diversification_score(portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Calculate diversification score and asset breakdown"""
        query = """
        WITH asset_allocation AS (
            SELECT 
                a.asset_type,
                SUM(ph.current_value) as type_value,
                COUNT(*) as asset_count
            FROM portfolio_holdings ph
            JOIN assets a ON ph.asset_id = a.id
            WHERE ph.portfolio_id = $1 AND ph.quantity > 0
            GROUP BY a.asset_type
        ),
        portfolio_total AS (
            SELECT total_value FROM portfolios WHERE id = $1
        )
        SELECT 
            aa.asset_type,
            aa.type_value,
            aa.asset_count,
            (aa.type_value / NULLIF(pt.total_value, 0)) * 100 as percentage,
            POWER((aa.type_value / NULLIF(pt.total_value, 0)), 2) as hhi_component
        FROM asset_allocation aa
        CROSS JOIN portfolio_total pt
        """
        
        result = await DatabaseQuery.execute_query(query, [portfolio_id])
        allocations = [dict(row) for row in result]
        
        # Calculate Herfindahl-Hirschman Index
        hhi = sum(float(row['hhi_component'] or 0) for row in allocations)
        
        # Convert HHI to diversification score (0-100, higher is more diversified)
        diversification_score = max(0, 100 - (hhi * 100))
        
        return {
            "diversification_score": round(diversification_score),
            "asset_type_breakdown": [
                {
                    "asset_type": row["asset_type"],
                    "percentage": round(float(row["percentage"] or 0), 2),
                    "asset_count": row["asset_count"],
                    "value": float(row["type_value"] or 0)
                }
                for row in allocations
            ],
            "concentration_index": hhi
        }