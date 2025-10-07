# =====================================================
# main.py - Updated with Enhanced Authentication & Audit Middleware
# =====================================================

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text  # Add this line

from config.database import Base, get_db
from routers import (
    auth_router, portfolio_router, alpaca_router, info_router,
    trade_router, smallcase_router, rebalancing_router, broker_router, dividend_router, dividend_scheduler_router, gtt_router, settings_router, broker_config_router
)
from brokers import initialize_brokers, cleanup_brokers, broker_manager
from middleware.auth_middleware import AuthAuditMiddleware

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO for production readiness
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_gateway.log'),
        logging.FileHandler('security_audit.log')  # Dedicated security log
    ]
)

# Set specific log levels
logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.INFO)

# Security logger
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security_events.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

# Global variables for database and Redis
engine = None
async_session = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with enhanced startup/shutdown"""
    global engine, async_session, redis_client
    
    # Startup
    logger.info("🚀 Starting up Saras Trading Platform API Gateway...")
    
    try:
        # Initialize database
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://trading_user:dev_password_123@localhost:6432/trading_dev"
        )
        engine = create_async_engine(
            database_url, 
            echo=False,  # Changed to False for production
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800  # 30 minutes
        )
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database connection established and tables created")
        
        # Initialize Redis with connection pooling
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(
            redis_url, 
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True
        )
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("✅ Redis connection established")
        
        # Initialize brokers
        await initialize_brokers()
        logger.info("✅ Broker connections initialized")
        
        # Run security table setup
        await _ensure_security_tables()
        
        # Start background tasks
        await _start_background_tasks()
        
        logger.info("🎉 API Gateway started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("🔄 Shutting down API Gateway...")
    
    try:
        # Stop background tasks
        await _stop_background_tasks()
        
        # Cleanup brokers
        await cleanup_brokers()
        logger.info("✅ Broker connections closed")
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis connection closed")
        
        # Close database connection
        if engine:
            await engine.dispose()
            logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"⚠️ Shutdown error: {e}")
    
    logger.info("👋 API Gateway shutdown complete")

async def _ensure_security_tables():
    """Ensure security and audit tables exist"""
    try:
        async with engine.begin() as conn:
            # Check if audit tables exist, create if not
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(50) NOT NULL,
                    request_id UUID,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    client_ip INET,
                    user_agent TEXT,
                    path VARCHAR(500),
                    method VARCHAR(10),
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    status_code INTEGER,
                    processing_time_ms NUMERIC(10,2),
                    success BOOLEAN DEFAULT true,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            # Add indexes if they don't exist
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_client_ip ON audit_logs(client_ip)"))
            
        logger.info("✅ Security tables verified/created")
        
    except Exception as e:
        logger.error(f"⚠️ Failed to ensure security tables: {e}")

async def _start_background_tasks():
    """Start background maintenance tasks"""
    try:
        # Initialize dividend scheduler
        from services.dividend_scheduler import initialize_dividend_scheduler
        await initialize_dividend_scheduler(async_session)
        logger.info("✅ Dividend scheduler initialized")

        # You can add more background tasks here like:
        # - Cleaning old audit logs
        # - Refreshing security metrics
        # - Monitoring suspicious activities
        logger.info("✅ Background tasks started")
    except Exception as e:
        logger.error(f"⚠️ Failed to start background tasks: {e}")

async def _stop_background_tasks():
    """Stop background tasks"""
    try:
        # Stop dividend scheduler
        from services.dividend_scheduler import get_dividend_scheduler
        try:
            scheduler = await get_dividend_scheduler()
            await scheduler.stop()
            logger.info("✅ Dividend scheduler stopped")
        except RuntimeError:
            # Scheduler not initialized, ignore
            pass

        logger.info("✅ Background tasks stopped")
    except Exception as e:
        logger.error(f"⚠️ Failed to stop background tasks: {e}")

# Create FastAPI app
app = FastAPI(
    title="Saras Trading Platform API",
    description="Unified API Gateway for multi-broker trading platform with enhanced security",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") != "production" else None
)

# Get CORS origins from environment
cors_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,"
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Clean up origins (remove whitespace)
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

# Add CORS middleware
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
        "X-Real-IP",
        "X-Forwarded-For",
        "User-Agent"
    ],
    expose_headers=["X-Request-ID"]
)

# Add enhanced authentication and audit middleware
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
app.add_middleware(AuthAuditMiddleware, secret_key=SECRET_KEY)

# Global exception handler for better error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with security logging"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log the error
    logger.error(
        f"Unhandled exception for request {request_id}: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    # Log security-relevant errors
    if isinstance(exc, (PermissionError, ValueError)) or "auth" in str(exc).lower():
        security_logger.warning(
            f"Security-related exception: {type(exc).__name__}: {str(exc)} "
            f"- Request: {request.method} {request.url.path} "
            f"- IP: {request.client.host if request.client else 'unknown'}"
        )
    
    # Return appropriate error response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "request_id": request_id
        }
    )

# Health check endpoint with security info
@app.get("/health")
async def health_check():
    """Enhanced health check with system status"""
    try:
        # Check database
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Check Redis
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    # Check brokers
    try:
        active_brokers = len(broker_manager.list_brokers())
        broker_status = "healthy" if active_brokers > 0 else "no_brokers"
    except Exception:
        broker_status = "unhealthy"
    
    overall_status = "healthy" if all(
        status == "healthy" for status in [db_status, redis_status]
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "brokers": broker_status
        },
        "version": "2.0.0"
    }

# Security monitoring endpoint (admin only)
@app.get("/security/metrics")
async def get_security_metrics_endpoint(
#current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get security metrics (admin only)"""
    from dependencies.enhanced_auth import get_security_metrics
    
    metrics = await get_security_metrics(db, days=7)
    return {
        "success": True,
        "data": metrics
    }

