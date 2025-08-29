-- Create admin user and additional setup for trading platform

-- Insert admin user (password is hashed version of 'admin123')
INSERT INTO users (email, username, password_hash, first_name, last_name, email_verified, kyc_status, account_status) VALUES
('admin@saras-trading.com', 'admin', '$2b$10$K7L/8Y.LvPXyU.aQ8LH8BeN8Z5kQ8H9.dH5VqGZQJ5N.7dQ8H9dQ8', 'Admin', 'User', TRUE, 'approved', 'active');

-- Create admin portfolio with higher cash balance for managing trades
INSERT INTO portfolios (user_id, name, description, cash_balance, total_value)
SELECT 
    id,
    'Admin Trading Portfolio',
    'Administrative portfolio for managing user trades and smallcases',
    100000.00,
    100000.00
FROM users WHERE username = 'admin';

-- Add more diverse assets for smallcases
INSERT INTO assets (symbol, name, asset_type, exchange, currency, current_price, price_updated_at, metadata) VALUES
-- Additional tech stocks
('META', 'Meta Platforms Inc.', 'stock', 'NASDAQ', 'USD', 298.75, CURRENT_TIMESTAMP, '{"sector": "technology", "market_cap": "large"}'),
('AMZN', 'Amazon.com Inc.', 'stock', 'NASDAQ', 'USD', 142.50, CURRENT_TIMESTAMP, '{"sector": "technology", "market_cap": "large"}'),
('NFLX', 'Netflix Inc.', 'stock', 'NASDAQ', 'USD', 425.80, CURRENT_TIMESTAMP, '{"sector": "technology", "market_cap": "large"}'),

-- Financial stocks
('JPM', 'JPMorgan Chase & Co.', 'stock', 'NYSE', 'USD', 158.25, CURRENT_TIMESTAMP, '{"sector": "financial", "market_cap": "large"}'),
('BAC', 'Bank of America Corp.', 'stock', 'NYSE', 'USD', 32.75, CURRENT_TIMESTAMP, '{"sector": "financial", "market_cap": "large"}'),
('GS', 'Goldman Sachs Group Inc.', 'stock', 'NYSE', 'USD', 385.90, CURRENT_TIMESTAMP, '{"sector": "financial", "market_cap": "large"}'),

-- Healthcare stocks
('JNJ', 'Johnson & Johnson', 'stock', 'NYSE', 'USD', 162.40, CURRENT_TIMESTAMP, '{"sector": "healthcare", "market_cap": "large"}'),
('PFE', 'Pfizer Inc.', 'stock', 'NYSE', 'USD', 28.85, CURRENT_TIMESTAMP, '{"sector": "healthcare", "market_cap": "large"}'),
('UNH', 'UnitedHealth Group Inc.', 'stock', 'NYSE', 'USD', 528.75, CURRENT_TIMESTAMP, '{"sector": "healthcare", "market_cap": "large"}'),

-- Energy stocks
('XOM', 'Exxon Mobil Corporation', 'stock', 'NYSE', 'USD', 105.25, CURRENT_TIMESTAMP, '{"sector": "energy", "market_cap": "large"}'),
('CVX', 'Chevron Corporation', 'stock', 'NYSE', 'USD', 148.90, CURRENT_TIMESTAMP, '{"sector": "energy", "market_cap": "large"}');

-- Create smallcases table for predefined investment themes
CREATE TABLE smallcases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    theme VARCHAR(50) NOT NULL,
    minimum_investment DECIMAL(10, 2) DEFAULT 1000.00,
    expected_return DECIMAL(5, 2),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create smallcase_assets table for asset allocation within smallcases
CREATE TABLE smallcase_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    smallcase_id UUID NOT NULL REFERENCES smallcases(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id),
    weight_percentage DECIMAL(5, 2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(smallcase_id, asset_id)
);

