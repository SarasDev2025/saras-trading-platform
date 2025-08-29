#!/usr/bin/env python3
"""
Demo User Setup Script for Saras Trading Platform

This script creates a demo user and demo portfolio for testing and launch purposes.
The demo user will be used as the default user when no authentication is present.
"""

import asyncio
import asyncpg
import bcrypt
import uuid
from datetime import datetime, timezone

# Database connection settings
DATABASE_URL = "postgresql://trading_user:dev_password_123@localhost:5432/trading_dev"

# Demo user configuration
DEMO_USER_ID = "12345678-1234-1234-1234-123456789012"
DEMO_PORTFOLIO_ID = "87654321-4321-4321-4321-210987654321"

async def setup_demo_user():
    """Create demo user and demo portfolio"""
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database successfully")
        
        # Hash password for demo user
        password = "demo123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create demo user
        await conn.execute("""
            INSERT INTO users (id, username, email, password_hash, first_name, last_name, account_status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (username) DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                account_status = EXCLUDED.account_status,
                updated_at = NOW()
        """, 
            DEMO_USER_ID,
            "demo_user", 
            "demo@saras.trading",
            password_hash,
            "Demo",
            "User",
            "active",
            datetime.now(timezone.utc)
        )
        print("✅ Demo user created/updated successfully")
        
        # Create demo portfolio
        await conn.execute("""
            INSERT INTO portfolios (id, user_id, name, description, currency, total_value, cash_balance, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                currency = EXCLUDED.currency,
                total_value = EXCLUDED.total_value,
                cash_balance = EXCLUDED.cash_balance,
                updated_at = NOW()
        """,
            DEMO_PORTFOLIO_ID,
            DEMO_USER_ID,
            "Demo Portfolio",
            "Default demo portfolio for testing and launch",
            "USD",
            25000.0,
            5000.0,
            datetime.now(timezone.utc)
        )
        print("✅ Demo portfolio created/updated successfully")
        
        # Add some demo holdings to the portfolio
        demo_holdings = [
            ("AAPL", 10, 175.0, 1750.0, 170.0, 1700.0, 50.0),
            ("GOOGL", 3, 2580.0, 7740.0, 2500.0, 7500.0, 240.0),
            ("MSFT", 15, 420.0, 6300.0, 410.0, 6150.0, 150.0),
            ("TSLA", 5, 250.0, 1250.0, 240.0, 1200.0, 50.0),
            ("BTC", 0.5, 43000.0, 21500.0, 40000.0, 20000.0, 1500.0)
        ]
        
        for symbol, quantity, current_price, current_value, avg_cost, total_cost, unrealized_pnl in demo_holdings:
            # Get asset ID
            asset_result = await conn.fetchrow("SELECT id FROM assets WHERE symbol = $1", symbol)
            if asset_result:
                asset_id = asset_result['id']
                
                # Insert or update portfolio holding
                await conn.execute("""
                    INSERT INTO portfolio_holdings (
                        id, portfolio_id, asset_id, quantity, average_cost, 
                        total_cost, current_value, unrealized_pnl, last_updated
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (portfolio_id, asset_id) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        average_cost = EXCLUDED.average_cost,
                        total_cost = EXCLUDED.total_cost,
                        current_value = EXCLUDED.current_value,
                        unrealized_pnl = EXCLUDED.unrealized_pnl,
                        last_updated = NOW()
                """,
                    str(uuid.uuid4()),
                    DEMO_PORTFOLIO_ID,
                    asset_id,
                    quantity,
                    avg_cost,
                    total_cost,
                    current_value,
                    unrealized_pnl,
                    datetime.now(timezone.utc)
                )
                print(f"✅ Added demo holding for {symbol}")
        
        # Update portfolio total value
        total_holdings_value = sum(holding[3] for holding in demo_holdings)  # current_value
        cash_balance = 5000.0
        total_portfolio_value = total_holdings_value + cash_balance
        
        await conn.execute("""
            UPDATE portfolios 
            SET total_value = $1, updated_at = NOW()
            WHERE id = $2
        """, total_portfolio_value, DEMO_PORTFOLIO_ID)
        
        print(f"✅ Updated demo portfolio total value: ${total_portfolio_value:,.2f}")
        
        # Verify demo user setup
        user_result = await conn.fetchrow("""
            SELECT u.username, u.email, p.name as portfolio_name, p.total_value
            FROM users u
            JOIN portfolios p ON u.id = p.user_id
            WHERE u.id = $1
        """, DEMO_USER_ID)
        
        if user_result:
            print(f"\n📊 Demo User Setup Complete:")
            print(f"   Username: {user_result['username']}")
            print(f"   Email: {user_result['email']}")
            print(f"   Portfolio: {user_result['portfolio_name']}")
            print(f"   Total Value: ${user_result['total_value']:,.2f}")
            print(f"   User ID: {DEMO_USER_ID}")
            print(f"   Portfolio ID: {DEMO_PORTFOLIO_ID}")
        
        await conn.close()
        print("\n🎉 Demo user setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up demo user: {e}")
        raise

async def verify_demo_user():
    """Verify demo user exists and return user info"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        result = await conn.fetchrow("""
            SELECT 
                u.id, u.username, u.email, u.first_name, u.last_name,
                COUNT(p.id) as portfolio_count
            FROM users u
            LEFT JOIN portfolios p ON u.id = p.user_id
            WHERE u.id = $1
            GROUP BY u.id, u.username, u.email, u.first_name, u.last_name
        """, DEMO_USER_ID)
        
        await conn.close()
        
        if result:
            print(f"✅ Demo user verified:")
            print(f"   ID: {result['id']}")
            print(f"   Username: {result['username']}")
            print(f"   Name: {result['first_name']} {result['last_name']}")
            print(f"   Portfolios: {result['portfolio_count']}")
            return True
        else:
            print("❌ Demo user not found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying demo user: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        asyncio.run(verify_demo_user())
    else:
        asyncio.run(setup_demo_user())
