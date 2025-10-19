"""
Data Aggregator Service
Background service that continuously fetches market data and calculates indicators
Stores results in Redis cache for fast access by algorithm execution engine
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from sqlalchemy import text

from services.redis_cache_service import get_cache_service, RedisCacheService
from services.symbol_subscription_manager import get_subscription_manager, SymbolSubscriptionManager
from services.data_providers.factory import DataProviderFactory
from services.market_hours_service import is_market_open
from brokers import broker_manager, AlpacaBroker

logger = logging.getLogger(__name__)


class DataAggregatorService:
    """
    Background service for aggregating market data and calculating indicators

    Runs periodic tasks to:
    1. Fetch OHLCV bars for subscribed symbols
    2. Calculate technical indicators (RSI, SMA, EMA, MACD, Bollinger Bands)
    3. Store results in Redis cache with appropriate TTLs
    """

    def __init__(
        self,
        cache_service: RedisCacheService,
        subscription_manager: SymbolSubscriptionManager,
        db_session_factory
    ):
        """
        Initialize Data Aggregator Service

        Args:
            cache_service: Redis cache service instance
            subscription_manager: Symbol subscription manager instance
            db_session_factory: Database session factory for querying algorithms
        """
        self.cache_service = cache_service
        self.subscription_manager = subscription_manager
        self.db_session_factory = db_session_factory

        # Background task control
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Fetch intervals (in seconds)
        self.fetch_interval_market_hours = 60  # 1 minute during market hours
        self.fetch_interval_after_hours = 900  # 15 minutes after hours
        self.fetch_interval_weekend = 3600     # 1 hour on weekends

        # Data providers
        self.data_provider_factory = DataProviderFactory()

        # Performance tracking
        self.last_fetch_time: Optional[datetime] = None
        self.last_fetch_duration: Optional[float] = None
        self.total_fetches = 0
        self.fetch_errors = 0

    async def start(self):
        """Start the background data aggregation service"""
        if self._running:
            logger.warning("Data aggregator already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_aggregation_loop())
        logger.info("🚀 Data Aggregator Service started")

    async def stop(self):
        """Stop the background data aggregation service"""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 Data Aggregator Service stopped")

    async def _run_aggregation_loop(self):
        """Main loop for data aggregation"""
        try:
            # Initial sync with database
            await self._sync_subscriptions_from_db()

            while self._running:
                try:
                    # Determine fetch interval based on market hours
                    interval = self._get_fetch_interval()

                    # Fetch and cache data for all active symbols
                    await self._fetch_and_cache_data()

                    # Wait before next fetch
                    await asyncio.sleep(interval)

                    # Periodically sync subscriptions from database (every 5 minutes)
                    if self.total_fetches % 5 == 0:
                        await self._sync_subscriptions_from_db()

                except Exception as e:
                    logger.error(f"Error in data aggregation loop: {e}", exc_info=True)
                    self.fetch_errors += 1
                    # Wait a bit before retrying on error
                    await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("Data aggregation loop cancelled")
            raise

    def _get_fetch_interval(self) -> int:
        """
        Determine appropriate fetch interval based on market hours

        Returns:
            Interval in seconds
        """
        now = datetime.now()

        # Weekend
        if now.weekday() >= 5:
            return self.fetch_interval_weekend

        # Check if US market is open
        if is_market_open('US'):
            return self.fetch_interval_market_hours
        else:
            return self.fetch_interval_after_hours

    async def _sync_subscriptions_from_db(self):
        """Sync symbol subscriptions from database"""
        try:
            async with self.db_session_factory() as db:
                await self.subscription_manager.update_from_database(db)

        except Exception as e:
            logger.error(f"Error syncing subscriptions from database: {e}")

    async def _fetch_and_cache_data(self):
        """Fetch and cache data for all active symbols"""
        start_time = datetime.utcnow()

        try:
            # Get active symbols
            symbols = self.subscription_manager.get_active_symbols()

            if not symbols:
                logger.debug("No active symbol subscriptions, skipping data fetch")
                return

            logger.info(f"Fetching data for {len(symbols)} symbols...")

            # Fetch data from Alpaca or Yahoo Finance
            bars_data = await self._fetch_historical_bars(symbols)

            if not bars_data:
                logger.warning("No data fetched from providers")
                return

            # Process each symbol
            cached_symbols = 0
            for symbol, bars in bars_data.items():
                try:
                    # Convert to DataFrame for indicator calculation
                    df = pd.DataFrame(bars)

                    if df.empty:
                        logger.warning(f"Empty data for {symbol}")
                        continue

                    # Calculate indicators
                    indicators = self._calculate_indicators(df, symbol)

                    # Store bars in cache
                    await self.cache_service.set_bars(symbol, '1day', bars)

                    # Store indicators in cache
                    await self.cache_service.set_indicators(symbol, indicators)

                    # Store metadata (current price, volume, etc.)
                    metadata = self._extract_metadata(df, symbol)
                    await self.cache_service.set_symbol_metadata(symbol, metadata)

                    # Persist bars to database for historical record
                    await self._store_bars_to_database(symbol, '1day', bars)

                    # Persist indicators to database
                    await self._store_indicators_to_database(symbol, indicators, df)

                    cached_symbols += 1

                except Exception as e:
                    logger.error(f"Error processing data for {symbol}: {e}")
                    continue

            # Update performance metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.last_fetch_time = start_time
            self.last_fetch_duration = duration
            self.total_fetches += 1

            logger.info(
                f"✅ Cached data for {cached_symbols}/{len(symbols)} symbols "
                f"in {duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error fetching and caching data: {e}", exc_info=True)
            self.fetch_errors += 1

    async def _fetch_historical_bars(
        self,
        symbols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch historical bars from data providers

        Args:
            symbols: List of symbols to fetch

        Returns:
            Dict mapping symbol to list of OHLCV bar dicts
        """
        try:
            # Try Alpaca first (free for all users)
            broker = await self._get_alpaca_broker()

            if broker:
                # Use Alpaca's batch API
                bars_data = await self._fetch_from_alpaca(broker, symbols)
                if bars_data:
                    return bars_data

            # Fallback to Yahoo Finance
            logger.info("Falling back to Yahoo Finance for historical data")
            return await self._fetch_from_yahoo(symbols)

        except Exception as e:
            logger.error(f"Error fetching historical bars: {e}")
            return {}

    async def _get_alpaca_broker(self) -> Optional[AlpacaBroker]:
        """Get Alpaca broker instance"""
        try:
            import os

            api_key = os.getenv('ALPACA_API_KEY')
            api_secret = os.getenv('ALPACA_SECRET_KEY')

            if not api_key or not api_secret:
                return None

            broker = AlpacaBroker(
                api_key=api_key,
                secret_key=api_secret,
                paper_trading=True
            )

            await broker.authenticate()
            return broker

        except Exception as e:
            logger.error(f"Error creating Alpaca broker: {e}")
            return None

    async def _fetch_from_alpaca(
        self,
        broker: AlpacaBroker,
        symbols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch bars from Alpaca using batch API

        Args:
            broker: Alpaca broker instance
            symbols: List of symbols

        Returns:
            Dict mapping symbol to bars
        """
        try:
            # Get last 100 days of daily bars
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=100)

            # Alpaca's get_bars_multi supports batch fetching
            bars_response = await broker.get_bars_multi(
                symbols=symbols,
                timeframe='1Day',
                start=start_date.isoformat(),
                end=end_date.isoformat()
            )

            # Convert to our format
            result = {}
            for symbol, bars in bars_response.items():
                result[symbol] = [
                    {
                        'date': bar['timestamp'].isoformat() if hasattr(bar['timestamp'], 'isoformat') else bar['timestamp'],
                        'open': float(bar['open']),
                        'high': float(bar['high']),
                        'low': float(bar['low']),
                        'close': float(bar['close']),
                        'volume': int(bar['volume'])
                    }
                    for bar in bars
                ]

            logger.info(f"Fetched data for {len(result)} symbols from Alpaca")
            return result

        except Exception as e:
            logger.error(f"Error fetching from Alpaca: {e}")
            return {}

    async def _fetch_from_yahoo(
        self,
        symbols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch bars from Yahoo Finance

        Args:
            symbols: List of symbols

        Returns:
            Dict mapping symbol to bars
        """
        try:
            # Get Yahoo Finance provider
            provider = self.data_provider_factory.get_provider('yahoo')

            # Fetch last 100 days
            end_date = date.today()
            start_date = end_date - timedelta(days=100)

            historical_data = await provider.get_historical_data(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                region='US'
            )

            # Convert DataFrame to list of dicts
            result = {}
            for symbol, df in historical_data.items():
                result[symbol] = df.to_dict('records')

            logger.info(f"Fetched data for {len(result)} symbols from Yahoo Finance")
            return result

        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance: {e}")
            return {}

    async def _store_bars_to_database(
        self,
        symbol: str,
        timeframe: str,
        bars: List[Dict[str, Any]]
    ):
        """
        Store fetched bars to PostgreSQL for historical record
        Uses batch upsert - only stores new data (idempotent)

        Args:
            symbol: Stock symbol
            timeframe: Timeframe ('1min', '5min', '1day', etc.)
            bars: List of OHLCV bar dicts
        """
        if not bars:
            return

        try:
            async with self.db_session_factory() as db:
                # Prepare batch insert values
                values = []
                for bar in bars:
                    # Parse timestamp
                    timestamp = bar.get('date') or bar.get('timestamp')
                    if isinstance(timestamp, str):
                        # Convert ISO string to datetime
                        try:
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            # Fallback to current time if parsing fails
                            timestamp = datetime.utcnow()

                    values.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': timestamp,
                        'open': float(bar.get('open', 0)),
                        'high': float(bar.get('high', 0)),
                        'low': float(bar.get('low', 0)),
                        'close': float(bar.get('close', 0)),
                        'volume': int(bar.get('volume', 0)),
                        'vwap': float(bar['vwap']) if 'vwap' in bar else None,
                        'trade_count': int(bar['trade_count']) if 'trade_count' in bar else None
                    })

                # Batch upsert (ON CONFLICT DO NOTHING for existing data)
                if values:
                    await db.execute(text("""
                        INSERT INTO market_data_bars
                        (symbol, timeframe, timestamp, open, high, low, close, volume, vwap, trade_count)
                        VALUES (:symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :vwap, :trade_count)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
                    """), values)

                    await db.commit()
                    logger.debug(f"Stored {len(values)} bars for {symbol} ({timeframe}) to database")

        except Exception as e:
            logger.error(f"Failed to store bars to database for {symbol}: {e}")

    async def _store_indicators_to_database(
        self,
        symbol: str,
        indicators: Dict[str, float],
        df: pd.DataFrame
    ):
        """
        Store calculated indicators to PostgreSQL

        Args:
            symbol: Stock symbol
            indicators: Dict of indicator name -> value
            df: DataFrame with bar data (to get timestamp)
        """
        if not indicators or df.empty:
            return

        try:
            async with self.db_session_factory() as db:
                # Get latest timestamp from dataframe
                latest_timestamp = df.iloc[-1].get('date')
                if isinstance(latest_timestamp, str):
                    try:
                        latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                    except:
                        latest_timestamp = datetime.utcnow()
                elif not isinstance(latest_timestamp, datetime):
                    latest_timestamp = datetime.utcnow()

                # Prepare batch insert
                values = []
                for indicator_name, indicator_value in indicators.items():
                    if indicator_value is not None and not pd.isna(indicator_value):
                        values.append({
                            'symbol': symbol,
                            'timestamp': latest_timestamp,
                            'indicator_name': indicator_name,
                            'indicator_value': float(indicator_value)
                        })

                # Batch upsert
                if values:
                    await db.execute(text("""
                        INSERT INTO market_data_indicators
                        (symbol, timestamp, indicator_name, indicator_value)
                        VALUES (:symbol, :timestamp, :indicator_name, :indicator_value)
                        ON CONFLICT (symbol, timestamp, indicator_name)
                        DO UPDATE SET indicator_value = EXCLUDED.indicator_value
                    """), values)

                    await db.commit()
                    logger.debug(f"Stored {len(values)} indicators for {symbol} to database")

        except Exception as e:
            logger.error(f"Failed to store indicators to database for {symbol}: {e}")

    def _calculate_indicators(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> Dict[str, float]:
        """
        Calculate technical indicators from OHLCV data

        Args:
            df: DataFrame with OHLCV columns
            symbol: Stock symbol (for logging)

        Returns:
            Dict with indicator values
        """
        indicators = {}

        try:
            # Ensure we have close prices
            if 'close' not in df.columns:
                logger.warning(f"No close prices for {symbol}")
                return indicators

            close = df['close'].astype(float)
            high = df['high'].astype(float) if 'high' in df.columns else close
            low = df['low'].astype(float) if 'low' in df.columns else close

            # RSI (14-period)
            indicators['rsi_14'] = self._calculate_rsi(close, 14)

            # Simple Moving Averages
            indicators['sma_10'] = self._calculate_sma(close, 10)
            indicators['sma_20'] = self._calculate_sma(close, 20)
            indicators['sma_50'] = self._calculate_sma(close, 50)
            indicators['sma_200'] = self._calculate_sma(close, 200)

            # Exponential Moving Averages
            indicators['ema_10'] = self._calculate_ema(close, 10)
            indicators['ema_20'] = self._calculate_ema(close, 20)
            indicators['ema_50'] = self._calculate_ema(close, 50)

            # MACD (12, 26, 9)
            macd_values = self._calculate_macd(close)
            indicators['macd'] = macd_values['macd']
            indicators['macd_signal'] = macd_values['signal']
            indicators['macd_histogram'] = macd_values['histogram']

            # Bollinger Bands (20-period, 2 std dev)
            bb_values = self._calculate_bollinger_bands(close, 20, 2)
            indicators['bb_upper_20'] = bb_values['upper']
            indicators['bb_middle_20'] = bb_values['middle']
            indicators['bb_lower_20'] = bb_values['lower']

            # Volume indicators (if volume available)
            if 'volume' in df.columns:
                volume = df['volume'].astype(float)
                indicators['volume_sma_20'] = self._calculate_sma(volume, 20)

        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")

        return indicators

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        except Exception:
            return 50.0

    def _calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        try:
            sma = prices.rolling(window=period).mean()
            return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1])

        except Exception:
            return float(prices.iloc[-1]) if len(prices) > 0 else 0.0

    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        try:
            ema = prices.ewm(span=period, adjust=False).mean()
            return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else float(prices.iloc[-1])

        except Exception:
            return float(prices.iloc[-1]) if len(prices) > 0 else 0.0

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, float]:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()

            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            histogram = macd - signal_line

            return {
                'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0,
                'signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
                'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0,
            }

        except Exception:
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()

            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)

            return {
                'upper': float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else float(prices.iloc[-1]) * 1.02,
                'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1]),
                'lower': float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else float(prices.iloc[-1]) * 0.98,
            }

        except Exception:
            current_price = float(prices.iloc[-1]) if len(prices) > 0 else 100.0
            return {
                'upper': current_price * 1.02,
                'middle': current_price,
                'lower': current_price * 0.98,
            }

    def _extract_metadata(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Extract symbol metadata from DataFrame"""
        try:
            latest = df.iloc[-1]

            return {
                'symbol': symbol,
                'price': float(latest['close']),
                'volume': int(latest['volume']) if 'volume' in df.columns else 0,
                'open': float(latest['open']) if 'open' in df.columns else float(latest['close']),
                'high': float(latest['high']) if 'high' in df.columns else float(latest['close']),
                'low': float(latest['low']) if 'low' in df.columns else float(latest['close']),
                'timestamp': latest['date'] if 'date' in df.columns else datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error extracting metadata for {symbol}: {e}")
            return {
                'symbol': symbol,
                'price': 0.0,
                'volume': 0,
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'running': self._running,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_fetch_duration_seconds': self.last_fetch_duration,
            'total_fetches': self.total_fetches,
            'fetch_errors': self.fetch_errors,
            'error_rate': (self.fetch_errors / self.total_fetches * 100) if self.total_fetches > 0 else 0.0,
            'active_symbols': len(self.subscription_manager.get_active_symbols()),
            'subscription_stats': self.subscription_manager.get_subscription_stats()
        }


# Singleton instance
_aggregator_service: Optional[DataAggregatorService] = None


async def get_aggregator_service(
    cache_service: RedisCacheService = None,
    subscription_manager: SymbolSubscriptionManager = None,
    db_session_factory = None
) -> DataAggregatorService:
    """
    Get or create DataAggregatorService singleton

    Args:
        cache_service: Redis cache service (required on first call)
        subscription_manager: Subscription manager (required on first call)
        db_session_factory: Database session factory (required on first call)

    Returns:
        DataAggregatorService instance
    """
    global _aggregator_service

    if _aggregator_service is None:
        if not all([cache_service, subscription_manager, db_session_factory]):
            raise ValueError("All parameters required for first initialization")

        _aggregator_service = DataAggregatorService(
            cache_service=cache_service,
            subscription_manager=subscription_manager,
            db_session_factory=db_session_factory
        )

    return _aggregator_service
