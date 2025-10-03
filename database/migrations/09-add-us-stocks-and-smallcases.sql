-- Migration 09: Add US Stocks and US-based Smallcases
-- Creates US stock assets and professional smallcase portfolios for US market

-- =====================================================
-- US STOCK ASSETS
-- =====================================================

-- Insert US stocks compatible with Alpaca
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, market_cap, sector, region, is_active) VALUES

-- Technology Stocks (FAANG+)
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 195.89, 3000000000000, 'Technology', 'US', true),
('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD', 384.51, 2850000000000, 'Technology', 'US', true),
('GOOGL', 'Alphabet Inc. Class A', 'stock', 'NASDAQ', 'USD', 138.83, 1750000000000, 'Technology', 'US', true),
('AMZN', 'Amazon.com Inc.', 'stock', 'NASDAQ', 'USD', 145.86, 1520000000000, 'Consumer Discretionary', 'US', true),
('META', 'Meta Platforms Inc.', 'stock', 'NASDAQ', 'USD', 513.13, 1300000000000, 'Technology', 'US', true),
('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'USD', 248.42, 785000000000, 'Consumer Discretionary', 'US', true),
('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 124.47, 3060000000000, 'Technology', 'US', true),
('NFLX', 'Netflix Inc.', 'stock', 'NASDAQ', 'USD', 661.50, 285000000000, 'Communication Services', 'US', true),

-- Financial Services
('JPM', 'JPMorgan Chase & Co.', 'stock', 'NYSE', 'USD', 217.89, 630000000000, 'Financial Services', 'US', true),
('BAC', 'Bank of America Corporation', 'stock', 'NYSE', 'USD', 45.32, 350000000000, 'Financial Services', 'US', true),
('WFC', 'Wells Fargo & Company', 'stock', 'NYSE', 'USD', 61.45, 210000000000, 'Financial Services', 'US', true),
('GS', 'Goldman Sachs Group Inc.', 'stock', 'NYSE', 'USD', 478.95, 158000000000, 'Financial Services', 'US', true),
('V', 'Visa Inc.', 'stock', 'NYSE', 'USD', 295.67, 620000000000, 'Financial Services', 'US', true),
('MA', 'Mastercard Incorporated', 'stock', 'NYSE', 'USD', 490.12, 460000000000, 'Financial Services', 'US', true),

-- Healthcare & Pharma
('JNJ', 'Johnson & Johnson', 'stock', 'NYSE', 'USD', 157.83, 410000000000, 'Healthcare', 'US', true),
('PFE', 'Pfizer Inc.', 'stock', 'NYSE', 'USD', 25.89, 145000000000, 'Healthcare', 'US', true),
('UNH', 'UnitedHealth Group Inc.', 'stock', 'NYSE', 'USD', 542.67, 505000000000, 'Healthcare', 'US', true),
('ABBV', 'AbbVie Inc.', 'stock', 'NYSE', 'USD', 166.84, 295000000000, 'Healthcare', 'US', true),

-- Consumer Goods & Retail
('PG', 'Procter & Gamble Company', 'stock', 'NYSE', 'USD', 164.52, 385000000000, 'Consumer Staples', 'US', true),
('KO', 'Coca-Cola Company', 'stock', 'NYSE', 'USD', 62.18, 268000000000, 'Consumer Staples', 'US', true),
('WMT', 'Walmart Inc.', 'stock', 'NYSE', 'USD', 81.23, 658000000000, 'Consumer Staples', 'US', true),
('HD', 'Home Depot Inc.', 'stock', 'NYSE', 'USD', 389.67, 385000000000, 'Consumer Discretionary', 'US', true),

-- Energy & Utilities
('XOM', 'Exxon Mobil Corporation', 'stock', 'NYSE', 'USD', 117.85, 485000000000, 'Energy', 'US', true),
('CVX', 'Chevron Corporation', 'stock', 'NYSE', 'USD', 156.42, 285000000000, 'Energy', 'US', true),

-- Industrial & Manufacturing
('BA', 'Boeing Company', 'stock', 'NYSE', 'USD', 155.67, 92000000000, 'Industrials', 'US', true),
('CAT', 'Caterpillar Inc.', 'stock', 'NYSE', 'USD', 384.25, 195000000000, 'Industrials', 'US', true),
('GE', 'General Electric Company', 'stock', 'NYSE', 'USD', 169.84, 185000000000, 'Industrials', 'US', true),

-- Communication Services
('ORCL', 'Oracle Corporation', 'stock', 'NYSE', 'USD', 142.67, 385000000000, 'Technology', 'US', true),
('CRM', 'Salesforce Inc.', 'stock', 'NYSE', 'USD', 285.43, 275000000000, 'Technology', 'US', true),

-- ETFs for diversification
('SPY', 'SPDR S&P 500 ETF Trust', 'stock', 'NYSE Arca', 'USD', 572.45, 0, 'Index Fund', 'US', true),
('QQQ', 'Invesco QQQ Trust', 'stock', 'NASDAQ', 'USD', 481.23, 0, 'Index Fund', 'US', true),
('IWM', 'iShares Russell 2000 ETF', 'stock', 'NYSE Arca', 'USD', 218.56, 0, 'Index Fund', 'US', true),
('VTI', 'Vanguard Total Stock Market ETF', 'stock', 'NYSE Arca', 'USD', 285.67, 0, 'Index Fund', 'US', true)

ON CONFLICT (symbol) DO UPDATE SET
current_price = EXCLUDED.current_price,
market_cap = EXCLUDED.market_cap,
sector = EXCLUDED.sector,
region = EXCLUDED.region,
currency = EXCLUDED.currency;

-- =====================================================
-- US SMALLCASES
-- =====================================================

-- Insert US-based smallcases compatible with Alpaca
INSERT INTO smallcases (name, description, category, risk_level, expected_return_min, expected_return_max, minimum_investment, region, supported_brokers, currency, strategy_type) VALUES

('US Tech Giants',
 'Portfolio of established technology companies with strong moats and global reach. Focused on FAANG+ stocks with proven business models.',
 'Technology', 'MEDIUM', 12.0, 22.0, 5000, 'US', ARRAY['alpaca'], 'USD', 'GROWTH'),

('S&P 500 Core Holdings',
 'Diversified portfolio of large-cap US stocks representing major sectors of the American economy.',
 'Large Cap', 'LOW', 8.0, 15.0, 2500, 'US', ARRAY['alpaca'], 'USD', 'VALUE'),

('US Banking Powerhouse',
 'Major US banks and financial services companies benefiting from interest rate cycles and economic growth.',
 'Financial Services', 'MEDIUM', 10.0, 18.0, 3000, 'US', ARRAY['alpaca'], 'USD', 'VALUE'),

('Growth Innovation Fund',
 'High-growth US companies leading innovation in AI, cloud computing, and digital transformation.',
 'Growth', 'HIGH', 15.0, 30.0, 10000, 'US', ARRAY['alpaca'], 'USD', 'GROWTH'),

('Dividend Aristocrats US',
 'Established US companies with consistent dividend payments and strong cash flow generation.',
 'Dividend', 'LOW', 6.0, 12.0, 4000, 'US', ARRAY['alpaca'], 'USD', 'DIVIDEND'),

('Healthcare Leaders USA',
 'Pharmaceutical and healthcare companies with strong pipelines and defensive characteristics.',
 'Healthcare', 'MEDIUM', 9.0, 16.0, 3500, 'US', ARRAY['alpaca'], 'USD', 'DEFENSIVE'),

('Consumer Brands Portfolio',
 'Iconic American consumer brands with global reach and pricing power.',
 'Consumer Staples', 'LOW', 7.0, 14.0, 3000, 'US', ARRAY['alpaca'], 'USD', 'DEFENSIVE'),

('US Energy Infrastructure',
 'Energy companies positioned to benefit from energy transition and infrastructure spending.',
 'Energy', 'HIGH', 12.0, 25.0, 5000, 'US', ARRAY['alpaca'], 'USD', 'CYCLICAL'),

('American Industrial Strength',
 'Manufacturing and industrial companies benefiting from reshoring and infrastructure investment.',
 'Industrials', 'MEDIUM', 11.0, 19.0, 4000, 'US', ARRAY['alpaca'], 'USD', 'CYCLICAL'),

('ETF Foundation Portfolio',
 'Low-cost ETF portfolio providing broad market exposure with minimal management.',
 'Index Fund', 'LOW', 7.0, 12.0, 1000, 'US', ARRAY['alpaca'], 'USD', 'PASSIVE')

ON CONFLICT (name) DO UPDATE SET
description = EXCLUDED.description,
minimum_investment = EXCLUDED.minimum_investment,
region = EXCLUDED.region,
supported_brokers = EXCLUDED.supported_brokers,
currency = EXCLUDED.currency;

-- =====================================================
-- US SMALLCASE CONSTITUENTS
-- =====================================================

-- US Tech Giants
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('US Tech Giants', 'AAPL', 20.0),
    ('US Tech Giants', 'MSFT', 18.0),
    ('US Tech Giants', 'GOOGL', 15.0),
    ('US Tech Giants', 'AMZN', 12.0),
    ('US Tech Giants', 'META', 10.0),
    ('US Tech Giants', 'NVDA', 15.0),
    ('US Tech Giants', 'TSLA', 10.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- S&P 500 Core Holdings
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('S&P 500 Core Holdings', 'AAPL', 15.0),
    ('S&P 500 Core Holdings', 'MSFT', 12.0),
    ('S&P 500 Core Holdings', 'GOOGL', 8.0),
    ('S&P 500 Core Holdings', 'AMZN', 8.0),
    ('S&P 500 Core Holdings', 'JPM', 10.0),
    ('S&P 500 Core Holdings', 'JNJ', 8.0),
    ('S&P 500 Core Holdings', 'PG', 7.0),
    ('S&P 500 Core Holdings', 'UNH', 9.0),
    ('S&P 500 Core Holdings', 'V', 8.0),
    ('S&P 500 Core Holdings', 'HD', 7.0),
    ('S&P 500 Core Holdings', 'WMT', 8.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- US Banking Powerhouse
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('US Banking Powerhouse', 'JPM', 30.0),
    ('US Banking Powerhouse', 'BAC', 25.0),
    ('US Banking Powerhouse', 'WFC', 20.0),
    ('US Banking Powerhouse', 'GS', 15.0),
    ('US Banking Powerhouse', 'V', 10.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Growth Innovation Fund
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Growth Innovation Fund', 'NVDA', 25.0),
    ('Growth Innovation Fund', 'TSLA', 20.0),
    ('Growth Innovation Fund', 'META', 15.0),
    ('Growth Innovation Fund', 'NFLX', 12.0),
    ('Growth Innovation Fund', 'CRM', 13.0),
    ('Growth Innovation Fund', 'ORCL', 15.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Dividend Aristocrats US
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Dividend Aristocrats US', 'JNJ', 20.0),
    ('Dividend Aristocrats US', 'PG', 18.0),
    ('Dividend Aristocrats US', 'KO', 15.0),
    ('Dividend Aristocrats US', 'JPM', 17.0),
    ('Dividend Aristocrats US', 'XOM', 15.0),
    ('Dividend Aristocrats US', 'CVX', 15.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Healthcare Leaders USA
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Healthcare Leaders USA', 'UNH', 30.0),
    ('Healthcare Leaders USA', 'JNJ', 25.0),
    ('Healthcare Leaders USA', 'PFE', 20.0),
    ('Healthcare Leaders USA', 'ABBV', 25.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- Consumer Brands Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('Consumer Brands Portfolio', 'PG', 25.0),
    ('Consumer Brands Portfolio', 'KO', 20.0),
    ('Consumer Brands Portfolio', 'WMT', 25.0),
    ('Consumer Brands Portfolio', 'HD', 30.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- US Energy Infrastructure
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('US Energy Infrastructure', 'XOM', 40.0),
    ('US Energy Infrastructure', 'CVX', 35.0),
    ('US Energy Infrastructure', 'BA', 25.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- American Industrial Strength
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('American Industrial Strength', 'BA', 30.0),
    ('American Industrial Strength', 'CAT', 25.0),
    ('American Industrial Strength', 'GE', 25.0),
    ('American Industrial Strength', 'HD', 20.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- ETF Foundation Portfolio
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, weight_percentage::DECIMAL
FROM smallcases s, assets a, (VALUES
    ('ETF Foundation Portfolio', 'SPY', 40.0),
    ('ETF Foundation Portfolio', 'QQQ', 25.0),
    ('ETF Foundation Portfolio', 'IWM', 20.0),
    ('ETF Foundation Portfolio', 'VTI', 15.0)
) AS weights(smallcase_name, stock_symbol, weight_percentage)
WHERE s.name = weights.smallcase_name AND a.symbol = weights.stock_symbol
ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
weight_percentage = EXCLUDED.weight_percentage;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Show US assets count
SELECT
    'US Assets Created' as status,
    COUNT(*) as total_us_assets
FROM assets
WHERE region = 'US' AND is_active = true;

-- Show US smallcases count
SELECT
    'US Smallcases Created' as status,
    COUNT(*) as total_us_smallcases
FROM smallcases
WHERE region = 'US' AND is_active = true;

-- Show regional distribution
SELECT
    region,
    currency,
    COUNT(*) as smallcase_count,
    AVG(minimum_investment) as avg_min_investment
FROM smallcases
WHERE is_active = true
GROUP BY region, currency
ORDER BY region;

-- Show broker compatibility
SELECT
    region,
    unnest(supported_brokers) as broker,
    COUNT(*) as smallcase_count
FROM smallcases
WHERE is_active = true
GROUP BY region, broker
ORDER BY region, broker;