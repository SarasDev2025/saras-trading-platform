"""
Synthetic Data Provider
Generates random walk price data for testing and fallback
"""
import logging
from datetime import date
from typing import Dict, List
import pandas as pd
import numpy as np

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


class SyntheticDataProvider(HistoricalDataProvider):
    """
    Provider that generates synthetic historical data using random walk

    Useful for:
    - Testing and development
    - Fallback when real data providers fail
    - Demo purposes

    NOT suitable for actual trading decisions
    """

    async def get_historical_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        region: str = 'US'
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic historical data using random walk

        Args:
            symbols: List of stock symbols
            start_date: Start date
            end_date: End date
            region: Market region (not used for synthetic data)

        Returns:
            Dict mapping symbol to synthetic OHLCV DataFrame
        """
        historical_data = {}

        for symbol in symbols:
            try:
                # Generate synthetic price based on symbol hash
                base_price = self._get_base_price(symbol)

                # Generate daily prices with random walk
                days = (end_date - start_date).days + 1
                dates = pd.date_range(start=start_date, end=end_date, freq='D')

                # Simple random walk for demo purposes
                # Use symbol hash as seed for consistency
                np.random.seed(hash(symbol) % 2**32)

                # Generate returns with slight upward drift
                returns = np.random.normal(0.0005, 0.02, days)
                prices = base_price * np.exp(np.cumsum(returns))

                # Generate OHLCV data
                df = pd.DataFrame({
                    'date': dates[:len(prices)],
                    'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(prices))),
                    'high': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
                    'low': prices * (1 - np.random.uniform(0, 0.02, len(prices))),
                    'close': prices,
                    'volume': np.random.randint(100000, 10000000, len(prices))
                })

                # Ensure data types
                df['date'] = pd.to_datetime(df['date'])
                df['volume'] = df['volume'].astype(int)

                historical_data[symbol] = df

                logger.info(f"Generated {len(df)} synthetic data points for {symbol}")

            except Exception as e:
                logger.error(f"Failed to generate synthetic data for {symbol}: {e}")

        return historical_data

    def _get_base_price(self, symbol: str) -> float:
        """
        Get a consistent base price for a symbol

        Uses symbol hash to generate a price between $10 and $500

        Args:
            symbol: Stock symbol

        Returns:
            Base price for the symbol
        """
        # Generate consistent price based on symbol hash
        symbol_hash = hash(symbol) % 10000
        # Map to price range $10 - $500
        base_price = 10 + (symbol_hash / 10000) * 490

        return base_price

    async def validate_connection(self) -> bool:
        """
        Synthetic provider is always available

        Returns:
            Always True
        """
        return True
