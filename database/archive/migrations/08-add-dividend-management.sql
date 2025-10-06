-- Add dividend management tables for multi-user bulk order system
-- Part of Phase 1: Enhanced Investment Flow with Broker Integration

-- Table to store dividend declarations by companies
CREATE TABLE IF NOT EXISTS dividend_declarations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    ex_dividend_date DATE NOT NULL,
    record_date DATE NOT NULL,
    payment_date DATE NOT NULL,
    dividend_amount DECIMAL(15,4) NOT NULL,
    dividend_type VARCHAR(20) NOT NULL DEFAULT 'cash', -- 'cash', 'stock', 'special'
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    announcement_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'announced', -- 'announced', 'paid', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_dividend_per_asset_ex_date UNIQUE (asset_id, ex_dividend_date)
);

-- Table to track user position snapshots for dividend eligibility
CREATE TABLE IF NOT EXISTS user_position_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    average_cost DECIMAL(15,4) NOT NULL,
    market_value DECIMAL(15,4) NOT NULL,
    broker_name VARCHAR(50) NOT NULL,
    dividend_declaration_id UUID REFERENCES dividend_declarations(id) ON DELETE SET NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_position_snapshot UNIQUE (user_id, asset_id, snapshot_date, dividend_declaration_id)
);

-- Table to store dividend payments received by users
CREATE TABLE IF NOT EXISTS user_dividend_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    dividend_declaration_id UUID NOT NULL REFERENCES dividend_declarations(id) ON DELETE CASCADE,
    position_snapshot_id UUID REFERENCES user_position_snapshots(id) ON DELETE SET NULL,
    eligible_shares DECIMAL(15,4) NOT NULL,
    dividend_per_share DECIMAL(15,4) NOT NULL,
    gross_amount DECIMAL(15,4) NOT NULL,
    tax_withheld DECIMAL(15,4) DEFAULT 0,
    net_amount DECIMAL(15,4) NOT NULL,
    payment_date DATE NOT NULL,
    broker_name VARCHAR(50) NOT NULL,
    reinvestment_preference VARCHAR(20) DEFAULT 'cash', -- 'cash', 'drip', 'manual'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'received', 'reinvested'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store DRIP (Dividend Reinvestment Plan) transactions
CREATE TABLE IF NOT EXISTS drip_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_dividend_payment_id UUID NOT NULL REFERENCES user_dividend_payments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    reinvestment_amount DECIMAL(15,4) NOT NULL,
    shares_purchased DECIMAL(15,4) NOT NULL,
    purchase_price DECIMAL(15,4) NOT NULL,
    transaction_date DATE NOT NULL,
    broker_name VARCHAR(50) NOT NULL,
    broker_transaction_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'executed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store user DRIP preferences
CREATE TABLE IF NOT EXISTS user_drip_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE, -- NULL means global preference
    is_enabled BOOLEAN NOT NULL DEFAULT false,
    minimum_amount DECIMAL(15,4) DEFAULT 0, -- Minimum dividend amount to reinvest
    maximum_percentage DECIMAL(5,2) DEFAULT 100.00, -- Max % of dividend to reinvest
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_user_drip_pref UNIQUE (user_id, asset_id)
);

-- Table to aggregate bulk orders for dividend reinvestment
CREATE TABLE IF NOT EXISTS dividend_bulk_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    execution_date DATE NOT NULL,
    total_amount DECIMAL(15,4) NOT NULL,
    total_shares_to_purchase DECIMAL(15,4) NOT NULL,
    target_price DECIMAL(15,4),
    actual_price DECIMAL(15,4),
    broker_name VARCHAR(50) NOT NULL,
    broker_order_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'executed', 'partially_filled', 'failed'
    execution_window_start TIMESTAMP WITH TIME ZONE,
    execution_window_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to link individual DRIP transactions to bulk orders
CREATE TABLE IF NOT EXISTS drip_bulk_order_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drip_transaction_id UUID NOT NULL REFERENCES drip_transactions(id) ON DELETE CASCADE,
    dividend_bulk_order_id UUID NOT NULL REFERENCES dividend_bulk_orders(id) ON DELETE CASCADE,
    allocated_amount DECIMAL(15,4) NOT NULL,
    allocated_shares DECIMAL(15,4) NOT NULL,
    allocation_percentage DECIMAL(8,4) NOT NULL, -- Percentage of bulk order allocated to this user
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_drip_bulk_allocation UNIQUE (drip_transaction_id, dividend_bulk_order_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dividend_declarations_asset_ex_date ON dividend_declarations(asset_id, ex_dividend_date);
CREATE INDEX IF NOT EXISTS idx_dividend_declarations_payment_date ON dividend_declarations(payment_date);

CREATE INDEX IF NOT EXISTS idx_position_snapshots_user_asset ON user_position_snapshots(user_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_date ON user_position_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_dividend ON user_position_snapshots(dividend_declaration_id);

CREATE INDEX IF NOT EXISTS idx_dividend_payments_user ON user_dividend_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_dividend_payments_asset ON user_dividend_payments(asset_id);
CREATE INDEX IF NOT EXISTS idx_dividend_payments_date ON user_dividend_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_dividend_payments_status ON user_dividend_payments(status);

CREATE INDEX IF NOT EXISTS idx_drip_transactions_user ON drip_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_drip_transactions_asset ON drip_transactions(asset_id);
CREATE INDEX IF NOT EXISTS idx_drip_transactions_date ON drip_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_drip_preferences_user ON user_drip_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_drip_preferences_asset ON user_drip_preferences(asset_id);

CREATE INDEX IF NOT EXISTS idx_dividend_bulk_orders_asset ON dividend_bulk_orders(asset_id);
CREATE INDEX IF NOT EXISTS idx_dividend_bulk_orders_date ON dividend_bulk_orders(execution_date);
CREATE INDEX IF NOT EXISTS idx_dividend_bulk_orders_status ON dividend_bulk_orders(status);

CREATE INDEX IF NOT EXISTS idx_drip_bulk_allocations_drip ON drip_bulk_order_allocations(drip_transaction_id);
CREATE INDEX IF NOT EXISTS idx_drip_bulk_allocations_bulk ON drip_bulk_order_allocations(dividend_bulk_order_id);