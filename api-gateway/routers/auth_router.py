# =====================================================
# auth_router.py - Complete Authentication Backend - FIXED
# =====================================================

from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
import json
import os

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from config.database import get_db
from models import APIResponse

# =====================================================
# Configuration
# =====================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =====================================================
# Helper Functions
# =====================================================

def user_to_dict(user_row) -> dict:
    """Convert database user row to dictionary with proper types"""
    return {
        "id": str(user_row.id),
        "email": user_row.email,
        "username": user_row.username,
        "first_name": user_row.first_name,
        "last_name": user_row.last_name,
        "email_verified": user_row.email_verified,
        "kyc_status": user_row.kyc_status,
        "account_status": user_row.account_status,
        "created_at": user_row.created_at
    }

# =====================================================
# Pydantic Models
# =====================================================

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with optional _ or -)')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 30:
            raise ValueError('Username must be less than 30 characters')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_verified: bool
    kyc_status: str
    account_status: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# =====================================================
# Auth Service Class
# =====================================================

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a random refresh token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token"""
        to_encode = {
            "sub": email,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
            "iat": datetime.utcnow()
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "password_reset":
                return None
            return email
        except JWTError:
            return None

# =====================================================
# Database Functions
# =====================================================

async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email"""
    try:
        result = await db.execute(
            text("SELECT * FROM users WHERE email = :email AND account_status = 'active'"),
            {"email": email.lower()}
        )
        return result.fetchone()
    except Exception as e:
        await db.rollback()
        raise e

async def get_user_by_username(db: AsyncSession, username: str):
    """Get user by username"""
    try:
        result = await db.execute(
            text("SELECT * FROM users WHERE username = :username AND account_status = 'active'"),
            {"username": username.lower()}
        )
        return result.fetchone()
    except Exception as e:
        await db.rollback()
        raise e

async def get_user_by_id(db: AsyncSession, user_id: str):
    """Get user by ID"""
    try:
        result = await db.execute(
            text("SELECT * FROM users WHERE id = :user_id AND account_status = 'active'"),
            {"user_id": user_id}
        )
        return result.fetchone()
    except Exception as e:
        await db.rollback()
        raise e

