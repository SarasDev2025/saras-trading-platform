"""
Symbol Subscription Manager
Tracks which symbols are actively needed for algorithm execution
Manages dynamic subscription to market data feeds
"""
import logging
from typing import Set, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SymbolSubscriptionManager:
    """
    Manages symbol subscriptions for market data aggregation

    Tracks which symbols are needed by active algorithms and
    determines which symbols need real-time data updates.
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize Symbol Subscription Manager

        Args:
            redis_client: Async Redis client for persistent storage
        """
        self.redis = redis_client

        # In-memory tracking
        self._active_symbols: Set[str] = set()
        self._algorithm_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._symbol_subscribers: Dict[str, Set[str]] = defaultdict(set)

        # Redis keys
        self.ACTIVE_SYMBOLS_KEY = "subscriptions:active_symbols"
        self.ALGORITHM_PREFIX = "subscriptions:algorithm:"
        self.SYMBOL_PREFIX = "subscriptions:symbol:"

    async def initialize(self):
        """
        Initialize from Redis (restore state after restart)
        """
        try:
            # Load active symbols from Redis
            active_symbols = await self.redis.smembers(self.ACTIVE_SYMBOLS_KEY)
            if active_symbols:
                self._active_symbols = {s if isinstance(s, str) else s.decode('utf-8') for s in active_symbols}
                logger.info(f"Restored {len(self._active_symbols)} active symbol subscriptions from Redis")

            # Load algorithm subscriptions
            async for key in self.redis.scan_iter(match=f"{self.ALGORITHM_PREFIX}*"):
                key_str = key if isinstance(key, str) else key.decode('utf-8')
                algorithm_id = key_str.replace(self.ALGORITHM_PREFIX, '')

                symbols = await self.redis.smembers(key_str)
                if symbols:
                    symbol_set = {s if isinstance(s, str) else s.decode('utf-8') for s in symbols}
                    self._algorithm_subscriptions[algorithm_id] = symbol_set

                    # Update reverse mapping
                    for symbol in symbol_set:
                        self._symbol_subscribers[symbol].add(algorithm_id)

            logger.info(f"Restored {len(self._algorithm_subscriptions)} algorithm subscriptions")

        except Exception as e:
            logger.error(f"Error initializing symbol subscriptions from Redis: {e}")

    async def subscribe_algorithm(
        self,
        algorithm_id: str,
        symbols: List[str]
    ) -> bool:
        """
        Subscribe an algorithm to symbols

        Args:
            algorithm_id: Unique algorithm identifier
            symbols: List of symbols the algorithm needs

        Returns:
            True if successful
        """
        try:
            symbols_upper = [s.upper() for s in symbols]

            # Update in-memory state
            old_symbols = self._algorithm_subscriptions.get(algorithm_id, set())
            new_symbols = set(symbols_upper)

            # Add new subscriptions
            self._algorithm_subscriptions[algorithm_id] = new_symbols
            self._active_symbols.update(new_symbols)

            # Update reverse mapping
            for symbol in new_symbols:
                self._symbol_subscribers[symbol].add(algorithm_id)

            # Remove old subscriptions that are no longer needed
            removed_symbols = old_symbols - new_symbols
            for symbol in removed_symbols:
                self._symbol_subscribers[symbol].discard(algorithm_id)
                # If no algorithms need this symbol, remove it
                if not self._symbol_subscribers[symbol]:
                    self._active_symbols.discard(symbol)
                    del self._symbol_subscribers[symbol]

            # Persist to Redis
            pipeline = self.redis.pipeline()

            # Store algorithm subscriptions
            algo_key = f"{self.ALGORITHM_PREFIX}{algorithm_id}"
            await self.redis.delete(algo_key)  # Clear old
            if new_symbols:
                pipeline.sadd(algo_key, *new_symbols)

            # Update active symbols set
            if new_symbols:
                pipeline.sadd(self.ACTIVE_SYMBOLS_KEY, *new_symbols)

            # Remove inactive symbols
            if removed_symbols:
                for symbol in removed_symbols:
                    if not self._symbol_subscribers.get(symbol):
                        pipeline.srem(self.ACTIVE_SYMBOLS_KEY, symbol)

            await pipeline.execute()

            logger.info(
                f"Algorithm {algorithm_id} subscribed to {len(new_symbols)} symbols. "
                f"Total active symbols: {len(self._active_symbols)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error subscribing algorithm {algorithm_id}: {e}")
            return False

    async def unsubscribe_algorithm(self, algorithm_id: str) -> bool:
        """
        Unsubscribe an algorithm from all symbols

        Args:
            algorithm_id: Unique algorithm identifier

        Returns:
            True if successful
        """
        try:
            # Get symbols this algorithm was subscribed to
            subscribed_symbols = self._algorithm_subscriptions.get(algorithm_id, set())

            if not subscribed_symbols:
                logger.debug(f"Algorithm {algorithm_id} has no active subscriptions")
                return True

            # Remove from reverse mapping
            for symbol in subscribed_symbols:
                self._symbol_subscribers[symbol].discard(algorithm_id)

                # If no algorithms need this symbol anymore, remove it from active
                if not self._symbol_subscribers[symbol]:
                    self._active_symbols.discard(symbol)
                    del self._symbol_subscribers[symbol]

            # Remove algorithm subscriptions
            del self._algorithm_subscriptions[algorithm_id]

            # Persist to Redis
            pipeline = self.redis.pipeline()

            # Delete algorithm subscription key
            algo_key = f"{self.ALGORITHM_PREFIX}{algorithm_id}"
            pipeline.delete(algo_key)

            # Remove symbols that are no longer active
            inactive_symbols = [s for s in subscribed_symbols if s not in self._active_symbols]
            if inactive_symbols:
                pipeline.srem(self.ACTIVE_SYMBOLS_KEY, *inactive_symbols)

            await pipeline.execute()

            logger.info(
                f"Algorithm {algorithm_id} unsubscribed from {len(subscribed_symbols)} symbols. "
                f"Remaining active symbols: {len(self._active_symbols)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error unsubscribing algorithm {algorithm_id}: {e}")
            return False

    def get_active_symbols(self) -> List[str]:
        """
        Get list of all symbols that need data updates

        Returns:
            List of symbol strings
        """
        return sorted(list(self._active_symbols))

    def get_algorithm_symbols(self, algorithm_id: str) -> List[str]:
        """
        Get symbols subscribed by a specific algorithm

        Args:
            algorithm_id: Unique algorithm identifier

        Returns:
            List of symbols
        """
        return sorted(list(self._algorithm_subscriptions.get(algorithm_id, set())))

    def get_symbol_subscribers(self, symbol: str) -> List[str]:
        """
        Get algorithms subscribed to a symbol

        Args:
            symbol: Stock symbol

        Returns:
            List of algorithm IDs
        """
        return sorted(list(self._symbol_subscribers.get(symbol.upper(), set())))

    def get_subscription_stats(self) -> Dict[str, any]:
        """
        Get subscription statistics

        Returns:
            Dict with subscription stats
        """
        return {
            'total_active_symbols': len(self._active_symbols),
            'total_algorithms': len(self._algorithm_subscriptions),
            'average_symbols_per_algorithm': (
                sum(len(symbols) for symbols in self._algorithm_subscriptions.values()) /
                len(self._algorithm_subscriptions)
            ) if self._algorithm_subscriptions else 0,
            'average_subscribers_per_symbol': (
                sum(len(algos) for algos in self._symbol_subscribers.values()) /
                len(self._symbol_subscribers)
            ) if self._symbol_subscribers else 0,
            'most_subscribed_symbols': self._get_top_subscribed_symbols(5),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _get_top_subscribed_symbols(self, limit: int = 5) -> List[tuple]:
        """
        Get top N symbols by subscriber count

        Args:
            limit: Number of top symbols to return

        Returns:
            List of (symbol, subscriber_count) tuples
        """
        symbol_counts = [
            (symbol, len(subscribers))
            for symbol, subscribers in self._symbol_subscribers.items()
        ]

        # Sort by subscriber count descending
        symbol_counts.sort(key=lambda x: x[1], reverse=True)

        return symbol_counts[:limit]

    async def update_from_database(self, db_session) -> bool:
        """
        Update subscriptions from database (fetch active algorithms)

        This is called periodically to sync with database state

        Args:
            db_session: Database session

        Returns:
            True if successful
        """
        try:
            from sqlalchemy import text

            # Query active algorithms and their stock universes
            query = text("""
                SELECT id, stock_universe
                FROM trading_algorithms
                WHERE status = 'active'
            """)

            result = await db_session.execute(query)
            algorithms = result.fetchall()

            # Track which algorithms we've seen
            active_algorithm_ids = set()

            for algo in algorithms:
                algorithm_id = str(algo.id)
                active_algorithm_ids.add(algorithm_id)

                # Parse stock universe
                stock_universe = algo.stock_universe or {}

                # Determine symbols
                symbols = []
                if stock_universe.get('type') == 'specific':
                    symbols = stock_universe.get('symbols', [])
                elif stock_universe.get('type') == 'all':
                    # For 'all', we could subscribe to a default set
                    # For now, skip these to avoid over-subscription
                    continue

                # Subscribe algorithm to symbols
                if symbols:
                    await self.subscribe_algorithm(algorithm_id, symbols)

            # Unsubscribe algorithms that are no longer active
            all_subscribed_algorithms = set(self._algorithm_subscriptions.keys())
            inactive_algorithms = all_subscribed_algorithms - active_algorithm_ids

            for algorithm_id in inactive_algorithms:
                await self.unsubscribe_algorithm(algorithm_id)

            logger.info(
                f"Updated subscriptions from database: "
                f"{len(active_algorithm_ids)} active algorithms, "
                f"{len(inactive_algorithms)} inactive removed"
            )

            return True

        except Exception as e:
            logger.error(f"Error updating subscriptions from database: {e}")
            return False

    async def cleanup_stale_subscriptions(self, max_age_hours: int = 24) -> int:
        """
        Clean up stale subscription data from Redis

        Args:
            max_age_hours: Maximum age for subscription data

        Returns:
            Number of cleaned up entries
        """
        try:
            # This is a placeholder for future implementation
            # Could track last access time and remove old entries
            return 0

        except Exception as e:
            logger.error(f"Error cleaning up stale subscriptions: {e}")
            return 0


# Singleton instance
_subscription_manager: Optional[SymbolSubscriptionManager] = None


def get_subscription_manager(redis_client: redis.Redis = None) -> SymbolSubscriptionManager:
    """
    Get or create SymbolSubscriptionManager singleton

    Args:
        redis_client: Redis client (required on first call)

    Returns:
        SymbolSubscriptionManager instance
    """
    global _subscription_manager

    if _subscription_manager is None:
        if redis_client is None:
            raise ValueError("redis_client required for first initialization")
        _subscription_manager = SymbolSubscriptionManager(redis_client)

    return _subscription_manager
