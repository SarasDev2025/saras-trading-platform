from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()

class Trade(BaseModel):
    id: int
    createdAt: datetime
    symbol: str
    side: str
    quantity: int
    price: float
    value: float
    status: str

@router.get("/portfolios/{portfolio_id}/trades", response_model=List[Trade])
async def get_trades(portfolio_id: str):
    # Replace with your DB query
    trades = [
        Trade(
            id=1,
            createdAt=datetime.utcnow(),
            symbol="AAPL",
            side="BUY",
            quantity=10,
            price=150.5,
            value=1505,
            status="FILLED"
        ),
        Trade(
            id=2,
            createdAt=datetime.utcnow(),
            symbol="TSLA",
            side="SELL",
            quantity=5,
            price=700.0,
            value=3500,
            status="PENDING"
        )
    ]
    return trades
