-- Migration 11: Paper Trading Enhancements
-- Add cash impact tracking, paper orders, and virtual money configuration

-- Add cash impact tracking to transactions
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS cash_impact DECIMAL(15, 2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS cash_balance_after DECIMAL(15, 2);

COMMENT ON COLUMN transactions.cash_impact IS 'Cash debit (-) or credit (+) from this transaction';
COMMENT ON COLUMN transactions.cash_balance_after IS 'User cash balance after this transaction';

-- Create paper orders tracking table
CREATE TABLE IF NOT EXISTS paper_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broker_connection_id UUID NOT NULL REFERENCES user_broker_connections(id) ON DELETE CASCADE,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL CHECK (quantity > 0),
    price DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partial', 'cancelled', 'rejected')),
    filled_quantity DECIMAL(15, 4) DEFAULT 0,
    average_fill_price DECIMAL(15, 2),
    broker_type VARCHAR(50) NOT NULL,
    is_paper_trading BOOLEAN DEFAULT true,
    order_response JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    filled_at TIMESTAMP
);

CREATE INDEX idx_paper_orders_user ON paper_orders(user_id, created_at DESC);
CREATE INDEX idx_paper_orders_status ON paper_orders(status, broker_type);
CREATE INDEX idx_paper_orders_symbol ON paper_orders(symbol, created_at DESC);

COMMENT ON TABLE paper_orders IS 'Tracks all paper trading orders (both mock and real paper API)';

-- Add virtual money configuration
CREATE TABLE IF NOT EXISTS virtual_money_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    initial_allocation DECIMAL(15, 2) DEFAULT 100000.00,
    max_top_up DECIMAL(15, 2) DEFAULT 1000000.00,
    total_added DECIMAL(15, 2) DEFAULT 0.00,
    allow_reset BOOLEAN DEFAULT true,
    last_reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_virtual_money_user ON virtual_money_config(user_id);

COMMENT ON TABLE virtual_money_config IS 'Virtual money configuration and limits per user';

-- Add paper trading statistics
CREATE TABLE IF NOT EXISTS paper_trading_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0.00,
    best_trade DECIMAL(15, 2) DEFAULT 0.00,
    worst_trade DECIMAL(15, 2) DEFAULT 0.00,
    current_streak INTEGER DEFAULT 0,
    max_drawdown DECIMAL(15, 2) DEFAULT 0.00,
    total_fees DECIMAL(15, 2) DEFAULT 0.00,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_paper_stats_user ON paper_trading_stats(user_id);

COMMENT ON TABLE paper_trading_stats IS 'Paper trading performance statistics per user';

-- Function to update paper trading stats
CREATE OR REPLACE FUNCTION update_paper_trading_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update stats when a paper order is filled
    IF NEW.status = 'filled' AND OLD.status != 'filled' THEN
        INSERT INTO paper_trading_stats (user_id, total_trades)
        VALUES (NEW.user_id, 1)
        ON CONFLICT (user_id) DO UPDATE
        SET total_trades = paper_trading_stats.total_trades + 1,
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update stats
DROP TRIGGER IF EXISTS trigger_update_paper_stats ON paper_orders;
CREATE TRIGGER trigger_update_paper_stats
    AFTER UPDATE ON paper_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_paper_trading_stats();

-- Function to initialize virtual money for new users
CREATE OR REPLACE FUNCTION initialize_virtual_money()
RETURNS TRIGGER AS $$
BEGIN
    -- Create virtual money config for new user
    INSERT INTO virtual_money_config (user_id, initial_allocation)
    VALUES (NEW.id, 100000.00);

    -- Create paper trading stats record
    INSERT INTO paper_trading_stats (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-initialize virtual money on user creation
DROP TRIGGER IF EXISTS trigger_init_virtual_money ON users;
CREATE TRIGGER trigger_init_virtual_money
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION initialize_virtual_money();

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolios_cash_balance ON portfolios(cash_balance);

-- Migration complete
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (11, 'Add paper trading enhancements', NOW())
ON CONFLICT (version) DO NOTHING;
