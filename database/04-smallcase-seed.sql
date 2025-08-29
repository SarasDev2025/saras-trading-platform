-- Seed data for smallcases functionality

-- Insert sample smallcases
INSERT INTO smallcases (id, name, description, category, theme, risk_level, expected_return_min, expected_return_max, minimum_investment, created_by) VALUES
('11111111-1111-1111-1111-111111111111', 'Tech Giants', 'Large-cap technology companies with strong fundamentals', 'technology', 'Big Tech', 'medium', 8.0, 15.0, 1000.00, '12345678-1234-1234-1234-123456789012'),
('22222222-2222-2222-2222-222222222222', 'Clean Energy Future', 'Renewable energy and sustainable technology companies', 'energy', 'Clean Energy', 'high', 12.0, 25.0, 2000.00, '12345678-1234-1234-1234-123456789012'),
('33333333-3333-3333-3333-333333333333', 'Dividend Champions', 'High-dividend yielding stable companies', 'dividend', 'Income Generation', 'low', 4.0, 8.0, 500.00, '12345678-1234-1234-1234-123456789012'),
('44444444-4444-4444-4444-444444444444', 'AI Revolution', 'Artificial Intelligence and Machine Learning companies', 'technology', 'AI & ML', 'high', 15.0, 30.0, 2500.00, '12345678-1234-1234-1234-123456789012'),
('55555555-5555-5555-5555-555555555555', 'Healthcare Innovation', 'Biotechnology and pharmaceutical companies', 'healthcare', 'Biotech', 'medium', 10.0, 20.0, 1500.00, '12345678-1234-1234-1234-123456789012');

-- Insert smallcase constituents (assuming we have the assets from previous seed data)
-- Tech Giants smallcase
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
('11111111-1111-1111-1111-111111111111', (SELECT id FROM assets WHERE symbol = 'AAPL'), 25.0),
('11111111-1111-1111-1111-111111111111', (SELECT id FROM assets WHERE symbol = 'GOOGL'), 25.0),
('11111111-1111-1111-1111-111111111111', (SELECT id FROM assets WHERE symbol = 'MSFT'), 25.0),
('11111111-1111-1111-1111-111111111111', (SELECT id FROM assets WHERE symbol = 'TSLA'), 25.0);

-- Clean Energy Future smallcase (using available assets, would need more in real scenario)
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
('22222222-2222-2222-2222-222222222222', (SELECT id FROM assets WHERE symbol = 'TSLA'), 60.0),
('22222222-2222-2222-2222-222222222222', (SELECT id FROM assets WHERE symbol = 'AAPL'), 40.0); -- Apple has clean energy initiatives

-- Dividend Champions smallcase
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
('33333333-3333-3333-3333-333333333333', (SELECT id FROM assets WHERE symbol = 'AAPL'), 30.0),
('33333333-3333-3333-3333-333333333333', (SELECT id FROM assets WHERE symbol = 'MSFT'), 70.0);

-- AI Revolution smallcase
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
('44444444-4444-4444-4444-444444444444', (SELECT id FROM assets WHERE symbol = 'GOOGL'), 40.0),
('44444444-4444-4444-4444-444444444444', (SELECT id FROM assets WHERE symbol = 'MSFT'), 35.0),
('44444444-4444-4444-4444-444444444444', (SELECT id FROM assets WHERE symbol = 'TSLA'), 25.0);

-- Healthcare Innovation smallcase (using available assets as placeholders)
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
('55555555-5555-5555-5555-555555555555', (SELECT id FROM assets WHERE symbol = 'AAPL'), 50.0), -- Apple Health initiatives
('55555555-5555-5555-5555-555555555555', (SELECT id FROM assets WHERE symbol = 'GOOGL'), 50.0); -- Google Health/Verily

-- Insert sample user investments in smallcases for demo_user
INSERT INTO user_smallcase_investments (user_id, portfolio_id, smallcase_id, investment_amount, units_purchased, purchase_price, current_value, unrealized_pnl, status) VALUES
('12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321', '11111111-1111-1111-1111-111111111111', 5000.00, 5.0, 1000.00, 5750.00, 750.00, 'active'),
('12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321', '33333333-3333-3333-3333-333333333333', 2000.00, 4.0, 500.00, 2100.00, 100.00, 'active');
