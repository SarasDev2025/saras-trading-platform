# Database Schema - Entity Relationship Diagram

This document contains the Entity Relationship Diagram for the Saras Trading Platform database schema.

## Overview

The database schema supports a multi-broker trading platform with the following key components:

- **User Management**: Authentication, sessions, and audit logging
- **Broker Integration**: Multi-broker connections with proper alias handling
- **Portfolio Management**: User portfolios, holdings, and transactions
- **Smallcase System**: Investment baskets, constituents, and user investments
- **Trade Execution**: Execution runs and orders through broker APIs
- **Market Data**: Asset information and price history
- **Position Tracking**: Historical position snapshots

## Entity Relationship Diagram

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email
        varchar password_hash
        varchar first_name
        varchar last_name
        timestamp created_at
        timestamp updated_at
    }

    user_broker_connections {
        uuid id PK
        uuid user_id FK
        varchar broker_type
        varchar alias
        text api_key
        text api_secret
        jsonb credentials
        boolean paper_trading
        varchar status
        jsonb connection_metadata
        timestamp created_at
        timestamp updated_at
    }

    portfolios {
        uuid id PK
        uuid user_id FK
        varchar name
        text description
        numeric total_value
        numeric cash_balance
        varchar currency
        timestamp created_at
        timestamp updated_at
    }

    portfolio_holdings {
        uuid id PK
        uuid portfolio_id FK
        uuid asset_id FK
        numeric quantity
        numeric average_price
        numeric current_price
        numeric total_value
        numeric unrealized_pnl
        timestamp created_at
        timestamp updated_at
    }

    assets {
        uuid id PK
        varchar symbol
        varchar name
        varchar asset_type
        varchar exchange
        varchar currency
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    smallcases {
        uuid id PK
        varchar name
        text description
        varchar category
        numeric min_investment
        varchar risk_level
        boolean is_active
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    smallcase_constituents {
        uuid id PK
        uuid smallcase_id FK
        uuid asset_id FK
        numeric weight_percentage
        varchar rationale
        timestamp created_at
        timestamp updated_at
    }

    user_smallcase_investments {
        uuid id PK
        uuid user_id FK
        uuid smallcase_id FK
        uuid portfolio_id FK
        uuid broker_connection_id FK
        numeric investment_amount
        varchar status
        varchar execution_mode
        timestamp invested_at
        timestamp closed_at
        timestamp created_at
        timestamp updated_at
    }

    smallcase_execution_runs {
        uuid id PK
        uuid investment_id FK
        uuid broker_connection_id FK
        varchar run_type
        varchar status
        numeric total_amount
        jsonb execution_plan
        timestamp started_at
        timestamp completed_at
        timestamp created_at
        timestamp updated_at
    }

    smallcase_execution_orders {
        uuid id PK
        uuid execution_run_id FK
        uuid asset_id FK
        varchar side
        numeric quantity
        numeric price
        varchar order_type
        varchar status
        varchar broker_order_id
        jsonb order_metadata
        timestamp created_at
        timestamp updated_at
    }

    trading_transactions {
        uuid id PK
        uuid portfolio_id FK
        uuid asset_id FK
        varchar transaction_type
        numeric quantity
        numeric price
        numeric fees
        varchar broker_transaction_id
        timestamp transaction_date
        timestamp created_at
        timestamp updated_at
    }

    price_history {
        uuid id PK
        uuid asset_id FK
        numeric open_price
        numeric high_price
        numeric low_price
        numeric close_price
        numeric volume
        date price_date
        timestamp created_at
    }

    user_smallcase_position_history {
        uuid id PK
        uuid investment_id FK
        uuid asset_id FK
        uuid broker_connection_id FK
        numeric quantity
        numeric average_price
        numeric market_value
        numeric unrealized_pnl
        timestamp snapshot_date
        timestamp created_at
    }

    user_sessions {
        uuid id PK
        uuid user_id FK
        varchar session_token
        timestamp expires_at
        jsonb session_data
        timestamp created_at
        timestamp updated_at
    }

    audit_logs {
        uuid id PK
        varchar event_type
        uuid request_id
        timestamp timestamp
        inet client_ip
        text user_agent
        varchar path
        varchar method
        uuid user_id FK
        integer status_code
        numeric processing_time_ms
        boolean success
        text error_message
        timestamp created_at
    }

    %% Relationships
    users ||--o{ user_broker_connections : has
    users ||--o{ portfolios : owns
    users ||--o{ user_smallcase_investments : makes
    users ||--o{ user_sessions : has
    users ||--o{ audit_logs : generates

    portfolios ||--o{ portfolio_holdings : contains
    portfolios ||--o{ trading_transactions : has

    assets ||--o{ portfolio_holdings : held_in
    assets ||--o{ smallcase_constituents : part_of
    assets ||--o{ smallcase_execution_orders : traded
    assets ||--o{ trading_transactions : involves
    assets ||--o{ price_history : has
    assets ||--o{ user_smallcase_position_history : tracked

    smallcases ||--o{ smallcase_constituents : contains
    smallcases ||--o{ user_smallcase_investments : invested_in

    user_broker_connections ||--o{ user_smallcase_investments : used_for
    user_broker_connections ||--o{ smallcase_execution_runs : executes_via
    user_broker_connections ||--o{ user_smallcase_position_history : tracks

    user_smallcase_investments ||--o{ smallcase_execution_runs : triggers
    user_smallcase_investments ||--o{ user_smallcase_position_history : generates

    smallcase_execution_runs ||--o{ smallcase_execution_orders : contains
```

## Key Tables Description

### Core User Tables
- **users**: User account information and authentication
- **user_sessions**: JWT session management
- **audit_logs**: Security and request audit trail

### Broker Integration
- **user_broker_connections**: Multi-broker connections with unique aliases per user
  - Supports Alpaca, Zerodha, and other brokers
  - Each connection has a unique alias (e.g., "alpaca_primary")
  - Stores encrypted API keys and broker-specific metadata

### Portfolio Management
- **portfolios**: User portfolios containing multiple assets
- **portfolio_holdings**: Current positions in each portfolio
- **trading_transactions**: Historical trade records

### Smallcase System
- **smallcases**: Investment basket definitions
- **smallcase_constituents**: Assets and weights within each smallcase
- **user_smallcase_investments**: User investments in smallcases
- **smallcase_execution_runs**: Trade execution batches
- **smallcase_execution_orders**: Individual orders within execution runs

### Market Data
- **assets**: Asset master data (stocks, ETFs, etc.)
- **price_history**: Historical OHLCV data
- **user_smallcase_position_history**: Position snapshots over time

## Recent Schema Fixes

The following schema issues were recently resolved:

1. **Missing `updated_at` column** in `portfolio_holdings` table - Fixed via migration
2. **Column name mismatches** in broker selection service:
   - `broker_name` → `broker_type`
   - `is_active` → `status = 'active'`
   - `account_status` → `paper_trading`
3. **Missing `alias` field** in broker connection creation - Added with auto-generated values

## Database Migrations

Database migrations are stored in `/database/migrations/` and should be run in sequential order. The latest migration addresses the `portfolio_holdings.updated_at` column issue.