"""
Trade Scheduler - Automatic processing of queued orders

This service runs in the background and automatically processes
queued orders at regular intervals, providing true time-based aggregation.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from services.trade_queue_service import TradeQueueService

logger = logging.getLogger(__name__)


class TradeScheduler:
    """Background scheduler for automated trade queue processing"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.is_running = False
        self.process_interval_seconds = 60  # Check every minute
        self.scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("[TradeScheduler] Scheduler already running")
            return

        logger.info("[TradeScheduler] Starting trade queue scheduler...")
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop the background scheduler"""
        if not self.is_running:
            return

        logger.info("[TradeScheduler] Stopping trade queue scheduler...")
        self.is_running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        await self.engine.dispose()

    async def _scheduler_loop(self):
        """Main scheduler loop that runs continuously"""
        logger.info(f"[TradeScheduler] Scheduler loop started, checking every {self.process_interval_seconds} seconds")

        while self.is_running:
            try:
                await self._process_queued_orders()

                # Wait for next check interval
                await asyncio.sleep(self.process_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[TradeScheduler] Error in scheduler loop: {exc}")
                # Wait a bit before retrying on error
                await asyncio.sleep(30)

        logger.info("[TradeScheduler] Scheduler loop stopped")

    async def _process_queued_orders(self):
        """Process queued orders that are ready for execution"""
        try:
            async with self.session_factory() as db:
                result = await TradeQueueService.process_queued_orders(db)

                if result["processed_batches"] > 0:
                    logger.info(
                        f"[TradeScheduler] Processed {result['processed_batches']} batches "
                        f"with {result['total_orders']} orders at {result['execution_time']}"
                    )
                else:
                    logger.debug("[TradeScheduler] No orders ready for processing")

                await db.commit()

        except Exception as exc:
            logger.error(f"[TradeScheduler] Error processing queued orders: {exc}")

    async def force_process_now(self) -> dict:
        """Force immediate processing of all queued orders (for testing/manual intervention)"""
        try:
            async with self.session_factory() as db:
                result = await TradeQueueService.process_queued_orders(db)
                await db.commit()

                logger.info(f"[TradeScheduler] Force processing completed: {result}")
                return result

        except Exception as exc:
            logger.error(f"[TradeScheduler] Error in force processing: {exc}")
            return {"error": str(exc), "processed_batches": 0, "total_orders": 0}

    async def get_scheduler_status(self) -> dict:
        """Get current scheduler status and statistics"""
        try:
            async with self.session_factory() as db:
                queue_status = await TradeQueueService.get_queue_status(db)

            return {
                "is_running": self.is_running,
                "process_interval_seconds": self.process_interval_seconds,
                "current_time": datetime.now(timezone.utc).isoformat(),
                "queue_status": queue_status
            }

        except Exception as exc:
            logger.error(f"[TradeScheduler] Error getting scheduler status: {exc}")
            return {
                "is_running": self.is_running,
                "error": str(exc)
            }


# Global scheduler instance
_scheduler: Optional[TradeScheduler] = None


async def start_trade_scheduler(database_url: str):
    """Start the global trade scheduler"""
    global _scheduler

    if _scheduler and _scheduler.is_running:
        logger.warning("[TradeScheduler] Global scheduler already running")
        return

    _scheduler = TradeScheduler(database_url)
    await _scheduler.start()


async def stop_trade_scheduler():
    """Stop the global trade scheduler"""
    global _scheduler

    if _scheduler:
        await _scheduler.stop()
        _scheduler = None


def get_trade_scheduler() -> Optional[TradeScheduler]:
    """Get the global trade scheduler instance"""
    return _scheduler


# FastAPI lifespan integration
async def trade_scheduler_lifespan(database_url: str):
    """Context manager for FastAPI lifespan integration"""
    await start_trade_scheduler(database_url)
    try:
        yield
    finally:
        await stop_trade_scheduler()


# Example usage in FastAPI main.py:
"""
from contextlib import asynccontextmanager
from services.trade_scheduler import trade_scheduler_lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database_url = "postgresql+asyncpg://user:pass@localhost/db"
    async with trade_scheduler_lifespan(database_url):
        yield

app = FastAPI(lifespan=lifespan)
"""