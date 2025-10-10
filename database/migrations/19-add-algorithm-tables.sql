-- Migration: Add algorithmic trading tables
-- Purpose: Support algorithm creation, backtesting, execution, and performance tracking
-- Multi-Broker Support: Zerodha (live only) + Alpaca (paper/live)

-- =====================================================
-- Core Algorithm Definition Table
-- =====================================================
CREATE TABLE IF NOT EXISTS trading_algorithms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    language VARCHAR(20) DEFAULT 'python',
    strategy_code TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',

    -- Execution settings
    auto_run BOOLEAN DEFAULT false,
    execution_interval VARCHAR(20) DEFAULT 'manual', -- manual, 1min, 5min, 15min, 1hour, daily
    max_positions INTEGER DEFAULT 5,
    risk_per_trade NUMERIC(5,2) DEFAULT 2.0, -- % of portfolio per trade
    max_daily_loss NUMERIC(10,2) DEFAULT 1000.00, -- Max loss per day before auto-stop

    -- Broker/Mode constraints
    allowed_regions VARCHAR(50)[] DEFAULT ARRAY['IN', 'US'], -- Which regions can run this
    allowed_trading_modes VARCHAR(20)[] DEFAULT ARRAY['paper', 'live'],
    target_broker VARCHAR(50), -- zerodha, alpaca, null for auto-detect

    -- Status and metrics
    status VARCHAR(20) DEFAULT 'inactive', -- active, inactive, error, backtesting
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT trading_algorithms_status_check
        CHECK (status IN ('active', 'inactive', 'error', 'backtesting')),
    CONSTRAINT trading_algorithms_interval_check
        CHECK (execution_interval IN ('manual', '1min', '5min', '15min', '1hour', 'daily'))
);

-- =====================================================
-- Algorithm Execution History
-- =====================================================
CREATE TABLE IF NOT EXISTS algorithm_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE SET NULL,

    execution_type VARCHAR(20) NOT NULL, -- scheduled, manual, backtest
    broker_used VARCHAR(50), -- zerodha, alpaca
    trading_mode VARCHAR(10), -- paper, live

    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER, -- Execution time in milliseconds
    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed, cancelled

    trades_generated INTEGER DEFAULT 0,
    signals_count INTEGER DEFAULT 0,
    orders_placed INTEGER DEFAULT 0,
    orders_filled INTEGER DEFAULT 0,

    error_message TEXT,
    execution_log JSONB DEFAULT '[]', -- Array of log entries with timestamps

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT algorithm_executions_type_check
        CHECK (execution_type IN ('scheduled', 'manual', 'backtest')),
    CONSTRAINT algorithm_executions_status_check
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- =====================================================
-- Backtest Results
-- =====================================================
CREATE TABLE IF NOT EXISTS algorithm_backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES algorithm_executions(id) ON DELETE SET NULL,

    backtest_name VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(15,2) NOT NULL,
    final_capital NUMERIC(15,2),

    -- Return metrics
    total_return NUMERIC(15,2), -- Absolute return
    total_return_pct NUMERIC(10,4), -- Percentage return
    annualized_return NUMERIC(10,4), -- Annualized return %

    -- Risk metrics
    sharpe_ratio NUMERIC(10,4),
    sortino_ratio NUMERIC(10,4),
    max_drawdown NUMERIC(15,2), -- Absolute max drawdown
    max_drawdown_pct NUMERIC(10,4), -- Max drawdown %
    volatility NUMERIC(10,4), -- Annualized volatility

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate NUMERIC(10,4), -- Percentage of winning trades
    profit_factor NUMERIC(10,4), -- Gross profit / Gross loss
    avg_win NUMERIC(15,2),
    avg_loss NUMERIC(15,2),
    avg_trade_duration_hours NUMERIC(10,2),

    -- Best/Worst
    best_trade NUMERIC(15,2),
    worst_trade NUMERIC(15,2),
    longest_winning_streak INTEGER,
    longest_losing_streak INTEGER,

    -- Equity curve (array of {date, equity, drawdown, trades})
    equity_curve JSONB DEFAULT '[]',

    -- Trade log (array of {date, symbol, side, quantity, price, pnl})
    trade_log JSONB DEFAULT '[]',

    -- Configuration snapshot
    parameters JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Trading Signals Generated by Algorithms