async def create_user(db: AsyncSession, user_data: dict):
    """Create new user"""
    user_id = secrets.token_hex(16)
    
    try:
        await db.begin()
        
        await db.execute(text("""
            INSERT INTO users (
                id, email, username, password_hash, first_name, last_name,
                email_verified, kyc_status, account_status, created_at
            ) VALUES (
                :id, :email, :username, :password_hash, :first_name, :last_name,
                :email_verified, :kyc_status, :account_status, :created_at
            )
        """), {
            "id": user_id,
            "email": user_data["email"].lower(),
            "username": user_data["username"].lower(),
            "password_hash": user_data["password_hash"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "email_verified": False,
            "kyc_status": "pending",
            "account_status": "active",
            "created_at": datetime.utcnow()
        })
        
        # Create default portfolio for user
        await db.execute(text("""
            INSERT INTO portfolios (user_id, name, description, cash_balance, total_value, created_at)
            VALUES (:user_id, 'Default Portfolio', 'Main investment portfolio', 50000.00, 50000.00, :created_at)
        """), {
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        
        await db.commit()
        return await get_user_by_id(db, user_id)
    except Exception as e:
        await db.rollback()
        raise e

async def store_refresh_token(db: AsyncSession, user_id: str, token: str, device_info: dict = None):
    """Store refresh token in database"""
    token_hash = AuthService.hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    try:
        await db.execute(text("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at, device_info, created_at)
            VALUES (:user_id, :token_hash, :expires_at, :device_info, :created_at)
        """), {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "device_info": json.dumps(device_info) if device_info else None,
            "created_at": datetime.utcnow()
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[str]:
    """Verify refresh token and return user_id if valid"""
    token_hash = AuthService.hash_token(token)
    
    try:
        result = await db.execute(text("""
            UPDATE refresh_tokens 
            SET last_used = :current_time 
            WHERE token_hash = :token_hash 
            AND expires_at > :current_time 
            AND is_revoked = FALSE
            RETURNING user_id
        """), {
            "token_hash": token_hash,
            "current_time": datetime.utcnow()
        })
        
        row = result.fetchone()
        if row:
            await db.commit()
            return row.user_id
        else:
            await db.rollback()
            return None
    except Exception as e:
        await db.rollback()
        raise e

async def revoke_refresh_token(db: AsyncSession, token: str):
    """Revoke a refresh token"""
    token_hash = AuthService.hash_token(token)
    try:
        await db.execute(text("""
            UPDATE refresh_tokens 
            SET is_revoked = TRUE,
                revoked_at = :current_time
            WHERE token_hash = :token_hash
        """), {
            "token_hash": token_hash,
            "current_time": datetime.utcnow()
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def revoke_all_user_tokens(db: AsyncSession, user_id: str):
    """Revoke all refresh tokens for a user"""
    try:
        await db.execute(text("""
            UPDATE refresh_tokens 
            SET is_revoked = TRUE,
                revoked_at = :current_time
            WHERE user_id = :user_id AND is_revoked = FALSE
        """), {
            "user_id": user_id,
            "current_time": datetime.utcnow()
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate user with email and password"""
    try:
        user = await get_user_by_email(db, email)
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            # Increment failed login attempts
            await db.execute(text("""
                UPDATE users 
                SET failed_login_attempts = failed_login_attempts + 1,
                    locked_until = CASE 
                        WHEN failed_login_attempts >= 4 THEN :lock_time
                        ELSE locked_until
                    END
                WHERE id = :user_id
            """), {
                "user_id": str(user.id),  # Convert UUID to string
                "lock_time": datetime.utcnow() + timedelta(minutes=15)
            })
            await db.commit()
            return None
        
        # Reset failed login attempts on successful login
        await db.execute(text("""
            UPDATE users 
            SET failed_login_attempts = 0,
                locked_until = NULL,
                last_login = :current_time
            WHERE id = :user_id
        """), {
            "user_id": str(user.id),  # Convert UUID to string
            "current_time": datetime.utcnow()
        })
        await db.commit()
        
        return user
    except Exception as e:
        await db.rollback()
        raise e

async def update_password(db: AsyncSession, email: str, new_password: str):
    """Update user password"""
    try:
        hashed_password = AuthService.get_password_hash(new_password)
        await db.execute(text("""
            UPDATE users 
            SET password_hash = :password_hash,
                failed_login_attempts = 0,
                locked_until = NULL
            WHERE email = :email
        """), {
            "email": email.lower(),
            "password_hash": hashed_password
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

# =====================================================
# Dependencies
# =====================================================

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    return user

# =====================================================
# Router and Endpoints
# =====================================================

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=APIResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check username availability
    existing_username = await get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Hash password and create user
    hashed_password = AuthService.get_password_hash(user_data.password)
    
    user_dict = user_data.model_dump()  # Changed from dict() to model_dump()
    user_dict["password_hash"] = hashed_password
    del user_dict["password"]
    
    user = await create_user(db, user_dict)
    
    # Generate tokens
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(str(user.id))
    
    # Store refresh token
    device_info = {
        "ip_address": str(request.client.host),
        "user_agent": request.headers.get("user-agent", "")
    }
    await store_refresh_token(db, str(user.id), refresh_token, device_info)  # Convert UUID to string
    
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user_to_dict(user))  # Use helper function
        )
    )

@router.post("/login", response_model=APIResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(str(user.id))
    
    # Store refresh token
    device_info = {
        "ip_address": str(request.client.host) if request else None,
        "user_agent": request.headers.get("user-agent", "") if request else ""
    }
    await store_refresh_token(db, str(user.id), refresh_token, device_info)  # Convert UUID to string
    
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user_to_dict(user))  # Use helper function
        )
    )

@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    user_id = await verify_refresh_token(db, token_data.refresh_token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    
    return APIResponse(
        success=True,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    )

@router.post("/logout", response_model=APIResponse)
async def logout(
    token_data: RefreshTokenRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout and revoke refresh token"""
    await revoke_refresh_token(db, token_data.refresh_token)
    
    return APIResponse(
        success=True,
        data={"message": "Successfully logged out"}
    )

@router.post("/logout-all", response_model=APIResponse)
async def logout_all(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout from all devices - revoke all refresh tokens"""
    await revoke_all_user_tokens(db, str(current_user.id))  # Convert UUID to string
    
    return APIResponse(
        success=True,
        data={"message": "Successfully logged out from all devices"}
    )

@router.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current user information"""
    return APIResponse(
        success=True,
        data=UserResponse(**user_to_dict(current_user))  # Use helper function
    )

@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email"""
    user = await get_user_by_email(db, request_data.email)
    
    # Always return success to prevent email enumeration
    # In production, you would send an email here
    reset_token = AuthService.create_password_reset_token(request_data.email)
    
    # TODO: Send email with reset_token
    # For now, just log it (remove in production)
    print(f"Password reset token for {request_data.email}: {reset_token}")
    
    return APIResponse(
        success=True,
        data={"message": "If the email exists, a password reset link has been sent"}
    )

@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    request_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    email = AuthService.verify_password_reset_token(request_data.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if user exists
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Update password
    await update_password(db, email, request_data.new_password)
    
    # Revoke all refresh tokens for security
    await revoke_all_user_tokens(db, str(user.id))  # Convert UUID to string
    
    return APIResponse(
        success=True,
        data={"message": "Password reset successfully"}
    )

@router.post("/change-password", response_model=APIResponse)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password for authenticated user"""
    # Verify current password
    if not AuthService.verify_password(request_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    await update_password(db, current_user.email, request_data.new_password)
    
    # Optionally revoke all refresh tokens for security
    await revoke_all_user_tokens(db, str(current_user.id))  # Convert UUID to string
    
    return APIResponse(
        success=True,
        data={"message": "Password changed successfully"}
    )