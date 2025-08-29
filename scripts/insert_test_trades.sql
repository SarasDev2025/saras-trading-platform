-- First, let's check if we have any assets
SELECT id, symbol FROM assets LIMIT 5;

-- Insert test trades
INSERT INTO trading_transactions (
    id, user_id, portfolio_id, asset_id, transaction_type, 
    quantity, price_per_unit, total_amount, fees, net_amount,
    transaction_date, status, order_type
) VALUES 
    (gen_random_uuid(), '12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321', 
     (SELECT id FROM assets WHERE symbol = 'AAPL' LIMIT 1), 'BUY',
     10, 180.50, 1805.00, 1.81, 1806.81,
     NOW() - INTERVAL '2 days', 'executed', 'market'),
     
    (gen_random_uuid(), '12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321',
     (SELECT id FROM assets WHERE symbol = 'MSFT' LIMIT 1), 'BUY',
     5, 400.25, 2001.25, 2.00, 2003.25,
     NOW() - INTERVAL '1 day', 'executed', 'market'),
     
    (gen_random_uuid(), '12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321',
     (SELECT id FROM assets WHERE symbol = 'GOOGL' LIMIT 1), 'BUY',
     8, 175.75, 1406.00, 1.41, 1407.41,
     NOW() - INTERVAL '3 days', 'executed', 'market');

-- Verify the trades were inserted
SELECT t.id, a.symbol, t.transaction_type, t.quantity, t.price_per_unit, t.total_amount, t.status, t.transaction_date
FROM trading_transactions t
JOIN assets a ON t.asset_id = a.id
ORDER BY t.transaction_date DESC;