-- Create user_smallcase_investments table to track user investments in smallcases
CREATE TABLE user_smallcase_investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    smallcase_id UUID NOT NULL REFERENCES smallcases(id),
    invested_amount DECIMAL(15, 2) NOT NULL,
    current_value DECIMAL(15, 2) DEFAULT 0,
    units DECIMAL(18, 8) NOT NULL,
    investment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'redeemed', 'partial_redeemed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample smallcases
DO $$
DECLARE
    admin_user_id UUID;
    tech_smallcase_id UUID;
    finance_smallcase_id UUID;
    healthcare_smallcase_id UUID;
BEGIN
    -- Get admin user ID
    SELECT id INTO admin_user_id FROM users WHERE username = 'admin';
    
    -- Insert Tech Growth smallcase
    INSERT INTO smallcases (name, description, theme, minimum_investment, expected_return, risk_level, created_by) 
    VALUES ('Tech Growth', 'High-growth technology companies with strong fundamentals', 'technology', 5000.00, 15.50, 'high', admin_user_id)
    RETURNING id INTO tech_smallcase_id;
    
    -- Insert Finance Stability smallcase
    INSERT INTO smallcases (name, description, theme, minimum_investment, expected_return, risk_level, created_by) 
    VALUES ('Finance Stability', 'Stable financial institutions with consistent dividends', 'financial', 3000.00, 8.25, 'medium', admin_user_id)
    RETURNING id INTO finance_smallcase_id;
    
    -- Insert Healthcare Defensive smallcase
    INSERT INTO smallcases (name, description, theme, minimum_investment, expected_return, risk_level, created_by) 
    VALUES ('Healthcare Defensive', 'Defensive healthcare stocks for stable returns', 'healthcare', 4000.00, 10.75, 'low', admin_user_id)
    RETURNING id INTO healthcare_smallcase_id;
    
    -- Add assets to Tech Growth smallcase
    INSERT INTO smallcase_assets (smallcase_id, asset_id, weight_percentage) VALUES
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'AAPL'), 25.00),
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'GOOGL'), 20.00),
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'MSFT'), 20.00),
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'NVDA'), 15.00),
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'META'), 12.00),
    (tech_smallcase_id, (SELECT id FROM assets WHERE symbol = 'NFLX'), 8.00);
    
    -- Add assets to Finance Stability smallcase
    INSERT INTO smallcase_assets (smallcase_id, asset_id, weight_percentage) VALUES
    (finance_smallcase_id, (SELECT id FROM assets WHERE symbol = 'JPM'), 35.00),
    (finance_smallcase_id, (SELECT id FROM assets WHERE symbol = 'BAC'), 30.00),
    (finance_smallcase_id, (SELECT id FROM assets WHERE symbol = 'GS'), 25.00),
    (finance_smallcase_id, (SELECT id FROM assets WHERE symbol = 'XOM'), 10.00);
    
    -- Add assets to Healthcare Defensive smallcase
    INSERT INTO smallcase_assets (smallcase_id, asset_id, weight_percentage) VALUES
    (healthcare_smallcase_id, (SELECT id FROM assets WHERE symbol = 'JNJ'), 40.00),
    (healthcare_smallcase_id, (SELECT id FROM assets WHERE symbol = 'UNH'), 35.00),
    (healthcare_smallcase_id, (SELECT id FROM assets WHERE symbol = 'PFE'), 25.00);
    
END $$;

-- Add indexes for new tables
CREATE INDEX idx_smallcases_theme ON smallcases(theme);
CREATE INDEX idx_smallcases_active ON smallcases(is_active);
CREATE INDEX idx_smallcase_assets_smallcase_id ON smallcase_assets(smallcase_id);
CREATE INDEX idx_user_smallcase_investments_user_id ON user_smallcase_investments(user_id);
CREATE INDEX idx_user_smallcase_investments_portfolio_id ON user_smallcase_investments(portfolio_id);
CREATE INDEX idx_user_smallcase_investments_smallcase_id ON user_smallcase_investments(smallcase_id);

-- Add triggers for updated_at columns
CREATE TRIGGER update_smallcases_updated_at BEFORE UPDATE ON smallcases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_smallcase_investments_updated_at BEFORE UPDATE ON user_smallcase_investments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
