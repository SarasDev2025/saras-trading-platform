"""
SQLAlchemy models for the trading platform
"""
import uuid
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Column, String, DateTime, Boolean, Numeric, Text, Integer,
    ForeignKey, CheckConstraint, Index, func, text, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func as sql_func

from config.database import Base


class KYCStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    BOND = "bond"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class IntervalType(str, Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))
    profile_image_url: Mapped[Optional[str]] = mapped_column(Text)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_status: Mapped[KYCStatus] = mapped_column(String(20), default=KYCStatus.PENDING)
    account_status: Mapped[AccountStatus] = mapped_column(String(20), default=AccountStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now(), onupdate=sql_func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    portfolios: Mapped[List["Portfolio"]] = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    trading_transactions: Mapped[List["TradingTransaction"]] = relationship("TradingTransaction", back_populates="user", cascade="all, delete-orphan")
    user_sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_smallcases: Mapped[List["Smallcase"]] = relationship("Smallcase", back_populates="creator")
    smallcase_investments: Mapped[List["UserSmallcaseInvestment"]] = relationship("UserSmallcaseInvestment", back_populates="user", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("kyc_status IN ('pending', 'approved', 'rejected')", name='check_kyc_status'),
        CheckConstraint("account_status IN ('active', 'suspended', 'closed')", name='check_account_status'),
    )

    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Default Portfolio")
    description: Mapped[Optional[str]] = mapped_column(Text)
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal('0.00'))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal('0.00'))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now(), onupdate=sql_func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    holdings: Mapped[List["PortfolioHolding"]] = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    trading_transactions: Mapped[List["TradingTransaction"]] = relationship("TradingTransaction", back_populates="portfolio", cascade="all, delete-orphan")

    @hybrid_property
    def holdings_value(self) -> Decimal:
        """Calculate total value of holdings"""
        return sum(holding.current_value or Decimal('0') for holding in self.holdings if holding.quantity > 0)

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name='{self.name}', total_value={self.total_value})>"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(String(20), nullable=False, index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 8))
    price_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    asset_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now(), onupdate=sql_func.now())

    # Relationships
    holdings: Mapped[List["PortfolioHolding"]] = relationship("PortfolioHolding", back_populates="asset")
    trading_transactions: Mapped[List["TradingTransaction"]] = relationship("TradingTransaction", back_populates="asset")
    price_history: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="asset", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("asset_type IN ('stock', 'crypto', 'forex', 'commodity', 'bond')", name='check_asset_type'),
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class TradingTransaction(Base):
    __tablename__ = "trading_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(15, 8), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now(), index=True)
    settlement_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[TransactionStatus] = mapped_column(String(20), default=TransactionStatus.PENDING, index=True)
    order_type: Mapped[OrderType] = mapped_column(String(20), default=OrderType.MARKET)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now(), onupdate=sql_func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trading_transactions")
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="trading_transactions")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="trading_transactions")

    # Constraints
    __table_args__ = (
        CheckConstraint("transaction_type IN ('buy', 'sell')", name='check_transaction_type'),
        CheckConstraint("status IN ('pending', 'executed', 'cancelled', 'failed')", name='check_status'),
        CheckConstraint("order_type IN ('market', 'limit', 'stop', 'stop_limit')", name='check_order_type'),
    )

    def __repr__(self) -> str:
        return f"<TradingTransaction(id={self.id}, type='{self.transaction_type}', quantity={self.quantity})>"


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=Decimal('0'))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(15, 8), nullable=False, default=Decimal('0'))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal('0'))
    current_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=Decimal('0'))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=Decimal('0'))
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=Decimal('0'))
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="holdings")

    # Constraints
    __table_args__ = (
        Index('idx_unique_portfolio_asset', 'portfolio_id', 'asset_id', unique=True),
    )

    @hybrid_property
    def return_percentage(self) -> Optional[Decimal]:
        """Calculate return percentage"""
        if self.total_cost and self.total_cost != 0:
            return ((self.current_value or Decimal('0')) - self.total_cost) / self.total_cost * 100
        return None

    def __repr__(self) -> str:
        return f"<PortfolioHolding(id={self.id}, quantity={self.quantity}, current_value={self.current_value})>"


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 8), nullable=False)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    interval_type: Mapped[IntervalType] = mapped_column(String(10), default=IntervalType.ONE_DAY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="price_history")

    # Constraints
    __table_args__ = (
        CheckConstraint("interval_type IN ('1m', '5m', '15m', '1h', '4h', '1d', '1w')", name='check_interval_type'),
    )

    def __repr__(self) -> str:
        return f"<PriceHistory(id={self.id}, price={self.price}, timestamp={self.timestamp})>"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sql_func.now())
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


# Smallcase models
class Smallcase(Base):
    __tablename__ = "smallcases"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(100))
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    expected_return_min: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    expected_return_max: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    minimum_investment: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("1000.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    creator: Mapped[Optional["User"]] = relationship("User", back_populates="created_smallcases")
    constituents: Mapped[List["SmallcaseConstituent"]] = relationship("SmallcaseConstituent", back_populates="smallcase", cascade="all, delete-orphan")
    investments: Mapped[List["UserSmallcaseInvestment"]] = relationship("UserSmallcaseInvestment", back_populates="smallcase")

    def __repr__(self) -> str:
        return f"<Smallcase(id={self.id}, name={self.name}, category={self.category})>"


class SmallcaseConstituent(Base):
    __tablename__ = "smallcase_constituents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    smallcase_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("smallcases.id"), nullable=False)
    asset_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    weight_percentage: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    smallcase: Mapped["Smallcase"] = relationship("Smallcase", back_populates="constituents")
    asset: Mapped["Asset"] = relationship("Asset")

    def __repr__(self) -> str:
        return f"<SmallcaseConstituent(smallcase_id={self.smallcase_id}, asset_id={self.asset_id}, weight={self.weight_percentage}%)>"


class UserSmallcaseInvestment(Base):
    __tablename__ = "user_smallcase_investments"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    portfolio_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    smallcase_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("smallcases.id"), nullable=False)
    investment_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    units_purchased: Mapped[Decimal] = mapped_column(DECIMAL(15, 8), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 8), nullable=False)
    current_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    invested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="smallcase_investments")
    portfolio: Mapped["Portfolio"] = relationship("Portfolio")
    smallcase: Mapped["Smallcase"] = relationship("Smallcase", back_populates="investments")

    def __repr__(self) -> str:
        return f"<UserSmallcaseInvestment(id={self.id}, user_id={self.user_id}, smallcase_id={self.smallcase_id}, amount={self.investment_amount})>"


# Export all models
__all__ = [
    "Base",
    "User",
    "Portfolio", 
    "Asset",
    "TradingTransaction",
    "PortfolioHolding",
    "PriceHistory",
    "UserSession",
    "Smallcase",
    "SmallcaseConstituent", 
    "UserSmallcaseInvestment",
    "KYCStatus",
    "AccountStatus",
    "AssetType",
    "TransactionType",
    "TransactionStatus",
    "OrderType",
    "IntervalType"
]