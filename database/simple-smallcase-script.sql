-- =====================================================
-- SIMPLE WORKING SCRIPT - Professional Smallcases
-- Compatible with your existing database schema
-- =====================================================

-- Check current schema first
SELECT 'Starting smallcase setup...' as status;

-- Insert Professional Assets (stocks)
-- =====================================================
INSERT INTO assets (symbol, name, asset_type, exchange, current_price, market_cap, sector) VALUES
-- Technology Stocks
('TCS', 'Tata Consultancy Services', 'STOCK', 'NSE', 3650.50, 1320000000000, 'Information Technology'),
('INFY', 'Infosys Limited', 'STOCK', 'NSE', 1420.75, 590000000000, 'Information Technology'),
('WIPRO', 'Wipro Limited', 'STOCK', 'NSE', 385.20, 210000000000, 'Information Technology'),
('HCLTECH', 'HCL Technologies', 'STOCK', 'NSE', 1485.60, 400000000000, 'Information Technology'),

-- Banking Stocks
('HDFCBANK', 'HDFC Bank Limited', 'STOCK', 'NSE', 1545.60, 1180000000000, 'Financial Services'),
('ICICIBANK', 'ICICI Bank Limited', 'STOCK', 'NSE', 1085.40, 760000000000, 'Financial Services'),
('KOTAKBANK', 'Kotak Mahindra Bank', 'STOCK', 'NSE', 1720.90, 340000000000, 'Financial Services'),
('BAJFINANCE', 'Bajaj Finance Limited', 'STOCK', 'NSE', 6850.75, 425000000000, 'Financial Services'),

-- FMCG Stocks
('HINDUNILVR', 'Hindustan Unilever Ltd', 'STOCK', 'NSE', 2385.45, 560000000000, 'Fast Moving Consumer Goods'),
('NESTLEIND', 'Nestle India Limited', 'STOCK', 'NSE', 2195.80, 212000000000, 'Fast Moving Consumer Goods'),
('ITC', 'ITC Limited', 'STOCK', 'NSE', 405.65, 510000000000, 'Fast Moving Consumer Goods'),

-- Energy Stocks
('RELIANCE', 'Reliance Industries Ltd', 'STOCK', 'NSE', 2685.90, 1815000000000, 'Oil Gas & Consumable Fuels'),
('ONGC', 'Oil & Natural Gas Corp', 'STOCK', 'NSE', 285.75, 359000000000, 'Oil Gas & Consumable Fuels'),
('NTPC', 'NTPC Limited', 'STOCK', 'NSE', 385.20, 374000000000, 'Utilities'),

-- Pharma Stocks
('SUNPHARMA', 'Sun Pharmaceutical Inds', 'STOCK', 'NSE', 1650.75, 395000000000, 'Healthcare'),
('DRREDDY', 'Dr Reddys Laboratories', 'STOCK', 'NSE', 1285.40, 214000000000, 'Healthcare'),
('CIPLA', 'Cipla Limited', 'STOCK', 'NSE', 1420.85, 115000000000, 'Healthcare'),

-- Auto Stocks
('MARUTI', 'Maruti Suzuki India Ltd', 'STOCK', 'NSE', 10850.75, 328000000000, 'Consumer Discretionary'),
('TATAMOTORS', 'Tata Motors Limited', 'STOCK', 'NSE', 785.60, 290000000000, 'Consumer Discretionary'),
('M&M', 'Mahindra & Mahindra', 'STOCK', 'NSE', 1485.90, 185000000000, 'Consumer Discretionary'),

-- Infrastructure Stocks
('LT', 'Larsen & Toubro Ltd', 'STOCK', 'NSE', 3485.75, 490000000000, 'Capital Goods'),
('ULTRACEMCO', 'UltraTech Cement Ltd', 'STOCK', 'NSE', 10850.60, 310000000000, 'Construction Materials'),
('TATASTEEL', 'Tata Steel Limited', 'STOCK', 'NSE', 118.45, 145000000000, 'Materials'),

