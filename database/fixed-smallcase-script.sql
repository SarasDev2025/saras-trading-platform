-- Defensive Dividend Strategy
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Defensive Dividend Strategy', 'ITC', 25.0, 'Consistent 4%+ dividend yield'),
    ('Defensive Dividend Strategy', 'ONGC', 20.0, 'High dividend yield from energy major'),
    ('Defensive Dividend Strategy', 'NTPC', 18.0, 'Stable utility with regular dividends'),
    ('Defensive Dividend Strategy', 'HINDUNILVR', 15.0, 'Stable FMCG with modest but consistent dividends'),
    ('Defensive Dividend Strategy', 'VEDL', 12.0, 'High dividend yield from metals major'),
    ('Defensive Dividend Strategy', 'TATASTEEL', 10.0, 'Cyclical dividends but high when profitable')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Banking & NBFC Focus
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Banking & NBFC Focus', 'HDFCBANK', 30.0, 'Best-in-class private bank'),
    ('Banking & NBFC Focus', 'ICICIBANK', 25.0, 'Strong retail franchise and digital banking'),
    ('Banking & NBFC Focus', 'KOTAKBANK', 20.0, 'Premium bank with wealth management focus'),
    ('Banking & NBFC Focus', 'BAJFINANCE', 25.0, 'Leading NBFC with strong growth trajectory')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- IT Export Leaders
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('IT Export Leaders', 'TCS', 35.0, 'Largest IT services with global presence'),
    ('IT Export Leaders', 'INFY', 30.0, 'Digital transformation and cloud leader'),
    ('IT Export Leaders', 'WIPRO', 20.0, 'Strong in consulting and digital services'),
    ('IT Export Leaders', 'HCLTECH', 15.0, 'Product engineering and IP partnership model')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Infrastructure & Capex Theme
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Infrastructure & Capex Theme', 'LT', 30.0, 'Infrastructure and defense conglomerate'),
    ('Infrastructure & Capex Theme', 'ULTRACEMCO', 25.0, 'Cement leader for infrastructure projects'),
    ('Infrastructure & Capex Theme', 'TATASTEEL', 20.0, 'Steel demand from infrastructure'),
    ('Infrastructure & Capex Theme', 'HINDALCO', 15.0, 'Aluminum for infrastructure and auto'),
    ('Infrastructure & Capex Theme', 'JSWSTEEL', 10.0, 'Steel major with coastal advantage')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Consumer Staples Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Consumer Staples Portfolio', 'HINDUNILVR', 40.0, 'FMCG leader with strong brand portfolio'),
    ('Consumer Staples Portfolio', 'NESTLEIND', 30.0, 'Premium food and beverages'),
    ('Consumer Staples Portfolio', 'ITC', 30.0, 'Diversified FMCG with cigarettes and foods')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Energy & Power Utilities
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Energy & Power Utilities', 'RELIANCE', 40.0, 'Integrated oil & gas with petrochemicals'),
    ('Energy & Power Utilities', 'ONGC', 25.0, 'Upstream oil & gas exploration'),
    ('Energy & Power Utilities', 'NTPC', 35.0, 'Largest power generation utility')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- High Beta Momentum Strategy
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('High Beta Momentum Strategy', 'TATAMOTORS', 25.0, 'High beta auto stock with EV play'),
    ('High Beta Momentum Strategy', 'BAJFINANCE', 20.0, 'High growth NBFC with market sensitivity'),
    ('High Beta Momentum Strategy', 'VEDL', 20.0, 'Commodity play with high volatility'),
    ('High Beta Momentum Strategy', 'JSWSTEEL', 15.0, 'Steel sector momentum play'),
    ('High Beta Momentum Strategy', 'M&M', 10.0, 'Auto and farm equipment cyclical'),
    ('High Beta Momentum Strategy', 'HINDALCO', 10.0, 'Metals and commodity exposure')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- All Weather Balanced
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('All Weather Balanced', 'HDFCBANK', 15.0, 'Stable banking exposure'),
    ('All Weather Balanced', 'TCS', 12.0, 'IT services for stability'),
    ('All Weather Balanced', 'RELIANCE', 13.0, 'Energy and telecom diversification'),
    ('All Weather Balanced', 'HINDUNILVR', 10.0, 'Defensive FMCG'),
    ('All Weather Balanced', 'LT', 8.0, 'Infrastructure exposure'),
    ('All Weather Balanced', 'SUNPHARMA', 8.0, 'Healthcare sector representation'),
    ('All Weather Balanced', 'MARUTI', 7.0, 'Auto sector exposure'),
    ('All Weather Balanced', 'ICICIBANK', 8.0, 'Additional banking exposure'),
    ('All Weather Balanced', 'ITC', 7.0, 'High dividend yield component'),
    ('All Weather Balanced', 'BHARTIARTL', 6.0, 'Telecom sector exposure'),
    ('All Weather Balanced', 'NTPC', 6.0, 'Utility sector stability')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Create Professional Views
