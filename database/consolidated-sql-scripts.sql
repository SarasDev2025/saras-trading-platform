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

-- =====================================================
-- 03-DUMMY-DATA.SQL - Sample Users and Demo Data
-- Run after seed to add test users and sample transactions
-- =====================================================

-- Insert demo users (passwords are hashed version of 'password123')
INSERT INTO users (email, username, password_hash, first_name, last_name, email_verified, kyc_status) VALUES
('john.doe@example.com', 'johndoe', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'John', 'Doe', TRUE, 'approved'),
('jane.smith@example.com', 'janesmith', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Jane', 'Smith', TRUE, 'approved'),
('admin@saras-trading.com', 'admin', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Admin', 'User', TRUE, 'approved'),
('alice.johnson@example.com', 'alicejohnson', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Alice', 'Johnson', TRUE, 'pending')
ON CONFLICT (email) DO NOTHING;

-- Insert demo portfolios
INSERT INTO portfolios (user_id, name, description, cash_balance, total_value)
SELECT 
    id,
    'Default Portfolio',
    'Main investment portfolio',
    50000.00,
    50000.00
FROM users
ON CONFLICT DO NOTHING;

-- Insert additional US stocks for demo data
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, metadata) VALUES
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 175.50, '{"sector": "technology", "market_cap": "large"}'),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'USD', 2580.25, '{"sector": "technology", "market_cap": "large"}'),
('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD', 338.75, '{"sector": "technology", "market_cap": "large"}'),
('TSLA', 'Tesla, Inc.', 'stock', 'NASDAQ', 'USD', 185.30, '{"sector": "automotive", "market_cap": "large"}'),
('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 421.90, '{"sector": "technology", "market_cap": "large"}'),
('BTC', 'Bitcoin', 'crypto', 'Binance', 'USD', 43250.75, '{"type": "cryptocurrency"}'),
('ETH', 'Ethereum', 'crypto', 'Binance', 'USD', 2485.60, '{"type": "cryptocurrency"}')
ON CONFLICT (symbol) DO UPDATE SET
current_price = EXCLUDED.current_price,
updated_at = CURRENT_TIMESTAMP;

-- Insert sample trading transactions
DO $
DECLARE
    user_john_id UUID;
    user_jane_id UUID;
    portfolio_john_id UUID;
    portfolio_jane_id UUID;
    asset_tcs_id UUID;
    asset_hdfc_id UUID;
    asset_reliance_id UUID;
BEGIN
    -- Get user IDs
    SELECT id INTO user_john_id FROM users WHERE username = 'johndoe';
    SELECT id INTO user_jane_id FROM users WHERE username = 'janesmith';
    
    -- Get portfolio IDs
    SELECT id INTO portfolio_john_id FROM portfolios WHERE user_id = user_john_id;
    SELECT id INTO portfolio_jane_id FROM portfolios WHERE user_id = user_jane_id;
    
    -- Get asset IDs
    SELECT id INTO asset_tcs_id FROM assets WHERE symbol = 'TCS';
    SELECT id INTO asset_hdfc_id FROM assets WHERE symbol = 'HDFCBANK';
    SELECT id INTO asset_reliance_id FROM assets WHERE symbol = 'RELIANCE';
    
    -- Insert sample transactions for John
    INSERT INTO trading_transactions (user_id, portfolio_id, asset_id, transaction_type, quantity, price_per_unit, total_amount, fees, net_amount, status, transaction_date) VALUES
    (user_john_id::VARCHAR, portfolio_john_id, asset_tcs_id, 'buy', 10, 3500.00, 35000.00, 50.00, 35050.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (user_john_id::VARCHAR, portfolio_john_id, asset_hdfc_id, 'buy', 5, 1500.00, 7500.00, 25.00, 7525.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '25 days'),
    (user_john_id::VARCHAR, portfolio_john_id, asset_reliance_id, 'buy', 2, 2600.00, 5200.00, 20.00, 5220.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '20 days');
    
    -- Insert sample transactions for Jane
    INSERT INTO trading_transactions (user_id, portfolio_id, asset_id, transaction_type, quantity, price_per_unit, total_amount, fees, net_amount, status, transaction_date) VALUES
    (user_jane_id::VARCHAR, portfolio_jane_id, asset_tcs_id, 'buy', 5, 3600.00, 18000.00, 30.00, 18030.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '15 days'),
    (user_jane_id::VARCHAR, portfolio_jane_id, asset_hdfc_id, 'buy', 8, 1520.00, 12160.00, 35.00, 12195.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '12 days');
    
    -- Insert portfolio holdings based on transactions
    INSERT INTO portfolio_holdings (portfolio_id, asset_id, quantity, average_cost, total_cost) VALUES
    -- John's holdings
    (portfolio_john_id, asset_tcs_id, 10, 3500.00, 35000.00),
    (portfolio_john_id, asset_hdfc_id, 5, 1500.00, 7500.00),
    (portfolio_john_id, asset_reliance_id, 2, 2600.00, 5200.00),
    -- Jane's holdings
    (portfolio_jane_id, asset_tcs_id, 5, 3600.00, 18000.00),
    (portfolio_jane_id, asset_hdfc_id, 8, 1520.00, 12160.00);
    
    -- Update current values and PnL for holdings
    UPDATE portfolio_holdings 
    SET 
        current_value = quantity * (SELECT current_price FROM assets WHERE assets.id = portfolio_holdings.asset_id),
        unrealized_pnl = (quantity * (SELECT current_price FROM assets WHERE assets.id = portfolio_holdings.asset_id)) - total_cost;
    
    -- Update portfolio total values
    UPDATE portfolios 
    SET total_value = cash_balance + COALESCE((
        SELECT SUM(current_value) 
        FROM portfolio_holdings 
        WHERE portfolio_holdings.portfolio_id = portfolios.id
    ), 0);
END $;

-- Insert sample smallcase investments
INSERT INTO user_smallcase_investments (
    user_id, 
    portfolio_id, 
    smallcase_id, 
    investment_amount, 
    units_purchased, 
    purchase_price, 
    current_value, 
    unrealized_pnl, 
    status
) 
SELECT 
    '12345678-1234-1234-1234-123456789012',
    (SELECT id FROM portfolios WHERE user_id = (SELECT id FROM users WHERE username = 'johndoe') LIMIT 1),
    s.id,
    CASE 
        WHEN s.name = 'Large Cap Value Fund' THEN 100000.00
        WHEN s.name = 'IT Export Leaders' THEN 175000.00
        ELSE 50000.00
    END,
    CASE 
        WHEN s.name = 'Large Cap Value Fund' THEN 100.0
        WHEN s.name = 'IT Export Leaders' THEN 175.0
        ELSE 50.0
    END,
    1000.00,
    CASE 
        WHEN s.name = 'Large Cap Value Fund' THEN 108000.00
        WHEN s.name = 'IT Export Leaders' THEN 189000.00
        ELSE 52500.00
    END,
    CASE 
        WHEN s.name = 'Large Cap Value Fund' THEN 8000.00
        WHEN s.name = 'IT Export Leaders' THEN 14000.00
        ELSE 2500.00
    END,
    'active'
FROM smallcases s
WHERE s.name IN ('Large Cap Value Fund', 'IT Export Leaders', 'Banking & NBFC Focus')
LIMIT 3;

-- Insert sample price history data
INSERT INTO price_history (asset_id, price, volume, timestamp, interval_type)
SELECT 
    a.id,
    a.current_price + (random() - 0.5) * a.current_price * 0.05,
    (random() * 1000000)::BIGINT,
    CURRENT_TIMESTAMP - (random() * INTERVAL '30 days'),
    '1d'
FROM assets a, generate_series(1, 20) AS day_offset
WHERE a.symbol IN ('TCS', 'HDFCBANK', 'RELIANCE', 'INFY', 'ICICIBANK');

-- Insert sample smallcase performance data
INSERT INTO smallcase_performance (smallcase_id, date, nav, total_return_1d, total_return_1w, total_return_1m, total_return_1y, alpha)
SELECT 
    s.id,
    CURRENT_DATE - (random() * 30)::INTEGER,
    100.0 + (random() * 20 - 10),
    (random() * 4 - 2),
    (random() * 10 - 5),
    (random() * 20 - 10),
    COALESCE(s.expected_return_1y, 12.0) + (random() * 10 - 5),
    (random() * 8 - 4)
FROM smallcases s, generate_series(1, 10) AS day_offset
WHERE s.is_active = true;

-- Create sample user sessions
INSERT INTO user_sessions (user_id, session_token, expires_at)
SELECT 
    id,
    'session_' || generate_random_uuid()::TEXT,
    CURRENT_TIMESTAMP + INTERVAL '30 days'
FROM users
WHERE username IN ('johndoe', 'janesmith', 'admin');

-- Final verification and summary
SELECT 
    'Demo data setup complete!' as status,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM portfolios) as total_portfolios,
    (SELECT COUNT(*) FROM smallcases WHERE is_active = true) as total_smallcases,
    (SELECT COUNT(*) FROM assets WHERE is_active = true) as total_assets,
    (SELECT COUNT(*) FROM trading_transactions) as total_transactions,
    (SELECT COUNT(*) FROM user_smallcase_investments) as smallcase_investments;