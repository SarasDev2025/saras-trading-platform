-- Migration 21: Add Visual/No-Code Algorithm Builder Support
-- Enables users to build algorithms visually without writing code

-- Add columns to trading_algorithms table
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS builder_type VARCHAR(20) DEFAULT 'code',
ADD COLUMN IF NOT EXISTS visual_config JSONB DEFAULT NULL;

-- Add comment for builder_type
COMMENT ON COLUMN trading_algorithms.builder_type IS 'Type of builder used: code or visual';
COMMENT ON COLUMN trading_algorithms.visual_config IS 'Visual builder configuration (JSON structure of rules and conditions)';

-- Create index on builder_type for filtering
CREATE INDEX IF NOT EXISTS idx_algorithms_builder_type ON trading_algorithms(builder_type);

-- Create algorithm_rule_blocks table for granular visual rule storage
CREATE TABLE IF NOT EXISTS algorithm_rule_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES trading_algorithms(id) ON DELETE CASCADE,
    block_type VARCHAR(50) NOT NULL, -- 'indicator', 'condition', 'action', 'filter'
    block_config JSONB NOT NULL DEFAULT '{}',
    execution_order INTEGER NOT NULL DEFAULT 0,
    parent_block_id UUID REFERENCES algorithm_rule_blocks(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_rule_blocks_algorithm ON algorithm_rule_blocks(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_rule_blocks_type ON algorithm_rule_blocks(block_type);
CREATE INDEX IF NOT EXISTS idx_rule_blocks_order ON algorithm_rule_blocks(algorithm_id, execution_order);
CREATE INDEX IF NOT EXISTS idx_rule_blocks_parent ON algorithm_rule_blocks(parent_block_id);

-- Add comments
COMMENT ON TABLE algorithm_rule_blocks IS 'Individual building blocks for visual algorithm builder';
COMMENT ON COLUMN algorithm_rule_blocks.block_type IS 'Type of rule block: indicator, condition, action, filter';
COMMENT ON COLUMN algorithm_rule_blocks.block_config IS 'Configuration for this rule block (indicator settings, comparison values, etc.)';
COMMENT ON COLUMN algorithm_rule_blocks.execution_order IS 'Order in which this block is evaluated';
COMMENT ON COLUMN algorithm_rule_blocks.parent_block_id IS 'Parent block ID for nested conditions (e.g., AND/OR groups)';

-- Create visual_strategy_templates table
CREATE TABLE IF NOT EXISTS visual_strategy_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'momentum', 'mean_reversion', 'breakout', 'trend_following'
    difficulty_level VARCHAR(20) DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced'
    visual_config JSONB NOT NULL,
    default_parameters JSONB DEFAULT '{}',
    compatible_regions VARCHAR(50)[] DEFAULT ARRAY['IN', 'US', 'GB'],
    compatible_brokers VARCHAR(50)[] DEFAULT ARRAY['zerodha', 'alpaca'],
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_visual_templates_category ON visual_strategy_templates(category);
CREATE INDEX IF NOT EXISTS idx_visual_templates_difficulty ON visual_strategy_templates(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_visual_templates_active ON visual_strategy_templates(is_active);

-- Add comments
COMMENT ON TABLE visual_strategy_templates IS 'Pre-built visual strategy templates for no-code builder';
COMMENT ON COLUMN visual_strategy_templates.visual_config IS 'Complete visual configuration that can be cloned';

-- Insert sample visual strategy templates

-- Template 1: RSI Oversold/Overbought
INSERT INTO visual_strategy_templates (
    name, description, category, difficulty_level, visual_config, default_parameters
) VALUES (
    'RSI Oversold/Overbought',
    'Buy when RSI is oversold (below 30), sell when overbought (above 70). Simple mean reversion strategy.',
    'mean_reversion',
    'beginner',
    '{
        "entry_conditions": [
            {
                "type": "indicator_comparison",
                "indicator": "RSI",
                "period": 14,
                "operator": "below",
                "value": 30
            }
        ],
        "exit_conditions": [
            {
                "type": "indicator_comparison",
                "indicator": "RSI",
                "period": 14,
                "operator": "above",
                "value": 70
            }
        ],
        "position_sizing": {
            "type": "fixed",
            "quantity": 10
        }
    }',
    '{"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70, "position_size": 10}'
);

-- Template 2: Moving Average Crossover
INSERT INTO visual_strategy_templates (
    name, description, category, difficulty_level, visual_config, default_parameters
) VALUES (
    'Moving Average Crossover',
    'Buy when fast MA crosses above slow MA, sell when fast MA crosses below slow MA.',
    'momentum',
    'beginner',
    '{
        "entry_conditions": [
            {
                "type": "indicator_crossover",
                "indicator1": "SMA",
                "period1": 10,
                "indicator2": "SMA",
                "period2": 20,
                "direction": "above"
            }
        ],
        "exit_conditions": [
            {
                "type": "indicator_crossover",
                "indicator1": "SMA",
                "period1": 10,
                "indicator2": "SMA",
                "period2": 20,
                "direction": "below"
            }
        ],
        "position_sizing": {
            "type": "fixed",
            "quantity": 10
        }
    }',
    '{"fast_period": 10, "slow_period": 20, "position_size": 10}'
);

-- Template 3: Price Breakout
INSERT INTO visual_strategy_templates (
    name, description, category, difficulty_level, visual_config, default_parameters
) VALUES (
    'Price Breakout',
    'Buy when price breaks above resistance level with volume confirmation.',
    'breakout',
    'intermediate',
    '{
        "entry_conditions": [
            {
                "type": "price_comparison",
                "compare": "price",
                "operator": "above",
                "reference": "highest_high",
                "lookback_period": 20
            },
            {
                "type": "logical_operator",
                "operator": "AND"
            },
            {
                "type": "volume_comparison",
                "compare": "volume",
                "operator": "above",
                "reference": "average_volume",
                "multiplier": 1.5
            }
        ],
        "exit_conditions": [
            {
                "type": "price_comparison",
                "compare": "price",
                "operator": "below",
                "reference": "SMA",
                "period": 20
            }
        ],
        "position_sizing": {
            "type": "fixed",
            "quantity": 10
        }
    }',
    '{"breakout_period": 20, "volume_multiplier": 1.5, "position_size": 10}'
);

