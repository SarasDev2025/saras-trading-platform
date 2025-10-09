"""
Market Hours Detection Service
Determines if markets are open for different regions
"""
from datetime import datetime, time
from typing import Dict, Tuple
import pytz
import logging

logger = logging.getLogger(__name__)


class MarketHoursService:
    """Service to check market operating hours by region"""

    MARKET_CONFIG = {
        'US': {
            'timezone': 'America/New_York',
            'open': time(9, 30),
            'close': time(16, 0),
            'name': 'US Markets (NYSE/NASDAQ)'
        },
        'IN': {
            'timezone': 'Asia/Kolkata',
            'open': time(9, 15),
            'close': time(15, 30),
            'name': 'Indian Market (NSE/BSE)'
        },
        'GB': {
            'timezone': 'Europe/London',
            'open': time(8, 0),
            'close': time(16, 30),
            'name': 'London Stock Exchange'
        }
    }

    @staticmethod
    def is_market_open(region: str) -> bool:
        """
        Check if market is currently open for given region.

        Args:
            region: Region code ('US', 'IN', 'GB')

        Returns:
            True if market is open, False otherwise
        """
        try:
            if region not in MarketHoursService.MARKET_CONFIG:
                logger.warning(f"Unknown region: {region}, defaulting to closed")
                return False

            config = MarketHoursService.MARKET_CONFIG[region]
            tz = pytz.timezone(config['timezone'])
            now = datetime.now(tz)

            # Check if weekend
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False

            # Check if within market hours
            current_time = now.time()
            is_open = config['open'] <= current_time <= config['close']

            return is_open

        except Exception as e:
            logger.error(f"Error checking market hours for {region}: {e}")
            return False

    @staticmethod
    def get_market_status(region: str) -> Dict[str, any]:
        """
        Get detailed market status information.

        Returns:
            Dict with market status details
        """
        try:
            if region not in MarketHoursService.MARKET_CONFIG:
                return {
                    'region': region,
                    'is_open': False,
                    'error': 'Unknown region'
                }

            config = MarketHoursService.MARKET_CONFIG[region]
            tz = pytz.timezone(config['timezone'])
            now = datetime.now(tz)

            is_weekend = now.weekday() >= 5
            current_time = now.time()
            is_open = not is_weekend and (config['open'] <= current_time <= config['close'])

            # Calculate next open/close
            if is_open:
                next_change = 'close'
                next_time = datetime.combine(now.date(), config['close'])
            elif is_weekend:
                # Find next Monday
                days_until_monday = (7 - now.weekday()) % 7 or 7
                next_date = now.date() + pytz.timedelta(days=days_until_monday)
                next_change = 'open'
                next_time = datetime.combine(next_date, config['open'])
            elif current_time < config['open']:
                next_change = 'open'
                next_time = datetime.combine(now.date(), config['open'])
            else:  # After close
                next_change = 'open'
                next_date = now.date() + pytz.timedelta(days=1)
                next_time = datetime.combine(next_date, config['open'])

            # Localize next_time
            next_time = tz.localize(next_time) if next_time.tzinfo is None else next_time

            return {
                'region': region,
                'market_name': config['name'],
                'is_open': is_open,
                'current_time': now.isoformat(),
                'market_open_time': config['open'].strftime('%H:%M'),
                'market_close_time': config['close'].strftime('%H:%M'),
                'timezone': config['timezone'],
                'is_weekend': is_weekend,
                'next_change': next_change,
                'next_change_time': next_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market status for {region}: {e}")
            return {
                'region': region,
                'is_open': False,
                'error': str(e)
            }

    @staticmethod
    def get_cache_ttl(region: str, use_case: str = 'default') -> int:
        """
        Get cache TTL in seconds based on market status and use case.

        Args:
            region: Market region
            use_case: Type of data being cached ('order', 'portfolio', 'smallcase_detail', 'smallcase_list')

        Returns:
            Cache TTL in seconds
        """
        is_open = MarketHoursService.is_market_open(region)

        if not is_open:
            # Market closed - cache until next trading day
            return 86400  # 24 hours

        # Market open - use case specific TTL
        ttl_map = {
            'order': 0,              # Always fresh for orders
            'portfolio': 60,         # 1 minute for portfolio
            'smallcase_detail': 120, # 2 minutes for details
            'smallcase_list': 300,   # 5 minutes for list
            'default': 180           # 3 minutes default
        }

        return ttl_map.get(use_case, ttl_map['default'])

    @staticmethod
    def should_fetch_price(last_updated: datetime, region: str, use_case: str = 'default') -> bool:
        """
        Determine if price should be fetched based on last update time.

        Args:
            last_updated: When price was last updated
            region: Asset region
            use_case: Type of request

        Returns:
            True if price should be fetched
        """
        if last_updated is None:
            return True  # No price available

        # Make last_updated timezone aware if needed
        if last_updated.tzinfo is None:
            last_updated = pytz.UTC.localize(last_updated)

        is_open = MarketHoursService.is_market_open(region)
        now = datetime.now(pytz.UTC)
        age_seconds = (now - last_updated).total_seconds()

        if not is_open:
            # Market closed - check if we have today's closing price
            config = MarketHoursService.MARKET_CONFIG.get(region, {})
            tz = pytz.timezone(config.get('timezone', 'UTC'))
            now_local = now.astimezone(tz)
            last_updated_local = last_updated.astimezone(tz)

            # If last update was today and after market close, don't fetch
            if (last_updated_local.date() == now_local.date() and
                last_updated_local.time() >= config.get('close', time(23, 59))):
                return False

            # Otherwise fetch closing price
            return True

        # Market is open - check cache age
        ttl = MarketHoursService.get_cache_ttl(region, use_case)
        should_fetch = age_seconds > ttl

        logger.debug(f"Price age: {age_seconds}s, TTL: {ttl}s, Should fetch: {should_fetch}")
        return should_fetch


# Convenience functions
def is_market_open(region: str) -> bool:
    """Check if market is open"""
    return MarketHoursService.is_market_open(region)


def get_market_status(region: str) -> Dict:
    """Get market status details"""
    return MarketHoursService.get_market_status(region)


def should_fetch_price(last_updated: datetime, region: str, use_case: str = 'default') -> bool:
    """Check if price needs refreshing"""
    return MarketHoursService.should_fetch_price(last_updated, region, use_case)
