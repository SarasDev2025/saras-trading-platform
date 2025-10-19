-- Migration: Add source tracking to portfolio_holdings
-- Description: Add source_type and source_id fields to track where positions came from
-- Created: 2025-01-19

-- Add source_type column (smallcase, algorithm, or manual)
ALTER TABLE portfolio_holdings
ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) CHECK (source_type IN ('smallcase', 'algorithm', 'manual'));

-- Add source_id column (references the smallcase_id, algorithm_id, or NULL for manual)
ALTER TABLE portfolio_holdings
ADD COLUMN IF NOT EXISTS source_id UUID;

-- Set default value for existing rows to 'manual' with NULL source_id
UPDATE portfolio_holdings
SET source_type = 'manual', source_id = NULL
WHERE source_type IS NULL;

-- Create index for faster filtering by source_type
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_source_type ON portfolio_holdings(source_type);

-- Create index for faster lookups by source_id
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_source_id ON portfolio_holdings(source_id);

-- Add comment to document the new fields
COMMENT ON COLUMN portfolio_holdings.source_type IS 'Origin of the position: smallcase, algorithm, or manual';
COMMENT ON COLUMN portfolio_holdings.source_id IS 'ID of the source (smallcase_investment_id, algorithm_id, or NULL for manual trades)';
