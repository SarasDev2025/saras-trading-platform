"""
Redis Cache Service for Market Data and Indicators
Provides high-performance caching for price bars and technical indicators
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Service for caching market data and indicators in Redis

    Cache Structure:
    - market_data:{symbol}:{timeframe}:bars -> JSON array of OHLCV bars
    - indicators:{symbol}:{indicator}:{period} -> float value
    - symbol:{symbol}:metadata -> JSON with current price, volume, timestamp
    - batch:indicators:{hash} -> JSON dict of multiple indicators
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize Redis Cache Service

        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client

        # TTL configurations (in seconds)
        self.ttl_config = {
            '1min': 60,      # 1 minute
            '5min': 300,     # 5 minutes
            '15min': 900,    # 15 minutes
            '1hour': 3600,   # 1 hour
            '1day': 86400,   # 24 hours
            'indicators': 60,  # 1 minute for indicators
            'metadata': 30,    # 30 seconds for metadata
        }

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = '1min',
        limit: int = 500
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get OHLCV bars from cache

        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe (1min, 5min, 15min, 1hour, 1day)
            limit: Maximum number of bars to return

        Returns:
            List of bar dicts with OHLCV data, or None if not cached
        """
        try:
            cache_key = f"market_data:{symbol.upper()}:{timeframe}:bars"
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                bars = json.loads(cached_data)
                # Return most recent bars up to limit
                return bars[-limit:] if len(bars) > limit else bars

            return None

        except Exception as e:
            logger.error(f"Error retrieving bars from cache for {symbol}: {e}")
            return None

    async def set_bars(
        self,
        symbol: str,
        timeframe: str,
        bars: List[Dict[str, Any]]
    ) -> bool:
        """
        Store OHLCV bars in cache

        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            bars: List of bar dicts with OHLCV data

        Returns:
            True if successful
        """
        try:
            cache_key = f"market_data:{symbol.upper()}:{timeframe}:bars"

            # Store only last 500 bars to save memory
            bars_to_store = bars[-500:] if len(bars) > 500 else bars

            # Serialize to JSON
            data = json.dumps(bars_to_store, default=str)

            # Set with TTL
            ttl = self.ttl_config.get(timeframe, 300)
            await self.redis.setex(cache_key, ttl, data)

            logger.debug(f"Cached {len(bars_to_store)} bars for {symbol} ({timeframe})")
            return True

        except Exception as e:
            logger.error(f"Error storing bars in cache for {symbol}: {e}")
            return False

    async def get_indicator(
        self,
        symbol: str,
        indicator: str,
        period: int = 14
    ) -> Optional[float]:
        """
        Get single indicator value from cache

        Args:
            symbol: Stock symbol
            indicator: Indicator name (rsi, sma, ema, macd, etc.)
            period: Indicator period

        Returns:
            Indicator value or None if not cached
        """
        try:
            cache_key = f"indicators:{symbol.upper()}:{indicator.lower()}:{period}"
            cached_value = await self.redis.get(cache_key)

            if cached_value:
                return float(cached_value)

            return None

        except Exception as e:
            logger.error(f"Error retrieving indicator from cache: {e}")
            return None

    async def get_indicators(
        self,
        symbol: str,
        indicator_list: List[tuple]
    ) -> Dict[str, float]:
        """
        Get multiple indicators for a symbol in batch

        Args:
            symbol: Stock symbol
            indicator_list: List of (indicator_name, period) tuples
                Example: [('rsi', 14), ('sma', 20), ('ema', 20)]

        Returns:
            Dict mapping indicator key to value
            Example: {'rsi_14': 52.3, 'sma_20': 150.5}
        """
        try:
            results = {}

            # Build cache keys
            keys_to_fetch = []
            key_mapping = {}

            for indicator, period in indicator_list:
                cache_key = f"indicators:{symbol.upper()}:{indicator.lower()}:{period}"
                result_key = f"{indicator.lower()}_{period}"
                keys_to_fetch.append(cache_key)
                key_mapping[cache_key] = result_key

            # Batch get using pipeline
            if keys_to_fetch:
                pipeline = self.redis.pipeline()
                for key in keys_to_fetch:
                    pipeline.get(key)

                values = await pipeline.execute()

                # Map results
                for cache_key, value in zip(keys_to_fetch, values):
                    result_key = key_mapping[cache_key]
                    if value:
                        results[result_key] = float(value)

            return results

        except Exception as e:
            logger.error(f"Error retrieving indicators from cache: {e}")
            return {}

    async def set_indicator(
        self,
        symbol: str,
        indicator: str,
        period: int,
        value: float
    ) -> bool:
        """
        Store single indicator value in cache

        Args:
            symbol: Stock symbol
            indicator: Indicator name
            period: Indicator period
            value: Indicator value

        Returns:
            True if successful
        """
        try:
            cache_key = f"indicators:{symbol.upper()}:{indicator.lower()}:{period}"
            ttl = self.ttl_config['indicators']

            await self.redis.setex(cache_key, ttl, str(value))

            logger.debug(f"Cached indicator {indicator}_{period} for {symbol}: {value}")
            return True

        except Exception as e:
            logger.error(f"Error storing indicator in cache: {e}")
            return False

    async def set_indicators(
        self,
        symbol: str,
        indicators: Dict[str, float]
    ) -> bool:
        """
        Store multiple indicators for a symbol in batch

        Args:
            symbol: Stock symbol
            indicators: Dict with indicator values
                Example: {'rsi_14': 52.3, 'sma_20': 150.5, 'ema_20': 151.2}

        Returns:
            True if successful
        """
        try:
            ttl = self.ttl_config['indicators']

            # Use pipeline for atomic batch operation
            pipeline = self.redis.pipeline()

            for indicator_key, value in indicators.items():
                # Parse indicator_key like "rsi_14" -> indicator="rsi", period=14
                parts = indicator_key.rsplit('_', 1)
                if len(parts) == 2:
                    indicator = parts[0]
                    period = parts[1]
                    cache_key = f"indicators:{symbol.upper()}:{indicator.lower()}:{period}"
                    pipeline.setex(cache_key, ttl, str(value))

            await pipeline.execute()

            logger.debug(f"Cached {len(indicators)} indicators for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error storing indicators in cache: {e}")
            return False

    async def get_symbol_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol metadata (current price, volume, timestamp)

        Args:
            symbol: Stock symbol

        Returns:
            Dict with metadata or None
        """
        try:
            cache_key = f"symbol:{symbol.upper()}:metadata"
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

            return None

        except Exception as e:
            logger.error(f"Error retrieving metadata from cache: {e}")
            return None

    async def set_symbol_metadata(
        self,
        symbol: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store symbol metadata

        Args:
            symbol: Stock symbol
            metadata: Dict with price, volume, timestamp, etc.

        Returns:
            True if successful
        """
        try:
            cache_key = f"symbol:{symbol.upper()}:metadata"
            ttl = self.ttl_config['metadata']

            data = json.dumps(metadata, default=str)
            await self.redis.setex(cache_key, ttl, data)

            logger.debug(f"Cached metadata for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error storing metadata in cache: {e}")
            return False

    async def invalidate_symbol(self, symbol: str) -> bool:
        """
        Invalidate all cached data for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            True if successful
        """
        try:
            pattern = f"*:{symbol.upper()}:*"

            # Find all keys matching pattern
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            # Delete in batch
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for {symbol}")

            return True

        except Exception as e:
            logger.error(f"Error invalidating cache for {symbol}: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache stats
        """
        try:
            info = await self.redis.info('stats')

            # Count different types of keys
            bar_keys = 0
            indicator_keys = 0
            metadata_keys = 0

            async for key in self.redis.scan_iter():
                key_str = key if isinstance(key, str) else key.decode('utf-8')
                if ':bars' in key_str:
                    bar_keys += 1
                elif 'indicators:' in key_str:
                    indicator_keys += 1
                elif ':metadata' in key_str:
                    metadata_keys += 1

            return {
                'total_keys': info.get('db0', {}).get('keys', 0),
                'bar_cache_entries': bar_keys,
                'indicator_cache_entries': indicator_keys,
                'metadata_cache_entries': metadata_keys,
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    async def health_check(self) -> bool:
        """
        Check if Redis is healthy

        Returns:
            True if Redis is accessible
        """
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Singleton instance
_cache_service: Optional[RedisCacheService] = None


def get_cache_service(redis_client: redis.Redis = None) -> RedisCacheService:
    """
    Get or create RedisCacheService singleton

    Args:
        redis_client: Redis client (required on first call)

    Returns:
        RedisCacheService instance
    """
    global _cache_service

    if _cache_service is None:
        if redis_client is None:
            raise ValueError("redis_client required for first initialization")
        _cache_service = RedisCacheService(redis_client)

    return _cache_service
