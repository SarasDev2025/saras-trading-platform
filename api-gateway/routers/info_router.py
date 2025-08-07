import os
import asyncpg
from fastapi import APIRouter

router = APIRouter()

# Create a database connection
async def get_db():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST")  # 👈 Reads from env
    )

@router.get("/info")
async def get_platform_info():
    conn = await get_db()
    try:
        row = await conn.fetchrow("SELECT * FROM platform_info LIMIT 1")
        return dict(row) if row else {"message": "No info found"}
    finally:
        await conn.close()
