-- Trading Database Schema
-- Optimized for high-performance trading operations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS risk;

-- Set search path
SET search_path TO trading, market_data, risk, public;

-- Trading pairs table
CREATE TABLE trading.trading_pairs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    base_asset VARCHAR(10) NOT NULL,
    quote_asset VARCHAR(10) NOT NULL,
    min_quantity DECIMAL(20,8) NOT NULL,
    max_quantity DECIMAL(20,8) NOT NULL,
    quantity_precision INTEGER NOT NULL DEFAULT 8,
    price_precision INTEGER NOT NULL DEFAULT 8,
    min_notional DECIMAL(20,8) NOT NULL DEFAULT 0,
    maker_fee DECIMAL(5,4) NOT NULL DEFAULT 0.001,
    taker_fee DECIMAL(5,4) NOT NULL DEFAULT 0.001,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Orders table (partitioned by date for performance)
CREATE TABLE trading.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    trading_pair_id INTEGER NOT NULL REFERENCES trading.trading_pairs(id),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')),
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(20,8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20,8) CHECK (price > 0),
    stop_price DECIMAL(20,8) CHECK (stop_price > 0),
    filled_quantity DECIMAL(20,8) NOT NULL DEFAULT 0,
    remaining_quantity DECIMAL(20,8) NOT NULL,
    average_price DECIMAL(20,8),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'OPEN', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'REJECTED')),
    time_in_force VARCHAR(10) NOT NULL DEFAULT 'GTC' CHECK (time_in_force IN ('GTC', 'IOC', 'FOK')),
    client_order_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Ensure remaining quantity is consistent
    CONSTRAINT orders_remaining_qty_check CHECK (remaining_quantity = quantity - filled_quantity),
    
    -- Ensure price is set for limit orders
    CONSTRAINT orders_limit_price_check CHECK (
        (order_type IN ('LIMIT', 'STOP_LIMIT') AND price IS NOT NULL) OR
        (order_type IN ('MARKET', 'STOP'))
    ),
    
    -- Ensure stop price is set for stop orders
    CONSTRAINT orders_stop_price_check CHECK (
        (order_type IN ('STOP', 'STOP_LIMIT') AND stop_price IS NOT NULL) OR
        (order_type IN ('MARKET', 'LIMIT'))
    )
) PARTITION BY RANGE (created_at);

-- Create partitions for orders (monthly partitions)
CREATE TABLE trading.orders_2025_01 PARTITION OF trading.orders
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE trading.orders_2025_02 PARTITION OF trading.orders
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Add more partitions as needed...

-- Trades table (partitioned by date)
CREATE TABLE trading.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_order_id UUID NOT NULL,
    seller_order_id UUID NOT NULL,
    trading_pair_id INTEGER NOT NULL REFERENCES trading.trading_pairs(id),
    buyer_user_id INTEGER NOT NULL,
    seller_user_id INTEGER NOT NULL,
    quantity DECIMAL(20,8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20,8) NOT NULL CHECK (price > 0),
    buyer_fee DECIMAL(20,8) NOT NULL DEFAULT 0,
    seller_fee DECIMAL(20,8) NOT NULL DEFAULT 0,
    trade_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    sequence_number BIGSERIAL,
    
    -- Foreign key constraints will be added after partition setup
    UNIQUE(sequence_number)
) PARTITION BY RANGE (trade_time);

-- Create partitions for trades
CREATE TABLE trading.trades_2025_01 PARTITION OF trading.trades
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE trading.trades_2025_02 PARTITION OF trading.trades
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- User positions table
CREATE TABLE trading.positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    asset VARCHAR(10) NOT NULL,
    total_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    available_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    locked_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, asset),
    
    -- Ensure balance consistency
    CONSTRAINT positions_balance_check CHECK (total_balance = available_balance + locked_balance),
    CONSTRAINT positions_non_negative_check CHECK (
        total_balance >= 0 AND available_balance >= 0 AND locked_balance >= 0
    )
);

