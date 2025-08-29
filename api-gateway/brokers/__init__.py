"""
Broker integrations package
Exports: Base types, concrete brokers, and managers (no duplicates).
"""

import logging

from .base import (
    BrokerType, OrderType, OrderSide, OrderStatus,
    Position, Order, BaseBroker,
)
from .zerodha import ZerodhaBroker
from .alpaca import AlpacaBroker
from .managers import (
    BrokerFactory, BrokerManager, BrokerConnectionPool, BrokerEventManager,
    BrokerEvents, BrokerMetrics, broker_manager, connection_pool,
    event_manager, broker_metrics, monitor_broker_operation
)

logger = logging.getLogger(__name__)

__version__ = "1.1.0"
__author__ = "Trading Platform Team"
__description__ = "Multi-broker trading integration for Zerodha and Alpaca"

__all__ = [
    # Base classes and enums
    "BrokerType", "OrderType", "OrderSide", "OrderStatus", "Position", "Order", "BaseBroker",
    # Concrete brokers
    "ZerodhaBroker", "AlpacaBroker",
    # Management classes
    "BrokerFactory", "BrokerManager", "BrokerConnectionPool", "BrokerEventManager",
    "BrokerEvents", "BrokerMetrics",
    # Global instances
    "broker_manager", "connection_pool", "event_manager", "broker_metrics",
    # Utilities
    "monitor_broker_operation",
    # Package meta
    "__version__", "__author__", "__description__",
]

# Convenience functions
def get_supported_brokers():
    """Get list of all supported brokers"""
    return BrokerFactory.get_supported_brokers()

def create_broker(broker_type: str, api_key: str, secret: str, paper_trading: bool = True) -> BaseBroker:
    """Convenience function to create a broker instance"""
    return BrokerFactory.create_broker(BrokerType(broker_type), api_key, secret, paper_trading)

def get_broker_info(broker_type: str):
    """Get information about a specific broker"""
    return BrokerFactory.get_broker_info(broker_type)

async def initialize_brokers():
    """Initialize global broker components"""
    await broker_manager.start_health_monitoring()
    return True

async def cleanup_brokers():
    """Cleanup all broker connections and resources"""
    await broker_manager.close_all()
    await connection_pool.close_all_pools()
    broker_metrics.reset_metrics()

async def quick_connect(broker_type: str, api_key: str, secret: str, 
                       user_id: str, broker_name: str = None, paper_trading: bool = True) -> bool:
    """Quick way to connect a broker for a user"""
    try:
        broker = create_broker(broker_type, api_key, secret, paper_trading)
        connection_name = f"{user_id}_{broker_name or broker_type}"
        return await broker_manager.add_broker(connection_name, broker)
    except Exception as e:
        logger.error(f"Quick connect failed: {e}")
        return False

async def quick_disconnect(user_id: str, broker_name: str = None) -> bool:
    """Quick way to disconnect a broker for a user"""
    try:
        if broker_name:
            connection_name = f"{user_id}_{broker_name}"
            return await broker_manager.remove_broker(connection_name)
        else:
            removed_count = await broker_manager.remove_user_brokers(user_id)
            return removed_count > 0
    except Exception as e:
        logger.error(f"Quick disconnect failed: {e}")
        return False

def get_broker_status(user_id: str, broker_name: str = None):
    """Get status of user's brokers"""
    try:
        if broker_name:
            connection_name = f"{user_id}_{broker_name}"
            broker = broker_manager.get_broker(connection_name)
            if broker:
                return {
                    "broker_name": broker_name,
                    "authenticated": broker.authenticated,
                    "paper_trading": broker.paper_trading,
                    "broker_type": broker.get_broker_type(),
                    "status": "connected"
                }
            else:
                return {"broker_name": broker_name, "status": "not_found"}
        else:
            user_brokers = broker_manager.list_user_brokers(user_id)
            status = {}
            for name in user_brokers:
                connection_name = f"{user_id}_{name}"
                broker = broker_manager.get_broker(connection_name)
                if broker:
                    status[name] = {
                        "authenticated": broker.authenticated,
                        "paper_trading": broker.paper_trading,
                        "broker_type": broker.get_broker_type(),
                        "status": "connected"
                    }
            return status
    except Exception as e:
        logger.error(f"Error getting broker status: {e}")
        return {"error": str(e)}

def list_active_brokers():
    """Get list of all active broker connections"""
    return broker_manager.list_brokers()

async def health_check_all():
    """Perform health check on all active brokers"""
    try:
        return await broker_manager.health_check_all()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {}
