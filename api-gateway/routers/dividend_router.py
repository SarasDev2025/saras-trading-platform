"""
Dividend Management Router for Multi-User Bulk Order System
API endpoints for dividend declarations, DRIP management, and bulk order tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Annotated, Optional
from uuid import UUID
import uuid
import logging
from datetime import date, datetime
from decimal import Decimal

# Import enhanced auth dependencies
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

from config.database import get_db
from models import APIResponse
from services.dividend_service import DividendService
from services.broker_selection_service import BrokerSelectionService

router = APIRouter(tags=["dividends"], prefix="/dividends")
logger = logging.getLogger(__name__)


@router.post("/declarations", response_model=APIResponse)
async def create_dividend_declaration(
    declaration_data: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new dividend declaration (admin/system function)"""
    try:
        # For now, allow any authenticated user to create declarations (in production, restrict to admin)
        required_fields = ["asset_id", "ex_dividend_date", "record_date", "payment_date", "dividend_amount"]

        for field in required_fields:
            if field not in declaration_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Parse and validate dates
        try:
            ex_dividend_date = date.fromisoformat(declaration_data["ex_dividend_date"])
            record_date = date.fromisoformat(declaration_data["record_date"])
            payment_date = date.fromisoformat(declaration_data["payment_date"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")

        # Parse dividend amount
        try:
            dividend_amount = Decimal(str(declaration_data["dividend_amount"]))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid dividend amount")

        # Create dividend declaration
        result = await DividendService.create_dividend_declaration(
            db=db,
            asset_id=declaration_data["asset_id"],
            ex_dividend_date=ex_dividend_date,
            record_date=record_date,
            payment_date=payment_date,
            dividend_amount=dividend_amount,
            dividend_type=declaration_data.get("dividend_type", "cash"),
            currency=declaration_data.get("currency", "USD"),
            announcement_date=date.fromisoformat(declaration_data["announcement_date"]) if declaration_data.get("announcement_date") else None
        )

        return APIResponse(
            success=True,
            data=result,
            message="Dividend declaration created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dividend declaration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create dividend declaration: {str(e)}")


@router.post("/declarations/{declaration_id}/process-snapshots", response_model=APIResponse)
async def process_dividend_snapshots(
    declaration_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Process position snapshots for a dividend declaration"""
    try:
        # Get dividend declaration
        declaration_result = await db.execute(text("""
            SELECT record_date FROM dividend_declarations
            WHERE id = :declaration_id
        """), {"declaration_id": declaration_id})

        declaration_row = declaration_result.fetchone()
        if not declaration_row:
            raise HTTPException(status_code=404, detail="Dividend declaration not found")

        record_date = declaration_row[0]

        # Create position snapshots
        snapshots = await DividendService.create_position_snapshots_for_dividend(
            db=db,
            dividend_declaration_id=declaration_id,
            snapshot_date=record_date
        )

        return APIResponse(
            success=True,
            data={
                "declaration_id": declaration_id,
                "snapshots_created": len(snapshots),
                "record_date": record_date.isoformat()
            },
            message=f"Created {len(snapshots)} position snapshots for dividend"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process dividend snapshots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process dividend snapshots: {str(e)}")


@router.post("/declarations/{declaration_id}/calculate-payments", response_model=APIResponse)
async def calculate_dividend_payments(
    declaration_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Calculate dividend payments for all eligible users"""
    try:
        payments = await DividendService.calculate_dividend_payments(
            db=db,
            dividend_declaration_id=declaration_id
        )

        return APIResponse(
            success=True,
            data={
                "declaration_id": declaration_id,
                "payments_calculated": len(payments),
                "total_gross_amount": sum(p["gross_amount"] for p in payments),
                "total_net_amount": sum(p["net_amount"] for p in payments)
            },
            message=f"Calculated {len(payments)} dividend payments"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate dividend payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate dividend payments: {str(e)}")


@router.post("/drip/process/{asset_id}", response_model=APIResponse)
async def process_drip_transactions(
    asset_id: str,
    execution_date: str = Query(..., description="Date to execute DRIP transactions (YYYY-MM-DD)"),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Process DRIP transactions and create bulk orders"""
    try:
        # Parse execution date
        try:
            exec_date = date.fromisoformat(execution_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid execution date format. Use YYYY-MM-DD")

        # Process DRIP transactions
        result = await DividendService.process_drip_transactions(
            db=db,
            asset_id=asset_id,
            execution_date=exec_date
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"Processed DRIP transactions for asset {asset_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process DRIP transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process DRIP transactions: {str(e)}")


@router.get("/user/summary", response_model=APIResponse)
async def get_user_dividend_summary(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dividend summary for the current user"""
    try:
        user_id = str(current_user["id"])

        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Get dividend summary
        summary = await DividendService.get_user_dividend_summary(
            db=db,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )

        return APIResponse(
            success=True,
            data=summary,
            message="User dividend summary retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user dividend summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user dividend summary: {str(e)}")


@router.get("/user/preferences", response_model=APIResponse)
async def get_user_drip_preferences(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get user's DRIP preferences"""
    try:
        user_id = str(current_user["id"])

        # Get user's DRIP preferences
        result = await db.execute(text("""
            SELECT
                udp.id,
                udp.asset_id,
                udp.is_enabled,
                udp.minimum_amount,
                udp.maximum_percentage,
                a.symbol,
                a.name as asset_name
            FROM user_drip_preferences udp
            LEFT JOIN assets a ON udp.asset_id = a.id
            WHERE udp.user_id = :user_id
            ORDER BY a.symbol NULLS FIRST
        """), {"user_id": user_id})

        preferences = []
        for row in result.fetchall():
            preferences.append({
                "id": str(row[0]),
                "asset_id": str(row[1]) if row[1] else None,
                "is_enabled": row[2],
                "minimum_amount": float(row[3]) if row[3] else 0.0,
                "maximum_percentage": float(row[4]) if row[4] else 100.0,
                "asset_symbol": row[5],
                "asset_name": row[6],
                "is_global": row[1] is None
            })

        return APIResponse(
            success=True,
            data={"preferences": preferences},
            message="DRIP preferences retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get DRIP preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get DRIP preferences: {str(e)}")


@router.post("/user/preferences", response_model=APIResponse)
async def update_user_drip_preferences(
    preference_data: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update user's DRIP preferences"""
    try:
        user_id = str(current_user["id"])

        asset_id = preference_data.get("asset_id")  # None for global preference
        is_enabled = preference_data.get("is_enabled", False)
        minimum_amount = Decimal(str(preference_data.get("minimum_amount", 0)))
        maximum_percentage = Decimal(str(preference_data.get("maximum_percentage", 100)))

        # Validate percentage
        if not (0 <= maximum_percentage <= 100):
            raise HTTPException(status_code=400, detail="Maximum percentage must be between 0 and 100")

        # Upsert preference
        await db.execute(text("""
            INSERT INTO user_drip_preferences
            (id, user_id, asset_id, is_enabled, minimum_amount, maximum_percentage)
            VALUES (:id, :user_id, :asset_id, :is_enabled, :minimum_amount, :maximum_percentage)
            ON CONFLICT (user_id, asset_id) DO UPDATE SET
                is_enabled = EXCLUDED.is_enabled,
                minimum_amount = EXCLUDED.minimum_amount,
                maximum_percentage = EXCLUDED.maximum_percentage,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "asset_id": asset_id,
            "is_enabled": is_enabled,
            "minimum_amount": minimum_amount,
            "maximum_percentage": maximum_percentage
        })

        await db.commit()

        return APIResponse(
            success=True,
            data={
                "user_id": user_id,
                "asset_id": asset_id,
                "is_enabled": is_enabled,
                "minimum_amount": float(minimum_amount),
                "maximum_percentage": float(maximum_percentage)
            },
            message="DRIP preference updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update DRIP preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update DRIP preferences: {str(e)}")


@router.get("/bulk-orders", response_model=APIResponse)
async def get_dividend_bulk_orders(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results"),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get dividend bulk orders with optional filtering"""
    try:
        # Build query with filters
        filters = []
        params = {"limit": limit}

        if asset_id:
            filters.append("dbo.asset_id = :asset_id")
            params["asset_id"] = asset_id

        if status:
            filters.append("dbo.status = :status")
            params["status"] = status

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Get bulk orders
        result = await db.execute(text(f"""
            SELECT
                dbo.id,
                dbo.asset_id,
                dbo.execution_date,
                dbo.total_amount,
                dbo.total_shares_to_purchase,
                dbo.target_price,
                dbo.actual_price,
                dbo.broker_name,
                dbo.broker_order_id,
                dbo.status,
                dbo.execution_window_start,
                dbo.execution_window_end,
                dbo.created_at,
                a.symbol,
                a.name as asset_name,
                COUNT(dboa.id) as user_count
            FROM dividend_bulk_orders dbo
            JOIN assets a ON dbo.asset_id = a.id
            LEFT JOIN drip_bulk_order_allocations dboa ON dbo.id = dboa.dividend_bulk_order_id
            {where_clause}
            GROUP BY dbo.id, a.symbol, a.name
            ORDER BY dbo.created_at DESC
            LIMIT :limit
        """), params)

        bulk_orders = []
        for row in result.fetchall():
            bulk_orders.append({
                "id": str(row[0]),
                "asset_id": str(row[1]),
                "execution_date": row[2].isoformat(),
                "total_amount": float(row[3]),
                "total_shares_to_purchase": float(row[4]),
                "target_price": float(row[5]) if row[5] else None,
                "actual_price": float(row[6]) if row[6] else None,
                "broker_name": row[7],
                "broker_order_id": row[8],
                "status": row[9],
                "execution_window_start": row[10].isoformat() if row[10] else None,
                "execution_window_end": row[11].isoformat() if row[11] else None,
                "created_at": row[12].isoformat(),
                "asset_symbol": row[13],
                "asset_name": row[14],
                "user_count": row[15]
            })

        return APIResponse(
            success=True,
            data={
                "bulk_orders": bulk_orders,
                "count": len(bulk_orders)
            },
            message="Dividend bulk orders retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get dividend bulk orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dividend bulk orders: {str(e)}")


@router.get("/declarations", response_model=APIResponse)
async def get_dividend_declarations(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results"),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get dividend declarations with optional filtering"""
    try:
        # Build query with filters
        filters = []
        params = {"limit": limit}

        if asset_id:
            filters.append("dd.asset_id = :asset_id")
            params["asset_id"] = asset_id

        if status:
            filters.append("dd.status = :status")
            params["status"] = status

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Get declarations
        result = await db.execute(text(f"""
            SELECT
                dd.id,
                dd.asset_id,
                dd.ex_dividend_date,
                dd.record_date,
                dd.payment_date,
                dd.dividend_amount,
                dd.dividend_type,
                dd.currency,
                dd.announcement_date,
                dd.status,
                dd.created_at,
                a.symbol,
                a.name as asset_name
            FROM dividend_declarations dd
            JOIN assets a ON dd.asset_id = a.id
            {where_clause}
            ORDER BY dd.ex_dividend_date DESC
            LIMIT :limit
        """), params)

        declarations = []
        for row in result.fetchall():
            declarations.append({
                "id": str(row[0]),
                "asset_id": str(row[1]),
                "ex_dividend_date": row[2].isoformat(),
                "record_date": row[3].isoformat(),
                "payment_date": row[4].isoformat(),
                "dividend_amount": float(row[5]),
                "dividend_type": row[6],
                "currency": row[7],
                "announcement_date": row[8].isoformat() if row[8] else None,
                "status": row[9],
                "created_at": row[10].isoformat(),
                "asset_symbol": row[11],
                "asset_name": row[12]
            })

        return APIResponse(
            success=True,
            data={
                "declarations": declarations,
                "count": len(declarations)
            },
            message="Dividend declarations retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get dividend declarations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dividend declarations: {str(e)}")