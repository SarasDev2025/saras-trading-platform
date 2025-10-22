-- Migration: Add broker_connection_id to trading_transactions
-- Description: Add broker_connection_id field to track which broker connection was used for the transaction
-- Created: 2025-10-21

-- Add broker_connection_id column
ALTER TABLE trading_transactions
ADD COLUMN IF NOT EXISTS broker_connection_id UUID;

-- Add foreign key constraint (using DO block to check if exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_trading_transactions_broker_connection'
    ) THEN
        ALTER TABLE trading_transactions
        ADD CONSTRAINT fk_trading_transactions_broker_connection
        FOREIGN KEY (broker_connection_id)
        REFERENCES user_broker_connections(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Create index for faster filtering by broker_connection_id
CREATE INDEX IF NOT EXISTS idx_trading_transactions_broker_connection_id
ON trading_transactions(broker_connection_id);

-- Add comment to document the new field
COMMENT ON COLUMN trading_transactions.broker_connection_id IS 'ID of the broker connection used for this transaction (NULL for manual/paper trades)';
