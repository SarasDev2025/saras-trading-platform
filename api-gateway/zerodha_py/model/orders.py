from pydantic import BaseModel, Field, validator
from typing import Literal, Optional

TransactionType = Literal["BUY", "SELL"]
ProductType = Literal["CNC", "MIS", "NRML", "CO", "BO"]


class BaseOrder(BaseModel):
    symbol: str = Field(..., description="Tradingsymbol, e.g., INFY")
    exchange: str = Field("NSE", description="Exchange, e.g., NSE/BSE")
    qty: int = Field(..., gt=0)
    side: TransactionType
    product: ProductType = "CNC"

    @validator("symbol")
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()


class MarketOrderRequest(BaseOrder):
    order_type: str = "MARKET"


class LimitOrderRequest(BaseOrder):
    order_type: str = "LIMIT"
    price: float