-- Template 4: MACD Momentum
INSERT INTO visual_strategy_templates (
    name, description, category, difficulty_level, visual_config, default_parameters
) VALUES (
    'MACD Momentum',
    'Buy when MACD crosses above signal line, sell when crosses below.',
    'momentum',
    'intermediate',
    '{
        "entry_conditions": [
            {
                "type": "indicator_crossover",
                "indicator1": "MACD",
                "indicator2": "MACD_SIGNAL",
                "direction": "above"
            }
        ],
        "exit_conditions": [
            {
                "type": "indicator_crossover",
                "indicator1": "MACD",
                "indicator2": "MACD_SIGNAL",
                "direction": "below"
            }
        ],
        "position_sizing": {
            "type": "fixed",
            "quantity": 10
        }
    }',
    '{"macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "position_size": 10}'
);

-- Template 5: Bollinger Band Bounce
INSERT INTO visual_strategy_templates (
    name, description, category, difficulty_level, visual_config, default_parameters
) VALUES (
    'Bollinger Band Bounce',
    'Buy when price touches lower band, sell when touches upper band.',
    'mean_reversion',
    'intermediate',
    '{
        "entry_conditions": [
            {
                "type": "price_comparison",
                "compare": "price",
                "operator": "below",
                "reference": "BB_LOWER",
                "period": 20,
                "std_dev": 2
            }
        ],
        "exit_conditions": [
            {
                "type": "price_comparison",
                "compare": "price",
                "operator": "above",
                "reference": "BB_UPPER",
                "period": 20,
                "std_dev": 2
            }
        ],
        "position_sizing": {
            "type": "fixed",
            "quantity": 10
        }
    }',
    '{"bb_period": 20, "bb_std_dev": 2, "position_size": 10}'
);

-- Print success message
SELECT 'Visual algorithm support migration completed successfully!' AS status;
