# =====================================================
# dependencies/enhanced_auth.py - Enhanced Authentication Dependencies
# =====================================================

import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import jwt
from jose import JWTError

from config.database import get_db
from middleware.auth_middleware import enhanced_token_service

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error with enhanced logging"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


async def get_enhanced_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Enhanced authentication dependency with comprehensive security checks.
    This replaces your existing get_current_user dependency.
    """
    if not credentials:
        await _log_auth_attempt(db, None, request, "NO_TOKEN", "No authentication token provided")
        raise AuthenticationError("Authentication token required")
    
    # Extract client information
    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    try:
        # Use enhanced token validation service
        validation_result = await enhanced_token_service.validate_token_comprehensive(
            credentials.credentials, db, client_ip, user_agent
        )
        
        user = validation_result["user"]
        user_id = validation_result["user_id"]
        
        # Update last activity
        await _update_user_activity(db, user_id, client_ip, user_agent)
        
        # Add security context to request state
        request.state.auth_user = user
        request.state.auth_context = {
            "user_id": user_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "token_age": validation_result.get("token_age"),
            "validation_time": validation_result.get("validation_time_ms")
        }
        
        return user
        
    except HTTPException as e:
        await _log_auth_attempt(db, None, request, "TOKEN_ERROR", str(e.detail))
        raise
    except Exception as e:
        await _log_auth_attempt(db, None, request, "SYSTEM_ERROR", str(e))
        raise AuthenticationError("Authentication system error")


async def get_current_user_id(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
) -> str:
    """Extract user ID from authenticated user - maintains compatibility with existing code"""
    return current_user["id"]


async def get_optional_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns None if no valid token provided.
    Useful for endpoints that work both with and without authentication.
    """
    if not credentials:
        return None
    
    try:
        return await get_enhanced_current_user(request, credentials, db)
    except HTTPException:
        return None


async def require_email_verified(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
):
    """Dependency that requires email verification"""
    if not current_user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def require_admin_role(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Dependency that requires admin role"""
    # Check if user has admin role (you'll need to implement role system)
    user_roles = await _get_user_roles(db, current_user["id"])
    
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return current_user


class RateLimiter:
    """Rate limiting dependency"""
    
    def __init__(self, max_requests: int, window_minutes: int):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
    
    async def __call__(
        self, 
        request: Request,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[Dict[str, Any], Depends(get_optional_current_user)]
    ):
        client_ip = _get_client_ip(request)
        user_id = current_user["id"] if current_user else None
        
        # Check rate limit
        is_limited = await self._check_rate_limit(db, client_ip, user_id, request.url.path)
        
        if is_limited:
            await self._log_rate_limit_violation(db, client_ip, user_id, request.url.path)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.max_requests} requests per {self.window_minutes} minutes"
            )
        
        return True
    
    async def _check_rate_limit(
        self, db: AsyncSession, client_ip: str, user_id: Optional[str], endpoint: str
    ) -> bool:
        """Check if request should be rate limited"""
        try:
            # Count requests in time window
            result = await db.execute(text("""
                SELECT COUNT(*) as request_count
                FROM audit_logs 
                WHERE (client_ip = :client_ip OR user_id = :user_id)
                AND path = :endpoint
                AND created_at > NOW() - INTERVAL ':window_minutes minutes'
            """), {
                "client_ip": client_ip,
                "user_id": user_id,
                "endpoint": endpoint,
                "window_minutes": self.window_minutes
            })
            
            count = result.scalar()
            return count >= self.max_requests
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False
    
    async def _log_rate_limit_violation(
        self, db: AsyncSession, client_ip: str, user_id: Optional[str], endpoint: str
    ):
        """Log rate limit violation"""
        try:
            await db.execute(text("""
                INSERT INTO rate_limit_violations (
                    client_ip, user_id, endpoint, request_count, time_window_minutes
                ) VALUES (
                    :client_ip, :user_id, :endpoint, :max_requests, :window_minutes
                )
            """), {
                "client_ip": client_ip,
                "user_id": user_id,
                "endpoint": endpoint,
                "max_requests": self.max_requests,
                "window_minutes": self.window_minutes
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to log rate limit violation: {e}")


# Common rate limiters
login_rate_limiter = RateLimiter(max_requests=5, window_minutes=15)  # 5 login attempts per 15 min
api_rate_limiter = RateLimiter(max_requests=1000, window_minutes=60)  # 1000 API calls per hour
strict_rate_limiter = RateLimiter(max_requests=100, window_minutes=60)  # 100 requests per hour


async def track_user_activity(
    request: Request,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Dependency to track user activity for analytics and security.
    Add this to important endpoints you want to monitor.
    """
    try:
        await db.execute(text("""
            INSERT INTO user_activity (
                id, user_id, action, endpoint, client_ip, user_agent, created_at
            ) VALUES (
                gen_random_uuid(), :user_id, :action, :endpoint, :client_ip, :user_agent, NOW()
            )
        """), {
            "user_id": current_user["id"],
            "action": f"{request.method} {request.url.path}",
            "endpoint": request.url.path,
            "client_ip": _get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "")
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to track user activity: {e}")
    
    return current_user


# Helper functions
def _get_client_ip(request: Request) -> str:
    """Extract real client IP considering proxies"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
        
    return request.client.host if request.client else "unknown"


_user_table_columns: Optional[set] = None


async def _get_user_table_columns(db: AsyncSession) -> set:
    """Read user table columns once so we can build compatible UPDATE statements."""
    global _user_table_columns

    if _user_table_columns is not None:
        return _user_table_columns

    try:
        result = await db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
              AND table_schema = current_schema()
        """))
        _user_table_columns = {row.column_name for row in result}
    except Exception as e:
        logger.warning(f"Unable to introspect users table columns: {e}")
        _user_table_columns = set()

    return _user_table_columns


