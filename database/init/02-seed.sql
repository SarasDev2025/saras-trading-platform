-- =====================================================
-- 02-SEED.SQL - Professional Smallcase Data
-- Run after setup to populate professional smallcases
-- =====================================================

-- Insert Professional Indian Assets
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, pb_ratio, dividend_yield, beta, industry) VALUES

-- Technology Stocks
('TCS', 'Tata Consultancy Services', 'stock', 'NSE', 'INR', 3650.50, 12.4, 1.8, 0.85, 'IT Services'),
('INFY', 'Infosys Limited', 'stock', 'NSE', 'INR', 1420.75, 8.1, 2.1, 0.78, 'IT Services'),
('WIPRO', 'Wipro Limited', 'stock', 'NSE', 'INR', 385.20, 3.2, 1.5, 0.82, 'IT Services'),
('HCLTECH', 'HCL Technologies', 'stock', 'NSE', 'INR', 1485.60, 6.8, 1.9, 0.90, 'IT Services'),

-- Banking Stocks
('HDFCBANK', 'HDFC Bank Limited', 'stock', 'NSE', 'INR', 1545.60, 2.8, 1.2, 0.95, 'Private Sector Bank'),
('ICICIBANK', 'ICICI Bank Limited', 'stock', 'NSE', 'INR', 1085.40, 2.1, 0.8, 1.12, 'Private Sector Bank'),
('KOTAKBANK', 'Kotak Mahindra Bank', 'stock', 'NSE', 'INR', 1720.90, 2.5, 0.6, 1.05, 'Private Sector Bank'),
('BAJFINANCE', 'Bajaj Finance Limited', 'stock', 'NSE', 'INR', 6850.75, 4.8, 0.4, 1.25, 'NBFC'),

-- FMCG Stocks
('HINDUNILVR', 'Hindustan Unilever Ltd', 'stock', 'NSE', 'INR', 2385.45, 12.5, 1.4, 0.45, 'Personal Care'),
('NESTLEIND', 'Nestle India Limited', 'stock', 'NSE', 'INR', 2195.80, 15.8, 0.8, 0.35, 'Food Products'),
('ITC', 'ITC Limited', 'stock', 'NSE', 'INR', 405.65, 4.2, 4.5, 0.65, 'Tobacco & Cigarettes'),

-- Energy Stocks
('RELIANCE', 'Reliance Industries Ltd', 'stock', 'NSE', 'INR', 2685.90, 1.5, 0.5, 1.15, 'Refineries'),
('ONGC', 'Oil & Natural Gas Corp', 'stock', 'NSE', 'INR', 285.75, 0.8, 5.2, 1.45, 'Oil Exploration'),
('NTPC', 'NTPC Limited', 'stock', 'NSE', 'INR', 385.20, 1.2, 3.8, 0.85, 'Power Generation'),

-- Pharma Stocks
('SUNPHARMA', 'Sun Pharmaceutical Inds', 'stock', 'NSE', 'INR', 1650.75, 6.2, 0.6, 0.75, 'Pharmaceuticals'),
('DRREDDY', 'Dr Reddys Laboratories', 'stock', 'NSE', 'INR', 1285.40, 2.8, 0.8, 0.82, 'Pharmaceuticals'),
('CIPLA', 'Cipla Limited', 'stock', 'NSE', 'INR', 1420.85, 4.1, 1.2, 0.68, 'Pharmaceuticals'),

-- Auto Stocks
('MARUTI', 'Maruti Suzuki India Ltd', 'stock', 'NSE', 'INR', 10850.75, 3.8, 1.8, 1.22, 'Passenger Cars'),
('TATAMOTORS', 'Tata Motors Limited', 'stock', 'NSE', 'INR', 785.60, 2.1, 0.0, 1.85, 'Commercial Vehicles'),
('M&M', 'Mahindra & Mahindra', 'stock', 'NSE', 'INR', 1485.90, 2.8, 1.2, 1.35, 'Passenger Cars'),

-- Infrastructure Stocks
('LT', 'Larsen & Toubro Ltd', 'stock', 'NSE', 'INR', 3485.75, 4.2, 0.8, 1.15, 'Construction & Engineering'),
('ULTRACEMCO', 'UltraTech Cement Ltd', 'stock', 'NSE', 'INR', 10850.60, 6.8, 0.6, 1.25, 'Cement'),
('TATASTEEL', 'Tata Steel Limited', 'stock', 'NSE', 'INR', 118.45, 0.8, 8.5, 1.68, 'Steel'),

-- Other Stocks
('BHARTIARTL', 'Bharti Airtel Limited', 'stock', 'NSE', 'INR', 1485.20, 8.2, 0.4, 0.95, 'Telecom Services'),
('HINDALCO', 'Hindalco Industries Ltd', 'stock', 'NSE', 'INR', 485.70, 1.8, 2.5, 1.45, 'Aluminium'),
('JSWSTEEL', 'JSW Steel Limited', 'stock', 'NSE', 'INR', 785.30, 1.5, 3.2, 1.55, 'Steel'),
('VEDL', 'Vedanta Limited', 'stock', 'NSE', 'INR', 485.25, 1.2, 18.5, 1.85, 'Diversified Metals & Mining')

