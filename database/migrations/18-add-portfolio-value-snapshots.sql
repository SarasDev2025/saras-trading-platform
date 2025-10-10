-- Migration: Add portfolio_value_snapshots table and deposit tracking
-- Purpose: Track daily portfolio values for performance charts and calculations

-- Create portfolio_value_snapshots table
CREATE TABLE IF NOT EXISTS portfolio_value_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(15, 2) NOT NULL,
    cash_balance NUMERIC(15, 2) NOT NULL,
    holdings_value NUMERIC(15, 2) NOT NULL,
    total_invested NUMERIC(15, 2) DEFAULT 0,
    total_pnl NUMERIC(15, 2) DEFAULT 0,
    day_change NUMERIC(15, 2) DEFAULT 0,
    day_change_percent NUMERIC(10, 4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_portfolio_snapshot UNIQUE (portfolio_id, snapshot_date)
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_portfolio_value_snapshots_portfolio_id ON portfolio_value_snapshots(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_value_snapshots_user_id ON portfolio_value_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_value_snapshots_date ON portfolio_value_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_value_snapshots_portfolio_date ON portfolio_value_snapshots(portfolio_id, snapshot_date DESC);

-- Add comments
COMMENT ON TABLE portfolio_value_snapshots IS 'Daily snapshots of portfolio values for performance tracking';
COMMENT ON COLUMN portfolio_value_snapshots.snapshot_date IS 'Date of snapshot (one per day per portfolio)';
COMMENT ON COLUMN portfolio_value_snapshots.total_value IS 'Total portfolio value (cash + holdings)';
COMMENT ON COLUMN portfolio_value_snapshots.cash_balance IS 'Available cash balance';
COMMENT ON COLUMN portfolio_value_snapshots.holdings_value IS 'Market value of all holdings';
COMMENT ON COLUMN portfolio_value_snapshots.total_invested IS 'Total deposits minus withdrawals';
COMMENT ON COLUMN portfolio_value_snapshots.total_pnl IS 'Total profit/loss (total_value - total_invested)';
COMMENT ON COLUMN portfolio_value_snapshots.day_change IS 'Change in value from previous snapshot';
COMMENT ON COLUMN portfolio_value_snapshots.day_change_percent IS 'Percentage change from previous snapshot';

-- Add deposit tracking columns to portfolios table
ALTER TABLE portfolios
ADD COLUMN IF NOT EXISTS initial_deposit NUMERIC(15, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_deposits NUMERIC(15, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_withdrawals NUMERIC(15, 2) DEFAULT 0;

COMMENT ON COLUMN portfolios.initial_deposit IS 'First deposit amount (for "since open" calculations)';
COMMENT ON COLUMN portfolios.total_deposits IS 'Sum of all deposits made to portfolio';
COMMENT ON COLUMN portfolios.total_withdrawals IS 'Sum of all withdrawals from portfolio';
