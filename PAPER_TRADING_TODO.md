# Paper Trading System - TODO & Implementation Plan

## 📊 Current Implementation Status

### ✅ Existing Components

#### 1. Database Schema
- ✅ `portfolios.cash_balance` - Cash balance tracking (DECIMAL type)
- ✅ `user_holdings` - Stock holdings with quantity and average price
- ✅ `transactions` - Transaction history (buy/sell)
- ✅ `user_broker_connections.paper_trading` - Paper trading mode flag
- ✅ `portfolios.total_value` - Total portfolio value calculation

#### 2. Core Services
- ✅ `TradingService` (`api-gateway/services/trading_service.py`)
  - Execute trades via broker APIs
  - Transaction recording
  - Portfolio updates after trades
- ✅ `PortfolioService` (`api-gateway/services/portfolio_service.py`)
  - Holdings management
  - Portfolio value calculation
  - Transaction history
- ✅ `ZerodhaBroker` with paper trading mode
  - Mock order placement when `paper_trading=True`
  - No real API calls in paper mode
- ✅ `AlpacaBroker` integration
  - Actual paper trading API support
  - Real Alpaca paper trading endpoints

#### 3. Frontend Components
- ✅ Dashboard portfolio overview
- ✅ Holdings display
- ✅ Recent transactions list
- ✅ Portfolio charts

---

## 🏗️ Paper Trading Architecture

### Virtual Money Flow

```
User Signup → Auto-Allocate Virtual Cash ($100,000) → Store in portfolios.cash_balance
     ↓
User Places Order → Validate Buying Power → Execute Trade (Mock or Real Paper API)
     ↓
Update Cash Balance → Update Holdings → Record Transaction → Refresh Dashboard
```

### Trade Execution by Broker

#### Zerodha (Mock/Simulated)
```
Order Request → ZerodhaBroker (paper_trading=True) → Generate Mock Response
     ↓
No Real API Call → Return Simulated Order ID → Update Local DB Only
     ↓
Instant Fill at Current Price → Update Portfolio → Show on Dashboard
```

#### Alpaca (Actual Paper Trading API)
```
Order Request → AlpacaBroker (paper=True) → Call Alpaca Paper Trading API
     ↓
Real API Call to paper-api.alpaca.markets → Actual Order Processing
     ↓
Real Fill Notification → Update Portfolio → Show on Dashboard
```

---

## 📋 TODO Items

### 🔴 Critical - Must Complete

#### 1. **Auto-Allocate Virtual Money on Signup**
- [ ] Modify user registration flow to create portfolio with initial cash
- [ ] Default allocation: $100,000 (configurable via environment variable)
- [ ] Set `cash_balance` in `portfolios` table on user creation
- [ ] Create initial transaction record for "INITIAL_DEPOSIT"
- **Location**: `api-gateway/services/user_service.py:create_user()`
- **Database**: `portfolios` table already has `cash_balance` column

#### 2. **Add Funds API (Virtual Money Top-up)**
- [ ] Create endpoint `POST /portfolio/add-funds`
- [ ] Accept amount parameter (validation: min $100, max $1,000,000)
- [ ] Update `portfolios.cash_balance`
- [ ] Create transaction record with type "DEPOSIT"
- [ ] Return updated cash balance and total portfolio value
- **Location**: `api-gateway/routers/portfolio_router.py` (new endpoint)
- **Service**: `api-gateway/services/portfolio_service.py` (new method)

#### 3. **Dashboard Cash Balance Display**
- [ ] Add prominent cash balance card on dashboard
- [ ] Show "Buying Power" prominently at top
- [ ] Display total portfolio value (cash + holdings)
- [ ] Add "Add Funds" button linking to top-up modal
- [ ] Real-time updates via React Query
- **Location**: `web-ui/client/src/pages/dashboard.tsx`
- **Component**: Create `<CashBalanceCard />` component

#### 4. **Buying Power Validation**
- [ ] Implement pre-trade cash validation in `TradingService`
- [ ] Calculate required cash: `price * quantity + estimated_fees`
- [ ] Reject order if `cash_balance < required_cash`
- [ ] Return clear error message with available balance
- [ ] Support margin calculation (future: 2x buying power for margin accounts)
- **Location**: `api-gateway/services/trading_service.py`
- **Method**: New `_validate_buying_power()` method

