#!/usr/bin/env python3
"""
Mock Data Setup Script for Saras Trading Platform
Creates users, portfolios, assets, smallcases, and sample transactions
"""

import asyncio
import asyncpg
import bcrypt
from decimal import Decimal
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Any

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,  # Direct PostgreSQL port
    'user': 'trading_user',
    'password': 'dev_password_123',
    'database': 'trading_dev'
}

class MockDataGenerator:
    def __init__(self):
        self.conn = None
        
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(**DATABASE_CONFIG)
        
    async def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            await self.conn.close()
            
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
    async def create_users(self) -> Dict[str, str]:
        """Create sample users and return their IDs"""
        users_data = [
            {
                'email': 'admin@saras-trading.com',
                'username': 'admin',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'kyc_status': 'approved'
            },
            {
                'email': 'john.doe@example.com',
                'username': 'johndoe',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'kyc_status': 'approved'
            },
            {
                'email': 'jane.smith@example.com',
                'username': 'janesmith',
                'password': 'password123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'kyc_status': 'approved'
            },
            {
                'email': 'alice.johnson@example.com',
                'username': 'alicejohnson',
                'password': 'password123',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'kyc_status': 'pending'
            },
            {
                'email': 'bob.wilson@example.com',
                'username': 'bobwilson',
                'password': 'password123',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'kyc_status': 'approved'
            }
        ]
        
        user_ids = {}
        
        for user in users_data:
            password_hash = self.hash_password(user['password'])
            
            user_id = await self.conn.fetchval("""
                INSERT INTO users (email, username, password_hash, first_name, last_name, 
                                 email_verified, kyc_status, account_status)
                VALUES ($1, $2, $3, $4, $5, TRUE, $6, 'active')
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    kyc_status = EXCLUDED.kyc_status
                RETURNING id
            """, user['email'], user['username'], password_hash, 
                user['first_name'], user['last_name'], user['kyc_status'])
            
            user_ids[user['username']] = user_id
            print(f"Created/Updated user: {user['username']} ({user_id})")
            
        return user_ids
        
    async def create_assets(self) -> Dict[str, str]:
        """Create sample assets and return their IDs"""
        assets_data = [
            # Tech Stocks
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 175.50, 'sector': 'technology'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 2580.25, 'sector': 'technology'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 338.75, 'sector': 'technology'},
            {'symbol': 'TSLA', 'name': 'Tesla, Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 185.30, 'sector': 'technology'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 421.90, 'sector': 'technology'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 298.75, 'sector': 'technology'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 142.50, 'sector': 'technology'},
            {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'type': 'stock', 'exchange': 'NASDAQ', 'price': 425.80, 'sector': 'technology'},
            
            # Financial Stocks
            {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'type': 'stock', 'exchange': 'NYSE', 'price': 158.25, 'sector': 'financial'},
            {'symbol': 'BAC', 'name': 'Bank of America Corp.', 'type': 'stock', 'exchange': 'NYSE', 'price': 32.75, 'sector': 'financial'},
            {'symbol': 'GS', 'name': 'Goldman Sachs Group Inc.', 'type': 'stock', 'exchange': 'NYSE', 'price': 385.90, 'sector': 'financial'},
            
            # Healthcare Stocks
            {'symbol': 'JNJ', 'name': 'Johnson & Johnson', 'type': 'stock', 'exchange': 'NYSE', 'price': 162.40, 'sector': 'healthcare'},
            {'symbol': 'PFE', 'name': 'Pfizer Inc.', 'type': 'stock', 'exchange': 'NYSE', 'price': 28.85, 'sector': 'healthcare'},
            {'symbol': 'UNH', 'name': 'UnitedHealth Group Inc.', 'type': 'stock', 'exchange': 'NYSE', 'price': 528.75, 'sector': 'healthcare'},
            
            # Energy Stocks
            {'symbol': 'XOM', 'name': 'Exxon Mobil Corporation', 'type': 'stock', 'exchange': 'NYSE', 'price': 105.25, 'sector': 'energy'},
            {'symbol': 'CVX', 'name': 'Chevron Corporation', 'type': 'stock', 'exchange': 'NYSE', 'price': 148.90, 'sector': 'energy'},
            
            # Crypto
            {'symbol': 'BTC', 'name': 'Bitcoin', 'type': 'crypto', 'exchange': 'Binance', 'price': 43250.75, 'sector': 'crypto'},
            {'symbol': 'ETH', 'name': 'Ethereum', 'type': 'crypto', 'exchange': 'Binance', 'price': 2485.60, 'sector': 'crypto'},
            {'symbol': 'ADA', 'name': 'Cardano', 'type': 'crypto', 'exchange': 'Binance', 'price': 0.485, 'sector': 'crypto'},
            {'symbol': 'SOL', 'name': 'Solana', 'type': 'crypto', 'exchange': 'Binance', 'price': 98.25, 'sector': 'crypto'},
        ]
        
        asset_ids = {}
        
        for asset in assets_data:
            metadata = json.dumps({'sector': asset['sector'], 'market_cap': 'large'})
            
            asset_id = await self.conn.fetchval("""
                INSERT INTO assets (symbol, name, asset_type, exchange, currency, 
                                  current_price, price_updated_at, metadata)
                VALUES ($1, $2, $3, $4, 'USD', $5, CURRENT_TIMESTAMP, $6)
                ON CONFLICT (symbol) DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    price_updated_at = CURRENT_TIMESTAMP,
                    metadata = EXCLUDED.metadata
                RETURNING id
            """, asset['symbol'], asset['name'], asset['type'], 
                asset['exchange'], asset['price'], metadata)
            
            asset_ids[asset['symbol']] = asset_id
            print(f"Created/Updated asset: {asset['symbol']} ({asset_id})")
            
        return asset_ids
        
    async def create_portfolios(self, user_ids: Dict[str, str]) -> Dict[str, str]:
        """Create portfolios for users"""
        portfolio_ids = {}
        
        for username, user_id in user_ids.items():
            cash_balance = 100000.00 if username == 'admin' else 10000.00
            
            portfolio_id = await self.conn.fetchval("""
                INSERT INTO portfolios (user_id, name, description, cash_balance, total_value)
                VALUES ($1, $2, $3, $4, $4)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, user_id, 
                f"{username.title()}'s Portfolio",
                f"Default portfolio for {username}",
                cash_balance)
            
            if not portfolio_id:
                portfolio_id = await self.conn.fetchval("""
                    SELECT id FROM portfolios WHERE user_id = $1 LIMIT 1
                """, user_id)
            
            portfolio_ids[username] = portfolio_id
            print(f"Created/Found portfolio for {username}: {portfolio_id}")
            
        return portfolio_ids
        
    async def create_smallcases(self, user_ids: Dict[str, str], asset_ids: Dict[str, str]) -> Dict[str, str]:
        """Create smallcases with asset allocations"""
        admin_id = user_ids['admin']
        
        smallcases_data = [
            {
                'name': 'Tech Growth',
                'description': 'High-growth technology companies with strong fundamentals',
                'theme': 'technology',
                'min_investment': 5000.00,
                'expected_return': 15.50,
                'risk_level': 'high',
                'assets': [
                    {'symbol': 'AAPL', 'weight': 25.00},
                    {'symbol': 'GOOGL', 'weight': 20.00},
                    {'symbol': 'MSFT', 'weight': 20.00},
                    {'symbol': 'NVDA', 'weight': 15.00},
                    {'symbol': 'META', 'weight': 12.00},
                    {'symbol': 'NFLX', 'weight': 8.00}
                ]
            },
            {
                'name': 'Finance Stability',
                'description': 'Stable financial institutions with consistent dividends',
                'theme': 'financial',
                'min_investment': 3000.00,
                'expected_return': 8.25,
                'risk_level': 'medium',
                'assets': [
                    {'symbol': 'JPM', 'weight': 35.00},
                    {'symbol': 'BAC', 'weight': 30.00},
                    {'symbol': 'GS', 'weight': 25.00},
                    {'symbol': 'XOM', 'weight': 10.00}
                ]
            },
            {
                'name': 'Healthcare Defensive',
                'description': 'Defensive healthcare stocks for stable returns',
                'theme': 'healthcare',
                'min_investment': 4000.00,
                'expected_return': 10.75,
                'risk_level': 'low',
                'assets': [
                    {'symbol': 'JNJ', 'weight': 40.00},
                    {'symbol': 'UNH', 'weight': 35.00},
                    {'symbol': 'PFE', 'weight': 25.00}
                ]
            },
            {
                'name': 'Crypto Basket',
                'description': 'Diversified cryptocurrency portfolio',
                'theme': 'crypto',
                'min_investment': 1000.00,
                'expected_return': 25.00,
                'risk_level': 'high',
                'assets': [
                    {'symbol': 'BTC', 'weight': 50.00},
                    {'symbol': 'ETH', 'weight': 30.00},
                    {'symbol': 'SOL', 'weight': 15.00},
                    {'symbol': 'ADA', 'weight': 5.00}
                ]
            }
        ]
        
        smallcase_ids = {}
        
        for smallcase in smallcases_data:
            # Create smallcase
            smallcase_id = await self.conn.fetchval("""
                INSERT INTO smallcases (name, description, theme, minimum_investment, 
                                      expected_return, risk_level, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, smallcase['name'], smallcase['description'], smallcase['theme'],
                smallcase['min_investment'], smallcase['expected_return'],
                smallcase['risk_level'], admin_id)
            
            if not smallcase_id:
                smallcase_id = await self.conn.fetchval("""
                    SELECT id FROM smallcases WHERE name = $1
                """, smallcase['name'])
            
            smallcase_ids[smallcase['name']] = smallcase_id
            
            # Add assets to smallcase
            for asset_allocation in smallcase['assets']:
                symbol = asset_allocation['symbol']
                weight = asset_allocation['weight']
                
                if symbol in asset_ids:
                    await self.conn.execute("""
                        INSERT INTO smallcase_assets (smallcase_id, asset_id, weight_percentage)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (smallcase_id, asset_id) DO UPDATE SET
                            weight_percentage = EXCLUDED.weight_percentage
                    """, smallcase_id, asset_ids[symbol], weight)
            
            print(f"Created/Updated smallcase: {smallcase['name']} ({smallcase_id})")
            
        return smallcase_ids
        
    async def create_sample_transactions(self, user_ids: Dict[str, str], 
                                       portfolio_ids: Dict[str, str], 
                                       asset_ids: Dict[str, str]):
        """Create sample trading transactions"""
        transactions_data = [
            # John's transactions
            {
                'username': 'johndoe',
                'transactions': [
                    {'symbol': 'AAPL', 'type': 'buy', 'quantity': 10, 'price': 170.00, 'days_ago': 30},
                    {'symbol': 'GOOGL', 'type': 'buy', 'quantity': 2, 'price': 2500.00, 'days_ago': 25},
                    {'symbol': 'BTC', 'type': 'buy', 'quantity': 0.1, 'price': 40000.00, 'days_ago': 20},
                    {'symbol': 'AAPL', 'type': 'sell', 'quantity': 2, 'price': 175.00, 'days_ago': 10}
                ]
            },
            # Jane's transactions
            {
                'username': 'janesmith',
                'transactions': [
                    {'symbol': 'MSFT', 'type': 'buy', 'quantity': 15, 'price': 330.00, 'days_ago': 28},
                    {'symbol': 'ETH', 'type': 'buy', 'quantity': 2, 'price': 2200.00, 'days_ago': 22},
                    {'symbol': 'JPM', 'type': 'buy', 'quantity': 20, 'price': 155.00, 'days_ago': 15},
                    {'symbol': 'NVDA', 'type': 'buy', 'quantity': 5, 'price': 400.00, 'days_ago': 12}
                ]
            }
        ]
        
        for user_data in transactions_data:
            username = user_data['username']
            user_id = user_ids[username]
            portfolio_id = portfolio_ids[username]
            
            for tx in user_data['transactions']:
                symbol = tx['symbol']
                if symbol not in asset_ids:
                    continue
                    
                asset_id = asset_ids[symbol]
                quantity = Decimal(str(tx['quantity']))
                price = Decimal(str(tx['price']))
                total_amount = quantity * price
                fees = total_amount * Decimal('0.001')  # 0.1% fees
                net_amount = total_amount + fees if tx['type'] == 'buy' else total_amount - fees
                
                transaction_date = datetime.now() - timedelta(days=tx['days_ago'])
                
                await self.conn.execute("""
                    INSERT INTO trading_transactions 
                    (user_id, portfolio_id, asset_id, transaction_type, quantity, 
                     price_per_unit, total_amount, fees, net_amount, status, 
                     transaction_date, settlement_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'executed', $10, $10)
                    ON CONFLICT DO NOTHING
                """, user_id, portfolio_id, asset_id, tx['type'], quantity,
                    price, total_amount, fees, net_amount, transaction_date)
                
                print(f"Created transaction: {username} {tx['type']} {quantity} {symbol} @ ${price}")
        
    async def update_portfolio_holdings(self, portfolio_ids: Dict[str, str]):
        """Calculate and update portfolio holdings based on transactions"""
        for username, portfolio_id in portfolio_ids.items():
            # Calculate holdings from transactions
            await self.conn.execute("""
                INSERT INTO portfolio_holdings (portfolio_id, asset_id, quantity, average_cost, total_cost)
                SELECT 
                    portfolio_id,
                    asset_id,
                    SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as net_quantity,
                    AVG(CASE WHEN transaction_type = 'buy' THEN price_per_unit END) as avg_cost,
                    SUM(CASE WHEN transaction_type = 'buy' THEN total_amount ELSE -total_amount END) as total_cost
                FROM trading_transactions 
                WHERE portfolio_id = $1 AND status = 'executed'
                GROUP BY portfolio_id, asset_id
                HAVING SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) > 0
                ON CONFLICT (portfolio_id, asset_id) DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    average_cost = EXCLUDED.average_cost,
                    total_cost = EXCLUDED.total_cost
            """, portfolio_id)
            
            # Update current values and unrealized P&L
            await self.conn.execute("""
                UPDATE portfolio_holdings 
                SET 
                    current_value = quantity * (SELECT current_price FROM assets WHERE assets.id = portfolio_holdings.asset_id),
                    unrealized_pnl = (quantity * (SELECT current_price FROM assets WHERE assets.id = portfolio_holdings.asset_id)) - total_cost,
                    last_updated = CURRENT_TIMESTAMP
                WHERE portfolio_id = $1
            """, portfolio_id)
            
            # Update portfolio total value
            await self.conn.execute("""
                UPDATE portfolios 
                SET 
                    total_value = cash_balance + COALESCE((
                        SELECT SUM(current_value) 
                        FROM portfolio_holdings 
                        WHERE portfolio_holdings.portfolio_id = portfolios.id
                    ), 0),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, portfolio_id)
            
            print(f"Updated holdings for {username}'s portfolio")
    
    async def generate_price_history(self, asset_ids: Dict[str, str]):
        """Generate sample price history for assets"""
        for symbol, asset_id in asset_ids.items():
            # Get current price
            current_price = await self.conn.fetchval("""
                SELECT current_price FROM assets WHERE id = $1
            """, asset_id)
            
            if not current_price:
                continue
                
            # Generate 30 days of price history
            for days_back in range(30, 0, -1):
                # Add some random variation (±10%)
                import random
                variation = (random.random() - 0.5) * 0.2  # ±10%
                historical_price = float(current_price) * (1 + variation)
                volume = random.randint(100000, 10000000)
                
                timestamp = datetime.now() - timedelta(days=days_back)
                
                await self.conn.execute("""
                    INSERT INTO price_history (asset_id, price, volume, timestamp, interval_type)
                    VALUES ($1, $2, $3, $4, '1d')
                    ON CONFLICT DO NOTHING
                """, asset_id, historical_price, volume, timestamp)
        
        print("Generated price history for all assets")

async def main():
    """Main function to set up all mock data"""
    generator = MockDataGenerator()
    
    try:
        await generator.connect()
        print("Connected to database")
        
        # Create all mock data
        print("\n1. Creating users...")
        user_ids = await generator.create_users()
        
        print("\n2. Creating assets...")
        asset_ids = await generator.create_assets()
        
        print("\n3. Creating portfolios...")
        portfolio_ids = await generator.create_portfolios(user_ids)
        
        print("\n4. Creating smallcases...")
        smallcase_ids = await generator.create_smallcases(user_ids, asset_ids)
        
        print("\n5. Creating sample transactions...")
        await generator.create_sample_transactions(user_ids, portfolio_ids, asset_ids)
        
        print("\n6. Updating portfolio holdings...")
        await generator.update_portfolio_holdings(portfolio_ids)
        
        print("\n7. Generating price history...")
        await generator.generate_price_history(asset_ids)
        
        print("\n✅ Mock data setup completed successfully!")
        print(f"Created {len(user_ids)} users, {len(asset_ids)} assets, {len(portfolio_ids)} portfolios, {len(smallcase_ids)} smallcases")
        
    except Exception as e:
        print(f"❌ Error setting up mock data: {e}")
        raise
    finally:
        await generator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
