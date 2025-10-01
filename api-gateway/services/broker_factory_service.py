"""
Broker Factory Service
Creates broker instances with proper configuration based on trading mode
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..brokers.alpaca import AlpacaBroker
from ..brokers.zerodha import ZerodhaBroker
from ..brokers.base import BaseBroker
from .broker_config_service import BrokerConfigService

logger = logging.getLogger(__name__)


class BrokerFactoryService:
    """Factory service for creating configured broker instances"""

    @staticmethod
    async def create_broker_from_connection(
        db: AsyncSession,
        broker_connection_id: str
    ) -> BaseBroker:
        """Create a broker instance from a broker connection ID"""
        try:
            # Get configuration for this connection
            config = await BrokerConfigService.get_broker_connection_config(
                db, broker_connection_id
            )

            return BrokerFactoryService._create_broker_instance(config)

        except Exception as e:
            logger.error(f"Failed to create broker from connection {broker_connection_id}: {str(e)}")
            raise

    @staticmethod
    def create_broker_by_type(
        broker_type: str,
        paper_trading: bool = True,
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> BaseBroker:
        """Create a broker instance by type and trading mode"""
        try:
            if custom_credentials:
                # Use custom credentials (for testing or special cases)
                config = {
                    "broker_type": broker_type,
                    "trading_mode": "paper" if paper_trading else "live",
                    "paper_trading": paper_trading,
                    **custom_credentials
                }
            else:
                # Get configuration from environment
                config = BrokerConfigService.get_broker_config_by_type(broker_type, paper_trading)

            return BrokerFactoryService._create_broker_instance(config)

        except Exception as e:
            logger.error(f"Failed to create {broker_type} broker: {str(e)}")
            raise

    @staticmethod
    def _create_broker_instance(config: Dict[str, Any]) -> BaseBroker:
        """Create broker instance from configuration"""
        broker_type = config["broker_type"]
        api_key = config["api_key"]
        secret_key = config["secret_key"]
        paper_trading = config["paper_trading"]
        base_url = config.get("base_url")

        logger.info(f"Creating {broker_type} broker instance in {config['trading_mode']} mode")

        if broker_type == "alpaca":
            return AlpacaBroker(
                api_key=api_key,
                secret_key=secret_key,
                paper_trading=paper_trading,
                base_url=base_url
            )
        elif broker_type == "zerodha":
            return ZerodhaBroker(
                api_key=api_key,
                access_token=secret_key,  # Zerodha uses access_token instead of secret_key
                paper_trading=paper_trading,
                base_url=base_url
            )
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")

    @staticmethod
    def get_supported_brokers() -> Dict[str, Dict[str, Any]]:
        """Get list of supported brokers and their capabilities"""
        return {
            "alpaca": {
                "name": "Alpaca Trading",
                "regions": ["US"],
                "supports_paper_trading": True,
                "supports_live_trading": True,
                "supported_assets": ["stocks", "etfs", "crypto"],
                "minimum_live_investment": 1000.0,
                "commission_free": True
            },
            "zerodha": {
                "name": "Zerodha Kite",
                "regions": ["IN"],
                "supports_paper_trading": True,
                "supports_live_trading": True,
                "supported_assets": ["stocks", "etfs", "mutual_funds"],
                "minimum_live_investment": 500.0,  # ₹500 minimum
                "commission_free": False
            }
        }

    @staticmethod
    async def test_broker_connection(
        db: AsyncSession,
        broker_connection_id: str
    ) -> Dict[str, Any]:
        """Test a broker connection and return status"""
        try:
            broker = await BrokerFactoryService.create_broker_from_connection(
                db, broker_connection_id
            )

            # Attempt authentication
            auth_success = await broker.authenticate()

            if auth_success:
                # Get account info if authentication succeeds
                try:
                    account_info = await broker.get_account_info()
                    return {
                        "status": "connected",
                        "authenticated": True,
                        "account_info": account_info,
                        "trading_mode": broker.trading_mode,
                        "message": f"Successfully connected to {broker.__class__.__name__}"
                    }
                except Exception as account_error:
                    logger.warning(f"Authentication succeeded but failed to get account info: {account_error}")
                    return {
                        "status": "connected",
                        "authenticated": True,
                        "account_info": None,
                        "trading_mode": broker.trading_mode,
                        "message": "Connected but unable to retrieve account information"
                    }
            else:
                return {
                    "status": "failed",
                    "authenticated": False,
                    "error": "Authentication failed",
                    "trading_mode": broker.trading_mode
                }

        except Exception as e:
            logger.error(f"Broker connection test failed: {str(e)}")
            return {
                "status": "error",
                "authenticated": False,
                "error": str(e),
                "trading_mode": "unknown"
            }

    @staticmethod
    def validate_broker_credentials(
        broker_type: str,
        credentials: Dict[str, str],
        trading_mode: str
    ) -> Dict[str, Any]:
        """Validate broker credentials format"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        required_fields = {
            "alpaca": ["api_key", "secret_key"],
            "zerodha": ["api_key", "access_token"]
        }

        if broker_type not in required_fields:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported broker type: {broker_type}")
            return validation_result

        # Check required fields
        for field in required_fields[broker_type]:
            if field not in credentials or not credentials[field]:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")

        # Validate field formats
        if broker_type == "alpaca":
            api_key = credentials.get("api_key", "")
            if api_key and (len(api_key) < 20 or not api_key.isalnum()):
                validation_result["warnings"].append("Alpaca API key format may be incorrect")

        elif broker_type == "zerodha":
            api_key = credentials.get("api_key", "")
            if api_key and len(api_key) != 32:
                validation_result["warnings"].append("Zerodha API key should be 32 characters")

        # Trading mode specific validations
        if trading_mode == "live":
            validation_result["warnings"].append(
                "Live trading credentials will execute real trades with actual money"
            )

        return validation_result