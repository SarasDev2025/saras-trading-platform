# Architecture Principles

## Single Source of Truth (SSOT)

### Trading Mode

**Source of Truth:** `users.trading_mode` (PostgreSQL database)

**How It Works:**
- User's trading mode (`paper` or `live`) is stored in the database
- Backend reads mode from database and filters all queries automatically
- Frontend displays mode for UI purposes only
- Frontend never sends mode in API requests or URLs

**Frontend Usage:**
```typescript
// ✅ CORRECT - Display only
const { tradingMode } = useTradingMode();
return <Badge>{tradingMode === 'live' ? 'LIVE' : 'PAPER'}</Badge>;

// ✅ CORRECT - Switch mode (updates database)
switchMode('live'); // Calls API, updates DB, invalidates queries

// ❌ WRONG - Don't send mode in URLs
queryKey: ["/api/portfolios", tradingMode] // NO!
queryKey: ["/api/portfolios"] // YES!
```

**Backend Implementation:**
```python
# Backend reads mode from database
user_result = await db.execute(
    text("SELECT trading_mode FROM users WHERE id = :user_id"),
    {"user_id": user_id}
)
user_mode = user_result.scalar_one()

# Filter by mode automatically
result = await db.execute(
    text("SELECT * FROM portfolios WHERE user_id = :user_id AND trading_mode = :trading_mode"),
    {"user_id": user_id, "trading_mode": user_mode}
)
```

**Benefits:**
- No sync issues between frontend/backend
- Mode changes automatically affect all queries
- Impossible to query wrong mode's data
- Single update point when switching modes

### User Data

**Source of Truth:** `users` table (PostgreSQL database)

**Flow:**
1. User logs in → Backend returns user data with JWT
2. Frontend stores in AuthContext
3. All components read from AuthContext
4. Settings page uses `key` prop to force re-render on user data changes

**Frontend Usage:**
```typescript
// ✅ CORRECT
const { user } = useAuth();
<Input key={`name-${user?.id}`} defaultValue={user?.first_name} />

// ❌ WRONG - Hardcoded values
<Input defaultValue="John Doe" />
```

### Region-Based Broker Selection

**Source of Truth:** `users.region` (PostgreSQL database)

**Mapping:**
- `IN` (India) → Zerodha
- `US` (United States) → Alpaca
- `GB` (United Kingdom) → Interactive Brokers

**Implementation:**
```typescript
// ✅ CORRECT - Derive from user.region
const defaultBroker = useMemo(() => {
  switch (user.region) {
    case "IN": return "zerodha";
    case "US": return "alpaca";
    case "GB": return "interactive_brokers";
  }
}, [user?.region]);

// ❌ WRONG - Hardcoded
const brokerType = "alpaca";
```

## React Query Cache Management

**Principle:** Additional queryKey elements are for cache invalidation ONLY, not URL construction

**Implementation:**
```typescript
// queryClient.ts uses ONLY first element as URL
const url = queryKey[0] as string;
// NOT: const url = queryKey.join("/");

// ✅ CORRECT
queryKey: ["/api/portfolios"]
// Fetches: /api/portfolios
// Backend filters by user's mode automatically

// ❌ WRONG
queryKey: ["/api/portfolios", tradingMode]
// Would fetch: /api/portfolios/paper (wrong route!)
```

**Cache Invalidation:**
```typescript
// When switching modes, invalidate all relevant queries
queryClient.invalidateQueries({ queryKey: ['/api/portfolios'] });
queryClient.invalidateQueries({ queryKey: ['/api/portfolios/cash-balance'] });
```

## Database Schema as Contract

**Principle:** Database schema defines the data contract between frontend and backend

**Rules:**
1. Backend models must match database exactly
2. Frontend types should match backend responses
3. Schema migrations must be applied before code changes
4. Default values in database apply to new records

**Example:**
```sql
-- Migration defines contract
ALTER TABLE users ADD COLUMN trading_mode VARCHAR(10) DEFAULT 'paper';

-- Backend model matches
trading_mode: Mapped[str] = mapped_column(String(10), default='paper')

-- Frontend type matches
interface User {
  trading_mode: 'paper' | 'live';
}
```

## Key Takeaways

1. **Database is truth** - All authoritative data lives in PostgreSQL
2. **Frontend displays** - UI shows current state, doesn't maintain it
3. **Backend filters** - Server-side logic uses database values automatically
4. **No duplication** - Don't store same data in multiple places
5. **Cache invalidation** - When source updates, invalidate derived data

## Anti-Patterns to Avoid

❌ Storing mode in localStorage and database (duplication)
❌ Sending mode in every API request (redundant)
❌ Using queryKey elements to build URLs (wrong abstraction)
❌ Hardcoding user data in UI (loses sync)
❌ Deriving broker from local state instead of user.region (out of sync)

## When This Was Learned

**Issue:** Cash card not showing after database changes
**Root Cause:** Added `tradingMode` to queryKey, which built wrong URL `/api/portfolios/paper`
**Fix:** Removed mode from queryKey, backend reads from database instead
**Lesson:** Keep Single Source of Truth in database, frontend only displays

**Date:** 2025-10-06
