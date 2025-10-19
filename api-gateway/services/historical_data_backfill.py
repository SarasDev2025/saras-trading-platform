"""
Historical Data Backfill Service

Background service that gradually backfills historical market data
for all symbols used by active algorithms.

Runs nightly (configurable) to:
1. Identify symbols needing historical data
2. Fill data gaps for existing symbols
3. Backfill 2 years of data for new symbols
4. Track progress and avoid redundant fetches

NOTE: This service is DISABLED by default. To enable:
1. Import in main.py: from services.historical_data_backfill import start_backfill_service, stop_backfill_service
2. Add to startup: await start_backfill_service() in _start_background_tasks()
3. Add to shutdown: await stop_backfill_service() in _stop_background_tasks()
"""
import asyncio
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Set
import pandas as pd

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.data_providers.factory import DataProviderFactory
from services.redis_cache_service import RedisCacheService

logger = logging.getLogger(__name__)


class HistoricalDataBackfillService:
    """
    Background service for backfilling historical market data

    Features:
    - Gradual backfill to avoid rate limits
    - Gap detection and filling
    - Configurable backfill depth (default: 2 years)
    - Progress tracking
    - Error recovery
    """

    def __init__(
        self,
        db_session_factory,
        cache_service: Optional[RedisCacheService] = None,
        backfill_days: int = 730,  # 2 years
        run_hour: int = 1,  # 1 AM (after market close)
        max_symbols_per_run: int = 50,
        batch_size: int = 10
    ):
        """
        Initialize Historical Data Backfill Service

        Args:
            db_session_factory: Database session factory
            cache_service: Optional Redis cache service (for caching fetched data)
            backfill_days: Number of days to backfill (default: 730 = 2 years)
            run_hour: Hour of day to run (0-23, default: 1 AM)
            max_symbols_per_run: Maximum symbols to process per run
            batch_size: Number of symbols to fetch in parallel
        """
        self.db_session_factory = db_session_factory
        self.cache_service = cache_service
        self.backfill_days = backfill_days
        self.run_hour = run_hour
        self.max_symbols_per_run = max_symbols_per_run
        self.batch_size = batch_size

        # Background task control
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Data provider
        self.data_provider_factory = DataProviderFactory()

        # Statistics
        self.total_symbols_processed = 0
        self.total_bars_stored = 0
        self.total_errors = 0
        self.last_run_time: Optional[datetime] = None
        self.last_run_duration: Optional[float] = None

    async def start(self):
        """Start the backfill service"""
        if self._running:
            logger.warning("Backfill service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_backfill_loop())
        logger.info("🚀 Historical Data Backfill Service started")

    async def stop(self):
        """Stop the backfill service"""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 Historical Data Backfill Service stopped")

    async def _run_backfill_loop(self):
        """Main loop for backfill service - runs nightly"""
        try:
            logger.info(f"Backfill service will run daily at {self.run_hour}:00")

            while self._running:
                try:
                    # Calculate next run time
                    now = datetime.now()
                    next_run = now.replace(
                        hour=self.run_hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )

                    # If we've passed today's run time, schedule for tomorrow
                    if now >= next_run:
                        next_run += timedelta(days=1)

                    # Wait until next run time
                    wait_seconds = (next_run - now).total_seconds()
                    logger.info(f"Next backfill run scheduled for {next_run} ({wait_seconds / 3600:.1f} hours)")
                    await asyncio.sleep(wait_seconds)

                    # Run backfill
                    await self._run_backfill()

                except Exception as e:
                    logger.error(f"Error in backfill loop: {e}", exc_info=True)
                    self.total_errors += 1
                    # Wait 1 hour before retrying on error
                    await asyncio.sleep(3600)

        except asyncio.CancelledError:
            logger.info("Backfill loop cancelled")
            raise

    async def _run_backfill(self):
        """Execute a single backfill run"""
        start_time = datetime.utcnow()
        logger.info("=" * 60)
        logger.info("🔄 Starting historical data backfill run")
        logger.info("=" * 60)

        try:
            # Get symbols that need backfilling
            symbols_to_backfill = await self._get_symbols_needing_backfill()

            if not symbols_to_backfill:
                logger.info("✅ No symbols need backfilling")
                return

            # Limit to max_symbols_per_run
            symbols_to_backfill = symbols_to_backfill[:self.max_symbols_per_run]

            logger.info(f"📋 Processing {len(symbols_to_backfill)} symbols")

            # Process in batches to avoid overwhelming the API
            for i in range(0, len(symbols_to_backfill), self.batch_size):
                batch = symbols_to_backfill[i:i + self.batch_size]

                logger.info(f"Processing batch {i // self.batch_size + 1}: {batch}")

                # Process each symbol in batch
                tasks = [self._backfill_symbol(symbol_info) for symbol_info in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successes and errors
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {result}")
                        self.total_errors += 1

                # Small delay between batches to avoid rate limits
                if i + self.batch_size < len(symbols_to_backfill):
                    await asyncio.sleep(5)

            # Update statistics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.last_run_time = start_time
            self.last_run_duration = duration

            logger.info("=" * 60)
            logger.info(f"✅ Backfill run completed in {duration:.1f}s")
            logger.info(f"📊 Total symbols processed: {self.total_symbols_processed}")
            logger.info(f"📊 Total bars stored: {self.total_bars_stored}")
            logger.info(f"📊 Total errors: {self.total_errors}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error in backfill run: {e}", exc_info=True)
            self.total_errors += 1

    async def _get_symbols_needing_backfill(self) -> List[Dict]:
        """
        Get list of symbols that need historical data backfilling

        Returns:
            List of dicts with symbol info and data gap details
        """
        try:
            async with self.db_session_factory() as db:
                # Get all symbols from active algorithms
                result = await db.execute(text("""
                    WITH active_symbols AS (
                        SELECT DISTINCT unnest(stock_universe->'symbols') as symbol
                        FROM trading_algorithms
                        WHERE status = 'active'
                        AND stock_universe->>'type' = 'specific'
                    )
                    SELECT
                        as_sym.symbol,
                        sm.earliest_data_date,
                        sm.latest_data_date,
                        sm.total_bars_stored
                    FROM active_symbols as_sym
                    LEFT JOIN symbol_metadata sm ON as_sym.symbol = sm.symbol
                    ORDER BY sm.total_bars_stored ASC NULLS FIRST
                """))

                symbols = result.fetchall()

                symbols_needing_backfill = []
                target_start_date = date.today() - timedelta(days=self.backfill_days)

                for row in symbols:
                    symbol = row.symbol
                    if isinstance(symbol, str) and symbol.startswith('"'):
                        symbol = symbol.strip('"')

                    earliest_date = row.earliest_data_date
                    latest_date = row.latest_data_date
                    total_bars = row.total_bars_stored or 0

                    needs_backfill = False
                    reason = ""

                    if earliest_date is None:
                        # No data at all
                        needs_backfill = True
                        reason = "no_data"
                        start_date = target_start_date
                        end_date = date.today()
                    elif earliest_date > target_start_date:
                        # Incomplete backfill
                        needs_backfill = True
                        reason = "incomplete_backfill"
                        start_date = target_start_date
                        end_date = earliest_date - timedelta(days=1)
                    elif latest_date and latest_date < date.today() - timedelta(days=1):
                        # Gap in recent data
                        needs_backfill = True
                        reason = "recent_gap"
                        start_date = latest_date + timedelta(days=1)
                        end_date = date.today()
                    else:
                        # Data is up to date
                        continue

                    if needs_backfill:
                        symbols_needing_backfill.append({
                            'symbol': symbol,
                            'reason': reason,
                            'start_date': start_date,
                            'end_date': end_date,
                            'current_bars': total_bars
                        })

                logger.info(f"Found {len(symbols_needing_backfill)} symbols needing backfill")
                return symbols_needing_backfill

        except Exception as e:
            logger.error(f"Error getting symbols for backfill: {e}")
            return []

    async def _backfill_symbol(self, symbol_info: Dict) -> bool:
        """
        Backfill historical data for a single symbol

        Args:
            symbol_info: Dict with symbol, start_date, end_date, reason

        Returns:
            True if successful
        """
        symbol = symbol_info['symbol']
        start_date = symbol_info['start_date']
        end_date = symbol_info['end_date']
        reason = symbol_info['reason']

        try:
            logger.info(
                f"📥 Backfilling {symbol}: {start_date} to {end_date} "
                f"(reason: {reason})"
            )

            # Fetch data from Yahoo Finance (free, no rate limits)
            provider = self.data_provider_factory.get_provider('yahoo')

            historical_data = await provider.get_historical_data(
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date,
                region='US'  # Can be made configurable
            )

            if symbol not in historical_data:
                logger.warning(f"No data returned for {symbol}")
                return False

            df = historical_data[symbol]
            bars = df.to_dict('records')

            if not bars:
                logger.warning(f"Empty dataset for {symbol}")
                return False

            # Store in database
            stored_count = await self._store_bars_to_database(symbol, '1day', bars)

            # Optionally cache recent bars in Redis
            if self.cache_service and len(bars) > 0:
                recent_bars = bars[-500:]  # Cache last 500 bars
                await self.cache_service.set_bars(symbol, '1day', recent_bars)

            self.total_symbols_processed += 1
            self.total_bars_stored += stored_count

            logger.info(
                f"✅ Backfilled {symbol}: {stored_count} bars stored "
                f"({start_date} to {end_date})"
            )

            return True

        except Exception as e:
            logger.error(f"Error backfilling {symbol}: {e}")
            self.total_errors += 1
            return False

    async def _store_bars_to_database(
        self,
        symbol: str,
        timeframe: str,
        bars: List[Dict]
    ) -> int:
        """
        Store bars to database

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            bars: List of OHLCV bar dicts

        Returns:
            Number of bars stored
        """
        if not bars:
            return 0

        try:
            async with self.db_session_factory() as db:
                values = []
                for bar in bars:
                    # Parse timestamp
                    timestamp = bar.get('date') or bar.get('timestamp')
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            timestamp = datetime.utcnow()
                    elif isinstance(timestamp, date) and not isinstance(timestamp, datetime):
                        timestamp = datetime.combine(timestamp, datetime.min.time())

                    values.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': timestamp,
                        'open': float(bar.get('open', 0)),
                        'high': float(bar.get('high', 0)),
                        'low': float(bar.get('low', 0)),
                        'close': float(bar.get('close', 0)),
                        'volume': int(bar.get('volume', 0)),
                        'vwap': float(bar['vwap']) if 'vwap' in bar and bar['vwap'] else None,
                        'trade_count': int(bar['trade_count']) if 'trade_count' in bar else None
                    })

                # Batch insert
                if values:
                    # Use INSERT ... ON CONFLICT DO NOTHING for idempotency
                    await db.execute(text("""
                        INSERT INTO market_data_bars
                        (symbol, timeframe, timestamp, open, high, low, close, volume, vwap, trade_count)
                        VALUES (:symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :vwap, :trade_count)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
                    """), values)

                    await db.commit()
                    return len(values)

                return 0

        except Exception as e:
            logger.error(f"Failed to store bars to database for {symbol}: {e}")
            return 0

    async def backfill_specific_symbol(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Manually trigger backfill for a specific symbol
        Useful for on-demand backfilling

        Args:
            symbol: Stock symbol
            start_date: Optional start date (default: 2 years ago)
            end_date: Optional end date (default: today)

        Returns:
            Dict with results
        """
        if not start_date:
            start_date = date.today() - timedelta(days=self.backfill_days)
        if not end_date:
            end_date = date.today()

        symbol_info = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'reason': 'manual'
        }

        success = await self._backfill_symbol(symbol_info)

        return {
            'success': success,
            'symbol': symbol,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_bars_stored': self.total_bars_stored
        }

    def get_stats(self) -> Dict:
        """Get backfill service statistics"""
        return {
            'running': self._running,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_duration_seconds': self.last_run_duration,
            'total_symbols_processed': self.total_symbols_processed,
            'total_bars_stored': self.total_bars_stored,
            'total_errors': self.total_errors,
            'backfill_days': self.backfill_days,
            'run_hour': self.run_hour,
            'max_symbols_per_run': self.max_symbols_per_run
        }


# Singleton instance
_backfill_service: Optional[HistoricalDataBackfillService] = None


async def get_backfill_service(
    db_session_factory=None,
    cache_service: Optional[RedisCacheService] = None,
    **kwargs
) -> HistoricalDataBackfillService:
    """
    Get or create HistoricalDataBackfillService singleton

    Args:
        db_session_factory: Database session factory (required on first call)
        cache_service: Optional Redis cache service
        **kwargs: Additional configuration options

    Returns:
        HistoricalDataBackfillService instance
    """
    global _backfill_service

    if _backfill_service is None:
        if db_session_factory is None:
            raise ValueError("db_session_factory required for first initialization")

        _backfill_service = HistoricalDataBackfillService(
            db_session_factory=db_session_factory,
            cache_service=cache_service,
            **kwargs
        )

    return _backfill_service


async def start_backfill_service(
    db_session_factory=None,
    cache_service: Optional[RedisCacheService] = None,
    **kwargs
):
    """
    Start the historical data backfill service

    Args:
        db_session_factory: Database session factory
        cache_service: Optional Redis cache service
        **kwargs: Additional configuration options
    """
    service = await get_backfill_service(
        db_session_factory=db_session_factory,
        cache_service=cache_service,
        **kwargs
    )
    await service.start()


async def stop_backfill_service():
    """Stop the historical data backfill service"""
    global _backfill_service
    if _backfill_service:
        await _backfill_service.stop()
        _backfill_service = None