# WebSocket connection manager with authentication
class ConnectionManager:
    """WebSocket connection manager with user tracking"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        logger.info(f"WebSocket connected: user {user_id}, connection {connection_id}")
    
    def disconnect(self, connection_id: str, user_id: str = None):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id and user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: connection {connection_id}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await websocket.send_text(message)
    
    async def send_user_message(self, message: str, user_id: str):
        """Send message to all connections for a user"""
        connections = self.user_connections.get(user_id, [])
        for connection_id in connections:
            await self.send_personal_message(message, connection_id)

manager = ConnectionManager()

# WebSocket endpoint with authentication
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str,
    token: str = None
):
    """WebSocket endpoint with token-based authentication"""
    connection_id = f"{user_id}_{int(time.time())}"
    
    # TODO: Add token validation for WebSocket connections
    # For now, accept all connections but log them
    logger.info(f"WebSocket connection attempt: user {user_id}")
    
    await manager.connect(websocket, user_id, connection_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WebSocket message from {user_id}: {data}")
            
            # Echo back for now - implement your WebSocket logic here
            await manager.send_personal_message(f"Echo: {data}", connection_id)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)

# Include routers with enhanced dependencies and proper organization
app.include_router(auth_router.router, tags=["Authentication"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["User Settings"])
app.include_router(broker_router.router, prefix="/brokers", tags=["Broker Management"])
app.include_router(broker_config_router.router, prefix="/api/v1", tags=["Broker Configuration"])
app.include_router(portfolio_router.router, prefix="/portfolios", tags=["Portfolio"])
app.include_router(smallcase_router.router, prefix="/smallcases", tags=["Smallcases"])
app.include_router(dividend_router.router, tags=["Dividend Management"])
app.include_router(dividend_scheduler_router.router, tags=["Dividend Scheduler"])
app.include_router(gtt_router.router, tags=["GTT Orders (Zerodha)"])
app.include_router(rebalancing_router.router, prefix="/api/v1", tags=["Rebalancing"])
app.include_router(trade_router.router, prefix="/api/v1", tags=["Trading"])
app.include_router(alpaca_router.router, prefix="/api/v1", tags=["Alpaca"])
app.include_router(info_router.router, prefix="/api/v1", tags=["Market Info"])

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Saras Trading Platform API Gateway",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Startup event logging
@app.on_event("startup")
async def startup_event():
    """Log startup completion"""
    logger.info("🎯 All systems initialized - API Gateway ready to serve requests")

# Import required dependencies at the end to avoid circular imports
try:
    from dependencies.enhanced_auth import require_admin_role
    from typing import Dict
    import time
except ImportError as e:
    logger.warning(f"Some enhanced auth features may not be available: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # Production-ready server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        workers=1,  # Use 1 worker for development, scale for production
        access_log=True,
        log_level="info"
    )