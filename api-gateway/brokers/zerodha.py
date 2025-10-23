"""
Zerodha Kite Connect broker integration
"""
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Dict, List, Optional, Any

from .base import (
    BaseBroker, Position, Order, OrderType, OrderSide, OrderStatus,
    AuthenticationError, OrderError, MarketDataError, convert_to_decimal, safe_float, safe_int
)
import logging

logger = logging.getLogger(__name__)


class ZerodhaBroker(BaseBroker):
    """Zerodha Kite Connect integration"""

    def __init__(self, api_key: str, access_token: str, paper_trading: bool = True, base_url: str = None):
        super().__init__(api_key, access_token, paper_trading)
        self.access_token = access_token
        # Use provided base_url or default
        self.base_url = base_url or "https://api.kite.trade"
        self.headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {api_key}:{access_token}"
        }
        self.instrument_cache = {}
        self.exchange_map = {
            "NSE": "NSE",
            "BSE": "BSE",
            "MCX": "MCX",
            "NCDEX": "NCDEX"
        }
        self.trading_mode = "paper" if paper_trading else "live"
        logger.info(f"Initialized Zerodha broker in {self.trading_mode} mode using {self.base_url}")

        # Note: Zerodha doesn't have separate paper/live URLs like Alpaca
        # Paper trading simulation would be handled at the application level
    
    async def authenticate(self) -> bool:
        """Authenticate with Zerodha"""
        # Skip authentication for paper trading mode
        if self.paper_trading:
            self.authenticated = True
            self.last_auth_check = datetime.utcnow()
            logger.info("Zerodha paper trading mode - skipping real authentication")
            return True

        try:
            response = await self.http_client.get(
                f"{self.base_url}/user/profile",
                headers=self.headers
            )

            if response.status_code == 200:
                self.authenticated = True
                self.last_auth_check = datetime.utcnow()
                return True
            else:
                raise AuthenticationError("Zerodha authentication failed", "zerodha", str(response.status_code))

        except Exception as e:
            logger.error(f"Zerodha authentication failed: {e}")
            self.authenticated = False
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(str(e), "zerodha")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Zerodha account information"""
        await self.ensure_authenticated()
        
        try:
            # Get user profile
            profile_response = await self.http_client.get(
                f"{self.base_url}/user/profile",
                headers=self.headers
            )
            
            # Get margins
            margins_response = await self.http_client.get(
                f"{self.base_url}/user/margins",
                headers=self.headers
            )
            
            if profile_response.status_code == 200 and margins_response.status_code == 200:
                profile_data = profile_response.json()["data"]
                margins_data = margins_response.json()["data"]
                
                return {
                    "broker": "zerodha",
                    "user_id": profile_data["user_id"],
                    "user_name": profile_data["user_name"],
                    "user_shortname": profile_data["user_shortname"],
                    "email": profile_data["email"],
                    "user_type": profile_data["user_type"],
                    "broker": profile_data["broker"],
                    "exchanges": profile_data["exchanges"],
                    "products": profile_data["products"],
                    "order_types": profile_data["order_types"],
                    "equity_balance": convert_to_decimal(margins_data["equity"]["available"]["live_balance"]),
                    "equity_used": convert_to_decimal(margins_data["equity"]["utilised"]["live_balance"]),
                    "commodity_balance": convert_to_decimal(margins_data["commodity"]["available"]["live_balance"]),
                    "commodity_used": convert_to_decimal(margins_data["commodity"]["utilised"]["live_balance"]),
                    "paper_trading": self.paper_trading
                }
            else:
                raise MarketDataError("Failed to fetch account info", "zerodha")
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha account info: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_positions(self) -> List[Position]:
        """Get Zerodha positions"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/portfolio/positions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                positions_data = response.json()["data"]["net"]
                positions = []
                
                for pos in positions_data:
                    quantity = convert_to_decimal(pos["quantity"])
                    if quantity != 0:
                        position = Position(
                            symbol=pos["tradingsymbol"],
                            quantity=quantity,
                            avg_price=convert_to_decimal(pos["average_price"]),
                            market_value=convert_to_decimal(pos["value"])
                        )
                        positions.append(position)
                
                return positions
            else:
                raise MarketDataError("Failed to fetch positions", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha positions: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_balance(self) -> Dict[str, Decimal]:
        """Get Zerodha account balance"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/user/margins",
                headers=self.headers
            )
            
            if response.status_code == 200:
                margins_data = response.json()["data"]
                return {
                    "equity_cash": convert_to_decimal(margins_data["equity"]["available"]["cash"]),
                    "equity_margin": convert_to_decimal(margins_data["equity"]["available"]["live_balance"]),
                    "equity_used": convert_to_decimal(margins_data["equity"]["utilised"]["live_balance"]),
                    "commodity_cash": convert_to_decimal(margins_data["commodity"]["available"]["cash"]),
                    "commodity_margin": convert_to_decimal(margins_data["commodity"]["available"]["live_balance"]),
                    "commodity_used": convert_to_decimal(margins_data["commodity"]["utilised"]["live_balance"])
                }
            else:
                raise MarketDataError("Failed to fetch balance", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha balance: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def place_order(self, symbol: str, side: OrderSide, quantity: Decimal,
                         order_type: OrderType, price: Optional[Decimal] = None,
                         validity: str = "DAY", product: str = "CNC") -> Order:
        """Place order with Zerodha"""
        await self.ensure_authenticated()

        try:
            # Map our order types to Zerodha format
            zerodha_order_type_map = {
                OrderType.MARKET: "MARKET",
                OrderType.LIMIT: "LIMIT",
                OrderType.STOP: "SL",
                OrderType.STOP_LIMIT: "SL-M"
            }

            zerodha_order_type = zerodha_order_type_map[order_type]

            # Determine exchange (default to NSE for stocks)
            exchange = self._determine_exchange(symbol)

            order_data = {
                "tradingsymbol": symbol.upper(),
                "exchange": exchange,
                "transaction_type": side.value.upper(),
                "order_type": zerodha_order_type,
                "quantity": str(int(quantity)),
                "product": product,  # CNC, MIS, NRML, CO, BO
                "validity": validity  # DAY, IOC
            }

            # Add price for limit orders
            if price and order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                order_data["price"] = str(float(price))

            # Add trigger price for stop orders
            if price and order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                order_data["trigger_price"] = str(float(price))

            if self.paper_trading:
                # Mock response for paper trading
                order_id = f"zerodha_mock_{int(datetime.utcnow().timestamp())}"
                return Order(
                    order_id=order_id,
                    symbol=symbol.upper(),
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    status=OrderStatus.FILLED,
                    price=price
                )

            response = await self.http_client.post(
                f"{self.base_url}/orders/regular",
                headers=self.headers,
                data=order_data
            )

            if response.status_code == 200:
                response_data = response.json()
                order_id = response_data["data"]["order_id"]

                return Order(
                    order_id=order_id,
                    symbol=symbol.upper(),
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    status=OrderStatus.PENDING,
                    price=price
                )
            else:
                error_msg = response.json().get("message", "Order placement failed")
                raise OrderError(error_msg, "zerodha", str(response.status_code))

        except Exception as e:
            logger.error(f"Error placing Zerodha order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "zerodha")

    async def place_gtt_order(self, symbol: str, side: OrderSide, quantity: Decimal,
                             trigger_price: Decimal, limit_price: Optional[Decimal] = None,
                             trigger_type: str = "single", product: str = "CNC") -> Dict[str, Any]:
        """Place GTT (Good Till Triggered) order with Zerodha

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            trigger_price: Price at which order should trigger
            limit_price: Limit price for triggered order (None for market order)
            trigger_type: 'single' or 'two-leg' (for OCO orders)
            product: Product type (CNC, MIS, NRML)
        """
        await self.ensure_authenticated()

        try:
            exchange = self._determine_exchange(symbol)

            # Build GTT order data
            gtt_data = {
                "tradingsymbol": symbol.upper(),
                "exchange": exchange,
                "trigger_type": trigger_type,
                "last_price": str(float(trigger_price)),
                "orders": [
                    {
                        "transaction_type": side.value.upper(),
                        "quantity": int(quantity),
                        "product": product,
                        "order_type": "LIMIT" if limit_price else "MARKET",
                        "price": str(float(limit_price)) if limit_price else "0"
                    }
                ]
            }

            if self.paper_trading:
                # Mock GTT response for paper trading
                gtt_id = f"zerodha_gtt_mock_{int(datetime.utcnow().timestamp())}"
                return {
                    "trigger_id": gtt_id,
                    "symbol": symbol.upper(),
                    "trigger_price": trigger_price,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
                }

            response = await self.http_client.post(
                f"{self.base_url}/gtt/triggers",
                headers=self.headers,
                json=gtt_data
            )

            if response.status_code == 200:
                response_data = response.json()
                trigger_id = response_data["data"]["trigger_id"]

                return {
                    "trigger_id": trigger_id,
                    "symbol": symbol.upper(),
                    "trigger_price": trigger_price,
                    "limit_price": limit_price,
                    "side": side,
                    "quantity": quantity,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
                }
            else:
                error_msg = response.json().get("message", "GTT order placement failed")
                raise OrderError(error_msg, "zerodha", str(response.status_code))

        except Exception as e:
            logger.error(f"Error placing Zerodha GTT order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "zerodha")

    async def place_basket_order(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Place basket order with multiple stocks (up to 20 orders)

        Args:
            orders: List of order dictionaries with symbol, side, quantity, order_type, price
        """
        await self.ensure_authenticated()

        if len(orders) > 20:
            raise OrderError("Maximum 20 orders allowed in basket", "zerodha")

        try:
            basket_orders = []
            for order in orders:
                exchange = self._determine_exchange(order["symbol"])

                order_data = {
                    "tradingsymbol": order["symbol"].upper(),
                    "exchange": exchange,
                    "transaction_type": order["side"].upper(),
                    "order_type": order.get("order_type", "MARKET"),
                    "quantity": str(int(order["quantity"])),
                    "product": order.get("product", "CNC"),
                    "validity": order.get("validity", "DAY")
                }

                if order.get("price"):
                    order_data["price"] = str(float(order["price"]))

                if order.get("trigger_price"):
                    order_data["trigger_price"] = str(float(order["trigger_price"]))

                basket_orders.append(order_data)

            if self.paper_trading:
                # Mock basket response for paper trading
                return {
                    "basket_id": f"zerodha_basket_mock_{int(datetime.utcnow().timestamp())}",
                    "orders_placed": len(orders),
                    "status": "completed",
                    "success_count": len(orders),
                    "failure_count": 0
                }

            # Place all orders in the basket
            results = []
            success_count = 0
            failure_count = 0

            for order_data in basket_orders:
                try:
                    response = await self.http_client.post(
                        f"{self.base_url}/orders/regular",
                        headers=self.headers,
                        data=order_data
                    )

                    if response.status_code == 200:
                        results.append({"status": "success", "order_id": response.json()["data"]["order_id"]})
                        success_count += 1
                    else:
                        results.append({"status": "failed", "error": response.json().get("message")})
                        failure_count += 1

                except Exception as e:
                    results.append({"status": "failed", "error": str(e)})
                    failure_count += 1

            return {
                "basket_id": f"zerodha_basket_{int(datetime.utcnow().timestamp())}",
                "orders_placed": len(orders),
                "success_count": success_count,
                "failure_count": failure_count,
                "results": results,
                "status": "completed" if failure_count == 0 else "partial"
            }

        except Exception as e:
            logger.error(f"Error placing Zerodha basket order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "zerodha")

    async def get_gtt_orders(self) -> List[Dict[str, Any]]:
        """Get all active GTT orders"""
        await self.ensure_authenticated()

        try:
            if self.paper_trading:
                # Return mock GTT orders for paper trading
                return [
                    {
                        "trigger_id": "mock_gtt_1",
                        "symbol": "RELIANCE",
                        "trigger_price": 2500.0,
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(days=300)).isoformat()
                    }
                ]

            response = await self.http_client.get(
                f"{self.base_url}/gtt/triggers",
                headers=self.headers
            )

            if response.status_code == 200:
                gtt_data = response.json()["data"]
                return [
                    {
                        "trigger_id": gtt["id"],
                        "symbol": gtt["condition"]["tradingsymbol"],
                        "exchange": gtt["condition"]["exchange"],
                        "trigger_price": float(gtt["condition"]["trigger_values"][0]),
                        "trigger_type": gtt["type"],
                        "status": gtt["status"],
                        "created_at": gtt["created_at"],
                        "expires_at": gtt["expires_at"],
                        "orders": gtt["orders"]
                    }
                    for gtt in gtt_data
                ]
            else:
                raise MarketDataError("Failed to fetch GTT orders", "zerodha", str(response.status_code))

        except Exception as e:
            logger.error(f"Error fetching Zerodha GTT orders: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")

    async def modify_gtt_order(self, trigger_id: str, **kwargs) -> bool:
        """Modify an existing GTT order"""
        await self.ensure_authenticated()

        try:
            if self.paper_trading:
                return True  # Mock success for paper trading

            # Filter valid modification parameters
            valid_params = ["quantity", "price", "trigger_price", "order_type"]
            gtt_data = {k: v for k, v in kwargs.items() if k in valid_params}

            if not gtt_data:
                raise OrderError("No valid parameters to modify", "zerodha")

            response = await self.http_client.put(
                f"{self.base_url}/gtt/triggers/{trigger_id}",
                headers=self.headers,
                json=gtt_data
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error modifying Zerodha GTT order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            return False

    async def cancel_gtt_order(self, trigger_id: str) -> bool:
        """Cancel a GTT order"""
        await self.ensure_authenticated()

        try:
            if self.paper_trading:
                return True  # Mock success for paper trading

            response = await self.http_client.delete(
                f"{self.base_url}/gtt/triggers/{trigger_id}",
                headers=self.headers
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error cancelling Zerodha GTT order: {e}")
            return False

    async def place_oco_order(self, symbol: str, side: OrderSide, quantity: Decimal,
                             target_price: Decimal, stop_loss_price: Decimal,
                             product: str = "CNC") -> Dict[str, Any]:
        """Place One-Cancels-Other (OCO) order using GTT two-leg feature

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            target_price: Target profit price
            stop_loss_price: Stop loss price
            product: Product type (CNC, MIS, NRML)
        """
        await self.ensure_authenticated()

        try:
            exchange = self._determine_exchange(symbol)

            # Create two-leg GTT order (OCO)
            gtt_data = {
                "tradingsymbol": symbol.upper(),
                "exchange": exchange,
                "trigger_type": "two-leg",
                "last_price": str(float(target_price if side == OrderSide.SELL else stop_loss_price)),
                "orders": [
                    {
                        "transaction_type": side.value.upper(),
                        "quantity": int(quantity),
                        "product": product,
                        "order_type": "LIMIT",
                        "price": str(float(target_price))
                    },
                    {
                        "transaction_type": side.value.upper(),
                        "quantity": int(quantity),
                        "product": product,
                        "order_type": "SL-M",
                        "price": str(float(stop_loss_price))
                    }
                ]
            }

            if self.paper_trading:
                # Mock OCO response for paper trading
                oco_id = f"zerodha_oco_mock_{int(datetime.utcnow().timestamp())}"
                return {
                    "trigger_id": oco_id,
                    "symbol": symbol.upper(),
                    "target_price": target_price,
                    "stop_loss_price": stop_loss_price,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
                }

            response = await self.http_client.post(
                f"{self.base_url}/gtt/triggers",
                headers=self.headers,
                json=gtt_data
            )

            if response.status_code == 200:
                response_data = response.json()
                trigger_id = response_data["data"]["trigger_id"]

                return {
                    "trigger_id": trigger_id,
                    "symbol": symbol.upper(),
                    "target_price": target_price,
                    "stop_loss_price": stop_loss_price,
                    "side": side,
                    "quantity": quantity,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
                }
            else:
                error_msg = response.json().get("message", "OCO order placement failed")
                raise OrderError(error_msg, "zerodha", str(response.status_code))

        except Exception as e:
            logger.error(f"Error placing Zerodha OCO order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "zerodha")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Zerodha order"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                return True  # Mock success for paper trading
            
            response = await self.http_client.delete(
                f"{self.base_url}/orders/regular/{order_id}",
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error cancelling Zerodha order: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Order:
        """Get Zerodha order status"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                # Return mock filled order for paper trading
                return Order(
                    order_id=order_id,
                    symbol="MOCK",
                    side=OrderSide.BUY,
                    quantity=Decimal('1'),
                    order_type=OrderType.MARKET,
                    status=OrderStatus.FILLED
                )
            
            # Get order history for the day
            response = await self.http_client.get(
                f"{self.base_url}/orders",
                headers=self.headers
            )
            
            if response.status_code == 200:
                orders = response.json()["data"]
                
                for order_data in orders:
                    if order_data["order_id"] == order_id:
                        status_map = {
                            "COMPLETE": OrderStatus.FILLED,
                            "CANCELLED": OrderStatus.CANCELLED,
                            "REJECTED": OrderStatus.REJECTED,
                            "OPEN": OrderStatus.PENDING,
                            "TRIGGER PENDING": OrderStatus.PENDING
                        }
                        
                        order_type_map = {
                            "MARKET": OrderType.MARKET,
                            "LIMIT": OrderType.LIMIT,
                            "SL": OrderType.STOP,
                            "SL-M": OrderType.STOP_LIMIT
                        }
                        
                        order = Order(
                            order_id=order_data["order_id"],
                            symbol=order_data["tradingsymbol"],
                            side=OrderSide(order_data["transaction_type"].lower()),
                            quantity=convert_to_decimal(order_data["quantity"]),
                            order_type=order_type_map.get(order_data["order_type"], OrderType.MARKET),
                            status=status_map.get(order_data["status"], OrderStatus.PENDING),
                            price=convert_to_decimal(order_data.get("price"))
                        )
                        
                        order.filled_quantity = convert_to_decimal(order_data.get("filled_quantity", 0))
                        return order
                
                raise OrderError("Order not found", "zerodha")
            else:
                raise OrderError("Failed to fetch order status", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha order status: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            raise OrderError(str(e), "zerodha")
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get Zerodha market data"""
        await self.ensure_authenticated()
        
        try:
            # Determine exchange and format instrument key
            exchange = self._determine_exchange(symbol)
            instrument_key = f"{exchange}:{symbol.upper()}"
            
            response = await self.http_client.get(
                f"{self.base_url}/quote",
                headers=self.headers,
                params={"i": instrument_key}
            )
            
            if response.status_code == 200:
                quote_data = response.json()["data"][instrument_key]
                
                return {
                    "symbol": symbol.upper(),
                    "last_price": convert_to_decimal(quote_data["last_price"]),
                    "open": convert_to_decimal(quote_data["ohlc"]["open"]),
                    "high": convert_to_decimal(quote_data["ohlc"]["high"]),
                    "low": convert_to_decimal(quote_data["ohlc"]["low"]),
                    "close": convert_to_decimal(quote_data["ohlc"]["close"]),
                    "change": convert_to_decimal(quote_data["net_change"]),
                    "change_percent": safe_float(quote_data["net_change"]) / safe_float(quote_data["last_price"]) * 100,
                    "volume": safe_int(quote_data["volume"]),
                    "average_price": convert_to_decimal(quote_data["average_price"]),
                    "oi": safe_int(quote_data.get("oi", 0)),
                    "timestamp": datetime.utcnow()
                }
            else:
                raise MarketDataError("Failed to fetch market data", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha market data: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_historical_data(self, symbol: str, period: str) -> List[Dict[str, Any]]:
        """Get Zerodha historical data"""
        await self.ensure_authenticated()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            if period == "1d":
                start_date = end_date - timedelta(days=1)
                interval = "minute"
            elif period == "1w":
                start_date = end_date - timedelta(weeks=1)
                interval = "15minute"
            elif period == "1m":
                start_date = end_date - timedelta(days=30)
                interval = "day"
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
                interval = "day"
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
                interval = "day"
            else:  # 1y
                start_date = end_date - timedelta(days=365)
                interval = "day"
            
            if self.paper_trading:
                # Return mock historical data
                days = (end_date - start_date).days
                return [
                    {
                        "timestamp": end_date - timedelta(days=i),
                        "open": Decimal('100') + Decimal(str(i)),
                        "high": Decimal('105') + Decimal(str(i)),
                        "low": Decimal('95') + Decimal(str(i)),
                        "close": Decimal('102') + Decimal(str(i)),
                        "volume": 1000 * (i + 1)
                    }
                    for i in range(min(days, 100))
                ]
            
            # For actual implementation, you need instrument tokens
            # This would require mapping symbols to instrument tokens first
            logger.warning("Historical data requires instrument token mapping - returning mock data")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Zerodha historical data: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    # Additional Zerodha-specific methods
    async def get_orders(self) -> List[Order]:
        """Get all orders for the day"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                # Return mock orders for paper trading
                return [
                    Order(
                        order_id="mock_order_1",
                        symbol="RELIANCE",
                        side=OrderSide.BUY,
                        quantity=Decimal('10'),
                        order_type=OrderType.MARKET,
                        status=OrderStatus.FILLED
                    )
                ]
            
            response = await self.http_client.get(
                f"{self.base_url}/orders",
                headers=self.headers
            )
            
            if response.status_code == 200:
                orders_data = response.json()["data"]
                orders = []
                
                status_map = {
                    "COMPLETE": OrderStatus.FILLED,
                    "CANCELLED": OrderStatus.CANCELLED,
                    "REJECTED": OrderStatus.REJECTED,
                    "OPEN": OrderStatus.PENDING,
                    "TRIGGER PENDING": OrderStatus.PENDING
                }
                
                order_type_map = {
                    "MARKET": OrderType.MARKET,
                    "LIMIT": OrderType.LIMIT,
                    "SL": OrderType.STOP,
                    "SL-M": OrderType.STOP_LIMIT
                }
                
                for order_data in orders_data:
                    order = Order(
                        order_id=order_data["order_id"],
                        symbol=order_data["tradingsymbol"],
                        side=OrderSide(order_data["transaction_type"].lower()),
                        quantity=convert_to_decimal(order_data["quantity"]),
                        order_type=order_type_map.get(order_data["order_type"], OrderType.MARKET),
                        status=status_map.get(order_data["status"], OrderStatus.PENDING),
                        price=convert_to_decimal(order_data.get("price"))
                    )
                    
                    order.filled_quantity = convert_to_decimal(order_data.get("filled_quantity", 0))
                    orders.append(order)
                
                return orders
            else:
                raise MarketDataError("Failed to fetch orders", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha orders: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_holdings(self) -> List[Dict[str, Any]]:
        """Get long-term holdings"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/portfolio/holdings",
                headers=self.headers
            )
            
            if response.status_code == 200:
                holdings_data = response.json()["data"]
                holdings = []
                
                for holding in holdings_data:
                    quantity = safe_float(holding["quantity"])
                    if quantity > 0:
                        holdings.append({
                            "tradingsymbol": holding["tradingsymbol"],
                            "exchange": holding["exchange"],
                            "isin": holding["isin"],
                            "quantity": quantity,
                            "t1_quantity": safe_float(holding["t1_quantity"]),
                            "average_price": safe_float(holding["average_price"]),
                            "last_price": safe_float(holding["last_price"]),
                            "pnl": safe_float(holding["pnl"]),
                            "product": holding["product"],
                            "collateral_quantity": safe_float(holding["collateral_quantity"]),
                            "collateral_type": holding.get("collateral_type")
                        })
                
                return holdings
            else:
                raise MarketDataError("Failed to fetch holdings", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha holdings: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify an existing order"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                return True  # Mock success for paper trading
            
            # Filter valid modification parameters
            valid_params = ["quantity", "price", "order_type", "validity", "disclosed_quantity", "trigger_price"]
            order_data = {k: str(v) for k, v in kwargs.items() if k in valid_params}
            
            if not order_data:
                raise OrderError("No valid parameters to modify", "zerodha")
            
            response = await self.http_client.put(
                f"{self.base_url}/orders/regular/{order_id}",
                headers=self.headers,
                data=order_data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error modifying Zerodha order: {e}")
            if isinstance(e, (AuthenticationError, OrderError)):
                raise
            return False
    
    async def get_trades(self) -> List[Dict[str, Any]]:
        """Get executed trades for the day"""
        await self.ensure_authenticated()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/trades",
                headers=self.headers
            )
            
            if response.status_code == 200:
                trades_data = response.json()["data"]
                return [
                    {
                        "trade_id": trade["trade_id"],
                        "order_id": trade["order_id"],
                        "exchange_order_id": trade.get("exchange_order_id"),
                        "tradingsymbol": trade["tradingsymbol"],
                        "exchange": trade["exchange"],
                        "instrument_token": trade.get("instrument_token"),
                        "transaction_type": trade["transaction_type"],
                        "product": trade["product"],
                        "quantity": safe_int(trade["quantity"]),
                        "price": safe_float(trade["price"]),
                        "order_timestamp": trade.get("order_timestamp"),
                        "exchange_timestamp": trade.get("exchange_timestamp"),
                        "fill_timestamp": trade.get("fill_timestamp")
                    }
                    for trade in trades_data
                ]
            else:
                raise MarketDataError("Failed to fetch trades", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha trades: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_instruments(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of tradeable instruments"""
        try:
            url = f"{self.base_url}/instruments"
            if exchange:
                url += f"/{exchange}"
            
            response = await self.http_client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                instruments_csv = response.text
                instruments = []
                reader = csv.DictReader(StringIO(instruments_csv))
                
                for row in reader:
                    instruments.append({
                        "instrument_token": row["instrument_token"],
                        "exchange_token": row["exchange_token"],
                        "tradingsymbol": row["tradingsymbol"],
                        "name": row.get("name", ""),
                        "last_price": safe_float(row.get("last_price")),
                        "expiry": row.get("expiry", ""),
                        "strike": safe_float(row.get("strike")),
                        "tick_size": safe_float(row.get("tick_size")),
                        "lot_size": safe_int(row.get("lot_size")),
                        "instrument_type": row.get("instrument_type", ""),
                        "segment": row.get("segment", ""),
                        "exchange": row.get("exchange", "")
                    })
                
                # Cache instruments for later use
                self.instrument_cache[exchange or "ALL"] = instruments
                return instruments
            else:
                raise MarketDataError("Failed to fetch instruments", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha instruments: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    def _determine_exchange(self, symbol: str) -> str:
        """Determine exchange for a symbol (simple heuristic)"""
        symbol = symbol.upper()
        
        # Common NSE stocks
        nse_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT']
        if symbol in nse_symbols:
            return "NSE"
        
        # If it contains specific suffixes, determine exchange
        if symbol.endswith("-EQ"):
            return "NSE"
        elif symbol.endswith(".BO"):
            return "BSE"
        elif "FUT" in symbol or "CE" in symbol or "PE" in symbol:
            return "NFO"  # Derivatives
        
        # Default to NSE for equity
        return "NSE"
    
    def _get_instrument_token(self, symbol: str, exchange: str) -> Optional[str]:
        """Get instrument token for a symbol"""
        # This would require searching through the instruments cache
        # For now, return None - in production you'd implement proper mapping
        instruments = self.instrument_cache.get(exchange, [])
        
        for instrument in instruments:
            if instrument["tradingsymbol"].upper() == symbol.upper():
                return instrument["instrument_token"]
        
        return None
    
    async def get_ltp(self, instruments: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get Last Traded Price for multiple instruments"""
        await self.ensure_authenticated()
        
        try:
            # Format instruments as exchange:symbol
            formatted_instruments = []
            for instrument in instruments:
                if ":" not in instrument:
                    exchange = self._determine_exchange(instrument)
                    formatted_instruments.append(f"{exchange}:{instrument.upper()}")
                else:
                    formatted_instruments.append(instrument.upper())
            
            response = await self.http_client.get(
                f"{self.base_url}/quote/ltp",
                headers=self.headers,
                params={"i": formatted_instruments}
            )
            
            if response.status_code == 200:
                ltp_data = response.json()["data"]
                result = {}
                
                for instrument_key, data in ltp_data.items():
                    result[instrument_key] = {
                        "last_price": convert_to_decimal(data["last_price"]),
                        "timestamp": datetime.utcnow()
                    }
                
                return result
            else:
                raise MarketDataError("Failed to fetch LTP data", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha LTP: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def get_ohlc(self, instruments: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get OHLC data for multiple instruments"""
        await self.ensure_authenticated()
        
        try:
            # Format instruments as exchange:symbol
            formatted_instruments = []
            for instrument in instruments:
                if ":" not in instrument:
                    exchange = self._determine_exchange(instrument)
                    formatted_instruments.append(f"{exchange}:{instrument.upper()}")
                else:
                    formatted_instruments.append(instrument.upper())
            
            response = await self.http_client.get(
                f"{self.base_url}/quote/ohlc",
                headers=self.headers,
                params={"i": formatted_instruments}
            )
            
            if response.status_code == 200:
                ohlc_data = response.json()["data"]
                result = {}
                
                for instrument_key, data in ohlc_data.items():
                    ohlc = data["ohlc"]
                    result[instrument_key] = {
                        "open": convert_to_decimal(ohlc["open"]),
                        "high": convert_to_decimal(ohlc["high"]),
                        "low": convert_to_decimal(ohlc["low"]),
                        "close": convert_to_decimal(ohlc["close"]),
                        "last_price": convert_to_decimal(data["last_price"]),
                        "volume": safe_int(data.get("volume", 0)),
                        "timestamp": datetime.utcnow()
                    }
                
                return result
            else:
                raise MarketDataError("Failed to fetch OHLC data", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha OHLC: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")
    
    async def convert_position(self, symbol: str, transaction_type: str, 
                            old_product: str, new_product: str, quantity: int) -> bool:
        """Convert position between different products (MIS to CNC, etc.)"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                return True
            
            exchange = self._determine_exchange(symbol)
            
            conversion_data = {
                "tradingsymbol": symbol.upper(),
                "exchange": exchange,
                "transaction_type": transaction_type.upper(),
                "old_product": old_product.upper(),
                "new_product": new_product.upper(),
                "quantity": str(quantity)
            }
            
            response = await self.http_client.put(
                f"{self.base_url}/portfolio/positions",
                headers=self.headers,
                data=conversion_data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error converting Zerodha position: {e}")
            return False
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges"""
        return list(self.exchange_map.keys())
    
    def get_supported_products(self) -> List[str]:
        """Get list of supported products"""
        return ["CNC", "MIS", "NRML", "CO", "BO"]
    
    def get_supported_order_types(self) -> List[str]:
        """Get list of supported order types"""
        return ["MARKET", "LIMIT", "SL", "SL-M"]
    
    async def get_margins(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get margin requirements for orders"""
        await self.ensure_authenticated()
        
        try:
            if self.paper_trading:
                # Return mock margin data
                return {
                    "equity": {"required": 10000.0, "available": 50000.0},
                    "commodity": {"required": 0.0, "available": 20000.0}
                }
            
            response = await self.http_client.post(
                f"{self.base_url}/margins/orders",
                headers=self.headers,
                json=orders
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                raise MarketDataError("Failed to fetch margin requirements", "zerodha", str(response.status_code))
                
        except Exception as e:
            logger.error(f"Error fetching Zerodha margins: {e}")
            if isinstance(e, (AuthenticationError, MarketDataError)):
                raise
            raise MarketDataError(str(e), "zerodha")


__all__ = ["ZerodhaBroker"]