-- Order book snapshots for market data
CREATE TABLE market_data.order_book_snapshots (
    id BIGSERIAL PRIMARY KEY,
    trading_pair_id INTEGER NOT NULL REFERENCES trading.trading_pairs(id),
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (snapshot_time);

-- Create partition for current month
CREATE TABLE market_data.order_book_snapshots_2025_01 PARTITION OF market_data.order_book_snapshots
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- OHLCV candles for different timeframes
CREATE TABLE market_data.candles (
    id BIGSERIAL PRIMARY KEY,
    trading_pair_id INTEGER NOT NULL REFERENCES trading.trading_pairs(id),
    timeframe VARCHAR(10) NOT NULL, -- '1m', '5m', '1h', '1d', etc.
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL DEFAULT 0,
    quote_volume DECIMAL(20,8) NOT NULL DEFAULT 0,
    trade_count INTEGER NOT NULL DEFAULT 0,
    
    UNIQUE(trading_pair_id, timeframe, open_time)
) PARTITION BY RANGE (open_time);

-- Risk management tables
CREATE TABLE risk.user_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    daily_trade_limit DECIMAL(20,8),
    max_open_orders INTEGER DEFAULT 100,
    max_position_size DECIMAL(20,8),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX CONCURRENTLY idx_orders_user_status ON trading.orders(user_id, status) WHERE status IN ('OPEN', 'PARTIALLY_FILLED');
CREATE INDEX CONCURRENTLY idx_orders_trading_pair_side_price ON trading.orders(trading_pair_id, side, price) WHERE status IN ('OPEN', 'PARTIALLY_FILLED');
CREATE INDEX CONCURRENTLY idx_orders_created_at ON trading.orders(created_at);
CREATE INDEX CONCURRENTLY idx_trades_trading_pair_time ON trading.trades(trading_pair_id, trade_time);
CREATE INDEX CONCURRENTLY idx_trades_user_time ON trading.trades(buyer_user_id, trade_time);
CREATE INDEX CONCURRENTLY idx_positions_user_asset ON trading.positions(user_id, asset);

-- BRIN indexes for time-series data (very efficient for large datasets)
CREATE INDEX CONCURRENTLY idx_trades_sequence_brin ON trading.trades USING BRIN(sequence_number);
CREATE INDEX CONCURRENTLY idx_orders_created_brin ON trading.orders USING BRIN(created_at);

-- Functions and triggers for maintaining data consistency
CREATE OR REPLACE FUNCTION update_position_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- This function would handle position updates
    -- Implementation depends on your specific business logic
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_positions_update_timestamp
    BEFORE UPDATE ON trading.positions
    FOR EACH ROW
    EXECUTE FUNCTION update_position_balance();

-- Function to automatically create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    table_name text;
BEGIN
    -- Create partitions for the next 3 months
    FOR i IN 0..2 LOOP
        start_date := date_trunc('month', CURRENT_DATE + interval '1 month' * i);
        end_date := start_date + interval '1 month';
        
        -- Orders partitions
        table_name := 'orders_' || to_char(start_date, 'YYYY_MM');
        EXECUTE format('CREATE TABLE IF NOT EXISTS trading.%I PARTITION OF trading.orders FOR VALUES FROM (%L) TO (%L)',
                      table_name, start_date, end_date);
        
        -- Trades partitions
        table_name := 'trades_' || to_char(start_date, 'YYYY_MM');
        EXECUTE format('CREATE TABLE IF NOT EXISTS trading.%I PARTITION OF trading.trades FOR VALUES FROM (%L) TO (%L)',
                      table_name, start_date, end_date);
                      
        -- Order book partitions
        table_name := 'order_book_snapshots_' || to_char(start_date, 'YYYY_MM');
        EXECUTE format('CREATE TABLE IF NOT EXISTS market_data.%I PARTITION OF market_data.order_book_snapshots FOR VALUES FROM (%L) TO (%L)',
                      table_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create initial data
INSERT INTO trading.trading_pairs (symbol, base_asset, quote_asset, min_quantity, max_quantity, quantity_precision, price_precision, min_notional)
VALUES 
    ('BTCUSD', 'BTC', 'USD', 0.00001, 1000, 8, 2, 10),
    ('ETHUSD', 'ETH', 'USD', 0.001, 10000, 8, 2, 10),
    ('ADAUSD', 'ADA', 'USD', 1, 1000000, 8, 6, 5);

-- Setup row-level security (if needed)
-- ALTER TABLE trading.orders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trading.trades ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trading.positions ENABLE ROW LEVEL SECURITY;