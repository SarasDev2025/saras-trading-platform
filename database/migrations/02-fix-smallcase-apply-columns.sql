-- =====================================================
-- 02-FIX-SMALLCASE-APPLY-COLUMNS.SQL
-- Fix column mismatches for smallcase apply feature
-- =====================================================

-- This migration fixes column mismatches between SQLAlchemy models and database schema
-- for the smallcase apply/execution feature to work properly

BEGIN;

-- 1. Add missing columns to trading_transactions table
ALTER TABLE trading_transactions
ADD COLUMN IF NOT EXISTS order_type VARCHAR(20) CHECK (order_type IN ('market', 'limit', 'stop_loss'));

ALTER TABLE trading_transactions
ADD COLUMN IF NOT EXISTS notes TEXT;

ALTER TABLE trading_transactions
ADD COLUMN IF NOT EXISTS external_transaction_id VARCHAR(255);

-- Add index for the new external_transaction_id column
CREATE INDEX IF NOT EXISTS idx_trading_transactions_external_id ON trading_transactions(external_transaction_id);

-- 2. Rename metadata column to details in smallcase_execution_orders table
-- Check if the metadata column exists before renaming
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'smallcase_execution_orders'
        AND column_name = 'metadata'
        AND table_schema = 'public'
    ) THEN
        -- Only rename if details column doesn't already exist
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'smallcase_execution_orders'
            AND column_name = 'details'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE smallcase_execution_orders RENAME COLUMN metadata TO details;
            RAISE NOTICE 'Renamed metadata column to details in smallcase_execution_orders';
        ELSE
            RAISE NOTICE 'Details column already exists in smallcase_execution_orders, skipping rename';
        END IF;
    ELSE
        -- If metadata doesn't exist but details doesn't exist either, create details column
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'smallcase_execution_orders'
            AND column_name = 'details'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE smallcase_execution_orders ADD COLUMN details JSONB;
            RAISE NOTICE 'Added details column to smallcase_execution_orders';
        ELSE
            RAISE NOTICE 'Details column already exists in smallcase_execution_orders';
        END IF;
    END IF;
END $$;

-- 3. Update updated_at trigger for trading_transactions if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers
        WHERE trigger_name = 'update_trading_transactions_updated_at'
        AND event_object_table = 'trading_transactions'
    ) THEN
        CREATE TRIGGER update_trading_transactions_updated_at
        BEFORE UPDATE ON trading_transactions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Created updated_at trigger for trading_transactions';
    ELSE
        RAISE NOTICE 'updated_at trigger already exists for trading_transactions';
    END IF;
END $$;

-- 4. Verify the changes
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE 'Migration completed. Verifying changes:';

    -- Check trading_transactions columns
    FOR rec IN
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'trading_transactions'
        AND column_name IN ('order_type', 'notes', 'external_transaction_id')
        ORDER BY column_name
    LOOP
        RAISE NOTICE 'trading_transactions.%: %', rec.column_name, rec.data_type;
    END LOOP;

    -- Check smallcase_execution_orders columns
    FOR rec IN
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'smallcase_execution_orders'
        AND column_name IN ('details', 'metadata')
        ORDER BY column_name
    LOOP
        RAISE NOTICE 'smallcase_execution_orders.%: %', rec.column_name, rec.data_type;
    END LOOP;
END $$;

COMMIT;

-- =====================================================
-- Migration Notes:
-- 1. This script is idempotent - safe to run multiple times
-- 2. The order_type column accepts 'market', 'limit', 'stop_loss' values
-- 3. The metadata->details rename preserves existing data
-- 4. All changes are wrapped in a transaction for safety
-- =====================================================