#### 5. **Cash Balance Updates After Trades**
- [ ] **BUY Orders**: Deduct `(price * quantity) + fees` from cash_balance
- [ ] **SELL Orders**: Add `(price * quantity) - fees` to cash_balance
- [ ] Update `portfolios.cash_balance` atomically with trade execution
- [ ] Handle partial fills correctly
- [ ] Rollback cash on trade failure
- **Location**: `api-gateway/services/trading_service.py:execute_trade()`

#### 6. **Transaction History Enhancement**
- [ ] Add `cash_impact` column to `transactions` table (migration needed)
- [ ] Record cash debit/credit for each transaction
- [ ] Show running cash balance in transaction history
- [ ] Filter transactions by type (BUY, SELL, DEPOSIT, DIVIDEND)
- **Location**: Database migration + `portfolio_service.py`

---

### 🟡 Important - Paper Trading Features

#### 7. **Zerodha Mock Order Execution**
- [x] Basic mock response generation (✅ implemented)
- [ ] Realistic price simulation (use live quotes if available)
- [ ] Simulated order delays (configurable 1-5 seconds)
- [ ] Mock order rejection scenarios (insufficient margin, invalid symbol)
- [ ] Generate realistic order IDs and timestamps
- **Location**: `api-gateway/brokers/zerodha.py`
- **Status**: Partially complete, needs enhancement

#### 8. **Alpaca Paper Trading Integration**
- [x] Alpaca paper API connection (✅ implemented)
- [ ] Verify paper trading mode is correctly set
- [ ] Handle Alpaca paper API rate limits
- [ ] Process actual fill notifications from Alpaca
- [ ] Store Alpaca paper order IDs for tracking
- [ ] Reconcile Alpaca paper positions with local holdings
- **Location**: `api-gateway/brokers/alpaca.py`
- **API**: `https://paper-api.alpaca.markets`

#### 9. **Portfolio Reconciliation**
- [ ] Periodic sync of paper trading positions
- [ ] Compare local holdings with broker paper account
- [ ] Identify and resolve discrepancies
- [ ] Admin dashboard for reconciliation monitoring
- [ ] Automated alerts on mismatch
- **Location**: New `api-gateway/services/reconciliation_service.py`

#### 10. **Order History & Status Tracking**
- [ ] Create `paper_orders` table for order tracking
- [ ] Store order status: pending → filled → cancelled
- [ ] Track partial fills and average fill price
- [ ] Link orders to transactions
- [ ] Display order history on dashboard
- **Location**: Database migration + new service

#### 11. **Market Data for Paper Trading**
- [ ] Use real-time quotes for order pricing
- [ ] Fallback to last known price if market closed
- [ ] Support for delayed fills based on market conditions
- [ ] Historical price data for backtesting
- **Location**: Integrate with existing market data service

---

### 🟢 Enhancement - Future Features

#### 12. **Virtual Money Management**
- [ ] Configurable initial allocation per user/plan
- [ ] Periodic resets (e.g., monthly reset to $100k)
- [ ] Leaderboard based on paper trading returns
- [ ] Track P&L across resets
- **Status**: Future feature

#### 13. **Advanced Order Types in Paper Mode**
- [ ] Stop-loss orders (simulated)
- [ ] Limit orders with queue simulation
- [ ] Bracket orders (OCO) in paper mode
- [ ] GTD (Good-Till-Date) order expiry
- **Status**: Basic orders implemented, advanced types pending

#### 14. **Paper Trading Analytics**
- [ ] Win/loss ratio tracking
- [ ] Sharpe ratio calculation
- [ ] Drawdown analysis
- [ ] Trade frequency metrics
- [ ] Export trading journal
- **Status**: Not started

#### 15. **Transition to Live Trading**
- [ ] "Upgrade to Live" flow
- [ ] Copy paper trading strategy to live
- [ ] Compare paper vs live performance
- [ ] Risk warnings and confirmations
- **Status**: Future consideration

---

## 🔧 Recommended Implementation Order

