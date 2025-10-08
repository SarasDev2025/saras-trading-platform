# Saras Trading Platform - Database Setup

Complete guide for setting up the PostgreSQL database for the Saras Trading Platform.

## 📋 Overview

The database uses **PostgreSQL 12+** and supports multi-region trading (India, US, UK) with paper and live trading modes.

**Key Features:**
- Multi-region support (IN, US, GB)
- Paper vs Live trading modes
- Smallcases (basket investing)
- Dividend management with DRIP
- GTT orders (Zerodha)
- Broker integrations (Zerodha, Alpaca, Interactive Brokers)

## 📁 Directory Structure

```
database/
├── README.md                    # This file
├── init/                        # Initial database setup (runs on fresh DB)
│   ├── 00-init.sql             # Main orchestration script
│   ├── schema/                  # Table definitions
│   │   ├── 01-extensions.sql   # PostgreSQL extensions (uuid-ossp, etc.)
│   │   ├── 02-functions.sql    # Helper functions (update_updated_at)
│   │   ├── 03-core-tables.sql  # Users, assets, portfolios
│   │   ├── 04-trading-tables.sql  # Orders, transactions
│   │   ├── 05-smallcase-tables.sql # Smallcases, investments
│   │   ├── 06-auth-tables.sql  # Sessions, refresh tokens
│   │   ├── 07-broker-tables.sql # Broker connections
│   │   ├── 08-dividend-tables.sql # Dividend tracking
│   │   └── 09-triggers-indexes.sql # Performance & automation
│   └── seed/                    # Initial data
│       ├── 01-initial-config.sql
│       ├── 02-indian-stocks.sql  # NSE stocks
│       ├── 03-us-stocks.sql      # NYSE/NASDAQ stocks
│       ├── 04-indian-smallcases.sql
│       └── 05-us-smallcases.sql
├── migrations/                  # Schema changes (post-setup)
│   ├── 11-add-user-region.sql
│   ├── 12-add-user-trading-mode.sql
│   ├── 13-add-portfolio-trading-mode.sql
│   ├── 14-add-user-region.sql
│   ├── 15-add-broker-configurations.sql
│   └── 16-complete-smallcase-constituents.sql
└── backups/                     # Database backups
```

## 🚀 Quick Start

### Method 1: Docker Compose (Recommended)

The database is automatically initialized when you start the services:

```bash
# From project root
docker-compose up -d

# The database will automatically:
# 1. Create the database 'trading_dev'
# 2. Run all schema scripts in order
# 3. Load seed data (stocks, smallcases)
# 4. Apply migrations
```

**Database Access:**
- **Host:** localhost
- **Port:** 5432 (mapped from container)
- **Database:** trading_dev
- **User:** trading_user
- **Password:** dev_password_123

**PgBouncer (Connection Pool):**
- **Port:** 6432
- **Use this in applications** for connection pooling

### Method 2: Manual Setup (Development)

For local PostgreSQL installation:

```bash
# 1. Create database and user
psql -U postgres -c "CREATE DATABASE trading_dev;"
psql -U postgres -c "CREATE USER trading_user WITH PASSWORD 'dev_password_123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE trading_dev TO trading_user;"

# 2. Run initialization script
psql -U trading_user -d trading_dev -f database/init/00-init.sql

# 3. Apply migrations (in order)
psql -U trading_user -d trading_dev -f database/migrations/11-add-user-region.sql
psql -U trading_user -d trading_dev -f database/migrations/12-add-user-trading-mode.sql
psql -U trading_user -d trading_dev -f database/migrations/13-add-portfolio-trading-mode.sql
psql -U trading_user -d trading_dev -f database/migrations/14-add-user-region.sql
psql -U trading_user -d trading_dev -f database/migrations/15-add-broker-configurations.sql
psql -U trading_user -d trading_dev -f database/migrations/16-complete-smallcase-constituents.sql
```

### Method 3: Apply Migrations (Existing Database)

If you already have a database and need to apply migrations:

```bash
# Via Docker
docker-compose exec -T postgres psql -U trading_user -d trading_dev < database/migrations/16-complete-smallcase-constituents.sql

# Via local psql
psql -U trading_user -d trading_dev -f database/migrations/16-complete-smallcase-constituents.sql
```

## 📊 Schema Execution Order

The `init/00-init.sql` script orchestrates all setup in this order:

### Phase 1: Extensions & Configuration
- **01-extensions.sql** - Enables UUID generation, pgcrypto

### Phase 2: Functions
- **02-functions.sql** - `update_updated_at()` trigger function

### Phase 3: Table Creation
1. **03-core-tables.sql** - Users, assets, portfolios, holdings
2. **06-auth-tables.sql** - User sessions, refresh tokens
3. **07-broker-tables.sql** - User broker connections, credentials
4. **04-trading-tables.sql** - Orders, transactions, executions
5. **05-smallcase-tables.sql** - Smallcases, constituents, investments
6. **08-dividend-tables.sql** - Dividend declarations, payments, DRIP

### Phase 4: Triggers & Indexes
- **09-triggers-indexes.sql** - Performance indexes, updated_at triggers

### Phase 5: Seed Data
1. **01-initial-config.sql** - System configuration
2. **02-indian-stocks.sql** - 100+ NSE stocks (RELIANCE, TCS, INFY, etc.)
3. **03-us-stocks.sql** - 100+ US stocks (AAPL, TSLA, GOOGL, etc.)
4. **04-indian-smallcases.sql** - 5 India smallcases with constituents
5. **05-us-smallcases.sql** - 12 US smallcases with constituents

