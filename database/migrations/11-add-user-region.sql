-- =====================================================
-- Migration: Add User Region Field
-- =====================================================
-- Purpose: Add explicit region field to users table for accurate broker selection
-- Date: 2025-10-06
-- Author: Database Schema Consolidation
--
-- Changes:
-- 1. Add region column to users table (IN, US, GB)
-- 2. Set default value to 'IN' for all existing users
-- 3. Add check constraint for valid regions
-- =====================================================

-- Add region column to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS region VARCHAR(5) DEFAULT 'IN' NOT NULL;

-- Add check constraint for valid region values
ALTER TABLE public.users
ADD CONSTRAINT users_region_check CHECK (region IN ('IN', 'US', 'GB'));

-- Create index for faster region-based queries
CREATE INDEX IF NOT EXISTS idx_users_region ON public.users(region);

-- Update any existing users to have 'IN' region (default)
-- (This is already handled by the DEFAULT 'IN', but explicit for clarity)
UPDATE public.users
SET region = 'IN'
WHERE region IS NULL;

-- Add comment explaining the column
COMMENT ON COLUMN public.users.region IS 'User''s market region for broker selection: IN (India/Zerodha), US (United States/Alpaca), GB (United Kingdom/Interactive Brokers)';
