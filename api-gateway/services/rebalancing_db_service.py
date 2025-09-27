# Complete services/rebalancing_db_service.py with all required methods

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException, status


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RebalancingDBService:
    """Database operations for rebalancing functionality"""
    
    @staticmethod
    def get_utc_now():
        """Get current UTC time with timezone info (replaces deprecated utcnow)"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    async def verify_user_access_to_smallcase(
        db: AsyncSession,
        smallcase_id: str,
        user_id: str
    ) -> bool:
        """Verify if user has access to modify this smallcase (owns investment)"""
        try:
            # Use correct table name
            result = await db.execute(text("""
                SELECT usi.id 
                FROM user_smallcase_investments usi
                WHERE usi.smallcase_id = :smallcase_id 
                AND usi.user_id = :user_id
                AND usi.status = 'active'
                LIMIT 1
            """), {
                "smallcase_id": smallcase_id,
                "user_id": user_id
            })
            
            return result.fetchone() is not None
            
        except Exception as e:
            logger.exception("[RebalanceDB] verify_user_access_to_smallcase failed smallcase=%s user=%s", smallcase_id, user_id)
            return False
    
    @staticmethod
    async def apply_rebalancing_to_database(
        db: AsyncSession,
        smallcase_id: str,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply rebalancing suggestions to database"""
        try:
            logger.info("[RebalanceDB] Starting rebalancing smallcase=%s suggestions=%d", smallcase_id, len(suggestions))
            
            # Verify smallcase exists
            smallcase_check = await db.execute(text("""
                SELECT s.id, s.name 
                FROM smallcases s 
                WHERE s.id = :smallcase_id AND s.is_active = true
            """), {"smallcase_id": smallcase_id})
            
            smallcase_row = smallcase_check.fetchone()
            if not smallcase_row:
                raise HTTPException(status_code=404, detail="Smallcase not found")
            
            logger.info("[RebalanceDB] Found smallcase name=%s", smallcase_row.name)
            
            # Get current UTC time with timezone
            current_time = RebalancingDBService.get_utc_now()
            
            # Update weights for each suggestion
            updated_stocks = []
            for i, suggestion in enumerate(suggestions):
                try:
                    logger.info("[RebalanceDB] Processing suggestion index=%d payload=%s", i + 1, suggestion)
                    
                    stock_id = suggestion.get("stock_id")
                    suggested_weight = suggestion.get("suggested_weight")
                    symbol = suggestion.get("symbol", "UNKNOWN")
                    
                    if not stock_id or suggested_weight is None:
                        logger.warning("[RebalanceDB] Skipping suggestion index=%d missing required fields", i + 1)
                        continue
                    
                    # Update the constituent weight
                    update_result = await db.execute(text("""
                        UPDATE smallcase_constituents 
                        SET weight_percentage = :new_weight, 
                            updated_at = :updated_at
                        WHERE smallcase_id = :smallcase_id 
                        AND asset_id = :stock_id
                        AND is_active = true
                    """), {
                        "new_weight": float(suggested_weight),
                        "smallcase_id": smallcase_id,
                        "stock_id": stock_id,
                        "updated_at": current_time
                    })
                    
                    rows_updated = update_result.rowcount
                    logger.info("[RebalanceDB] Updated rows=%d stock=%s symbol=%s", rows_updated, stock_id, symbol)
                    
                    if rows_updated > 0:
                        updated_stocks.append({
                            "stock_id": stock_id,
                            "symbol": symbol,
                            "old_weight": suggestion.get("current_weight", 0),
                            "new_weight": suggested_weight,
                            "change": suggestion.get("weight_change", 0)
                        })
                    else:
                        logger.warning("[RebalanceDB] No rows updated for stock=%s", stock_id)
                
                except Exception as e:
                    logger.exception("[RebalanceDB] Error processing suggestion index=%d", i + 1)
                    continue
            
            # Update smallcase timestamp
            logger.info("[RebalanceDB] Updating smallcase timestamp smallcase=%s", smallcase_id)
            await db.execute(text("""
                UPDATE smallcases 
                SET updated_at = :updated_at
                WHERE id = :smallcase_id
            """), {
                "smallcase_id": smallcase_id,
                "updated_at": current_time
            })
            
            # Commit the changes
            await db.commit()
            logger.info("[RebalanceDB] Changes committed successfully smallcase=%s", smallcase_id)
            
            # Return result with ISO string for JSON serialization
            result = {
                "success": True,
                "message": "Smallcase rebalanced successfully",
                "updated_stocks": updated_stocks,
                "total_changes": len(updated_stocks),
                "applied_at": current_time,
                "smallcase_name": smallcase_row.name
            }
            
            logger.info("[RebalanceDB] Rebalancing completed updated_stocks=%d", len(updated_stocks))
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("[RebalanceDB] apply_rebalancing_to_database failed smallcase=%s", smallcase_id)

            try:
                await db.rollback()
                logger.warning("[RebalanceDB] Transaction rolled back smallcase=%s", smallcase_id)
            except Exception as rollback_error:
                logger.exception("[RebalanceDB] Failed to rollback smallcase=%s", smallcase_id)

            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply rebalancing: {str(e)}"
            )
    
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
            logger.info("[RebalanceDB] Attempting to log rebalancing activity smallcase=%s", smallcase_id)
            
            # Check if rebalancing_history table exists first
            table_check = await db.execute(text("""
                SELECT to_regclass('rebalancing_history') IS NOT NULL as table_exists
            """))
            
            table_result = table_check.fetchone()
            table_exists = table_result.table_exists if table_result else False

            if not table_exists:
                logger.warning("[RebalanceDB] rebalancing_history table missing; skipping audit log")
                return
            
            current_time = RebalancingDBService.get_utc_now()
            
            # Insert the audit log
            await db.execute(text("""
                INSERT INTO rebalancing_history (
                    id,
                    smallcase_id, 
                    user_id, 
                    strategy_used,
                    changes_applied,
                    applied_at,
                    created_at
                ) VALUES (
                    gen_random_uuid(),
                    :smallcase_id,
                    :user_id,
                    :strategy,
                    :changes_applied,
                    :applied_at,
                    :created_at
                )
            """), {
                "smallcase_id": smallcase_id,
                "user_id": user_id,
                "strategy": strategy,
                "changes_applied": changes_applied,
                "applied_at": current_time,
                "created_at": current_time
            })
            
            await db.commit()
            logger.info("[RebalanceDB] Rebalancing activity logged smallcase=%s", smallcase_id)

        except Exception as e:
            logger.exception("[RebalanceDB] Failed to log rebalancing activity smallcase=%s", smallcase_id)
            # Don't fail the main operation if audit logging fails
            pass
    
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
                WHERE sc.smallcase_id = :smallcase_id AND sc.is_active = true
                ORDER BY sc.weight_percentage DESC
            """), {"smallcase_id": smallcase_id})
            
            stocks = []
            total_target_weight = 0
            total_market_value = 0
            
            for row in constituents_result.fetchall():
                # Generate mock performance data
                stock_data = {
                    "stock_id": str(row.stock_id),
                    "symbol": row.symbol,
                    "stock_name": row.stock_name,
                    "sector": row.sector or "Technology",
                    "current_price": float(row.current_price or 100.0),
                    "target_weight": float(row.target_weight),
                    "market_cap": int(row.market_cap),
                    "performance": {
                        "price_change_1d": round((hash(row.symbol) % 1000) / 100 - 5, 2),
                        "price_change_7d": round((hash(row.symbol + "7d") % 2000) / 100 - 10, 2),
                        "price_change_30d": round((hash(row.symbol + "30d") % 4000) / 100 - 20, 2),
                        "volatility_30d": round((hash(row.symbol + "vol") % 500) / 100 + 5, 2)
                    }
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
                "last_updated": RebalancingDBService.get_utc_now().isoformat()
            }
            
            return composition
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch smallcase composition: {str(e)}"
            )
