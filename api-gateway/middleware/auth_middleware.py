# =====================================================
# middleware/auth_middleware.py - Enhanced Authentication & Audit Middleware
# =====================================================

import time
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import jwt
from jose import JWTError
import os 


from config.database import get_db

logger = logging.getLogger(__name__)

class AuthAuditMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware that tracks:
    - Login attempts (success/failure)
    - Token usage and validation
    - User activity patterns
    - Suspicious behavior detection
    """
    
    def __init__(self, app, secret_key: str, algorithm: str = "HS256"):
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add request ID to headers for tracking
        request.state.request_id = request_id
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Extract auth token if present
        auth_header = request.headers.get("authorization")
        token = None
        user_id = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_id = await self._extract_user_from_token(token)
        
        # Log request start
        await self._log_request_start(
            request_id, client_ip, user_agent, request.url.path, 
            request.method, user_id
        )
        
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Log successful request
            await self._log_request_complete(
                request_id, response.status_code, processing_time, 
                user_id, success=True
            )
            
            # Special handling for auth endpoints
            if request.url.path in ["/auth/login", "/auth/register"]:
                await self._handle_auth_endpoint(request, response, client_ip, user_agent)
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log failed request
            await self._log_request_complete(
                request_id, 500, processing_time, user_id, 
                success=False, error=str(e)
            )
            
            # Log potential security issues
            if isinstance(e, HTTPException) and e.status_code == 401:
                await self._log_security_event(
                    "INVALID_TOKEN", client_ip, user_agent, token, str(e)
                )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    async def _extract_user_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token without full validation"""
        try:
            # Decode without verification to get user_id for logging
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        except Exception:
            return None
    
    async def _log_request_start(
        self, request_id: str, client_ip: str, user_agent: str, 
        path: str, method: str, user_id: Optional[str]
    ):
        """Log request initiation"""
        log_data = {
            "event": "REQUEST_START",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "path": path,
            "method": method,
            "user_id": user_id
        }
        
        logger.info(f"REQUEST_START: {json.dumps(log_data)}")
        
        # Store in database for audit trail
        try:
            async for db in get_db():
                await self._store_audit_log(db, log_data)
                break
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")
    
    async def _log_request_complete(
        self, request_id: str, status_code: int, processing_time: float,
        user_id: Optional[str], success: bool, error: str = None
    ):
        """Log request completion"""
        log_data = {
            "event": "REQUEST_COMPLETE",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "user_id": user_id,
            "success": success,
            "error": error
        }
        
        logger.info(f"REQUEST_COMPLETE: {json.dumps(log_data)}")
    
    async def _handle_auth_endpoint(
        self, request: Request, response: Response, 
        client_ip: str, user_agent: str
    ):
        """Special handling for authentication endpoints"""
        if request.url.path == "/auth/login":
            if response.status_code == 200:
                # Extract user info from response if possible
                await self._log_security_event(
                    "LOGIN_SUCCESS", client_ip, user_agent, 
                    details="User logged in successfully"
                )
            else:
                await self._log_security_event(
                    "LOGIN_FAILURE", client_ip, user_agent, 
                    details=f"Login failed with status {response.status_code}"
                )
    
    async def _log_security_event(
        self, event_type: str, client_ip: str, user_agent: str,
        token: str = None, details: str = None
    ):
        """Log security-related events"""
        log_data = {
            "event": "SECURITY_EVENT",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "token_present": token is not None,
            "details": details
        }
        
        logger.warning(f"SECURITY_EVENT: {json.dumps(log_data)}")
        
        # Store security events in database
        try:
            async for db in get_db():
                await self._store_security_log(db, log_data)
                break
        except Exception as e:
            logger.error(f"Failed to store security log: {e}")
    
    async def _store_audit_log(self, db: AsyncSession, log_data: Dict[str, Any]):
        """Store audit log in database"""
        try:
            timestamp = log_data.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")
                    except ValueError:
                        try:
                            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            timestamp = None

            await db.execute(text("""
                INSERT INTO audit_logs (
                    id, event_type, request_id, timestamp, client_ip, 
                    user_agent, path, method, user_id, created_at
                ) VALUES (
                    gen_random_uuid(), :event, :request_id, :timestamp, 
                    :client_ip, :user_agent, :path, :method, :user_id, NOW()
                )
            """), {
                "event": log_data["event"],
                "request_id": log_data["request_id"],
                "timestamp": timestamp,
                "client_ip": log_data["client_ip"],
                "user_agent": log_data["user_agent"],
                "path": log_data.get("path"),
                "method": log_data.get("method"),
                "user_id": log_data.get("user_id")
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Database audit log error: {e}")
    
    async def _store_security_log(self, db: AsyncSession, log_data: Dict[str, Any]):
        """Store security events in database"""
        try:
            timestamp = log_data.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")
                    except ValueError:
                        try:
                            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            timestamp = None

            await db.execute(text("""
                INSERT INTO security_logs (
                    id, event_type, timestamp, client_ip, user_agent, 
                    token_present, details, created_at
                ) VALUES (
                    gen_random_uuid(), :event_type, :timestamp, 
                    :client_ip, :user_agent, :token_present, :details, NOW()
                )
            """), {
                "event_type": log_data["event_type"],
                "timestamp": timestamp,
                "client_ip": log_data["client_ip"],
                "user_agent": log_data["user_agent"],
                "token_present": log_data["token_present"],
                "details": log_data["details"]
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Database security log error: {e}")
            # Log the problematic query for debugging
            logger.error(f"Failed log_data: {log_data}")


# =====================================================
# Enhanced Token Validation Service
# =====================================================

class EnhancedTokenService:
    """Enhanced token validation with comprehensive security checks"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    async def validate_token_comprehensive(
        self, token: str, db: AsyncSession, 
        client_ip: str, user_agent: str
    ) -> Dict[str, Any]:
        """
        Comprehensive token validation with security checks
        Returns user info and logs validation attempt
        """
        validation_start = time.time()
        
        try:
            # 1. Basic JWT validation
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            token_type = payload.get("type", "access")
            issued_at = payload.get("iat")
            expires_at = payload.get("exp")
            
            if not user_id or token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token structure"
                )
            
            # 2. Check if token is blacklisted
            is_blacklisted = await self._check_token_blacklist(db, token)
            if is_blacklisted:
                await self._log_suspicious_activity(
                    db, user_id, "BLACKLISTED_TOKEN_USE", client_ip, user_agent
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # 3. Get user info and check account status
            user_info = await self._get_user_with_security_check(db, user_id)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # 4. Check for suspicious patterns
            await self._check_suspicious_patterns(
                db, user_id, client_ip, user_agent, token
            )
            
            # 5. Log successful validation
            validation_time = (time.time() - validation_start) * 1000
            await self._log_token_validation(
                db, user_id, "SUCCESS", validation_time, client_ip, user_agent
            )
            
            return {
                "user_id": user_id,
                "user": user_info,
                "token_age": time.time() - issued_at,
                "validation_time_ms": validation_time
            }
            
        except JWTError as e:
            await self._log_token_validation(
                db, None, "JWT_ERROR", (time.time() - validation_start) * 1000, 
                client_ip, user_agent, str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        except HTTPException:
            raise
        except Exception as e:
            await self._log_token_validation(
                db, None, "VALIDATION_ERROR", (time.time() - validation_start) * 1000,
                client_ip, user_agent, str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token validation failed"
            )
    
    async def _check_token_blacklist(self, db: AsyncSession, token: str) -> bool:
        """Check if token is in blacklist"""
        try:
            result = await db.execute(text("""
                SELECT 1 FROM token_blacklist 
                WHERE token_hash = :token_hash 
                AND expires_at > NOW()
            """), {"token_hash": self._hash_token(token)})
            
            return result.fetchone() is not None
        except Exception:
            return False
    
    async def _get_user_with_security_check(
        self, db: AsyncSession, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user info with security status checks"""
        try:
            result = await db.execute(text("""
                SELECT 
                    id, email, username, first_name, last_name,
                    account_status, email_verified, 
                    locked_until, failed_login_attempts,
                    last_login, created_at
                FROM users 
                WHERE id = :user_id
            """), {"user_id": user_id})
            
            user_row = result.fetchone()
            if not user_row:
                return None
            
            # Check if account is locked
            if user_row.locked_until:
                locked_until = user_row.locked_until
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)

                if locked_until > datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail="Account is temporarily locked"
                    )
            
            # Check account status - match your database values (lowercase)
            if user_row.account_status not in ["active", "verified"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is suspended or inactive"
                )
            
            return {
                "id": str(user_row.id),
                "email": user_row.email,
                "username": user_row.username,
                "first_name": user_row.first_name,
                "last_name": user_row.last_name,
                "account_status": user_row.account_status,
                "email_verified": user_row.email_verified,
                "last_login": user_row.last_login
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User security check error: {e}")
            return None
    
    async def _check_suspicious_patterns(
        self, db: AsyncSession, user_id: str, client_ip: str, 
        user_agent: str, token: str
    ):
        """Check for suspicious usage patterns"""
        try:
            # Check for rapid requests from same IP
            recent_requests = await db.execute(text("""
                SELECT COUNT(*) as count
                FROM audit_logs 
                WHERE client_ip = :client_ip 
                AND user_id = :user_id
                AND created_at > NOW() - INTERVAL '1 minute'
            """), {"client_ip": client_ip, "user_id": user_id})
            
            count = recent_requests.scalar()
            if count and count > 100:  # More than 100 requests per minute
                await self._log_suspicious_activity(
                    db, user_id, "RAPID_REQUESTS", client_ip, user_agent,
                    f"Too many requests: {count} in 1 minute"
                )
            
            # Check for multiple IPs using same token
            ip_count = await db.execute(text("""
                SELECT COUNT(DISTINCT client_ip) as ip_count
                FROM audit_logs 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '5 minutes'
            """), {"user_id": user_id})
            
            distinct_ips = ip_count.scalar()
            if distinct_ips and distinct_ips > 3:  # Token used from >3 IPs in 5 min
                await self._log_suspicious_activity(
                    db, user_id, "MULTIPLE_IPS", client_ip, user_agent,
                    f"Token used from {distinct_ips} different IPs"
                )
            
        except Exception as e:
            logger.error(f"Suspicious pattern check error: {e}")
    
    async def _log_suspicious_activity(
        self, db: AsyncSession, user_id: str, activity_type: str,
        client_ip: str, user_agent: str, details: str = None
    ):
        """Log suspicious activity for security monitoring"""
        try:
            await db.execute(text("""
                INSERT INTO suspicious_activities (
                    id, user_id, activity_type, client_ip, user_agent, 
                    details, created_at
                ) VALUES (
                    gen_random_uuid(), :user_id, :activity_type, :client_ip, 
                    :user_agent, :details, NOW()
                )
            """), {
                "user_id": user_id,
                "activity_type": activity_type,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "details": details
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to log suspicious activity: {e}")
    
    async def _log_token_validation(
        self, db: AsyncSession, user_id: Optional[str], result: str,
        validation_time_ms: float, client_ip: str, user_agent: str,
        error_details: str = None
    ):
        """Log token validation attempts"""
        try:
            await db.execute(text("""
                INSERT INTO token_validations (
                    id, user_id, result, validation_time_ms, client_ip, 
                    user_agent, error_details, created_at
                ) VALUES (
                    gen_random_uuid(), :user_id, :result, :validation_time_ms, 
                    :client_ip, :user_agent, :error_details, NOW()
                )
            """), {
                "user_id": user_id,
                "result": result,
                "validation_time_ms": validation_time_ms,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "error_details": error_details
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to log token validation: {e}")
    
    def _hash_token(self, token: str) -> str:
        """Create hash of token for blacklist storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def blacklist_token(self, db: AsyncSession, token: str, expires_at: datetime):
        """Add token to blacklist"""
        try:
            token_hash = self._hash_token(token)
            await db.execute(text("""
                INSERT INTO token_blacklist (
                    id, token_hash, expires_at, created_at
                ) VALUES (
                    gen_random_uuid(), :token_hash, :expires_at, NOW()
                )
            """), {
                "token_hash": token_hash,
                "expires_at": expires_at
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to blacklist token: {e}")


# Global instance
enhanced_token_service = EnhancedTokenService(
    secret_key=os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
)
