"""
Database configuration and connection management for FastAPI trading platform
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
import redis.asyncio as redis
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URLs - Using PgBouncer for connection pooling
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://trading_user:dev_password_123@pgbouncer:5432/trading_dev")
DIRECT_DATABASE_URL = os.getenv("DIRECT_DATABASE_URL", "postgresql+asyncpg://trading_user:dev_password_123@postgres:5432/trading_dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()

# Async engine for main operations (through PgBouncer)
async_engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("NODE_ENV") == "development",
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Direct engine for migrations and admin operations
direct_async_engine = create_async_engine(
    DIRECT_DATABASE_URL,
    echo=os.getenv("NODE_ENV") == "development",
    pool_size=5,
    max_overflow=0,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Redis client
redis_client: Optional[redis.Redis] = None


class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.direct_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize_connections(self) -> bool:
        """Initialize all database connections"""
        try:
            # Initialize PostgreSQL connection pools
            self.pool = await asyncpg.create_pool(
                DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            self.direct_pool = await asyncpg.create_pool(
                DIRECT_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=2,
                max_size=5,
                command_timeout=60
            )
            
            # Test PostgreSQL connection
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT NOW()')
                logger.info(f"PostgreSQL connected successfully. Server time: {result}")
            
            # Initialize Redis connection
            self.redis_client = redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            logger.info("Redis connected successfully")
            
            # Set global redis client
            global redis_client
            redis_client = self.redis_client
            
            return True
            
        except Exception as error:
            logger.error(f"Database connection failed: {error}")
            return False
    
    async def close_connections(self):
        """Close all database connections"""
        logger.info("Shutting down database connections...")
        
        try:
            if self.pool:
                await self.pool.close()
            if self.direct_pool:
                await self.direct_pool.close()
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Database connections closed successfully")
        except Exception as error:
            logger.error(f"Error during shutdown: {error}")


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session"""
    async with get_db_session() as session:
        yield session


class DatabaseQuery:
    """Database query helper with error handling and logging"""
    
    @staticmethod
    async def execute_query(query: str, params: list = None, fetch_one: bool = False, fetch_all: bool = True):
        """Execute a query with error handling and logging"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with db_manager.pool.acquire() as conn:
                if params:
                    if fetch_one:
                        result = await conn.fetchrow(query, *params)
                    elif fetch_all:
                        result = await conn.fetch(query, *params)
                    else:
                        result = await conn.execute(query, *params)
                else:
                    if fetch_one:
                        result = await conn.fetchrow(query)
                    elif fetch_all:
                        result = await conn.fetch(query)
                    else:
                        result = await conn.execute(query)
                
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                
                if os.getenv("NODE_ENV") == "development":
                    query_preview = query[:100] + ("..." if len(query) > 100 else "")
                    logger.info(f"Query executed: {query_preview} | Duration: {duration:.2f}ms")
                
                return result
                
        except Exception as error:
            query_preview = query[:100] + ("..." if len(query) > 100 else "")
            logger.error(f"Database query error: {error} | Query: {query_preview}")
            raise


@asynccontextmanager
async def transaction():
    """Transaction context manager"""
    async with db_manager.pool.acquire() as conn:
        async with conn.transaction():
            yield conn


class CacheManager:
    """Redis cache helper functions"""
    
    @staticmethod
    async def get(key: str):
        """Get value from cache"""
        try:
            if redis_client:
                value = await redis_client.get(key)
                if value:
                    import json
                    return json.loads(value)
            return None
        except Exception as error:
            logger.error(f"Redis GET error: {error}")
            return None
    
    @staticmethod
    async def set(key: str, value, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            if redis_client:
                import json
                await redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as error:
            logger.error(f"Redis SET error: {error}")
    
    @staticmethod
    async def delete(key: str):
        """Delete key from cache"""
        try:
            if redis_client:
                await redis_client.delete(key)
        except Exception as error:
            logger.error(f"Redis DEL error: {error}")
    
    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if redis_client:
                return await redis_client.exists(key)
            return False
        except Exception as error:
            logger.error(f"Redis EXISTS error: {error}")
            return False


async def health_check() -> dict:
    """Check health of all database connections"""
    try:
        # Check PostgreSQL
        async with db_manager.pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        
        # Check Redis
        if redis_client:
            await redis_client.ping()
        
        return {
            "database": "healthy",
            "redis": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as error:
        return {
            "database": "unhealthy" if "pool" in str(error).lower() else "healthy",
            "redis": "unhealthy" if "redis" in str(error).lower() else "healthy",
            "error": str(error),
            "timestamp": asyncio.get_event_loop().time()
        }


# Startup and shutdown functions for FastAPI
async def startup_database():
    """Initialize database connections on startup"""
    success = await db_manager.initialize_connections()
    if not success:
        raise RuntimeError("Failed to initialize database connections")


async def shutdown_database():
    """Close database connections on shutdown"""
    await db_manager.close_connections()


# Export commonly used items
__all__ = [
    "Base",
    "async_engine",
    "direct_async_engine",
    "get_db",
    "get_db_session",
    "DatabaseQuery",
    "transaction",
    "CacheManager",
    "health_check",
    "startup_database",
    "shutdown_database",
    "db_manager"
]