-- =====================================================

-- Professional Portfolio Analytics View
CREATE OR REPLACE VIEW v_professional_smallcases AS
SELECT 
    s.id,
    s.name,
    s.description,
    s.strategy_type,
    s.category,
    s.risk_level,
    s.expected_return_1y,
    s.expected_return_3y,
    s.expected_return_5y,
    s.volatility,
    s.sharpe_ratio,
    s.max_drawdown,
    s.minimum_investment,
    s.expense_ratio,
    COUNT(sc.id) as constituent_count,
    ROUND(AVG(a.pe_ratio), 2) as portfolio_pe,
    ROUND(AVG(a.pb_ratio), 2) as portfolio_pb,
    ROUND(AVG(a.dividend_yield), 2) as portfolio_dividend_yield,
    ROUND(AVG(a.beta), 3) as portfolio_beta,
    COALESCE(SUM(a.current_price * sc.weight_percentage / 100), 100.0) as current_nav
FROM smallcases s
LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
LEFT JOIN assets a ON sc.asset_id = a.id
WHERE s.is_active = true
GROUP BY s.id, s.name, s.description, s.strategy_type, s.category, s.risk_level,
         s.expected_return_1y, s.expected_return_3y, s.expected_return_5y, s.volatility,
         s.sharpe_ratio, s.max_drawdown, s.minimum_investment, s.expense_ratio
ORDER BY s.sharpe_ratio DESC;

-- Sector Allocation View
CREATE OR REPLACE VIEW v_smallcase_sector_allocation AS
SELECT 
    s.name as smallcase_name,
    s.id as smallcase_id,
    a.sector,
    COUNT(sc.id) as stock_count,
    ROUND(SUM(sc.weight_percentage), 2) as sector_weight,
    ROUND(AVG(a.current_price), 2) as avg_price,
    ROUND(SUM(a.market_cap * sc.weight_percentage / 100), 0) as weighted_market_cap
FROM smallcases s
JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
JOIN assets a ON sc.asset_id = a.id
WHERE s.is_active = true
GROUP BY s.name, s.id, a.sector
ORDER BY s.name, sector_weight DESC;

-- Risk Analytics View
CREATE OR REPLACE VIEW v_smallcase_risk_metrics AS
SELECT 
    s.id as smallcase_id,
    s.name as smallcase_name,
    s.risk_level,
    s.volatility,
    s.max_drawdown,
    ROUND(AVG(a.beta), 3) as portfolio_beta,
    COUNT(DISTINCT a.sector) as sector_diversification,
    ROUND(MAX(sc.weight_percentage), 2) as max_single_position,
    ROUND(AVG(sc.weight_percentage), 2) as avg_position_size,
    CASE 
        WHEN COUNT(sc.id) >= 15 THEN 'WELL_DIVERSIFIED'
        WHEN COUNT(sc.id) >= 8 THEN 'MODERATELY_DIVERSIFIED'
        ELSE 'CONCENTRATED'
    END as diversification_level
