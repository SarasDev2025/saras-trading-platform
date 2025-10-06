-- =====================================================
-- 01-SETUP.SQL - Database Schema Setup
-- Professional Trading Platform Database Structure
-- =====================================================

-- This file should be run first to create all tables and constraints

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_verified BOOLEAN DEFAULT FALSE,
    kyc_status VARCHAR(20) DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'approved', 'rejected')),
    account_status VARCHAR(20) DEFAULT 'active' CHECK (account_status IN ('active', 'suspended', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity', 'bond')),
    exchange VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    current_price NUMERIC(15,8),
    price_updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pb_ratio NUMERIC(8,2),
    dividend_yield NUMERIC(5,2),
    beta NUMERIC(6,3),
    industry VARCHAR(150)
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    cash_balance DECIMAL(15,2) DEFAULT 0,
    total_value DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Smallcases table
CREATE TABLE IF NOT EXISTS smallcases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    theme VARCHAR(100),
    risk_level VARCHAR(20) DEFAULT 'medium' CHECK (risk_level IN ('low', 'medium', 'high')),
    expected_return_min NUMERIC(5,2),
    expected_return_max NUMERIC(5,2),
    minimum_investment NUMERIC(15,2) DEFAULT 1000.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    strategy_type VARCHAR(100) DEFAULT 'VALUE',
    expected_return_1y NUMERIC(6,2),
    expected_return_3y NUMERIC(6,2),
    expected_return_5y NUMERIC(6,2),
    volatility NUMERIC(6,2),
    sharpe_ratio NUMERIC(6,3),
    max_drawdown NUMERIC(6,2),
    expense_ratio NUMERIC(5,3)
);

-- Smallcase constituents table
CREATE TABLE IF NOT EXISTS smallcase_constituents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    smallcase_id UUID REFERENCES smallcases(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    weight_percentage NUMERIC(5,2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(smallcase_id, asset_id)
);

-- User broker connections table
CREATE TABLE IF NOT EXISTS user_broker_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    broker_type VARCHAR(50) NOT NULL,
    alias VARCHAR(50) NOT NULL,
    api_key TEXT,
    api_secret TEXT,
    credentials JSONB,
    paper_trading BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    connection_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, alias)
);

-- User smallcase investments table
CREATE TABLE IF NOT EXISTS user_smallcase_investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id),
    smallcase_id UUID REFERENCES smallcases(id),
    investment_amount NUMERIC(15,2) NOT NULL,
    units_purchased NUMERIC(12,6) NOT NULL,
    purchase_price NUMERIC(12,4) NOT NULL,
    current_value NUMERIC(15,2) DEFAULT 0,
    unrealized_pnl NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'partial')),
    execution_mode VARCHAR(10) DEFAULT 'paper' CHECK (execution_mode IN ('paper', 'live')),
    broker_connection_id UUID REFERENCES user_broker_connections(id) ON DELETE SET NULL,
    auto_rebalance BOOLEAN DEFAULT FALSE,
    last_rebalanced_at TIMESTAMP WITH TIME ZONE,
    invested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio holdings table
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id),
    quantity NUMERIC(18,8) NOT NULL,
    average_cost NUMERIC(15,8) NOT NULL,
    total_cost NUMERIC(15,2) NOT NULL,
    current_value NUMERIC(15,2) DEFAULT 0,
    unrealized_pnl NUMERIC(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Smallcase execution runs table
CREATE TABLE IF NOT EXISTS smallcase_execution_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    investment_id UUID REFERENCES user_smallcase_investments(id) ON DELETE CASCADE,
    broker_connection_id UUID REFERENCES user_broker_connections(id) ON DELETE SET NULL,
    execution_mode VARCHAR(10) NOT NULL DEFAULT 'paper' CHECK (execution_mode IN ('paper', 'live')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'completed', 'failed')),
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    summary JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Smallcase execution orders table
CREATE TABLE IF NOT EXISTS smallcase_execution_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_run_id UUID REFERENCES smallcase_execution_runs(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id),
    symbol VARCHAR(50),
    action VARCHAR(20),
    current_weight NUMERIC(7,3),
    suggested_weight NUMERIC(7,3),
    weight_change NUMERIC(7,3),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'completed', 'failed', 'simulated')),
    broker_order_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trading transactions table
