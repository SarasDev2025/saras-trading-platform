# Dividend Management System - Development Plan

## Overview
This document outlines the comprehensive development plan for implementing a multi-user dividend management system supporting multiple brokers (Zerodha/India and Alpaca/US), mixed user preferences (cash vs DRIP), and cross-currency operations.

## Core Challenges

### 1. Multi-User Asset Pooling
- **Challenge**: Multiple users invest in same stocks through smallcases, but broker holds aggregate positions
- **Solution**: Maintain detailed position snapshots at dividend record dates to determine user eligibility

### 2. Mixed Dividend Preferences
- **Challenge**: Some users want cash dividends, others want reinvestment (DRIP)
- **Solution**: User-level dividend preferences with sophisticated distribution logic

### 3. Cross-Broker & Cross-Currency
- **Challenge**: Zerodha (INR) and Alpaca (USD) have different dividend mechanisms and tax treatments
- **Solution**: Broker-agnostic dividend adapters with currency conversion and tax handling

### 4. Fractional Share Management
- **Challenge**: DRIP creates fractional shares that need to be tracked and managed
- **Solution**: Fractional share tracking with consolidation mechanisms

## Phase 1: API Design & Testing

### 1.1 Database Schema Extensions

#### Dividend Preferences Table
```sql
CREATE TABLE user_dividend_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    preference_type VARCHAR(20) NOT NULL CHECK (preference_type IN ('cash', 'reinvest', 'mixed')),
    default_cash_percentage DECIMAL(5,2) DEFAULT 0.00, -- For mixed preference
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);
```

#### Position Snapshots Table
```sql
CREATE TABLE position_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(50) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,6) NOT NULL, -- Support fractional shares
    average_price DECIMAL(15,4) NOT NULL,
    market_value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(snapshot_date, symbol, broker),
    INDEX(user_id, symbol, broker)
);
```

#### Dividend Events Table
```sql
CREATE TABLE dividend_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    ex_date DATE NOT NULL,
    record_date DATE NOT NULL,
    pay_date DATE NOT NULL,
    dividend_amount DECIMAL(15,4) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    total_shares_held DECIMAL(15,6) NOT NULL, -- Our aggregate position
    total_dividend_received DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'distributed', 'failed')),
    broker_reference VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(symbol, broker, ex_date)
);
```

#### Dividend Distributions Table
```sql
CREATE TABLE dividend_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dividend_event_id UUID NOT NULL REFERENCES dividend_events(id),
    user_id UUID NOT NULL REFERENCES users(id),
    eligible_shares DECIMAL(15,6) NOT NULL,
    gross_dividend DECIMAL(15,2) NOT NULL,
    tax_deducted DECIMAL(15,2) DEFAULT 0.00,
    net_dividend DECIMAL(15,2) NOT NULL,
    distribution_type VARCHAR(20) NOT NULL CHECK (distribution_type IN ('cash', 'reinvest')),
    shares_purchased DECIMAL(15,6), -- For reinvestment
    purchase_price DECIMAL(15,4), -- Price per share for reinvestment
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

#### Fractional Holdings Table
```sql
CREATE TABLE fractional_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(50) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    fractional_quantity DECIMAL(15,6) NOT NULL,
    accumulated_value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, symbol, broker)
);
```

### 1.2 Broker Adapter Interfaces

#### Base Dividend Adapter
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date

class DividendAdapter(ABC):
    @abstractmethod
    async def fetch_dividend_events(self, symbols: List[str], start_date: date, end_date: date) -> List[Dict]:
        """Fetch dividend events from broker API"""
        pass

    @abstractmethod
    async def get_position_on_date(self, symbol: str, target_date: date) -> Dict:
        """Get our aggregate position on specific date"""
        pass

    @abstractmethod
    async def execute_dividend_reinvestment(self, symbol: str, amount: Decimal, user_id: str) -> Dict:
        """Execute DRIP purchase for user"""
        pass

    @abstractmethod
    async def process_cash_dividend(self, user_id: str, amount: Decimal, currency: str) -> Dict:
        """Process cash dividend payment to user account"""
        pass
```

#### Zerodha Dividend Adapter
```python
class ZerodhaDividendAdapter(DividendAdapter):
    def __init__(self, kite_client):
        self.kite = kite_client

    async def fetch_dividend_events(self, symbols: List[str], start_date: date, end_date: date) -> List[Dict]:
        # Implement Zerodha-specific dividend fetching
        # Handle INR currency and Indian tax regulations (TDS)
        pass

    async def execute_dividend_reinvestment(self, symbol: str, amount: Decimal, user_id: str) -> Dict:
        # Place buy order for fractional amount
        # Handle Indian market constraints (no fractional shares)
        pass
```

