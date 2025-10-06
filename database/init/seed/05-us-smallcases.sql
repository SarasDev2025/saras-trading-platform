-- =====================================================
-- US Smallcases and Constituents
-- =====================================================
-- Comprehensive US-themed smallcases with constituents
-- Each smallcase has 5-10 stocks with weights summing to exactly 100%

-- Insert US-themed smallcases
INSERT INTO public.smallcases (id, name, description, category, region, risk_level, minimum_investment, is_active, created_at, updated_at) VALUES
(public.uuid_generate_v4(), 'FAANG Leaders', 'Classic FAANG stocks representing the biggest tech giants that have dominated the market. Includes Apple, Amazon, Netflix, Google, and Meta (formerly Facebook).', 'Sector', 'US', 'medium', 2500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Magnificent 7 Tech', 'The magnificent seven technology stocks that have driven market returns. Includes the most influential tech companies with AI and cloud capabilities.', 'Sector', 'US', 'high', 3000.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'S&P 500 Core', 'Diversified blue-chip portfolio representing the backbone of the S&P 500 index. Balanced exposure across sectors for steady long-term growth.', 'Diversified', 'US', 'medium', 2000.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Banking & Financials', 'Leading US banks and financial institutions. Exposure to the core of American financial services with established market leaders.', 'Sector', 'US', 'medium', 1500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Healthcare Innovation', 'Top pharmaceutical and healthcare companies driving medical innovation. Mix of established pharma giants and biotech leaders.', 'Sector', 'US', 'medium', 2000.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Dividend Aristocrats US', 'Reliable dividend-paying companies with decades of consistent dividend growth. Focus on stability and passive income generation.', 'Income', 'US', 'low', 1500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'EV & Clean Energy', 'Electric vehicle manufacturers and renewable energy leaders. High-growth exposure to the transition to sustainable energy.', 'Thematic', 'US', 'high', 2500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Semiconductors & AI', 'Chip manufacturers and AI hardware leaders powering the next generation of computing. Critical infrastructure for AI revolution.', 'Sector', 'US', 'high', 3000.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Consumer Discretionary', 'Leading consumer brands and retailers benefiting from consumer spending trends. Exposure to e-commerce, retail, and lifestyle brands.', 'Sector', 'US', 'medium', 2000.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Cloud & SaaS', 'Cloud computing and software-as-a-service leaders. Pure-play exposure to the digital transformation and enterprise software.', 'Sector', 'US', 'high', 2500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'Energy & Oil', 'Traditional energy giants and oil exploration companies. Exposure to energy sector with focus on established producers.', 'Sector', 'US', 'medium', 1500.00, TRUE, NOW(), NOW()),
(public.uuid_generate_v4(), 'All Weather US Portfolio', 'Diversified portfolio designed to perform across all market conditions. Balanced allocation across sectors, market caps, and risk profiles.', 'Diversified', 'US', 'low', 5000.00, TRUE, NOW(), NOW());

-- =====================================================
-- FAANG Leaders Constituents (5 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'FAANG Leaders'), (SELECT id FROM assets WHERE symbol = 'AAPL'), 22.0),
((SELECT id FROM smallcases WHERE name = 'FAANG Leaders'), (SELECT id FROM assets WHERE symbol = 'AMZN'), 20.0),
((SELECT id FROM smallcases WHERE name = 'FAANG Leaders'), (SELECT id FROM assets WHERE symbol = 'NFLX'), 18.0),
((SELECT id FROM smallcases WHERE name = 'FAANG Leaders'), (SELECT id FROM assets WHERE symbol = 'GOOGL'), 22.0),
((SELECT id FROM smallcases WHERE name = 'FAANG Leaders'), (SELECT id FROM assets WHERE symbol = 'META'), 18.0);

-- =====================================================
-- Magnificent 7 Tech Constituents (7 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'AAPL'), 16.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'MSFT'), 16.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'GOOGL'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'NVDA'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'TSLA'), 13.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'AMZN'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Magnificent 7 Tech'), (SELECT id FROM assets WHERE symbol = 'META'), 11.0);