async def _update_user_activity(
    db: AsyncSession, user_id: str, client_ip: str, user_agent: str
):
    """Update user's last activity information without assuming optional columns exist."""
    try:
        columns = await _get_user_table_columns(db)

        set_clauses = ["last_login = NOW()"]
        params = {"user_id": user_id}

        if "last_login_ip" in columns:
            set_clauses.append("last_login_ip = :client_ip")
            params["client_ip"] = client_ip

        if "last_login_user_agent" in columns:
            set_clauses.append("last_login_user_agent = :user_agent")
            params["user_agent"] = user_agent

        update_sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :user_id"
        await db.execute(text(update_sql), params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user activity: {e}")


async def _log_auth_attempt(
    db: AsyncSession, user_id: Optional[str], request: Request, 
    result: str, details: str
):
    """Log authentication attempt"""
    try:
        await db.execute(text("""
            INSERT INTO security_logs (
                event_type, user_id, timestamp, client_ip, user_agent, details
            ) VALUES (
                :event_type, :user_id, NOW(), :client_ip, :user_agent, :details
            )
        """), {
            "event_type": f"AUTH_{result}",
            "user_id": user_id,
            "client_ip": _get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "details": details
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log auth attempt: {e}")


async def _get_user_roles(db: AsyncSession, user_id: str) -> list:
    """Get user roles - implement based on your role system"""
    try:
        result = await db.execute(text("""
            SELECT role_name FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND ur.is_active = true
        """), {"user_id": user_id})
        
        roles = [row.role_name for row in result.fetchall()]
        return roles
    except Exception:
        return []  # Return empty list if role system not implemented yet


# Security monitoring functions
async def get_security_metrics(db: AsyncSession, days: int = 7) -> Dict[str, Any]:
    """Get security metrics for monitoring dashboard"""
    try:
        # Failed login attempts
        failed_logins = await db.execute(text("""
            SELECT COUNT(*) FROM security_logs 
            WHERE event_type = 'LOGIN_FAILURE' 
            AND created_at > NOW() - INTERVAL ':days days'
        """), {"days": days})
        
        # Suspicious activities
        suspicious_count = await db.execute(text("""
            SELECT COUNT(*) FROM suspicious_activities 
            WHERE created_at > NOW() - INTERVAL ':days days'
        """), {"days": days})
        
        # Token validation failures
        token_failures = await db.execute(text("""
            SELECT COUNT(*) FROM token_validations 
            WHERE result != 'SUCCESS' 
            AND created_at > NOW() - INTERVAL ':days days'
        """), {"days": days})
        
        # Top IPs with failures
        top_failed_ips = await db.execute(text("""
            SELECT client_ip, COUNT(*) as failure_count
            FROM security_logs 
            WHERE event_type IN ('LOGIN_FAILURE', 'INVALID_TOKEN')
            AND created_at > NOW() - INTERVAL ':days days'
            GROUP BY client_ip
            ORDER BY failure_count DESC
            LIMIT 10
        """), {"days": days})
        
        return {
            "failed_logins": failed_logins.scalar(),
            "suspicious_activities": suspicious_count.scalar(),
            "token_failures": token_failures.scalar(),
            "top_failed_ips": [
                {"ip": row.client_ip, "count": row.failure_count} 
                for row in top_failed_ips.fetchall()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        return {}


# Usage examples for your existing endpoints:
"""
# Replace your existing dependencies like this:

# OLD:
from routers.users_router import get_current_user_id

# NEW:
from dependencies.enhanced_auth import get_current_user_id, get_enhanced_current_user

# In your route handlers:
@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Your existing code works the same way
    pass

# For rate limiting:
@router.post("/login", dependencies=[Depends(login_rate_limiter)])
async def login(...):
    pass

# For activity tracking:
@router.post("/important-action")
async def important_action(
    user: Annotated[Dict[str, Any], Depends(track_user_activity)]
):
    pass
"""
