"""
Visual Algorithm Compiler Service
Converts visual/no-code configurations into executable Python algorithm code
"""
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class VisualAlgorithmCompiler:
    """Compiles visual algorithm configurations into Python code"""

    # Available building blocks for the visual builder
    AVAILABLE_BLOCKS = {
        "indicators": [
            {"id": "RSI", "name": "RSI (Relative Strength Index)", "params": ["period"]},
            {"id": "SMA", "name": "Simple Moving Average", "params": ["period"]},
            {"id": "EMA", "name": "Exponential Moving Average", "params": ["period"]},
            {"id": "MACD", "name": "MACD", "params": ["fast", "slow", "signal"]},
            {"id": "BB_UPPER", "name": "Bollinger Band Upper", "params": ["period", "std_dev"]},
            {"id": "BB_LOWER", "name": "Bollinger Band Lower", "params": ["period", "std_dev"]},
            {"id": "VOLUME", "name": "Volume", "params": []},
        ],
        "comparisons": [
            {"id": "above", "name": "is above", "symbol": ">"},
            {"id": "below", "name": "is below", "symbol": "<"},
            {"id": "equals", "name": "equals", "symbol": "=="},
            {"id": "above_or_equal", "name": "is above or equal to", "symbol": ">="},
            {"id": "below_or_equal", "name": "is below or equal to", "symbol": "<="},
        ],
        "logical_operators": [
            {"id": "AND", "name": "AND"},
            {"id": "OR", "name": "OR"},
        ],
        "references": [
            {"id": "price", "name": "Current Price"},
            {"id": "volume", "name": "Current Volume"},
            {"id": "SMA", "name": "Moving Average"},
            {"id": "highest_high", "name": "Highest High"},
            {"id": "lowest_low", "name": "Lowest Low"},
            {"id": "average_volume", "name": "Average Volume"},
        ],
        "position_sizing": [
            {"id": "fixed", "name": "Fixed Quantity"},
            {"id": "percent_portfolio", "name": "Percent of Portfolio"},
            {"id": "risk_based", "name": "Risk-Based"},
        ],
    }

    @staticmethod
    def get_available_blocks() -> Dict[str, List[Dict[str, Any]]]:
        """Get all available building blocks for the visual builder"""
        return VisualAlgorithmCompiler.AVAILABLE_BLOCKS

    @staticmethod
    def compile_visual_to_code(visual_config: Dict[str, Any]) -> str:
        """
        Convert visual configuration to executable Python code

        Args:
            visual_config: Visual builder configuration

        Returns:
            Python code string
        """
        try:
            entry_conditions = visual_config.get('entry_conditions', [])
            exit_conditions = visual_config.get('exit_conditions', [])
            position_sizing = visual_config.get('position_sizing', {'type': 'fixed', 'quantity': 10})
            risk_management = visual_config.get('risk_management', {})

            # Generate code
            code_parts = []

            # Header
            code_parts.append("# Auto-generated from Visual Builder")
            code_parts.append("# This code was automatically created from your visual configuration")
            code_parts.append("")

            # Get parameters
            code_parts.append("# Get position sizing configuration")
            quantity = position_sizing.get('quantity', 10)
            code_parts.append(f"position_size = parameters.get('position_size', {quantity})")
            code_parts.append("")

            # Main loop
            code_parts.append("# Iterate through available market data")
            code_parts.append("for symbol, data in market_data.items():")
            code_parts.append("    # Skip if we already have max positions")
            code_parts.append("    if len(positions) >= max_positions:")
            code_parts.append("        break")
            code_parts.append("")
            code_parts.append("    current_price = data.get('price', 0)")
            code_parts.append("    current_volume = data.get('volume', 0)")
            code_parts.append("")
            code_parts.append("    if current_price == 0:")
            code_parts.append("        continue")
            code_parts.append("")

            # Check existing position
            code_parts.append("    # Check if we have an existing position")
            code_parts.append("    existing_position = next((p for p in positions if p['symbol'] == symbol), None)")
            code_parts.append("")

            # Entry conditions
            if entry_conditions:
                code_parts.append("    # Entry Conditions")
                code_parts.append("    if not existing_position:")
                entry_condition_code = VisualAlgorithmCompiler._generate_condition_code(
                    entry_conditions, indent=2
                )
                code_parts.append(f"        if {entry_condition_code}:")

                # Generate buy signal
                reason = VisualAlgorithmCompiler._generate_reason(entry_conditions, "entry")
                code_parts.append("            generate_signal(")
                code_parts.append("                symbol=symbol,")
                code_parts.append("                signal_type='buy',")
                code_parts.append("                quantity=position_size,")
                code_parts.append(f"                reason='{reason}'")
                code_parts.append("            )")
                code_parts.append("")

            # Exit conditions
            if exit_conditions:
                code_parts.append("    # Exit Conditions")
                code_parts.append("    elif existing_position:")
                exit_condition_code = VisualAlgorithmCompiler._generate_condition_code(
                    exit_conditions, indent=2
                )
                code_parts.append(f"        if {exit_condition_code}:")

                # Generate sell signal
                reason = VisualAlgorithmCompiler._generate_reason(exit_conditions, "exit")
                code_parts.append("            generate_signal(")
                code_parts.append("                symbol=symbol,")
                code_parts.append("                signal_type='sell',")
                code_parts.append("                quantity=existing_position['quantity'],")
                code_parts.append(f"                reason='{reason}'")
                code_parts.append("            )")

            return "\n".join(code_parts)

        except Exception as e:
            logger.error(f"Failed to compile visual config: {e}")
            raise ValueError(f"Compilation error: {str(e)}")

    @staticmethod
    def _generate_condition_code(conditions: List[Dict[str, Any]], indent: int = 0) -> str:
        """Generate Python condition code from visual conditions"""
        condition_parts = []
        logical_op = " and "  # Default to AND

        for condition in conditions:
            condition_type = condition.get('type')

            if condition_type == 'logical_operator':
                # Set the logical operator for next condition
                op = condition.get('operator', 'AND')
                logical_op = " and " if op == "AND" else " or "
                continue

            elif condition_type == 'indicator_comparison':
                # RSI < 30, SMA > 50, etc.
                indicator = condition.get('indicator')
                operator = condition.get('operator')
                value = condition.get('value')
                period = condition.get('period', 14)

                # Generate indicator calculation (simplified)
                if indicator == 'RSI':
                    indicator_var = f"(50)"  # Placeholder - would use actual RSI calculation
                    comparison = VisualAlgorithmCompiler._get_operator_symbol(operator)
                    condition_parts.append(f"{indicator_var} {comparison} {value}")

                elif indicator in ['SMA', 'EMA']:
                    condition_parts.append(f"current_price {VisualAlgorithmCompiler._get_operator_symbol(operator)} (100)")  # Placeholder

            elif condition_type == 'price_comparison':
                # Price > SMA, Price < BB_LOWER, etc.
                reference = condition.get('reference')
                operator = condition.get('operator')
                comparison = VisualAlgorithmCompiler._get_operator_symbol(operator)

                if reference == 'SMA':
                    period = condition.get('period', 20)
                    condition_parts.append(f"current_price {comparison} (100)")  # Placeholder SMA
                elif reference == 'price':
                    value = condition.get('value', 0)
                    condition_parts.append(f"current_price {comparison} {value}")
                elif reference == 'highest_high':
                    lookback = condition.get('lookback_period', 20)
                    condition_parts.append(f"current_price {comparison} (150)")  # Placeholder
                elif reference == 'lowest_low':
                    lookback = condition.get('lookback_period', 20)
                    condition_parts.append(f"current_price {comparison} (80)")  # Placeholder

            elif condition_type == 'indicator_crossover':
                # MA crossover: fast SMA crosses above slow SMA
                indicator1 = condition.get('indicator1')
                period1 = condition.get('period1', 10)
                indicator2 = condition.get('indicator2')
                period2 = condition.get('period2', 20)
                direction = condition.get('direction', 'above')

                comparison = ">" if direction == "above" else "<"
                condition_parts.append(f"(100) {comparison} (120)")  # Placeholder crossover logic

            elif condition_type == 'volume_comparison':
                # Volume comparison
                operator = condition.get('operator')
                multiplier = condition.get('multiplier', 1.5)
                comparison = VisualAlgorithmCompiler._get_operator_symbol(operator)
                condition_parts.append(f"current_volume {comparison} (1000 * {multiplier})")  # Placeholder

        # Join conditions with logical operator
        if condition_parts:
            return logical_op.join(condition_parts)
        return "True"

    @staticmethod
    def _get_operator_symbol(operator: str) -> str:
        """Convert operator name to Python symbol"""
        operator_map = {
            'above': '>',
            'below': '<',
            'equals': '==',
            'above_or_equal': '>=',
            'below_or_equal': '<=',
        }
        return operator_map.get(operator, '==')

    @staticmethod
    def _generate_reason(conditions: List[Dict[str, Any]], signal_type: str) -> str:
        """Generate a human-readable reason for the signal"""
        condition_descriptions = []

        for condition in conditions:
            condition_type = condition.get('type')

            if condition_type == 'indicator_comparison':
                indicator = condition.get('indicator')
                operator = condition.get('operator')
                value = condition.get('value')
                condition_descriptions.append(f"{indicator} {operator} {value}")

            elif condition_type == 'price_comparison':
                reference = condition.get('reference')
                operator = condition.get('operator')
                condition_descriptions.append(f"Price {operator} {reference}")

            elif condition_type == 'indicator_crossover':
                indicator1 = condition.get('indicator1')
                indicator2 = condition.get('indicator2')
                direction = condition.get('direction')
                condition_descriptions.append(f"{indicator1} crosses {direction} {indicator2}")

        if condition_descriptions:
            return f"Visual {signal_type}: " + " and ".join(condition_descriptions[:2])  # Limit to 2 conditions
        return f"Visual {signal_type} signal"

    @staticmethod
    def validate_visual_config(visual_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate visual configuration

        Returns:
            Dict with 'valid' boolean and optional 'error' message
        """
        try:
            # Check required fields
            if 'entry_conditions' not in visual_config and 'exit_conditions' not in visual_config:
                return {
                    'valid': False,
                    'error': 'At least one entry or exit condition is required'
                }

            entry_conditions = visual_config.get('entry_conditions', [])
            exit_conditions = visual_config.get('exit_conditions', [])

            # Validate entry conditions
            if entry_conditions:
                validation = VisualAlgorithmCompiler._validate_conditions(entry_conditions)
                if not validation['valid']:
                    return validation

            # Validate exit conditions
            if exit_conditions:
                validation = VisualAlgorithmCompiler._validate_conditions(exit_conditions)
                if not validation['valid']:
                    return validation

            # Validate position sizing
            position_sizing = visual_config.get('position_sizing', {})
            if not position_sizing:
                return {
                    'valid': False,
                    'error': 'Position sizing configuration is required'
                }

            sizing_type = position_sizing.get('type')
            if sizing_type not in ['fixed', 'percent_portfolio', 'risk_based']:
                return {
                    'valid': False,
                    'error': f'Invalid position sizing type: {sizing_type}'
                }

            return {'valid': True, 'message': 'Visual configuration is valid'}

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    @staticmethod
    def _validate_conditions(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a list of conditions"""
        valid_condition_types = [
            'indicator_comparison',
            'price_comparison',
            'indicator_crossover',
            'volume_comparison',
            'logical_operator'
        ]

        for i, condition in enumerate(conditions):
            condition_type = condition.get('type')

            if not condition_type:
                return {
                    'valid': False,
                    'error': f'Condition {i+1}: type is required'
                }

            if condition_type not in valid_condition_types:
                return {
                    'valid': False,
                    'error': f'Condition {i+1}: invalid type "{condition_type}"'
                }

            # Type-specific validation
            if condition_type == 'indicator_comparison':
                if 'indicator' not in condition:
                    return {'valid': False, 'error': f'Condition {i+1}: indicator is required'}
                if 'operator' not in condition:
                    return {'valid': False, 'error': f'Condition {i+1}: operator is required'}
                if 'value' not in condition:
                    return {'valid': False, 'error': f'Condition {i+1}: value is required'}

        return {'valid': True}
