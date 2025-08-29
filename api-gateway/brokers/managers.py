"""
Broker factory and manager for handling multiple broker connections
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json

from .base import BaseBroker, BrokerType
from .zerodha import ZerodhaBroker
from .alpaca import AlpacaBroker

logger = logging.getLogger(__name__)


class BrokerEvents(str, Enum):
    """Broker event types"""
    BROKER_CONNECTED = "broker_connected"
    BROKER_DISCONNECTED = "broker_disconnected"
    BROKER_ERROR = "broker_error"
    BROKER_HEALTH_CHECK = "broker_health_check"


class BrokerConnectionPool:
    """Connection pool for managing broker connections"""
    
    def __init__(self):
        self.pools: Dict[str, List[BaseBroker]] = {}
    
    async def close_all_pools(self):
        """Close all connection pools"""
        for pool_name, brokers in self.pools.items():
            for broker in brokers:
                try:
                    await broker.close()
                except Exception as e:
                    logger.error(f"Error closing broker in pool {pool_name}: {e}")
        self.pools.clear()


class BrokerEventManager:
    """Event manager for broker events"""
    
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = {}
    
    async def emit(self, event: str, data: Dict[str, Any]):
        """Emit an event"""
        if event in self.listeners:
            for listener in self.listeners[event]:
                try:
                    await listener(data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event}: {e}")
    
    def subscribe(self, event: str, listener: callable):
        """Subscribe to an event"""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)


class BrokerMetrics:
    """Metrics collector for broker operations"""
    
    def __init__(self):
        self.request_counts: Dict[str, int] = {}
        self.response_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
    
    def record_request(self, broker_name: str, response_time: float, success: bool):
        """Record a broker request"""
        if broker_name not in self.request_counts:
            self.request_counts[broker_name] = 0
            self.response_times[broker_name] = []
            self.error_counts[broker_name] = 0
        
        self.request_counts[broker_name] += 1
        self.response_times[broker_name].append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times[broker_name]) > 100:
            self.response_times[broker_name] = self.response_times[broker_name][-100:]
        
        if not success:
            self.error_counts[broker_name] += 1
    
    def get_metrics(self, broker_name: str = None) -> Dict[str, Any]:
        """Get metrics for a broker or all brokers"""
        if broker_name:
            return {
                "request_count": self.request_counts.get(broker_name, 0),
                "error_count": self.error_counts.get(broker_name, 0),
                "avg_response_time": sum(self.response_times.get(broker_name, [])) / len(self.response_times.get(broker_name, [1])),
                "error_rate": self.error_counts.get(broker_name, 0) / max(1, self.request_counts.get(broker_name, 1))
            }
        
        return {
            "total_requests": sum(self.request_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "brokers": {
                name: self.get_metrics(name) for name in self.request_counts.keys()
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.request_counts.clear()
        self.response_times.clear()
        self.error_counts.clear()


class BrokerFactory:
    """Factory class to create broker instances"""
    
    @staticmethod
    def create_broker(broker_type: BrokerType, api_key: str, secret: str, 
                     paper_trading: bool = True) -> BaseBroker:
        """Create a broker instance based on type"""
        broker_type_lower = broker_type.lower() if isinstance(broker_type, str) else broker_type.value.lower()
        
        if broker_type_lower == "zerodha":
            return ZerodhaBroker(api_key, secret, paper_trading)
        elif broker_type_lower == "alpaca":
            return AlpacaBroker(api_key, secret, paper_trading)
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")
    
    @staticmethod
    def get_supported_brokers() -> List[str]:
        """Get list of supported broker types"""
        return ["zerodha", "alpaca"]
    
    @staticmethod
    def get_broker_info(broker_type: str) -> Dict[str, Any]:
        """Get information about a broker type"""
        broker_info = {
            "zerodha": {
                "name": "Zerodha Kite Connect",
                "country": "India",
                "markets": ["NSE", "BSE", "MCX", "NCDEX"],
                "asset_types": ["equity", "futures", "options", "commodity"],
                "api_docs": "https://kite.trade/docs/connect/v3/",
                "paper_trading": True
            },
            "alpaca": {
                "name": "Alpaca Trading",
                "country": "United States", 
                "markets": ["NASDAQ", "NYSE", "AMEX", "ARCA"],
                "asset_types": ["equity", "crypto"],
                "api_docs": "https://alpaca.markets/docs/",
                "paper_trading": True
            }
        }
        
        return broker_info.get(broker_type.lower(), {})


class BrokerManager:
    """Manager class to handle multiple broker connections"""
    
    def __init__(self):
        self.brokers: Dict[str, BaseBroker] = {}
        self._connection_health: Dict[str, datetime] = {}
        self._connection_errors: Dict[str, List[str]] = {}
        self._health_check_interval = 300  # 5 minutes
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def add_broker(self, name: str, broker: BaseBroker) -> bool:
        """Add a broker connection"""
        try:
            logger.info(f"Adding broker connection: {name}")
            
            if await broker.authenticate():
                self.brokers[name] = broker
                self._connection_health[name] = datetime.utcnow()
                self._connection_errors[name] = []
                
                logger.info(f"Successfully added broker: {name}")
                return True
            else:
                logger.error(f"Failed to authenticate broker: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding broker {name}: {e}")
            self._connection_errors[name] = [str(e)]
            return False
    
    def get_broker(self, name: str) -> Optional[BaseBroker]:
        """Get a broker by name"""
        return self.brokers.get(name)
    
    def list_brokers(self) -> List[str]:
        """List all available broker names"""
        return list(self.brokers.keys())
    
    def list_user_brokers(self, user_id: str) -> List[str]:
        """List brokers for a specific user"""
        user_prefix = f"{user_id}_"
        return [
            name[len(user_prefix):] 
            for name in self.brokers.keys() 
            if name.startswith(user_prefix)
        ]
    
    def get_user_broker(self, user_id: str, broker_name: str) -> Optional[BaseBroker]:
        """Get a broker for a specific user"""
        full_name = f"{user_id}_{broker_name}"
        return self.brokers.get(full_name)
    
    async def remove_broker(self, name: str) -> bool:
        """Remove a broker connection"""
        if name in self.brokers:
            try:
                await self.brokers[name].close()
                del self.brokers[name]
                
                if name in self._connection_health:
                    del self._connection_health[name]
                if name in self._connection_errors:
                    del self._connection_errors[name]
                    
                logger.info(f"Removed broker: {name}")
                return True
            except Exception as e:
                logger.error(f"Error removing broker {name}: {e}")
                return False
        return False
    
    async def remove_user_brokers(self, user_id: str) -> int:
        """Remove all brokers for a user"""
        user_prefix = f"{user_id}_"
        removed_count = 0
        
        broker_names = [name for name in self.brokers.keys() if name.startswith(user_prefix)]
        
        for name in broker_names:
            if await self.remove_broker(name):
                removed_count += 1
        
        return removed_count
    
    async def health_check(self, name: str) -> bool:
        """Check if broker connection is healthy"""
        broker = self.brokers.get(name)
        if not broker:
            return False
        
        try:
            # Simple authentication check
            result = await broker.authenticate()
            if result:
                self._connection_health[name] = datetime.utcnow()
                # Clear any previous errors
                if name in self._connection_errors:
                    self._connection_errors[name] = []
            return result
            
        except Exception as e:
            logger.error(f"Health check failed for broker {name}: {e}")
            if name not in self._connection_errors:
                self._connection_errors[name] = []
            self._connection_errors[name].append(str(e))
            # Keep only last 5 errors
            self._connection_errors[name] = self._connection_errors[name][-5:]
            return False
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all brokers"""
        results = {}
        for name in list(self.brokers.keys()):  # Create a copy to avoid modification during iteration
            results[name] = await self.health_check(name)
        return results
    
    async def start_health_monitoring(self):
        """Start periodic health monitoring"""
        if self._health_check_task and not self._health_check_task.done():
            return  # Already running
        
        self._health_check_task = asyncio.create_task(self._periodic_health_check())
        logger.info("Started broker health monitoring")
    
    async def stop_health_monitoring(self):
        """Stop periodic health monitoring"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped broker health monitoring")
    
    async def _periodic_health_check(self):
        """Periodic health check task"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                if self.brokers:
                    logger.debug(f"Running health check for {len(self.brokers)} brokers")
                    results = await self.health_check_all()
                    
                    unhealthy_brokers = [name for name, healthy in results.items() if not healthy]
                    if unhealthy_brokers:
                        logger.warning(f"Unhealthy brokers detected: {unhealthy_brokers}")
                
            except asyncio.CancelledError:
                logger.info("Health monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
    
    async def reconnect_broker(self, name: str) -> bool:
        """Attempt to reconnect a broker"""
        broker = self.brokers.get(name)
        if not broker:
            return False
        
        try:
            logger.info(f"Attempting to reconnect broker: {name}")
            
            # Close existing connection
            await broker.close()
            
            # Create new HTTP client
            import httpx
            broker.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Test authentication
            if await broker.authenticate():
                self._connection_health[name] = datetime.utcnow()
                if name in self._connection_errors:
                    self._connection_errors[name] = []
                logger.info(f"Successfully reconnected broker: {name}")
                return True
            else:
                logger.error(f"Failed to reconnect broker: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Error reconnecting broker {name}: {e}")
            if name not in self._connection_errors:
                self._connection_errors[name] = []
            self._connection_errors[name].append(f"Reconnect failed: {str(e)}")
            return False
    
    async def close_all(self):
        """Close all broker connections"""
        logger.info("Closing all broker connections")
        
        # Stop health monitoring
        await self.stop_health_monitoring()
        
        # Close all brokers
        for name, broker in list(self.brokers.items()):
            try:
                await broker.close()
                logger.info(f"Closed broker: {name}")
            except Exception as e:
                logger.error(f"Error closing broker {name}: {e}")
        
        self.brokers.clear()
        self._connection_health.clear()
        self._connection_errors.clear()
    
    def get_connection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get connection statistics for all brokers"""
        stats = {}
        for name, broker in self.brokers.items():
            last_health_check = self._connection_health.get(name)
            errors = self._connection_errors.get(name, [])
            
            stats[name] = {
                "broker_type": broker.get_broker_type(),
                "paper_trading": broker.paper_trading,
                "authenticated": broker.authenticated,
                "last_health_check": last_health_check.isoformat() if last_health_check else None,
                "uptime_minutes": int((datetime.utcnow() - last_health_check).total_seconds() / 60) if last_health_check else 0,
                "error_count": len(errors),
                "recent_errors": errors[-3:] if errors else []  # Last 3 errors
            }
        return stats
    
    def get_broker_summary(self) -> Dict[str, Any]:
        """Get summary of all brokers"""
        total_brokers = len(self.brokers)
        healthy_brokers = 0
        broker_types = {}
        
        for name, broker in self.brokers.items():
            # Check if broker was healthy in last 10 minutes
            last_check = self._connection_health.get(name)
            if last_check and (datetime.utcnow() - last_check).total_seconds() < 600:
                healthy_brokers += 1
            
            broker_type = broker.get_broker_type()
            broker_types[broker_type] = broker_types.get(broker_type, 0) + 1
        
        return {
            "total_brokers": total_brokers,
            "healthy_brokers": healthy_brokers,
            "unhealthy_brokers": total_brokers - healthy_brokers,
            "broker_types": broker_types,
            "health_check_interval_seconds": self._health_check_interval,
            "monitoring_active": self._health_check_task is not None and not self._health_check_task.done()
        }
    
    async def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Test all broker connections and return detailed results"""
        results = {}
        
        for name, broker in self.brokers.items():
            start_time = datetime.utcnow()
            
            try:
                # Test authentication
                auth_result = await broker.authenticate()
                
                # Test basic API call
                account_info = None
                if auth_result:
                    try:
                        account_info = await broker.get_account_info()
                    except Exception as e:
                        logger.warning(f"Account info failed for {name}: {e}")
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                results[name] = {
                    "status": "connected" if auth_result else "auth_failed",
                    "broker_type": broker.get_broker_type(),
                    "paper_trading": broker.paper_trading,
                    "response_time_ms": round(response_time, 2),
                    "account_info_available": account_info is not None,
                    "last_tested": start_time.isoformat()
                }
                
            except Exception as e:
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                results[name] = {
                    "status": "error",
                    "broker_type": broker.get_broker_type(),
                    "paper_trading": broker.paper_trading,
                    "response_time_ms": round(response_time, 2),
                    "error": str(e),
                    "last_tested": start_time.isoformat()
                }
        
        return results


# Global broker manager instance
broker_manager = BrokerManager()


class BrokerConnectionPool:
    """Connection pool for managing broker connections efficiently"""
    
    def __init__(self, max_connections_per_broker: int = 5):
        self.max_connections = max_connections_per_broker
        self.connection_pools: Dict[str, List[BaseBroker]] = {}
        self.active_connections: Dict[str, int] = {}
    
    async def get_connection(self, broker_type: str, api_key: str, secret: str, 
                           paper_trading: bool = True) -> BaseBroker:
        """Get a connection from the pool or create a new one"""
        pool_key = f"{broker_type}_{api_key}_{paper_trading}"
        
        if pool_key not in self.connection_pools:
            self.connection_pools[pool_key] = []
            self.active_connections[pool_key] = 0
        
        # Try to get an existing connection from the pool
        pool = self.connection_pools[pool_key]
        for broker in pool:
            if broker.authenticated and await broker.is_authenticated():
                pool.remove(broker)
                self.active_connections[pool_key] += 1
                return broker
        
        # Create a new connection if under limit
        if self.active_connections[pool_key] < self.max_connections:
            broker = BrokerFactory.create_broker(
                BrokerType(broker_type), api_key, secret, paper_trading
            )
            
            if await broker.authenticate():
                self.active_connections[pool_key] += 1
                return broker
            else:
                raise Exception(f"Failed to authenticate new {broker_type} connection")
        
        raise Exception(f"Maximum connections reached for {broker_type}")
    
    async def return_connection(self, broker: BaseBroker):
        """Return a connection to the pool"""
        broker_type = broker.get_broker_type()
        pool_key = f"{broker_type}_{broker.api_key}_{broker.paper_trading}"
        
        if pool_key in self.connection_pools:
            self.connection_pools[pool_key].append(broker)
            self.active_connections[pool_key] = max(0, self.active_connections[pool_key] - 1)
    
    async def close_all_pools(self):
        """Close all connections in all pools"""
        for pool_key, pool in self.connection_pools.items():
            for broker in pool:
                await broker.close()
        
        self.connection_pools.clear()
        self.active_connections.clear()


# Global connection pool instance
connection_pool = BrokerConnectionPool()


class BrokerEventManager:
    """Event manager for broker-related events"""
    
    def __init__(self):
        self.event_handlers = {}
    
    def on(self, event_type: str, handler):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    def remove_handler(self, event_type: str, handler):
        """Remove an event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass


# Global event manager instance
event_manager = BrokerEventManager()


# Event types
class BrokerEvents:
    BROKER_CONNECTED = "broker_connected"
    BROKER_DISCONNECTED = "broker_disconnected"
    BROKER_ERROR = "broker_error"
    ORDER_FILLED = "order_filled"
    ORDER_REJECTED = "order_rejected"
    POSITION_UPDATED = "position_updated"
    ACCOUNT_UPDATED = "account_updated"


class BrokerMetrics:
    """Collect and track broker performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "requests": {},  # broker_name -> count
            "response_times": {},  # broker_name -> list of times
            "errors": {},  # broker_name -> count
            "orders": {},  # broker_name -> count
            "last_reset": datetime.utcnow()
        }
    
    def record_request(self, broker_name: str, response_time_ms: float, success: bool):
        """Record an API request"""
        if broker_name not in self.metrics["requests"]:
            self.metrics["requests"][broker_name] = 0
            self.metrics["response_times"][broker_name] = []
            self.metrics["errors"][broker_name] = 0
        
        self.metrics["requests"][broker_name] += 1
        self.metrics["response_times"][broker_name].append(response_time_ms)
        
        if not success:
            self.metrics["errors"][broker_name] += 1
        
        # Keep only last 100 response times
        if len(self.metrics["response_times"][broker_name]) > 100:
            self.metrics["response_times"][broker_name] = self.metrics["response_times"][broker_name][-100:]
    
    def record_order(self, broker_name: str):
        """Record an order placement"""
        if broker_name not in self.metrics["orders"]:
            self.metrics["orders"][broker_name] = 0
        self.metrics["orders"][broker_name] += 1
    
    def get_metrics(self, broker_name: str = None) -> Dict[str, Any]:
        """Get metrics for a specific broker or all brokers"""
        if broker_name:
            response_times = self.metrics["response_times"].get(broker_name, [])
            return {
                "requests": self.metrics["requests"].get(broker_name, 0),
                "errors": self.metrics["errors"].get(broker_name, 0),
                "orders": self.metrics["orders"].get(broker_name, 0),
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "error_rate": self.metrics["errors"].get(broker_name, 0) / max(1, self.metrics["requests"].get(broker_name, 1)),
                "last_reset": self.metrics["last_reset"].isoformat()
            }
        else:
            # Return summary for all brokers
            summary = {}
            for name in set(list(self.metrics["requests"].keys()) + list(self.metrics["orders"].keys())):
                summary[name] = self.get_metrics(name)
            return summary
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "requests": {},
            "response_times": {},
            "errors": {},
            "orders": {},
            "last_reset": datetime.utcnow()
        }


