-- Migration 08: Add Regional Smallcase Support
-- Adds region and market columns to support US and India smallcases

-- Add region and market columns to assets table
ALTER TABLE assets
ADD COLUMN IF NOT EXISTS region VARCHAR(5) DEFAULT 'IN',
ADD COLUMN IF NOT EXISTS market_cap BIGINT,
ADD COLUMN IF NOT EXISTS sector VARCHAR(100);

-- Add region and supported_brokers columns to smallcases table
ALTER TABLE smallcases
ADD COLUMN IF NOT EXISTS region VARCHAR(5) DEFAULT 'IN',
ADD COLUMN IF NOT EXISTS supported_brokers TEXT[] DEFAULT ARRAY['zerodha'],
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'INR';

-- Update existing assets to have region 'IN' for India
UPDATE assets SET region = 'IN', currency = 'INR' WHERE currency IS NULL OR currency = 'USD';

-- Update existing smallcases to have region 'IN' for India
UPDATE smallcases SET region = 'IN', currency = 'INR', supported_brokers = ARRAY['zerodha'] WHERE region IS NULL;

-- Add indexes for efficient querying by region
CREATE INDEX IF NOT EXISTS idx_assets_region ON assets(region);
CREATE INDEX IF NOT EXISTS idx_assets_region_active ON assets(region, is_active);
CREATE INDEX IF NOT EXISTS idx_smallcases_region ON smallcases(region);
CREATE INDEX IF NOT EXISTS idx_smallcases_region_active ON smallcases(region, is_active);

-- Add check constraints for valid regions
ALTER TABLE assets ADD CONSTRAINT check_assets_region CHECK (region IN ('US', 'IN'));
ALTER TABLE smallcases ADD CONSTRAINT check_smallcases_region CHECK (region IN ('US', 'IN'));

-- Add check constraints for valid currencies
ALTER TABLE assets ADD CONSTRAINT check_assets_currency CHECK (currency IN ('USD', 'INR'));
ALTER TABLE smallcases ADD CONSTRAINT check_smallcases_currency CHECK (currency IN ('USD', 'INR'));

-- Add comments for documentation
COMMENT ON COLUMN assets.region IS 'Market region: US for United States, IN for India';
COMMENT ON COLUMN assets.market_cap IS 'Market capitalization in local currency';
COMMENT ON COLUMN assets.sector IS 'Business sector classification';
COMMENT ON COLUMN smallcases.region IS 'Target market region: US for United States, IN for India';
COMMENT ON COLUMN smallcases.supported_brokers IS 'Array of supported broker types (alpaca, zerodha)';
COMMENT ON COLUMN smallcases.currency IS 'Base currency for the smallcase (USD, INR)';

-- Create view for regional assets
CREATE OR REPLACE VIEW regional_assets AS
SELECT
    a.*,
    CASE
        WHEN a.region = 'US' THEN 'NASDAQ/NYSE'
        WHEN a.region = 'IN' THEN 'NSE/BSE'
        ELSE a.exchange
    END as display_exchange,
    CASE
        WHEN a.region = 'US' THEN ARRAY['alpaca']
        WHEN a.region = 'IN' THEN ARRAY['zerodha']
        ELSE ARRAY[]::TEXT[]
    END as compatible_brokers
FROM assets a
WHERE a.is_active = true;

-- Create view for regional smallcases
CREATE OR REPLACE VIEW regional_smallcases AS
SELECT
    s.*,
    COUNT(sc.id) as constituent_count,
    SUM(sc.weight_percentage) as total_weight,
    CASE
        WHEN s.region = 'US' THEN 'United States'
        WHEN s.region = 'IN' THEN 'India'
        ELSE s.region
    END as region_name
FROM smallcases s
LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
WHERE s.is_active = true
GROUP BY s.id, s.name, s.description, s.category, s.theme, s.risk_level,
         s.expected_return_min, s.expected_return_max, s.minimum_investment,
         s.is_active, s.created_by, s.created_at, s.updated_at, s.strategy_type,
         s.expected_return_1y, s.expected_return_3y, s.expected_return_5y,
         s.volatility, s.sharpe_ratio, s.max_drawdown, s.expense_ratio,
         s.region, s.supported_brokers, s.currency;

COMMENT ON VIEW regional_assets IS 'View of assets with regional and broker compatibility information';
COMMENT ON VIEW regional_smallcases IS 'View of smallcases with regional filtering and constituent statistics';