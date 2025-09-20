"""
Smallcase router for managing curated investment themes and paper trading
"""

# Fix for routers/smallcase_router.py
# Replace the dummy authentication with real authentication

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Annotated
from uuid import UUID
import uuid
from datetime import datetime

# Import enhanced auth dependencies
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

from config.database import get_db
from routers.auth_router import get_current_user  # Import real auth
from models import APIResponse

router = APIRouter(tags=["smallcases"])

# Remove the dummy function and import real auth
# def get_current_user_id() -> str:
#     """Get current user ID - returns demo user for now"""
#     return "12345678-1234-1234-1234-123456789012"

def validate_uuid(uuid_string: str) -> str:
    """Validate UUID string and return demo portfolio ID if invalid"""
    try:
        uuid.UUID(uuid_string)
        return uuid_string
    except ValueError:
        # Return demo portfolio ID for placeholder values
        return "87654321-4321-4321-4321-210987654321"

@router.get("/user/investments", response_model=APIResponse)
async def get_user_investments(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
        db: AsyncSession = Depends(get_db)
):
    """Get user's smallcase investments"""
    try:
        user_id = str(current_user["id"])  # Access user ID from dictionary
        
        print(f"🔍 DEBUG: Fetching investments for user {user_id}")
        
        result = await db.execute(text("""
            SELECT 
                usi.id,
                usi.investment_amount,
                usi.units_purchased,
                usi.purchase_price,
                usi.current_value,
                usi.unrealized_pnl,
                usi.status,
                usi.invested_at,
                s.id as smallcase_id,
                s.name as smallcase_name,
                s.category,
                s.theme,
                s.risk_level,
                p.id as portfolio_id,
                p.name as portfolio_name
            FROM user_smallcase_investments usi
            JOIN smallcases s ON usi.smallcase_id = s.id
            JOIN portfolios p ON usi.portfolio_id = p.id
            WHERE usi.user_id = :user_id AND usi.status = 'active'
            ORDER BY usi.invested_at DESC
        """), {"user_id": user_id})
        
        investments = []
        rows = result.fetchall()
        
        print(f"🔍 DEBUG: Found {len(rows)} investments for user {user_id}")
        
        for row in rows:
            investments.append({
                "id": str(row.id),
                "investmentAmount": float(row.investment_amount),
                "unitsPurchased": float(row.units_purchased),
                "purchasePrice": float(row.purchase_price),
                "currentValue": float(row.current_value) if row.current_value else 0,
                "unrealizedPnL": float(row.unrealized_pnl) if row.unrealized_pnl else 0,
                "status": row.status,
                "investedAt": row.invested_at.isoformat(),
                "smallcase": {
                    "id": str(row.smallcase_id),
                    "name": row.smallcase_name,
                    "category": row.category,
                    "theme": row.theme,
                    "riskLevel": row.risk_level
                },
                "portfolio": {
                    "id": str(row.portfolio_id),
                    "name": row.portfolio_name
                }
            })
        
        return APIResponse(success=True, data=investments)
    except Exception as e:
        print(f"❌ ERROR fetching investments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user investments: {str(e)}")