### **Phase 1: Core Virtual Money (Week 1)** - Priority: 🔴 CRITICAL
1. [ ] Database migration for cash transactions tracking (#6)
2. [ ] Auto-allocate virtual money on signup (#1)
3. [ ] Add funds API endpoint (#2)
4. [ ] Dashboard cash balance display (#3)
5. [ ] Buying power validation (#4)
6. [ ] Cash balance updates after trades (#5)
7. [ ] Test end-to-end: signup → get $100k → buy → sell → verify cash

### **Phase 2: Broker-Specific Paper Trading (Week 2)** - Priority: 🟡 IMPORTANT
8. [ ] Enhance Zerodha mock execution (#7)
9. [ ] Verify Alpaca paper API integration (#8)
10. [ ] Order history tracking system (#10)
11. [ ] Market data integration for pricing (#11)
12. [ ] Test both Zerodha (mock) and Alpaca (real paper API) flows

### **Phase 3: Polish & Monitoring (Week 3-4)** - Priority: 🟢 NICE-TO-HAVE
13. [ ] Portfolio reconciliation service (#9)
14. [ ] Virtual money management features (#12)
15. [ ] Paper trading analytics (#14)
16. [ ] Admin monitoring dashboard
17. [ ] Production deployment preparation

---

## 🗄️ Database Changes Needed

### Migration: `11-add-paper-trading-enhancements.sql`

```sql
-- Add cash impact tracking to transactions
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS cash_impact DECIMAL(15, 2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS cash_balance_after DECIMAL(15, 2);

-- Create paper orders tracking table
CREATE TABLE IF NOT EXISTS paper_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    broker_connection_id UUID NOT NULL REFERENCES user_broker_connections(id),
    order_id VARCHAR(100) NOT NULL, -- Broker's order ID
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- BUY or SELL
    order_type VARCHAR(20) NOT NULL, -- MARKET, LIMIT, STOP
    quantity DECIMAL(15, 4) NOT NULL,
    price DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'pending', -- pending, filled, cancelled, rejected
    filled_quantity DECIMAL(15, 4) DEFAULT 0,
    average_fill_price DECIMAL(15, 2),
    broker_type VARCHAR(50) NOT NULL, -- zerodha or alpaca
    is_paper_trading BOOLEAN DEFAULT true,
    order_response JSONB, -- Full broker response
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    filled_at TIMESTAMP
);

CREATE INDEX idx_paper_orders_user ON paper_orders(user_id, created_at DESC);
CREATE INDEX idx_paper_orders_status ON paper_orders(status, broker_type);

-- Add virtual money configuration
CREATE TABLE IF NOT EXISTS virtual_money_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    initial_allocation DECIMAL(15, 2) DEFAULT 100000.00,
    max_top_up DECIMAL(15, 2) DEFAULT 1000000.00,
    allow_reset BOOLEAN DEFAULT true,
    last_reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add paper trading statistics
CREATE TABLE IF NOT EXISTS paper_trading_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0.00,
    best_trade DECIMAL(15, 2) DEFAULT 0.00,
    worst_trade DECIMAL(15, 2) DEFAULT 0.00,
    current_streak INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_paper_stats_user ON paper_trading_stats(user_id);
```

---

## 🔌 API Endpoints to Create

### Portfolio Endpoints

```python
# Add funds
POST /portfolio/add-funds
Body: { "amount": 50000.00 }
Response: { "cash_balance": 150000.00, "total_value": 175000.00 }

# Get cash balance
GET /portfolio/cash-balance
Response: { "cash_balance": 100000.00, "buying_power": 100000.00 }

# Reset paper trading portfolio
POST /portfolio/reset-paper-trading
Response: { "message": "Portfolio reset", "new_balance": 100000.00 }
```

### Order Tracking Endpoints

```python
# List paper orders
GET /orders/paper/list?status=filled&broker_type=zerodha
Response: [{ "order_id": "...", "symbol": "RELIANCE", "status": "filled", ... }]

# Get order details
GET /orders/paper/{order_id}
Response: { "order_id": "...", "fills": [...], "cash_impact": -25000.00 }
```

---

## 🎨 UI Components to Create/Update

### 1. Cash Balance Card Component
**File**: `web-ui/client/src/components/CashBalanceCard.tsx`
```tsx
- Display cash balance prominently
- Show buying power
- "Add Funds" button
- Visual cash flow indicator
- Real-time updates
```

### 2. Add Funds Modal
**File**: `web-ui/client/src/components/AddFundsModal.tsx`
```tsx
- Amount input with validation
- Preset amounts ($10k, $50k, $100k)
- Confirm and cancel buttons
- Success/error notifications
```

### 3. Paper Trading Mode Indicator
**File**: `web-ui/client/src/components/PaperTradingBadge.tsx`
```tsx
- "Paper Trading" badge in header
- Visual distinction from live trading
- Tooltip explaining paper mode
```

### 4. Enhanced Dashboard
**File**: `web-ui/client/src/pages/dashboard.tsx`
```tsx
- Add CashBalanceCard at top
- Show paper trading mode prominently
- Add P&L metrics for paper trading
- Quick actions: Add Funds, View Orders
```

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [x] New users automatically receive $100,000 virtual cash
- [x] Cash balance visible on dashboard
- [x] Users can add virtual funds via API
- [x] Buying power validated before every trade
- [x] Cash correctly debited/credited on trades
- [x] Transaction history shows cash impact

### Phase 2 Complete When:
- [x] Zerodha orders execute as mock (no real API)
- [x] Alpaca orders use actual paper trading API
- [x] Order history shows all paper trades
- [x] Portfolio reflects correct holdings and cash
- [x] Market data used for realistic pricing

### Phase 3 Complete When:
- [x] Reconciliation service running
- [x] Paper trading analytics available
- [x] Admin can monitor paper trading activity
- [x] System ready for production paper trading

---

## 🚀 Quick Start for Development

### 1. Apply Database Migration
```bash
docker exec -i saras-trading-platform-postgres-1 \
  psql -U trading_user -d trading_dev < database/migrations/11-add-paper-trading-enhancements.sql
```

### 2. Test Virtual Money Allocation
```bash
# Create new user and verify $100k allocation
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "paper_trader@example.com",
    "password": "Password123",
    "full_name": "Paper Trader"
  }'

# Check portfolio cash balance
curl -X GET http://localhost:8000/portfolio/cash-balance \
  -H "Authorization: Bearer <token>"
```

### 3. Test Add Funds
```bash
curl -X POST http://localhost:8000/portfolio/add-funds \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "amount": 50000.00 }'
```

### 4. Test Paper Trade Flow
```bash
# Place Zerodha mock order (should not call real API)
curl -X POST http://localhost:8000/orders/place \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "broker_connection_id": "<zerodha_connection_id>",
    "symbol": "RELIANCE",
    "side": "BUY",
    "quantity": 10,
    "order_type": "MARKET"
  }'

# Verify cash deducted from balance
curl -X GET http://localhost:8000/portfolio/cash-balance \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Implementation Notes

### Zerodha Mock vs Alpaca Paper API

| Aspect | Zerodha (Mock) | Alpaca (Paper API) |
|--------|---------------|-------------------|
| **API Calls** | None - fully simulated | Actual API calls to paper-api.alpaca.markets |
| **Order IDs** | Generated locally (UUID) | Real Alpaca paper order IDs |
| **Fills** | Instant at current price | Real market simulation with delays |
| **Market Data** | Use cached/latest price | Alpaca real-time paper market data |
| **Positions** | Stored only in our DB | Synced with Alpaca paper account |
| **Advantages** | No rate limits, instant | Realistic paper trading experience |

### Cash Balance Calculation
```python
# Total Portfolio Value
total_value = cash_balance + sum(holdings.quantity * current_price)

# Buying Power (basic)
buying_power = cash_balance

# Buying Power (with margin - future)
buying_power = cash_balance * margin_multiplier  # e.g., 2x for margin accounts
```

### Transaction Types
- `INITIAL_DEPOSIT` - Virtual money on signup
- `DEPOSIT` - Manual add funds
- `BUY` - Stock purchase (cash debit)
- `SELL` - Stock sale (cash credit)
- `DIVIDEND` - Dividend payment (cash credit)
- `FEE` - Transaction fees (cash debit)

---

## 🔗 Related Documentation

- Architecture: `/PRODUCTION.PLAN.md`
- Dividend System: `/DIVIDEND_TODO.md`
- Database Schema: `/database/migrations/`
- API Documentation: `http://localhost:8000/docs`
- Zerodha Integration: `/api-gateway/brokers/zerodha.py`
- Alpaca Integration: `/api-gateway/brokers/alpaca.py`

---

**Last Updated**: 2025-10-03
**Status**: 🔴 Not Started - Ready for Implementation
**Priority**: HIGH - Core feature for platform viability