FROM smallcases s
JOIN smallcase_constituents sc ON s.id = sc.smallcase_id AND sc.is_active = true
JOIN assets a ON sc.asset_id = a.id
WHERE s.is_active = true
GROUP BY s.id, s.name, s.risk_level, s.volatility, s.max_drawdown
ORDER BY portfolio_beta DESC;

-- Insert Sample Performance Data
-- =====================================================
INSERT INTO smallcase_performance (smallcase_id, date, nav, total_return_1d, total_return_1w, total_return_1m, total_return_1y, alpha)
SELECT 
    s.id,
    CURRENT_DATE,
    100.0 + (RANDOM() * 20 - 10), -- Random NAV between 90-110
    (RANDOM() * 4 - 2), -- Daily return between -2% to +2%
    (RANDOM() * 10 - 5), -- Weekly return between -5% to +5%
    (RANDOM() * 20 - 10), -- Monthly return between -10% to +10%
    s.expected_return_1y + (RANDOM() * 10 - 5), -- Annual return around expected with variance
    (RANDOM() * 8 - 4) -- Alpha between -4% to +4%
FROM smallcases s
WHERE s.is_active = true AND s.created_by = 'SYSTEM';

-- Create Indexes for Performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_smallcases_strategy_type ON smallcases(strategy_type);
CREATE INDEX IF NOT EXISTS idx_smallcases_risk_level ON smallcases(risk_level);
CREATE INDEX IF NOT EXISTS idx_smallcases_sharpe_ratio ON smallcases(sharpe_ratio);
CREATE INDEX IF NOT EXISTS idx_assets_sector ON assets(sector);
CREATE INDEX IF NOT EXISTS idx_assets_pe_ratio ON assets(pe_ratio);
CREATE INDEX IF NOT EXISTS idx_constituents_weight ON smallcase_constituents(weight_percentage);
CREATE INDEX IF NOT EXISTS idx_performance_date ON smallcase_performance(date);

-- Professional Query Examples & Analytics
-- =====================================================

-- Query 1: Top performing strategies by risk-adjusted returns
SELECT 
    strategy_type,
    COUNT(*) as fund_count,
    ROUND(AVG(expected_return_1y), 2) as avg_return,
    ROUND(AVG(sharpe_ratio), 3) as avg_sharpe,
    ROUND(AVG(volatility), 2) as avg_volatility,
    ROUND(AVG(minimum_investment), 0) as avg_min_investment
FROM smallcases 
WHERE is_active = true AND created_by = 'SYSTEM'
GROUP BY strategy_type
ORDER BY avg_sharpe DESC;

-- Query 2: Best funds by risk categories
SELECT 
    risk_level,
    COUNT(*) as fund_count,
    ROUND(AVG(expected_return_1y), 2) as avg_return,
    ROUND(AVG(volatility), 2) as avg_volatility,
    ROUND(AVG(max_drawdown), 2) as avg_max_drawdown,
    MIN(minimum_investment) as min_investment
FROM smallcases 
WHERE is_active = true AND created_by = 'SYSTEM'
GROUP BY risk_level
ORDER BY avg_return DESC;

-- Query 3: Sector diversification across smallcases
SELECT 
    sector,
    COUNT(DISTINCT smallcase_id) as funds_invested,
    ROUND(AVG(sector_weight), 2) as avg_allocation,
    ROUND(SUM(weighted_market_cap)/1000000000, 2) as total_market_cap_bn
FROM v_smallcase_sector_allocation
GROUP BY sector
ORDER BY funds_invested DESC, avg_allocation DESC;

-- Query 4: Professional fund recommendations by investment amount
SELECT 
    CASE 
        WHEN minimum_investment <= 150000 THEN 'ENTRY_LEVEL (≤1.5L)'
        WHEN minimum_investment <= 300000 THEN 'MODERATE (1.5L-3L)'
        WHEN minimum_investment <= 500000 THEN 'HIGH (3L-5L)'
        ELSE 'PREMIUM (>5L)'
    END as investment_tier,
    name,
    strategy_type,
    risk_level,
    ROUND(expected_return_1y, 2) as expected_return,
    ROUND(sharpe_ratio, 3) as sharpe_ratio,
    minimum_investment
