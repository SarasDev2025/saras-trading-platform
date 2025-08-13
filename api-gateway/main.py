from fastapi import FastAPI
from routers import auth_router, portfolio_router, alpaca_router, info_router, trade_router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")

app = FastAPI(title="Saras Trading API Gateway")


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # cannot be "*" if allow_credentials=True
    allow_credentials=False,         # set True ONLY if you actually use cookies/auth
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],             # or list specific: ["Content-Type","Authorization"]
)

@app.get("/")
async def root():
    return {"message": "API Gateway is running"}

app.include_router(auth_router.router, prefix="/auth")
app.include_router(portfolio_router.router, prefix="/portfolio")
app.include_router(alpaca_router.router, prefix="/alpaca")
app.include_router(info_router.router, prefix="/platform")
app.include_router(trade_router.router, prefix="/trade")