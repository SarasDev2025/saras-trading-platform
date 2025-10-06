--
-- Migration: Add trading_mode to users table
-- Description: Adds user-level trading mode field to support paper/live trading toggle
-- Date: 2025-01-06
--

-- Add trading_mode column to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(10) DEFAULT 'paper' NOT NULL;

-- Add constraint to ensure only valid values
ALTER TABLE public.users
ADD CONSTRAINT users_trading_mode_check CHECK (trading_mode IN ('paper', 'live'));

-- Add index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_users_trading_mode ON public.users(trading_mode);

-- Add comment
COMMENT ON COLUMN public.users.trading_mode IS 'Current trading mode for user: paper (virtual money) or live (real money)';
