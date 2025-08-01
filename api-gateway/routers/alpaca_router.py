import httpx
import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/account")
async def get_alpaca_account():
    headers = {
        "APCA-API-KEY-ID": os.getenv("ALPACA_API_KEY"),
        "APCA-API-SECRET-KEY": os.getenv("ALPACA_SECRET_KEY")
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{os.getenv('ALPACA_BASE_URL')}/account", headers=headers)
        response.raise_for_status()
        return response.json()
