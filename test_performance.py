#!/usr/bin/env python3
"""
Test script for portfolio performance API
Tests all timeframes: 1D, 1W, 1M, 3M, 1Y, YTD, OPEN, ALL
"""
import asyncio
import sys
import uuid
from datetime import date

# Add api-gateway to path
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.portfolio_performance_service import PortfolioPerformanceService

DATABASE_URL = "postgresql+asyncpg://trading_user:dev_password_123@postgres:5432/trading_dev"

async def test_performance():
    """Test performance endpoints with all timeframes"""

    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    portfolio_id = uuid.UUID("593d30c5-aa9c-423f-820d-4e77f7f62910")
    user_id = uuid.UUID("ee5c4245-9f77-4324-a35e-420c826d81d2")

    timeframes = ["1D", "1W", "1M", "3M", "1Y", "YTD", "OPEN", "ALL"]

    print("=" * 80)
    print("PORTFOLIO PERFORMANCE TEST")
    print("=" * 80)
    print(f"Portfolio ID: {portfolio_id}")
    print(f"User ID: {user_id}")
    print("=" * 80)

    async with async_session() as session:
        # Test creating a snapshot first
        print("\n1. Testing Snapshot Creation")
        print("-" * 80)
        try:
            snapshot = await PortfolioPerformanceService.calculate_daily_snapshot(
                db=session,
                portfolio_id=portfolio_id,
                user_id=user_id
            )
            print("✓ Snapshot created successfully")
            print(f"  Date: {snapshot['snapshot_date']}")
            print(f"  Total Value: ${snapshot['total_value']:,.2f}")
            print(f"  P&L: ${snapshot['total_pnl']:,.2f}")
        except Exception as e:
            print(f"✗ Snapshot creation failed: {e}")
            import traceback
            traceback.print_exc()

        # Test all timeframes
        print("\n2. Testing Performance Data Retrieval")
        print("-" * 80)

        for timeframe in timeframes:
            print(f"\nTesting timeframe: {timeframe}")
            try:
                result = await PortfolioPerformanceService.get_performance_data(
                    db=session,
                    portfolio_id=portfolio_id,
                    user_id=user_id,
                    timeframe=timeframe
                )

                print(f"  ✓ {timeframe} - Success")
                print(f"    Period: {result['start_date']} to {result['end_date']}")
                print(f"    Data Points: {len(result['chart_data'])}")

                if result['metrics']:
                    metrics = result['metrics']
                    print(f"    Current Value: ${metrics['current_value']:,.2f}")
                    print(f"    Period Return: ${metrics['period_return']:,.2f} ({metrics['period_return_percent']:.2f}%)")
                    print(f"    High: ${metrics['period_high']:,.2f}")
                    print(f"    Low: ${metrics['period_low']:,.2f}")

            except Exception as e:
                print(f"  ✗ {timeframe} - Failed: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_performance())
