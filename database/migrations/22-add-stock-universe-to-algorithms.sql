-- Migration: Add stock universe and position sizing configuration to algorithms
-- Purpose: Allow users to specify which stocks to trade and how much to trade per position

-- =====================================================
-- Add Stock Universe and Position Sizing Config
-- =====================================================

-- Add stock_universe column to define which stocks this algorithm can trade
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS stock_universe JSONB DEFAULT '{
    "type": "all",
    "symbols": [],
    "filters": {}
}'::jsonb;

-- Add position_sizing_config column for detailed position sizing rules
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS position_sizing_config JSONB DEFAULT '{
    "type": "fixed",
    "quantity": 10,
    "percent_of_portfolio": null,
    "risk_amount": null,
    "per_symbol_allocation": {}
}'::jsonb;

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON COLUMN trading_algorithms.stock_universe IS 'Defines which stocks this algorithm can trade. Types: all (all liquid stocks), watchlist (user watchlist), specific (explicit symbol list), filtered (by sector/market cap/volume). Example: {"type": "specific", "symbols": ["AAPL", "MSFT", "GOOGL"], "filters": {}}';

COMMENT ON COLUMN trading_algorithms.position_sizing_config IS 'Detailed position sizing configuration. Types: fixed (fixed quantity), percent (% of portfolio), risk_based ($ risk per trade). Example: {"type": "fixed", "quantity": 10, "percent_of_portfolio": null, "risk_amount": null, "per_symbol_allocation": {"AAPL": 20, "MSFT": 15}}';

-- =====================================================
-- Index for Stock Universe Queries
-- =====================================================

-- Index for finding algorithms trading specific symbols
CREATE INDEX IF NOT EXISTS idx_algorithms_stock_universe
ON trading_algorithms USING GIN (stock_universe);

-- =====================================================
-- Update Existing Algorithms
-- =====================================================

-- Set default stock universe for existing algorithms
UPDATE trading_algorithms
SET
    stock_universe = '{"type": "all", "symbols": [], "filters": {}}'::jsonb,
    position_sizing_config = jsonb_build_object(
        'type', 'fixed',
        'quantity', COALESCE((parameters->>'default_quantity')::numeric, 10),
        'percent_of_portfolio', NULL,
        'risk_amount', risk_per_trade,
        'per_symbol_allocation', '{}'::jsonb
    )
WHERE stock_universe IS NULL OR position_sizing_config IS NULL;
