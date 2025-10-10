from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Any, Dict, Annotated
from decimal import Decimal
import uuid
import re
from config.database import get_db
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user
from services.portfolio_services import PortfolioService
from services.portfolio_performance_service import PortfolioPerformanceService

router = APIRouter()

logger = logging.getLogger(__name__)

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    value: float

class Portfolio(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    currency: str = "USD"
    total_value: float = 0.0

class CreatePortfolio(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = "USD"

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None

# Get current authenticated user
# This will be injected by FastAPI's dependency injection

def validate_uuid(portfolio_id: str) -> str:
    """Validate and handle portfolio ID, return demo portfolio for invalid UUIDs"""
    # Check if it's a valid UUID format
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    if uuid_pattern.match(portfolio_id):
        return portfolio_id
    else:
        # Return demo portfolio ID for invalid UUIDs like "portfolio-id"
        return "87654321-4321-4321-4321-210987654321"

# Mock data for portfolios
mock_portfolios = [
    {
        "id": "portfolio-1",
        "name": "Growth Portfolio",
        "description": "High growth stocks",
        "currency": "USD",
        "total_value": 25000.0
    },
    {
        "id": "portfolio-2", 
        "name": "Conservative Portfolio",
        "description": "Stable dividend stocks",
        "currency": "USD",
        "total_value": 15000.0
    }
]

@router.get("", response_model=APIResponse)
@router.get("/", response_model=APIResponse)
async def get_portfolios(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get all portfolios for the current user in their current trading mode"""
    try:
        user_id = current_user["id"]

        # Get user's current trading mode
        user_result = await db.execute(text("""
            SELECT trading_mode FROM users WHERE id = :user_id
        """), {"user_id": user_id})
        user_mode = user_result.scalar_one()

        # Filter portfolios by trading mode
        result = await db.execute(text("""
            SELECT p.id, p.name, p.description, p.currency, p.total_value, p.cash_balance, p.trading_mode
            FROM portfolios p
            WHERE p.user_id = :user_id AND p.trading_mode = :trading_mode
            ORDER BY p.created_at
        """), {"user_id": user_id, "trading_mode": user_mode})
        
        portfolios = []
        for row in result:
            portfolios.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "currency": row.currency,
                "total_value": float(row.total_value),
                "cash_balance": float(row.cash_balance)
            })
        
        return APIResponse(success=True, data=portfolios)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolios: {str(e)}")

@router.post("/", response_model=APIResponse)
async def create_portfolio(
    portfolio: CreatePortfolio,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio"""
    try:
        user_id = current_user["id"]
        portfolio_id = str(uuid.uuid4())
        
        await db.execute(text("""
            INSERT INTO portfolios (id, user_id, name, description, currency, total_value, cash_balance)
            VALUES (:id, :user_id, :name, :description, :currency, 0.0, 0.0)
        """), {
            "id": portfolio_id,
            "user_id": user_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "currency": portfolio.currency
        })
        await db.commit()
        
        new_portfolio = {
            "id": portfolio_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "currency": portfolio.currency,
            "total_value": 0.0,
            "cash_balance": 0.0
        }
        
        return APIResponse(success=True, data=new_portfolio, message="Portfolio created successfully")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create portfolio: {str(e)}")

# Paper Trading Endpoints - Must be before /{portfolio_id} to avoid route conflicts

@router.get("/cash-balance", response_model=APIResponse)
async def get_cash_balance(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get current cash balance for user's default portfolio in current trading mode

    **Returns:**
    Cash balance and buying power
    """
    try:
        user_id = current_user["id"]

        # Get user's current trading mode
        user_result = await db.execute(text("""
            SELECT trading_mode FROM users WHERE id = :user_id
        """), {"user_id": user_id})
        user_mode = user_result.scalar_one()

        # Get default portfolio in current trading mode
        result = await db.execute(
            text("""
                SELECT id, cash_balance, total_value
                FROM portfolios
                WHERE user_id = :user_id AND trading_mode = :trading_mode AND is_default = true
                LIMIT 1
            """),
            {"user_id": user_id, "trading_mode": user_mode}
        )

        portfolio = result.fetchone()

        if not portfolio:
            raise HTTPException(status_code=404, detail="No default portfolio found")

        return APIResponse(
            success=True,
            data={
                "portfolio_id": str(portfolio.id),
                "cash_balance": float(portfolio.cash_balance),
                "buying_power": float(portfolio.cash_balance),  # For paper trading, buying power = cash
                "total_value": float(portfolio.total_value)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cash balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cash balance: {str(e)}")

class AddFundsRequest(BaseModel):
    portfolio_id: str
    amount: float

@router.post("/add-funds", response_model=APIResponse)
async def add_funds(
    request: AddFundsRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Add virtual funds to portfolio for paper trading

    **Parameters:**
    - **portfolio_id**: Portfolio ID to add funds to
    - **amount**: Amount to add (min $100, max $1,000,000)

    **Returns:**
    Updated portfolio with new cash balance
    """
    try:
        user_id = current_user["id"]
        portfolio_id = uuid.UUID(request.portfolio_id)
        amount = Decimal(str(request.amount))

        # Use the service to add funds
        updated_portfolio = await PortfolioService.add_funds(
            portfolio_id=portfolio_id,
            user_id=uuid.UUID(user_id),
            amount=amount
        )

        return APIResponse(
            success=True,
            data={
                "portfolio_id": str(updated_portfolio.id),
                "cash_balance": float(updated_portfolio.cash_balance),
                "total_value": float(updated_portfolio.total_value),
                "amount_added": float(amount)
            },
            message=f"Successfully added ${amount:,.2f} to portfolio"
        )

    except ValueError as e:
        logger.error(f"Validation error adding funds: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add funds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add funds: {str(e)}")

# Portfolio-specific endpoints

@router.get("/{portfolio_id}", response_model=APIResponse)
async def get_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific portfolio"""
    try:
        # Validate and fix portfolio ID
        portfolio_id = validate_uuid(portfolio_id)
        
        result = await db.execute(text("""
            SELECT p.id, p.name, p.description, p.currency, p.total_value, p.cash_balance
            FROM portfolios p 
            WHERE p.id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        portfolio = {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "currency": row.currency,
            "total_value": float(row.total_value),
            "cash_balance": float(row.cash_balance)
        }
        
        return APIResponse(success=True, data=portfolio)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio: {str(e)}")

@router.put("/{portfolio_id}", response_model=APIResponse)
async def update_portfolio(portfolio_id: str, updates: dict, db: AsyncSession = Depends(get_db)):
    """Update a portfolio"""
    try:
        # Check if portfolio exists
        result = await db.execute(text("""
            SELECT id FROM portfolios WHERE id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Build update query dynamically
        update_fields = []
        params = {"portfolio_id": portfolio_id}
        
        allowed_fields = ["name", "description", "currency"]
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = :{field}")
                params[field] = updates[field]
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        query = f"UPDATE portfolios SET {', '.join(update_fields)} WHERE id = :portfolio_id"
        await db.execute(text(query), params)
        await db.commit()
        
        # Fetch updated portfolio
        result = await db.execute(text("""
            SELECT p.id, p.name, p.description, p.currency, p.total_value, p.cash_balance
            FROM portfolios p WHERE p.id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        row = result.fetchone()
        portfolio = {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "currency": row.currency,
            "total_value": float(row.total_value),
            "cash_balance": float(row.cash_balance)
        }
        
        return APIResponse(success=True, data=portfolio, message="Portfolio updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update portfolio: {str(e)}")

@router.delete("/{portfolio_id}", response_model=APIResponse)
async def delete_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a portfolio"""
    try:
        # Check if portfolio exists
        result = await db.execute(text("""
            SELECT id FROM portfolios WHERE id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Delete related data first (due to foreign key constraints)
        await db.execute(text("""
            DELETE FROM portfolio_holdings WHERE portfolio_id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        await db.execute(text("""
            DELETE FROM trading_transactions WHERE portfolio_id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        # Delete the portfolio
        await db.execute(text("""
            DELETE FROM portfolios WHERE id = :portfolio_id
        """), {"portfolio_id": portfolio_id})
        
        await db.commit()
        return APIResponse(success=True, message="Portfolio deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete portfolio: {str(e)}")

@router.get("/{portfolio_id}/positions", response_model=APIResponse)
async def get_portfolio_positions(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Get positions for a specific portfolio"""
    try:
        # Validate and fix portfolio ID
        portfolio_id = validate_uuid(portfolio_id)
        
        result = await db.execute(text("""
            SELECT 
                a.symbol,
                a.name as asset_name,
                a.asset_type,
                ph.quantity,
                a.current_price,
                ph.current_value as market_value,
                ph.average_cost as cost_basis,
                ph.unrealized_pnl
            FROM portfolio_holdings ph
            JOIN assets a ON ph.asset_id = a.id
            WHERE ph.portfolio_id = :portfolio_id
            AND ph.quantity > 0
            ORDER BY ph.current_value DESC
        """), {"portfolio_id": portfolio_id})
        
        positions = []
        rows = result.fetchall()
        
        for row in rows:
            # Calculate unrealized P&L percentage
            unrealized_pnl_percent = 0.0
            if row.cost_basis and float(row.cost_basis) > 0:
                unrealized_pnl_percent = (float(row.unrealized_pnl or 0) / float(row.cost_basis)) * 100
            
            positions.append({
                "id": f"{portfolio_id}-{row.symbol}",  # Generate ID for Web UI
                "symbol": row.symbol,
                "asset_name": row.asset_name,
                "assetType": row.asset_type,  # camelCase for Web UI
                "quantity": float(row.quantity),
                "avgPrice": float(row.cost_basis) if row.cost_basis else 0.0,  # Web UI expects avgPrice
                "currentPrice": float(row.current_price) if row.current_price else 0.0,  # camelCase
                "marketValue": float(row.market_value) if row.market_value else 0.0,  # camelCase
                "unrealizedPnL": float(row.unrealized_pnl) if row.unrealized_pnl else 0.0,  # camelCase
                "unrealized_pnl_percent": unrealized_pnl_percent,
                # Keep snake_case versions for backward compatibility
                "asset_type": row.asset_type,
                "current_price": float(row.current_price) if row.current_price else 0.0,
                "market_value": float(row.market_value) if row.market_value else 0.0,
                "cost_basis": float(row.cost_basis) if row.cost_basis else 0.0,
                "unrealized_pnl": float(row.unrealized_pnl) if row.unrealized_pnl else 0.0
            })
        
        return APIResponse(success=True, data=positions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@router.get("/{portfolio_id}/trades", response_model=APIResponse)
async def get_portfolio_trades(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Get trades for a specific portfolio"""
    logger.info(f"[DEBUG] Getting trades for portfolio: {portfolio_id}")
    
    try:
        # Log the incoming request
        logger.debug(f"[DEBUG] Incoming request for portfolio_id: {portfolio_id}")
        
        # Validate and fix portfolio ID
        portfolio_id = validate_uuid(portfolio_id)
        logger.debug(f"[DEBUG] Validated portfolio ID: {portfolio_id}")
        
        # First, verify the portfolio exists
        portfolio_query = "SELECT id FROM portfolios WHERE id = :portfolio_id"
        logger.debug(f"[DEBUG] Executing portfolio check query: {portfolio_query}")
        
        portfolio = await db.execute(
            text(portfolio_query),
            {"portfolio_id": portfolio_id}
        )
        portfolio_exists = portfolio.fetchone() is not None
        logger.debug(f"[DEBUG] Portfolio exists: {portfolio_exists}")
        
        if not portfolio_exists:
            error_msg = f"Portfolio {portfolio_id} not found"
            logger.error(f"[ERROR] {error_msg}")
            return APIResponse(success=False, error=error_msg)
        
        # Get trades with all required fields
        query = """
            SELECT 
                t.id,
                a.symbol,
                t.transaction_type,
                t.quantity,
                t.price_per_unit,
                t.total_amount,
                t.status,
                t.transaction_date as created_at,
                t.settlement_date as filled_at
            FROM trading_transactions t
            JOIN assets a ON t.asset_id = a.id
            WHERE t.portfolio_id = :portfolio_id
            ORDER BY t.transaction_date DESC
            LIMIT 50
        """
        logger.debug(f"[DEBUG] Executing query: {query}")
        logger.debug(f"[DEBUG] With params: portfolio_id={portfolio_id}")
        
        try:
            result = await db.execute(text(query), {"portfolio_id": portfolio_id})
            rows = result.mappings().all()
            logger.debug(f"[DEBUG] Query executed successfully. Found {len(rows)} trades.")
            
            if not rows:
                logger.warning(f"[WARNING] No trades found for portfolio {portfolio_id}")
                return APIResponse(success=True, data=[])
            
            # Log the first row to see the structure
            logger.debug(f"[DEBUG] First row data: {dict(rows[0])}")
            
            trades = []
            for row in rows:
                try:
                    trade = {
                        "id": str(row['id']),
                        "symbol": row['symbol'],
                        "side": row['transaction_type'].upper() if row['transaction_type'] else 'UNKNOWN',
                        "quantity": float(row['quantity']) if row['quantity'] is not None else 0.0,
                        "price": float(row['price_per_unit']) if row['price_per_unit'] is not None else 0.0,
                        "total": float(row['total_amount']) if row['total_amount'] is not None else 0.0,
                        "status": row['status'].upper() if row['status'] else 'UNKNOWN',
                        "createdAt": row['created_at'].isoformat() if row['created_at'] else None,
                        "filledAt": row['filled_at'].isoformat() if row['filled_at'] else None
                    }
                    logger.debug(f"[DEBUG] Processed trade: {trade}")
                    trades.append(trade)
                except Exception as trade_error:
                    logger.error(f"[ERROR] Error processing trade row {row}: {str(trade_error)}")
                    continue
            
            if not trades:
                logger.error("[ERROR] No trades could be processed successfully")
                return APIResponse(success=False, error="Failed to process trades data")
            
            response = APIResponse(success=True, data=trades)
            logger.debug(f"[DEBUG] Returning {len(trades)} trades in response")
            return response
            
        except Exception as query_error:
            logger.error(f"[ERROR] Error executing trades query: {str(query_error)}", exc_info=True)
            return APIResponse(success=False, error=f"Database error: {str(query_error)}")
        
    except Exception as e:
        import traceback
        error_msg = f"Error in get_portfolio_trades: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}")

@router.post("/{portfolio_id}/trades", response_model=APIResponse)
async def create_portfolio_trade(portfolio_id: str, trade_data: dict):
    """Create a new trade for a portfolio"""
    # Mock trade creation
    new_trade = {
        "id": f"trade-{4}",  # Fixed reference
        "symbol": trade_data.get("symbol", "UNKNOWN"),
        "side": trade_data.get("side", "BUY"),
        "quantity": trade_data.get("quantity", 0),
        "price": trade_data.get("price", 0.0),
        "total": trade_data.get("quantity", 0) * trade_data.get("price", 0.0),
        "status": "PENDING",
        "createdAt": "2024-01-15T12:00:00Z",
        "filledAt": None
    }
    return APIResponse(success=True, data=new_trade, message="Trade created successfully")

@router.get("/{portfolio_id}/performance", response_model=APIResponse)
async def get_portfolio_performance(
    portfolio_id: str,
    timeframe: str = "1D",
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get portfolio performance data for charts

    **Parameters:**
    - **portfolio_id**: Portfolio UUID
    - **timeframe**: One of: 1D, 1W, 1M, 3M, 1Y, YTD, OPEN, ALL (default: 1D)

    **Returns:**
    Chart data and performance metrics including returns, high/low, etc.
    """
    try:
        user_id = current_user["id"] if current_user else None
        portfolio_uuid = uuid.UUID(portfolio_id)

        # Validate timeframe
        valid_timeframes = ["1D", "1W", "1M", "3M", "1Y", "YTD", "OPEN", "ALL"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )

        # Get performance data
        performance_data = await PortfolioPerformanceService.get_performance_data(
            db=db,
            portfolio_id=portfolio_uuid,
            user_id=uuid.UUID(user_id),
            timeframe=timeframe
        )

        return APIResponse(success=True, data=performance_data)

    except ValueError as e:
        logger.error(f"Invalid portfolio ID or user ID: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio performance: {str(e)}")

@router.post("/{portfolio_id}/performance/snapshot", response_model=APIResponse)
async def create_performance_snapshot(
    portfolio_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger creation of today's performance snapshot

    **Parameters:**
    - **portfolio_id**: Portfolio UUID

    **Returns:**
    Snapshot data for today
    """
    try:
        user_id = current_user["id"]
        portfolio_uuid = uuid.UUID(portfolio_id)

        # Create today's snapshot
        snapshot = await PortfolioPerformanceService.calculate_daily_snapshot(
            db=db,
            portfolio_id=portfolio_uuid,
            user_id=uuid.UUID(user_id)
        )

        return APIResponse(
            success=True,
            data=snapshot,
            message="Performance snapshot created successfully"
        )

    except ValueError as e:
        logger.error(f"Invalid portfolio ID or user ID: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create performance snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create performance snapshot: {str(e)}")

@router.get("/status", response_model=List[PortfolioItem])
async def status():
    return [
        {"symbol": "AAPL", "quantity": 10, "value": 1950.0},
        {"symbol": "TSLA", "quantity": 5, "value": 1100.0},
        {"symbol": "GOOGL", "quantity": 8, "value": 1500.0}
    ]
