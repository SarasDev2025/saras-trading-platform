"""
Market Data Service
Fetches live prices from broker APIs and updates database
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from brokers import AlpacaBroker, ZerodhaBroker, broker_manager
from services.market_hours_service import should_fetch_price, is_market_open
from services.broker_connection_service import BrokerConnectionService
import os

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for fetching and caching market data from broker APIs"""

    @staticmethod
    async def get_broker_for_region(region: str, paper_trading: bool = True) -> Optional[object]:
        """
        Get appropriate broker instance for region.

        Args:
            region: 'US', 'IN', or 'GB'
            paper_trading: Whether to use paper trading mode

        Returns:
            Broker instance or None
        """
        try:
            if region == 'US':
                # Alpaca for US markets
                api_key = os.getenv('ALPACA_API_KEY')
                api_secret = os.getenv('ALPACA_SECRET_KEY')

                if not api_key or not api_secret:
                    logger.warning("Alpaca credentials not found in environment")
                    return None

                broker = AlpacaBroker(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper_trading=paper_trading
                )
                await broker.authenticate()
                return broker

            elif region == 'IN':
                # Zerodha for Indian markets (live mode only)
                if paper_trading:
                    logger.info("Zerodha doesn't support paper trading, using cached prices")
                    return None

                api_key = os.getenv('ZERODHA_API_KEY')
                api_secret = os.getenv('ZERODHA_SECRET_KEY')

                if not api_key or not api_secret:
                    logger.warning("Zerodha credentials not found in environment")
                    return None

                broker = ZerodhaBroker(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper_trading=False
                )
                await broker.authenticate()
                return broker

            else:
                logger.warning(f"Unsupported region for market data: {region}")
                return None

        except Exception as e:
            logger.error(f"Error creating broker for region {region}: {e}")
            return None

    @staticmethod
    async def fetch_price_from_broker(
        broker: object,
        symbol: str
    ) -> Optional[Dict]:
        """
        Fetch current price for a single symbol from broker.

        Returns:
            Dict with price data or None
        """
        try:
            market_data = await broker.get_market_data(symbol)

            if not market_data:
                return None

            return {
                'symbol': symbol,
                'price': market_data.get('last_price'),
                'bid': market_data.get('bid_price'),
                'ask': market_data.get('ask_price'),
                'timestamp': market_data.get('timestamp', datetime.utcnow())
            }

        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    @staticmethod
    async def fetch_prices_batch(
        broker: object,
        symbols: List[str],
        region: str
    ) -> Dict[str, Dict]:
        """
        Fetch prices for multiple symbols in batch.

        Args:
            broker: Broker instance
            symbols: List of symbols to fetch
            region: Market region

        Returns:
            Dict mapping symbol to price data
        """
        prices = {}

        try:
            if region == 'US' and hasattr(broker, 'get_bars_multi'):
                # Alpaca supports batch fetching
                logger.info(f"Fetching batch prices for {len(symbols)} US stocks")

                # Alpaca get_bars_multi returns latest bar for each symbol
                bars_data = await broker.get_bars_multi(
                    symbols=symbols,
                    timeframe='1Min',
                    start=(datetime.utcnow().date()).isoformat()
                )

                for symbol, bars in bars_data.items():
                    if bars and len(bars) > 0:
                        latest_bar = bars[-1]  # Get most recent bar
                        prices[symbol] = {
                            'symbol': symbol,
                            'price': latest_bar.get('close'),
                            'open': latest_bar.get('open'),
                            'high': latest_bar.get('high'),
                            'low': latest_bar.get('low'),
                            'volume': latest_bar.get('volume'),
                            'timestamp': latest_bar.get('timestamp', datetime.utcnow())
                        }

                # Fallback: fetch missing symbols individually
                missing_symbols = set(symbols) - set(prices.keys())
                if missing_symbols:
                    logger.info(f"Batch fetch missed {len(missing_symbols)} symbols, fetching individually: {missing_symbols}")
                    for symbol in missing_symbols:
                        try:
                            price_data = await MarketDataService.fetch_price_from_broker(broker, symbol)
                            if price_data:
                                prices[symbol] = price_data
                        except Exception as e:
                            logger.error(f"Failed to fetch price for {symbol}: {e}")

            elif region == 'IN' and hasattr(broker, 'get_quotes'):
                # Zerodha batch quotes (if available)
                logger.info(f"Fetching batch prices for {len(symbols)} Indian stocks")
                quotes_data = await broker.get_quotes(symbols)

                for symbol, quote in quotes_data.items():
                    prices[symbol] = {
                        'symbol': symbol,
                        'price': quote.get('last_price'),
                        'bid': quote.get('bid'),
                        'ask': quote.get('ask'),
                        'timestamp': datetime.utcnow()
                    }
            else:
                # Fallback: Fetch individually
                logger.info(f"Fetching individual prices for {len(symbols)} stocks")
                for symbol in symbols:
                    price_data = await MarketDataService.fetch_price_from_broker(broker, symbol)
                    if price_data:
                        prices[symbol] = price_data

        except Exception as e:
            logger.error(f"Error in batch price fetch: {e}")

        return prices

    @staticmethod
    async def update_asset_prices(
        db: AsyncSession,
        price_data: Dict[str, Dict]
    ) -> int:
        """
        Update asset prices in database.

        Args:
            db: Database session
            price_data: Dict mapping symbol to price info

        Returns:
            Number of assets updated
        """
        updated_count = 0

        try:
            for symbol, data in price_data.items():
                price = data.get('price')
                if price is None:
                    continue

                # Convert to Decimal if needed
                if not isinstance(price, Decimal):
                    price = Decimal(str(price))

                # Update asset price
                result = await db.execute(text("""
                    UPDATE assets
                    SET current_price = :price,
                        price_updated_at = :timestamp,
                        updated_at = NOW()
                    WHERE symbol = :symbol
                    RETURNING id
                """), {
                    'symbol': symbol,
                    'price': price,
                    'timestamp': data.get('timestamp', datetime.utcnow())
                })

                if result.rowcount > 0:
                    updated_count += 1

            await db.commit()
            logger.info(f"Updated prices for {updated_count} assets")

        except Exception as e:
            logger.error(f"Error updating asset prices: {e}")
            await db.rollback()

        return updated_count

    @staticmethod
    async def refresh_prices_for_symbols(
        db: AsyncSession,
        symbols: List[str],
        region: str,
        use_case: str = 'default',
        force: bool = False
    ) -> Dict[str, any]:
        """
        Refresh prices for given symbols if needed.

        Args:
            db: Database session
            symbols: List of symbols to refresh
            region: Market region
            use_case: Type of request ('order', 'portfolio', etc.)
            force: Force refresh even if cached

        Returns:
            Dict with refresh stats
        """
        if not symbols:
            return {'updated': 0, 'cached': 0, 'failed': 0}

        try:
            # Get current price info from database
            result = await db.execute(text("""
                SELECT symbol, current_price, price_updated_at
                FROM assets
                WHERE symbol = ANY(:symbols)
            """), {'symbols': symbols})

            assets_info = {row.symbol: row for row in result.fetchall()}

            # Determine which symbols need fetching
            symbols_to_fetch = []
            for symbol in symbols:
                asset_info = assets_info.get(symbol)

                if force:
                    symbols_to_fetch.append(symbol)
                elif not asset_info:
                    logger.warning(f"Symbol {symbol} not found in assets table")
                    continue
                elif should_fetch_price(asset_info.price_updated_at, region, use_case):
                    symbols_to_fetch.append(symbol)

            stats = {
                'total': len(symbols),
                'cached': len(symbols) - len(symbols_to_fetch),
                'to_fetch': len(symbols_to_fetch),
                'updated': 0,
                'failed': 0
            }

            if not symbols_to_fetch:
                logger.info(f"All {len(symbols)} prices are cached")
                return stats

            logger.info(f"Fetching fresh prices for {len(symbols_to_fetch)} symbols")

            # Determine paper trading mode (assume paper for now, can be passed as param)
            paper_trading = True

            # Get broker for region
            broker = await MarketDataService.get_broker_for_region(region, paper_trading)

            if not broker:
                logger.warning(f"No broker available for region {region}, using cached prices")
                stats['cached'] += stats['to_fetch']
                stats['to_fetch'] = 0
                return stats

            # Fetch prices in batch
            price_data = await MarketDataService.fetch_prices_batch(
                broker, symbols_to_fetch, region
            )

            # Update database
            if price_data:
                updated = await MarketDataService.update_asset_prices(db, price_data)
                stats['updated'] = updated
                stats['failed'] = len(symbols_to_fetch) - updated
            else:
                stats['failed'] = len(symbols_to_fetch)

            return stats

        except Exception as e:
            logger.error(f"Error refreshing prices: {e}")
            return {'updated': 0, 'cached': 0, 'failed': len(symbols)}

    @staticmethod
    async def get_current_prices(
        db: AsyncSession,
        symbols: List[str]
    ) -> Dict[str, Decimal]:
        """
        Get current prices for symbols from database.

        Returns:
            Dict mapping symbol to price
        """
        try:
            result = await db.execute(text("""
                SELECT symbol, current_price
                FROM assets
                WHERE symbol = ANY(:symbols)
                AND current_price IS NOT NULL
            """), {'symbols': symbols})

            return {row.symbol: row.current_price for row in result.fetchall()}

        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            return {}


# Convenience functions
async def refresh_prices(
    db: AsyncSession,
    symbols: List[str],
    region: str,
    use_case: str = 'default',
    force: bool = False
) -> Dict:
    """Refresh prices for symbols"""
    return await MarketDataService.refresh_prices_for_symbols(
        db, symbols, region, use_case, force
    )


async def get_prices(db: AsyncSession, symbols: List[str]) -> Dict[str, Decimal]:
    """Get current prices from database"""
    return await MarketDataService.get_current_prices(db, symbols)
