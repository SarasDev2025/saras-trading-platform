"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests including:
- Database setup/teardown
- Test client
- Authentication tokens
- Mock data
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from datetime import datetime
import uuid

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from faker import Faker

from main import app
from config.database import Base, get_db

# Initialize Faker for test data
fake = Faker()

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://trading_user:dev_password_123@localhost:5432/trading_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database session for each test"""
    # Create session factory
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""

    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user_id = uuid.uuid4()
    user_data = {
        'id': str(user_id),
        'email': fake.email(),
        'password_hash': pwd_context.hash('testpassword123'),
        'full_name': fake.name(),
        'region': 'US',
        'trading_mode': 'paper',
        'is_active': True,
        'created_at': datetime.utcnow()
    }

    await db_session.execute(
        text("""
            INSERT INTO users (id, email, password_hash, full_name, region, trading_mode, is_active, created_at)
            VALUES (:id, :email, :password_hash, :full_name, :region, :trading_mode, :is_active, :created_at)
        """),
        user_data
    )
    await db_session.commit()

    return {
        'id': str(user_id),
        'email': user_data['email'],
        'password': 'testpassword123',
        'full_name': user_data['full_name']
    }


@pytest.fixture
async def auth_token(client, test_user):
    """Get authentication token for test user"""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user['email'],
            "password": test_user['password']
        }
    )

    assert response.status_code == 200
    data = response.json()
    return data['access_token']


@pytest.fixture
async def auth_headers(auth_token):
    """Get authentication headers"""
    return {
        "Authorization": f"Bearer {auth_token}"
    }


@pytest.fixture
async def test_algorithm(db_session, test_user):
    """Create a test algorithm"""
    algorithm_id = uuid.uuid4()
    algorithm_data = {
        'id': str(algorithm_id),
        'user_id': test_user['id'],
        'name': 'Test Algorithm',
        'description': 'Test algorithm for unit tests',
        'language': 'python',
        'builder_type': 'code',
        'strategy_code': '''
def execute(context):
    # Simple test strategy
    if context['data']['AAPL']['close'] > context['data']['AAPL']['sma_20']:
        return {'action': 'buy', 'symbol': 'AAPL', 'quantity': 10}
    return None
        ''',
        'parameters': '{}',
        'auto_run': False,
        'execution_interval': 'manual',
        'max_positions': 5,
        'risk_per_trade': 2.0,
        'allowed_regions': ['US'],
        'allowed_trading_modes': ['paper'],
        'stock_universe': '{"type": "specific", "symbols": ["AAPL", "GOOGL"]}',
        'status': 'inactive',
        'created_at': datetime.utcnow()
    }

    await db_session.execute(
        text("""
            INSERT INTO trading_algorithms
            (id, user_id, name, description, language, builder_type, strategy_code,
             parameters, auto_run, execution_interval, max_positions, risk_per_trade,
             allowed_regions, allowed_trading_modes, stock_universe, status, created_at)
            VALUES
            (:id, :user_id, :name, :description, :language, :builder_type, :strategy_code,
             :parameters, :auto_run, :execution_interval, :max_positions, :risk_per_trade,
             :allowed_regions, :allowed_trading_modes, :stock_universe, :status, :created_at)
        """),
        algorithm_data
    )
    await db_session.commit()

    return {
        'id': str(algorithm_id),
        'name': algorithm_data['name'],
        'user_id': test_user['id']
    }


@pytest.fixture
async def test_portfolio(db_session, test_user):
    """Create a test portfolio"""
    portfolio_id = uuid.uuid4()
    portfolio_data = {
        'id': str(portfolio_id),
        'user_id': test_user['id'],
        'name': 'Test Portfolio',
        'description': 'Test portfolio for unit tests',
        'region': 'US',
        'trading_mode': 'paper',
        'broker': 'alpaca',
        'is_active': True,
        'created_at': datetime.utcnow()
    }

    await db_session.execute(
        text("""
            INSERT INTO portfolios
            (id, user_id, name, description, region, trading_mode, broker, is_active, created_at)
            VALUES
            (:id, :user_id, :name, :description, :region, :trading_mode, :broker, :is_active, :created_at)
        """),
        portfolio_data
    )
    await db_session.commit()

    return {
        'id': str(portfolio_id),
        'name': portfolio_data['name'],
        'user_id': test_user['id']
    }


@pytest.fixture
def mock_market_data():
    """Generate mock market data for testing"""
    import pandas as pd
    import numpy as np

    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')

    data = {
        'AAPL': pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(150, 200, len(dates)),
            'high': np.random.uniform(150, 200, len(dates)),
            'low': np.random.uniform(150, 200, len(dates)),
            'close': np.random.uniform(150, 200, len(dates)),
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }),
        'GOOGL': pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 150, len(dates)),
            'high': np.random.uniform(100, 150, len(dates)),
            'low': np.random.uniform(100, 150, len(dates)),
            'close': np.random.uniform(100, 150, len(dates)),
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })
    }

    return data


@pytest.fixture(autouse=True)
async def cleanup_database(db_session):
    """Clean up database after each test"""
    yield

    # Clean up tables in reverse order of dependencies
    tables_to_clean = [
        'test_results',
        'test_runs',
        'algorithm_performance_snapshots',
        'trades',
        'backtests',
        'trading_algorithms',
        'portfolio_holdings',
        'portfolios',
        'user_broker_configs',
        'users'
    ]

    for table in tables_to_clean:
        try:
            await db_session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass  # Table might not exist

    await db_session.commit()


# Helper functions for tests
def assert_valid_uuid(value: str):
    """Assert that a string is a valid UUID"""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def assert_valid_timestamp(value: str):
    """Assert that a string is a valid ISO timestamp"""
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


# Playwright Fixtures
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for Playwright tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "record_video_dir": "videos/",
        "record_video_size": {"width": 1920, "height": 1080}
    }


@pytest.fixture(scope="session")
def screenshot_dir():
    """Create screenshot directory"""
    import os
    os.makedirs("screenshots", exist_ok=True)
    return "screenshots"
