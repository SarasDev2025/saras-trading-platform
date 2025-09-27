-- Migration: Add Trade Queue for Time-based Order Aggregation
-- This enables queued execution instead of immediate execution

-- Trade Queue Table
CREATE TABLE IF NOT EXISTS trade_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_order_id UUID NOT NULL, -- References smallcase_execution_orders.id
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity DECIMAL(15, 6) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (priority IN ('high', 'normal', 'low')),
    status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'batched', 'executing', 'executed', 'failed', 'cancelled')),
    broker_type VARCHAR(20) NOT NULL,

    -- Timing fields
    queued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    scheduled_execution_at TIMESTAMP WITH TIME ZONE NOT NULL,
    execution_started_at TIMESTAMP WITH TIME ZONE,
    execution_completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- Batch tracking
    batch_id VARCHAR(100),

    -- Results and metadata
    execution_result JSONB,
    error_message TEXT,
    cancellation_reason TEXT,
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for efficient querying
    INDEX idx_trade_queue_status_scheduled (status, scheduled_execution_at),
    INDEX idx_trade_queue_user_symbol (user_id, symbol),
    INDEX idx_trade_queue_batch (batch_id),
    INDEX idx_trade_queue_broker_symbol (broker_type, symbol, side)
);

-- Trade Queue Aggregation View
-- This view shows pending aggregations by symbol and execution window
CREATE OR REPLACE VIEW trade_queue_aggregation_view AS
SELECT
    scheduled_execution_at,
    broker_type,
    symbol,
    side,
    COUNT(*) as order_count,
    SUM(quantity) as total_quantity,
    AVG(quantity) as avg_quantity,
    MIN(queued_at) as earliest_queue_time,
    MAX(queued_at) as latest_queue_time,
    STRING_AGG(DISTINCT priority, ',') as priorities
FROM trade_queue
WHERE status = 'queued'
GROUP BY scheduled_execution_at, broker_type, symbol, side
ORDER BY scheduled_execution_at, symbol;

-- Trade Queue Statistics View
-- This view provides real-time statistics about queue performance
CREATE OR REPLACE VIEW trade_queue_stats_view AS
SELECT
    status,
    COUNT(*) as count,
    MIN(queued_at) as oldest_order,
    MAX(queued_at) as newest_order,
    AVG(EXTRACT(EPOCH FROM (execution_completed_at - queued_at))) as avg_processing_time_seconds
FROM trade_queue
GROUP BY status;

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_trade_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trade_queue_updated_at_trigger
    BEFORE UPDATE ON trade_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_trade_queue_updated_at();

-- Function to get next batch execution window
CREATE OR REPLACE FUNCTION get_next_batch_window(interval_minutes INTEGER DEFAULT 5)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    current_time TIMESTAMP WITH TIME ZONE := NOW();
    current_minute INTEGER;
    next_interval INTEGER;
    next_window TIMESTAMP WITH TIME ZONE;
BEGIN
    current_minute := EXTRACT(MINUTE FROM current_time);
    next_interval := ((current_minute / interval_minutes) + 1) * interval_minutes;

    IF next_interval >= 60 THEN
        next_window := DATE_TRUNC('hour', current_time) + INTERVAL '1 hour';
    ELSE
        next_window := DATE_TRUNC('hour', current_time) + (next_interval || ' minutes')::INTERVAL;
    END IF;

    RETURN next_window;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (optional)
-- INSERT INTO trade_queue (
--     execution_order_id, user_id, symbol, side, quantity, broker_type, scheduled_execution_at
-- ) VALUES (
--     gen_random_uuid(),
--     'b4d57aec-44ee-42c2-a823-739087343bd1'::UUID,
--     'AAPL',
--     'buy',
--     100.00,
--     'zerodha',
--     get_next_batch_window(5)
-- );

COMMENT ON TABLE trade_queue IS 'Queue for time-based order aggregation and batch execution';
COMMENT ON COLUMN trade_queue.scheduled_execution_at IS 'When this order should be executed (batch window)';
COMMENT ON COLUMN trade_queue.batch_id IS 'Groups orders that were executed together';
COMMENT ON COLUMN trade_queue.priority IS 'Order priority: high orders execute first within batch';
COMMENT ON VIEW trade_queue_aggregation_view IS 'Shows pending orders grouped for aggregation';
COMMENT ON VIEW trade_queue_stats_view IS 'Real-time queue performance statistics';