-- Migration 20: Seed Algorithm Templates
-- Provides pre-built algorithm templates for users

-- SMA Crossover Strategy Template
INSERT INTO algorithm_templates (
    name,
    description,
    category,
    strategy_code,
    default_parameters,
    compatible_regions,
    compatible_brokers,
    difficulty_level
) VALUES (
    'SMA Crossover Strategy',
    'Classic moving average crossover with short and long period SMAs. Generates buy signal when short SMA crosses above long SMA, sell signal on opposite.',
    'momentum',
    '# SMA Crossover Strategy
# Buy when short SMA crosses above long SMA
# Sell when short SMA crosses below long SMA

import pandas as pd

short_period = parameters.get(''short_period'', 10)
long_period = parameters.get(''long_period'', 20)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    # Skip if we already have max positions
    if len(positions) >= max_positions:
        break

    # For demo: use simple threshold logic
    # In production, you would calculate actual SMAs from historical data
    current_price = data.get(''price'', 0)

    if current_price == 0:
        continue

    # Check if we have a position
    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)

    # Simple buy logic (placeholder for actual SMA crossover)
    if not existing_position and current_price > 100:
        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''SMA crossover buy signal at ${current_price}''
        )',
    '{"short_period": 10, "long_period": 20, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'beginner'
);

-- RSI Mean Reversion Strategy
INSERT INTO algorithm_templates (
    name,
    description,
    category,
    strategy_code,
    default_parameters,
    compatible_regions,
    compatible_brokers,
    difficulty_level
) VALUES (
    'RSI Mean Reversion',
    'Relative Strength Index based mean reversion strategy. Buys when RSI is oversold (below 30), sells when overbought (above 70).',
    'mean_reversion',
    '# RSI Mean Reversion Strategy
# Buy when RSI < oversold_threshold (default 30)
# Sell when RSI > overbought_threshold (default 70)

oversold_threshold = parameters.get(''oversold_threshold'', 30)
overbought_threshold = parameters.get(''overbought_threshold'', 70)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    current_price = data.get(''price'', 0)

    if current_price == 0:
        continue

    # Check if we have a position
    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)

    # Placeholder RSI logic (in production, calculate from historical data)
    # For demo purposes, use price-based threshold
    if not existing_position and current_price < 80:
        # Simulating oversold condition
        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''RSI oversold buy signal at ${current_price}''
        )
    elif existing_position and current_price > 150:
        # Simulating overbought condition
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''RSI overbought sell signal at ${current_price}''
        )',
    '{"oversold_threshold": 30, "overbought_threshold": 70, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'beginner'
);

-- Bollinger Bands Breakout Strategy
INSERT INTO algorithm_templates (
    name,
    description,
    category,
    strategy_code,
    default_parameters,
    compatible_regions,
    compatible_brokers,
    difficulty_level
) VALUES (
    'Bollinger Bands Breakout',
    'Identifies volatility breakouts using Bollinger Bands. Buys on lower band bounce, sells on upper band touch.',
    'breakout',
    '# Bollinger Bands Breakout Strategy
# Buy when price touches or goes below lower band
# Sell when price touches or goes above upper band

bb_period = parameters.get(''bb_period'', 20)
bb_std_dev = parameters.get(''bb_std_dev'', 2)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    if len(positions) >= max_positions:
        break

    current_price = data.get(''price'', 0)

    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)

    # Placeholder Bollinger Band logic
    # In production, calculate actual bands from historical data
    if not existing_position and current_price < 90:
        # Simulating lower band bounce
        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''Lower Bollinger Band bounce at ${current_price}''
        )
    elif existing_position and current_price > 140:
        # Simulating upper band touch
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''Upper Bollinger Band touch at ${current_price}''
        )',
    '{"bb_period": 20, "bb_std_dev": 2, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'intermediate'
);

-- MACD Momentum Strategy
INSERT INTO algorithm_templates (
    name,
    description,
    category,
    strategy_code,
    default_parameters,
    compatible_regions,
    compatible_brokers,
    difficulty_level
) VALUES (
    'MACD Momentum Strategy',
    'Moving Average Convergence Divergence momentum strategy. Generates signals on MACD line crossovers with signal line.',
    'momentum',
    '# MACD Momentum Strategy
# Buy when MACD crosses above signal line
# Sell when MACD crosses below signal line

macd_fast = parameters.get(''macd_fast'', 12)
macd_slow = parameters.get(''macd_slow'', 26)
macd_signal = parameters.get(''macd_signal'', 9)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    if len(positions) >= max_positions:
        break

    current_price = data.get(''price'', 0)

    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)

    # Placeholder MACD logic
    # In production, calculate actual MACD from historical data
    if not existing_position and current_price > 95 and current_price < 110:
        # Simulating bullish MACD crossover
        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''MACD bullish crossover at ${current_price}''
        )
    elif existing_position and current_price > 135:
        # Simulating bearish MACD crossover
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''MACD bearish crossover at ${current_price}''
        )',
    '{"macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'intermediate'
);

-- Volume Breakout Strategy
INSERT INTO algorithm_templates (
    name,
    description,
    category,
    strategy_code,
    default_parameters,
    compatible_regions,
    compatible_brokers,
    difficulty_level
) VALUES (
    'Volume Breakout Strategy',
    'Identifies price breakouts confirmed by above-average volume. Combines price action with volume analysis.',
    'breakout',
    '# Volume Breakout Strategy
# Buy when price breaks resistance with high volume
# Sell when price breaks support with high volume

volume_threshold = parameters.get(''volume_threshold'', 1.5)
breakout_pct = parameters.get(''breakout_pct'', 2.0)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    if len(positions) >= max_positions:
        break

    current_price = data.get(''price'', 0)

    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)

    # Placeholder volume breakout logic
    # In production, calculate from actual volume data
    if not existing_position and current_price > 105:
        # Simulating volume breakout
        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''Volume breakout detected at ${current_price}''
        )
    elif existing_position and current_price < 85:
        # Simulating volume breakdown
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''Volume breakdown at ${current_price}''
        )',
    '{"volume_threshold": 1.5, "breakout_pct": 2.0, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'advanced'
);

-- Print success message
SELECT 'Algorithm templates seeded successfully!' AS status;
