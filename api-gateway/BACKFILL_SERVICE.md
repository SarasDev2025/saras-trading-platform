# Historical Data Backfill Service

## Overview

The Historical Data Backfill Service gradually backfills 2 years of historical market data for all symbols used by active trading algorithms. This ensures your database has complete historical data without overwhelming broker APIs.

## Status

**Currently: DISABLED (not integrated into main.py)**

The service is fully implemented but not enabled by default to give you control over when backfilling begins.

## Features

- **Gradual Backfill**: Processes symbols in batches to avoid API rate limits
- **Gap Detection**: Automatically identifies and fills missing data
- **Smart Scheduling**: Runs nightly at 1 AM (configurable) after market close
- **Progress Tracking**: Monitors bars stored, symbols processed, and errors
- **Error Recovery**: Handles failures gracefully and retries on next run
- **Idempotent**: Won't duplicate data (uses `ON CONFLICT DO NOTHING`)

## How It Works

### 1. Symbol Discovery
Queries database for symbols used by active algorithms that need backfilling:
- **No data**: Backfills full 2 years
- **Incomplete backfill**: Fills gap to 2 years
- **Recent gap**: Updates missing recent data

### 2. Batch Processing
- Processes up to 50 symbols per run (configurable)
- Fetches in batches of 10 to avoid rate limits
- 5-second delay between batches

### 3. Data Storage
- Stores OHLCV bars in `market_data_bars` table
- Updates `symbol_metadata` automatically (via trigger)
- Optionally caches recent 500 bars in Redis

## Configuration

Default settings in `historical_data_backfill.py`:

```python
backfill_days = 730          # 2 years of history
run_hour = 1                 # Run at 1 AM daily
max_symbols_per_run = 50     # Process 50 symbols per run
batch_size = 10              # Fetch 10 symbols in parallel
```

## How to Enable

### Option 1: Enable in Main App Startup

Edit `/Users/lalitchandivade/Projects/saras-trading-platform/api-gateway/main.py`:

**1. Add import at top:**
```python
from services.historical_data_backfill import start_backfill_service, stop_backfill_service
```

**2. In `_start_background_tasks()` function, add:**
```python
# Start historical data backfill service (runs nightly at 1 AM)
await start_backfill_service(
    db_session_factory=async_session,
    cache_service=cache_service,
    backfill_days=730,        # 2 years
    run_hour=1,               # 1 AM
    max_symbols_per_run=50
)
logger.info("✅ Historical data backfill service started")
```

**3. In `_stop_background_tasks()` function, add:**
```python
# Stop backfill service
await stop_backfill_service()
logger.info("✅ Historical data backfill service stopped")
```

**4. Restart services:**
```bash
docker-compose restart api-gateway
```

### Option 2: Manual On-Demand Backfill

You can trigger backfill for specific symbols without enabling the nightly service.

**Create a management script (`scripts/backfill_symbol.py`):**

```python
import asyncio
from services.historical_data_backfill import get_backfill_service
from config.database import async_session

async def backfill_symbol(symbol: str):
    service = await get_backfill_service(db_session_factory=async_session)
    result = await service.backfill_specific_symbol(symbol)
    print(f"Backfill result: {result}")

# Usage
asyncio.run(backfill_symbol('AAPL'))
```

**Or use API endpoint (add to routers):**

```python
@router.post("/admin/backfill/{symbol}")
async def backfill_symbol_endpoint(symbol: str):
    from services.historical_data_backfill import get_backfill_service
    service = await get_backfill_service()
    result = await service.backfill_specific_symbol(symbol)
    return result
```

## Monitoring

### Check Backfill Statistics

```python
from services.historical_data_backfill import get_backfill_service

service = await get_backfill_service()
stats = service.get_stats()

print(f"Running: {stats['running']}")
print(f"Last run: {stats['last_run_time']}")
print(f"Symbols processed: {stats['total_symbols_processed']}")
print(f"Bars stored: {stats['total_bars_stored']}")
print(f"Errors: {stats['total_errors']}")
```

### Check Database Progress

```sql
-- Symbols with most data
SELECT symbol, total_bars_stored, earliest_data_date, latest_data_date
FROM symbol_metadata
ORDER BY total_bars_stored DESC
LIMIT 10;

-- Total bars in database
SELECT COUNT(*) as total_bars, COUNT(DISTINCT symbol) as total_symbols
FROM market_data_bars;

-- Data coverage by symbol
SELECT
    symbol,
    COUNT(*) as bars,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    EXTRACT(DAY FROM MAX(timestamp) - MIN(timestamp)) as coverage_days
FROM market_data_bars
GROUP BY symbol
ORDER BY bars DESC;
```

### Check Logs

```bash
# View backfill service logs
docker-compose logs api-gateway | grep -i backfill

# Monitor real-time
docker-compose logs -f api-gateway | grep -i backfill
```

