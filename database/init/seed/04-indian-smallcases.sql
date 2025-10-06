-- =====================================================
-- Indian Smallcases and Constituents
-- =====================================================
-- This file creates comprehensive Indian-themed smallcases with realistic
-- stock allocations based on stocks from 02-indian-stocks.sql
-- Each smallcase has constituents with weights summing to exactly 100%

-- Insert Indian Smallcases
INSERT INTO public.smallcases (id, name, description, category, region, risk_level, minimum_investment, is_active, created_at, updated_at) VALUES
(public.uuid_generate_v4(), 'Banking & NBFC Focus', 'Concentrated portfolio of top Indian banking and financial services companies with strong fundamentals and market leadership', 'Sector', 'India', 'medium', 15000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'IT Export Leaders', 'Premier Indian IT services companies with global presence and consistent dollar revenue growth', 'Sector', 'India', 'medium', 20000, TRUE, NOW()),
(public.uuid_generate_v4(), 'Consumer Staples Basket', 'Defensive portfolio of leading FMCG and consumer goods companies with pricing power and brand moats', 'Sector', 'India', 'low', 12000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Dividend Aristocrats', 'High dividend yielding PSU and infrastructure stocks for steady passive income generation', 'Income', 'India', 'low', 10000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Growth Momentum Portfolio', 'High-growth companies across sectors with strong earnings momentum and market leadership', 'Growth', 'India', 'high', 25000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Pharma & Healthcare Leaders', 'Top pharmaceutical companies with strong domestic and export presence', 'Sector', 'India', 'medium', 15000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Infrastructure Build India', 'Companies benefiting from infrastructure capex cycle and government spending', 'Thematic', 'India', 'high', 18000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Auto & Ancillaries', 'Leading automobile manufacturers and auto component companies poised for EV transition', 'Sector', 'India', 'high', 15000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Metals & Mining Play', 'Cyclical portfolio of metal producers benefiting from commodity upcycles', 'Sector', 'India', 'high', 12000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'All Weather Balanced', 'Diversified portfolio across sectors for all market conditions with balanced risk-reward', 'Diversified', 'India', 'medium', 20000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Nifty 50 Core', 'Blue-chip portfolio tracking large-cap benchmark constituents for long-term wealth creation', 'Index', 'India', 'low', 15000, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'ESG & Quality Leaders', 'High-quality companies with strong ESG scores and sustainable business practices', 'Thematic', 'India', 'medium', 20000, TRUE, NOW(), NOW());

-- =====================================================
-- Banking & NBFC Focus Constituents (25% HDFC, 25% ICICI, 20% SBI, 15% Kotak, 15% Axis)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Banking & NBFC Focus'), (SELECT id FROM assets WHERE symbol = 'HDFCBANK'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Banking & NBFC Focus'), (SELECT id FROM assets WHERE symbol = 'ICICIBANK'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Banking & NBFC Focus'), (SELECT id FROM assets WHERE symbol = 'SBIN'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Banking & NBFC Focus'), (SELECT id FROM assets WHERE symbol = 'KOTAKBANK'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Banking & NBFC Focus'), (SELECT id FROM assets WHERE symbol = 'AXISBANK'), 15.0);

-- =====================================================
-- IT Export Leaders Constituents (30% TCS, 25% Infy, 20% Wipro, 15% HCL, 10% Tech M)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'IT Export Leaders'), (SELECT id FROM assets WHERE symbol = 'TCS'), 30.0),
((SELECT id FROM smallcases WHERE name = 'IT Export Leaders'), (SELECT id FROM assets WHERE symbol = 'INFY'), 25.0),
((SELECT id FROM smallcases WHERE name = 'IT Export Leaders'), (SELECT id FROM assets WHERE symbol = 'WIPRO'), 20.0),
((SELECT id FROM smallcases WHERE name = 'IT Export Leaders'), (SELECT id FROM assets WHERE symbol = 'HCLTECH'), 15.0),
((SELECT id FROM smallcases WHERE name = 'IT Export Leaders'), (SELECT id FROM assets WHERE symbol = 'TECHM'), 10.0);

-- =====================================================
-- Consumer Staples Basket Constituents (30% HUL, 25% ITC, 25% Nestle, 20% Britannia)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Consumer Staples Basket'), (SELECT id FROM assets WHERE symbol = 'HINDUNILVR'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Staples Basket'), (SELECT id FROM assets WHERE symbol = 'ITC'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Staples Basket'), (SELECT id FROM assets WHERE symbol = 'NESTLEIND'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Staples Basket'), (SELECT id FROM assets WHERE symbol = 'BRITANNIA'), 20.0);

