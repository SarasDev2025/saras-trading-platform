"""
Alpaca Trading API broker integration
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

from .base import (
    BaseBroker, Position, Order, OrderType, OrderSide, OrderStatus,
    AuthenticationError, OrderError, MarketDataError, convert_to_decimal, safe_float, safe_int
)
import logging

logger = logging.getLogger(__name__)


class AlpacaBroker(BaseBroker):
    """Alpaca Trading API integration"""
    
    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True):
        super().__init__(api_key, secret_key, paper_trading)
        self.secret_key = secret_key
        self.base_url = "https://paper-api.alpaca.markets" if paper_trading else "https://api.alpaca.markets"
        self.data_url = "https://data.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json"
        }
        self.account_info_cache = {}
        self.cache_expiry = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Alpaca"""
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.authenticated = True
                self.last_auth_check = datetime.utcnow()
                return True
            else:
                raise AuthenticationError("Alpaca authentication failed", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Alpaca authentication failed: {e}")
            self.authenticated = False
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(str(e), "alpaca")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Alpaca account information"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                account_data = response.json()
                
                # Cache account info for 5 minutes
                self.account_info_cache = {
                    "broker": "alpaca",
                    "account_id": account_data["id"],
                    "account_number": account_data["account_number"],
                    "status": account_data["status"],
                    "currency": account_data["currency"],
                    "buying_power": convert_to_decimal(account_data["buying_power"]),
                    "regt_buying_power": convert_to_decimal(account_data["regt_buying_power"]),
                    "daytrading_buying_power": convert_to_decimal(account_data["daytrading_buying_power"]),
                    "cash": convert_to_decimal(account_data["cash"]),
                    "portfolio_value": convert_to_decimal(account_data["portfolio_value"]),
                    "equity": convert_to_decimal(account_data["equity"]),
                    "last_equity": convert_to_decimal(account_data["last_equity"]),
                    "long_market_value": convert_to_decimal(account_data["long_market_value"]),
                    "short_market_value": convert_to_decimal(account_data["short_market_value"]),
                    "multiplier": account_data["multiplier"],
                    "pattern_day_trader": account_data["pattern_day_trader"],
                    "day_trade_count": safe_int(account_data["day_trade_count"]),
                    "daytrade_count": safe_int(account_data["daytrade_count"]),
                    "trading_blocked": account_data["trading_blocked"],
                    "transfers_blocked": account_data["transfers_blocked"],
                    "account_blocked": account_data["account_blocked"],
                    "created_at": account_data["created_at"],
                    "trade_suspended_by_user": account_data["trade_suspended_by_user"],
                    "paper_trading": self.paper_trading
                }
                self.cache_expiry = datetime.utcnow() + timedelta(minutes=5)
                
                return self.account_info_cache
            else:
                raise MarketDataError("Failed to fetch account info", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca account info: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_positions(self) -> List[Position]:
        """Get Alpaca positions"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/positions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                positions_data = response.json()
                positions = []
                
                for pos in positions_data:
                    quantity = convert_to_decimal(pos["qty"])
                    if quantity != 0:
                        position = Position(
                            symbol=pos["symbol"],
                            quantity=quantity,
                            avg_price=convert_to_decimal(pos["avg_entry_price"]),
                            market_value=convert_to_decimal(pos["market_value"])
                        )
                        positions.append(position)
                
                return positions
            else:
                raise MarketDataError("Failed to fetch positions", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca positions: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_balance(self) -> Dict[str, Decimal]:
        """Get Alpaca account balance"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                account_data = response.json()
                return {
                    "cash": convert_to_decimal(account_data["cash"]),
                    "buying_power": convert_to_decimal(account_data["buying_power"]),
                    "regt_buying_power": convert_to_decimal(account_data["regt_buying_power"]),
                    "daytrading_buying_power": convert_to_decimal(account_data["daytrading_buying_power"]),
                    "portfolio_value": convert_to_decimal(account_data["portfolio_value"]),
                    "equity": convert_to_decimal(account_data["equity"]),
                    "long_market_value": convert_to_decimal(account_data["long_market_value"]),
                    "short_market_value": convert_to_decimal(account_data["short_market_value"])
                }
            else:
                raise MarketDataError("Failed to fetch balance", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca balance: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def place_order(self, symbol: str, side: OrderSide, quantity: Decimal, 
                         order_type: OrderType, price: Optional[Decimal] = None) -> Order:
        """Place order with Alpaca"""
        await self.ensure_authenticated()
        
        try:
            # Map our order types to Alpaca format
            alpaca_order_type_map = {
                OrderType.MARKET: "market",
                OrderType.LIMIT: "limit",
                OrderType.STOP: "stop",
                OrderType.STOP_LIMIT: "stop_limit"
            }
            
            alpaca_order_type = alpaca_order_type_map[order_type]
            
            order_data = {
                "symbol": symbol.upper(),
                "side": side,
                "type": alpaca_order_type,
                "time_in_force": "day",
                "qty": str(int(quantity))
            }
            
            # Add price for limit orders
            if price and order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                order_data["limit_price"] = str(float(price))
            
            # Add stop price for stop orders
            if price and order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                order_data["stop_price"] = str(float(price))
            
            response = await self.http_client.post(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                json=order_data
            )
            
            if response.status_code == 201:
                order_response = response.json()
                status_map = {
                    "new": OrderStatus.PENDING,
                    "filled": OrderStatus.FILLED,
                    "partially_filled": OrderStatus.PARTIALLY_FILLED,
                    "canceled": OrderStatus.CANCELLED,
                    "cancelled": OrderStatus.CANCELLED,
                    "rejected": OrderStatus.REJECTED,
                    "pending_new": OrderStatus.PENDING,
                    "accepted": OrderStatus.PENDING
                }
                
                order = Order(
                    order_id=order_response["id"],
                    symbol=order_response["symbol"],
                    side=OrderSide(order_response["side"]),
                    quantity=convert_to_decimal(order_response["qty"]),
                    order_type=OrderType(order_response["type"]),
                    status=status_map.get(order_response["status"], OrderStatus.PENDING),
                    price=convert_to_decimal(order_response.get("limit_price")) if order_response.get("limit_price") else None
                )
                
                order.filled_quantity = convert_to_decimal(order_response.get("filled_qty", 0))
                return order
            else:
                error_data = response.json()
                error_msg = error_data.get("message", "Order placement failed")
                raise OrderError(error_msg, "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error placing Alpaca order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "alpaca")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Alpaca order"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.delete(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Error cancelling Alpaca order: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Order:
        """Get Alpaca order status"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                order_data = response.json()
                status_map = {
                    "new": OrderStatus.PENDING,
                    "filled": OrderStatus.FILLED,
                    "partially_filled": OrderStatus.PARTIALLY_FILLED,
                    "canceled": OrderStatus.CANCELLED,
                    "cancelled": OrderStatus.CANCELLED,
                    "rejected": OrderStatus.REJECTED,
                    "pending_new": OrderStatus.PENDING,
                    "accepted": OrderStatus.PENDING
                }
                
                order = Order(
                    order_id=order_data["id"],
                    symbol=order_data["symbol"],
                    side=OrderSide(order_data["side"]),
                    quantity=convert_to_decimal(order_data["qty"]),
                    order_type=OrderType(order_data["type"]),
                    status=status_map.get(order_data["status"], OrderStatus.PENDING),
                    price=convert_to_decimal(order_data.get("limit_price")) if order_data.get("limit_price") else None
                )
                
                order.filled_quantity = convert_to_decimal(order_data.get("filled_qty", 0))
                return order
            else:
                raise OrderError("Failed to fetch order status", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca order status: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "alpaca")
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get Alpaca market data"""
        await self.ensure_authenticated()
        
        try:
            # Get latest quote
            quote_response = await self.http_client.get(
                f"{self.data_url}/v2/stocks/{symbol.upper()}/quotes/latest",
                headers=self.headers
            )
            
            # Get latest trade for more accurate last price
            trade_response = await self.http_client.get(
                f"{self.data_url}/v2/stocks/{symbol.upper()}/trades/latest",
                headers=self.headers
            )
            
            # Get daily bar for OHLC data
            bar_response = await self.http_client.get(
                f"{self.data_url}/v2/stocks/{symbol.upper()}/bars/latest",
                headers=self.headers
            )
            
            result = {"symbol": symbol.upper()}
            
            # Process quote data
            if quote_response.status_code == 200:
                quote_data = quote_response.json()["quote"]
                result.update({
                    "bid_price": convert_to_decimal(quote_data["bp"]),
                    "ask_price": convert_to_decimal(quote_data["ap"]),
                    "bid_size": safe_int(quote_data["bs"]),
                    "ask_size": safe_int(quote_data["as"]),
                    "quote_timestamp": datetime.fromisoformat(quote_data["t"].replace('Z', '+00:00'))
                })
            
            # Process trade data
            if trade_response.status_code == 200:
                trade_data = trade_response.json()["trade"]
                result["last_price"] = convert_to_decimal(trade_data["p"])
                result["last_size"] = safe_int(trade_data["s"])
                result["trade_timestamp"] = datetime.fromisoformat(trade_data["t"].replace('Z', '+00:00'))
            elif "bid_price" in result and "ask_price" in result:
                # Use mid price if no trade data
                result["last_price"] = (result["bid_price"] + result["ask_price"]) / 2
            
            # Process bar data for OHLC
            if bar_response.status_code == 200:
                bar_data = bar_response.json()["bar"]
                result.update({
                    "open": convert_to_decimal(bar_data["o"]),
                    "high": convert_to_decimal(bar_data["h"]),
                    "low": convert_to_decimal(bar_data["l"]),
                    "close": convert_to_decimal(bar_data["c"]),
                    "volume": safe_int(bar_data["v"]),
                    "vwap": convert_to_decimal(bar_data.get("vw", 0)),
                    "bar_timestamp": datetime.fromisoformat(bar_data["t"].replace('Z', '+00:00'))
                })
                
                # Calculate change if we have close price
                if "last_price" in result and result["close"]:
                    change = result["last_price"] - result["close"]
                    result["change"] = change
                    result["change_percent"] = (change / result["close"] * 100) if result["close"] != 0 else Decimal('0')
            
            result["timestamp"] = datetime.utcnow()
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Alpaca market data: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_historical_data(self, symbol: str, period: str) -> List[Dict[str, Any]]:
        """Get Alpaca historical data"""
        await self.ensure_authenticated()
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            if period == "1d":
                start_date = end_date - timedelta(days=1)
                timeframe = "1Min"
            elif period == "1w":
                start_date = end_date - timedelta(weeks=1)
                timeframe = "15Min"
            elif period == "1m":
                start_date = end_date - timedelta(days=30)
                timeframe = "1Day"
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
                timeframe = "1Day"
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
                timeframe = "1Day"
            else:  # 1y
                start_date = end_date - timedelta(days=365)
                timeframe = "1Day"
            
            params = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "timeframe": timeframe,
                "adjustment": "raw"
            }
            
            response = await self.http_client.get(
                f"{self.data_url}/v2/stocks/{symbol.upper()}/bars",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                response_data = response.json()
                bars_data = response_data.get("bars", [])
                historical_data = []
                
                for bar in bars_data:
                    historical_data.append({
                        "timestamp": datetime.fromisoformat(bar["t"].replace('Z', '+00:00')),
                        "open": convert_to_decimal(bar["o"]),
                        "high": convert_to_decimal(bar["h"]),
                        "low": convert_to_decimal(bar["l"]),
                        "close": convert_to_decimal(bar["c"]),
                        "volume": safe_int(bar["v"]),
                        "vwap": convert_to_decimal(bar.get("vw", 0)),
                        "trade_count": safe_int(bar.get("n", 0))
                    })
                
                return historical_data
            else:
                raise MarketDataError("Failed to fetch historical data", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca historical data: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    # Additional Alpaca-specific methods
    async def get_orders(self) -> List[Order]:
        """Get all orders"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                params={"status": "all", "limit": 500, "nested": True}
            )
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = []
                
                status_map = {
                    "new": OrderStatus.PENDING,
                    "filled": OrderStatus.FILLED,
                    "partially_filled": OrderStatus.PARTIALLY_FILLED,
                    "canceled": OrderStatus.CANCELLED,
                    "cancelled": OrderStatus.CANCELLED,
                    "rejected": OrderStatus.REJECTED,
                    "pending_new": OrderStatus.PENDING,
                    "accepted": OrderStatus.PENDING
                }
                
                for order_data in orders_data:
                    order = Order(
                        order_id=order_data["id"],
                        symbol=order_data["symbol"],
                        side=OrderSide(order_data["side"]),
                        quantity=convert_to_decimal(order_data["qty"]),
                        order_type=OrderType(order_data["type"]),
                        status=status_map.get(order_data["status"], OrderStatus.PENDING),
                        price=convert_to_decimal(order_data.get("limit_price")) if order_data.get("limit_price") else None
                    )
                    
                    order.filled_quantity = convert_to_decimal(order_data.get("filled_qty", 0))
                    order.created_at = datetime.fromisoformat(order_data["created_at"].replace('Z', '+00:00'))
                    order.updated_at = datetime.fromisoformat(order_data["updated_at"].replace('Z', '+00:00'))
                    orders.append(order)
                
                return orders
            else:
                raise MarketDataError("Failed to fetch orders", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca orders: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify an existing order"""
        await self.ensure_authenticated()
        
        try:
            # Filter valid modification parameters
            valid_params = ["qty", "time_in_force", "limit_price", "stop_price", "client_order_id"]
            order_data = {k: str(v) for k, v in kwargs.items() if k in valid_params}
            
            if not order_data:
                raise OrderError("No valid parameters to modify", "alpaca")
            
            response = await self.http_client.patch(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers,
                json=order_data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error modifying Alpaca order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            return False
    
    async def close_position(self, symbol: str, percentage: Optional[int] = None) -> bool:
        """Close a position (Alpaca specific feature)"""
        await self.ensure_authenticated()
        
        try:
            url = f"{self.base_url}/v2/positions/{symbol.upper()}"
            params = {}
            
            if percentage is not None:
                params["percentage"] = str(percentage)
            
            response = await self.http_client.delete(
                url, 
                headers=self.headers, 
                params=params
            )
            
            return response.status_code in [200, 207]  # 207 = Multi-status response
            
        except Exception as e:
            logger.error(f"Error closing Alpaca position: {e}")
            return False
    
    async def close_all_positions(self, cancel_orders: bool = True) -> Dict[str, Any]:
        """Close all positions"""
        await self.ensure_authenticated()
        
        try:
            params = {}
            if cancel_orders:
                params["cancel_orders"] = "true"
            
            response = await self.http_client.delete(
                f"{self.base_url}/v2/positions",
                headers=self.headers,
                params=params
            )
            
            if response.status_code in [200, 207]:
                return response.json()
            else:
                raise OrderError("Failed to close all positions", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error closing all Alpaca positions: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "alpaca")
    
    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1D") -> Dict[str, Any]:
        """Get portfolio history"""
        await self.ensure_authenticated()
        
        try:
            params = {
                "period": period,
                "timeframe": timeframe
            }
            
            response = await self.http_client.get(
                f"{self.base_url}/v2/account/portfolio/history",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                history_data = response.json()
                
                # Process the data
                result = {
                    "equity": history_data.get("equity", []),
                    "profit_loss": history_data.get("profit_loss", []),
                    "profit_loss_pct": history_data.get("profit_loss_pct", []),
                    "base_value": safe_float(history_data.get("base_value", 0)),
                    "timeframe": history_data.get("timeframe"),
                    "timestamp": [
                        datetime.fromtimestamp(ts) for ts in history_data.get("timestamp", [])
                    ]
                }
                
                return result
            else:
                raise MarketDataError("Failed to fetch portfolio history", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca portfolio history: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_watchlists(self) -> List[Dict[str, Any]]:
        """Get user's watchlists"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/watchlists",
                headers=self.headers
            )
            
            if response.status_code == 200:
                watchlists_data = response.json()
                watchlists = []
                
                for watchlist in watchlists_data:
                    watchlists.append({
                        "id": watchlist["id"],
                        "name": watchlist["name"],
                        "account_id": watchlist["account_id"],
                        "created_at": datetime.fromisoformat(watchlist["created_at"].replace('Z', '+00:00')),
                        "updated_at": datetime.fromisoformat(watchlist["updated_at"].replace('Z', '+00:00')),
                        "assets": [
                            {
                                "id": asset["id"],
                                "class": asset["class"],
                                "exchange": asset["exchange"],
                                "symbol": asset["symbol"],
                                "name": asset.get("name"),
                                "status": asset["status"],
                                "tradable": asset["tradable"]
                            }
                            for asset in watchlist.get("assets", [])
                        ]
                    })
                
                return watchlists
            else:
                raise MarketDataError("Failed to fetch watchlists", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca watchlists: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def create_watchlist(self, name: str, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new watchlist"""
        await self.ensure_authenticated()
        
        try:
            watchlist_data = {"name": name}
            if symbols:
                watchlist_data["symbols"] = [s.upper() for s in symbols]
            
            response = await self.http_client.post(
                f"{self.base_url}/v2/watchlists",
                headers=self.headers,
                json=watchlist_data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                raise MarketDataError("Failed to create watchlist", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error creating Alpaca watchlist: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_calendar(self, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get market calendar"""
        await self.ensure_authenticated()
        
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            
            response = await self.http_client.get(
                f"{self.base_url}/v2/calendar",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                calendar_data = response.json()
                return [
                    {
                        "date": cal["date"],
                        "open": cal["open"],
                        "close": cal["close"],
                        "session_open": datetime.fromisoformat(f"{cal['date']}T{cal['open']}:00-05:00"),
                        "session_close": datetime.fromisoformat(f"{cal['date']}T{cal['close']}:00-05:00")
                    }
                    for cal in calendar_data
                ]
            else:
                raise MarketDataError("Failed to fetch calendar", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca calendar: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_clock(self) -> Dict[str, Any]:
        """Get market clock"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v2/clock",
                headers=self.headers
            )
            
            if response.status_code == 200:
                clock_data = response.json()
                return {
                    "timestamp": datetime.fromisoformat(clock_data["timestamp"].replace('Z', '+00:00')),
                    "is_open": clock_data["is_open"],
                    "next_open": datetime.fromisoformat(clock_data["next_open"].replace('Z', '+00:00')),
                    "next_close": datetime.fromisoformat(clock_data["next_close"].replace('Z', '+00:00'))
                }
            else:
                raise MarketDataError("Failed to fetch market clock", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca market clock: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_assets(self, status: str = "active", asset_class: str = "us_equity") -> List[Dict[str, Any]]:
        """Get tradeable assets"""
        await self.ensure_authenticated()
        
        try:
            params = {
                "status": status,
                "asset_class": asset_class
            }
            
            response = await self.http_client.get(
                f"{self.base_url}/v2/assets",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                assets_data = response.json()
                return [
                    {
                        "id": asset["id"],
                        "class": asset["class"],
                        "exchange": asset["exchange"],
                        "symbol": asset["symbol"],
                        "name": asset.get("name"),
                        "status": asset["status"],
                        "tradable": asset["tradable"],
                        "marginable": asset["marginable"],
                        "shortable": asset["shortable"],
                        "easy_to_borrow": asset["easy_to_borrow"],
                        "fractionable": asset["fractionable"]
                    }
                    for asset in assets_data
                ]
            else:
                raise MarketDataError("Failed to fetch assets", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca assets: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    async def get_bars_multi(self, symbols: List[str], timeframe: str = "1Day", 
                           start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get bars for multiple symbols"""
        await self.ensure_authenticated()
        
        try:
            params = {
                "symbols": ",".join([s.upper() for s in symbols]),
                "timeframe": timeframe
            }
            
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            
            response = await self.http_client.get(
                f"{self.data_url}/v2/stocks/bars",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                bars_data = response.json()["bars"]
                result = {}
                
                for symbol, bars in bars_data.items():
                    result[symbol] = [
                        {
                            "timestamp": datetime.fromisoformat(bar["t"].replace('Z', '+00:00')),
                            "open": convert_to_decimal(bar["o"]),
                            "high": convert_to_decimal(bar["h"]),
                            "low": convert_to_decimal(bar["l"]),
                            "close": convert_to_decimal(bar["c"]),
                            "volume": safe_int(bar["v"]),
                            "vwap": convert_to_decimal(bar.get("vw", 0)),
                            "trade_count": safe_int(bar.get("n", 0))
                        }
                        for bar in bars
                    ]
                
                return result
            else:
                raise MarketDataError("Failed to fetch multi-symbol bars", "alpaca", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Alpaca multi-symbol bars: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "alpaca")
    
    def get_supported_order_types(self) -> List[str]:
        """Get list of supported order types"""
        return ["market", "limit", "stop", "stop_limit", "trailing_stop"]
    
    def get_supported_time_in_force(self) -> List[str]:
        """Get list of supported time in force values"""
        return ["day", "gtc", "opg", "cls", "ioc", "fok"]
    
    def is_market_open(self) -> bool:
        """Check if market is currently open (simple check)"""
        # This is a simplified check - for accurate data use get_clock()
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Market hours: 9:30 AM - 4:00 PM EST (simplified)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def get_account_type(self) -> str:
        """Get account type"""
        return "paper" if self.paper_trading else "live"


__all__ = ["AlpacaBroker"]