FROM smallcases 
WHERE is_active = true AND created_by = 'SYSTEM'
ORDER BY 
    CASE 
        WHEN minimum_investment <= 150000 THEN 1
        WHEN minimum_investment <= 300000 THEN 2
        WHEN minimum_investment <= 500000 THEN 3
        ELSE 4
    END,
    sharpe_ratio DESC;

-- Final Summary
-- =====================================================
SELECT 
    'Professional Trading Platform Setup Complete!' as status,
    (SELECT COUNT(*) FROM smallcases WHERE is_active = true AND created_by = 'SYSTEM') as total_smallcases,
    (SELECT COUNT(*) FROM assets WHERE is_active = true) as total_assets,
    (SELECT COUNT(DISTINCT strategy_type) FROM smallcases WHERE created_by = 'SYSTEM') as strategy_types,
    (SELECT COUNT(DISTINCT sector) FROM assets) as sectors_covered,
    (SELECT ROUND(AVG(minimum_investment), 0) FROM smallcases WHERE created_by = 'SYSTEM') as avg_min_investment,
    (SELECT ROUND(AVG(expected_return_1y), 2) FROM smallcases WHERE created_by = 'SYSTEM') as avg_expected_return; =====================================================
-- FIXED: Professional Trading Platform Smallcases
-- Compatible with existing database schema
-- =====================================================

-- Add new columns to existing tables (safe approach)
-- =====================================================

-- Enhance assets table
ALTER TABLE assets ADD COLUMN IF NOT EXISTS pe_ratio DECIMAL(8,2);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS pb_ratio DECIMAL(8,2);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS dividend_yield DECIMAL(5,2);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS beta DECIMAL(6,3);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS industry VARCHAR(150);

-- Enhance smallcases table
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(100) DEFAULT 'VALUE';
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS expected_return_1y DECIMAL(6,2);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS expected_return_3y DECIMAL(6,2);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS expected_return_5y DECIMAL(6,2);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS volatility DECIMAL(6,2);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS sharpe_ratio DECIMAL(6,3);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS max_drawdown DECIMAL(6,2);
ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS expense_ratio DECIMAL(5,3);

-- Enhance constituents table
ALTER TABLE smallcase_constituents ADD COLUMN IF NOT EXISTS rationale TEXT;

-- Performance tracking table
CREATE TABLE IF NOT EXISTS smallcase_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    smallcase_id UUID REFERENCES smallcases(id),
    date DATE NOT NULL,
    nav DECIMAL(15,4) NOT NULL,
    total_return_1d DECIMAL(8,4),
    total_return_1w DECIMAL(8,4),
    total_return_1m DECIMAL(8,4),
    total_return_1y DECIMAL(8,4),
    alpha DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(smallcase_id, date)
);

-- Clear only system-created data
-- =====================================================
DELETE FROM smallcase_constituents 
WHERE smallcase_id IN (SELECT id FROM smallcases WHERE created_by = 'SYSTEM');
DELETE FROM smallcases WHERE created_by = 'SYSTEM';

-- Delete existing professional assets to avoid conflicts
DELETE FROM assets WHERE symbol IN (
    'TCS', 'INFY', 'WIPRO', 'HCLTECH', 'HDFCBANK', 'ICICIBANK', 
    'KOTAKBANK', 'BAJFINANCE', 'HINDUNILVR', 'NESTLEIND', 'ITC',
    'RELIANCE', 'ONGC', 'NTPC', 'SUNPHARMA', 'DRREDDY', 'CIPLA',
    'MARUTI', 'TATAMOTORS', 'M&M', 'LT', 'ULTRACEMCO', 'TATASTEEL',
    'BHARTIARTL', 'HINDALCO', 'JSWSTEEL', 'VEDL'
);

