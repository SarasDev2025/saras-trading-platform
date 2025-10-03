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
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Import enhanced auth dependencies
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user

from config.database import get_db
from routers.auth_router import get_current_user  # Import real auth
from models import APIResponse
from services.order_aggregation_service import OrderAggregationService
from services.dividend_service import DividendService
from services.broker_selection_service import BrokerSelectionService

router = APIRouter(tags=["smallcases"])
logger = logging.getLogger(__name__)

# Constants for financial calculations
DEFAULT_NAV = Decimal("100.00")
DEFAULT_STOCK_PRICE = Decimal("100.00")
PERCENTAGE_DIVISOR = Decimal("100")

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
                p.name as portfolio_name,
                ubc.id as broker_connection_id,
                ubc.broker_type,
                ubc.alias as broker_alias,
                ubc.status as broker_status
            FROM user_smallcase_investments usi
            JOIN smallcases s ON usi.smallcase_id = s.id
            JOIN portfolios p ON usi.portfolio_id = p.id
            LEFT JOIN user_broker_connections ubc ON usi.broker_connection_id = ubc.id
            WHERE usi.user_id = :user_id AND usi.status = 'active'
            ORDER BY usi.invested_at DESC
        """), {"user_id": user_id})
        
        investments = []
        rows = result.fetchall()
        
        print(f"🔍 DEBUG: Found {len(rows)} investments for user {user_id}")

        for i, row in enumerate(rows):
            print(f"🔍 DEBUG: Investment {i+1}: {row.id} - Status: {row.status}")

        for row in rows:
            # Build broker connection info if available
            broker_connection = None
            if row.broker_connection_id:
                broker_connection = {
                    "id": str(row.broker_connection_id),
                    "broker_type": row.broker_type,
                    "alias": row.broker_alias,
                    "status": row.broker_status
                }

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
                },
                "broker_connection": broker_connection
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
    # Print this immediately at function start
    print(f"🚀🚀🚀 INVEST ENDPOINT CALLED for smallcase {smallcase_id} with data {investment_data}")
    logger.info(f"🚀🚀🚀 INVEST ENDPOINT CALLED for smallcase {smallcase_id} with data {investment_data}")
    try:
        user_id = str(current_user["id"])  # Access user ID from dictionary
        logger.info(f"👤👤👤 User ID: {user_id}")
        print(f"👤👤👤 User ID: {user_id}")
        
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

        # Use Decimal for all financial calculations
        try:
            investment_amount = Decimal(str(investment_data.get("amount", 0)))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid investment amount")

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
        
        minimum_investment = Decimal(str(smallcase_row.minimum_investment))
        if investment_amount < minimum_investment:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum investment is ${minimum_investment}"
            )
        
        # Calculate NAV (simplified - using average of constituent prices)
        nav_result = await db.execute(text("""
            SELECT AVG(a.current_price * sc.weight_percentage / 100) as nav
            FROM smallcase_constituents sc
            JOIN assets a ON sc.asset_id = a.id
            WHERE sc.smallcase_id = :smallcase_id AND sc.is_active = true
        """), {"smallcase_id": smallcase_id})
        
        nav_row = nav_result.fetchone()
        nav = Decimal(str(nav_row.nav)) if nav_row.nav else DEFAULT_NAV

        units_purchased = investment_amount / nav

        # Create investment record with broker connection
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
            "investment_amount": float(investment_amount),
            "units_purchased": float(units_purchased),
            "purchase_price": float(nav),
            "current_value": float(investment_amount),  # Initial value = investment amount
            "unrealized_pnl": 0.0  # Initial P&L = 0
        })

        # Create portfolio holdings based on smallcase constituents
        print(f"🔄 Creating portfolio holdings for investment {investment_id}")

        # Get smallcase constituents
        constituents_result = await db.execute(text("""
            SELECT sc.asset_id, sc.weight_percentage, a.symbol, a.current_price
            FROM smallcase_constituents sc
            JOIN assets a ON sc.asset_id = a.id
            WHERE sc.smallcase_id = :smallcase_id AND sc.is_active = true
        """), {"smallcase_id": smallcase_id})

        constituents = constituents_result.fetchall()
        print(f"📊 Found {len(constituents)} constituents for smallcase")

        # Enhanced: Add broker selection BEFORE creating holdings
        try:
            print(f"🚀 Starting broker selection for user {user_id} with investment ${investment_amount}")

            # Get constituent symbols for broker selection
            constituent_symbols = [row.symbol for row in constituents]
            print(f"📊 Constituent symbols: {constituent_symbols}")

            # Select optimal broker for this user and investment
            broker_selection = await BrokerSelectionService.select_optimal_broker(
                db, user_id, constituent_symbols, float(investment_amount)
            )

            print(f"🏦 Selected broker: {broker_selection['selected_broker']} ({broker_selection['selection_reason']})")

            # Ensure broker connection exists
            broker_connection = await BrokerSelectionService.ensure_broker_connection(
                db, user_id, broker_selection['selected_broker']
            )

            print(f"🔗 Broker connection: {broker_connection['status']} ({broker_connection['connection_id']})")

        except Exception as broker_error:
            print(f"💥 BROKER SELECTION ERROR: {broker_error}")
            logger.error(f"Broker selection failed: {broker_error}")
            # Fall back to no broker connection for now
            broker_connection = {"connection_id": None}
            broker_selection = {"selected_broker": None}

        # Update the investment record with broker connection ID
        if broker_connection.get('connection_id'):
            await db.execute(text("""
                UPDATE user_smallcase_investments
                SET broker_connection_id = :broker_connection_id
                WHERE id = :investment_id
            """), {
                "broker_connection_id": broker_connection['connection_id'],
                "investment_id": investment_id
            })
            print(f"✅ Updated investment with broker connection: {broker_connection['connection_id']}")

        # Create holdings for each constituent
        holdings_created = 0
        for constituent in constituents:
            try:
                # Convert weight percentage to Decimal
                weight_value = constituent.weight_percentage or 0
                weight_decimal = Decimal(str(weight_value))

                # Calculate constituent value using proper Decimal arithmetic
                constituent_value_decimal = (investment_amount * weight_decimal) / PERCENTAGE_DIVISOR

                # Handle stock price with proper default
                price_value = constituent.current_price if constituent.current_price is not None else DEFAULT_STOCK_PRICE
                price_decimal = Decimal(str(price_value))

                # Ensure price is positive
                if price_decimal <= 0:
                    price_decimal = DEFAULT_STOCK_PRICE

                # Calculate quantity
                quantity_decimal = constituent_value_decimal / price_decimal

                # Convert to float for database insert (with proper rounding)
                constituent_value = float(constituent_value_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                current_price = float(price_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                quantity = float(quantity_decimal.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))

            except (ValueError, TypeError, AttributeError) as calc_error:
                print(f"  ❌ Calculation error for {constituent.symbol}: {calc_error}")
                continue

            # Create portfolio holding (simple insert, no conflict handling for now)
            holding_id = str(uuid.uuid4())
            try:
                await db.execute(text("""
                    INSERT INTO portfolio_holdings
                    (id, portfolio_id, asset_id, quantity, average_cost, total_cost,
                     current_value, unrealized_pnl, realized_pnl, created_at, last_updated)
                    VALUES (:id, :portfolio_id, :asset_id, :quantity, :average_cost, :total_cost,
                            :current_value, :unrealized_pnl, :realized_pnl, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (portfolio_id, asset_id) DO UPDATE SET
                        quantity = portfolio_holdings.quantity + EXCLUDED.quantity,
                        total_cost = portfolio_holdings.total_cost + EXCLUDED.total_cost,
                        current_value = portfolio_holdings.current_value + EXCLUDED.current_value,
                        last_updated = CURRENT_TIMESTAMP
                """), {
                    "id": holding_id,
                    "portfolio_id": portfolio_id,
                    "asset_id": str(constituent.asset_id),
                    "quantity": quantity,
                    "average_cost": current_price,
                    "total_cost": constituent_value,
                    "current_value": constituent_value,
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0
                })
                holdings_created += 1
                print(f"  📈 Created holding: {constituent.symbol} - {quantity:.4f} shares @ ${current_price:.2f} = ${constituent_value:.2f}")
            except Exception as holding_error:
                print(f"  ❌ Failed to create holding for {constituent.symbol}: {holding_error}")
                logger.error(f"Failed to create holding for {constituent.symbol}: {holding_error}")
                # Continue with other holdings

        print(f"✅ Created {holdings_created} portfolio holdings")

        # Create position snapshot for dividend tracking
        try:
            from datetime import date
            snapshot_date = date.today()

            # Create position snapshots for dividend eligibility tracking
            for constituent in constituents:
                snapshot_id = str(uuid.uuid4())

                # Get broker info for user (simplified - defaulting to appropriate broker based on future location logic)
                broker_name = "zerodha"  # Will be enhanced with location-based logic

                await db.execute(text("""
                    INSERT INTO user_position_snapshots
                    (id, user_id, asset_id, portfolio_id, snapshot_date, quantity,
                     average_cost, market_value, broker_name, dividend_declaration_id, is_eligible)
                    VALUES (:id, :user_id, :asset_id, :portfolio_id, :snapshot_date,
                            :quantity, :average_cost, :market_value, :broker_name, NULL, true)
                    ON CONFLICT (user_id, asset_id, snapshot_date, dividend_declaration_id) DO NOTHING
                """), {
                    "id": snapshot_id,
                    "user_id": user_id,
                    "asset_id": str(constituent.asset_id),
                    "portfolio_id": portfolio_id,
                    "snapshot_date": snapshot_date,
                    "quantity": float(quantity_decimal.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)),
                    "average_cost": float(price_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                    "market_value": float(constituent_value_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                    "broker_name": broker_name
                })

            print(f"📸 Created position snapshots for dividend tracking")

        except Exception as snapshot_error:
            print(f"⚠️  Warning: Failed to create position snapshots: {snapshot_error}")
            logger.warning(f"Failed to create position snapshots: {snapshot_error}")
            # Don't fail the investment if snapshot creation fails

        # Update position snapshots with the selected broker (if broker selection succeeded)
        if broker_connection.get('connection_id') and broker_selection.get('selected_broker'):
            try:
                await db.execute(text("""
                    UPDATE user_position_snapshots
                    SET broker_name = :broker_name
                    WHERE user_id = :user_id
                    AND snapshot_date = :snapshot_date
                    AND broker_name = 'zerodha'  -- Update the placeholder we set earlier
                """), {
                    "broker_name": broker_selection['selected_broker'],
                    "user_id": user_id,
                    "snapshot_date": snapshot_date
                })
                print(f"📊 Updated position snapshots with broker: {broker_selection['selected_broker']}")
            except Exception as snapshot_update_error:
                print(f"⚠️  Warning: Failed to update position snapshots with broker: {snapshot_update_error}")
                logger.warning(f"Failed to update position snapshots with broker: {snapshot_update_error}")

        await db.commit()
        
        return APIResponse(
            success=True,
            data={
                "investmentId": investment_id,
                "amount": float(investment_amount),
                "units": float(units_purchased),
                "nav": float(nav),
                "holdingsCreated": holdings_created
            },
            message=f"Successfully invested ${investment_amount} in {smallcase_row.name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ ERROR creating investment: {e}")
        logger.error(f"Investment creation failed for user {user_id}, smallcase {smallcase_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create investment: {str(e)}")

# Keep other endpoints the same but add real auth where needed
@router.get("", response_model=APIResponse)
async def get_user_smallcases(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    region: str = None,
    broker_type: str = None
):
    """Get all available smallcases with user investment status, optionally filtered by region/broker"""
    try:
        user_id = str(current_user["id"])

        # Build dynamic WHERE clause for regional filtering
        where_conditions = ["s.is_active = true"]
        params = {"user_id": user_id}

        if region:
            where_conditions.append("s.region = :region")
            params["region"] = region

        if broker_type:
            where_conditions.append(":broker_type = ANY(s.supported_brokers)")
            params["broker_type"] = broker_type

        where_clause = " AND ".join(where_conditions)

        result = await db.execute(text(f"""
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
                s.region,
                s.currency,
                s.supported_brokers,
                COUNT(DISTINCT sc.id) as constituent_count,
                COALESCE(AVG(a.current_price * sc.weight_percentage / 100), 0) as estimated_nav,
                CASE WHEN usi.id IS NOT NULL THEN true ELSE false END as is_invested,
                usi.investment_amount,
                usi.current_value,
                usi.unrealized_pnl
            FROM smallcases s
            LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
            LEFT JOIN assets a ON sc.asset_id = a.id
            LEFT JOIN user_smallcase_investments usi ON s.id = usi.smallcase_id
                AND usi.user_id = :user_id AND usi.status = 'active'
            WHERE {where_clause}
            GROUP BY s.id, s.name, s.description, s.category, s.theme, s.risk_level,
                     s.expected_return_min, s.expected_return_max, s.minimum_investment, s.is_active,
                     s.region, s.currency, s.supported_brokers,
                     usi.id, usi.investment_amount, usi.current_value, usi.unrealized_pnl
            ORDER BY s.created_at DESC
        """), params)

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
                "isActive": row.is_active,
                "isInvested": row.is_invested,
                "investmentAmount": float(row.investment_amount) if row.investment_amount else None,
                "currentValue": float(row.current_value) if row.current_value else None,
                "unrealizedPnl": float(row.unrealized_pnl) if row.unrealized_pnl else None,
                "region": row.region,
                "currency": row.currency,
                "supportedBrokers": row.supported_brokers or [],
                "regionName": "United States" if row.region == "US" else "India" if row.region == "IN" else row.region,
                "isCompatible": not broker_type or broker_type in (row.supported_brokers or [])
            })

        return APIResponse(success=True, data=smallcases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch smallcases: {str(e)}")


@router.get("/regional", response_model=APIResponse)
async def get_regional_smallcases(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get smallcases grouped by region with broker compatibility info"""
    try:
        user_id = str(current_user["id"])

        result = await db.execute(text("""
            SELECT
                s.region,
                s.currency,
                unnest(s.supported_brokers) as broker_type,
                COUNT(DISTINCT s.id) as smallcase_count,
                AVG(s.minimum_investment) as avg_min_investment,
                array_agg(DISTINCT s.category) as categories
            FROM smallcases s
            WHERE s.is_active = true
            GROUP BY s.region, s.currency, unnest(s.supported_brokers)
            ORDER BY s.region, broker_type
        """))

        regional_summary = {}
        for row in result.fetchall():
            region = row.region
            if region not in regional_summary:
                regional_summary[region] = {
                    "region": region,
                    "currency": row.currency,
                    "region_name": "United States" if region == "US" else "India" if region == "IN" else region,
                    "brokers": [],
                    "total_smallcases": 0,
                    "categories": set()
                }

            regional_summary[region]["brokers"].append({
                "broker_type": row.broker_type,
                "smallcase_count": row.smallcase_count,
                "avg_min_investment": float(row.avg_min_investment)
            })
            regional_summary[region]["total_smallcases"] += row.smallcase_count
            regional_summary[region]["categories"].update(row.categories or [])

        # Convert sets to lists for JSON serialization
        for region_data in regional_summary.values():
            region_data["categories"] = list(region_data["categories"])

        return APIResponse(success=True, data={
            "regional_summary": list(regional_summary.values()),
            "available_regions": list(regional_summary.keys()),
            "supported_brokers": ["alpaca", "zerodha"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch regional smallcases: {str(e)}")


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


# ==========================================
# SMALLCASE CLOSURE ENDPOINTS
# ==========================================

@router.get("/investments/{investment_id}/closure-preview", response_model=APIResponse)
async def preview_smallcase_closure(
    investment_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    closure_percentage: float = 100.0
):
    """Preview the closure of a smallcase investment"""
    try:
        from services.smallcase_closure_service import SmallcaseClosureService

        if closure_percentage <= 0 or closure_percentage > 100:
            raise HTTPException(
                status_code=400,
                detail="Closure percentage must be between 0 and 100"
            )

        user_id = str(current_user["id"])
        preview = await SmallcaseClosureService.preview_closure(
            db, user_id, investment_id, closure_percentage
        )

        return APIResponse(success=True, data=preview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview closure: {str(e)}"
        )


@router.post("/investments/{investment_id}/close", response_model=APIResponse)
async def close_smallcase_position(
    investment_id: str,
    closure_data: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Close a smallcase position (full or partial)

    Request body format:
    {
        "closure_reason": "manual_close|rebalance|stop_loss|target_reached|risk_management",
        "closure_percentage": 100.0  // optional, defaults to 100.0
    }
    """
    try:
        from services.smallcase_closure_service import SmallcaseClosureService

        # Extract parameters from request body
        closure_reason = closure_data.get("closure_reason", "manual_close")
        closure_percentage = float(closure_data.get("closure_percentage", 100.0))

        # Validate closure percentage
        if closure_percentage <= 0 or closure_percentage > 100:
            raise HTTPException(
                status_code=400,
                detail="Closure percentage must be between 0 and 100"
            )

        # Validate closure reason
        valid_reasons = [
            "manual_close", "rebalance", "stop_loss", "target_reached",
            "risk_management", "test_closure_api", "user_exit"
        ]
        if closure_reason not in valid_reasons:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid closure reason. Must be one of: {', '.join(valid_reasons)}"
            )

        user_id = str(current_user["id"])

        logger.info(f"[Closure] User {user_id} closing investment {investment_id} - {closure_percentage}% - {closure_reason}")

        result = await SmallcaseClosureService.close_position(
            db, user_id, investment_id, closure_reason, closure_percentage
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"Position {'fully closed' if closure_percentage >= 100 else 'partially closed'} successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Closure] Failed to close position {investment_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close position: {str(e)}"
        )


@router.get("/user/positions/history", response_model=APIResponse)
async def get_user_position_history(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):

    """Get user's closed smallcase position history"""
    try:
        user_id = str(current_user["id"])

        result = await db.execute(text("""
            SELECT
                h.id,
                h.smallcase_id,
                s.name as smallcase_name,
                s.category,
                h.investment_amount,
                h.exit_value,
                h.realized_pnl,
                h.roi_percentage,
                h.holding_period_days,
                h.invested_at,
                h.closed_at,
                h.closure_reason,
                h.execution_mode
            FROM user_smallcase_position_history h
            JOIN smallcases s ON h.smallcase_id = s.id
            WHERE h.user_id = :user_id
            ORDER BY h.closed_at DESC
            LIMIT :limit OFFSET :offset
        """), {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })

        positions = []
        for row in result.fetchall():
            positions.append({
                "id": str(row.id),
                "smallcaseId": str(row.smallcase_id),
                "smallcaseName": row.smallcase_name,
                "category": row.category,
                "investmentAmount": float(row.investment_amount),
                "exitValue": float(row.exit_value),
                "realizedPnl": float(row.realized_pnl),
                "roiPercentage": float(row.roi_percentage),
                "holdingPeriodDays": row.holding_period_days,
                "investedAt": row.invested_at.isoformat(),
                "closedAt": row.closed_at.isoformat(),
                "closureReason": row.closure_reason,
                "executionMode": row.execution_mode
            })

        return APIResponse(success=True, data=positions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch position history: {str(e)}"
        )


@router.get("/user/positions/closed", response_model=APIResponse)
async def get_user_closed_investments(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get user's closed smallcase investments (different from history - shows current closed status)"""
    try:
        user_id = str(current_user["id"])

        result = await db.execute(text("""
            SELECT
                usi.id,
                usi.smallcase_id,
                s.name as smallcase_name,
                s.category,
                usi.investment_amount,
                usi.current_value,
                usi.unrealized_pnl,
                usi.exit_value,
                usi.realized_pnl,
                usi.closure_reason,
                usi.status,
                usi.invested_at,
                usi.closed_at,
                usi.execution_mode
            FROM user_smallcase_investments usi
            JOIN smallcases s ON usi.smallcase_id = s.id
            WHERE usi.user_id = :user_id
            AND usi.status IN ('sold', 'partial')
            ORDER BY usi.closed_at DESC
        """), {"user_id": user_id})

        investments = []
        for row in result.fetchall():
            investments.append({
                "id": str(row.id),
                "smallcaseId": str(row.smallcase_id),
                "smallcaseName": row.smallcase_name,
                "category": row.category,
                "investmentAmount": float(row.investment_amount),
                "currentValue": float(row.current_value) if row.current_value else 0,
                "unrealizedPnl": float(row.unrealized_pnl) if row.unrealized_pnl else 0,
                "exitValue": float(row.exit_value) if row.exit_value else 0,
                "realizedPnl": float(row.realized_pnl) if row.realized_pnl else 0,
                "closureReason": row.closure_reason,
                "status": row.status,
                "investedAt": row.invested_at.isoformat(),
                "closedAt": row.closed_at.isoformat() if row.closed_at else None,
                "executionMode": row.execution_mode
            })

        return APIResponse(success=True, data=investments)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch closed investments: {str(e)}"
        )


@router.post("/bulk/rebalance", response_model=APIResponse)
async def execute_bulk_rebalance(
    rebalance_requests: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db)
):
    """
    Execute rebalancing for multiple users using order aggregation

    This endpoint allows efficient bulk execution of rebalances by aggregating
    individual user orders into consolidated broker orders.

    Request format:
    [
        {
            "user_id": "uuid",
            "smallcase_id": "uuid",
            "suggestions": [
                {
                    "stock_id": "uuid",
                    "symbol": "AAPL",
                    "action": "buy/sell",
                    "current_weight": 10.0,
                    "suggested_weight": 15.0,
                    "weight_change": 5.0
                }
            ],
            "rebalance_summary": {...}
        }
    ]
    """
    try:
        from services.smallcase_execution_service import SmallcaseExecutionService

        if not rebalance_requests:
            raise HTTPException(
                status_code=400,
                detail="At least one rebalance request is required"
            )

        # Validate request structure
        for i, request in enumerate(rebalance_requests):
            required_fields = ['user_id', 'smallcase_id', 'suggestions']
            for field in required_fields:
                if field not in request:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required field '{field}' in request {i}"
                    )

        logger.info(f"[BulkRebalance] Processing {len(rebalance_requests)} rebalance requests")

        # Execute aggregated rebalancing
        result = await SmallcaseExecutionService.execute_multiple_rebalances_aggregated(
            db, rebalance_requests
        )

        logger.info(f"[BulkRebalance] Completed aggregated execution")

        return APIResponse(
            success=True,
            data=result,
            message=f"Successfully executed aggregated rebalance for {result.get('total_users', 0)} users"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BulkRebalance] Failed to execute bulk rebalance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute bulk rebalance: {str(e)}"
        )


@router.post("/bulk/close", response_model=APIResponse)
async def execute_bulk_closure(
    closure_requests: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db)
):
    """
    Execute closure for multiple investments using order aggregation

    This endpoint allows efficient bulk execution of closures by aggregating
    individual sell orders into consolidated broker orders.

    Request format:
    [
        {
            "user_id": "uuid",
            "investment_id": "uuid",
            "closure_reason": "user_exit"
        }
    ]
    """
    try:
        from services.smallcase_closure_service import SmallcaseClosureService

        if not closure_requests:
            raise HTTPException(
                status_code=400,
                detail="At least one closure request is required"
            )

        # Validate request structure
        for i, request in enumerate(closure_requests):
            required_fields = ['user_id', 'investment_id']
            for field in required_fields:
                if field not in request:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required field '{field}' in request {i}"
                    )

        logger.info(f"[BulkClosure] Processing {len(closure_requests)} closure requests")

        # Execute aggregated closures
        result = await SmallcaseClosureService.execute_bulk_closures_aggregated(
            db, closure_requests
        )

        logger.info(f"[BulkClosure] Completed aggregated closure")

        return APIResponse(
            success=True,
            data=result,
            message=f"Successfully executed aggregated closure for {result.get('total_investments', 0)} investments"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BulkClosure] Failed to execute bulk closure: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute bulk closure: {str(e)}"
        )
