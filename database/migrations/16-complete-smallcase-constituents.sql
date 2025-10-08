--
-- Migration: Complete Smallcase Constituents Data
-- Description: Add missing constituents for US smallcases and create India smallcases
-- Date: 2025-10-07
--

-- =====================================================
-- Step 1: Create Assets for US Stocks
-- =====================================================

-- Cloud & SaaS stocks
INSERT INTO assets (symbol, name, asset_type, exchange, currency, region, is_active)
VALUES
    ('CRM', 'Salesforce Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('NOW', 'ServiceNow Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('SNOW', 'Snowflake Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('DDOG', 'Datadog Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('MDB', 'MongoDB Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('ZM', 'Zoom Video Communications', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('OKTA', 'Okta Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('NET', 'Cloudflare Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('TWLO', 'Twilio Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('TEAM', 'Atlassian Corporation', 'stock', 'NASDAQ', 'USD', 'US', true)
ON CONFLICT (symbol) DO NOTHING;

-- EV & Clean Energy stocks
INSERT INTO assets (symbol, name, asset_type, exchange, currency, region, is_active)
VALUES
    ('ENPH', 'Enphase Energy Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('RIVN', 'Rivian Automotive Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('LCID', 'Lucid Group Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('PLUG', 'Plug Power Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('FSLR', 'First Solar Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('CHPT', 'ChargePoint Holdings', 'stock', 'NYSE', 'USD', 'US', true),
    ('NIO', 'NIO Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('BLNK', 'Blink Charging Co', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('XPEV', 'XPeng Inc', 'stock', 'NYSE', 'USD', 'US', true)
ON CONFLICT (symbol) DO NOTHING;

-- Energy & Oil stocks
INSERT INTO assets (symbol, name, asset_type, exchange, currency, region, is_active)
VALUES
    ('XOM', 'Exxon Mobil Corporation', 'stock', 'NYSE', 'USD', 'US', true),
    ('CVX', 'Chevron Corporation', 'stock', 'NYSE', 'USD', 'US', true),
    ('COP', 'ConocoPhillips', 'stock', 'NYSE', 'USD', 'US', true),
    ('SLB', 'Schlumberger NV', 'stock', 'NYSE', 'USD', 'US', true),
    ('EOG', 'EOG Resources Inc', 'stock', 'NYSE', 'USD', 'US', true),
    ('PXD', 'Pioneer Natural Resources', 'stock', 'NYSE', 'USD', 'US', true),
    ('MPC', 'Marathon Petroleum Corp', 'stock', 'NYSE', 'USD', 'US', true),
    ('VLO', 'Valero Energy Corporation', 'stock', 'NYSE', 'USD', 'US', true),
    ('PSX', 'Phillips 66', 'stock', 'NYSE', 'USD', 'US', true)
ON CONFLICT (symbol) DO NOTHING;

-- Semiconductors & AI stocks
INSERT INTO assets (symbol, name, asset_type, exchange, currency, region, is_active)
VALUES
    ('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('AMD', 'Advanced Micro Devices', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('INTC', 'Intel Corporation', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('QCOM', 'QUALCOMM Incorporated', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('AVGO', 'Broadcom Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('TSM', 'Taiwan Semiconductor', 'stock', 'NYSE', 'USD', 'US', true),
    ('ASML', 'ASML Holding NV', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('MU', 'Micron Technology Inc', 'stock', 'NASDAQ', 'USD', 'US', true),
    ('MRVL', 'Marvell Technology Inc', 'stock', 'NASDAQ', 'USD', 'US', true)
ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- Step 2: Create Assets for India Stocks
-- =====================================================

INSERT INTO assets (symbol, name, asset_type, exchange, currency, region, is_active)
VALUES
    -- Nifty 50 Core
    ('RELIANCE', 'Reliance Industries Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('TCS', 'Tata Consultancy Services', 'stock', 'NSE', 'INR', 'IN', true),
    ('HDFCBANK', 'HDFC Bank Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('INFY', 'Infosys Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('ICICIBANK', 'ICICI Bank Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('HINDUNILVR', 'Hindustan Unilever Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('ITC', 'ITC Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('SBIN', 'State Bank of India', 'stock', 'NSE', 'INR', 'IN', true),
    ('BHARTIARTL', 'Bharti Airtel Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('BAJFINANCE', 'Bajaj Finance Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    -- IT & Tech
    ('WIPRO', 'Wipro Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('HCLTECH', 'HCL Technologies Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('TECHM', 'Tech Mahindra Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('LTI', 'LTIMindtree Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('PERSISTENT', 'Persistent Systems Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('COFORGE', 'Coforge Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    -- Banking & Finance
    ('KOTAKBANK', 'Kotak Mahindra Bank Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('AXISBANK', 'Axis Bank Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('BAJAJFINSV', 'Bajaj Finserv Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('HDFCLIFE', 'HDFC Life Insurance Co Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    -- Pharma & Healthcare
    ('SUNPHARMA', 'Sun Pharmaceutical Industries', 'stock', 'NSE', 'INR', 'IN', true),
    ('DRREDDY', 'Dr Reddys Laboratories Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('CIPLA', 'Cipla Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('DIVISLAB', 'Divis Laboratories Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('APOLLOHOSP', 'Apollo Hospitals Enterprise', 'stock', 'NSE', 'INR', 'IN', true),
    ('BIOCON', 'Biocon Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('AUROPHARMA', 'Aurobindo Pharma Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('TORNTPHARM', 'Torrent Pharmaceuticals Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    -- Auto & EV
    ('MARUTI', 'Maruti Suzuki India Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('TATAMOTORS', 'Tata Motors Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('M&M', 'Mahindra & Mahindra Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('BAJAJ-AUTO', 'Bajaj Auto Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('EICHERMOT', 'Eicher Motors Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('HEROMOTOCO', 'Hero MotoCorp Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('BOSCHLTD', 'Bosch Ltd', 'stock', 'NSE', 'INR', 'IN', true),
    ('MOTHERSON', 'Samvardhana Motherson International', 'stock', 'NSE', 'INR', 'IN', true)
ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- Step 3: Add Missing US Smallcase Constituents
-- =====================================================

-- Cloud & SaaS
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('CRM', 15.00),
    ('NOW', 12.50),
    ('SNOW', 12.00),
    ('DDOG', 11.00),
    ('MDB', 10.00),
    ('ZM', 9.50),
    ('OKTA', 9.00),
    ('NET', 8.00),
    ('TWLO', 7.00),
    ('TEAM', 6.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Cloud & SaaS' AND s.region = 'US'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- EV & Clean Energy
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('TSLA', 25.00),
    ('ENPH', 15.00),
    ('RIVN', 12.00),
    ('LCID', 10.00),
    ('PLUG', 9.00),
    ('FSLR', 8.00),
    ('CHPT', 7.00),
    ('NIO', 6.50),
    ('BLNK', 4.50),
    ('XPEV', 3.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'EV & Clean Energy' AND s.region = 'US'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- Energy & Oil
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('XOM', 20.00),
    ('CVX', 18.00),
    ('COP', 14.00),
    ('SLB', 12.00),
    ('EOG', 10.00),
    ('PXD', 9.00),
    ('MPC', 8.00),
    ('VLO', 6.00),
    ('PSX', 3.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Energy & Oil' AND s.region = 'US'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- Semiconductors & AI
INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('NVDA', 22.00),
    ('AMD', 18.00),
    ('INTC', 14.00),
    ('QCOM', 12.00),
    ('AVGO', 11.00),
    ('TSM', 10.00),
    ('ASML', 8.00),
    ('MU', 3.00),
    ('MRVL', 2.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Semiconductors & AI' AND s.region = 'US'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- =====================================================
-- Step 4: Create India Smallcases
-- =====================================================

-- India Nifty 50 Core
INSERT INTO smallcases (name, description, region, category, minimum_investment, expected_return_min, expected_return_max, risk_level, is_active, currency, supported_brokers)
VALUES (
    'Nifty 50 Core',
    'Top 50 companies from NSE representing core Indian market',
    'IN',
    'Large Cap',
    10000.00,
    10.00,
    15.00,
    'medium',
    true,
    'INR',
    ARRAY['zerodha']
) ON CONFLICT DO NOTHING;

INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('RELIANCE', 10.00),
    ('TCS', 9.00),
    ('HDFCBANK', 8.50),
    ('INFY', 7.50),
    ('ICICIBANK', 7.00),
    ('HINDUNILVR', 6.00),
    ('ITC', 5.50),
    ('SBIN', 5.00),
    ('BHARTIARTL', 4.50),
    ('BAJFINANCE', 4.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Nifty 50 Core' AND s.region = 'IN'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- India IT & Technology
INSERT INTO smallcases (name, description, region, category, minimum_investment, expected_return_min, expected_return_max, risk_level, is_active, currency, supported_brokers)
VALUES (
    'IT & Technology India',
    'Leading Indian IT services and technology companies',
    'IN',
    'Sectoral',
    15000.00,
    12.00,
    18.00,
    'medium',
    true,
    'INR',
    ARRAY['zerodha']
) ON CONFLICT DO NOTHING;

INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('TCS', 20.00),
    ('INFY', 18.00),
    ('WIPRO', 14.00),
    ('HCLTECH', 13.00),
    ('TECHM', 12.00),
    ('LTI', 10.00),
    ('PERSISTENT', 7.00),
    ('COFORGE', 6.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'IT & Technology India' AND s.region = 'IN'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- India Banking & Finance
INSERT INTO smallcases (name, description, region, category, minimum_investment, expected_return_min, expected_return_max, risk_level, is_active, currency, supported_brokers)
VALUES (
    'Banking & Finance India',
    'Top Indian banks and financial institutions',
    'IN',
    'Sectoral',
    12000.00,
    11.00,
    17.00,
    'medium',
    true,
    'INR',
    ARRAY['zerodha']
) ON CONFLICT DO NOTHING;

INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('HDFCBANK', 18.00),
    ('ICICIBANK', 16.00),
    ('SBIN', 15.00),
    ('KOTAKBANK', 13.00),
    ('AXISBANK', 12.00),
    ('BAJFINANCE', 10.00),
    ('BAJAJFINSV', 8.00),
    ('HDFCLIFE', 8.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Banking & Finance India' AND s.region = 'IN'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- India Pharma & Healthcare
INSERT INTO smallcases (name, description, region, category, minimum_investment, expected_return_min, expected_return_max, risk_level, is_active, currency, supported_brokers)
VALUES (
    'Pharma & Healthcare India',
    'Leading Indian pharmaceutical and healthcare companies',
    'IN',
    'Sectoral',
    14000.00,
    10.00,
    16.00,
    'medium',
    true,
    'INR',
    ARRAY['zerodha']
) ON CONFLICT DO NOTHING;

INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('SUNPHARMA', 18.00),
    ('DRREDDY', 15.00),
    ('CIPLA', 14.00),
    ('DIVISLAB', 13.00),
    ('APOLLOHOSP', 12.00),
    ('BIOCON', 10.00),
    ('AUROPHARMA', 9.00),
    ('TORNTPHARM', 9.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Pharma & Healthcare India' AND s.region = 'IN'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;

-- India Auto & EV
INSERT INTO smallcases (name, description, region, category, minimum_investment, expected_return_min, expected_return_max, risk_level, is_active, currency, supported_brokers)
VALUES (
    'Auto & EV India',
    'Automotive and electric vehicle ecosystem in India',
    'IN',
    'Sectoral',
    16000.00,
    11.00,
    19.00,
    'high',
    true,
    'INR',
    ARRAY['zerodha']
) ON CONFLICT DO NOTHING;

INSERT INTO smallcase_constituents (smallcase_id, asset_id, weight_percentage)
SELECT s.id, a.id, w.weight
FROM smallcases s
CROSS JOIN (VALUES
    ('MARUTI', 20.00),
    ('TATAMOTORS', 18.00),
    ('M&M', 15.00),
    ('BAJAJ-AUTO', 13.00),
    ('EICHERMOT', 12.00),
    ('HEROMOTOCO', 10.00),
    ('BOSCHLTD', 7.00),
    ('MOTHERSON', 5.00)
) AS w(symbol, weight)
JOIN assets a ON a.symbol = w.symbol
WHERE s.name = 'Auto & EV India' AND s.region = 'IN'
ON CONFLICT (smallcase_id, asset_id) DO NOTHING;
