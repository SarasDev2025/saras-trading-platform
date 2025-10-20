-- Backfill source_type and source_id for existing algorithm positions
-- This migration associates portfolio holdings with their originating algorithms
-- based on transaction notes that contain "Algorithm: <uuid>"

-- =====================================================
-- Step 1: Backfill algorithm positions
-- =====================================================
-- Update holdings where transactions have "Algorithm:" in notes

UPDATE portfolio_holdings ph
SET
    source_type = 'algorithm',
    source_id = (
        -- Extract algorithm_id from transaction notes
        SELECT (regexp_match(tt.notes, 'Algorithm: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'))[1]::uuid
        FROM trading_transactions tt
        WHERE tt.portfolio_id = ph.portfolio_id
        AND tt.asset_id = ph.asset_id
        AND tt.notes LIKE 'Algorithm:%'
        ORDER BY tt.transaction_date DESC
        LIMIT 1
    )
WHERE ph.source_type IS NULL
AND EXISTS (
    SELECT 1 FROM trading_transactions tt
    WHERE tt.portfolio_id = ph.portfolio_id
    AND tt.asset_id = ph.asset_id
    AND tt.notes LIKE 'Algorithm:%'
);

-- =====================================================
-- Step 2: Backfill smallcase positions (if any exist)
-- =====================================================
-- Update holdings where transactions have smallcase metadata
-- (This will be populated if smallcase service uses execution_metadata)

UPDATE portfolio_holdings ph
SET
    source_type = 'smallcase',
    source_id = (
        SELECT (regexp_match(tt.notes, 'Smallcase: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'))[1]::uuid
        FROM trading_transactions tt
        WHERE tt.portfolio_id = ph.portfolio_id
        AND tt.asset_id = ph.asset_id
        AND tt.notes LIKE 'Smallcase:%'
        ORDER BY tt.transaction_date DESC
        LIMIT 1
    )
WHERE ph.source_type IS NULL
AND EXISTS (
    SELECT 1 FROM trading_transactions tt
    WHERE tt.portfolio_id = ph.portfolio_id
    AND tt.asset_id = ph.asset_id
    AND tt.notes LIKE 'Smallcase:%'
);

-- =====================================================
-- Step 3: Mark remaining positions as manual
-- =====================================================
-- Any holdings that still don't have a source are manual trades

UPDATE portfolio_holdings
SET source_type = 'manual'
WHERE source_type IS NULL;

-- =====================================================
-- Verification queries (for debugging)
-- =====================================================
-- Uncomment these to check the results:

-- SELECT
--     ph.source_type,
--     COUNT(*) as count,
--     SUM(ph.current_value) as total_value
-- FROM portfolio_holdings ph
-- WHERE ph.quantity > 0
-- GROUP BY ph.source_type
-- ORDER BY ph.source_type;

-- SELECT
--     ph.source_type,
--     ta.name as algorithm_name,
--     a.symbol,
--     ph.quantity,
--     ph.current_value
-- FROM portfolio_holdings ph
-- JOIN assets a ON ph.asset_id = a.id
-- LEFT JOIN trading_algorithms ta ON ph.source_id = ta.id AND ph.source_type = 'algorithm'
-- WHERE ph.source_type = 'algorithm'
-- AND ph.quantity > 0
-- ORDER BY ta.name, a.symbol
-- LIMIT 20;
