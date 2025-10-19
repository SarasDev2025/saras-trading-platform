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

short_period = parameters.get(''short_period'', 10)
long_period = parameters.get(''long_period'', 20)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    indicators = data.get(''indicators'', {})
    short_sma = indicators.get(f''sma_{short_period}'')
    long_sma = indicators.get(f''sma_{long_period}'')

    if short_sma is None or long_sma is None:
        continue

    current_price = data.get(''price'', 0)
    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)
    open_positions = sum(1 for p in positions if p.get(''quantity'', 0) > 0)

    if existing_position:
        if short_sma < long_sma:
            generate_signal(
                symbol=symbol,
                signal_type=''sell'',
                quantity=existing_position[''quantity''],
                reason=f''Short SMA crossed below long SMA at ${current_price}''
            )
    else:
        if open_positions >= max_positions:
            continue

        if short_sma > long_sma:
            generate_signal(
                symbol=symbol,
                signal_type=''buy'',
                quantity=position_size,
                reason=f''Short SMA crossed above long SMA at ${current_price}''
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
rsi_period = parameters.get(''rsi_period'', 14)
position_size = parameters.get(''position_size'', 10)

for symbol, data in market_data.items():
    indicators = data.get(''indicators'', {})
    rsi_value = indicators.get(f''rsi_{rsi_period}'')

    if rsi_value is None:
        continue

    current_price = data.get(''price'', 0)
    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)
    open_positions = sum(1 for p in positions if p.get(''quantity'', 0) > 0)

    if not existing_position and rsi_value <= oversold_threshold:
        if open_positions >= max_positions:
            continue

        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''RSI {rsi_value:.2f} <= {oversold_threshold}''
        )
    elif existing_position and rsi_value >= overbought_threshold:
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''RSI {rsi_value:.2f} >= {overbought_threshold}''
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
    indicators = data.get(''indicators'', {})
    lower_band = indicators.get(f''bb_lower_{bb_period}'') or indicators.get(''bb_lower'')
    upper_band = indicators.get(f''bb_upper_{bb_period}'') or indicators.get(''bb_upper'')

    if lower_band is None or upper_band is None:
        continue

    current_price = data.get(''price'', 0)
    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)
    open_positions = sum(1 for p in positions if p.get(''quantity'', 0) > 0)

    if not existing_position and current_price <= lower_band:
        if open_positions >= max_positions:
            continue

        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''Price ${current_price} touched lower band ${lower_band:.2f}''
        )
    elif existing_position and current_price >= upper_band:
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''Price ${current_price} touched upper band ${upper_band:.2f}''
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
    indicators = data.get(''indicators'', {})
    macd_value = indicators.get(''macd'')
    macd_signal_value = indicators.get(''macd_signal'')

    if macd_value is None or macd_signal_value is None:
        continue

    current_price = data.get(''price'', 0)
    if current_price == 0:
        continue

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)
    open_positions = sum(1 for p in positions if p.get(''quantity'', 0) > 0)

    if not existing_position and macd_value > macd_signal_value:
        if open_positions >= max_positions:
            continue

        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''MACD ({macd_value:.2f}) crossed above signal ({macd_signal_value:.2f})''
        )
    elif existing_position and macd_value < macd_signal_value:
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''MACD ({macd_value:.2f}) crossed below signal ({macd_signal_value:.2f})''
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
    indicators = data.get(''indicators'', {})
    current_price = data.get(''price'', 0)
    avg_volume = indicators.get(''avg_volume'')
    current_volume = indicators.get(''volume_sma_20'', avg_volume)
    recent_high = indicators.get(''sma_200'')
    recent_low = indicators.get(''sma_50'')

    if current_price == 0 or avg_volume is None:
        continue

    volume_ratio = current_volume / avg_volume if avg_volume else 0

    existing_position = next((p for p in positions if p[''symbol''] == symbol), None)
    open_positions = sum(1 for p in positions if p.get(''quantity'', 0) > 0)

    breakout_price = recent_high * (1 + breakout_pct / 100) if recent_high else current_price
    breakdown_price = recent_low * (1 - breakout_pct / 100) if recent_low else current_price

    if not existing_position and volume_ratio >= volume_threshold and current_price >= breakout_price:
        if open_positions >= max_positions:
            continue

        generate_signal(
            symbol=symbol,
            signal_type=''buy'',
            quantity=position_size,
            reason=f''Volume ratio {volume_ratio:.2f} >= {volume_threshold} with breakout price ${current_price}''
        )
    elif existing_position and volume_ratio >= volume_threshold and current_price <= breakdown_price:
        generate_signal(
            symbol=symbol,
            signal_type=''sell'',
            quantity=existing_position[''quantity''],
            reason=f''Volume ratio {volume_ratio:.2f} >= {volume_threshold} with breakdown price ${current_price}''
        )',
    '{"volume_threshold": 1.5, "breakout_pct": 2.0, "position_size": 10}',
    ARRAY['IN', 'US', 'GB'],
    ARRAY['zerodha', 'alpaca'],
    'advanced'
);

-- Print success message
SELECT 'Algorithm templates seeded successfully!' AS status;
