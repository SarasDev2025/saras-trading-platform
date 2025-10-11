"""
Data Provider Factory
Selects appropriate historical data provider based on configuration
"""
import logging
import os
from typing import Dict, Optional

from .base import HistoricalDataProvider
from .yahoo_provider import YahooFinanceProvider
from .synthetic_provider import SyntheticDataProvider

logger = logging.getLogger(__name__)


class DataProviderFactory:
    """
    Factory for creating historical data providers

    Selects provider based on:
    1. Environment variable HISTORICAL_DATA_PROVIDER
    2. Broker/region
    3. Fallback to synthetic
    """

    _providers = {
        'yahoo': YahooFinanceProvider,
        'synthetic': SyntheticDataProvider,
        # Future providers can be added here:
        # 'alpaca': AlpacaHistoricalProvider,
        # 'zerodha': ZerodhaHistoricalProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider_name: Optional[str] = None,
        broker: Optional[str] = None,
        region: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> HistoricalDataProvider:
        """
        Create appropriate historical data provider

        Priority:
        1. Explicit provider_name parameter
        2. Environment variable HISTORICAL_DATA_PROVIDER
        3. Auto-detect based on broker/region
        4. Fallback to synthetic

        Args:
            provider_name: Explicit provider name ('yahoo', 'synthetic', etc.)
            broker: Broker name ('zerodha', 'alpaca')
            region: Market region ('US', 'IN')
            config: Provider-specific configuration

        Returns:
            HistoricalDataProvider instance

        Examples:
            # Explicit provider
            provider = DataProviderFactory.create_provider('yahoo')

            # Environment-based
            os.environ['HISTORICAL_DATA_PROVIDER'] = 'yahoo'
            provider = DataProviderFactory.create_provider()

            # Auto-detect
            provider = DataProviderFactory.create_provider(broker='alpaca', region='US')
        """
        config = config or {}

        # 1. Check explicit provider name
        if provider_name:
            return cls._create_by_name(provider_name, config)

        # 2. Check environment variable
        env_provider = os.getenv('HISTORICAL_DATA_PROVIDER')
        if env_provider:
            logger.info(f"Using provider from environment: {env_provider}")
            return cls._create_by_name(env_provider, config)

        # 3. Auto-detect based on broker
        if broker:
            auto_provider = cls._auto_detect_provider(broker, region)
            logger.info(f"Auto-detected provider: {auto_provider} for broker {broker}")
            return cls._create_by_name(auto_provider, config)

        # 4. Default to Yahoo Finance (free and widely available)
        logger.info("No provider specified, defaulting to Yahoo Finance")
        return cls._create_by_name('yahoo', config)

    @classmethod
    def _create_by_name(cls, name: str, config: Dict) -> HistoricalDataProvider:
        """
        Create provider by name

        Args:
            name: Provider name
            config: Configuration dict

        Returns:
            Provider instance

        Raises:
            ValueError: If provider name is invalid
        """
        name = name.lower()

        if name not in cls._providers:
            logger.warning(
                f"Unknown provider '{name}'. Available: {list(cls._providers.keys())}. "
                f"Falling back to synthetic provider."
            )
            return SyntheticDataProvider(config)

        try:
            provider_class = cls._providers[name]
            return provider_class(config)

        except Exception as e:
            logger.error(f"Failed to create provider '{name}': {e}. Falling back to synthetic.")
            return SyntheticDataProvider(config)

    @classmethod
    def _auto_detect_provider(cls, broker: str, region: Optional[str]) -> str:
        """
        Auto-detect best provider based on broker and region

        Args:
            broker: Broker name
            region: Market region

        Returns:
            Provider name
        """
        # Map brokers to preferred providers
        broker_mapping = {
            'alpaca': 'yahoo',  # Use Yahoo for US stocks (until Alpaca provider implemented)
            'zerodha': 'yahoo',  # Use Yahoo for Indian stocks (until Zerodha provider implemented)
        }

        # Check if we have a specific provider for this broker
        if broker and broker.lower() in broker_mapping:
            return broker_mapping[broker.lower()]

        # Default to Yahoo Finance (works for most markets)
        return 'yahoo'

    @classmethod
    async def test_provider(cls, provider: HistoricalDataProvider) -> bool:
        """
        Test if provider is working

        Args:
            provider: Provider instance to test

        Returns:
            True if provider can fetch data
        """
        try:
            return await provider.validate_connection()
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return False

    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get list of available provider names

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