#### Alpaca Dividend Adapter
```python
class AlpacaDividendAdapter(DividendAdapter):
    def __init__(self, alpaca_client):
        self.alpaca = alpaca_client

    async def fetch_dividend_events(self, symbols: List[str], start_date: date, end_date: date) -> List[Dict]:
        # Implement Alpaca-specific dividend fetching
        # Handle USD currency and US tax regulations
        pass

    async def execute_dividend_reinvestment(self, symbol: str, amount: Decimal, user_id: str) -> Dict:
        # Place fractional buy order
        # Handle US market fractional share support
        pass
```

### 1.3 Core API Endpoints

#### Dividend Preferences API
```python
# GET /api/v1/dividends/preferences
# POST /api/v1/dividends/preferences
# PUT /api/v1/dividends/preferences/{user_id}

@router.get("/preferences")
async def get_dividend_preferences(current_user: User = Depends(get_current_user)):
    """Get user's dividend preferences"""
    pass

@router.post("/preferences")
async def set_dividend_preferences(
    preferences: DividendPreferencesCreate,
    current_user: User = Depends(get_current_user)
):
    """Set user's dividend preferences"""
    pass
```

#### Dividend Events API
```python
# GET /api/v1/dividends/events
# GET /api/v1/dividends/events/{event_id}
# POST /api/v1/dividends/events/{event_id}/process

@router.get("/events")
async def get_dividend_events(
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get dividend events affecting user's portfolio"""
    pass

@router.post("/events/{event_id}/process")
async def process_dividend_event(
    event_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Process dividend distribution for all eligible users"""
    pass
```

#### Position Snapshots API
```python
# GET /api/v1/positions/snapshots
# POST /api/v1/positions/snapshots/create

@router.post("/snapshots/create")
async def create_position_snapshot(
    snapshot_date: date,
    admin_user: User = Depends(get_admin_user)
):
    """Create position snapshots for dividend eligibility"""
    pass
```

### 1.4 Core Services

#### Dividend Detection Service
```python
class DividendDetectionService:
    def __init__(self, zerodha_adapter: ZerodhaDividendAdapter, alpaca_adapter: AlpacaDividendAdapter):
        self.adapters = {
            'zerodha': zerodha_adapter,
            'alpaca': alpaca_adapter
        }

    async def scan_for_dividend_events(self) -> List[DividendEvent]:
        """Scan all brokers for new dividend events"""
        pass

    async def create_position_snapshots(self, dividend_event: DividendEvent) -> bool:
        """Create position snapshots for dividend eligibility"""
        pass
```

#### Dividend Distribution Service
```python
class DividendDistributionService:
    async def calculate_user_eligibility(self, dividend_event: DividendEvent) -> List[UserDividendEligibility]:
        """Calculate each user's dividend eligibility"""
        pass

    async def distribute_dividends(self, dividend_event: DividendEvent) -> Dict:
        """Distribute dividends according to user preferences"""
        pass

    async def execute_reinvestments(self, reinvestment_orders: List[ReinvestmentOrder]) -> Dict:
        """Execute DRIP orders across brokers"""
        pass
```

### 1.5 API Testing Plan

#### Unit Tests
- Test dividend preference CRUD operations
- Test position snapshot creation
- Test dividend eligibility calculations
- Test broker adapter implementations

#### Integration Tests
- Test end-to-end dividend detection and distribution
- Test cross-broker dividend handling
- Test currency conversion accuracy
- Test tax calculation compliance

#### Test Data Setup
```python
# Create test users with different preferences
test_users = [
    {"email": "cash.user@test.com", "preference": "cash"},
    {"email": "drip.user@test.com", "preference": "reinvest"},
    {"email": "mixed.user@test.com", "preference": "mixed", "cash_percentage": 50}
]

# Create test dividend events
test_dividend_events = [
    {"symbol": "AAPL", "broker": "alpaca", "amount": 0.22, "currency": "USD"},
    {"symbol": "RELIANCE", "broker": "zerodha", "amount": 8.50, "currency": "INR"}
]
```

## Phase 2: UI Design & Testing

### 2.1 Dividend Preferences UI

#### User Dividend Settings Page
```tsx
interface DividendPreferencesForm {
  preferenceType: 'cash' | 'reinvest' | 'mixed';
  defaultCashPercentage?: number;
  stockSpecificPreferences?: Array<{
    symbol: string;
    preferenceType: 'cash' | 'reinvest' | 'mixed';
    cashPercentage?: number;
  }>;
}

const DividendPreferencesPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Dividend Preferences</h1>

      {/* Global Preference */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Default Dividend Preference</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup defaultValue="cash">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="cash" id="cash" />
              <Label htmlFor="cash">Cash Dividends</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="reinvest" id="reinvest" />
              <Label htmlFor="reinvest">Reinvest Dividends (DRIP)</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="mixed" id="mixed" />
              <Label htmlFor="mixed">Mixed (Percentage Split)</Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Stock-Specific Overrides */}
      <Card>
        <CardHeader>
          <CardTitle>Stock-Specific Preferences</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Table of current holdings with override options */}
        </CardContent>
      </Card>
    </div>
  );
};
```

