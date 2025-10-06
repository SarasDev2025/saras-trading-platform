--
-- Migration: Add region to users table
-- Description: Adds user region field for broker selection
-- Date: 2025-01-06
--

-- Add region column to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS region VARCHAR(5) DEFAULT 'IN' NOT NULL;

-- Add constraint to ensure only valid values
ALTER TABLE public.users
ADD CONSTRAINT users_region_check CHECK (region IN ('IN', 'US', 'GB'));

-- Add index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_users_region ON public.users(region);

-- Add comment
COMMENT ON COLUMN public.users.region IS 'User region for broker selection: IN (India), US (United States), GB (United Kingdom)';