## 🔄 Migrations Applied

After initial setup, these migrations have been applied:

| Migration | Description | Date |
|-----------|-------------|------|
| 11-add-user-region.sql | Add region column to users (IN/US/GB) | 2025-10-06 |
| 12-add-user-trading-mode.sql | Add trading_mode to users (paper/live) | 2025-10-06 |
| 13-add-portfolio-trading-mode.sql | Add trading_mode to portfolios | 2025-10-06 |
| 14-add-user-region.sql | Refinement of region handling | 2025-10-06 |
| 15-add-broker-configurations.sql | Broker URLs per region & mode | 2025-10-06 |
| 16-complete-smallcase-constituents.sql | Complete smallcase stock data | 2025-10-07 |

**Purpose of Migrations:**
- Enable **paper vs live trading mode** separation
- Support **multi-region trading** (India, US, UK)
- Configure **broker-specific settings** per region
- Complete **smallcase constituent data** for both regions

## 📈 Data Loaded

After initialization and migrations, the database contains:

**Assets:**
- ~100 Indian stocks (NSE) - RELIANCE, TCS, HDFCBANK, INFY, etc.
- ~100 US stocks (NYSE/NASDAQ) - AAPL, TSLA, GOOGL, MSFT, NVDA, etc.

**Smallcases:**

*India (5 smallcases):*
- Nifty 50 Core (10 stocks)
- IT & Technology India (8 stocks)
- Banking & Finance India (8 stocks)
- Pharma & Healthcare India (8 stocks)
- Auto & EV India (8 stocks)

*US (12 smallcases):*
- S&P 500 Core (10 stocks)
- Magnificent 7 Tech (7 stocks)
- FAANG Leaders (5 stocks)
- Cloud & SaaS (10 stocks)
- Semiconductors & AI (9 stocks)
- EV & Clean Energy (10 stocks)
- Energy & Oil (9 stocks)
- Healthcare Innovation (8 stocks)
- Banking & Financials (7 stocks)
- Consumer Discretionary (8 stocks)
- Dividend Aristocrats US (8 stocks)
- All Weather US Portfolio (10 stocks)

**Broker Configurations:**
- Zerodha (India) - Paper & Live
- Alpaca (US) - Paper & Live
- Interactive Brokers (UK) - Paper & Live

## 🔍 Verification Queries

Check that everything is set up correctly:

```sql
-- Count tables
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Check assets by region
SELECT region, COUNT(*) as count
FROM assets
GROUP BY region;

-- Check smallcases with constituents
SELECT
    s.name,
    s.region,
    COUNT(sc.id) as constituents
FROM smallcases s
LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id
GROUP BY s.id, s.name, s.region
ORDER BY s.region, s.name;

-- Verify broker configurations
SELECT broker_name, region, trading_mode, api_url
FROM broker_configurations
ORDER BY region, trading_mode;

-- Check for empty smallcases (should be 0)
SELECT COUNT(*) as empty_smallcases
FROM smallcases s
LEFT JOIN smallcase_constituents sc ON s.id = sc.smallcase_id
GROUP BY s.id
HAVING COUNT(sc.id) = 0;
```

Expected results:
- **Tables:** ~30+ tables
- **Assets:** 200+ stocks
- **Smallcases:** 17 total (5 India + 12 US)
- **All smallcases should have constituents** (empty_smallcases = 0)
- **Broker configs:** 6 entries (3 brokers × 2 modes)

## 🔧 Troubleshooting

### Issue: Database already exists

```bash
# Drop and recreate
docker-compose down -v
docker-compose up -d
```

### Issue: Permission denied

```bash
# Grant permissions
docker-compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE trading_dev TO trading_user;"
docker-compose exec postgres psql -U postgres -d trading_dev -c "GRANT ALL ON SCHEMA public TO trading_user;"
```

### Issue: Migrations already applied

Check if migration was applied:
```sql
SELECT * FROM smallcases WHERE name = 'Nifty 50 Core';
SELECT * FROM broker_configurations WHERE broker_name = 'zerodha';
```

### Issue: Empty smallcases

Run migration 16 to fix:
```bash
docker-compose exec -T postgres psql -U trading_user -d trading_dev < database/migrations/16-complete-smallcase-constituents.sql
```

### Full Database Reset

```bash
# Complete reset (WARNING: Deletes all data)
docker-compose down -v
rm -rf database/backups/*
docker-compose up -d

# Wait for initialization
docker-compose logs postgres | grep "database system is ready"
```

## 🔐 Security Notes

**Development Credentials (Change in Production):**
- Database password: `dev_password_123`
- PgBouncer auth: `trading_user`

**Production Checklist:**
- [ ] Change database password
- [ ] Use environment variables for credentials
- [ ] Enable SSL connections
- [ ] Configure PgBouncer for production
- [ ] Set up database backups
- [ ] Enable audit logging
- [ ] Restrict network access

## 📝 Environment Variables

Required environment variables (in `.env`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://trading_user:dev_password_123@localhost:6432/trading_dev
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=trading_dev

# PgBouncer
PGBOUNCER_AUTH_USER=trading_user
PGBOUNCER_AUTH_PASSWORD=dev_password_123
```

## 🔗 Related Documentation

- [Schema Documentation](init/schema/README.md) - Detailed table schemas
- [CLAUDE.md](../CLAUDE.md) - Development commands
- [Docker Compose](../docker-compose.yaml) - Service configuration

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs postgres`
2. Verify migrations applied correctly
3. Run verification queries above
4. Check [GitHub Issues](https://github.com/your-repo/issues)
