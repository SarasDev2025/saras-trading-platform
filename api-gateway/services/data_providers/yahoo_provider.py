"""
Yahoo Finance Historical Data Provider
Uses yfinance library to fetch real historical market data
"""
import logging
from datetime import date
from typing import Dict, List
import pandas as pd

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(HistoricalDataProvider):
    """
    Provider for Yahoo Finance historical data

    Supports both US and Indian stocks
    Free to use, no API key required
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            logger.error("yfinance library not installed. Install with: pip install yfinance")
            raise ImportError("yfinance library required for YahooFinanceProvider")

    async def get_historical_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        region: str = 'US'
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data from Yahoo Finance

        Args:
            symbols: List of stock symbols
            start_date: Start date
            end_date: End date
            region: Market region (used for symbol formatting)

        Returns:
            Dict mapping symbol to OHLCV DataFrame
        """
        historical_data = {}

        for symbol in symbols:
            try:
                # Format symbol for Indian stocks (add .NS or .BO suffix)
                yahoo_symbol = self._format_symbol(symbol, region)

                logger.info(f"Fetching historical data for {yahoo_symbol} from {start_date} to {end_date}")

                # Fetch data using yfinance
                ticker = self.yf.Ticker(yahoo_symbol)
                df = ticker.history(start=start_date, end=end_date)

                if df.empty:
                    logger.warning(f"No data returned for {yahoo_symbol}")
                    continue

                # Normalize column names and format
                df = df.reset_index()
                df.columns = df.columns.str.lower()

                # Rename 'date' column if it's 'index'
                if 'index' in df.columns:
                    df.rename(columns={'index': 'date'}, inplace=True)

                # Ensure required columns exist
                required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    logger.warning(f"Missing columns {missing_cols} for {symbol}, skipping")
                    continue

                # Select and order columns
                df = df[required_cols].copy()

                # Ensure proper types
                df['date'] = pd.to_datetime(df['date'])
                df['volume'] = df['volume'].astype(int)

                # Validate and normalize
                df = self.normalize_dataframe(df)

                # Store using original symbol (without suffix)
                historical_data[symbol] = df

                logger.info(f"Successfully fetched {len(df)} data points for {symbol}")

            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                # Continue with other symbols even if one fails

        return historical_data

    def _format_symbol(self, symbol: str, region: str) -> str:
        """
        Format symbol for Yahoo Finance

        Yahoo Finance uses different suffixes for different exchanges:
        - India NSE: .NS (e.g., RELIANCE.NS)
        - India BSE: .BO (e.g., RELIANCE.BO)
        - US: No suffix (e.g., AAPL)

        Args:
            symbol: Original symbol
            region: Market region

        Returns:
            Formatted symbol for Yahoo Finance
        """
        # If symbol already has a suffix, return as-is
        if '.' in symbol:
            return symbol

        # Add suffix based on region
        if region == 'IN':
            # Default to NSE for Indian stocks
            return f"{symbol}.NS"
        else:
            # US and other markets don't need suffix
            return symbol

    async def validate_connection(self) -> bool:
        """
        Validate Yahoo Finance connection

        Returns:
            True if can fetch data
        """
        try:
            from datetime import timedelta
            today = date.today()
            yesterday = today - timedelta(days=7)  # Use 7 days ago to avoid weekend issues

            result = await self.get_historical_data(
                symbols=['AAPL'],
                start_date=yesterday,
                end_date=today,
                region='US'
            )

            return len(result) > 0 and 'AAPL' in result

        except Exception as e:
            logger.error(f"Yahoo Finance validation failed: {e}")
            return False