-- Insert Professional Assets
-- =====================================================
INSERT INTO assets (symbol, name, asset_type, exchange, current_price, market_cap, pe_ratio, pb_ratio, dividend_yield, beta, sector, industry) VALUES

-- Technology Stocks
('TCS', 'Tata Consultancy Services', 'STOCK', 'NSE', 3650.50, 1320000000000, 28.5, 12.4, 1.8, 0.85, 'Information Technology', 'IT Services'),
('INFY', 'Infosys Limited', 'STOCK', 'NSE', 1420.75, 590000000000, 25.2, 8.1, 2.1, 0.78, 'Information Technology', 'IT Services'),
('WIPRO', 'Wipro Limited', 'STOCK', 'NSE', 385.20, 210000000000, 22.8, 3.2, 1.5, 0.82, 'Information Technology', 'IT Services'),
('HCLTECH', 'HCL Technologies', 'STOCK', 'NSE', 1485.60, 400000000000, 21.5, 6.8, 1.9, 0.90, 'Information Technology', 'IT Services'),

-- Banking Stocks
('HDFCBANK', 'HDFC Bank Limited', 'STOCK', 'NSE', 1545.60, 1180000000000, 18.5, 2.8, 1.2, 0.95, 'Financial Services', 'Private Sector Bank'),
('ICICIBANK', 'ICICI Bank Limited', 'STOCK', 'NSE', 1085.40, 760000000000, 16.8, 2.1, 0.8, 1.12, 'Financial Services', 'Private Sector Bank'),
('KOTAKBANK', 'Kotak Mahindra Bank', 'STOCK', 'NSE', 1720.90, 340000000000, 20.2, 2.5, 0.6, 1.05, 'Financial Services', 'Private Sector Bank'),
('BAJFINANCE', 'Bajaj Finance Limited', 'STOCK', 'NSE', 6850.75, 425000000000, 28.5, 4.8, 0.4, 1.25, 'Financial Services', 'NBFC'),

-- FMCG Stocks
('HINDUNILVR', 'Hindustan Unilever Ltd', 'STOCK', 'NSE', 2385.45, 560000000000, 58.2, 12.5, 1.4, 0.45, 'Fast Moving Consumer Goods', 'Personal Care'),
('NESTLEIND', 'Nestle India Limited', 'STOCK', 'NSE', 2195.80, 212000000000, 68.5, 15.8, 0.8, 0.35, 'Fast Moving Consumer Goods', 'Food Products'),
('ITC', 'ITC Limited', 'STOCK', 'NSE', 405.65, 510000000000, 25.8, 4.2, 4.5, 0.65, 'Fast Moving Consumer Goods', 'Tobacco & Cigarettes'),

-- Energy Stocks
('RELIANCE', 'Reliance Industries Ltd', 'STOCK', 'NSE', 2685.90, 1815000000000, 12.8, 1.5, 0.5, 1.15, 'Oil Gas & Consumable Fuels', 'Refineries'),
('ONGC', 'Oil & Natural Gas Corp', 'STOCK', 'NSE', 285.75, 359000000000, 8.5, 0.8, 5.2, 1.45, 'Oil Gas & Consumable Fuels', 'Oil Exploration'),
('NTPC', 'NTPC Limited', 'STOCK', 'NSE', 385.20, 374000000000, 12.5, 1.2, 3.8, 0.85, 'Utilities', 'Power Generation'),

-- Pharma Stocks
('SUNPHARMA', 'Sun Pharmaceutical Inds', 'STOCK', 'NSE', 1650.75, 395000000000, 35.8, 6.2, 0.6, 0.75, 'Healthcare', 'Pharmaceuticals'),
('DRREDDY', 'Dr Reddys Laboratories', 'STOCK', 'NSE', 1285.40, 214000000000, 18.5, 2.8, 0.8, 0.82, 'Healthcare', 'Pharmaceuticals'),
('CIPLA', 'Cipla Limited', 'STOCK', 'NSE', 1420.85, 115000000000, 28.2, 4.1, 1.2, 0.68, 'Healthcare', 'Pharmaceuticals'),

