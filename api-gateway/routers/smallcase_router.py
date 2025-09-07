"""
Smallcase router for managing curated investment themes and paper trading
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from uuid import UUID
import uuid

from config.database import get_db
from models import APIResponse

router = APIRouter(tags=["smallcases"])


def get_current_user_id() -> str:
    """Get current user ID - returns demo user for now"""
    return "12345678-1234-1234-1234-123456789012"


def validate_uuid(uuid_string: str) -> str:
    """Validate UUID string and return demo portfolio ID if invalid"""
    try:
        uuid.UUID(uuid_string)
        return uuid_string
    except ValueError:
        # Return demo portfolio ID for placeholder values
        return "87654321-4321-4321-4321-210987654321"


@router.get("", response_model=APIResponse)
async def get_user_smallcases(db: AsyncSession = Depends(get_db)):
    """Get smallcases for the current user"""
    try:
        user_id = get_current_user_id()

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
            WHERE s.is_active = true AND s.created_by = :user_id
            GROUP BY s.id, s.name, s.description, s.category, s.theme, s.risk_level,
                     s.expected_return_min, s.expected_return_max, s.minimum_investment, s.is_active
            ORDER BY s.created_at DESC
        """), {"user_id": user_id})

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


@router.get("/user/investments", response_model=APIResponse)
async def get_user_smallcase_investments(db: AsyncSession = Depends(get_db)):
    """Get user's smallcase investments"""
    try:
        user_id = get_current_user_id()
        
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch user investments: {str(e)}")


@router.post("/{smallcase_id}/invest", response_model=APIResponse)
async def invest_in_smallcase(smallcase_id: str, investment_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Invest in a smallcase (paper trading)"""
    try:
        user_id = get_current_user_id()
        portfolio_id = validate_uuid(investment_data.get("portfolio_id", "portfolio-id"))
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
            "current_value": investment_amount,
            "unrealized_pnl": 0.0
        })
        
        await db.commit()
        
        return APIResponse(
            success=True, 
            data={
                "investmentId": investment_id,
                "smallcaseName": smallcase_row.name,
                "investmentAmount": investment_amount,
                "unitsPurchased": units_purchased,
                "purchasePrice": nav,
                "message": f"Successfully invested ${investment_amount:,.2f} in {smallcase_row.name}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process investment: {str(e)}")


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
