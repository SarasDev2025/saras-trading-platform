-- Insert sample assets
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, price_updated_at) VALUES
-- Stocks
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 175.50, CURRENT_TIMESTAMP),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'USD', 2580.25, CURRENT_TIMESTAMP),
('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD', 338.75, CURRENT_TIMESTAMP),
('TSLA', 'Tesla, Inc.', 'stock', 'NASDAQ', 'USD', 185.30, CURRENT_TIMESTAMP),
('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 421.90, CURRENT_TIMESTAMP),
-- Crypto
('BTC', 'Bitcoin', 'crypto', 'Binance', 'USD', 43250.75, CURRENT_TIMESTAMP),
('ETH', 'Ethereum', 'crypto', 'Binance', 'USD', 2485.60, CURRENT_TIMESTAMP),
('ADA', 'Cardano', 'crypto', 'Binance', 'USD', 0.485, CURRENT_TIMESTAMP),
('SOL', 'Solana', 'crypto', 'Binance', 'USD', 98.25, CURRENT_TIMESTAMP),
('DOT', 'Polkadot', 'crypto', 'Binance', 'USD', 6.75, CURRENT_TIMESTAMP);

-- Insert sample users (passwords are hashed version of 'password123')
INSERT INTO users (email, username, password_hash, first_name, last_name, email_verified, kyc_status) VALUES
('john.doe@example.com', 'johndoe', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'John', 'Doe', TRUE, 'approved'),
('jane.smith@example.com', 'janesmith', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Jane', 'Smith', TRUE, 'approved'),
('alice.johnson@example.com', 'alicejohnson', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Alice', 'Johnson', TRUE, 'pending'),
('bob.wilson@example.com', 'bobwilson', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Bob', 'Wilson', FALSE, 'pending');

-- Insert default portfolios for users
INSERT INTO portfolios (user_id, name, cash_balance, total_value)
SELECT 
    id,
    'Default Portfolio',
    10000.00,
    10000.00
FROM users;

-- Get some IDs for sample transactions
DO $$
DECLARE
    user_john_id UUID;
    user_jane_id UUID;
    portfolio_john_id UUID;
    portfolio_jane_id UUID;
    asset_aapl_id UUID;
    asset_btc_id UUID;
    asset_eth_id UUID;
    asset_googl_id UUID;
BEGIN
    -- Get user IDs
    SELECT id INTO user_john_id FROM users WHERE username = 'johndoe';
    SELECT id INTO user_jane_id FROM users WHERE username = 'janesmith';
    
    -- Get portfolio IDs
    SELECT id INTO portfolio_john_id FROM portfolios WHERE user_id = user_john_id;
    SELECT id INTO portfolio_jane_id FROM portfolios WHERE user_id = user_jane_id;
    
    -- Get asset IDs
    SELECT id INTO asset_aapl_id FROM assets WHERE symbol = 'AAPL';
    SELECT id INTO asset_btc_id FROM assets WHERE symbol = 'BTC';
    SELECT id INTO asset_eth_id FROM assets WHERE symbol = 'ETH';
    SELECT id INTO asset_googl_id FROM assets WHERE symbol = 'GOOGL';
    
    -- Insert sample transactions for John
    INSERT INTO trading_transactions (user_id, portfolio_id, asset_id, transaction_type, quantity, price_per_unit, total_amount, fees, net_amount, status, transaction_date) VALUES
    (user_john_id, portfolio_john_id, asset_aapl_id, 'buy', 10, 170.00, 1700.00, 1.50, 1701.50, 'executed', CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (user_john_id, portfolio_john_id, asset_btc_id, 'buy', 0.1, 40000.00, 4000.00, 5.00, 4005.00, 'executed', CURRENT_TIMESTAMP - INTERVAL '25 days'),
    (user_john_id, portfolio_john_id, asset_eth_id, 'buy', 2, 2200.00, 4400.00, 3.50, 4403.50, 'executed', CURRENT_TIMESTAMP - INTERVAL '20 days'),
    (user_john_id, portfolio_john_id, asset_aapl_id, 'sell', 2, 175.00, 350.00, 0.75, 349.25, 'executed', CURRENT_TIMESTAMP - INTERVAL '10 days');
    
    -- Insert sample transactions for Jane
    INSERT INTO trading_transactions (user_id, portfolio_id, asset_id, transaction_type, quantity, price_per_unit, total_amount, fees, net_amount, status, transaction_date) VALUES
    (user_jane_id, portfolio_jane_id, asset_googl_id, 'buy', 2, 2500.00, 5000.00, 2.50, 5002.50, 'executed', CURRENT_TIMESTAMP - INTERVAL '15 days'),
    (user_jane_id, portfolio_jane_id, asset_eth_id, 'buy', 1.5, 2300.00, 3450.00, 2.25, 3452.25, 'executed', CURRENT_TIMESTAMP - INTERVAL '12 days');
    
    -- Insert portfolio holdings based on transactions
    INSERT INTO portfolio_holdings (portfolio_id, asset_id, quantity, average_cost, total_cost) VALUES
    -- John's holdings
    (portfolio_john_id, asset_aapl_id, 8, 170.00, 1360.00), -- 10 bought, 2 sold
    (portfolio_john_id, asset_btc_id, 0.1, 40000.00, 4000.00),
    (portfolio_john_id, asset_eth_id, 2, 2200.00, 4400.00),
    -- Jane's holdings
    (portfolio_jane_id, asset_googl_id, 2, 2500.00, 5000.00),
    (portfolio_jane_id, asset_eth_id, 1.5, 2300.00, 3450.00);
    
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
END $$;

-- Insert some sample price history data
INSERT INTO price_history (asset_id, price, volume, timestamp, interval_type)
SELECT 
    a.id,
    a.current_price + (random() - 0.5) * a.current_price * 0.1,
    random() * 1000000,
    CURRENT_TIMESTAMP - (random() * INTERVAL '30 days'),
    '1d'
FROM assets a, generate_series(1, 30) AS day_offset;