-- =====================================================
-- Dividend Aristocrats Constituents (25% Coal India, 20% ONGC, 20% GAIL, 20% Power Grid, 15% NTPC)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats'), (SELECT id FROM assets WHERE symbol = 'COALINDIA'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats'), (SELECT id FROM assets WHERE symbol = 'ONGC'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats'), (SELECT id FROM assets WHERE symbol = 'GAIL'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats'), (SELECT id FROM assets WHERE symbol = 'POWERGRID'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats'), (SELECT id FROM assets WHERE symbol = 'NTPC'), 15.0);

-- =====================================================
-- Growth Momentum Portfolio Constituents (30% Reliance, 25% Bajaj Finance, 20% Asian Paints, 15% HDFC Life, 10% HDFC Bank)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Growth Momentum Portfolio'), (SELECT id FROM assets WHERE symbol = 'RELIANCE'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Growth Momentum Portfolio'), (SELECT id FROM assets WHERE symbol = 'BAJFINANCE'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Growth Momentum Portfolio'), (SELECT id FROM assets WHERE symbol = 'ASIANPAINT'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Growth Momentum Portfolio'), (SELECT id FROM assets WHERE symbol = 'HDFCLIFE'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Growth Momentum Portfolio'), (SELECT id FROM assets WHERE symbol = 'HDFCBANK'), 10.0);

-- =====================================================
-- Pharma & Healthcare Leaders Constituents (30% Sun Pharma, 25% Dr Reddy, 25% Cipla, 20% Divis Labs)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Pharma & Healthcare Leaders'), (SELECT id FROM assets WHERE symbol = 'SUNPHARMA'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Pharma & Healthcare Leaders'), (SELECT id FROM assets WHERE symbol = 'DRREDDY'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Pharma & Healthcare Leaders'), (SELECT id FROM assets WHERE symbol = 'CIPLA'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Pharma & Healthcare Leaders'), (SELECT id FROM assets WHERE symbol = 'DIVISLAB'), 20.0);

-- =====================================================
-- Infrastructure Build India Constituents (40% L&T, 30% UltraTech, 20% Adani Ports, 10% Power Grid)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Infrastructure Build India'), (SELECT id FROM assets WHERE symbol = 'LT'), 40.0),
((SELECT id FROM smallcases WHERE name = 'Infrastructure Build India'), (SELECT id FROM assets WHERE symbol = 'ULTRACEMCO'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Infrastructure Build India'), (SELECT id FROM assets WHERE symbol = 'ADANIPORTS'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Infrastructure Build India'), (SELECT id FROM assets WHERE symbol = 'POWERGRID'), 10.0);

-- =====================================================
-- Auto & Ancillaries Constituents (30% Maruti, 25% Tata Motors, 25% Bajaj Auto, 20% Hero MotoCorp)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Auto & Ancillaries'), (SELECT id FROM assets WHERE symbol = 'MARUTI'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Auto & Ancillaries'), (SELECT id FROM assets WHERE symbol = 'TATAMOTORS'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Auto & Ancillaries'), (SELECT id FROM assets WHERE symbol = 'BAJAJ-AUTO'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Auto & Ancillaries'), (SELECT id FROM assets WHERE symbol = 'HEROMOTOCO'), 20.0);

-- =====================================================
-- Metals & Mining Play Constituents (30% Tata Steel, 25% Hindalco, 25% JSW Steel, 20% Vedanta)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Metals & Mining Play'), (SELECT id FROM assets WHERE symbol = 'TATASTEEL'), 30.0),
((SELECT id FROM smallcases WHERE name = 'Metals & Mining Play'), (SELECT id FROM assets WHERE symbol = 'HINDALCO'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Metals & Mining Play'), (SELECT id FROM assets WHERE symbol = 'JSWSTEEL'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Metals & Mining Play'), (SELECT id FROM assets WHERE symbol = 'VEDL'), 20.0);

-- =====================================================
-- All Weather Balanced Constituents (Diversified across sectors)
-- 15% Reliance, 12% HDFC Bank, 12% TCS, 10% Infosys, 10% ITC, 10% Asian Paints,
-- 10% L&T, 8% Sun Pharma, 8% Bajaj Finance, 5% NTPC
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'RELIANCE'), 15.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'HDFCBANK'), 12.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'TCS'), 12.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'INFY'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'ITC'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'ASIANPAINT'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'LT'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'SUNPHARMA'), 8.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'BAJFINANCE'), 8.0),
((SELECT id FROM smallcases WHERE name = 'All Weather Balanced'), (SELECT id FROM assets WHERE symbol = 'NTPC'), 5.0);

-- =====================================================
-- Nifty 50 Core Constituents (Top blue-chip large caps)
-- 14% Reliance, 12% HDFC Bank, 11% TCS, 10% Infosys, 9% ICICI Bank, 9% Hindustan Unilever,
-- 8% ITC, 8% HDFC Life, 7% Kotak Bank, 6% SBI, 6% L&T
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'RELIANCE'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'HDFCBANK'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'TCS'), 11.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'INFY'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'ICICIBANK'), 9.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'HINDUNILVR'), 9.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'ITC'), 8.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'HDFCLIFE'), 8.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'KOTAKBANK'), 7.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'SBIN'), 6.0),
((SELECT id FROM smallcases WHERE name = 'Nifty 50 Core'), (SELECT id FROM assets WHERE symbol = 'LT'), 6.0);

-- =====================================================
-- ESG & Quality Leaders Constituents (High-quality sustainable businesses)
-- 15% TCS, 14% Infosys, 13% HDFC Bank, 12% Asian Paints, 11% Hindustan Unilever,
-- 10% Nestle India, 10% Wipro, 8% Britannia, 7% Cipla
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'TCS'), 15.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'INFY'), 14.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'HDFCBANK'), 13.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'ASIANPAINT'), 12.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'HINDUNILVR'), 11.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'NESTLEIND'), 10.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'WIPRO'), 10.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'BRITANNIA'), 8.0),
((SELECT id FROM smallcases WHERE name = 'ESG & Quality Leaders'), (SELECT id FROM assets WHERE symbol = 'CIPLA'), 7.0);