-- Auto Stocks
('MARUTI', 'Maruti Suzuki India Ltd', 'STOCK', 'NSE', 10850.75, 328000000000, 25.8, 3.8, 1.8, 1.22, 'Consumer Discretionary', 'Passenger Cars'),
('TATAMOTORS', 'Tata Motors Limited', 'STOCK', 'NSE', 785.60, 290000000000, 45.2, 2.1, 0.0, 1.85, 'Consumer Discretionary', 'Commercial Vehicles'),
('M&M', 'Mahindra & Mahindra', 'STOCK', 'NSE', 1485.90, 185000000000, 22.5, 2.8, 1.2, 1.35, 'Consumer Discretionary', 'Passenger Cars'),

-- Infrastructure Stocks
('LT', 'Larsen & Toubro Ltd', 'STOCK', 'NSE', 3485.75, 490000000000, 28.5, 4.2, 0.8, 1.15, 'Capital Goods', 'Construction & Engineering'),
('ULTRACEMCO', 'UltraTech Cement Ltd', 'STOCK', 'NSE', 10850.60, 310000000000, 38.5, 6.8, 0.6, 1.25, 'Construction Materials', 'Cement'),
('TATASTEEL', 'Tata Steel Limited', 'STOCK', 'NSE', 118.45, 145000000000, 45.2, 0.8, 8.5, 1.68, 'Materials', 'Steel'),

-- Telecom Stocks
('BHARTIARTL', 'Bharti Airtel Limited', 'STOCK', 'NSE', 1485.20, 865000000000, 68.5, 8.2, 0.4, 0.95, 'Telecommunication', 'Telecom Services'),

-- Metals Stocks
('HINDALCO', 'Hindalco Industries Ltd', 'STOCK', 'NSE', 485.70, 108000000000, 15.8, 1.8, 2.5, 1.45, 'Materials', 'Aluminium'),
('JSWSTEEL', 'JSW Steel Limited', 'STOCK', 'NSE', 785.30, 195000000000, 28.5, 1.5, 3.2, 1.55, 'Materials', 'Steel'),
('VEDL', 'Vedanta Limited', 'STOCK', 'NSE', 485.25, 175000000000, 12.5, 1.2, 18.5, 1.85, 'Materials', 'Diversified Metals & Mining');

-- Create Professional Smallcases
-- =====================================================
INSERT INTO smallcases (name, description, strategy_type, category, risk_level, 
                       expected_return_1y, expected_return_3y, expected_return_5y, volatility, 
                       sharpe_ratio, max_drawdown, minimum_investment, expense_ratio, created_by) VALUES

('Large Cap Value Fund', 
 'Fundamentally strong large-cap companies trading at attractive valuations with focus on dividend yield and sustainable business models.',
 'VALUE', 'Equity', 'CONSERVATIVE', 12.0, 14.0, 15.0, 15.5, 0.85, -12.0, 100000, 0.75, 'SYSTEM'),

('Growth Momentum Portfolio', 
 'High-growth companies with strong earnings momentum and market leadership in technology and consumer discretionary sectors.',
 'GROWTH', 'Equity', 'AGGRESSIVE', 18.0, 22.0, 20.0, 22.5, 0.92, -18.0, 250000, 1.25, 'SYSTEM'),

('Defensive Dividend Strategy', 
 'High dividend-yielding stocks from stable sectors with consistent dividend payment history and strong cash flows.',
 'DEFENSIVE', 'Equity', 'CONSERVATIVE', 10.0, 12.0, 13.0, 12.0, 0.78, -8.0, 150000, 0.65, 'SYSTEM'),

('Banking & NBFC Focus', 
 'Concentrated exposure to banking and financial services sector with mix of private banks and NBFCs.',
 'SECTORAL', 'Financial Services', 'MODERATE', 15.0, 18.0, 16.0, 20.0, 0.88, -15.0, 200000, 0.95, 'SYSTEM'),

