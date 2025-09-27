-- =====================================================
-- 06-ADD-SMALLCASE-CLOSURE-SUPPORT.SQL
-- Add smallcase closure tracking and position history
-- =====================================================

-- This migration adds comprehensive support for closing smallcase positions
-- and tracking historical performance data

BEGIN;

-- Step 1: Add closure tracking fields to user_smallcase_investments
ALTER TABLE user_smallcase_investments
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE user_smallcase_investments
ADD COLUMN IF NOT EXISTS exit_price NUMERIC(15,8);

ALTER TABLE user_smallcase_investments
ADD COLUMN IF NOT EXISTS exit_value NUMERIC(15,2);

ALTER TABLE user_smallcase_investments
ADD COLUMN IF NOT EXISTS realized_pnl NUMERIC(15,2);

ALTER TABLE user_smallcase_investments
ADD COLUMN IF NOT EXISTS closure_reason VARCHAR(50);

-- Step 2: Update transaction_type enum to include closure types
-- First add the new values to the check constraint
DO $$
BEGIN
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'trading_transactions'
        AND constraint_name = 'trading_transactions_transaction_type_check'
    ) THEN
        ALTER TABLE trading_transactions
        DROP CONSTRAINT trading_transactions_transaction_type_check;
    END IF;

    -- Add new constraint with closure types
    ALTER TABLE trading_transactions
    ADD CONSTRAINT trading_transactions_transaction_type_check
    CHECK (transaction_type IN ('buy', 'sell', 'close_position', 'partial_close'));

    RAISE NOTICE 'Updated transaction_type constraint to include closure types';
END $$;

-- Step 3: Create position history table
CREATE TABLE IF NOT EXISTS user_smallcase_position_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    smallcase_id UUID NOT NULL REFERENCES smallcases(id),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),

    -- Investment details
    investment_amount NUMERIC(15,2) NOT NULL,
    units_purchased NUMERIC(15,8) NOT NULL,
    purchase_price NUMERIC(15,8) NOT NULL,

    -- Exit details
    exit_value NUMERIC(15,2) NOT NULL,
    exit_price NUMERIC(15,8) NOT NULL,
    realized_pnl NUMERIC(15,2) NOT NULL,

    -- Performance metrics
    holding_period_days INTEGER NOT NULL,
    roi_percentage NUMERIC(8,4) NOT NULL,

    -- Timestamps
    invested_at TIMESTAMP WITH TIME ZONE NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    closure_reason VARCHAR(50),
    execution_mode VARCHAR(10) NOT NULL CHECK (execution_mode IN ('paper', 'live')),
    broker_connection_id UUID REFERENCES user_broker_connections(id) ON DELETE SET NULL,

    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_smallcase_investments_closed_at
ON user_smallcase_investments(closed_at) WHERE closed_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_smallcase_investments_status_closed
ON user_smallcase_investments(user_id, status) WHERE status IN ('sold', 'partial');

CREATE INDEX IF NOT EXISTS idx_position_history_user_id
ON user_smallcase_position_history(user_id);

CREATE INDEX IF NOT EXISTS idx_position_history_smallcase_id
ON user_smallcase_position_history(smallcase_id);

CREATE INDEX IF NOT EXISTS idx_position_history_closed_at
ON user_smallcase_position_history(closed_at);

CREATE INDEX IF NOT EXISTS idx_trading_transactions_transaction_type
ON trading_transactions(transaction_type);

-- Step 5: Add triggers for updated_at
CREATE TRIGGER update_user_smallcase_position_history_updated_at
BEFORE UPDATE ON user_smallcase_position_history
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 6: Add closure reason check constraint
ALTER TABLE user_smallcase_investments
ADD CONSTRAINT user_smallcase_investments_closure_reason_check
CHECK (
    (status = 'active' AND closure_reason IS NULL) OR
    (status IN ('sold', 'partial') AND closure_reason IS NOT NULL)
);

-- Step 7: Verify the changes
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE 'Migration completed. Verifying changes:';

    -- Check new columns in user_smallcase_investments
    FOR rec IN
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_smallcase_investments'
        AND column_name IN ('closed_at', 'exit_price', 'exit_value', 'realized_pnl', 'closure_reason')
        ORDER BY column_name
    LOOP
        RAISE NOTICE 'user_smallcase_investments.%: % (nullable: %)',
                     rec.column_name, rec.data_type, rec.is_nullable;
    END LOOP;

    -- Check position history table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'user_smallcase_position_history'
    ) THEN
        RAISE NOTICE 'user_smallcase_position_history table created successfully';
    ELSE
        RAISE WARNING 'Failed to create user_smallcase_position_history table';
    END IF;

    -- Check transaction type constraint
    SELECT constraint_name INTO rec
    FROM information_schema.table_constraints
    WHERE table_name = 'trading_transactions'
    AND constraint_name = 'trading_transactions_transaction_type_check';

    IF rec.constraint_name IS NOT NULL THEN
        RAISE NOTICE 'Transaction type constraint updated successfully';
    ELSE
        RAISE WARNING 'Failed to update transaction type constraint';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- Migration Notes:
-- 1. Adds closure tracking fields to existing investments
-- 2. Creates position history table for closed positions
-- 3. Updates transaction types to support closure operations
-- 4. Adds proper indexing for performance
-- 5. Includes data validation constraints
-- 6. All changes are backward compatible
-- =====================================================