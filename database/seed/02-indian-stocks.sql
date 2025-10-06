-- =====================================================
-- Indian Stocks and ETFs Seed Data
-- =====================================================
-- This file contains seed data for popular Indian stocks
-- listed on NSE (National Stock Exchange) and BSE (Bombay Stock Exchange)
-- Covers major sectors: Banking, IT, Auto, Pharma, FMCG, Energy, Metals, Telecom, Consumer
-- Region: IN (India)
-- Currency: INR (Indian Rupee)
-- =====================================================

-- Banking Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('HDFCBANK', 'HDFC Bank Limited', 'stock', 'NSE', 'INR', 1650.50, 'Banking', 'IN', true),
('ICICIBANK', 'ICICI Bank Limited', 'stock', 'NSE', 'INR', 1125.75, 'Banking', 'IN', true),
('SBIN', 'State Bank of India', 'stock', 'NSE', 'INR', 785.30, 'Banking', 'IN', true),
('KOTAKBANK', 'Kotak Mahindra Bank Limited', 'stock', 'NSE', 'INR', 1875.25, 'Banking', 'IN', true),
('AXISBANK', 'Axis Bank Limited', 'stock', 'NSE', 'INR', 1095.60, 'Banking', 'IN', true),
('INDUSINDBK', 'IndusInd Bank Limited', 'stock', 'NSE', 'INR', 1425.80, 'Banking', 'IN', true),
('BANDHANBNK', 'Bandhan Bank Limited', 'stock', 'NSE', 'INR', 245.50, 'Banking', 'IN', true),
('FEDERALBNK', 'The Federal Bank Limited', 'stock', 'NSE', 'INR', 168.75, 'Banking', 'IN', true);

-- Information Technology Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('TCS', 'Tata Consultancy Services Limited', 'stock', 'NSE', 'INR', 4125.50, 'Information Technology', 'IN', true),
('INFY', 'Infosys Limited', 'stock', 'NSE', 'INR', 1845.75, 'Information Technology', 'IN', true),
('WIPRO', 'Wipro Limited', 'stock', 'NSE', 'INR', 565.30, 'Information Technology', 'IN', true),
('HCLTECH', 'HCL Technologies Limited', 'stock', 'NSE', 'INR', 1785.60, 'Information Technology', 'IN', true),
('TECHM', 'Tech Mahindra Limited', 'stock', 'NSE', 'INR', 1655.25, 'Information Technology', 'IN', true),
('LTI', 'LTIMindtree Limited', 'stock', 'NSE', 'INR', 5875.40, 'Information Technology', 'IN', true),
('MPHASIS', 'Mphasis Limited', 'stock', 'NSE', 'INR', 2845.90, 'Information Technology', 'IN', true),
('COFORGE', 'Coforge Limited', 'stock', 'NSE', 'INR', 6725.50, 'Information Technology', 'IN', true);

-- Automobile Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('MARUTI', 'Maruti Suzuki India Limited', 'stock', 'NSE', 'INR', 12850.75, 'Automobile', 'IN', true),
('TATAMOTORS', 'Tata Motors Limited', 'stock', 'NSE', 'INR', 975.50, 'Automobile', 'IN', true),
('M&M', 'Mahindra & Mahindra Limited', 'stock', 'NSE', 'INR', 2685.30, 'Automobile', 'IN', true),
('BAJAJ-AUTO', 'Bajaj Auto Limited', 'stock', 'NSE', 'INR', 9575.60, 'Automobile', 'IN', true),
('HEROMOTOCO', 'Hero MotoCorp Limited', 'stock', 'NSE', 'INR', 4825.25, 'Automobile', 'IN', true),
('EICHERMOT', 'Eicher Motors Limited', 'stock', 'NSE', 'INR', 4675.80, 'Automobile', 'IN', true),
('TVSMOTOR', 'TVS Motor Company Limited', 'stock', 'NSE', 'INR', 2475.50, 'Automobile', 'IN', true);

-- Pharmaceutical Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('SUNPHARMA', 'Sun Pharmaceutical Industries Limited', 'stock', 'NSE', 'INR', 1685.50, 'Pharmaceuticals', 'IN', true),
('DRREDDY', 'Dr. Reddy''s Laboratories Limited', 'stock', 'NSE', 'INR', 6275.75, 'Pharmaceuticals', 'IN', true),
('CIPLA', 'Cipla Limited', 'stock', 'NSE', 'INR', 1475.30, 'Pharmaceuticals', 'IN', true),
('LUPIN', 'Lupin Limited', 'stock', 'NSE', 'INR', 2085.60, 'Pharmaceuticals', 'IN', true),
('DIVISLAB', 'Divi''s Laboratories Limited', 'stock', 'NSE', 'INR', 5875.25, 'Pharmaceuticals', 'IN', true),
('BIOCON', 'Biocon Limited', 'stock', 'NSE', 'INR', 355.80, 'Pharmaceuticals', 'IN', true),
('TORNTPHARM', 'Torrent Pharmaceuticals Limited', 'stock', 'NSE', 'INR', 3285.50, 'Pharmaceuticals', 'IN', true),
('AUROPHARMA', 'Aurobindo Pharma Limited', 'stock', 'NSE', 'INR', 1275.90, 'Pharmaceuticals', 'IN', true);

