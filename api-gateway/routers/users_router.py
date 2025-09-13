"""
FastAPI routes for user management
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
import jwt

from ..services.user_service import UserService
from ..models import KYCStatus, AccountStatus

# Create router
router = APIRouter(prefix="/users", tags=["users"])

# JWT configuration
JWT_SECRET = "dev_jwt_secret_key_change_in_production"  # Get from env
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = 24 * 7  # 7 days

security = HTTPBearer()

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only letters and numbers')
        return v.lower()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    profile_image_url: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class APIResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None
    token: Optional[str] = None

# JWT helper functions
def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = {"sub": str(user_id), "type": "access"}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return uuid.UUID(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_id(user_id: uuid.UUID = Depends(verify_token)) -> uuid.UUID:
    """Get current authenticated user ID"""
    return user_id

# User registration and authentication
@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        # Check if email already exists
        if await UserService.is_email_taken(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if await UserService.is_username_taken(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user = await UserService.create_user(user_data.dict())
        
        # Create access token
        access_token = create_access_token(str(user.id))
        
        # Prepare response data (exclude sensitive info)
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": user.email_verified,
            "kyc_status": user.kyc_status,
            "created_at": user.created_at
        }
        
        return APIResponse(
            success=True,
            data=user_dict,
            token=access_token,
            message="User registered successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# @router.post("/login", response_model=APIResponse)
# async def login_user(login_data: UserLogin):
#     """Authenticate user and return token"""
#     try:
#         user = await UserService.authenticate_user(login_data.email, login_data.password)
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid email or password"
#             )
        
#         if user.account_status != AccountStatus.ACTIVE:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Account is suspended or closed"
#             )
        
#         # Create access token
#         access_token = create_access_token(str(user.id))
        
#         # Prepare response data
#         user_dict = {
#             "id": str(user.id),
#             "email": user.email,
#             "username": user.username,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "email_verified": user.email_verified,
#             "kyc_status": user.kyc_status,
#             "last_login": user.last_login
#         }
        
#         return APIResponse(
#             success=True,
#             data=user_dict,
#             token=access_token,
#             message="Login successful"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Login failed: {str(e)}"
#         )

# User profile management
@router.get("/profile", response_model=APIResponse)
async def get_profile(current_user_id: uuid.UUID = Depends(get_current_user_id)):
    """Get current user profile"""
    try:
        user = await UserService.get_user_with_portfolios(current_user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare response data
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "date_of_birth": user.date_of_birth,
            "profile_image_url": user.profile_image_url,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "kyc_status": user.kyc_status,
            "account_status": user.account_status,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "portfolios": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "total_value": float(p.total_value),
                    "is_default": p.is_default
                } for p in user.portfolios
            ]
        }
        
        return APIResponse(success=True, data=user_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )

@router.put("/profile", response_model=APIResponse)
async def update_profile(
    profile_data: UserProfile,
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """Update user profile"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        user = await UserService.update_profile(current_user_id, update_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "date_of_birth": user.date_of_birth,
            "profile_image_url": user.profile_image_url,
            "updated_at": user.updated_at
        }
        
        return APIResponse(
            success=True,
            data=user_dict,
            message="Profile updated successfully"
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/change-password", response_model=APIResponse)
async def change_password(
    password_data: PasswordChange,
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """Change user password"""
    try:
        success = await UserService.change_password(
            current_user_id,
            password_data.current_password,
            password_data.new_password
        )
        
        if success:
            return APIResponse(
                success=True,
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

# User statistics and activity
@router.get("/stats", response_model=APIResponse)
async def get_user_stats(current_user_id: uuid.UUID = Depends(get_current_user_id)):
    """Get user statistics"""
    try:
        stats = await UserService.get_user_stats(current_user_id)
        return APIResponse(success=True, data=stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user stats: {str(e)}"
        )

# Email verification
@router.post("/verify-email", response_model=APIResponse)
async def verify_email(current_user_id: uuid.UUID = Depends(get_current_user_id)):
    """Mark user email as verified (mock implementation)"""
    try:
        user = await UserService.update_email_verification(current_user_id, True)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="Email verified successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )

# Admin endpoints (for KYC management)
@router.put("/{user_id}/kyc-status", response_model=APIResponse)
async def update_kyc_status(
    user_id: uuid.UUID,
    kyc_status: KYCStatus,
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """Update user KYC status (admin only - add proper admin auth in production)"""
    try:
        user = await UserService.update_kyc_status(user_id, kyc_status)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            data={"kyc_status": user.kyc_status},
            message=f"KYC status updated to {kyc_status}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update KYC status: {str(e)}"
        )

# Account deletion
@router.delete("/account", response_model=APIResponse)
async def delete_account(current_user_id: uuid.UUID = Depends(get_current_user_id)):
    """Delete user account"""
    try:
        success = await UserService.delete_user(current_user_id)
        
        if success:
            return APIResponse(
                success=True,
                message="Account deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete account"
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

# Token validation endpoint
@router.get("/validate-token", response_model=APIResponse)
async def validate_token(current_user_id: uuid.UUID = Depends(get_current_user_id)):
    """Validate JWT token"""
    return APIResponse(
        success=True,
        data={"user_id": str(current_user_id)},
        message="Token is valid"
    )