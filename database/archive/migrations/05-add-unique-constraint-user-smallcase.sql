-- =====================================================
-- 05-ADD-UNIQUE-CONSTRAINT-USER-SMALLCASE.SQL
-- Add unique constraint to prevent duplicate active investments
-- =====================================================

-- This migration prevents users from having multiple active investments
-- for the same smallcase, which violates business logic

BEGIN;

-- Step 1: Check for existing duplicates
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT user_id, smallcase_id
        FROM user_smallcase_investments
        WHERE status = 'active'
        GROUP BY user_id, smallcase_id
        HAVING COUNT(*) > 1
    ) duplicates;

    RAISE NOTICE 'Found % duplicate active investment combinations', duplicate_count;
END $$;

-- Step 2: Clean up duplicates by keeping only the most recent investment
WITH ranked_investments AS (
    SELECT id,
           user_id,
           smallcase_id,
           invested_at,
           ROW_NUMBER() OVER (
               PARTITION BY user_id, smallcase_id
               ORDER BY invested_at DESC, created_at DESC
           ) as rn
    FROM user_smallcase_investments
    WHERE status = 'active'
)
UPDATE user_smallcase_investments
SET status = 'duplicate_removed',
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (
    SELECT id FROM ranked_investments WHERE rn > 1
);

-- Step 3: Report how many duplicates were cleaned up
DO $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cleaned_count
    FROM user_smallcase_investments
    WHERE status = 'duplicate_removed';

    RAISE NOTICE 'Marked % duplicate investments as removed', cleaned_count;
END $$;

-- Step 4: Add unique constraint to prevent future duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_smallcase_active_unique
ON user_smallcase_investments (user_id, smallcase_id)
WHERE status = 'active';

-- Step 5: Verify the constraint was added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_user_smallcase_active_unique'
    ) THEN
        RAISE NOTICE 'Unique constraint successfully created: idx_user_smallcase_active_unique';
    ELSE
        RAISE WARNING 'Failed to create unique constraint';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- Migration Notes:
-- 1. Keeps the most recent investment when duplicates exist
-- 2. Marks older duplicates as 'duplicate_removed' instead of deleting
-- 3. Prevents future duplicate active investments via unique index
-- 4. Uses partial index (WHERE status = 'active') for performance
-- =====================================================