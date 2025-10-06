--
-- Migration: Add trading_mode to portfolios table
-- Description: Adds portfolio-level trading mode for data isolation between paper and live trading
-- Date: 2025-01-06
--

-- Add trading_mode column to portfolios table
ALTER TABLE public.portfolios
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(10) DEFAULT 'paper' NOT NULL;

-- Add constraint to ensure only valid values
ALTER TABLE public.portfolios
ADD CONSTRAINT portfolios_trading_mode_check CHECK (trading_mode IN ('paper', 'live'));

-- Add indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_portfolios_trading_mode ON public.portfolios(trading_mode);
CREATE INDEX IF NOT EXISTS idx_portfolios_user_mode ON public.portfolios(user_id, trading_mode);

-- Add comment
COMMENT ON COLUMN public.portfolios.trading_mode IS 'Trading mode for this portfolio: paper (virtual money) or live (real money)';

-- Note: Existing portfolios will default to 'paper' mode
-- Users can create new live portfolios when they switch to live trading mode
