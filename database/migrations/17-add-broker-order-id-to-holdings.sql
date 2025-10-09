-- Migration: Add broker_order_id to portfolio_holdings
-- Purpose: Track actual broker orders for each holding

ALTER TABLE portfolio_holdings
ADD COLUMN IF NOT EXISTS broker_order_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS order_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS order_placed_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN portfolio_holdings.broker_order_id IS 'Order ID from broker API (e.g., Alpaca order ID)';
COMMENT ON COLUMN portfolio_holdings.order_status IS 'Status of broker order: pending, submitted, filled, cancelled, failed';
COMMENT ON COLUMN portfolio_holdings.order_placed_at IS 'Timestamp when order was placed with broker';
