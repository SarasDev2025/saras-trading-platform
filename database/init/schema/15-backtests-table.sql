-- Backtests table for storing backtest runs and results
CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,

    -- Backtest configuration
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital NUMERIC(15, 2) NOT NULL DEFAULT 100000.00,

    -- Position sizing
    position_sizing_model VARCHAR(50) DEFAULT 'fixed_percentage',
    position_sizing_params JSONB,

    -- Slippage and commissions
    slippage_model VARCHAR(50) DEFAULT 'percentage',
    slippage_params JSONB,
    commission_percentage NUMERIC(6, 5) DEFAULT 0.001,  -- 0.1%
    commission_per_trade NUMERIC(10, 2) DEFAULT 1.00,

    -- Benchmark
    benchmark_symbol VARCHAR(20),

    -- Execution
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    error TEXT,

    -- Results
    results JSONB,  -- Stores trades, equity curve, metrics

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT valid_dates CHECK (end_date > start_date),
    CONSTRAINT valid_capital CHECK (initial_capital > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_backtests_algorithm_id ON backtests(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status);
CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests(created_at DESC);

-- Comments
COMMENT ON TABLE backtests IS 'Stores historical backtest runs and their results';
COMMENT ON COLUMN backtests.results IS 'JSON containing trades, equity_curve, and performance metrics';
COMMENT ON COLUMN backtests.status IS 'Backtest execution status: pending, running, completed, failed';
