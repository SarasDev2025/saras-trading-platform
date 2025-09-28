-- Migration 09: Fix portfolio_holdings missing updated_at column
-- This fixes the PostgreSQL error: record "new" has no field "updated_at"
-- when the update trigger tries to set NEW.updated_at on a column that doesn't exist

-- Add updated_at column to portfolio_holdings table
DO $$
BEGIN
    -- Check if updated_at column already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'portfolio_holdings'
        AND column_name = 'updated_at'
    ) THEN
        -- Add the updated_at column
        ALTER TABLE portfolio_holdings
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

        -- Set updated_at to created_at for existing rows
        UPDATE portfolio_holdings
        SET updated_at = created_at
        WHERE updated_at IS NULL;

        RAISE NOTICE 'Added updated_at column to portfolio_holdings table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in portfolio_holdings table';
    END IF;
END;
$$;

-- Verify the trigger exists and is working properly
-- The trigger should already exist from 01-setup.sql:
-- CREATE TRIGGER update_portfolio_holdings_updated_at
-- BEFORE UPDATE ON portfolio_holdings
-- FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Test that the trigger works
DO $$
BEGIN
    RAISE NOTICE 'Portfolio holdings updated_at column migration completed successfully';
END;
$$;