-- =====================================================
CREATE TABLE IF NOT EXISTS algorithm_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES algorithm_executions(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE SET NULL,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,

    -- Signal details
    signal_type VARCHAR(10) NOT NULL, -- buy, sell, hold
    signal_strength NUMERIC(5,2) DEFAULT 1.0, -- 0-1 confidence scale
    quantity NUMERIC(18,8),
    suggested_price NUMERIC(15,8),
    stop_loss NUMERIC(15,8),
    take_profit NUMERIC(15,8),

    -- Execution tracking
    executed BOOLEAN DEFAULT false,
    transaction_id UUID REFERENCES trading_transactions(id) ON DELETE SET NULL,
    execution_price NUMERIC(15,8),
    executed_at TIMESTAMP WITH TIME ZONE,
    execution_status VARCHAR(20), -- pending, filled, rejected, cancelled, expired

    -- Signal metadata
    reason TEXT, -- Why this signal was generated
    indicators JSONB DEFAULT '{}', -- Indicator values at signal time (RSI, MACD, etc.)
    risk_reward_ratio NUMERIC(10,2), -- Calculated risk/reward

    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE, -- Signal expiration time

    CONSTRAINT algorithm_signals_type_check
        CHECK (signal_type IN ('buy', 'sell', 'hold'))
);

-- =====================================================
-- Daily Algorithm Performance Snapshots
-- =====================================================
CREATE TABLE IF NOT EXISTS algorithm_performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,

    -- P&L metrics
    daily_pnl NUMERIC(15,2) DEFAULT 0,
    daily_pnl_pct NUMERIC(10,4) DEFAULT 0,
    cumulative_pnl NUMERIC(15,2) DEFAULT 0,
    cumulative_pnl_pct NUMERIC(10,4) DEFAULT 0,

    -- Position metrics
    running_trades INTEGER DEFAULT 0,
    daily_trades INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,

    -- Win/Loss tracking
    daily_wins INTEGER DEFAULT 0,
    daily_losses INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    win_rate NUMERIC(10,4),

    -- Risk metrics
    current_drawdown NUMERIC(15,2) DEFAULT 0,
    current_drawdown_pct NUMERIC(10,4) DEFAULT 0,
    max_drawdown NUMERIC(15,2) DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_algo_snapshot UNIQUE (algorithm_id, snapshot_date)
);

-- =====================================================
-- Algorithm Templates (Pre-built Strategies)
-- =====================================================
CREATE TABLE IF NOT EXISTS algorithm_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- momentum, mean_reversion, trend_following, arbitrage
    language VARCHAR(20) DEFAULT 'python',

    strategy_code TEXT NOT NULL,
    default_parameters JSONB DEFAULT '{}',

    -- Region/broker compatibility
    compatible_regions VARCHAR(50)[] DEFAULT ARRAY['IN', 'US'],
    compatible_brokers VARCHAR(50)[] DEFAULT ARRAY['zerodha', 'alpaca'],

    -- Metadata
    difficulty_level VARCHAR(20), -- beginner, intermediate, advanced
    typical_timeframe VARCHAR(50), -- intraday, swing, positional
    risk_level VARCHAR(20), -- low, medium, high

    -- Usage stats
    times_used INTEGER DEFAULT 0,
    avg_rating NUMERIC(3,2),

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- trading_algorithms indexes
CREATE INDEX IF NOT EXISTS idx_algorithms_user_id ON trading_algorithms(user_id);
CREATE INDEX IF NOT EXISTS idx_algorithms_status ON trading_algorithms(status);
CREATE INDEX IF NOT EXISTS idx_algorithms_auto_run ON trading_algorithms(auto_run) WHERE auto_run = true;
CREATE INDEX IF NOT EXISTS idx_algorithms_updated_at ON trading_algorithms(updated_at DESC);

