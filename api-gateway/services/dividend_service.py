"""
Dividend Management Service for Multi-User Bulk Order System
Handles dividend declarations, position snapshots, DRIP transactions, and bulk order aggregation
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_, or_
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


class DividendService:
    """Core service for dividend management and multi-user bulk order coordination"""

    @staticmethod
    async def create_dividend_declaration(
        db: AsyncSession,
        asset_id: str,
        ex_dividend_date: date,
        record_date: date,
        payment_date: date,
        dividend_amount: Decimal,
        dividend_type: str = "cash",
        currency: str = "USD",
        announcement_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Create a new dividend declaration"""
        try:
            declaration_id = str(uuid.uuid4())

            await db.execute(text("""
                INSERT INTO dividend_declarations
                (id, asset_id, ex_dividend_date, record_date, payment_date,
                 dividend_amount, dividend_type, currency, announcement_date, status)
                VALUES (:id, :asset_id, :ex_dividend_date, :record_date, :payment_date,
                        :dividend_amount, :dividend_type, :currency, :announcement_date, 'announced')
            """), {
                "id": declaration_id,
                "asset_id": asset_id,
                "ex_dividend_date": ex_dividend_date,
                "record_date": record_date,
                "payment_date": payment_date,
                "dividend_amount": dividend_amount,
                "dividend_type": dividend_type,
                "currency": currency,
                "announcement_date": announcement_date
            })

            await db.commit()

            logger.info(f"✅ Created dividend declaration {declaration_id} for asset {asset_id}")
            return {
                "id": declaration_id,
                "asset_id": asset_id,
                "ex_dividend_date": ex_dividend_date,
                "dividend_amount": dividend_amount,
                "status": "announced"
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to create dividend declaration: {str(e)}")
            raise

    @staticmethod
    async def create_position_snapshots_for_dividend(
        db: AsyncSession,
        dividend_declaration_id: str,
        snapshot_date: date
    ) -> List[Dict[str, Any]]:
        """Create position snapshots for all users holding the asset on record date"""
        try:
            # Get dividend declaration details
            dividend_result = await db.execute(text("""
                SELECT asset_id, dividend_amount, ex_dividend_date
                FROM dividend_declarations
                WHERE id = :dividend_id
            """), {"dividend_id": dividend_declaration_id})

            dividend_row = dividend_result.fetchone()
            if not dividend_row:
                raise ValueError(f"Dividend declaration {dividend_declaration_id} not found")

            asset_id = dividend_row[0]

            # Get all users with holdings in this asset
            holdings_result = await db.execute(text("""
                SELECT DISTINCT
                    ph.portfolio_id,
                    p.user_id,
                    ph.asset_id,
                    ph.quantity,
                    ph.average_cost,
                    ph.current_value,
                    ubc.broker_type as broker_name
                FROM portfolio_holdings ph
                JOIN portfolios p ON ph.portfolio_id = p.id
                JOIN user_broker_connections ubc ON p.user_id = ubc.user_id AND ubc.status = 'active'
                WHERE ph.asset_id = :asset_id
                AND ph.quantity > 0
            """), {"asset_id": asset_id})

            snapshots = []

            for holding in holdings_result.fetchall():
                snapshot_id = str(uuid.uuid4())

                # Create position snapshot
                await db.execute(text("""
                    INSERT INTO user_position_snapshots
                    (id, user_id, asset_id, portfolio_id, snapshot_date, quantity,
                     average_cost, market_value, broker_name, dividend_declaration_id, is_eligible)
                    VALUES (:id, :user_id, :asset_id, :portfolio_id, :snapshot_date,
                            :quantity, :average_cost, :market_value, :broker_name, :dividend_id, true)
                """), {
                    "id": snapshot_id,
                    "user_id": holding[1],
                    "asset_id": holding[2],
                    "portfolio_id": holding[0],
                    "snapshot_date": snapshot_date,
                    "quantity": holding[3],
                    "average_cost": holding[4],
                    "market_value": holding[5],
                    "broker_name": holding[6],
                    "dividend_id": dividend_declaration_id
                })

                snapshots.append({
                    "id": snapshot_id,
                    "user_id": holding[1],
                    "asset_id": asset_id,
                    "quantity": holding[3],
                    "broker_name": holding[6]
                })

            await db.commit()
            logger.info(f"✅ Created {len(snapshots)} position snapshots for dividend {dividend_declaration_id}")
            return snapshots

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to create position snapshots: {str(e)}")
            raise

    @staticmethod
    async def calculate_dividend_payments(
        db: AsyncSession,
        dividend_declaration_id: str
    ) -> List[Dict[str, Any]]:
        """Calculate dividend payments for all eligible users"""
        try:
            # Get dividend and position data
            result = await db.execute(text("""
                SELECT
                    dd.id as dividend_id,
                    dd.asset_id,
                    dd.dividend_amount,
                    dd.payment_date,
                    ups.id as snapshot_id,
                    ups.user_id,
                    ups.portfolio_id,
                    ups.quantity,
                    ups.broker_name
                FROM dividend_declarations dd
                JOIN user_position_snapshots ups ON dd.id = ups.dividend_declaration_id
                WHERE dd.id = :dividend_id AND ups.is_eligible = true
            """), {"dividend_id": dividend_declaration_id})

            payments = []

            for row in result.fetchall():
                payment_id = str(uuid.uuid4())
                eligible_shares = row[7]  # quantity
                dividend_per_share = row[2]  # dividend_amount
                gross_amount = eligible_shares * dividend_per_share

                # Simple tax calculation (can be enhanced with country-specific logic)
                tax_rate = Decimal("0.15")  # 15% withholding tax
                tax_withheld = gross_amount * tax_rate
                net_amount = gross_amount - tax_withheld

                # Create dividend payment record
                await db.execute(text("""
                    INSERT INTO user_dividend_payments
                    (id, user_id, asset_id, portfolio_id, dividend_declaration_id,
                     position_snapshot_id, eligible_shares, dividend_per_share,
                     gross_amount, tax_withheld, net_amount, payment_date,
                     broker_name, reinvestment_preference, status)
                    VALUES (:id, :user_id, :asset_id, :portfolio_id, :dividend_id,
                            :snapshot_id, :eligible_shares, :dividend_per_share,
                            :gross_amount, :tax_withheld, :net_amount, :payment_date,
                            :broker_name, 'cash', 'pending')
                """), {
                    "id": payment_id,
                    "user_id": row[5],
                    "asset_id": row[1],
                    "portfolio_id": row[6],
                    "dividend_id": dividend_declaration_id,
                    "snapshot_id": row[4],
                    "eligible_shares": eligible_shares,
                    "dividend_per_share": dividend_per_share,
                    "gross_amount": gross_amount,
                    "tax_withheld": tax_withheld,
                    "net_amount": net_amount,
                    "payment_date": row[3],
                    "broker_name": row[8]
                })

                payments.append({
                    "id": payment_id,
                    "user_id": row[5],
                    "gross_amount": float(gross_amount),
                    "net_amount": float(net_amount),
                    "eligible_shares": float(eligible_shares)
                })

            await db.commit()
            logger.info(f"✅ Calculated {len(payments)} dividend payments for declaration {dividend_declaration_id}")
            return payments

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to calculate dividend payments: {str(e)}")
            raise

    @staticmethod
    async def process_drip_transactions(
        db: AsyncSession,
        asset_id: str,
        execution_date: date
    ) -> Dict[str, Any]:
        """Process DRIP transactions and create bulk orders for aggregated purchases"""
        try:
            # Get all pending dividend payments for users with DRIP enabled
            drip_result = await db.execute(text("""
                SELECT
                    udp.id as payment_id,
                    udp.user_id,
                    udp.asset_id,
                    udp.portfolio_id,
                    udp.net_amount,
                    udp.broker_name,
                    COALESCE(udrip.minimum_amount, 0) as min_amount,
                    COALESCE(udrip.maximum_percentage, 100) as max_percentage
                FROM user_dividend_payments udp
                JOIN user_drip_preferences udrip ON (
                    udp.user_id = udrip.user_id AND
                    (udrip.asset_id = udp.asset_id OR udrip.asset_id IS NULL)
                )
                WHERE udp.asset_id = :asset_id
                AND udp.status = 'received'
                AND udp.reinvestment_preference = 'drip'
                AND udrip.is_enabled = true
                AND udp.net_amount >= COALESCE(udrip.minimum_amount, 0)
                ORDER BY udrip.asset_id NULLS LAST  -- Specific asset preferences override global
            """), {"asset_id": asset_id})

            drip_transactions = []
            total_reinvestment_amount = Decimal("0")
            broker_groups = {}

            # Get current asset price (simplified - in reality would fetch from market data)
            current_price = Decimal("100.00")  # Placeholder

            for row in drip_result.fetchall():
                reinvestment_amount = row[4] * (row[7] / Decimal("100"))  # Apply percentage limit

                if reinvestment_amount >= row[6]:  # Check minimum amount
                    shares_to_purchase = (reinvestment_amount / current_price).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )

                    drip_id = str(uuid.uuid4())

                    # Create DRIP transaction
                    await db.execute(text("""
                        INSERT INTO drip_transactions
                        (id, user_dividend_payment_id, user_id, asset_id, portfolio_id,
                         reinvestment_amount, shares_purchased, purchase_price,
                         transaction_date, broker_name, status)
                        VALUES (:id, :payment_id, :user_id, :asset_id, :portfolio_id,
                                :amount, :shares, :price, :date, :broker, 'pending')
                    """), {
                        "id": drip_id,
                        "payment_id": row[0],
                        "user_id": row[1],
                        "asset_id": row[2],
                        "portfolio_id": row[3],
                        "amount": reinvestment_amount,
                        "shares": shares_to_purchase,
                        "price": current_price,
                        "date": execution_date,
                        "broker": row[5]
                    })

                    drip_transactions.append({
                        "id": drip_id,
                        "user_id": row[1],
                        "amount": reinvestment_amount,
                        "shares": shares_to_purchase,
                        "broker": row[5]
                    })

                    # Group by broker for bulk orders
                    broker_name = row[5]
                    if broker_name not in broker_groups:
                        broker_groups[broker_name] = {
                            "total_amount": Decimal("0"),
                            "total_shares": Decimal("0"),
                            "transactions": []
                        }

                    broker_groups[broker_name]["total_amount"] += reinvestment_amount
                    broker_groups[broker_name]["total_shares"] += shares_to_purchase
                    broker_groups[broker_name]["transactions"].append(drip_id)

            # Create bulk orders for each broker
            bulk_orders = []
            for broker_name, group_data in broker_groups.items():
                bulk_order_id = str(uuid.uuid4())

                await db.execute(text("""
                    INSERT INTO dividend_bulk_orders
                    (id, asset_id, execution_date, total_amount, total_shares_to_purchase,
                     target_price, broker_name, status, execution_window_start, execution_window_end)
                    VALUES (:id, :asset_id, :date, :amount, :shares, :price, :broker,
                            'pending', :start_time, :end_time)
                """), {
                    "id": bulk_order_id,
                    "asset_id": asset_id,
                    "date": execution_date,
                    "amount": group_data["total_amount"],
                    "shares": group_data["total_shares"],
                    "price": current_price,
                    "broker": broker_name,
                    "start_time": datetime.combine(execution_date, datetime.min.time().replace(hour=9, minute=30)),
                    "end_time": datetime.combine(execution_date, datetime.min.time().replace(hour=16, minute=0))
                })

                # Create allocations for each DRIP transaction in this bulk order
                for drip_id in group_data["transactions"]:
                    allocation_id = str(uuid.uuid4())
                    drip_tx = next(tx for tx in drip_transactions if tx["id"] == drip_id)

                    allocation_percentage = (drip_tx["amount"] / group_data["total_amount"]) * Decimal("100")

                    await db.execute(text("""
                        INSERT INTO drip_bulk_order_allocations
                        (id, drip_transaction_id, dividend_bulk_order_id,
                         allocated_amount, allocated_shares, allocation_percentage)
                        VALUES (:id, :drip_id, :bulk_id, :amount, :shares, :percentage)
                    """), {
                        "id": allocation_id,
                        "drip_id": drip_id,
                        "bulk_id": bulk_order_id,
                        "amount": drip_tx["amount"],
                        "shares": drip_tx["shares"],
                        "percentage": allocation_percentage
                    })

                bulk_orders.append({
                    "id": bulk_order_id,
                    "broker": broker_name,
                    "total_amount": float(group_data["total_amount"]),
                    "total_shares": float(group_data["total_shares"]),
                    "transaction_count": len(group_data["transactions"])
                })

            await db.commit()

            result = {
                "drip_transactions": len(drip_transactions),
                "bulk_orders": bulk_orders,
                "total_amount": float(sum(bo["total_amount"] for bo in bulk_orders))
            }

            logger.info(f"✅ Processed {len(drip_transactions)} DRIP transactions into {len(bulk_orders)} bulk orders")
            return result

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to process DRIP transactions: {str(e)}")
            raise

    @staticmethod
    async def get_user_dividend_summary(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dividend summary for a user"""
        try:
            date_filter = ""
            params = {"user_id": user_id}

            if start_date:
                date_filter += " AND udp.payment_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_filter += " AND udp.payment_date <= :end_date"
                params["end_date"] = end_date

            # Get dividend payments summary
            payments_result = await db.execute(text(f"""
                SELECT
                    COUNT(*) as payment_count,
                    SUM(udp.gross_amount) as total_gross,
                    SUM(udp.net_amount) as total_net,
                    SUM(udp.tax_withheld) as total_tax,
                    COUNT(CASE WHEN udp.reinvestment_preference = 'drip' THEN 1 END) as drip_count
                FROM user_dividend_payments udp
                WHERE udp.user_id = :user_id
                AND udp.status IN ('received', 'reinvested')
                {date_filter}
            """), params)

            payments_summary = payments_result.fetchone()

            # Get DRIP transactions summary
            drip_result = await db.execute(text(f"""
                SELECT
                    COUNT(*) as drip_transaction_count,
                    SUM(dt.reinvestment_amount) as total_reinvested,
                    SUM(dt.shares_purchased) as total_shares_acquired
                FROM drip_transactions dt
                WHERE dt.user_id = :user_id
                AND dt.status = 'executed'
                {date_filter.replace('udp.payment_date', 'dt.transaction_date')}
            """), params)

            drip_summary = drip_result.fetchone()

            return {
                "dividend_payments": {
                    "count": payments_summary[0] or 0,
                    "total_gross": float(payments_summary[1] or 0),
                    "total_net": float(payments_summary[2] or 0),
                    "total_tax": float(payments_summary[3] or 0),
                    "drip_eligible": payments_summary[4] or 0
                },
                "drip_transactions": {
                    "count": drip_summary[0] or 0,
                    "total_reinvested": float(drip_summary[1] or 0),
                    "total_shares_acquired": float(drip_summary[2] or 0)
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to get user dividend summary: {str(e)}")
            raise