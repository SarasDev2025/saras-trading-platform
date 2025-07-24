from fastapi import FastAPI
from routers import auth_router, portfolio_router

app = FastAPI(title="Saras Trading API Gateway")

app.include_router(auth_router.router, prefix="/auth")
app.include_router(portfolio_router.router, prefix="/portfolio")
