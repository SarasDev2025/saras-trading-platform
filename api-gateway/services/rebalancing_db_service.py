# services/rebalancing_db_service.py

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException, status
import random

class RebalancingDBService:
    """Database operations for rebalancing functionality"""
    
    @staticmethod
    async def get_smallcase_composition(
        db: AsyncSession, 
        smallcase_id: str
    ) -> Dict[str, Any]:
        """Get smallcase composition with market data for rebalancing"""
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
            
            # Get constituents with market data
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
            
            for row in constituents_result.fetchall():
                # Use beta and other indicators to generate realistic mock performance
                beta = float(row.beta) if row.beta else 1.0
                
                # More volatile stocks (higher beta) have higher performance swings
                mock_performance = {
                    "price_change_1d": round(random.uniform(-2 * beta, 2 * beta), 2),
                    "price_change_7d": round(random.uniform(-5 * beta, 5 * beta), 2),
                    "price_change_30d": round(random.uniform(-15 * beta, 15 * beta), 2),
                    "volatility_30d": round(max(5, beta * 10 + random.uniform(-3, 3)), 2)
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
            
            return composition
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch smallcase composition: {str(e)}"
            )
    
    @staticmethod
    async def apply_rebalancing_to_database(
        db: AsyncSession,
        smallcase_id: str,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply rebalancing suggestions to database"""
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
            
            # Start transaction
            await db.begin()
            
            # Update weights for each suggestion
            updated_stocks = []
            for suggestion in suggestions:
                await db.execute(text("""
                    UPDATE smallcase_constituents 
                    SET weight_percentage = :new_weight, 
                        updated_at = :updated_at
                    WHERE smallcase_id = :smallcase_id 
                    AND asset_id = :stock_id
                    AND is_active = true
                """), {
                    "new_weight": suggestion["suggested_weight"],
                    "smallcase_id": smallcase_id,
                    "stock_id": suggestion["stock_id"],
                    "updated_at": datetime.utcnow()
                })
                
                updated_stocks.append({
                    "stock_id": suggestion["stock_id"],
                    "symbol": suggestion["symbol"],
                    "old_weight": suggestion["current_weight"],
                    "new_weight": suggestion["suggested_weight"],
                    "change": suggestion["weight_change"]
                })
            
            # Update smallcase timestamp
            await db.execute(text("""
                UPDATE smallcases 
                SET updated_at = :updated_at
                WHERE id = :smallcase_id
            """), {
                "smallcase_id": smallcase_id,
                "updated_at": datetime.utcnow()
            })
            
            await db.commit()
            
            result = {
                "success": True,
                "message": "Smallcase rebalanced successfully",
                "updated_stocks": updated_stocks,
                "total_changes": len(updated_stocks),
                "applied_at": datetime.utcnow(),
                "smallcase_name": smallcase_row.name
            }
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply rebalancing: {str(e)}"
            )
    
    @staticmethod
    async def verify_user_access_to_smallcase(
        db: AsyncSession,
        smallcase_id: str,
        user_id: str
    ) -> bool:
        """Verify if user has access to modify this smallcase (owns investment)"""
        try:
            # Check if user has invested in this smallcase
            result = await db.execute(text("""
                SELECT ui.id 
                FROM user_investments ui
                WHERE ui.smallcase_id = :smallcase_id 
                AND ui.user_id = :user_id
                AND ui.status = 'active'
                LIMIT 1
            """), {
                "smallcase_id": smallcase_id,
                "user_id": user_id
            })
            
            return result.fetchone() is not None
            
        except Exception:
            return False
    
    @staticmethod 
    async def log_rebalancing_activity(
        db: AsyncSession,
        smallcase_id: str,
        user_id: str,
        strategy: str,
        changes_applied: int
    ):
        """Log rebalancing activity for audit trail"""
        try:
            await db.execute(text("""
                INSERT INTO rebalancing_history (
                    smallcase_id, 
                    user_id, 
                    strategy_used,
                    changes_applied,
                    applied_at
                ) VALUES (
                    :smallcase_id,
                    :user_id,
                    :strategy,
                    :changes_applied,
                    :applied_at
                )
            """), {
                "smallcase_id": smallcase_id,
                "user_id": user_id,
                "strategy": strategy,
                "changes_applied": changes_applied,
                "applied_at": datetime.utcnow()
            })
            await db.commit()
        except Exception:
            # Log but don't fail the main operation if audit logging fails
            pass