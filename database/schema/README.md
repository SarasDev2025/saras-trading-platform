# Database Schema Organization

This directory contains the organized database schema for the SARAS Trading Platform, extracted and organized from the full database dump.

## Schema Files

### 01-extensions.sql
PostgreSQL extensions required by the database:
- `pgcrypto` - Cryptographic functions
- `uuid-ossp` - UUID generation functions

### 02-functions.sql
Database functions used for triggers and automation (4 functions):
- `initialize_virtual_money()` - Initializes virtual money and paper trading stats for new users
- `update_last_activity()` - Updates last activity timestamp
- `update_paper_trading_stats()` - Updates paper trading statistics when orders are filled
- `update_updated_at_column()` - Generic trigger function to update updated_at timestamps

### 03-core-tables.sql
Core tables for users, portfolios, and assets (5 tables):
- `users` - User accounts and authentication
- `assets` - Stock/crypto/forex assets with regional support (US/IN)
- `portfolios` - User portfolio configurations
- `price_history` - Historical price data for assets
- `virtual_money_config` - Paper trading virtual money configuration

### 04-trading-tables.sql
Trading and order management tables (6 tables):
- `basket_orders` - Basket order tracking
- `oco_orders` - One-Cancels-Other orders
- `paper_orders` - Paper trading orders
- `paper_trading_stats` - Aggregated paper trading statistics
- `portfolio_holdings` - Current holdings in portfolios
- `trading_transactions` - All trading transactions (buy/sell/deposits/withdrawals)

### 05-smallcase-tables.sql
Smallcase investment product tables (7 tables):
- `smallcases` - Smallcase definitions with regional support
- `smallcase_constituents` - Asset composition of smallcases
- `smallcase_execution_orders` - Individual orders in smallcase executions
- `smallcase_execution_runs` - Execution run tracking (paper/live)
- `smallcase_performance` - Performance metrics and NAV history
- `user_smallcase_investments` - User investments in smallcases
- `user_smallcase_position_history` - Historical record of closed positions

### 06-auth-tables.sql
Authentication, sessions, and security logging (9 tables):
- `audit_logs` - General audit trail
- `login_attempts` - Login attempt tracking
- `rate_limit_violations` - Rate limiting violations
- `refresh_tokens` - JWT refresh token management
- `security_logs` - Security event logging
- `suspicious_activities` - Flagged suspicious activities
- `token_blacklist` - Revoked tokens
- `token_validations` - Token validation attempts
- `user_sessions` - Active user sessions

### 07-broker-tables.sql
Broker integration and advanced orders (2 tables):
- `gtt_orders` - Good-Till-Triggered orders (Zerodha)
- `user_broker_connections` - User broker API connections (Zerodha/Alpaca)

### 08-dividend-tables.sql
Dividend management and DRIP system (7 tables):
- `dividend_bulk_orders` - Aggregated bulk orders for DRIP execution
- `dividend_declarations` - Dividend announcements
- `drip_bulk_order_allocations` - Allocation of bulk orders to individual users
- `drip_transactions` - Individual DRIP reinvestment transactions
- `user_dividend_payments` - User dividend payments
- `user_drip_preferences` - User DRIP preferences per asset
- `user_position_snapshots` - Position snapshots for dividend eligibility

### 09-triggers-indexes.sql
Database triggers and indexes (18 triggers, 117 indexes):

**Triggers:**
- Update triggers for `updated_at` columns on 16 tables
- `trigger_init_virtual_money` - Initializes virtual money for new users
- `trigger_update_paper_stats` - Updates paper trading stats on order fills
- `update_user_sessions_last_activity` - Updates session activity timestamps

**Indexes:**
- Performance indexes on frequently queried columns
- Foreign key indexes
- Composite indexes for common query patterns
- Unique indexes for business constraints

## Table Count Summary

| Category | Tables | Purpose |
|----------|--------|---------|
| Core Tables | 5 | Users, assets, portfolios, pricing |
| Trading Tables | 6 | Orders, transactions, holdings |
| Smallcase Tables | 7 | Investment products, execution |
| Auth/Security | 9 | Sessions, tokens, audit logs |
| Broker Integration | 2 | Broker connections, GTT orders |
| Dividend Management | 7 | Dividends, DRIP automation |
| **Total** | **36** | **All database tables** |

## Features Supported

### Multi-Region Support
- **US Market**: NASDAQ/NYSE stocks, Alpaca broker
- **India Market**: NSE/BSE stocks, Zerodha broker
- Regional smallcases with appropriate broker support

### Trading Modes
- **Paper Trading**: Virtual money, simulated orders
- **Live Trading**: Real broker integration (Zerodha/Alpaca)

### Advanced Order Types
- Market, Limit, Stop, Stop-Limit orders
- GTT (Good-Till-Triggered) orders
- OCO (One-Cancels-Other) orders
- Basket orders

### Dividend Management
- Automatic dividend tracking
- DRIP (Dividend Reinvestment Program)
- Bulk order aggregation and execution
- Position snapshot tracking

### Security Features
- Comprehensive audit logging
- Security event tracking
- Token blacklisting
- Rate limiting
- Suspicious activity detection

## Usage

To initialize the database with this schema, run the files in order:

```bash
psql -U trading_user -d trading_dev -f 01-extensions.sql
psql -U trading_user -d trading_dev -f 02-functions.sql
psql -U trading_user -d trading_dev -f 03-core-tables.sql
psql -U trading_user -d trading_dev -f 04-trading-tables.sql
psql -U trading_user -d trading_dev -f 05-smallcase-tables.sql
psql -U trading_user -d trading_dev -f 06-auth-tables.sql
psql -U trading_user -d trading_dev -f 07-broker-tables.sql
psql -U trading_user -d trading_dev -f 08-dividend-tables.sql
psql -U trading_user -d trading_dev -f 09-triggers-indexes.sql
```

Or use the initialization script if available in `database/init/`.

## Notes

- All tables use UUID primary keys
- Timestamps are stored with timezone awareness
- JSONB is used extensively for flexible metadata storage
- Foreign key constraints are included in table definitions
- Indexes are optimized for common query patterns

---

Generated from full database dump on 2025-10-05
