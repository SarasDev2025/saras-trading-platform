# Mock Data Scripts for Saras Trading Platform

This directory contains scripts to set up and manage mock data for the trading platform.

## Scripts Overview

### 1. `setup_mock_data.py`
Main script that creates comprehensive mock data including:
- **Users**: Admin user + regular users (John, Jane, Alice, Bob)
- **Assets**: Stocks (tech, finance, healthcare, energy) + cryptocurrencies
- **Portfolios**: Default portfolios for each user with cash balances
- **Smallcases**: Predefined investment themes (Tech Growth, Finance Stability, Healthcare Defensive, Crypto Basket)
- **Transactions**: Sample buy/sell transactions with realistic dates
- **Holdings**: Calculated portfolio positions based on transactions
- **Price History**: 30 days of historical price data for all assets

### 2. `reset_database.py`
Utility script to completely reset the database by truncating all tables while respecting foreign key constraints.

### 3. `run_setup.sh`
Convenience bash script that:
- Creates Python virtual environment
- Installs dependencies
- Checks database connectivity
- Resets database (optional)
- Runs mock data generation
- Provides helpful commands for verification

## Quick Start

```bash
# From project root directory
./scripts/run_setup.sh
```

## Manual Setup

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Reset database (optional)
python3 scripts/reset_database.py

# Generate mock data
python3 scripts/setup_mock_data.py
```

## Generated Data

### Users
- **admin@saras-trading.com** (admin) - $100,000 cash balance
- **john.doe@example.com** (johndoe) - $10,000 cash balance
- **jane.smith@example.com** (janesmith) - $10,000 cash balance
- **alice.johnson@example.com** (alicejohnson) - $10,000 cash balance
- **bob.wilson@example.com** (bobwilson) - $10,000 cash balance

All users have password: `password123` (admin: `admin123`)

### Smallcases
1. **Tech Growth** - High-growth tech stocks (AAPL, GOOGL, MSFT, NVDA, META, NFLX)
2. **Finance Stability** - Financial institutions (JPM, BAC, GS, XOM)
3. **Healthcare Defensive** - Healthcare stocks (JNJ, UNH, PFE)
4. **Crypto Basket** - Cryptocurrency portfolio (BTC, ETH, SOL, ADA)

### Sample Transactions
- John: AAPL, GOOGL, BTC positions with some trading history
- Jane: MSFT, ETH, JPM, NVDA positions

## Verification Commands

```bash
# View users
docker-compose exec postgres psql -U trading_user -d trading_dev -c "SELECT username, email, kyc_status FROM users;"

# View assets
docker-compose exec postgres psql -U trading_user -d trading_dev -c "SELECT symbol, name, current_price FROM assets ORDER BY symbol;"

# View portfolios
docker-compose exec postgres psql -U trading_user -d trading_dev -c "SELECT u.username, p.name, p.total_value FROM portfolios p JOIN users u ON p.user_id = u.id;"

# View smallcases
docker-compose exec postgres psql -U trading_user -d trading_dev -c "SELECT name, theme, minimum_investment, expected_return FROM smallcases;"

# View holdings
docker-compose exec postgres psql -U trading_user -d trading_dev -c "SELECT u.username, a.symbol, ph.quantity, ph.current_value, ph.unrealized_pnl FROM portfolio_holdings ph JOIN portfolios p ON ph.portfolio_id = p.id JOIN users u ON p.user_id = u.id JOIN assets a ON ph.asset_id = a.id;"
```

## Configuration

Database connection settings are in each script:
- Host: localhost
- Port: 6432 (PgBouncer)
- User: trading_user
- Password: dev_password_123
- Database: trading_dev

## Dependencies

The scripts require the following Python packages:
- `asyncpg` - PostgreSQL async driver
- `bcrypt` - Password hashing

Install them using:
```bash
pip install asyncpg bcrypt
```

## Demo User Setup

For launch and testing purposes, a demo user is automatically configured:

### Demo User Credentials
- **User ID**: `12345678-1234-1234-1234-123456789012`
- **Username**: `demo_user`
- **Email**: `demo@saras.trading`
- **Password**: `demo123`
- **Portfolio ID**: `87654321-4321-4321-4321-210987654321`

### Demo Portfolio Holdings
- **AAPL**: 10 shares @ $175.50
- **GOOGL**: 3 shares @ $2,580.25
- **MSFT**: 15 shares @ $338.75
- **TSLA**: 5 shares @ $185.30
- **BTC**: 0.5 units @ $43,250.75
- **Cash Balance**: $5,000.00
- **Total Portfolio Value**: $43,540.00

### Setup Demo User
```bash
cd scripts
python3 setup_demo_user.py
```

### Verify Demo User
```bash
cd scripts
python3 setup_demo_user.py verify
```

The API Gateway automatically uses the demo user when no authentication is present, and handles placeholder portfolio IDs like "portfolio-id" by mapping them to the demo portfolio.
