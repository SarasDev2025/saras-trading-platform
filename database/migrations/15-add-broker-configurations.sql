--
-- Migration: Add broker configurations table
-- Description: Store broker URLs and settings per region and trading mode
-- Date: 2025-10-06
--

-- Create broker_configurations table
CREATE TABLE IF NOT EXISTS public.broker_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broker_name VARCHAR(50) NOT NULL,
    region VARCHAR(5) NOT NULL,
    trading_mode VARCHAR(10) NOT NULL,
    api_url TEXT NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT broker_configurations_region_check CHECK (region IN ('IN', 'US', 'GB')),
    CONSTRAINT broker_configurations_mode_check CHECK (trading_mode IN ('paper', 'live')),
    CONSTRAINT broker_configurations_unique UNIQUE (broker_name, region, trading_mode)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_broker_configs_region ON public.broker_configurations(region);
CREATE INDEX IF NOT EXISTS idx_broker_configs_active ON public.broker_configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_broker_configs_region_mode ON public.broker_configurations(region, trading_mode);

-- Add comments
COMMENT ON TABLE public.broker_configurations IS 'Broker API configurations by region and trading mode';
COMMENT ON COLUMN public.broker_configurations.broker_name IS 'Internal broker identifier (e.g., zerodha, alpaca, interactive_brokers)';
COMMENT ON COLUMN public.broker_configurations.region IS 'User region: IN (India), US (United States), GB (United Kingdom)';
COMMENT ON COLUMN public.broker_configurations.trading_mode IS 'Trading mode: paper or live';
COMMENT ON COLUMN public.broker_configurations.api_url IS 'Broker API base URL';
COMMENT ON COLUMN public.broker_configurations.display_name IS 'User-facing broker name';
COMMENT ON COLUMN public.broker_configurations.description IS 'Broker description shown to users';

-- Seed initial broker configurations
INSERT INTO public.broker_configurations (broker_name, region, trading_mode, api_url, display_name, description, sort_order) VALUES
-- India - Zerodha
('zerodha', 'IN', 'paper', 'https://api.kite.trade', 'Zerodha Kite', 'India Markets • Stocks, ETFs, Mutual Funds', 1),
('zerodha', 'IN', 'live', 'https://api.kite.trade', 'Zerodha Kite', 'India Markets • Stocks, ETFs, Mutual Funds', 1),

-- United States - Alpaca
('alpaca', 'US', 'paper', 'https://paper-api.alpaca.markets', 'Alpaca Trading', 'US Markets • Stocks, ETFs, Crypto', 1),
('alpaca', 'US', 'live', 'https://api.alpaca.markets', 'Alpaca Trading', 'US Markets • Stocks, ETFs, Crypto', 1),

-- United Kingdom - Interactive Brokers
('interactive_brokers', 'GB', 'paper', 'https://api.ibkr.com/v1/portal', 'Interactive Brokers', 'Global Markets • Stocks, Options, Futures', 1),
('interactive_brokers', 'GB', 'live', 'https://api.ibkr.com/v1/portal', 'Interactive Brokers', 'Global Markets • Stocks, Options, Futures', 1)

ON CONFLICT (broker_name, region, trading_mode) DO NOTHING;
