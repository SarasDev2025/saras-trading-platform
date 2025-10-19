"""
Algorithm Scheduler Service
Runs active algorithms on their configured intervals
Supports both Indian (Zerodha) and US (Alpaca) market hours
"""
import asyncio
import logging
from datetime import datetime, time, timezone
from typing import Optional
import pytz

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.algorithm_engine import AlgorithmEngine
from services.signal_processor import SignalProcessor
from config.database import get_db_session
from schedulers.flexible_scheduler import FlexibleSchedulerMixin

logger = logging.getLogger(__name__)


class AlgorithmScheduler(FlexibleSchedulerMixin):
    """Background scheduler for automated algorithm execution"""

    # Market hours (local time)
    MARKET_HOURS = {
        'IN': {  # Indian market (Zerodha)
            'timezone': 'Asia/Kolkata',
            'open': time(9, 15),
            'close': time(15, 30),
            'days': [0, 1, 2, 3, 4]  # Mon-Fri
        },
        'US': {  # US market (Alpaca)
            'timezone': 'America/New_York',
            'open': time(9, 30),
            'close': time(16, 0),
            'days': [0, 1, 2, 3, 4]  # Mon-Fri
        },
        'GB': {  # GB market (defaults to US hours for Alpaca)
            'timezone': 'Europe/London',
            'open': time(8, 0),
            'close': time(16, 30),
            'days': [0, 1, 2, 3, 4]
        }
    }

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler background task"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("Algorithm scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Algorithm scheduler stopped")

    async def _run_scheduler(self):
        """Main scheduler loop - runs every minute"""
        while self.running:
            try:
                await self._check_and_execute_algorithms()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            # Wait 60 seconds before next check
            await asyncio.sleep(60)

    async def _check_and_execute_algorithms(self):
        """Check for algorithms that need to be executed"""
        async with get_db_session() as db:
            try:
                # Get all active algorithms with auto_run enabled
                result = await db.execute(text("""
                    SELECT
                        a.id,
                        a.user_id,
                        a.name,
                        a.execution_interval,
                        a.last_run_at,
                        a.scheduling_type,
                        a.execution_time_windows,
                        a.execution_times,
                        a.run_continuously,
                        a.run_duration_type,
                        a.run_duration_value,
                        a.run_start_date,
                        a.run_end_date,
                        a.auto_stop_on_loss,
                        a.auto_stop_loss_threshold,
                        a.currently_executing,
                        a.created_at,
                        u.region,
                        u.trading_mode
                    FROM trading_algorithms a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.status = 'active'
                    AND a.auto_run = true
                    AND (a.currently_executing = false OR a.currently_executing IS NULL)
                """))

                algorithms = result.fetchall()

                if not algorithms:
                    return

                logger.info(f"Checking {len(algorithms)} active algorithms")

                for algo in algorithms:
                    try:
                        # Check if market is open for this algorithm's region
                        if not self._is_market_open(algo.region):
                            continue

                        # Check duration-based auto-stop
                        if await self._should_auto_stop_duration(algo):
                            await self._auto_stop_algorithm(
                                db, algo.id,
                                f"Duration limit reached ({algo.run_duration_type}: {algo.run_duration_value})"
                            )
                            continue

                        # Check loss-based auto-stop
                        if await self._should_stop_due_to_losses(db, algo):
                            await self._auto_stop_algorithm(
                                db, algo.id,
                                f"Loss threshold exceeded (${algo.auto_stop_loss_threshold})"
                            )
                            continue

                        # Get market config for scheduling
                        market_config = self.MARKET_HOURS.get(algo.region, self.MARKET_HOURS['US'])

                        # Check if algorithm should run based on scheduling configuration
                        if not self._should_run_based_on_schedule(algo, market_config):
                            continue

                        # Mark as currently executing
                        await self._mark_executing(db, algo.id, True)

                        # Execute algorithm
                        logger.info(
                            f"Auto-executing algorithm: {algo.name} (ID: {algo.id}) "
                            f"for user {algo.user_id}"
                        )

                        result = await AlgorithmEngine.execute_algorithm(
                            db=db,
                            algorithm_id=algo.id,
                            user_id=algo.user_id,
                            execution_type='scheduled',
                            dry_run=False
                        )

                        if result['success'] and result.get('signals'):
                            # Process signals if any were generated
                            await self._process_signals(
                                db=db,
                                algorithm_id=algo.id,
                                execution_id=result['execution_id'],
                                signals=result['signals'],
                                user_id=algo.user_id,
                                broker=result['broker'],
                                trading_mode=result['trading_mode']
                            )

                        # Update performance snapshot
                        await self._update_performance_snapshot(
                            db=db,
                            algorithm_id=algo.id,
                            user_id=algo.user_id
                        )

                        # Mark execution complete
                        await self._mark_executing(db, algo.id, False)

                        # Update next scheduled run time
                        await self._update_next_scheduled_run(db, algo)

                    except Exception as e:
                        logger.error(
                            f"Failed to execute algorithm {algo.id} ({algo.name}): {e}"
                        )
                        # Mark execution complete even on error
                        await self._mark_executing(db, algo.id, False)
                        continue

            except Exception as e:
                logger.error(f"Error in scheduler check: {e}")

    def _is_market_open(self, region: str) -> bool:
        """Check if market is currently open for the given region"""
        market_config = self.MARKET_HOURS.get(region)
        if not market_config:
            logger.warning(f"Unknown region {region}, defaulting to US hours")
            market_config = self.MARKET_HOURS['US']

        tz = pytz.timezone(market_config['timezone'])
        now = datetime.now(tz)

        # Check if it's a trading day (Mon-Fri)
        if now.weekday() not in market_config['days']:
            return False

        # Check if within market hours
        current_time = now.time()
        return market_config['open'] <= current_time <= market_config['close']

    def _should_run_now(self, interval: str, last_run_at: Optional[datetime]) -> bool:
        """
        Determine if algorithm should run now based on interval

        Intervals: '1min', '5min', '15min', 'hourly', 'daily', 'manual'
        """
        if interval == 'manual':
            return False

        now = datetime.now(timezone.utc)

        # If never run before, run now
        if not last_run_at:
            return True

        # Calculate time since last run
        time_since_last_run = (now - last_run_at).total_seconds()

        # Interval mappings (in seconds)
        interval_seconds = {
            '1min': 60,
            '5min': 300,
            '15min': 900,
            'hourly': 3600,
            'daily': 86400
        }

        required_interval = interval_seconds.get(interval)
        if not required_interval:
            logger.warning(f"Unknown interval {interval}, skipping")
            return False

        # Run if enough time has passed
        return time_since_last_run >= required_interval

    async def _process_signals(
        self,
        db: AsyncSession,
        algorithm_id: str,
        execution_id: str,
        signals: list,
        user_id: str,
        broker: str,
        trading_mode: str
    ):
        """Process signals generated by algorithm execution"""
        try:
            # Get portfolio ID
            portfolio_result = await db.execute(text("""
                SELECT id
                FROM portfolios
                WHERE user_id = :user_id
                AND trading_mode = :trading_mode
                AND is_default = true
                LIMIT 1
            """), {"user_id": str(user_id), "trading_mode": trading_mode})

            portfolio = portfolio_result.fetchone()
            if not portfolio:
                logger.error(f"No portfolio found for user {user_id} in {trading_mode} mode")
                return

            # Process signals via SignalProcessor
            result = await SignalProcessor.process_signals(
                db=db,
                algorithm_id=algorithm_id,
                execution_id=execution_id,
                signals=signals,
                user_id=user_id,
                portfolio_id=portfolio.id,
                broker=broker,
                trading_mode=trading_mode,
                dry_run=False
            )

            logger.info(
                f"Processed {result['processed']} signals for algorithm {algorithm_id}: "
                f"{result['executed']} executed, {result['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Failed to process signals for algorithm {algorithm_id}: {e}")

    async def _update_performance_snapshot(
        self,
        db: AsyncSession,
        algorithm_id: str,
        user_id: str
    ):
        """Update daily performance snapshot for algorithm"""
        try:
            today = datetime.now(timezone.utc).date()

            # Get today's executed signals
            result = await db.execute(text("""
                SELECT
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN s.execution_status = 'filled' THEN 1 ELSE 0 END) as filled_signals,
                    SUM(CASE
                        WHEN s.signal_type = 'buy' AND s.execution_status = 'filled'
                        THEN s.quantity * s.execution_price
                        ELSE 0
                    END) as total_buys,
                    SUM(CASE
                        WHEN s.signal_type = 'sell' AND s.execution_status = 'filled'
                        THEN s.quantity * s.execution_price
                        ELSE 0
                    END) as total_sells
                FROM algorithm_signals s
                WHERE s.algorithm_id = :algorithm_id
                AND DATE(s.generated_at) = :today
            """), {"algorithm_id": str(algorithm_id), "today": today})

            stats = result.fetchone()

            if not stats or stats.total_signals == 0:
                return

            # Calculate daily P&L (simplified - actual P&L comes from transactions)
            daily_pnl = (stats.total_sells or 0) - (stats.total_buys or 0)

            # Get cumulative P&L
            cumulative_result = await db.execute(text("""
                SELECT COALESCE(SUM(daily_pnl), 0) as cumulative_pnl
                FROM algorithm_performance_snapshots
                WHERE algorithm_id = :algorithm_id
                AND snapshot_date < :today
            """), {"algorithm_id": str(algorithm_id), "today": today})

            cumulative_row = cumulative_result.fetchone()
            cumulative_pnl = (cumulative_row.cumulative_pnl or 0) + daily_pnl

            # Calculate win rate for today
            win_rate_result = await db.execute(text("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN (
                        CASE WHEN s.signal_type = 'sell'
                        THEN s.execution_price > (SELECT average_cost FROM portfolio_holdings
                                                   WHERE asset_id = s.asset_id LIMIT 1)
                        ELSE true
                        END
                    ) THEN 1 ELSE 0 END) as winning_trades
                FROM algorithm_signals s
                WHERE s.algorithm_id = :algorithm_id
                AND s.execution_status = 'filled'
                AND DATE(s.executed_at) = :today
            """), {"algorithm_id": str(algorithm_id), "today": today})

            win_rate_row = win_rate_result.fetchone()
            win_rate = None
            if win_rate_row and win_rate_row.total_trades > 0:
                win_rate = (win_rate_row.winning_trades / win_rate_row.total_trades) * 100

            # Upsert snapshot
            await db.execute(text("""
                INSERT INTO algorithm_performance_snapshots (
                    algorithm_id, user_id, snapshot_date,
                    total_trades, winning_trades, losing_trades,
                    daily_pnl, cumulative_pnl, win_rate
                )
                VALUES (
                    :algorithm_id, :user_id, :snapshot_date,
                    :total_trades, :winning_trades, :losing_trades,
                    :daily_pnl, :cumulative_pnl, :win_rate
                )
                ON CONFLICT (algorithm_id, snapshot_date)
                DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    winning_trades = EXCLUDED.winning_trades,
                    losing_trades = EXCLUDED.losing_trades,
                    daily_pnl = EXCLUDED.daily_pnl,
                    cumulative_pnl = EXCLUDED.cumulative_pnl,
                    win_rate = EXCLUDED.win_rate,
                    updated_at = NOW()
            """), {
                "algorithm_id": str(algorithm_id),
                "user_id": str(user_id),
                "snapshot_date": today,
                "total_trades": stats.filled_signals or 0,
                "winning_trades": win_rate_row.winning_trades if win_rate_row else 0,
                "losing_trades": (stats.filled_signals or 0) - (win_rate_row.winning_trades if win_rate_row else 0),
                "daily_pnl": daily_pnl,
                "cumulative_pnl": cumulative_pnl,
                "win_rate": win_rate
            })

            await db.commit()

            logger.info(
                f"Updated performance snapshot for algorithm {algorithm_id}: "
                f"Daily P&L: ${daily_pnl:.2f}, Cumulative: ${cumulative_pnl:.2f}"
            )

        except Exception as e:
            logger.error(f"Failed to update performance snapshot: {e}")
            await db.rollback()


# Global scheduler instance
_scheduler_instance: Optional[AlgorithmScheduler] = None


async def get_scheduler() -> AlgorithmScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AlgorithmScheduler()
    return _scheduler_instance


async def start_scheduler():
    """Start the global scheduler"""
    scheduler = await get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler_instance
    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None