-- =====================================================
-- S&P 500 Core Constituents (10 stocks, diversified, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'AAPL'), 12.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'MSFT'), 12.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'JPM'), 10.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'JNJ'), 10.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'V'), 10.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'PG'), 9.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'XOM'), 9.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'HD'), 9.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'NVDA'), 10.0),
((SELECT id FROM smallcases WHERE name = 'S&P 500 Core'), (SELECT id FROM assets WHERE symbol = 'UNH'), 9.0);

-- =====================================================
-- Banking & Financials Constituents (7 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'JPM'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'BAC'), 18.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'WFC'), 16.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'GS'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'MS'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'V'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Banking & Financials'), (SELECT id FROM assets WHERE symbol = 'MA'), 8.0);

-- =====================================================
-- Healthcare Innovation Constituents (8 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'JNJ'), 16.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'UNH'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'PFE'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'ABBV'), 13.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'LLY'), 13.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'TMO'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'ABT'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Healthcare Innovation'), (SELECT id FROM assets WHERE symbol = 'MRK'), 9.0);

-- =====================================================
-- Dividend Aristocrats US Constituents (8 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'JNJ'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'PG'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'KO'), 13.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'PEP'), 13.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'MCD'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'XOM'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'CVX'), 11.0),
((SELECT id FROM smallcases WHERE name = 'Dividend Aristocrats US'), (SELECT id FROM assets WHERE symbol = 'WMT'), 11.0);

-- =====================================================
-- EV & Clean Energy Constituents (6 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'TSLA'), 30.0),
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'NIO'), 18.0),
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'ENPH'), 15.0),
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'NEE'), 15.0),
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'RIVN'), 12.0),
((SELECT id FROM smallcases WHERE name = 'EV & Clean Energy'), (SELECT id FROM assets WHERE symbol = 'LCID'), 10.0);

-- =====================================================
-- Semiconductors & AI Constituents (8 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'NVDA'), 25.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'AMD'), 18.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'INTC'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'QCOM'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'AVGO'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'TSM'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'ASML'), 5.0),
((SELECT id FROM smallcases WHERE name = 'Semiconductors & AI'), (SELECT id FROM assets WHERE symbol = 'MU'), 3.0);

-- =====================================================
-- Consumer Discretionary Constituents (8 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'AMZN'), 20.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'TSLA'), 18.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'HD'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'NKE'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'SBUX'), 11.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'MCD'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'LOW'), 8.0),
((SELECT id FROM smallcases WHERE name = 'Consumer Discretionary'), (SELECT id FROM assets WHERE symbol = 'TGT'), 7.0);

-- =====================================================
-- Cloud & SaaS Constituents (7 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'MSFT'), 22.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'AMZN'), 18.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'CRM'), 16.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'ORCL'), 14.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'ADBE'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'GOOGL'), 10.0),
((SELECT id FROM smallcases WHERE name = 'Cloud & SaaS'), (SELECT id FROM assets WHERE symbol = 'NOW'), 8.0);

-- =====================================================
-- Energy & Oil Constituents (6 stocks, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'XOM'), 24.0),
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'CVX'), 22.0),
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'COP'), 18.0),
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'SLB'), 15.0),
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'EOG'), 12.0),
((SELECT id FROM smallcases WHERE name = 'Energy & Oil'), (SELECT id FROM assets WHERE symbol = 'PSX'), 9.0);

-- =====================================================
-- All Weather US Portfolio Constituents (10 stocks, diversified across all sectors, 100% total)
-- =====================================================
INSERT INTO public.smallcase_constituents (smallcase_id, asset_id, weight_percentage) VALUES
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'AAPL'), 11.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'MSFT'), 11.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'JPM'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'JNJ'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'PG'), 9.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'XOM'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'V'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'UNH'), 9.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'HD'), 10.0),
((SELECT id FROM smallcases WHERE name = 'All Weather US Portfolio'), (SELECT id FROM assets WHERE symbol = 'KO'), 10.0);
