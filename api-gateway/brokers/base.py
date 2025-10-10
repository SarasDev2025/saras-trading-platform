"""
Base classes and interfaces for broker integrations
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import httpx

logger = logging.getLogger(__name__)


# Enums
class BrokerType(str, Enum):
    ZERODHA = "zerodha"
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "interactive_brokers"
    TD_AMERITRADE = "td_ameritrade"
    ROBINHOOD = "robinhood"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


# Exceptions
class BrokerError(Exception):
    """Base exception for broker-related errors"""
    def __init__(self, message: str, broker: str = None, error_code: str = None):
        self.message = message
        self.broker = broker
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(BrokerError):
    """Authentication failed with broker"""
    pass


class OrderError(BrokerError):
    """Order-related error"""
    pass


class MarketDataError(BrokerError):
    """Market data retrieval error"""
    pass


class RateLimitError(BrokerError):
    """Rate limit exceeded"""
    def __init__(self, message: str, broker: str = None, retry_after: int = None):
        super().__init__(message, broker)
        self.retry_after = retry_after


class InsufficientFundsError(BrokerError):
    """Insufficient funds for order"""
    pass


class InvalidSymbolError(BrokerError):
    """Invalid or unsupported symbol"""
    pass


# Data classes
class Position:
    """Represents a trading position"""
    
    def __init__(self, symbol: str, quantity: Decimal, avg_price: Decimal, market_value: Decimal):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_price = avg_price
        self.market_value = market_value
        self.unrealized_pnl: Optional[Decimal] = None
        self.realized_pnl: Optional[Decimal] = None
        self.cost_basis: Optional[Decimal] = None
        self.last_updated = datetime.utcnow()
    
    @property
    def current_price(self) -> Optional[Decimal]:
        """Calculate current price from market value and quantity"""
        if self.quantity != 0:
            return self.market_value / abs(self.quantity)
        return None
    
    def calculate_unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L"""
        if self.quantity == 0:
            return Decimal('0')
        
        current_value = current_price * abs(self.quantity)
        cost_value = self.avg_price * abs(self.quantity)
        
        if self.quantity > 0:  # Long position
            return current_value - cost_value
        else:  # Short position
            return cost_value - current_value
    
    def __repr__(self) -> str:
        return f"<Position(symbol={self.symbol}, quantity={self.quantity}, value={self.market_value})>"


class Order:
    """Represents a trading order"""
    
    def __init__(self, order_id: str, symbol: str, side: OrderSide, quantity: Decimal, 
                 order_type: OrderType, status: OrderStatus, price: Optional[Decimal] = None):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.status = status
        self.price = price
        self.filled_quantity: Decimal = Decimal('0')
        self.average_fill_price: Optional[Decimal] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.filled_at: Optional[datetime] = None
        self.commission: Optional[Decimal] = None
        self.notes: Optional[str] = None
        self.client_order_id: Optional[str] = None
        self.exchange_order_id: Optional[str] = None
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Get remaining quantity to be filled"""
        return self.quantity - self.filled_quantity
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage (0-100)"""
        if self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity * 100)
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
    
    def update_fill(self, filled_quantity: Decimal, fill_price: Decimal):
        """Update order with fill information"""
        self.filled_quantity = filled_quantity
        self.updated_at = datetime.utcnow()
        
        if filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.utcnow()
        elif filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED
        
        # Update average fill price
        if self.average_fill_price is None:
            self.average_fill_price = fill_price
        else:
            # Weighted average
            total_value = (self.average_fill_price * (self.filled_quantity - filled_quantity)) + (fill_price * filled_quantity)
            self.average_fill_price = total_value / self.filled_quantity
    
    def __repr__(self) -> str:
        return f"<Order(id={self.order_id}, symbol={self.symbol}, side={self.side}, status={self.status})>"


# Utility functions
def convert_to_decimal(value: Any) -> Decimal:
    """Safely convert value to Decimal"""
    if value is None:
        return Decimal('0')
    
    if isinstance(value, Decimal):
        return value
    
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to Decimal, returning 0")
        return Decimal('0')