-- FMCG (Fast Moving Consumer Goods) Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('HINDUNILVR', 'Hindustan Unilever Limited', 'stock', 'NSE', 'INR', 2475.50, 'FMCG', 'IN', true),
('ITC', 'ITC Limited', 'stock', 'NSE', 'INR', 475.75, 'FMCG', 'IN', true),
('NESTLEIND', 'Nestle India Limited', 'stock', 'NSE', 'INR', 24850.30, 'FMCG', 'IN', true),
('BRITANNIA', 'Britannia Industries Limited', 'stock', 'NSE', 'INR', 5275.60, 'FMCG', 'IN', true),
('DABUR', 'Dabur India Limited', 'stock', 'NSE', 'INR', 585.25, 'FMCG', 'IN', true),
('MARICO', 'Marico Limited', 'stock', 'NSE', 'INR', 625.80, 'FMCG', 'IN', true),
('GODREJCP', 'Godrej Consumer Products Limited', 'stock', 'NSE', 'INR', 1185.50, 'FMCG', 'IN', true),
('COLPAL', 'Colgate-Palmolive (India) Limited', 'stock', 'NSE', 'INR', 2875.90, 'FMCG', 'IN', true);

-- Energy & Oil/Gas Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('RELIANCE', 'Reliance Industries Limited', 'stock', 'NSE', 'INR', 2875.50, 'Energy', 'IN', true),
('ONGC', 'Oil and Natural Gas Corporation Limited', 'stock', 'NSE', 'INR', 285.75, 'Energy', 'IN', true),
('BPCL', 'Bharat Petroleum Corporation Limited', 'stock', 'NSE', 'INR', 625.30, 'Energy', 'IN', true),
('IOC', 'Indian Oil Corporation Limited', 'stock', 'NSE', 'INR', 165.60, 'Energy', 'IN', true),
('POWERGRID', 'Power Grid Corporation of India Limited', 'stock', 'NSE', 'INR', 325.25, 'Energy', 'IN', true),
('NTPC', 'NTPC Limited', 'stock', 'NSE', 'INR', 385.80, 'Energy', 'IN', true),
('COALINDIA', 'Coal India Limited', 'stock', 'NSE', 'INR', 475.50, 'Energy', 'IN', true),
('ADANIGREEN', 'Adani Green Energy Limited', 'stock', 'NSE', 'INR', 1875.90, 'Energy', 'IN', true),
('ADANIPOWER', 'Adani Power Limited', 'stock', 'NSE', 'INR', 585.50, 'Energy', 'IN', true);

-- Metals & Mining Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('TATASTEEL', 'Tata Steel Limited', 'stock', 'NSE', 'INR', 165.50, 'Metals & Mining', 'IN', true),
('HINDALCO', 'Hindalco Industries Limited', 'stock', 'NSE', 'INR', 685.75, 'Metals & Mining', 'IN', true),
('JSWSTEEL', 'JSW Steel Limited', 'stock', 'NSE', 'INR', 975.30, 'Metals & Mining', 'IN', true),
('VEDL', 'Vedanta Limited', 'stock', 'NSE', 'INR', 485.60, 'Metals & Mining', 'IN', true),
('HINDZINC', 'Hindustan Zinc Limited', 'stock', 'NSE', 'INR', 525.25, 'Metals & Mining', 'IN', true),
('NATIONALUM', 'National Aluminium Company Limited', 'stock', 'NSE', 'INR', 225.80, 'Metals & Mining', 'IN', true),
('JINDALSTEL', 'Jindal Steel & Power Limited', 'stock', 'NSE', 'INR', 985.50, 'Metals & Mining', 'IN', true);

-- Telecom Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('BHARTIARTL', 'Bharti Airtel Limited', 'stock', 'NSE', 'INR', 1585.50, 'Telecommunications', 'IN', true),
('IDEA', 'Vodafone Idea Limited', 'stock', 'NSE', 'INR', 12.75, 'Telecommunications', 'IN', true),
('INDIAMART', 'IndiaMART InterMESH Limited', 'stock', 'NSE', 'INR', 2575.30, 'Telecommunications', 'IN', true);

