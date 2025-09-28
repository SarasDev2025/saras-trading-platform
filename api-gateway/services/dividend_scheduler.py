"""
Advanced Dividend Aggregation Scheduler
Automated background service for dividend management and bulk order processing
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from brokers import OrderSide, OrderStatus as BrokerOrderStatus, OrderType as BrokerOrderType
from models import UserBrokerConnection
from services.dividend_service import DividendService
from services.broker_selection_service import BrokerSelectionService
from services.broker_connection_service import BrokerConnectionService
from services.order_aggregation_service import OrderAggregationService

logger = logging.getLogger(__name__)


class DividendScheduler:
    """Advanced scheduler for automated dividend processing and aggregation"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.is_running = False
        self.check_interval = 3600  # Check every hour
        self.processing_tasks = set()

    async def start(self):
        """Start the dividend scheduler"""
        if self.is_running:
            logger.warning("Dividend scheduler is already running")
            return

        self.is_running = True
        logger.info("🕐 Starting Dividend Aggregation Scheduler")

        # Start main monitoring loop
        asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Dividend scheduler started successfully")

    async def stop(self):
        """Stop the dividend scheduler"""
        self.is_running = False

        # Wait for any ongoing processing tasks to complete
        if self.processing_tasks:
            logger.info(f"⏳ Waiting for {len(self.processing_tasks)} processing tasks to complete")
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)

        logger.info("🛑 Dividend scheduler stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop that runs continuously"""
        while self.is_running:
            try:
                async with self.db_session_factory() as db:
                    # Check for upcoming dividend events
                    await self._process_upcoming_dividends(db)

                    # Process pending DRIP transactions
                    await self._process_pending_drip_transactions(db)

                    # Execute ready bulk orders
                    await self._execute_ready_bulk_orders(db)

                    # Cleanup completed transactions
                    await self._cleanup_old_transactions(db)

            except Exception as e:
                logger.error(f"❌ Error in dividend scheduler monitoring loop: {str(e)}")

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def _process_upcoming_dividends(self, db: AsyncSession):
        """Process upcoming dividend events and create position snapshots"""
        try:
            today = date.today()
            tomorrow = today + timedelta(days=1)

            # Find dividends with record date tomorrow (need to create snapshots today)
            upcoming_result = await db.execute(text("""
                SELECT id, asset_id, record_date, ex_dividend_date, dividend_amount
                FROM dividend_declarations
                WHERE record_date = :tomorrow
                AND status = 'announced'
                AND NOT EXISTS (
                    SELECT 1 FROM user_position_snapshots ups
                    WHERE ups.dividend_declaration_id = dividend_declarations.id
                )
            """), {"tomorrow": tomorrow})

            upcoming_dividends = upcoming_result.fetchall()

            for dividend in upcoming_dividends:
                dividend_id = str(dividend[0])
                logger.info(f"📸 Processing position snapshots for dividend {dividend_id}")

                # Create position snapshots in background
                task = asyncio.create_task(
                    self._create_position_snapshots_task(dividend_id, tomorrow)
                )
                self.processing_tasks.add(task)
                task.add_done_callback(self.processing_tasks.discard)

            if upcoming_dividends:
                logger.info(f"🔄 Started position snapshot creation for {len(upcoming_dividends)} dividends")

        except Exception as e:
            logger.error(f"❌ Error processing upcoming dividends: {str(e)}")

    async def _create_position_snapshots_task(self, dividend_id: str, snapshot_date: date):
        """Background task to create position snapshots"""
        try:
            async with self.db_session_factory() as db:
                snapshots = await DividendService.create_position_snapshots_for_dividend(
                    db=db,
                    dividend_declaration_id=dividend_id,
                    snapshot_date=snapshot_date
                )
                logger.info(f"✅ Created {len(snapshots)} position snapshots for dividend {dividend_id}")

                # Automatically calculate dividend payments
                payments = await DividendService.calculate_dividend_payments(
                    db=db,
                    dividend_declaration_id=dividend_id
                )
                logger.info(f"💰 Calculated {len(payments)} dividend payments for dividend {dividend_id}")

        except Exception as e:
            logger.error(f"❌ Error creating position snapshots for dividend {dividend_id}: {str(e)}")

    async def _process_pending_drip_transactions(self, db: AsyncSession):
        """Process pending DRIP transactions and create bulk orders"""
        try:
            today = date.today()

            # Find assets with received dividend payments that have DRIP enabled users
            drip_ready_result = await db.execute(text("""
                SELECT DISTINCT udp.asset_id, a.symbol
                FROM user_dividend_payments udp
                JOIN assets a ON udp.asset_id = a.id
                JOIN user_drip_preferences udrip ON udp.user_id = udrip.user_id
                WHERE udp.status = 'received'
                AND udp.reinvestment_preference = 'drip'
                AND udrip.is_enabled = true
                AND udp.payment_date <= :today
                AND NOT EXISTS (
                    SELECT 1 FROM drip_transactions dt
                    WHERE dt.user_dividend_payment_id = udp.id
                )
            """), {"today": today})

            drip_ready_assets = drip_ready_result.fetchall()

            for asset_id, symbol in drip_ready_assets:
                logger.info(f"🔄 Processing DRIP transactions for {symbol} ({asset_id})")

                # Process DRIP transactions in background
                task = asyncio.create_task(
                    self._process_drip_for_asset_task(str(asset_id), today)
                )
                self.processing_tasks.add(task)
                task.add_done_callback(self.processing_tasks.discard)

            if drip_ready_assets:
                logger.info(f"🔄 Started DRIP processing for {len(drip_ready_assets)} assets")

        except Exception as e:
            logger.error(f"❌ Error processing pending DRIP transactions: {str(e)}")

    async def _process_drip_for_asset_task(self, asset_id: str, execution_date: date):
        """Background task to process DRIP transactions for an asset"""
        try:
            async with self.db_session_factory() as db:
                result = await DividendService.process_drip_transactions(
                    db=db,
                    asset_id=asset_id,
                    execution_date=execution_date
                )

                logger.info(f"✅ Processed {result['drip_transactions']} DRIP transactions into {len(result['bulk_orders'])} bulk orders for asset {asset_id}")

                # Schedule bulk order execution
                for bulk_order in result['bulk_orders']:
                    await self._schedule_bulk_order_execution(bulk_order['id'], execution_date)

        except Exception as e:
            logger.error(f"❌ Error processing DRIP for asset {asset_id}: {str(e)}")

    async def _schedule_bulk_order_execution(self, bulk_order_id: str, execution_date: date):
        """Schedule a bulk order for execution during market hours"""
        try:
            # Calculate optimal execution time (market hours)
            execution_time = datetime.combine(execution_date, datetime.min.time().replace(hour=10, minute=0))

            # If it's already past the execution time today, schedule for next trading day
            if datetime.now() > execution_time:
                execution_time += timedelta(days=1)

            # Schedule the execution
            delay = (execution_time - datetime.now()).total_seconds()
            if delay > 0:
                asyncio.create_task(self._delayed_bulk_order_execution(bulk_order_id, delay))
                logger.info(f"⏰ Scheduled bulk order {bulk_order_id} for execution at {execution_time}")
            else:
                # Execute immediately if time has passed
                asyncio.create_task(self._execute_bulk_order_task(bulk_order_id))

        except Exception as e:
            logger.error(f"❌ Error scheduling bulk order execution: {str(e)}")

    async def _delayed_bulk_order_execution(self, bulk_order_id: str, delay_seconds: float):
        """Execute a bulk order after a delay"""
        await asyncio.sleep(delay_seconds)
        await self._execute_bulk_order_task(bulk_order_id)

    async def _execute_bulk_order_task(self, bulk_order_id: str):
        """Execute a bulk order via broker APIs"""
        try:
            async with self.db_session_factory() as db:
                # Get bulk order details
                bulk_order_result = await db.execute(text("""
                    SELECT dbo.*, a.symbol, a.name
                    FROM dividend_bulk_orders dbo
                    JOIN assets a ON dbo.asset_id = a.id
                    WHERE dbo.id = :bulk_order_id
                    AND dbo.status = 'pending'
                """), {"bulk_order_id": bulk_order_id})

                bulk_order = bulk_order_result.fetchone()
                if not bulk_order:
                    logger.warning(f"⚠️  Bulk order {bulk_order_id} not found or not pending")
                    return

                # Execute the bulk order via broker
                await self._execute_broker_order(db, bulk_order)

        except Exception as e:
            logger.error(f"❌ Error executing bulk order {bulk_order_id}: {str(e)}")

    async def _execute_broker_order(self, db: AsyncSession, bulk_order):
        """Execute the actual broker order via real broker APIs"""
        try:
            symbol = bulk_order.symbol
            quantity = Decimal(str(bulk_order.total_shares_to_purchase))
            broker_name = bulk_order.broker_name

            logger.info(f"📈 Executing bulk order: {quantity} shares of {symbol} via {broker_name}")

            # Get master broker connection for executing aggregated orders
            broker_connection = await self._get_master_broker_connection(db, broker_name)

            if not broker_connection:
                logger.error(f"❌ No master broker connection found for {broker_name}")
                await self._mark_bulk_order_failed(db, bulk_order, "No broker connection available")
                return

            # Get broker instance
            broker, _ = await BrokerConnectionService.ensure_broker_session(broker_connection)

            try:
                # Place the bulk order with the broker
                logger.info(f"🔄 Placing bulk dividend order: {symbol} BUY {quantity} via {broker_name}")

                broker_order = await broker.place_order(
                    symbol=symbol,
                    side=OrderSide.BUY,  # DRIP orders are always buy orders
                    quantity=quantity,
                    order_type=BrokerOrderType.MARKET
                )

                # Extract execution details from broker response
                execution_price = float(broker_order.price) if hasattr(broker_order, 'price') and broker_order.price else float(bulk_order.target_price or 100.00)
                broker_order_id = broker_order.order_id
                order_status = broker_order.status

                logger.info(f"✅ Broker order placed: {broker_order_id}, status: {order_status}")

                # Update bulk order based on broker response
                if order_status == BrokerOrderStatus.FILLED:
                    await self._mark_bulk_order_executed(db, bulk_order, broker_order_id, execution_price)
                elif order_status in [BrokerOrderStatus.PENDING, BrokerOrderStatus.PARTIALLY_FILLED]:
                    await self._mark_bulk_order_pending(db, bulk_order, broker_order_id, execution_price)
                else:
                    await self._mark_bulk_order_failed(db, bulk_order, f"Broker order {order_status}")
                    return

            except Exception as broker_exc:
                logger.error(f"❌ Broker API call failed for {symbol}: {str(broker_exc)}")
                await self._mark_bulk_order_failed(db, bulk_order, f"Broker API error: {str(broker_exc)}")
                return

            # Update user dividend payments to reinvested status for successful orders
            if order_status == BrokerOrderStatus.FILLED:
                await db.execute(text("""
                    UPDATE user_dividend_payments
                    SET status = 'reinvested',
                        updated_at = CURRENT_TIMESTAMP
                    FROM drip_transactions dt
                    WHERE user_dividend_payments.id = dt.user_dividend_payment_id
                    AND dt.id IN (
                        SELECT dboa.drip_transaction_id
                        FROM drip_bulk_order_allocations dboa
                        WHERE dboa.dividend_bulk_order_id = :bulk_order_id
                    )
                """), {"bulk_order_id": str(bulk_order.id)})

            await db.commit()

            logger.info(f"✅ Successfully executed bulk order {bulk_order.id}: {quantity} shares of {symbol} at ${execution_price}")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error executing broker order: {str(e)}")
            raise

    async def _get_master_broker_connection(self, db: AsyncSession, broker_name: str) -> Optional[UserBrokerConnection]:
        """Get the master/admin broker connection for executing bulk dividend orders"""
        try:
            # Look for a connection with alias 'master', 'admin', or 'aggregator'
            result = await db.execute(
                select(UserBrokerConnection).where(
                    UserBrokerConnection.broker_type == broker_name,
                    UserBrokerConnection.alias.in_(['master', 'admin', 'aggregator', 'dividend'])
                ).limit(1)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                # Fallback to any active connection of this broker type
                result = await db.execute(
                    select(UserBrokerConnection).where(
                        UserBrokerConnection.broker_type == broker_name,
                        UserBrokerConnection.status == 'active'
                    ).limit(1)
                )
                connection = result.scalar_one_or_none()

                if connection:
                    logger.warning(
                        f"⚠️ Using non-admin connection for {broker_name} dividend orders. "
                        f"Consider setting up dedicated admin accounts."
                    )

            return connection

        except Exception as exc:
            logger.error(f"❌ Error getting master broker connection: {exc}")
            return None

    async def _mark_bulk_order_executed(self, db: AsyncSession, bulk_order, broker_order_id: str, execution_price: float):
        """Mark bulk order as successfully executed"""
        await db.execute(text("""
            UPDATE dividend_bulk_orders
            SET status = 'executed',
                actual_price = :actual_price,
                broker_order_id = :broker_order_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :bulk_order_id
        """), {
            "actual_price": execution_price,
            "broker_order_id": broker_order_id,
            "bulk_order_id": str(bulk_order.id)
        })

        # Update individual DRIP transactions to executed status
        await db.execute(text("""
            UPDATE drip_transactions
            SET status = 'executed',
                broker_transaction_id = :broker_order_id || '_' || id,
                updated_at = CURRENT_TIMESTAMP
            FROM drip_bulk_order_allocations dboa
            WHERE drip_transactions.id = dboa.drip_transaction_id
            AND dboa.dividend_bulk_order_id = :bulk_order_id
        """), {
            "broker_order_id": broker_order_id,
            "bulk_order_id": str(bulk_order.id)
        })

    async def _mark_bulk_order_pending(self, db: AsyncSession, bulk_order, broker_order_id: str, execution_price: float):
        """Mark bulk order as pending (submitted but not filled)"""
        await db.execute(text("""
            UPDATE dividend_bulk_orders
            SET status = 'pending',
                actual_price = :actual_price,
                broker_order_id = :broker_order_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :bulk_order_id
        """), {
            "actual_price": execution_price,
            "broker_order_id": broker_order_id,
            "bulk_order_id": str(bulk_order.id)
        })

        # Update individual DRIP transactions to pending status
        await db.execute(text("""
            UPDATE drip_transactions
            SET status = 'pending',
                broker_transaction_id = :broker_order_id || '_' || id,
                updated_at = CURRENT_TIMESTAMP
            FROM drip_bulk_order_allocations dboa
            WHERE drip_transactions.id = dboa.drip_transaction_id
            AND dboa.dividend_bulk_order_id = :bulk_order_id
        """), {
            "broker_order_id": broker_order_id,
            "bulk_order_id": str(bulk_order.id)
        })

    async def _mark_bulk_order_failed(self, db: AsyncSession, bulk_order, error_message: str):
        """Mark bulk order as failed"""
        await db.execute(text("""
            UPDATE dividend_bulk_orders
            SET status = 'failed',
                error_message = :error_message,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :bulk_order_id
        """), {
            "error_message": error_message,
            "bulk_order_id": str(bulk_order.id)
        })

        # Update individual DRIP transactions to failed status
        await db.execute(text("""
            UPDATE drip_transactions
            SET status = 'failed',
                error_message = :error_message,
                updated_at = CURRENT_TIMESTAMP
            FROM drip_bulk_order_allocations dboa
            WHERE drip_transactions.id = dboa.drip_transaction_id
            AND dboa.dividend_bulk_order_id = :bulk_order_id
        """), {
            "error_message": error_message,
            "bulk_order_id": str(bulk_order.id)
        })

    async def _execute_ready_bulk_orders(self, db: AsyncSession):
        """Find and execute bulk orders that are ready for execution"""
        try:
            now = datetime.now()

            # Find bulk orders ready for execution
            ready_orders_result = await db.execute(text("""
                SELECT id, asset_id, broker_name, total_shares_to_purchase
                FROM dividend_bulk_orders
                WHERE status = 'pending'
                AND execution_window_start <= :now
                AND execution_window_end >= :now
            """), {"now": now})

            ready_orders = ready_orders_result.fetchall()

            for order in ready_orders:
                order_id = str(order[0])
                logger.info(f"⚡ Executing ready bulk order {order_id}")

                # Execute in background
                task = asyncio.create_task(self._execute_bulk_order_task(order_id))
                self.processing_tasks.add(task)
                task.add_done_callback(self.processing_tasks.discard)

            if ready_orders:
                logger.info(f"⚡ Started execution for {len(ready_orders)} ready bulk orders")

        except Exception as e:
            logger.error(f"❌ Error executing ready bulk orders: {str(e)}")

    async def _cleanup_old_transactions(self, db: AsyncSession):
        """Cleanup old completed transactions and maintain system performance"""
        try:
            # Archive old dividend declarations (older than 1 year)
            cutoff_date = date.today() - timedelta(days=365)

            # Log cleanup activity
            old_declarations_result = await db.execute(text("""
                SELECT COUNT(*) FROM dividend_declarations
                WHERE payment_date < :cutoff_date
                AND status = 'paid'
            """), {"cutoff_date": cutoff_date})

            old_count = old_declarations_result.scalar()

            if old_count > 0:
                logger.info(f"🧹 Found {old_count} old dividend declarations to archive")

                # In a real implementation, you might archive to a separate table
                # For now, just update status to 'archived'
                await db.execute(text("""
                    UPDATE dividend_declarations
                    SET status = 'archived',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE payment_date < :cutoff_date
                    AND status = 'paid'
                """), {"cutoff_date": cutoff_date})

                await db.commit()
                logger.info(f"✅ Archived {old_count} old dividend declarations")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")

    async def get_scheduler_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        try:
            # Get pending dividends count
            pending_dividends_result = await db.execute(text("""
                SELECT COUNT(*) FROM dividend_declarations
                WHERE status = 'announced'
                AND record_date >= CURRENT_DATE
            """))
            pending_dividends = pending_dividends_result.scalar()

            # Get pending DRIP transactions
            pending_drip_result = await db.execute(text("""
                SELECT COUNT(*) FROM user_dividend_payments
                WHERE status = 'received'
                AND reinvestment_preference = 'drip'
            """))
            pending_drip = pending_drip_result.scalar()

            # Get pending bulk orders
            pending_bulk_result = await db.execute(text("""
                SELECT COUNT(*) FROM dividend_bulk_orders
                WHERE status = 'pending'
            """))
            pending_bulk = pending_bulk_result.scalar()

            return {
                "is_running": self.is_running,
                "check_interval_seconds": self.check_interval,
                "active_processing_tasks": len(self.processing_tasks),
                "pending_dividends": pending_dividends,
                "pending_drip_transactions": pending_drip,
                "pending_bulk_orders": pending_bulk,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {str(e)}")
            return {
                "is_running": self.is_running,
                "error": str(e)
            }


# Global scheduler instance
dividend_scheduler = None


async def initialize_dividend_scheduler(db_session_factory):
    """Initialize the global dividend scheduler"""
    global dividend_scheduler
    if dividend_scheduler is None:
        dividend_scheduler = DividendScheduler(db_session_factory)
        await dividend_scheduler.start()
        logger.info("🚀 Dividend scheduler initialized and started")


async def get_dividend_scheduler() -> DividendScheduler:
    """Get the global dividend scheduler instance"""
    global dividend_scheduler
    if dividend_scheduler is None:
        raise RuntimeError("Dividend scheduler not initialized")
    return dividend_scheduler