def safe_float(value: Any) -> float:
    """Safely convert value to float"""
    if value is None:
        return 0.0
    
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to float, returning 0.0")
        return 0.0


def safe_int(value: Any) -> int:
    """Safely convert value to int"""
    if value is None:
        return 0
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to int, returning 0")
        return 0


# Base broker class
class BaseBroker(ABC):
    """Abstract base class for all broker integrations"""
    
    def __init__(self, api_key: str, secret: str, paper_trading: bool = True):
        self.api_key = api_key
        self.secret = secret
        self.paper_trading = paper_trading
        self.authenticated = False
        self.last_auth_check: Optional[datetime] = None
        self.rate_limit_reset: Optional[datetime] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self._create_http_client()
    
    def _create_http_client(self):
        """Create HTTP client with proper configuration"""
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    
    async def ensure_authenticated(self):
        """Ensure broker is authenticated, re-authenticate if needed"""
        if not self.authenticated or self._needs_reauth():
            if not await self.authenticate():
                raise AuthenticationError("Failed to authenticate with broker", self.get_broker_type())
    
    def _needs_reauth(self) -> bool:
        """Check if re-authentication is needed"""
        if not self.last_auth_check:
            return True
        
        # Re-authenticate every hour
        return datetime.utcnow() - self.last_auth_check > timedelta(hours=1)
    
    async def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        try:
            return await self.authenticate()
        except Exception:
            return False
    
    def get_broker_type(self) -> str:
        """Get broker type identifier"""
        return self.__class__.__name__.lower().replace('broker', '')
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the broker"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, side: OrderSide, quantity: Decimal, 
                         order_type: OrderType, price: Optional[Decimal] = None) -> Order:
        """Place a trading order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Order:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, period: str) -> List[Dict[str, Any]]:
        """Get historical price data"""
        pass
    
    # Optional methods with default implementations
    async def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify an existing order (optional)"""
        raise NotImplementedError("Order modification not supported by this broker")
    
    async def get_orders(self) -> List[Order]:
        """Get all orders (optional)"""
        raise NotImplementedError("Order listing not supported by this broker")

    def supports_fractional_shares(self) -> bool:
        """
        Check if broker supports fractional share trading.

        Returns:
            bool: True if broker supports fractional shares, False otherwise
        """
        return False  # Default: no fractional support

    async def get_trades(self) -> List[Dict[str, Any]]:
        """Get executed trades (optional)"""
        raise NotImplementedError("Trade listing not supported by this broker")
    
    async def get_watchlists(self) -> List[Dict[str, Any]]:
        """Get user watchlists (optional)"""
        raise NotImplementedError("Watchlists not supported by this broker")
    
    # Connection management
    async def close(self):
        """Close broker connection and cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        self.authenticated = False
        logger.info(f"Closed {self.get_broker_type()} broker connection")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    # Rate limiting helpers
    def check_rate_limit(self):
        """Check if rate limit allows request"""
        if self.rate_limit_reset and datetime.utcnow() < self.rate_limit_reset:
            raise RateLimitError(
                "Rate limit exceeded", 
                self.get_broker_type(),
                int((self.rate_limit_reset - datetime.utcnow()).total_seconds())
            )
    
    def set_rate_limit_reset(self, reset_time: datetime):
        """Set rate limit reset time"""
        self.rate_limit_reset = reset_time
    
    # Validation helpers
    def validate_symbol(self, symbol: str) -> str:
        """Validate and normalize symbol"""
        if not symbol or not isinstance(symbol, str):
            raise InvalidSymbolError("Invalid symbol format", self.get_broker_type())
        
        return symbol.upper().strip()
    
    def validate_quantity(self, quantity: Union[Decimal, float, int]) -> Decimal:
        """Validate and convert quantity"""
        try:
            qty = convert_to_decimal(quantity)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            return qty
        except Exception as e:
            raise OrderError(f"Invalid quantity: {e}", self.get_broker_type())
    
    def validate_price(self, price: Union[Decimal, float, int, None]) -> Optional[Decimal]:
        """Validate and convert price"""
        if price is None:
            return None
        
        try:
            p = convert_to_decimal(price)
            if p <= 0:
                raise ValueError("Price must be positive")
            return p
        except Exception as e:
            raise OrderError(f"Invalid price: {e}", self.get_broker_type())
    
    # Helper methods for common operations
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        positions = await self.get_positions()
        for position in positions:
            if position.symbol.upper() == symbol.upper():
                return position
        return None
    
    async def get_buying_power(self) -> Decimal:
        """Get available buying power"""
        balance = await self.get_balance()
        return balance.get('buying_power', balance.get('cash', Decimal('0')))
    
    async def get_portfolio_value(self) -> Decimal:
        """Get total portfolio value"""
        balance = await self.get_balance()
        return balance.get('portfolio_value', balance.get('total_value', Decimal('0')))
    
    # Market data helpers
    async def get_last_price(self, symbol: str) -> Optional[Decimal]:
        """Get last traded price for symbol"""
        try:
            market_data = await self.get_market_data(symbol)
            return market_data.get('last_price')
        except Exception as e:
            logger.warning(f"Failed to get last price for {symbol}: {e}")
            return None
    
    async def get_bid_ask(self, symbol: str) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """Get bid and ask prices"""
        try:
            market_data = await self.get_market_data(symbol)
            return market_data.get('bid_price'), market_data.get('ask_price')
        except Exception as e:
            logger.warning(f"Failed to get bid/ask for {symbol}: {e}")
            return None, None
    
    # Order helpers
    async def place_market_order(self, symbol: str, side: OrderSide, quantity: Decimal) -> Order:
        """Place a market order"""
        return await self.place_order(symbol, side, quantity, OrderType.MARKET)
    
    async def place_limit_order(self, symbol: str, side: OrderSide, quantity: Decimal, price: Decimal) -> Order:
        """Place a limit order"""
        return await self.place_order(symbol, side, quantity, OrderType.LIMIT, price)
    
    async def place_stop_order(self, symbol: str, side: OrderSide, quantity: Decimal, stop_price: Decimal) -> Order:
        """Place a stop order"""
        return await self.place_order(symbol, side, quantity, OrderType.STOP, stop_price)
    
    # Bulk operations
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[bool]:
        """Cancel all orders, optionally filtered by symbol"""
        try:
            orders = await self.get_orders()
            active_orders = [o for o in orders if o.is_active]
            
            if symbol:
                active_orders = [o for o in active_orders if o.symbol.upper() == symbol.upper()]
            
            results = []
            for order in active_orders:
                try:
                    result = await self.cancel_order(order.order_id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to cancel order {order.order_id}: {e}")
                    results.append(False)
            
            return results
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return []
    
    # Status and health checks
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            start_time = datetime.utcnow()
            
            # Test authentication
            auth_result = await self.authenticate()
            
            # Test basic API call
            account_info = None
            if auth_result:
                try:
                    account_info = await self.get_account_info()
                except Exception:
                    pass
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "broker": self.get_broker_type(),
                "authenticated": auth_result,
                "account_accessible": account_info is not None,
                "paper_trading": self.paper_trading,
                "response_time_ms": round(response_time, 2),
                "last_check": datetime.utcnow().isoformat(),
                "status": "healthy" if auth_result else "unhealthy"
            }
        except Exception as e:
            return {
                "broker": self.get_broker_type(),
                "authenticated": False,
                "account_accessible": False,
                "paper_trading": self.paper_trading,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
                "status": "error"
            }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(authenticated={self.authenticated}, paper_trading={self.paper_trading})>"


__all__ = [
    # Enums
    "BrokerType", "OrderType", "OrderSide", "OrderStatus",
    
    # Exceptions
    "BrokerError", "AuthenticationError", "OrderError", "MarketDataError", 
    "RateLimitError", "InsufficientFundsError", "InvalidSymbolError",
    
    # Data classes
    "Position", "Order",
    
    # Base class
    "BaseBroker",
    
    # Utilities
    "convert_to_decimal", "safe_float", "safe_int"
]
