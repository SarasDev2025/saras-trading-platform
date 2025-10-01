-- Migration 07: Add Order Monitoring Support
-- Adds table for tracking order execution status and next-day checking

-- Create order_monitoring table
CREATE TABLE IF NOT EXISTS order_monitoring (
    id SERIAL PRIMARY KEY,
    broker_connection_id UUID NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(50) NOT NULL,
    quantity DECIMAL(15, 8) NOT NULL,
    filled_quantity DECIMAL(15, 8) DEFAULT 0,
    fill_percentage DECIMAL(5, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    expected_execution_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checked_at TIMESTAMP NULL,

    -- Foreign key constraint
    FOREIGN KEY (broker_connection_id) REFERENCES user_broker_connections(id) ON DELETE CASCADE,

    -- Unique constraint to prevent duplicate monitoring
    UNIQUE(broker_connection_id, order_id)
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_order_monitoring_broker_connection
    ON order_monitoring(broker_connection_id);

CREATE INDEX IF NOT EXISTS idx_order_monitoring_expected_date
    ON order_monitoring(expected_execution_date);

CREATE INDEX IF NOT EXISTS idx_order_monitoring_status
    ON order_monitoring(status);

CREATE INDEX IF NOT EXISTS idx_order_monitoring_symbol
    ON order_monitoring(symbol);

CREATE INDEX IF NOT EXISTS idx_order_monitoring_created_at
    ON order_monitoring(created_at);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_order_monitoring_status_date
    ON order_monitoring(status, expected_execution_date);

-- Add comments for documentation
COMMENT ON TABLE order_monitoring IS 'Tracks order execution status for next-day monitoring';
COMMENT ON COLUMN order_monitoring.broker_connection_id IS 'Reference to user broker connection';
COMMENT ON COLUMN order_monitoring.order_id IS 'Broker-specific order identifier';
COMMENT ON COLUMN order_monitoring.symbol IS 'Stock/security symbol';
COMMENT ON COLUMN order_monitoring.order_type IS 'Type of order (market, limit, stop, etc.)';
COMMENT ON COLUMN order_monitoring.quantity IS 'Total order quantity';
COMMENT ON COLUMN order_monitoring.filled_quantity IS 'Quantity filled/executed';
COMMENT ON COLUMN order_monitoring.fill_percentage IS 'Percentage of order filled (0-100)';
COMMENT ON COLUMN order_monitoring.status IS 'Order status (pending, filled, cancelled, etc.)';
COMMENT ON COLUMN order_monitoring.expected_execution_date IS 'Expected trading day for execution';
COMMENT ON COLUMN order_monitoring.checked_at IS 'Last time order status was checked';