-- algorithm_executions indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_algo_id ON algorithm_executions(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_user_id ON algorithm_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_status ON algorithm_executions(status);
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_start_time ON algorithm_executions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_type ON algorithm_executions(execution_type);

-- algorithm_signals indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_algo_id ON algorithm_signals(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_user_id ON algorithm_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_asset_id ON algorithm_signals(asset_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_executed ON algorithm_signals(executed);
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_generated_at ON algorithm_signals(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_algorithm_signals_pending ON algorithm_signals(executed, execution_status)
    WHERE executed = false;

-- algorithm_backtest_results indexes
CREATE INDEX IF NOT EXISTS idx_backtest_results_algo_id ON algorithm_backtest_results(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_user_id ON algorithm_backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_created_at ON algorithm_backtest_results(created_at DESC);

-- algorithm_performance_snapshots indexes
CREATE INDEX IF NOT EXISTS idx_performance_snapshots_algo_id ON algorithm_performance_snapshots(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_performance_snapshots_date ON algorithm_performance_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_snapshots_algo_date ON algorithm_performance_snapshots(algorithm_id, snapshot_date DESC);

-- algorithm_templates indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_templates_category ON algorithm_templates(category);
CREATE INDEX IF NOT EXISTS idx_algorithm_templates_active ON algorithm_templates(is_active) WHERE is_active = true;

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE trading_algorithms IS 'User-created trading algorithms with code and configuration';
COMMENT ON TABLE algorithm_executions IS 'History of algorithm execution runs with performance metrics';
COMMENT ON TABLE algorithm_backtest_results IS 'Historical simulation results with detailed performance metrics';
COMMENT ON TABLE algorithm_signals IS 'Buy/sell signals generated by algorithms';
COMMENT ON TABLE algorithm_performance_snapshots IS 'Daily performance snapshots for tracking algorithm P&L';
COMMENT ON TABLE algorithm_templates IS 'Pre-built algorithm templates for users to customize';

COMMENT ON COLUMN trading_algorithms.strategy_code IS 'Python code for the trading strategy';
COMMENT ON COLUMN trading_algorithms.parameters IS 'JSON configuration for algorithm parameters';
COMMENT ON COLUMN trading_algorithms.auto_run IS 'Whether algorithm runs automatically on schedule';
COMMENT ON COLUMN trading_algorithms.execution_interval IS 'How often to run: manual, 1min, 5min, 15min, 1hour, daily';
COMMENT ON COLUMN trading_algorithms.risk_per_trade IS 'Maximum % of portfolio to risk per trade';
COMMENT ON COLUMN trading_algorithms.target_broker IS 'Specific broker to use, or null for auto-detect based on region';

COMMENT ON COLUMN algorithm_backtest_results.equity_curve IS 'Array of {date, equity, drawdown} for charting';
COMMENT ON COLUMN algorithm_backtest_results.trade_log IS 'Array of all trades executed during backtest';
COMMENT ON COLUMN algorithm_backtest_results.sharpe_ratio IS 'Risk-adjusted return metric (higher is better)';
COMMENT ON COLUMN algorithm_backtest_results.profit_factor IS 'Gross profit divided by gross loss';

COMMENT ON COLUMN algorithm_signals.signal_strength IS 'Confidence level from 0-1, where 1 is highest confidence';
COMMENT ON COLUMN algorithm_signals.indicators IS 'JSON object containing indicator values at signal generation time';
COMMENT ON COLUMN algorithm_signals.expires_at IS 'When this signal should no longer be considered valid';
