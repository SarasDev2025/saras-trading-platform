"""
Broker Configuration Service
Handles configuration and routing between paper and live trading APIs
"""

import os
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class BrokerConfigService:
    """Service for managing broker configurations and API routing"""

    @staticmethod
    def get_environment_config() -> Dict[str, Any]:
        """Get broker configuration from environment variables"""
        return {
            "default_trading_mode": os.getenv("DEFAULT_TRADING_MODE", "paper"),
            "allow_live_trading": os.getenv("ALLOW_LIVE_TRADING", "false").lower() == "true",

            # Alpaca Configuration
            "alpaca": {
                "paper": {
                    "api_key": os.getenv("ALPACA_API_KEY"),
                    "secret_key": os.getenv("ALPACA_SECRET_KEY"),
                    "base_url": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
                },
                "live": {
                    "api_key": os.getenv("ALPACA_LIVE_API_KEY"),
                    "secret_key": os.getenv("ALPACA_LIVE_SECRET_KEY"),
                    "base_url": os.getenv("ALPACA_LIVE_BASE_URL", "https://api.alpaca.markets")
                }
            },

            # Zerodha Configuration
            "zerodha": {
                "paper": {
                    "api_key": os.getenv("ZERODHA_API_KEY"),
                    "secret_key": os.getenv("ZERODHA_SECRET_KEY"),
                    "base_url": os.getenv("ZERODHA_BASE_URL", "https://api.kite.trade")
                },
                "live": {
                    "api_key": os.getenv("ZERODHA_LIVE_API_KEY"),
                    "secret_key": os.getenv("ZERODHA_LIVE_SECRET_KEY"),
                    "base_url": os.getenv("ZERODHA_LIVE_BASE_URL", "https://api.kite.trade")
                }
            }
        }

    @staticmethod
    async def get_broker_connection_config(
        db: AsyncSession,
        broker_connection_id: str
    ) -> Dict[str, Any]:
        """Get broker configuration for a specific connection"""
        try:
            result = await db.execute(text("""
                SELECT
                    broker_type,
                    paper_trading,
                    credentials,
                    status
                FROM user_broker_connections
                WHERE id = :connection_id AND status = 'active'
            """), {"connection_id": broker_connection_id})

            connection = result.fetchone()
            if not connection:
                raise ValueError(f"Broker connection {broker_connection_id} not found or inactive")

            broker_type = connection[0]
            paper_trading = connection[1]
            credentials = connection[2] or {}

            # Get environment configuration
            env_config = BrokerConfigService.get_environment_config()

            # Determine trading mode
            trading_mode = "paper" if paper_trading else "live"

            # Get broker-specific configuration
            if broker_type not in env_config:
                raise ValueError(f"Unsupported broker type: {broker_type}")

            broker_config = env_config[broker_type][trading_mode]

            # Validate live trading is allowed
            if trading_mode == "live" and not env_config["allow_live_trading"]:
                logger.warning(f"Live trading not allowed for connection {broker_connection_id}")
                raise ValueError("Live trading is not enabled in this environment")

            # Validate credentials are available
            if not broker_config["api_key"] or not broker_config["secret_key"]:
                logger.error(f"Missing {trading_mode} credentials for {broker_type}")
                raise ValueError(f"Missing {trading_mode} credentials for {broker_type}")

            return {
                "broker_type": broker_type,
                "trading_mode": trading_mode,
                "api_key": broker_config["api_key"],
                "secret_key": broker_config["secret_key"],
                "base_url": broker_config["base_url"],
                "paper_trading": paper_trading,
                "credentials": credentials
            }

        except Exception as e:
            logger.error(f"Failed to get broker connection config: {str(e)}")
            raise

    @staticmethod
    def get_broker_config_by_type(broker_type: str, paper_trading: bool = True) -> Dict[str, Any]:
        """Get broker configuration by type and trading mode"""
        env_config = BrokerConfigService.get_environment_config()

        if broker_type not in env_config:
            raise ValueError(f"Unsupported broker type: {broker_type}")

        trading_mode = "paper" if paper_trading else "live"

        # Validate live trading is allowed
        if trading_mode == "live" and not env_config["allow_live_trading"]:
            raise ValueError("Live trading is not enabled in this environment")

        broker_config = env_config[broker_type][trading_mode]

        # Validate credentials are available
        if not broker_config["api_key"] or not broker_config["secret_key"]:
            raise ValueError(f"Missing {trading_mode} credentials for {broker_type}")

        return {
            "broker_type": broker_type,
            "trading_mode": trading_mode,
            "api_key": broker_config["api_key"],
            "secret_key": broker_config["secret_key"],
            "base_url": broker_config["base_url"],
            "paper_trading": paper_trading
        }

    @staticmethod
    def validate_trading_mode_switch(
        current_mode: str,
        requested_mode: str,
        investment_amount: float
    ) -> Dict[str, Any]:
        """Validate if a trading mode switch is allowed"""
        env_config = BrokerConfigService.get_environment_config()

        validation_result = {
            "allowed": True,
            "warnings": [],
            "errors": [],
            "requirements": []
        }

        # Check if live trading is allowed in environment
        if requested_mode == "live" and not env_config["allow_live_trading"]:
            validation_result["allowed"] = False
            validation_result["errors"].append("Live trading is not enabled in this environment")

        # Check investment amount limits for live trading
        if requested_mode == "live":
            min_live_amount = 1000.0  # Minimum $1000 for live trading
            max_live_amount = 100000.0  # Maximum $100K for new live accounts

            if investment_amount < min_live_amount:
                validation_result["allowed"] = False
                validation_result["errors"].append(f"Minimum investment for live trading is ${min_live_amount:,.2f}")

            if investment_amount > max_live_amount:
                validation_result["warnings"].append(
                    f"Large investment amount (${investment_amount:,.2f}). Consider starting with smaller amounts."
                )

            # Add requirements for live trading
            validation_result["requirements"].extend([
                "Valid live broker account with sufficient funds",
                "Completed KYC verification",
                "Acknowledgment of live trading risks",
                "Confirmation of investment amount"
            ])

        # Switching from live to paper
        if current_mode == "live" and requested_mode == "paper":
            validation_result["warnings"].append(
                "Switching from live to paper trading. This will use simulated funds."
            )

        return validation_result

    @staticmethod
    def get_trading_mode_description(trading_mode: str) -> Dict[str, str]:
        """Get user-friendly description of trading modes"""
        descriptions = {
            "paper": {
                "title": "Paper Trading",
                "description": "Simulated trading with virtual money. Perfect for testing strategies risk-free.",
                "benefits": ["No real money at risk", "Practice trading strategies", "Learn platform features"],
                "limitations": ["Virtual profits/losses only", "May not reflect real market conditions"]
            },
            "live": {
                "title": "Live Trading",
                "description": "Real trading with actual money. All trades execute with real funds.",
                "benefits": ["Real profits and growth", "Actual market execution", "Build real portfolio"],
                "limitations": ["Real money at risk", "Actual losses possible", "Requires funded broker account"]
            }
        }

        return descriptions.get(trading_mode, {
            "title": "Unknown Mode",
            "description": "Unknown trading mode",
            "benefits": [],
            "limitations": []
        })