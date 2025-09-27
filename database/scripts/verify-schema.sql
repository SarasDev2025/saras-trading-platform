-- =====================================================
-- VERIFY-SCHEMA.SQL
-- Verify that database schema matches code requirements
-- =====================================================

-- This script checks for all columns that the smallcase apply feature needs

\echo 'Verifying database schema for smallcase apply feature...'
\echo ''

-- Check user_smallcase_investments table
\echo 'Checking user_smallcase_investments table:'
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'user_smallcase_investments'
AND column_name IN ('execution_mode', 'broker_connection_id', 'auto_rebalance', 'last_rebalanced_at')
ORDER BY column_name;

\echo ''
\echo 'Checking trading_transactions table:'
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'trading_transactions'
AND column_name IN ('order_type', 'notes', 'external_transaction_id')
ORDER BY column_name;

\echo ''
\echo 'Checking smallcase_execution_orders table:'
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'smallcase_execution_orders'
AND column_name IN ('details', 'metadata')
ORDER BY column_name;

\echo ''
\echo 'Checking for required indexes:'
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('trading_transactions', 'smallcase_execution_orders', 'user_smallcase_investments')
AND indexname LIKE '%external%'
ORDER BY tablename, indexname;

\echo ''
\echo 'Schema verification complete!'