('IT Export Leaders', 
 'Technology services companies with strong global presence benefiting from digital transformation.',
 'SECTORAL', 'Information Technology', 'MODERATE', 16.0, 19.0, 18.0, 18.5, 0.95, -14.0, 175000, 0.85, 'SYSTEM'),

('Infrastructure & Capex Theme', 
 'Companies benefiting from India infrastructure development cycle including construction, cement, steel, and engineering.',
 'SECTORAL', 'Infrastructure', 'AGGRESSIVE', 20.0, 25.0, 22.0, 25.0, 0.85, -22.0, 300000, 1.15, 'SYSTEM'),

('Consumer Staples Portfolio', 
 'Recession-proof FMCG companies with strong brand moats and consistent cash generation capabilities.',
 'DEFENSIVE', 'Consumer Staples', 'CONSERVATIVE', 11.0, 13.0, 14.0, 14.0, 0.82, -10.0, 125000, 0.70, 'SYSTEM'),

('Energy & Power Utilities', 
 'Diversified exposure to energy value chain including upstream, downstream, and power generation companies.',
 'SECTORAL', 'Energy', 'MODERATE', 14.0, 16.0, 15.0, 19.0, 0.75, -16.0, 180000, 0.90, 'SYSTEM'),

('High Beta Momentum Strategy', 
 'High beta stocks for aggressive investors seeking amplified market movements with momentum screening.',
 'MOMENTUM', 'High Beta', 'SPECULATIVE', 25.0, 30.0, 28.0, 35.0, 0.78, -30.0, 500000, 1.50, 'SYSTEM'),

('All Weather Balanced', 
 'Diversified portfolio across sectors and market caps designed for all market conditions with dynamic allocation.',
 'VALUE', 'Balanced', 'MODERATE', 13.0, 15.0, 16.0, 16.0, 0.90, -12.0, 100000, 0.80, 'SYSTEM');

-- Populate Smallcase Constituents
-- =====================================================

-- Large Cap Value Fund
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale) 
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Large Cap Value Fund', 'HDFCBANK', 18.0, 'Leading private bank with strong fundamentals'),
    ('Large Cap Value Fund', 'ITC', 15.0, 'High dividend yield with diverse portfolio'),
    ('Large Cap Value Fund', 'RELIANCE', 20.0, 'Undervalued conglomerate with oil & telecom'),
    ('Large Cap Value Fund', 'ONGC', 12.0, 'Government-backed energy major with high dividend'),
    ('Large Cap Value Fund', 'NTPC', 10.0, 'Stable power utility with consistent returns'),
    ('Large Cap Value Fund', 'TATASTEEL', 8.0, 'Cyclical play on infrastructure growth'),
    ('Large Cap Value Fund', 'VEDL', 7.0, 'Diversified mining with high dividend yield'),
    ('Large Cap Value Fund', 'LT', 10.0, 'Infrastructure leader with government backing')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Growth Momentum Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage, rationale)
SELECT s.id, a.id, weight_percentage, rationale
FROM smallcases s, assets a, (VALUES
    ('Growth Momentum Portfolio', 'TCS', 22.0, 'IT services leader with consistent growth'),
    ('Growth Momentum Portfolio', 'INFY', 18.0, 'Digital transformation beneficiary'),
    ('Growth Momentum Portfolio', 'HCLTECH', 15.0, 'Strong order book and margin expansion'),
    ('Growth Momentum Portfolio', 'BAJFINANCE', 20.0, 'NBFC with robust credit growth'),
    ('Growth Momentum Portfolio', 'MARUTI', 12.0, 'Auto leader with EV transition strategy'),
    ('Growth Momentum Portfolio', 'ULTRACEMCO', 13.0, 'Cement leader benefiting from infra boom')
) AS weights(smallcase_name, stock_symbol, weight_percentage, rationale)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

--