-- Telecom Stocks
('BHARTIARTL', 'Bharti Airtel Limited', 'STOCK', 'NSE', 1485.20, 865000000000, 'Telecommunication'),

-- Metals Stocks
('HINDALCO', 'Hindalco Industries Ltd', 'STOCK', 'NSE', 485.70, 108000000000, 'Materials'),
('JSWSTEEL', 'JSW Steel Limited', 'STOCK', 'NSE', 785.30, 195000000000, 'Materials'),
('VEDL', 'Vedanta Limited', 'STOCK', 'NSE', 485.25, 175000000000, 'Materials')

ON CONFLICT (symbol) DO UPDATE SET
current_price = EXCLUDED.current_price,
market_cap = EXCLUDED.market_cap,
sector = EXCLUDED.sector;

-- Create Professional Smallcases
-- =====================================================
INSERT INTO smallcases (name, description, category, risk_level, expected_return_min, expected_return_max, minimum_investment) VALUES

('Large Cap Value Fund', 
 'Fundamentally strong large-cap companies trading at attractive valuations with focus on dividend yield.',
 'Equity', 'LOW', 10.0, 15.0, 100000),

('Growth Momentum Portfolio', 
 'High-growth companies with strong earnings momentum in technology and financial services.',
 'Equity', 'HIGH', 15.0, 25.0, 250000),

('Banking & NBFC Focus', 
 'Concentrated exposure to banking and financial services sector with mix of private banks and NBFCs.',
 'Financial Services', 'MEDIUM', 12.0, 20.0, 200000),

('IT Export Leaders', 
 'Technology services companies with strong global presence benefiting from digital transformation.',
 'Information Technology', 'MEDIUM', 14.0, 22.0, 175000),

('Infrastructure & Capex Theme', 
 'Companies benefiting from India infrastructure development including construction, cement, and steel.',
 'Infrastructure', 'HIGH', 16.0, 28.0, 300000),

('Consumer Staples Portfolio', 
 'Recession-proof FMCG companies with strong brand moats and consistent cash generation.',
 'Consumer Staples', 'LOW', 8.0, 16.0, 125000),

('Energy & Power Utilities', 
 'Diversified exposure to energy value chain including oil, gas, and power generation companies.',
 'Energy', 'MEDIUM', 12.0, 18.0, 180000),

('High Beta Momentum Strategy', 
 'High beta stocks for aggressive investors seeking amplified market movements.',
 'High Beta', 'HIGH', 18.0, 35.0, 500000),

('All Weather Balanced', 
 'Diversified portfolio across sectors designed for all market conditions.',
 'Balanced', 'MEDIUM', 10.0, 18.0, 100000),

('Defensive Dividend Strategy', 
 'High dividend-yielding stocks from stable sectors with consistent payment history.',
 'Dividend', 'LOW', 8.0, 14.0, 150000)

ON CONFLICT (name) DO UPDATE SET
description = EXCLUDED.description,
minimum_investment = EXCLUDED.minimum_investment;

-- Create Smallcase Constituents
-- =====================================================

