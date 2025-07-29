from fastapi import FastAPI
from routers import auth_router, portfolio_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Saras Trading API Gateway")

origins = [
    "http://localhost:3000",      # from browser dev
    "http://127.0.0.1:3000",      # alt
    "http://api-gateway:8000",    # from within Docker network
    "http://web-ui:3000"          # if container sends fetch (SSR)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] temporarily for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API Gateway is running"}

app.include_router(auth_router.router, prefix="/auth")
app.include_router(portfolio_router.router, prefix="/portfolio")
