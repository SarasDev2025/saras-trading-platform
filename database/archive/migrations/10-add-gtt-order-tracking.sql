-- Migration 10: Add GTT Order Tracking Support
-- Adds table and functionality for tracking Zerodha GTT orders

-- Create GTT orders tracking table
CREATE TABLE IF NOT EXISTS gtt_orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    broker_connection_id UUID NOT NULL REFERENCES user_broker_connections(id) ON DELETE CASCADE,
    trigger_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(15,4) NOT NULL,
    trigger_price DECIMAL(15,4) NOT NULL,
    limit_price DECIMAL(15,4),
    trigger_type VARCHAR(20) DEFAULT 'single' CHECK (trigger_type IN ('single', 'two-leg')),
    product VARCHAR(10) DEFAULT 'CNC' CHECK (product IN ('CNC', 'MIS', 'NRML', 'CO', 'BO')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'triggered', 'cancelled', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    triggered_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    order_id VARCHAR(100), -- Order ID when GTT is triggered
    execution_details JSONB, -- Store execution details when triggered
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create basket orders tracking table
CREATE TABLE IF NOT EXISTS basket_orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    broker_connection_id UUID NOT NULL REFERENCES user_broker_connections(id) ON DELETE CASCADE,
    basket_id VARCHAR(100) NOT NULL,
    orders_placed INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'partial', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    basket_details JSONB, -- Store order details and results
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create OCO orders tracking table (One-Cancels-Other)
CREATE TABLE IF NOT EXISTS oco_orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    broker_connection_id UUID NOT NULL REFERENCES user_broker_connections(id) ON DELETE CASCADE,
    trigger_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(15,4) NOT NULL,
    target_price DECIMAL(15,4) NOT NULL,
    stop_loss_price DECIMAL(15,4) NOT NULL,
    product VARCHAR(10) DEFAULT 'CNC',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'target_hit', 'stop_hit', 'cancelled', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    triggered_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    executed_price DECIMAL(15,4), -- Actual execution price
    executed_side VARCHAR(20), -- Which leg was executed (target/stop)
    order_id VARCHAR(100), -- Order ID when OCO is triggered
    execution_details JSONB,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_gtt_orders_broker_connection ON gtt_orders(broker_connection_id);
CREATE INDEX IF NOT EXISTS idx_gtt_orders_status ON gtt_orders(status, is_active);
CREATE INDEX IF NOT EXISTS idx_gtt_orders_symbol ON gtt_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_gtt_orders_trigger_id ON gtt_orders(trigger_id);
CREATE INDEX IF NOT EXISTS idx_gtt_orders_created_at ON gtt_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_gtt_orders_expires_at ON gtt_orders(expires_at);

CREATE INDEX IF NOT EXISTS idx_basket_orders_broker_connection ON basket_orders(broker_connection_id);
CREATE INDEX IF NOT EXISTS idx_basket_orders_status ON basket_orders(status, is_active);
CREATE INDEX IF NOT EXISTS idx_basket_orders_basket_id ON basket_orders(basket_id);
CREATE INDEX IF NOT EXISTS idx_basket_orders_created_at ON basket_orders(created_at);

CREATE INDEX IF NOT EXISTS idx_oco_orders_broker_connection ON oco_orders(broker_connection_id);
CREATE INDEX IF NOT EXISTS idx_oco_orders_status ON oco_orders(status, is_active);
CREATE INDEX IF NOT EXISTS idx_oco_orders_symbol ON oco_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_oco_orders_trigger_id ON oco_orders(trigger_id);
CREATE INDEX IF NOT EXISTS idx_oco_orders_created_at ON oco_orders(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at
CREATE TRIGGER update_gtt_orders_updated_at BEFORE UPDATE ON gtt_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_basket_orders_updated_at BEFORE UPDATE ON basket_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oco_orders_updated_at BEFORE UPDATE ON oco_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE gtt_orders IS 'Tracks Zerodha GTT (Good Till Triggered) orders with up to 1-year validity';
COMMENT ON COLUMN gtt_orders.trigger_id IS 'Zerodha GTT trigger ID from Kite API';
COMMENT ON COLUMN gtt_orders.trigger_type IS 'single for basic GTT, two-leg for OCO orders';
COMMENT ON COLUMN gtt_orders.product IS 'Trading product: CNC (delivery), MIS (intraday), NRML (normal)';
COMMENT ON COLUMN gtt_orders.execution_details IS 'JSON details when GTT order is triggered and executed';

COMMENT ON TABLE basket_orders IS 'Tracks basket orders (up to 20 orders placed simultaneously)';
COMMENT ON COLUMN basket_orders.basket_details IS 'JSON details of all orders in the basket and their results';

COMMENT ON TABLE oco_orders IS 'Tracks One-Cancels-Other orders using Zerodha GTT two-leg feature';
COMMENT ON COLUMN oco_orders.executed_side IS 'Which order was executed: target_hit or stop_hit';

-- Create view for active GTT orders with user information
CREATE OR REPLACE VIEW active_gtt_orders AS
SELECT
    g.*,
    bc.user_id,
    bc.broker_type,
    u.username,
    u.email
FROM gtt_orders g
JOIN user_broker_connections bc ON g.broker_connection_id = bc.id
JOIN users u ON bc.user_id = u.id
WHERE g.is_active = true AND g.status = 'active';

-- Create view for GTT order monitoring summary
CREATE OR REPLACE VIEW gtt_order_summary AS
SELECT
    bc.user_id,
    bc.broker_type,
    COUNT(*) as total_gtt_orders,
    COUNT(*) FILTER (WHERE g.status = 'active') as active_orders,
    COUNT(*) FILTER (WHERE g.status = 'triggered') as triggered_orders,
    COUNT(*) FILTER (WHERE g.status = 'cancelled') as cancelled_orders,
    COUNT(*) FILTER (WHERE g.status = 'expired') as expired_orders,
    AVG(g.trigger_price) as avg_trigger_price,
    SUM(g.quantity * g.trigger_price) as total_trigger_value
FROM gtt_orders g
JOIN user_broker_connections bc ON g.broker_connection_id = bc.id
WHERE g.is_active = true
GROUP BY bc.user_id, bc.broker_type;

COMMENT ON VIEW active_gtt_orders IS 'View of all active GTT orders with user information for monitoring';
COMMENT ON VIEW gtt_order_summary IS 'Summary statistics of GTT orders by user and broker';