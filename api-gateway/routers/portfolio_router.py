from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    value: float

@router.get("/status", response_model=List[PortfolioItem])
async def status():
    return [
        {"symbol": "AAPL", "quantity": 10, "value": 1950.0},
        {"symbol": "TSLA", "quantity": 5, "value": 1100.0},
        {"symbol": "GOOGL", "quantity": 8, "value": 1500.0}
    ]