CREATE TABLE IF NOT EXISTS trading_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    portfolio_id UUID REFERENCES portfolios(id),
    asset_id UUID REFERENCES assets(id),
    broker_connection_id UUID REFERENCES user_broker_connections(id) ON DELETE SET NULL,
    execution_run_id UUID REFERENCES smallcase_execution_runs(id) ON DELETE SET NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('buy', 'sell')),
    quantity NUMERIC(18,8) NOT NULL,
    price_per_unit NUMERIC(15,8) NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,
    fees NUMERIC(10,2) DEFAULT 0,
    net_amount NUMERIC(15,2) NOT NULL,
    broker_order_id VARCHAR(255),
    order_type VARCHAR(20) DEFAULT 'market' CHECK (order_type IN ('market', 'limit', 'stop_loss')),
    notes TEXT,
    external_transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'cancelled', 'failed')),
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    price NUMERIC(15,8) NOT NULL,
    volume BIGINT DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    interval_type VARCHAR(10) DEFAULT '1d',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Smallcase performance table
CREATE TABLE IF NOT EXISTS smallcase_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    smallcase_id UUID REFERENCES smallcases(id),
    date DATE NOT NULL,
    nav NUMERIC(15,4) NOT NULL,
    total_return_1d NUMERIC(8,4),
    total_return_1w NUMERIC(8,4),
    total_return_1m NUMERIC(8,4),
    total_return_1y NUMERIC(8,4),
    alpha NUMERIC(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(smallcase_id, date)
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_smallcases_risk_level ON smallcases(risk_level);
CREATE INDEX IF NOT EXISTS idx_smallcase_constituents_smallcase_id ON smallcase_constituents(smallcase_id);
CREATE INDEX IF NOT EXISTS idx_user_smallcase_investments_user_id ON user_smallcase_investments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_smallcase_investments_broker_connection_id ON user_smallcase_investments(broker_connection_id);
-- Unique constraint to prevent multiple active investments for same user-smallcase combination
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_smallcase_active_unique ON user_smallcase_investments (user_id, smallcase_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_user_broker_connections_user_id ON user_broker_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_broker_connections_broker_type ON user_broker_connections(broker_type);
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_portfolio_id ON portfolio_holdings(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_smallcase_execution_runs_investment_id ON smallcase_execution_runs(investment_id);
CREATE INDEX IF NOT EXISTS idx_smallcase_execution_orders_run_id ON smallcase_execution_orders(execution_run_id);
CREATE INDEX IF NOT EXISTS idx_trading_transactions_user_id ON trading_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_transactions_execution_run_id ON trading_transactions(execution_run_id);
CREATE INDEX IF NOT EXISTS idx_trading_transactions_broker_connection_id ON trading_transactions(broker_connection_id);
CREATE INDEX IF NOT EXISTS idx_trading_transactions_external_id ON trading_transactions(external_transaction_id);
CREATE INDEX IF NOT EXISTS idx_price_history_asset_id ON price_history(asset_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_smallcases_updated_at BEFORE UPDATE ON smallcases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolio_holdings_updated_at BEFORE UPDATE ON portfolio_holdings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_smallcase_investments_updated_at BEFORE UPDATE ON user_smallcase_investments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_broker_connections_updated_at BEFORE UPDATE ON user_broker_connections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_smallcase_execution_runs_updated_at BEFORE UPDATE ON smallcase_execution_runs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_smallcase_execution_orders_updated_at BEFORE UPDATE ON smallcase_execution_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_transactions_updated_at BEFORE UPDATE ON trading_transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
