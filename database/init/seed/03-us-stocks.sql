-- =====================================================
-- US MARKET STOCKS AND ETFs SEED DATA
-- =====================================================
-- This file contains seed data for popular US stocks across all major sectors
-- and commonly traded US ETFs for development and testing purposes.
-- Region: US | Currency: USD | Exchanges: NASDAQ, NYSE

-- =====================================================
-- TECHNOLOGY SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 178.50, 'Technology', 'US', true),
    ('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD', 425.30, 'Technology', 'US', true),
    ('GOOGL', 'Alphabet Inc. Class A', 'stock', 'NASDAQ', 'USD', 142.65, 'Technology', 'US', true),
    ('GOOG', 'Alphabet Inc. Class C', 'stock', 'NASDAQ', 'USD', 144.20, 'Technology', 'US', true),
    ('AMZN', 'Amazon.com Inc.', 'stock', 'NASDAQ', 'USD', 178.25, 'Technology', 'US', true),
    ('META', 'Meta Platforms Inc.', 'stock', 'NASDAQ', 'USD', 512.80, 'Technology', 'US', true),
    ('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'USD', 248.50, 'Automotive', 'US', true),
    ('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 495.75, 'Technology', 'US', true),
    ('AMD', 'Advanced Micro Devices Inc.', 'stock', 'NASDAQ', 'USD', 142.30, 'Technology', 'US', true),
    ('INTC', 'Intel Corporation', 'stock', 'NASDAQ', 'USD', 24.85, 'Technology', 'US', true),
    ('ORCL', 'Oracle Corporation', 'stock', 'NYSE', 'USD', 128.40, 'Technology', 'US', true),
    ('CRM', 'Salesforce Inc.', 'stock', 'NYSE', 'USD', 285.90, 'Technology', 'US', true),
    ('ADBE', 'Adobe Inc.', 'stock', 'NASDAQ', 'USD', 495.20, 'Technology', 'US', true),
    ('NFLX', 'Netflix Inc.', 'stock', 'NASDAQ', 'USD', 645.80, 'Technology', 'US', true),
    ('CSCO', 'Cisco Systems Inc.', 'stock', 'NASDAQ', 'USD', 52.15, 'Technology', 'US', true);

-- =====================================================
-- FINANCIAL SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('JPM', 'JPMorgan Chase & Co.', 'stock', 'NYSE', 'USD', 198.45, 'Banking', 'US', true),
    ('BAC', 'Bank of America Corporation', 'stock', 'NYSE', 'USD', 39.80, 'Banking', 'US', true),
    ('WFC', 'Wells Fargo & Company', 'stock', 'NYSE', 'USD', 56.25, 'Banking', 'US', true),
    ('GS', 'Goldman Sachs Group Inc.', 'stock', 'NYSE', 'USD', 485.60, 'Banking', 'US', true),
    ('MS', 'Morgan Stanley', 'stock', 'NYSE', 'USD', 105.30, 'Banking', 'US', true),
    ('C', 'Citigroup Inc.', 'stock', 'NYSE', 'USD', 64.75, 'Banking', 'US', true),
    ('BLK', 'BlackRock Inc.', 'stock', 'NYSE', 'USD', 925.40, 'Financial Services', 'US', true),
    ('SCHW', 'Charles Schwab Corporation', 'stock', 'NYSE', 'USD', 72.85, 'Financial Services', 'US', true),
    ('AXP', 'American Express Company', 'stock', 'NYSE', 'USD', 248.90, 'Financial Services', 'US', true),
    ('V', 'Visa Inc.', 'stock', 'NYSE', 'USD', 285.50, 'Financial Services', 'US', true),
    ('MA', 'Mastercard Incorporated', 'stock', 'NYSE', 'USD', 482.30, 'Financial Services', 'US', true);

-- =====================================================
-- HEALTHCARE SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('JNJ', 'Johnson & Johnson', 'stock', 'NYSE', 'USD', 158.75, 'Healthcare', 'US', true),
    ('PFE', 'Pfizer Inc.', 'stock', 'NYSE', 'USD', 28.45, 'Pharmaceuticals', 'US', true),
    ('UNH', 'UnitedHealth Group Inc.', 'stock', 'NYSE', 'USD', 525.80, 'Healthcare', 'US', true),
    ('MRK', 'Merck & Co. Inc.', 'stock', 'NYSE', 'USD', 98.60, 'Pharmaceuticals', 'US', true),
    ('ABT', 'Abbott Laboratories', 'stock', 'NYSE', 'USD', 112.35, 'Healthcare', 'US', true),
    ('LLY', 'Eli Lilly and Company', 'stock', 'NYSE', 'USD', 785.40, 'Pharmaceuticals', 'US', true),
    ('TMO', 'Thermo Fisher Scientific Inc.', 'stock', 'NYSE', 'USD', 558.25, 'Healthcare', 'US', true),
    ('ABBV', 'AbbVie Inc.', 'stock', 'NYSE', 'USD', 172.90, 'Pharmaceuticals', 'US', true),
    ('CVS', 'CVS Health Corporation', 'stock', 'NYSE', 'USD', 62.45, 'Healthcare', 'US', true),
    ('MDT', 'Medtronic plc', 'stock', 'NYSE', 'USD', 84.70, 'Medical Devices', 'US', true);

-- =====================================================
-- CONSUMER GOODS & SERVICES
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('KO', 'The Coca-Cola Company', 'stock', 'NYSE', 'USD', 62.85, 'Beverages', 'US', true),
    ('PEP', 'PepsiCo Inc.', 'stock', 'NASDAQ', 'USD', 168.40, 'Beverages', 'US', true),
    ('PG', 'Procter & Gamble Company', 'stock', 'NYSE', 'USD', 168.25, 'Consumer Goods', 'US', true),
    ('NKE', 'Nike Inc.', 'stock', 'NYSE', 'USD', 78.90, 'Apparel', 'US', true),
    ('MCD', 'McDonald''s Corporation', 'stock', 'NYSE', 'USD', 298.50, 'Restaurants', 'US', true),
    ('SBUX', 'Starbucks Corporation', 'stock', 'NASDAQ', 'USD', 98.75, 'Restaurants', 'US', true),
    ('DIS', 'The Walt Disney Company', 'stock', 'NYSE', 'USD', 95.60, 'Entertainment', 'US', true),
    ('CL', 'Colgate-Palmolive Company', 'stock', 'NYSE', 'USD', 92.30, 'Consumer Goods', 'US', true),
    ('COST', 'Costco Wholesale Corporation', 'stock', 'NASDAQ', 'USD', 752.85, 'Retail', 'US', true);

-- =====================================================
-- INDUSTRIAL SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('BA', 'The Boeing Company', 'stock', 'NYSE', 'USD', 178.40, 'Aerospace', 'US', true),
    ('CAT', 'Caterpillar Inc.', 'stock', 'NYSE', 'USD', 345.60, 'Industrial', 'US', true),
    ('MMM', '3M Company', 'stock', 'NYSE', 'USD', 128.75, 'Industrial', 'US', true),
    ('HON', 'Honeywell International Inc.', 'stock', 'NASDAQ', 'USD', 208.90, 'Industrial', 'US', true),
    ('GE', 'General Electric Company', 'stock', 'NYSE', 'USD', 165.40, 'Industrial', 'US', true),
    ('UPS', 'United Parcel Service Inc.', 'stock', 'NYSE', 'USD', 132.85, 'Logistics', 'US', true),
    ('RTX', 'RTX Corporation', 'stock', 'NYSE', 'USD', 118.60, 'Aerospace', 'US', true),
    ('LMT', 'Lockheed Martin Corporation', 'stock', 'NYSE', 'USD', 495.30, 'Aerospace', 'US', true);

-- =====================================================
-- ENERGY SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('XOM', 'Exxon Mobil Corporation', 'stock', 'NYSE', 'USD', 115.80, 'Energy', 'US', true),
    ('CVX', 'Chevron Corporation', 'stock', 'NYSE', 'USD', 158.25, 'Energy', 'US', true),
    ('COP', 'ConocoPhillips', 'stock', 'NYSE', 'USD', 112.45, 'Energy', 'US', true),
    ('SLB', 'Schlumberger Limited', 'stock', 'NYSE', 'USD', 45.90, 'Energy', 'US', true),
    ('EOG', 'EOG Resources Inc.', 'stock', 'NYSE', 'USD', 128.70, 'Energy', 'US', true),
    ('PXD', 'Pioneer Natural Resources Company', 'stock', 'NYSE', 'USD', 245.80, 'Energy', 'US', true);

-- =====================================================
-- RETAIL SECTOR
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('WMT', 'Walmart Inc.', 'stock', 'NYSE', 'USD', 72.35, 'Retail', 'US', true),
    ('HD', 'The Home Depot Inc.', 'stock', 'NYSE', 'USD', 385.60, 'Retail', 'US', true),
    ('TGT', 'Target Corporation', 'stock', 'NYSE', 'USD', 148.90, 'Retail', 'US', true),
    ('LOW', 'Lowe''s Companies Inc.', 'stock', 'NYSE', 'USD', 258.45, 'Retail', 'US', true);

-- =====================================================
-- US ETFs - BROAD MARKET INDICES
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('SPY', 'SPDR S&P 500 ETF Trust', 'etf', 'NYSE', 'USD', 568.25, 'Index Fund', 'US', true),
    ('QQQ', 'Invesco QQQ Trust (NASDAQ-100)', 'etf', 'NASDAQ', 'USD', 485.30, 'Index Fund', 'US', true),
    ('DIA', 'SPDR Dow Jones Industrial Average ETF', 'etf', 'NYSE', 'USD', 425.80, 'Index Fund', 'US', true),
    ('IWM', 'iShares Russell 2000 ETF', 'etf', 'NYSE', 'USD', 218.45, 'Index Fund', 'US', true),
    ('VTI', 'Vanguard Total Stock Market ETF', 'etf', 'NYSE', 'USD', 265.90, 'Index Fund', 'US', true),
    ('VOO', 'Vanguard S&P 500 ETF', 'etf', 'NYSE', 'USD', 520.75, 'Index Fund', 'US', true);

-- =====================================================
-- US ETFs - SECTOR SPECIFIC
-- =====================================================

INSERT INTO public.assets (symbol, name, asset_type, exchange, currency, current_price, industry, region, is_active)
VALUES
    ('VGT', 'Vanguard Information Technology ETF', 'etf', 'NYSE', 'USD', 548.60, 'Technology', 'US', true),
    ('XLF', 'Financial Select Sector SPDR Fund', 'etf', 'NYSE', 'USD', 42.85, 'Banking', 'US', true),
    ('XLE', 'Energy Select Sector SPDR Fund', 'etf', 'NYSE', 'USD', 92.45, 'Energy', 'US', true),
    ('XLV', 'Health Care Select Sector SPDR Fund', 'etf', 'NYSE', 'USD', 158.90, 'Healthcare', 'US', true),
    ('XLK', 'Technology Select Sector SPDR Fund', 'etf', 'NYSE', 'USD', 212.35, 'Technology', 'US', true),
    ('XLI', 'Industrial Select Sector SPDR Fund', 'etf', 'NYSE', 'USD', 128.70, 'Industrial', 'US', true);

-- =====================================================
-- End of US Stocks and ETFs Seed Data
-- =====================================================