@router.post("/{smallcase_id}/invest", response_model=APIResponse)
async def invest_in_smallcase(
    smallcase_id: str, 
    investment_data: Dict[str, Any], 
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Invest in a smallcase (paper trading)"""
    try:
        user_id = str(current_user["id"])  # Access user ID from dictionary
        
        # Get user's default portfolio
        portfolio_result = await db.execute(text("""
            SELECT id FROM portfolios 
            WHERE user_id = :user_id 
            ORDER BY is_default DESC, created_at ASC 
            LIMIT 1
        """), {"user_id": user_id})
        
        portfolio_row = portfolio_result.fetchone()
        if not portfolio_row:
            raise HTTPException(status_code=400, detail="No portfolio found for user")
        
        portfolio_id = str(portfolio_row.id)
        investment_amount = float(investment_data.get("amount", 0))
        
        if investment_amount <= 0:
            raise HTTPException(status_code=400, detail="Investment amount must be positive")
        
        # Get smallcase details
        smallcase_result = await db.execute(text("""
            SELECT minimum_investment, name FROM smallcases 
            WHERE id = :smallcase_id AND is_active = true
        """), {"smallcase_id": smallcase_id})
        
        smallcase_row = smallcase_result.fetchone()
        if not smallcase_row:
            raise HTTPException(status_code=404, detail="Smallcase not found")
        
        if investment_amount < float(smallcase_row.minimum_investment):
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum investment is ${smallcase_row.minimum_investment}"
            )
        
        # Calculate NAV (simplified - using average of constituent prices)
        nav_result = await db.execute(text("""
            SELECT AVG(a.current_price * sc.weight_percentage / 100) as nav
            FROM smallcase_constituents sc
            JOIN assets a ON sc.asset_id = a.id
            WHERE sc.smallcase_id = :smallcase_id AND sc.is_active = true
        """), {"smallcase_id": smallcase_id})
        
        nav_row = nav_result.fetchone()
        nav = float(nav_row.nav) if nav_row.nav else 100.0  # Default NAV
        
        units_purchased = investment_amount / nav
        
        # Create investment record
        investment_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO user_smallcase_investments 
            (id, user_id, portfolio_id, smallcase_id, investment_amount, units_purchased, 
             purchase_price, current_value, unrealized_pnl, status)
            VALUES (:id, :user_id, :portfolio_id, :smallcase_id, :investment_amount, 
                    :units_purchased, :purchase_price, :current_value, :unrealized_pnl, 'active')
        """), {
            "id": investment_id,
            "user_id": user_id,
            "portfolio_id": portfolio_id,
            "smallcase_id": smallcase_id,
            "investment_amount": investment_amount,
            "units_purchased": units_purchased,
            "purchase_price": nav,
            "current_value": investment_amount,  # Initial value = investment amount
            "unrealized_pnl": 0.0  # Initial P&L = 0
        })
        
        await db.commit()
        
        return APIResponse(
            success=True,
            data={
                "investmentId": investment_id,
                "amount": investment_amount,
                "units": units_purchased,
                "nav": nav
            },
            message=f"Successfully invested ${investment_amount} in {smallcase_row.name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ ERROR creating investment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create investment: {str(e)}")

