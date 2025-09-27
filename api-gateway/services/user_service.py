"""
User service for managing user operations
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import bcrypt
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import User, Portfolio, KYCStatus, AccountStatus
from ..config.database import get_db_session, transaction, DatabaseQuery


class UserService:
    """Service class for user-related operations"""

    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> User:
        """Create a new user with default portfolio"""
        async with get_db_session() as session:
            # Hash password
            password_bytes = user_data['password'].encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # Create user
            user = User(
                email=user_data['email'],
                username=user_data['username'],
                password_hash=password_hash,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                phone=user_data.get('phone'),
                date_of_birth=user_data.get('date_of_birth')
            )
            
            session.add(user)
            await session.flush()  # Get the user ID
            
            # Create default portfolio
            default_portfolio = Portfolio(
                user_id=user.id,
                name="Default Portfolio",
                cash_balance=10000.00,
                total_value=10000.00
            )
            
            session.add(default_portfolio)
            await session.commit()
            await session.refresh(user)
            
            return user

    @staticmethod
    async def find_by_email(email: str) -> Optional[User]:
        """Find user by email"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def find_by_username(username: str) -> Optional[User]:
        """Find user by username"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def find_by_id(user_id: uuid.UUID) -> Optional[User]:
        """Find user by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    async def update_last_login(user_id: uuid.UUID) -> None:
        """Update user's last login timestamp"""
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await session.commit()

    @staticmethod
    async def update_profile(user_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[User]:
        """Update user profile"""
        allowed_fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'profile_image_url']
        
        # Filter updates to only allowed fields
        filtered_updates = {
            key: value for key, value in updates.items() 
            if key in allowed_fields
        }
        
        if not filtered_updates:
            raise ValueError("No valid fields to update")

        async with get_db_session() as session:
            # Update user
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**filtered_updates, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            # Return updated user
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_email_verification(user_id: uuid.UUID, verified: bool = True) -> Optional[User]:
        """Update email verification status"""
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(email_verified=verified, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_kyc_status(user_id: uuid.UUID, status: KYCStatus) -> Optional[User]:
        """Update KYC status"""
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(kyc_status=status, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_with_portfolios(user_id: uuid.UUID) -> Optional[User]:
        """Get user with all portfolios"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.portfolios))
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def change_password(user_id: uuid.UUID, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        async with get_db_session() as session:
            # Get current password hash
            result = await session.execute(
                select(User.password_hash).where(User.id == user_id)
            )
            user_data = result.first()
            
            if not user_data:
                raise ValueError("User not found")
            
            # Verify current password
            if not await UserService.verify_password(current_password, user_data.password_hash):
                raise ValueError("Current password is incorrect")
            
            # Hash new password
            new_password_bytes = new_password.encode('utf-8')
            salt = bcrypt.gensalt()
            new_password_hash = bcrypt.hashpw(new_password_bytes, salt).decode('utf-8')
            
            # Update password
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(password_hash=new_password_hash, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            return True

    @staticmethod
    async def delete_user(user_id: uuid.UUID) -> bool:
        """Delete user and all related data"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            await session.delete(user)
            await session.commit()
            
            return True

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await UserService.find_by_email(email)
        
        if not user:
            return None
        
        if not await UserService.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        await UserService.update_last_login(user.id)
        
        return user

    @staticmethod
    async def is_email_taken(email: str, exclude_user_id: Optional[uuid.UUID] = None) -> bool:
        """Check if email is already taken by another user"""
        async with get_db_session() as session:
            query = select(User).where(User.email == email)
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_username_taken(username: str, exclude_user_id: Optional[uuid.UUID] = None) -> bool:
        """Check if username is already taken by another user"""
        async with get_db_session() as session:
            query = select(User).where(User.username == username)
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_user_stats(user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user statistics"""
        query = """
        SELECT 
            COUNT(DISTINCT p.id) as portfolio_count,
            COUNT(DISTINCT tt.id) as transaction_count,
            SUM(p.total_value) as total_portfolio_value,
            SUM(p.cash_balance) as total_cash_balance,
            COUNT(DISTINCT ph.id) as total_holdings
        FROM users u
        LEFT JOIN portfolios p ON u.id = p.user_id
        LEFT JOIN trading_transactions tt ON u.id = tt.user_id AND tt.status = 'executed'
        LEFT JOIN portfolio_holdings ph ON p.id = ph.portfolio_id AND ph.quantity > 0
        WHERE u.id = $1
        GROUP BY u.id
        """
        
        result = await DatabaseQuery.execute_query(query, [user_id], fetch_one=True)
        
        if result:
            return {
                "portfolio_count": result['portfolio_count'] or 0,
                "transaction_count": result['transaction_count'] or 0,
                "total_portfolio_value": float(result['total_portfolio_value'] or 0),
                "total_cash_balance": float(result['total_cash_balance'] or 0),
                "total_holdings": result['total_holdings'] or 0
            }
        
        return {
            "portfolio_count": 0,
            "transaction_count": 0,
            "total_portfolio_value": 0.0,
            "total_cash_balance": 0.0,
            "total_holdings": 0
        }