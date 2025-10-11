"""
Abstract Base Class for Historical Data Providers
Defines the interface that all data providers must implement
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional
import pandas as pd


class HistoricalDataProvider(ABC):
    """
    Abstract base class for historical market data providers

    All providers must implement get_historical_data to return OHLCV data
    in a standardized pandas DataFrame format
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize provider with optional configuration

        Args:
            config: Provider-specific configuration (API keys, etc.)
        """
        self.config = config or {}

    @abstractmethod
    async def get_historical_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        region: str = 'US'
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical OHLCV data for given symbols

        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'MSFT'])
            start_date: Start date for historical data
            end_date: End date for historical data
            region: Market region ('US', 'IN', etc.)

        Returns:
            Dict mapping symbol to DataFrame with columns:
                - date: pd.Timestamp
                - open: float
                - high: float
                - low: float
                - close: float
                - volume: int

        Raises:
            Exception: If data fetch fails
        """
        pass

    async def validate_connection(self) -> bool:
        """
        Validate that the provider can connect and fetch data

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to fetch a single day of data for a common symbol
            test_symbol = 'AAPL' if self.config.get('region', 'US') == 'US' else 'RELIANCE'
            result = await self.get_historical_data(
                symbols=[test_symbol],
                start_date=date.today(),
                end_date=date.today(),
                region=self.config.get('region', 'US')
            )
            return len(result) > 0
        except Exception:
            return False

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame has required columns and format

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        required_columns = {'date', 'open', 'high', 'low', 'close', 'volume'}
        return required_columns.issubset(df.columns)

    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame to standard format

        Args:
            df: Raw DataFrame from provider

        Returns:
            Normalized DataFrame with standard columns
        """
        # Ensure date column
        if 'date' not in df.columns and df.index.name in ['Date', 'date', 'timestamp']:
            df = df.reset_index()
            df.rename(columns={df.columns[0]: 'date'}, inplace=True)

        # Standardize column names (lowercase)
        df.columns = df.columns.str.lower()

        # Ensure datetime type
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        # Sort by date
        df = df.sort_values('date')

        return df
