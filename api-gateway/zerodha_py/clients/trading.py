from typing import Dict, Any
from kiteconnect import KiteConnect
from ..model.orders import MarketOrderRequest, LimitOrderRequest
from ..exceptions import OrderError


class TradingClient:
    def __init__(self, api_key: str, access_token: str):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def place_market_order(self, req: MarketOrderRequest) -> Dict[str, Any]:
        try:
            res = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=req.exchange,
                tradingsymbol=req.symbol,
                transaction_type=req.side,
                quantity=req.qty,
                product=req.product,
                order_type=self.kite.ORDER_TYPE_MARKET,
            )
            return res
        except Exception as e:
            raise OrderError(str(e))

    def place_limit_order(self, req: LimitOrderRequest) -> Dict[str, Any]:
        try:
            res = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=req.exchange,
                tradingsymbol=req.symbol,
                transaction_type=req.side,
                quantity=req.qty,
                product=req.product,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=req.price,
            )
            return res
        except Exception as e:
            raise OrderError(str(e))

    def cancel_order(self, order_id: str):
        try:
            return self.kite.cancel_order(order_id=order_id)
        except Exception as e:
            raise OrderError(str(e))

    def get_orders(self):
        return self.kite.orders()

    def get_positions(self):
        return self.kite.positions()