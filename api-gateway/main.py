import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from config.database import Base
from routers import auth_router, portfolio_router, alpaca_router, info_router, trade_router, smallcase_router, rebalancing_router
from brokers import initialize_brokers, cleanup_brokers, broker_manager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_gateway.log')
    ]
)
logger = logging.getLogger(__name__)

# Enable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Global variables for database and Redis
engine = None
async_session = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global engine, async_session, redis_client
    
    # Startup
    logger.info("Starting up API Gateway...")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://trading_user:dev_password_123@localhost:6432/trading_dev")
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize brokers
    await initialize_brokers()
    
    logger.info("API Gateway started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway...")
    
    # Cleanup brokers
    await cleanup_brokers()
    
    # Close Redis connection
    if redis_client:
        await redis_client.close()
    
    # Close database connection
    if engine:
        await engine.dispose()
    
    logger.info("API Gateway shut down complete")

app = FastAPI(
    title="Saras Trading Platform API",
    description="Unified API Gateway for multi-broker trading platform",
    version="1.0.0",
    lifespan=lifespan
)

# Get CORS origins from environment or use comprehensive defaults
cors_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Clean up origins (remove whitespace)
cors_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=["X-Request-ID"],
)

# Also add an explicit OPTIONS handler
@app.options("/{path:path}")
async def handle_cors_options(path: str):
    return {"message": "OK"}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database connection
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        
        # Check Redis connection
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "brokers": len(broker_manager.list_brokers())
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Saras Trading Platform API Gateway",
        "version": "1.0.0",
        "status": "running"
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include routers
from routers import broker_router
app.include_router(auth_router.router, tags=["Authentication"])
app.include_router(portfolio_router.router, prefix="/portfolios", tags=["Portfolio"])
app.include_router(smallcase_router.router, prefix="/smallcases", tags=["Smallcases"])
app.include_router(alpaca_router.router, prefix="/alpaca", tags=["Alpaca Broker"])
app.include_router(info_router.router, prefix="/platform", tags=["Platform Info"])
app.include_router(trade_router.router, prefix="/trade", tags=["Trading"])
app.include_router(broker_router.router, prefix="/brokers", tags=["Broker Management"])
#app.include_router(rebalancing_router.router, prefix="/smallcases", tags=["Rebalancing"])
app.include_router(rebalancing_router.router, tags=["Rebalancing"])


# Dependency injection for database sessions
async def get_db_session():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Dependency injection for Redis client
async def get_redis():
    """Get Redis client"""
    return redis_client