-- Consumer Goods & Retail Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('ASIANPAINT', 'Asian Paints Limited', 'stock', 'NSE', 'INR', 2875.50, 'Consumer Goods', 'IN', true),
('TITAN', 'Titan Company Limited', 'stock', 'NSE', 'INR', 3475.75, 'Consumer Goods', 'IN', true),
('DMART', 'Avenue Supermarts Limited', 'stock', 'NSE', 'INR', 4285.30, 'Retail', 'IN', true),
('BAJAJFINSV', 'Bajaj Finserv Limited', 'stock', 'NSE', 'INR', 1685.60, 'Financial Services', 'IN', true),
('BAJFINANCE', 'Bajaj Finance Limited', 'stock', 'NSE', 'INR', 7275.25, 'Financial Services', 'IN', true),
('PIDILITIND', 'Pidilite Industries Limited', 'stock', 'NSE', 'INR', 2985.80, 'Chemicals', 'IN', true),
('ULTRACEMCO', 'UltraTech Cement Limited', 'stock', 'NSE', 'INR', 10875.50, 'Cement', 'IN', true),
('GRASIM', 'Grasim Industries Limited', 'stock', 'NSE', 'INR', 2485.90, 'Cement', 'IN', true);

-- Diversified & Conglomerate Sector
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('LT', 'Larsen & Toubro Limited', 'stock', 'NSE', 'INR', 3675.50, 'Diversified', 'IN', true),
('ADANIENT', 'Adani Enterprises Limited', 'stock', 'NSE', 'INR', 2875.75, 'Diversified', 'IN', true),
('ADANIPORTS', 'Adani Ports and Special Economic Zone Limited', 'stock', 'NSE', 'INR', 1285.30, 'Infrastructure', 'IN', true),
('HDFCLIFE', 'HDFC Life Insurance Company Limited', 'stock', 'NSE', 'INR', 685.60, 'Insurance', 'IN', true),
('SBILIFE', 'SBI Life Insurance Company Limited', 'stock', 'NSE', 'INR', 1575.25, 'Insurance', 'IN', true),
('ICICIPRULI', 'ICICI Prudential Life Insurance Company Limited', 'stock', 'NSE', 'INR', 585.80, 'Insurance', 'IN', true);

-- Additional Popular Stocks
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('SHREECEM', 'Shree Cement Limited', 'stock', 'NSE', 'INR', 26875.50, 'Cement', 'IN', true),
('APOLLOHOSP', 'Apollo Hospitals Enterprise Limited', 'stock', 'NSE', 'INR', 6785.75, 'Healthcare', 'IN', true),
('DRREDDY', 'Dr. Lal PathLabs Limited', 'stock', 'NSE', 'INR', 2375.30, 'Healthcare', 'IN', true),
('HAVELLS', 'Havells India Limited', 'stock', 'NSE', 'INR', 1685.60, 'Consumer Durables', 'IN', true),
('VOLTAS', 'Voltas Limited', 'stock', 'NSE', 'INR', 1475.25, 'Consumer Durables', 'IN', true),
('BERGEPAINT', 'Berger Paints India Limited', 'stock', 'NSE', 'INR', 585.80, 'Consumer Goods', 'IN', true),
('PGHH', 'Procter & Gamble Hygiene and Health Care Limited', 'stock', 'NSE', 'INR', 15875.50, 'FMCG', 'IN', true);

-- Indian ETFs
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
('NIFTYBEES', 'Nippon India ETF Nifty 50', 'etf', 'NSE', 'INR', 245.50, 'Index Fund', 'IN', true),
('BANKBEES', 'Nippon India ETF Bank Nifty', 'etf', 'NSE', 'INR', 485.75, 'Index Fund', 'IN', true),
('JUNIORBEES', 'Nippon India ETF Nifty Next 50', 'etf', 'NSE', 'INR', 68.30, 'Index Fund', 'IN', true),
('GOLDBEES', 'Nippon India ETF Gold', 'etf', 'NSE', 'INR', 62.60, 'Commodity', 'IN', true),
('LIQUIDBEES', 'Nippon India ETF Liquid', 'etf', 'NSE', 'INR', 1000.25, 'Liquid Fund', 'IN', true),
('SETFNIF50', 'SBI ETF Nifty 50', 'etf', 'NSE', 'INR', 248.80, 'Index Fund', 'IN', true),
('SETFNN50', 'SBI ETF Nifty Next 50', 'etf', 'NSE', 'INR', 69.50, 'Index Fund', 'IN', true),
('ICICINIFTY', 'ICICI Prudential Nifty 50 ETF', 'etf', 'NSE', 'INR', 246.90, 'Index Fund', 'IN', true);

-- =====================================================
-- End of Indian Stocks and ETFs Seed Data
-- Total: 60+ stocks across all major sectors + 8 ETFs
-- =====================================================
