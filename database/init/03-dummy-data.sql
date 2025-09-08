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