ON CONFLICT (symbol) DO UPDATE SET
current_price = EXCLUDED.current_price,
pb_ratio = EXCLUDED.pb_ratio,
dividend_yield = EXCLUDED.dividend_yield,
beta = EXCLUDED.beta,
industry = EXCLUDED.industry,
updated_at = CURRENT_TIMESTAMP;

-- Insert Professional Smallcases
INSERT INTO smallcases (
    name, 
    description, 
    category, 
    theme, 
    risk_level, 
    expected_return_min, 
    expected_return_max, 
    minimum_investment,
    strategy_type,
    expected_return_1y,
    expected_return_3y,
    expected_return_5y,
    volatility,
    sharpe_ratio,
    max_drawdown,
    expense_ratio
) VALUES

('Large Cap Value Fund', 
 'Fundamentally strong large-cap companies trading at attractive valuations with focus on dividend yield.',
 'Equity', 'Value Investing', 'low', 10.0, 15.0, 100000.00,
 'VALUE', 12.0, 14.0, 15.0, 15.5, 0.85, -12.0, 0.75),

('Growth Momentum Portfolio', 
 'High-growth companies with strong earnings momentum in technology and financial services.',
 'Equity', 'Growth & Momentum', 'high', 15.0, 25.0, 250000.00,
 'GROWTH', 18.0, 22.0, 20.0, 22.5, 0.92, -18.0, 1.25),

('Banking & NBFC Focus', 
 'Concentrated exposure to banking and financial services sector.',
 'Financial Services', 'Banking Sector', 'medium', 12.0, 20.0, 200000.00,
 'SECTORAL', 15.0, 18.0, 16.0, 20.0, 0.88, -15.0, 0.95),

('IT Export Leaders', 
 'Technology services companies with strong global presence.',
 'Information Technology', 'IT Services', 'medium', 14.0, 22.0, 175000.00,
 'SECTORAL', 16.0, 19.0, 18.0, 18.5, 0.95, -14.0, 0.85),

('Infrastructure & Capex Theme', 
 'Companies benefiting from India infrastructure development.',
 'Infrastructure', 'Nation Building', 'high', 16.0, 28.0, 300000.00,
 'SECTORAL', 20.0, 25.0, 22.0, 25.0, 0.85, -22.0, 1.15),

('Consumer Staples Portfolio', 
 'Recession-proof FMCG companies with strong brand moats.',
 'Consumer Staples', 'Daily Essentials', 'low', 8.0, 16.0, 125000.00,
 'DEFENSIVE', 11.0, 13.0, 14.0, 14.0, 0.82, -10.0, 0.70),

('Energy & Power Utilities', 
 'Diversified exposure to energy value chain.',
 'Energy', 'Energy Security', 'medium', 12.0, 18.0, 180000.00,
 'SECTORAL', 14.0, 16.0, 15.0, 19.0, 0.75, -16.0, 0.90),

('High Beta Momentum Strategy', 
 'High beta stocks for aggressive investors.',
 'High Beta', 'Volatility Play', 'high', 18.0, 35.0, 500000.00,
 'MOMENTUM', 25.0, 30.0, 28.0, 35.0, 0.78, -30.0, 1.50),

('All Weather Balanced', 
 'Diversified portfolio across sectors for all market conditions.',
 'Balanced', 'All Weather', 'medium', 10.0, 18.0, 100000.00,
 'VALUE', 13.0, 15.0, 16.0, 16.0, 0.90, -12.0, 0.80),

('Defensive Dividend Strategy', 
 'High dividend-yielding stocks from stable sectors.',
 'Dividend', 'Income Generation', 'low', 8.0, 14.0, 150000.00,
 'DEFENSIVE', 10.0, 12.0, 13.0, 12.0, 0.78, -8.0, 0.65);

-- Insert Smallcase Constituents
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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Banking & NBFC Focus
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Banking & NBFC Focus', 'HDFCBANK', 30.0),
    ('Banking & NBFC Focus', 'ICICIBANK', 25.0),
    ('Banking & NBFC Focus', 'KOTAKBANK', 20.0),
    ('Banking & NBFC Focus', 'BAJFINANCE', 25.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- IT Export Leaders
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('IT Export Leaders', 'TCS', 35.0),
    ('IT Export Leaders', 'INFY', 30.0),
    ('IT Export Leaders', 'WIPRO', 20.0),
    ('IT Export Leaders', 'HCLTECH', 15.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Consumer Staples Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Consumer Staples Portfolio', 'HINDUNILVR', 40.0),
    ('Consumer Staples Portfolio', 'NESTLEIND', 30.0),
    ('Consumer Staples Portfolio', 'ITC', 30.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Energy & Power Utilities
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Energy & Power Utilities', 'RELIANCE', 40.0),
    ('Energy & Power Utilities', 'ONGC', 25.0),
    ('Energy & Power Utilities', 'NTPC', 35.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

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
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol;

-- Success message
SELECT 'Professional smallcases setup complete!' as status,
       (SELECT COUNT(*) FROM smallcases WHERE is_active = true) as total_smallcases,
       (SELECT COUNT(*) FROM assets WHERE is_active = true) as total_assets;