# Keep other endpoints the same but add real auth where needed
@router.get("", response_model=APIResponse)
async def get_user_smallcases(db: AsyncSession = Depends(get_db)):
    """Get all available smallcases (not just user-created ones)"""
    try:
        result = await db.execute(text("""
            SELECT
                s.id,
                s.name,
                s.description,
                s.category,
                s.theme,
                s.risk_level,
                s.expected_return_min,
                s.expected_return_max,
                s.minimum_investment,
                s.is_active,
                COUNT(sc.id) as constituent_count,
                COALESCE(AVG(a.current_price * sc.weight_percentage / 100), 0) as estimated_nav
            FROM smallcases s
            LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
            LEFT JOIN assets a ON sc.asset_id = a.id
            WHERE s.is_active = true
            GROUP BY s.id, s.name, s.description, s.category, s.theme, s.risk_level,
                     s.expected_return_min, s.expected_return_max, s.minimum_investment, s.is_active
            ORDER BY s.created_at DESC
        """))

        smallcases = []
        rows = result.fetchall()

        for row in rows:
            smallcases.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "theme": row.theme,
                "riskLevel": row.risk_level,
                "expectedReturnMin": float(row.expected_return_min) if row.expected_return_min else None,
                "expectedReturnMax": float(row.expected_return_max) if row.expected_return_max else None,
                "minimumInvestment": float(row.minimum_investment),
                "constituentCount": row.constituent_count,
                "estimatedNAV": float(row.estimated_nav),
                "isActive": row.is_active
            })

        return APIResponse(success=True, data=smallcases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch smallcases: {str(e)}")


@router.get("/{smallcase_id}", response_model=APIResponse)
async def get_smallcase_details(smallcase_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific smallcase"""
    try:
        # Get smallcase basic info
        result = await db.execute(text("""
            SELECT 
                s.id,
                s.name,
                s.description,
                s.category,
                s.theme,
                s.risk_level,
                s.expected_return_min,
                s.expected_return_max,
                s.minimum_investment,
                s.is_active
            FROM smallcases s
            WHERE s.id = :smallcase_id AND s.is_active = true
        """), {"smallcase_id": smallcase_id})
        
        smallcase_row = result.fetchone()
        if not smallcase_row:
            raise HTTPException(status_code=404, detail="Smallcase not found")
        
        # Get constituents
        constituents_result = await db.execute(text("""
            SELECT 
                sc.id,
                sc.weight_percentage,
                a.id as asset_id,
                a.symbol,
                a.name as asset_name,
                a.asset_type,
                a.current_price,
                a.exchange
            FROM smallcase_constituents sc
            JOIN assets a ON sc.asset_id = a.id
            WHERE sc.smallcase_id = :smallcase_id AND sc.is_active = true
            ORDER BY sc.weight_percentage DESC
        """), {"smallcase_id": smallcase_id})
        
        constituents = []
        total_value = 0
        for const_row in constituents_result.fetchall():
            weight = float(const_row.weight_percentage)
            price = float(const_row.current_price) if const_row.current_price else 0
            value = price * weight / 100
            total_value += value
            
            constituents.append({
                "id": str(const_row.id),
                "assetId": str(const_row.asset_id),
                "symbol": const_row.symbol,
                "assetName": const_row.asset_name,
                "assetType": const_row.asset_type,
                "weightPercentage": weight,
                "currentPrice": price,
                "exchange": const_row.exchange,
                "value": value
            })
        
        smallcase_details = {
            "id": str(smallcase_row.id),
            "name": smallcase_row.name,
            "description": smallcase_row.description,
            "category": smallcase_row.category,
            "theme": smallcase_row.theme,
            "riskLevel": smallcase_row.risk_level,
            "expectedReturnMin": float(smallcase_row.expected_return_min) if smallcase_row.expected_return_min else None,
            "expectedReturnMax": float(smallcase_row.expected_return_max) if smallcase_row.expected_return_max else None,
            "minimumInvestment": float(smallcase_row.minimum_investment),
            "estimatedNAV": total_value,
            "constituents": constituents,
            "isActive": smallcase_row.is_active
        }
        
        return APIResponse(success=True, data=smallcase_details)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch smallcase details: {str(e)}")

# Add this to your existing smallcase router

@router.get("/{smallcase_id}/composition", response_model=APIResponse)
async def get_smallcase_composition(
    smallcase_id: str, 
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get smallcase composition with market data for modification/rebalancing"""
    try:
        # Verify smallcase exists
        smallcase_check = await db.execute(text("""
            SELECT s.id, s.name 
            FROM smallcases s 
            WHERE s.id = :smallcase_id AND s.is_active = true
        """), {"smallcase_id": smallcase_id})
        
        smallcase_row = smallcase_check.fetchone()
        if not smallcase_row:
            raise HTTPException(status_code=404, detail="Smallcase not found")
        
        # Get constituents with market data from your schema
        constituents_result = await db.execute(text("""
            SELECT 
                sc.id,
                sc.weight_percentage as target_weight,
                a.id as stock_id,
                a.symbol,
                a.name as stock_name,
                a.current_price,
                a.industry as sector,
                a.pb_ratio,
                a.dividend_yield,
                a.beta,
                -- Calculate mock market cap if not available
                CASE 
                    WHEN a.current_price IS NOT NULL 
                    THEN CAST(a.current_price * 1000000 as BIGINT)
                    ELSE 1000000000 
                END as market_cap
            FROM smallcase_constituents sc
            JOIN assets a ON sc.asset_id = a.id
            WHERE sc.smallcase_id = :smallcase_id 
            AND sc.is_active = true 
            AND a.is_active = true
            ORDER BY sc.weight_percentage DESC
        """), {"smallcase_id": smallcase_id})
        
        stocks = []
        total_target_weight = 0
        total_market_value = 0
        
        # Generate some mock performance data since you don't have performance table yet
        import random
        
        for row in constituents_result.fetchall():
            # Use beta and other indicators to generate realistic mock performance
            beta = float(row.beta) if row.beta else 1.0
            
            # More volatile stocks (higher beta) have higher performance swings
            volatility_factor = beta * 10
            
            mock_performance = {
                "price_change_1d": round(random.uniform(-2 * beta, 2 * beta), 2),
                "price_change_7d": round(random.uniform(-5 * beta, 5 * beta), 2),
                "price_change_30d": round(random.uniform(-15 * beta, 15 * beta), 2),
                "volatility_30d": round(max(5, volatility_factor + random.uniform(-3, 3)), 2)
            }
            
            stock_data = {
                "stock_id": str(row.stock_id),
                "symbol": row.symbol,
                "stock_name": row.stock_name,
                "sector": row.sector or "General",
                "current_price": float(row.current_price) if row.current_price else 100.0,
                "market_cap": int(row.market_cap) if row.market_cap else 1000000000,
                "target_weight": float(row.target_weight),
                "volume_avg_30d": random.randint(100000, 2000000),  # Mock volume
                "pb_ratio": float(row.pb_ratio) if row.pb_ratio else 2.5,
                "dividend_yield": float(row.dividend_yield) if row.dividend_yield else 1.0,
                "beta": float(row.beta) if row.beta else 1.0,
                "performance": mock_performance
            }
            
            stocks.append(stock_data)
            total_target_weight += stock_data["target_weight"]
            total_market_value += stock_data["current_price"] * stock_data["target_weight"] / 100
        
        composition = {
            "smallcase_id": smallcase_id,
            "total_stocks": len(stocks),
            "total_target_weight": total_target_weight,
            "total_market_value": total_market_value,
            "stocks": stocks,
            "last_updated": datetime.utcnow()
        }
        
        return APIResponse(success=True, data=composition)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch smallcase composition: {str(e)}"
        )


# Optional: If you want to create a performance tracking table later
# You can run this SQL to add performance tracking:

"""
CREATE TABLE IF NOT EXISTS stock_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id UUID NOT NULL REFERENCES assets(id),
    price_change_1d DECIMAL(8,2) DEFAULT 0,
    price_change_7d DECIMAL(8,2) DEFAULT 0,
    price_change_30d DECIMAL(8,2) DEFAULT 0,
    volatility_30d DECIMAL(8,2) DEFAULT 15,
    volume_avg_30d BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id)
);

-- Insert some sample performance data
INSERT INTO stock_performance (stock_id, price_change_1d, price_change_7d, price_change_30d, volatility_30d, volume_avg_30d)
SELECT 
    id,
    (RANDOM() * 4 - 2)::DECIMAL(8,2),  -- -2% to +2% daily
    (RANDOM() * 10 - 5)::DECIMAL(8,2), -- -5% to +5% weekly  
    (RANDOM() * 30 - 15)::DECIMAL(8,2), -- -15% to +15% monthly
    (RANDOM() * 20 + 5)::DECIMAL(8,2),  -- 5% to 25% volatility
    (RANDOM() * 1900000 + 100000)::BIGINT -- 100k to 2M volume
FROM assets 
WHERE asset_type = 'stock' AND is_active = true
ON CONFLICT (stock_id) DO NOTHING;
"""

@router.get("/categories/performance", response_model=APIResponse)
async def get_category_performance(db: AsyncSession = Depends(get_db)):
    """Get performance metrics by smallcase category"""
    try:
        result = await db.execute(text("""
            SELECT 
                s.category,
                COUNT(s.id) as smallcase_count,
                AVG(s.expected_return_min) as avg_min_return,
                AVG(s.expected_return_max) as avg_max_return,
                COUNT(usi.id) as total_investments,
                COALESCE(SUM(usi.investment_amount), 0) as total_invested,
                COALESCE(SUM(usi.unrealized_pnl), 0) as total_pnl
            FROM smallcases s
            LEFT JOIN user_smallcase_investments usi ON s.id = usi.smallcase_id AND usi.status = 'active'
            WHERE s.is_active = true
            GROUP BY s.category
            ORDER BY total_invested DESC
        """))
        
        categories = []
        rows = result.fetchall()
        
        for row in rows:
            categories.append({
                "category": row.category,
                "smallcaseCount": row.smallcase_count,
                "avgMinReturn": float(row.avg_min_return) if row.avg_min_return else 0,
                "avgMaxReturn": float(row.avg_max_return) if row.avg_max_return else 0,
                "totalInvestments": row.total_investments,
                "totalInvested": float(row.total_invested),
                "totalPnL": float(row.total_pnl)
            })
        
        return APIResponse(success=True, data=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category performance: {str(e)}")
