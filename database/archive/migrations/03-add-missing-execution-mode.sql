-- =====================================================
-- 03-ADD-MISSING-EXECUTION-MODE.SQL
-- Add missing execution_mode column to user_smallcase_investments
-- =====================================================

-- This migration adds the missing execution_mode column to user_smallcase_investments table

BEGIN;

-- Add execution_mode column to user_smallcase_investments if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'user_smallcase_investments'
        AND column_name = 'execution_mode'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE user_smallcase_investments
        ADD COLUMN execution_mode VARCHAR(10) DEFAULT 'paper' CHECK (execution_mode IN ('paper', 'live'));

        RAISE NOTICE 'Added execution_mode column to user_smallcase_investments';
    ELSE
        RAISE NOTICE 'execution_mode column already exists in user_smallcase_investments';
    END IF;
END $$;

-- Verify the changes
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE 'Migration completed. Verifying execution_mode column:';

    FOR rec IN
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_smallcase_investments'
        AND column_name = 'execution_mode'
    LOOP
        RAISE NOTICE 'user_smallcase_investments.%: % (default: %, nullable: %)',
                     rec.column_name, rec.data_type, rec.column_default, rec.is_nullable;
    END LOOP;
END $$;

COMMIT;

-- =====================================================
-- Migration Notes:
-- 1. This script is idempotent - safe to run multiple times
-- 2. The execution_mode column accepts 'paper' and 'live' values
-- 3. Default value is 'paper' for safety
-- =====================================================