#### Dividend Dashboard
```tsx
const DividendDashboard: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Dividends (YTD)</p>
                <p className="text-2xl font-bold">$1,234.56</p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Reinvested</p>
                <p className="text-2xl font-bold">$856.78</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cash Received</p>
                <p className="text-2xl font-bold">$377.78</p>
              </div>
              <Banknote className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Upcoming</p>
                <p className="text-2xl font-bold">3</p>
              </div>
              <Calendar className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Dividend Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Dividend Events</CardTitle>
        </CardHeader>
        <CardContent>
          <DividendEventsTable />
        </CardContent>
      </Card>
    </div>
  );
};
```

### 2.2 Enhanced Position Closure UI

#### Updated Closure Modal with Dividend Info
```tsx
const ClosureModal: React.FC<{ investment: UserInvestment }> = ({ investment }) => {
  const [closurePreview, setClosurePreview] = useState<ClosurePreview | null>(null);

  useEffect(() => {
    fetchClosurePreview();
  }, [investment.id]);

  return (
    <AlertDialog>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle>Close Position: {investment.smallcase_name}</AlertDialogTitle>
        </AlertDialogHeader>

        <div className="space-y-6">
          {/* Financial Summary */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Current Value</Label>
              <p className="text-xl font-semibold">{formatCurrency(closurePreview?.current_value)}</p>
            </div>
            <div>
              <Label>Total P&L</Label>
              <p className={`text-xl font-semibold ${closurePreview?.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(closurePreview?.unrealized_pnl)}
              </p>
            </div>
          </div>

          {/* Dividend Information */}
          {closurePreview?.accrued_dividends && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Dividend Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span>Accrued Dividends:</span>
                  <span className="font-semibold">{formatCurrency(closurePreview.accrued_dividends)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Pending Ex-Date Claims:</span>
                  <span className="font-semibold">{closurePreview.pending_dividend_count}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Warning for Pending Dividends */}
          {closurePreview?.pending_dividend_count > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Pending Dividend Claims</AlertTitle>
              <AlertDescription>
                This position has {closurePreview.pending_dividend_count} pending dividend claims.
                Closing now may forfeit future dividend payments.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirmClosure}
            className="bg-red-600 hover:bg-red-700"
          >
            Confirm Closure
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
```

### 2.3 UI Testing Plan

#### Browser Testing with Playwright
```javascript
// tests/dividend-preferences.spec.js
test.describe('Dividend Preferences', () => {
  test('should save dividend preferences', async ({ page }) => {
    await page.goto('/dividends/preferences');

    // Test cash preference
    await page.click('input[value="cash"]');
    await page.click('button:has-text("Save Preferences")');

    await expect(page.locator('.success-message')).toBeVisible();
  });

  test('should display dividend dashboard', async ({ page }) => {
    await page.goto('/dividends/dashboard');

    // Check summary cards
    await expect(page.locator('text="Total Dividends (YTD)"')).toBeVisible();
    await expect(page.locator('text="Reinvested"')).toBeVisible();
    await expect(page.locator('text="Cash Received"')).toBeVisible();
  });
});

// tests/enhanced-closure.spec.js
test.describe('Enhanced Position Closure', () => {
  test('should show dividend information in closure modal', async ({ page }) => {
    await page.goto('/portfolio');

    // Click close on first investment
    await page.click('.investment-card:first-child button:has-text("Close")');

    // Check for dividend information
    await expect(page.locator('text="Accrued Dividends"')).toBeVisible();
    await expect(page.locator('text="Pending Ex-Date Claims"')).toBeVisible();
  });

  test('should warn about pending dividends', async ({ page }) => {
    // Test with investment that has pending dividends
    // Should show warning alert
  });
});
```

## Phase 3: Implementation

### 3.1 Core Infrastructure Implementation

#### Database Migration Scripts
```sql
-- migrations/07-dividend-management-system.sql
-- All the CREATE TABLE statements from Phase 1.1
```

#### Broker Adapter Implementation
- Complete Zerodha and Alpaca dividend adapters
- Implement error handling and retry logic
- Add rate limiting and API quota management

#### Background Job System
```python
# dividend_jobs.py
from celery import Celery

app = Celery('dividend_system')

@app.task
def scan_dividend_events():
    """Daily job to scan for new dividend events"""
    pass

@app.task
def create_position_snapshots(dividend_event_id: str):
    """Create position snapshots before ex-date"""
    pass

@app.task
def process_dividend_distribution(dividend_event_id: str):
    """Process dividend distribution on pay-date"""
    pass
```

### 3.2 Dividend Distribution Logic

#### Core Algorithm
```python
async def distribute_dividend_event(dividend_event: DividendEvent):
    # 1. Get position snapshots from record date
    snapshots = await get_position_snapshots(dividend_event.record_date, dividend_event.symbol)

    # 2. Calculate each user's eligible shares
    for snapshot in snapshots:
        user_shares = snapshot.quantity
        user_dividend = (user_shares / dividend_event.total_shares_held) * dividend_event.total_dividend_received

        # 3. Apply tax calculations based on broker/country
        if dividend_event.broker == 'zerodha':
            tax_deducted = calculate_indian_tds(user_dividend, snapshot.user_id)
        else:
            tax_deducted = calculate_us_withholding(user_dividend, snapshot.user_id)

        net_dividend = user_dividend - tax_deducted

        # 4. Get user preference
        preference = await get_user_dividend_preference(snapshot.user_id)

        # 5. Execute distribution
        if preference.preference_type == 'cash':
            await process_cash_dividend(snapshot.user_id, net_dividend)
        elif preference.preference_type == 'reinvest':
            await execute_drip_purchase(snapshot.user_id, dividend_event.symbol, net_dividend)
        else:  # mixed
            cash_amount = net_dividend * (preference.default_cash_percentage / 100)
            reinvest_amount = net_dividend - cash_amount

            await process_cash_dividend(snapshot.user_id, cash_amount)
            await execute_drip_purchase(snapshot.user_id, dividend_event.symbol, reinvest_amount)
```

### 3.3 Broker Integration Implementation

#### Real-time Dividend Detection
```python
class DividendEventMonitor:
    async def monitor_zerodha_dividends(self):
        """Monitor Zerodha for dividend events"""
        # Check corporate actions API
        # Compare with existing events
        # Create new dividend events
        pass

    async def monitor_alpaca_dividends(self):
        """Monitor Alpaca for dividend events"""
        # Check Alpaca corporate actions
        # Handle different notification mechanisms
        pass
```

#### Fractional Share Handling
```python
class FractionalShareManager:
    async def accumulate_fractional_shares(self, user_id: str, symbol: str, fractional_amount: Decimal):
        """Accumulate fractional shares until they can be consolidated"""
        pass

    async def consolidate_fractional_shares(self, user_id: str, symbol: str):
        """Convert accumulated fractional shares to whole shares when threshold reached"""
        pass
```

### 3.4 Testing & Validation

#### End-to-End Testing
- Test complete dividend cycle from detection to distribution
- Validate tax calculations for both markets
- Test error scenarios and recovery mechanisms
- Performance testing with large user bases

#### Data Validation
- Reconciliation reports between broker statements and internal calculations
- Audit trails for all dividend distributions
- Compliance reporting for tax authorities

## Implementation Timeline

### Phase 1: API Design & Testing (4-6 weeks)
- Week 1-2: Database schema and migrations
- Week 3-4: Core API endpoints and services
- Week 5-6: Broker adapters and testing

### Phase 2: UI Design & Testing (3-4 weeks)
- Week 1-2: Dividend preferences and dashboard UI
- Week 3-4: Enhanced closure UI and browser testing

### Phase 3: Implementation (6-8 weeks)
- Week 1-2: Core infrastructure and background jobs
- Week 3-4: Dividend distribution logic
- Week 5-6: Broker integrations
- Week 7-8: End-to-end testing and validation

## Risk Mitigation

### Technical Risks
- **Broker API Changes**: Implement adapter pattern with version management
- **Data Inconsistencies**: Implement comprehensive reconciliation and audit systems
- **Performance Issues**: Implement caching and optimize database queries

### Financial Risks
- **Calculation Errors**: Implement multiple validation layers and manual approval gates
- **Tax Compliance**: Work with tax professionals for each jurisdiction
- **Reconciliation Failures**: Implement automated alerting and manual override capabilities

### Operational Risks
- **User Education**: Comprehensive documentation and support for dividend preferences
- **Support Volume**: Automated dividend reporting and self-service preference management
- **Regulatory Changes**: Modular design allowing for quick adaptation to new regulations

## Success Metrics

### Technical Metrics
- 99.9% accuracy in dividend calculations
- <24 hour processing time from dividend detection to distribution
- Zero data loss during dividend processing
- 99% uptime for dividend-related services

### Business Metrics
- User adoption of dividend management features
- Reduction in customer support queries about dividends
- Increased user retention due to comprehensive dividend handling
- Compliance with all applicable tax and regulatory requirements

This comprehensive plan provides a structured approach to implementing a sophisticated dividend management system that handles the complexities of multi-user portfolios, multiple brokers, and varying user preferences while maintaining accuracy, compliance, and performance.