## Expected Performance

### First Run (50 symbols, 2 years each)
- **Duration**: ~5-10 minutes
- **API Calls**: 50 (one per symbol)
- **Bars Stored**: ~25,000 bars (500 trading days × 50 symbols)
- **Database Growth**: ~2 MB

### Steady State (gap filling only)
- **Duration**: ~1-2 minutes
- **API Calls**: 10-20 (only symbols with gaps)
- **Bars Stored**: ~50-100 bars
- **Database Growth**: ~10 KB

### Full Backfill (1000 symbols, 2 years)
- **Total Runs**: 20 runs (50 symbols per run)
- **Total Duration**: 20 nights (one run per night)
- **Total Bars**: ~500,000 bars
- **Database Size**: ~50 MB (without indexes)

## Cost Analysis

### API Usage
- **Provider**: Yahoo Finance (FREE, no API key required)
- **Rate Limits**: ~2000 requests/hour (soft limit)
- **Our Usage**: 50 requests/night = **Well within limits**
- **Cost**: $0 ✅

### Database Storage
- **Per Symbol (2 years)**: ~500 bars × 50 bytes = 25 KB
- **1000 Symbols**: 25 MB
- **10,000 Symbols**: 250 MB
- **PostgreSQL RDS**: Included in any tier ✅

## Troubleshooting

### Service Not Running
Check if enabled in main.py:
```bash
docker-compose logs api-gateway | grep "backfill service started"
```

### No Data Being Backfilled
1. Check if there are active algorithms with symbols:
   ```sql
   SELECT id, name, stock_universe FROM trading_algorithms WHERE status = 'active';
   ```

2. Check if symbols are detected:
   ```bash
   docker-compose logs api-gateway | grep "Found.*symbols needing backfill"
   ```

### Errors During Backfill
Check logs for specific errors:
```bash
docker-compose logs api-gateway | grep -A 5 "Error backfilling"
```

Common issues:
- **Yahoo Finance rate limit**: Wait 1 hour, service will retry
- **Invalid symbol**: Check stock_universe in algorithm
- **Database connection**: Check PostgreSQL is running

## Advanced Configuration

### Change Run Schedule

**Run twice daily (1 AM and 1 PM):**
Modify the service to run more frequently:

```python
# In historical_data_backfill.py, change _run_backfill_loop():
run_hours = [1, 13]  # 1 AM and 1 PM

for hour in run_hours:
    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    # ... schedule logic
```

### Increase Backfill Speed

**Process more symbols per run:**
```python
await start_backfill_service(
    db_session_factory=async_session,
    cache_service=cache_service,
    max_symbols_per_run=100,  # Increase from 50
    batch_size=20             # Increase from 10
)
```

**Warning**: Higher values may hit Yahoo Finance rate limits.

### Change Backfill Depth

**Backfill 5 years instead of 2:**
```python
await start_backfill_service(
    db_session_factory=async_session,
    cache_service=cache_service,
    backfill_days=1825  # 5 years
)
```

## Security Considerations

- ✅ No API keys required (Yahoo Finance is public)
- ✅ Read-only access to trading_algorithms table
- ✅ Idempotent operations (safe to run multiple times)
- ✅ No external network access except Yahoo Finance
- ✅ Automatic error recovery

## Maintenance

### Monthly Tasks
1. Monitor database size: `SELECT pg_size_pretty(pg_database_size('trading_dev'));`
2. Check backfill statistics: Review total_bars_stored growth
3. Verify no symbols are stuck: Check symbols with errors

### Yearly Tasks
1. Review backfill_days configuration (still need 2 years?)
2. Clean up old data if needed (use retention policies)
3. Optimize database with `VACUUM ANALYZE market_data_bars;`

## Rollback / Disable

### Temporarily Disable
Set max_symbols_per_run to 0 (processes nothing):
```python
await start_backfill_service(max_symbols_per_run=0)
```

### Permanently Disable
Remove the startup code from main.py and restart:
```bash
# Comment out or remove the start_backfill_service() call
docker-compose restart api-gateway
```

### Remove All Backfilled Data
```sql
-- WARNING: This deletes all historical data!
TRUNCATE market_data_bars;
TRUNCATE market_data_indicators;
TRUNCATE symbol_metadata;
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs api-gateway | grep backfill`
2. Review stats: `service.get_stats()`
3. Check database: Query `market_data_bars` and `symbol_metadata`
4. File issue with logs attached

## References

- Main service: `/api-gateway/services/historical_data_backfill.py`
- Database schema: `/database/init/schema/10-market-data-tables.sql`
- Data aggregator: `/api-gateway/services/data_aggregator_service.py`
- Algorithm engine: `/api-gateway/services/algorithm_engine.py`
