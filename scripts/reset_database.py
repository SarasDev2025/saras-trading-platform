#!/usr/bin/env python3
"""
Database Reset Script for Saras Trading Platform
Clears all data and resets the database to initial state
"""

import asyncio
import asyncpg

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,  # Direct PostgreSQL port
    'user': 'trading_user',
    'password': 'dev_password_123',
    'database': 'trading_dev'
}

async def reset_database():
    """Reset database by truncating all tables"""
    conn = await asyncpg.connect(**DATABASE_CONFIG)
    
    try:
        print("🔄 Resetting database...")
        
        # Disable foreign key checks temporarily
        await conn.execute("SET session_replication_role = replica;")
        
        # List of tables to truncate in order (respecting dependencies)
        tables = [
            'user_sessions',
            'price_history',
            'user_smallcase_investments',
            'smallcase_assets',
            'smallcases',
            'portfolio_holdings',
            'trading_transactions',
            'portfolios',
            'assets',
            'users'
        ]
        
        for table in tables:
            try:
                await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"✅ Truncated {table}")
            except Exception as e:
                print(f"⚠️  Warning: Could not truncate {table}: {e}")
        
        # Re-enable foreign key checks
        await conn.execute("SET session_replication_role = DEFAULT;")
        
        print("✅ Database reset completed!")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_database())
