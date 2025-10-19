-- =====================================================
-- Market Data Tables
-- Historical OHLCV bars and technical indicators storage
-- =====================================================

-- Enable TimescaleDB extension for time-series optimization
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- =====================================================
-- OHLCV Bars Table
-- Stores historical price and volume data for all timeframes
-- =====================================================
CREATE TABLE IF NOT EXISTS market_data_bars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1min', '5min', '15min', '1hour', '1day'
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap NUMERIC(12, 4),              -- Volume Weighted Average Price
    trade_count INTEGER,               -- Number of trades in this bar
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure no duplicate bars for same symbol/timeframe/timestamp
    UNIQUE(symbol, timeframe, timestamp)
);

-- Convert to TimescaleDB hypertable for time-series optimization
-- This enables automatic partitioning by time and compression
SELECT create_hypertable(
    'market_data_bars',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 week'
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_bars_symbol_timeframe
    ON market_data_bars(symbol, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bars_timestamp
    ON market_data_bars(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bars_symbol
    ON market_data_bars(symbol);

-- Enable compression for old data (compress data older than 7 days)
ALTER TABLE market_data_bars SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,timeframe'
);

SELECT add_compression_policy(
    'market_data_bars',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add retention policy to automatically drop data older than 2 years
SELECT add_retention_policy(
    'market_data_bars',
    INTERVAL '2 years',
    if_not_exists => TRUE
);

-- =====================================================
-- Technical Indicators Table
-- Stores pre-calculated technical indicators
-- =====================================================
CREATE TABLE IF NOT EXISTS market_data_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,  -- 'rsi_14', 'sma_20', 'ema_50', 'macd_12_26_9', etc.
    indicator_value NUMERIC(16, 6) NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1day',  -- Base timeframe for calculation
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure no duplicate indicators for same symbol/timestamp/name
    UNIQUE(symbol, timestamp, indicator_name)
);

-- Convert to hypertable
SELECT create_hypertable(
    'market_data_indicators',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 week'
);

-- Indexes for fast indicator queries
CREATE INDEX IF NOT EXISTS idx_indicators_symbol
    ON market_data_indicators(symbol, indicator_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_indicators_timestamp
    ON market_data_indicators(timestamp DESC);

-- Enable compression
ALTER TABLE market_data_indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,indicator_name'
);

SELECT add_compression_policy(
    'market_data_indicators',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Retention policy
SELECT add_retention_policy(
    'market_data_indicators',
    INTERVAL '2 years',
    if_not_exists => TRUE
);

-- =====================================================
-- Data Source Tracking Table
-- Tracks where data was sourced from and when
-- =====================================================
CREATE TABLE IF NOT EXISTS market_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    source VARCHAR(20) NOT NULL,  -- 'alpaca', 'yahoo', 'manual'
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    bars_count INTEGER NOT NULL,
    fetch_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Track fetch history
    UNIQUE(symbol, timeframe, source, start_date, end_date, created_at)
);

CREATE INDEX IF NOT EXISTS idx_sources_symbol
    ON market_data_sources(symbol, timeframe);

CREATE INDEX IF NOT EXISTS idx_sources_created_at
    ON market_data_sources(created_at DESC);

-- =====================================================
-- Symbol Metadata Table
-- Stores symbol information and data availability
-- =====================================================
CREATE TABLE IF NOT EXISTS symbol_metadata (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255),
    exchange VARCHAR(50),
    asset_type VARCHAR(20),  -- 'stock', 'etf', 'crypto', 'forex'
    region VARCHAR(10),      -- 'US', 'IN', 'GB'
    currency VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,

    -- Data availability tracking
    earliest_data_date TIMESTAMPTZ,
    latest_data_date TIMESTAMPTZ,
    total_bars_stored BIGINT DEFAULT 0,
    last_fetched_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_symbol_metadata_active
    ON symbol_metadata(is_active, region);

CREATE INDEX IF NOT EXISTS idx_symbol_metadata_updated
    ON symbol_metadata(updated_at DESC);

-- =====================================================
-- Continuous Aggregates (TimescaleDB Materialized Views)
-- Pre-aggregate data for faster queries
-- =====================================================

-- Daily aggregated bars from 1-minute data
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_bars_daily
WITH (timescaledb.continuous) AS
SELECT
    symbol,
    time_bucket('1 day', timestamp) AS day,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume,
    avg(vwap) AS vwap
FROM market_data_bars
WHERE timeframe = '1min'
GROUP BY symbol, time_bucket('1 day', timestamp);

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy(
    'market_data_bars_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to get latest bar for a symbol
CREATE OR REPLACE FUNCTION get_latest_bar(
    p_symbol VARCHAR(20),
    p_timeframe VARCHAR(10) DEFAULT '1min'
)
RETURNS TABLE (
    timestamp TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.timestamp,
        b.open,
        b.high,
        b.low,
        b.close,
        b.volume
    FROM market_data_bars b
    WHERE b.symbol = p_symbol
    AND b.timeframe = p_timeframe
    ORDER BY b.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get data availability for a symbol
CREATE OR REPLACE FUNCTION get_data_availability(p_symbol VARCHAR(20))
RETURNS TABLE (
    timeframe VARCHAR(10),
    earliest_date TIMESTAMPTZ,
    latest_date TIMESTAMPTZ,
    total_bars BIGINT,
    coverage_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.timeframe,
        MIN(b.timestamp) AS earliest_date,
        MAX(b.timestamp) AS latest_date,
        COUNT(*) AS total_bars,
        EXTRACT(DAY FROM MAX(b.timestamp) - MIN(b.timestamp))::INTEGER AS coverage_days
    FROM market_data_bars b
    WHERE b.symbol = p_symbol
    GROUP BY b.timeframe
    ORDER BY b.timeframe;
END;
$$ LANGUAGE plpgsql;

-- Function to update symbol metadata
CREATE OR REPLACE FUNCTION update_symbol_metadata()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO symbol_metadata (
        symbol,
        earliest_data_date,
        latest_data_date,
        total_bars_stored,
        last_fetched_at
    )
    VALUES (
        NEW.symbol,
        NEW.timestamp,
        NEW.timestamp,
        1,
        NOW()
    )
    ON CONFLICT (symbol) DO UPDATE SET
        earliest_data_date = LEAST(symbol_metadata.earliest_data_date, NEW.timestamp),
        latest_data_date = GREATEST(symbol_metadata.latest_data_date, NEW.timestamp),
        total_bars_stored = symbol_metadata.total_bars_stored + 1,
        last_fetched_at = NOW(),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update symbol metadata when bars are inserted
CREATE TRIGGER trg_update_symbol_metadata
AFTER INSERT ON market_data_bars
FOR EACH ROW
EXECUTE FUNCTION update_symbol_metadata();

-- =====================================================
-- Comments for documentation
-- =====================================================
COMMENT ON TABLE market_data_bars IS 'Historical OHLCV price and volume data for all symbols and timeframes';
COMMENT ON TABLE market_data_indicators IS 'Pre-calculated technical indicators (RSI, MACD, SMA, etc.)';
COMMENT ON TABLE market_data_sources IS 'Tracks data source and fetch history for auditing';
COMMENT ON TABLE symbol_metadata IS 'Symbol information and data availability tracking';
COMMENT ON COLUMN market_data_bars.vwap IS 'Volume Weighted Average Price';
COMMENT ON COLUMN market_data_bars.trade_count IS 'Number of trades within this time period';