-- Large Cap Value Fund
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Large Cap Value Fund', 'HDFCBANK', 20.0),
    ('Large Cap Value Fund', 'ITC', 15.0),
    ('Large Cap Value Fund', 'RELIANCE', 25.0),
    ('Large Cap Value Fund', 'ONGC', 15.0),
    ('Large Cap Value Fund', 'NTPC', 12.0),
    ('Large Cap Value Fund', 'LT', 13.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Banking & NBFC Focus
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Banking & NBFC Focus', 'HDFCBANK', 30.0),
    ('Banking & NBFC Focus', 'ICICIBANK', 25.0),
    ('Banking & NBFC Focus', 'KOTAKBANK', 20.0),
    ('Banking & NBFC Focus', 'BAJFINANCE', 25.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- IT Export Leaders
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('IT Export Leaders', 'TCS', 35.0),
    ('IT Export Leaders', 'INFY', 30.0),
    ('IT Export Leaders', 'WIPRO', 20.0),
    ('IT Export Leaders', 'HCLTECH', 15.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Growth Momentum Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Growth Momentum Portfolio', 'TCS', 22.0),
    ('Growth Momentum Portfolio', 'INFY', 18.0),
    ('Growth Momentum Portfolio', 'HCLTECH', 15.0),
    ('Growth Momentum Portfolio', 'BAJFINANCE', 20.0),
    ('Growth Momentum Portfolio', 'MARUTI', 12.0),
    ('Growth Momentum Portfolio', 'ULTRACEMCO', 13.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Infrastructure & Capex Theme
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Infrastructure & Capex Theme', 'LT', 30.0),
    ('Infrastructure & Capex Theme', 'ULTRACEMCO', 25.0),
    ('Infrastructure & Capex Theme', 'TATASTEEL', 20.0),
    ('Infrastructure & Capex Theme', 'HINDALCO', 15.0),
    ('Infrastructure & Capex Theme', 'JSWSTEEL', 10.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Consumer Staples Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Consumer Staples Portfolio', 'HINDUNILVR', 40.0),
    ('Consumer Staples Portfolio', 'NESTLEIND', 30.0),
    ('Consumer Staples Portfolio', 'ITC', 30.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Energy & Power Utilities
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Energy & Power Utilities', 'RELIANCE', 40.0),
    ('Energy & Power Utilities', 'ONGC', 25.0),
    ('Energy & Power Utilities', 'NTPC', 35.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- High Beta Momentum Strategy
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('High Beta Momentum Strategy', 'TATAMOTORS', 25.0),
    ('High Beta Momentum Strategy', 'BAJFINANCE', 20.0),
    ('High Beta Momentum Strategy', 'VEDL', 20.0),
    ('High Beta Momentum Strategy', 'JSWSTEEL', 15.0),
    ('High Beta Momentum Strategy', 'M&M', 10.0),
    ('High Beta Momentum Strategy', 'HINDALCO', 10.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- All Weather Balanced
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('All Weather Balanced', 'HDFCBANK', 15.0),
    ('All Weather Balanced', 'TCS', 12.0),
    ('All Weather Balanced', 'RELIANCE', 13.0),
    ('All Weather Balanced', 'HINDUNILVR', 10.0),
    ('All Weather Balanced', 'LT', 8.0),
    ('All Weather Balanced', 'SUNPHARMA', 8.0),
    ('All Weather Balanced', 'MARUTI', 7.0),
    ('All Weather Balanced', 'ICICIBANK', 8.0),
    ('All Weather Balanced', 'ITC', 7.0),
    ('All Weather Balanced', 'BHARTIARTL', 6.0),
    ('All Weather Balanced', 'NTPC', 6.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Defensive Dividend Strategy
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Defensive Dividend Strategy', 'ITC', 25.0),
    ('Defensive Dividend Strategy', 'ONGC', 20.0),
    ('Defensive Dividend Strategy', 'NTPC', 18.0),
    ('Defensive Dividend Strategy', 'HINDUNILVR', 15.0),
    ('Defensive Dividend Strategy', 'VEDL', 12.0),
    ('Defensive Dividend Strategy', 'TATASTEEL', 10.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Final verification
SELECT 
    'Setup Complete!' as status,
    (SELECT COUNT(*) FROM smallcases WHERE is_active = true) as total_smallcases,
    (SELECT COUNT(*) FROM assets WHERE is_active = true) as total_assets,
    (SELECT COUNT(*) FROM smallcase_constituents WHERE is_active = true) as total_constituents;

-- Show the created smallcases
SELECT 
    name,
    category,
    risk_level,
    expected_return_min || '% - ' || expected_return_max || '%' as expected_returns,
    minimum_investment,
    (SELECT COUNT(*) FROM smallcase_constituents sc WHERE sc.smallcase_id = s.id) as stock_count
FROM smallcases s
WHERE is_active = true
ORDER BY minimum_investment;