# Global metrics instance
broker_metrics = BrokerMetrics()


# Decorator for monitoring broker operations
def monitor_broker_operation(operation_name: str):
    """Decorator to monitor broker operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            broker_name = "unknown"
            
            try:
                # Try to extract broker name from first argument (usually self)
                if args and hasattr(args[0], 'get_broker_type'):
                    broker_name = args[0].get_broker_type()
                
                result = await func(*args, **kwargs)
                
                # Record successful operation
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                broker_metrics.record_request(broker_name, response_time, True)
                
                return result
                
            except Exception as e:
                # Record failed operation
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                broker_metrics.record_request(broker_name, response_time, False)
                
                # Emit error event
                await event_manager.emit(BrokerEvents.BROKER_ERROR, {
                    "broker_name": broker_name,
                    "operation": operation_name,
                    "error": str(e),
                    "timestamp": start_time.isoformat()
                })
                
                raise
        
        return wrapper
    return decorator


# Global instances
broker_manager = BrokerManager()
connection_pool = BrokerConnectionPool()
event_manager = BrokerEventManager()
broker_metrics = BrokerMetrics()


__all__ = [
    "BrokerFactory", "BrokerManager", "BrokerConnectionPool", "BrokerEventManager",
    "BrokerEvents", "BrokerMetrics", "broker_manager", "connection_pool", 
    "event_manager", "broker_metrics", "monitor_broker_operation"
]