# Interactive Chart-Based Algorithm Builder - Implementation Plan

## Overview
Create a **new** interactive, chart-based algorithm builder as a third option alongside existing "Code" and "Visual Builder" modes. This provides real-time visual feedback as users configure trading strategies.

**Key Principle**: Keep existing visual builder unchanged. This is an additional, more advanced option.

---

## User Experience Vision

### Current Flow (Unchanged)
1. User clicks "Create Algorithm"
2. Chooses: **Code** or **Visual Builder**
3. Visual Builder: Configure entry/exit rules with dropdowns → Save → Backtest

### New Flow (Addition)
1. User clicks "Create Algorithm"
2. Chooses: **Code**, **Visual Builder**, or **Interactive Chart Builder** (NEW)
3. Interactive Chart Builder:
   - See live chart with historical data (e.g., AAPL last 3 months)
   - Add indicators visually → They appear on chart immediately
   - Adjust parameters with sliders → Chart updates in real-time
   - See buy/sell signal markers where conditions would trigger
   - Get instant feedback: "15 signals detected, 67% estimated win rate"
   - Save algorithm when satisfied

---

## Architecture

### Component Structure

```
web-ui/client/src/components/algorithms/
├── NoCodeAlgorithmBuilder.tsx (existing - keep as-is)
├── InteractiveChartBuilder/ (NEW)
│   ├── index.tsx (main component)
│   ├── ChartDisplay.tsx (price chart with overlays)
│   ├── IndicatorPanel.tsx (right sidebar controls)
│   ├── IndicatorOverlay.tsx (renders RSI, SMA, etc. on chart)
│   ├── SignalMarkers.tsx (buy/sell triangles)
│   ├── ParameterSlider.tsx (interactive sliders)
│   ├── StrategyTemplates.tsx (one-click presets)
│   └── hooks/
│       ├── useChartData.ts (fetch historical data)
│       ├── useIndicatorCalculation.ts (calculate indicators)
│       └── useSignalSimulation.ts (detect trigger points)
```

### API Endpoints (New)

```python
# api-gateway/routers/algorithm_router.py

@router.post("/visual/preview")
async def preview_visual_algorithm(request: PreviewRequest):
    """
    Generate preview data for interactive chart builder

    Input:
        - symbol: Stock symbol (e.g., "AAPL")
        - start_date: Date to start preview
        - end_date: Date to end preview
        - visual_config: Entry/exit conditions

    Output:
        - price_data: OHLCV data
        - indicators: Calculated indicator values (RSI, SMA, etc.)
        - signals: Array of trigger points with dates
        - stats: Quick metrics (signal_count, estimated_win_rate)
    """
```

---

## Detailed Feature Specifications

### 1. Chart Display (Left Panel - 70% width)

**Components:**
- **Price Chart**: Candlestick or line chart showing close prices
- **Volume Bars**: Below price chart
- **Indicator Panels**: RSI, MACD in separate panels below price
- **Time Range Selector**: 1M, 3M, 6M, 1Y, YTD buttons

**Overlays:**
- **Moving Averages**: SMA/EMA as colored lines on price (blue, orange, green)
- **Bollinger Bands**: Shaded area around price
- **Support/Resistance**: Horizontal dashed lines (optional)

**Signal Markers:**
- **Green Triangle (▲)**: Buy signal triggered
- **Red Triangle (▼)**: Sell signal triggered
- **Connecting Lines**: Dotted lines between paired buy/sell showing P&L

**Interactions:**
- Hover over any point → Tooltip with price, indicators, signal details
- Zoom with mouse wheel
- Pan by dragging
- Click signal marker → Highlight corresponding condition in right panel

### 2. Control Panel (Right Panel - 30% width)

**Stock Selector:**
```
[🔍 Search Symbol: AAPL ▼]
Popular: AAPL, MSFT, GOOGL, TSLA, AMZN
```

**Entry Conditions Section:**
```
┌─ Entry Rules ─────────────────────────┐
│ [+ Add Entry Condition]                │
│                                        │
│ ┌─ Condition 1 ──────────────────┐   │
│ │ Type: [Indicator Comparison ▼] │   │
│ │                                 │   │
│ │ Indicator: [RSI ▼]             │   │
│ │ Period: [14] ←─────────→       │   │
│ │         5──────14──────50       │   │
│ │                                 │   │
│ │ Operator: [< ▼] (Less than)    │   │
│ │ Value: [30] ←──────────→       │   │
│ │        0──────30──────100       │   │
│ │                                 │   │
│ │ [👁️ Show on Chart] ✓           │   │
│ │                      [🗑️ Remove]│   │
│ └─────────────────────────────────┘   │
└────────────────────────────────────────┘
```

**Exit Conditions Section:** (Same structure as entry)

**Live Preview Stats:**
```
┌─ Preview Results ──────────────────────┐
│ 🎯 15 Buy Signals Detected             │
│ 📊 13 Complete Trades                  │
│ ✅ 67% Win Rate (9 wins, 4 losses)     │
│ 💰 Estimated P&L: +$4,250 (+4.25%)    │
│                                        │
│ [🔄 Refresh Preview]  [💾 Save Algo]  │
└────────────────────────────────────────┘
```

**Strategy Templates:**
```
┌─ Quick Start Templates ────────────────┐
│ [RSI Oversold]  [MA Crossover]         │
│ [Bollinger Breakout]  [MACD Signal]    │
└────────────────────────────────────────┘
```

### 3. Indicator Library

**Supported Indicators:**

| Indicator | Visual Representation | Parameters |
|-----------|----------------------|------------|
| RSI | Line chart (0-100), separate panel | Period (5-50) |
| SMA | Colored line on price | Period (5-200) |
| EMA | Colored line on price | Period (5-200) |
| MACD | Histogram + signal line, separate panel | Fast, Slow, Signal |
| Bollinger Bands | Shaded area on price | Period, Std Dev |
| Volume | Bar chart below price | N/A |

**Color Scheme:**
- Price: Blue (#3B82F6)
- SMA 20: Orange (#F59E0B)
- SMA 50: Green (#10B981)
- RSI: Purple (#8B5CF6)
- Buy Signals: Green (#22C55E)
- Sell Signals: Red (#EF4444)

### 4. Real-Time Calculation Flow

```
User adjusts slider
       ↓
Debounce 300ms
       ↓
Recalculate indicators (client-side)
       ↓
Evaluate conditions against price data
       ↓
Detect signal trigger points
       ↓
Update chart markers
       ↓
Update stats display
```

**Performance:**
- Use Web Workers for heavy calculations
- Memoize results to avoid redundant calculations
- Debounce slider changes (300ms)
- Cache price data per symbol

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Basic chart display with price data

**Tasks:**
1. Create `InteractiveChartBuilder/index.tsx` with split layout
2. Add stock symbol selector dropdown
3. Fetch historical price data endpoint (`GET /api/v1/market-data/history/{symbol}`)
4. Render candlestick chart using Recharts
5. Add volume bars at bottom
6. Add time range selector (1M, 3M, 6M, 1Y)

**Deliverable:** Working chart that displays AAPL price history

---

### Phase 2: Indicator Overlays (Week 2)
**Goal:** Display calculated indicators on chart

**Tasks:**
1. Install `technicalindicators` npm package
2. Create `useIndicatorCalculation.ts` hook
3. Implement RSI calculation and display (separate panel)
4. Implement SMA/EMA lines on price chart
5. Implement Bollinger Bands visualization
6. Implement MACD histogram display
7. Add indicator toggles in right panel

**Deliverable:** Chart with multiple indicators overlaid, toggleable

---

### Phase 3: Interactive Controls (Week 3)
**Goal:** Real-time parameter adjustment

**Tasks:**
1. Create `IndicatorPanel.tsx` with collapsible sections
2. Create `ParameterSlider.tsx` component (reusable)
3. Add indicator selector dropdown with icons
4. Add period sliders (5-200 range) for SMA/EMA/RSI
5. Add threshold sliders for comparison values
6. Implement real-time recalculation on change
7. Add "Show on chart" toggle for each indicator

**Deliverable:** Sliders adjust indicators in real-time

---

### Phase 4: Signal Detection (Week 4)
**Goal:** Visualize when buy/sell conditions trigger

**Tasks:**
1. Create `useSignalSimulation.ts` hook
2. Port condition evaluation logic from backend
3. Implement signal detection (scan historical data)
4. Create `SignalMarkers.tsx` component
5. Add green/red triangle markers on chart
6. Display signal count and win rate estimate
7. Add hover tooltips for signal details

**Deliverable:** Triangle markers appear when conditions met

---

### Phase 5: Backend Preview API (Week 5)
**Goal:** Server-side validation and heavy computation

**Tasks:**
1. Create `POST /api/v1/algorithms/visual/preview` endpoint
2. Reuse indicator calculation from `backtesting_service.py`
3. Add condition evaluation for signal detection
4. Return annotated price data with signals
5. Calculate quick stats (signal count, simulated trades)
6. Add error handling and validation

**Deliverable:** Backend API that validates and enriches preview data

---

### Phase 6: Strategy Templates (Week 6)
**Goal:** One-click strategy presets

**Tasks:**
1. Create `StrategyTemplates.tsx` component
2. Define template configurations:
   - RSI Oversold: RSI < 30 entry, RSI > 70 exit
   - MA Crossover: SMA(20) crosses above SMA(50)
   - Bollinger Breakout: Price crosses below lower band
   - MACD Signal: MACD crosses above signal line
3. Add template selector buttons
4. Load template → Populate conditions → Update chart
5. Store templates in database for reuse

**Deliverable:** Working strategy templates

---

### Phase 7: Integration & Polish (Week 7)
**Goal:** Integrate into main algorithm flow

**Tasks:**
1. Update algorithm creation page with third option
2. Add "Interactive Chart Builder" button
3. Save algorithm from interactive builder (same data structure)
4. Add loading states and spinners
5. Add error handling and user feedback
6. Responsive design for mobile/tablet
7. Performance optimization (memoization, lazy loading)
8. User testing and bug fixes

**Deliverable:** Fully integrated interactive chart builder

---

## Technical Specifications

### Frontend Dependencies (Add to package.json)
```json
{
  "dependencies": {
    "technicalindicators": "^3.1.0",  // Client-side indicator calculations
    "recharts": "^2.5.0",              // Already installed
    "react-window": "^1.8.10"          // Virtualization for large datasets
  }
}
```

### Backend API Specs

#### Endpoint: `POST /api/v1/algorithms/visual/preview`

**Request:**
```json
{
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-10-11",
  "visual_config": {
    "entry_conditions": [
      {
        "type": "indicator_comparison",
        "indicator": "RSI",
        "period": 14,
        "operator": "less_than",
        "value": 30
      }
    ],
    "exit_conditions": [
      {
        "type": "indicator_comparison",
        "indicator": "RSI",
        "period": 14,
        "operator": "greater_than",
        "value": 70
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "price_data": [
      {
        "date": "2024-01-02",
        "open": 185.5,
        "high": 187.2,
        "low": 184.8,
        "close": 186.5,
        "volume": 52000000
      }
      // ... more days
    ],
    "indicators": {
      "RSI_14": [null, null, ..., 28.5, 32.1, 45.6],
      "SMA_20": [null, ..., 185.2, 186.1],
      "EMA_50": [null, ..., 182.5, 183.0]
    },
    "signals": {
      "buy": [
        {
          "date": "2024-01-15",
          "price": 180.5,
          "reason": "RSI (28.5) < 30"
        }
      ],
      "sell": [
        {
          "date": "2024-01-22",
          "price": 188.2,
          "reason": "RSI (72.3) > 70"
        }
      ]
    },
    "stats": {
      "total_signals": 15,
      "complete_trades": 13,
      "win_rate": 67.5,
      "estimated_pnl": 4250.00,
      "estimated_return_pct": 4.25
    }
  }
}
```

#### Endpoint: `GET /api/v1/market-data/history/{symbol}`

**Query Parameters:**
- `start_date`: ISO date string
- `end_date`: ISO date string
- `interval`: "1d" (daily), "1h" (hourly)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "data": [
      {
        "date": "2024-01-02T00:00:00Z",
        "open": 185.5,
        "high": 187.2,
        "low": 184.8,
        "close": 186.5,
        "volume": 52000000
      }
    ]
  }
}
```

---

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                           │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  Chart Display   │         │  Control Panel       │     │
│  │  - Price Chart   │         │  - Stock Selector    │     │
│  │  - Indicators    │         │  - Condition Builder │     │
│  │  - Signal Marks  │◄────────┤  - Sliders          │     │
│  └──────────────────┘         │  - Templates         │     │
│                                └──────────────────────┘     │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend State Management                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  useChartData: Fetch & cache price data             │  │
│  │  useIndicatorCalculation: Calculate RSI, SMA, etc.  │  │
│  │  useSignalSimulation: Detect trigger points         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  GET /market-data/history/{symbol}                 │    │
│  │  POST /algorithms/visual/preview                   │    │
│  │  POST /algorithms (save algorithm)                 │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Services                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  YahooFinanceProvider: Fetch historical data      │    │
│  │  BacktestingService: Calculate indicators         │    │
│  │  VisualAlgorithmCompiler: Evaluate conditions     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## User Flow Examples

### Example 1: RSI Oversold Strategy

1. User clicks "Create Algorithm" → "Interactive Chart Builder"
2. Chart loads with AAPL, last 3 months of data
3. User clicks "Add Entry Condition"
4. Selects "Indicator Comparison" → "RSI"
5. RSI line appears in panel below price chart (purple line, 0-100 scale)
6. User adjusts period slider to 14 (default is already 14)
7. User selects operator "Less than (<)"
8. User drags value slider to 30
9. **Green triangles (▲) appear** on chart wherever RSI drops below 30
10. Stats update: "15 buy signals detected"
11. User clicks "Add Exit Condition"
12. Selects RSI > 70
13. **Red triangles (▼) appear** on chart
14. Stats update: "13 complete trades, 67% win rate, +$4,250"
15. User clicks "Save Algorithm"
16. Algorithm saved, user can now backtest or run live

### Example 2: Moving Average Crossover

1. User loads Interactive Chart Builder
2. Clicks template button: "MA Crossover"
3. Chart instantly shows:
   - Blue line: Price
   - Orange line: SMA(20)
   - Green line: SMA(50)
   - Green triangles: When SMA(20) crosses above SMA(50)
   - Red triangles: When SMA(20) crosses below SMA(50)
4. User adjusts SMA(20) period slider from 20 to 15
5. Chart updates instantly, signal markers shift
6. User satisfied, clicks "Save Algorithm"

### Example 3: Custom Multi-Condition Strategy

1. User creates custom strategy:
   - Entry: RSI < 30 AND Price < SMA(50)
   - Exit: RSI > 70 OR Price > SMA(20)
2. User toggles "Show on Chart" for all indicators
3. Chart shows:
   - RSI panel below
   - SMA(20) and SMA(50) on price chart
   - Green triangles only where BOTH conditions met
   - Red triangles where EITHER exit condition met
4. User hovers over green triangle → Tooltip shows:
   ```
   Buy Signal - Jan 15, 2024
   Price: $180.50
   RSI: 28.5 (< 30) ✓
   Price vs SMA(50): $180.50 < $185.20 ✓
   ```
5. User saves algorithm

---

## Benefits Over Current Visual Builder

| Feature | Current Visual Builder | Interactive Chart Builder |
|---------|----------------------|--------------------------|
| **Visual Feedback** | None until backtest | Real-time on chart |
| **Signal Preview** | Run full backtest | Instant preview |
| **Parameter Tuning** | Type numbers, guess | Sliders with live updates |
| **Learning Curve** | Need to understand indicators | See indicators in action |
| **Confidence** | Blind until backtest | See what you're getting |
| **Speed** | Slow (backtest each change) | Fast (instant feedback) |
| **Flexibility** | Text-based forms | Visual + Interactive |

---

## Success Metrics

**User Engagement:**
- 50%+ of new algorithms created via Interactive Chart Builder (vs. Visual Builder)
- Average time to create algorithm < 5 minutes
- 80%+ of users run preview before saving

**Quality Indicators:**
- Fewer algorithms with "0 signals" (better configuration)
- Higher backtest success rate (users tune parameters better)
- Reduced support tickets about "how to use indicators"

**Technical Performance:**
- Chart loads in < 2 seconds
- Indicator recalculation in < 300ms
- Preview API response in < 1 second

---

## Future Enhancements (Post-MVP)

1. **Multi-Symbol Testing**: Test strategy across 10 symbols simultaneously
2. **Real-Time Data**: Live price updates during market hours
3. **Advanced Charting**: Candlestick patterns, Fibonacci retracements
4. **AI Suggestions**: "Based on your conditions, consider adding..."
5. **Shareable Strategies**: Export/import strategy configurations
6. **Community Templates**: Browse strategies shared by other users
7. **Walk-Forward Analysis**: Test on rolling time windows
8. **Custom Indicators**: Upload custom indicator formulas
9. **Alert Zones**: Visual zones where alerts would trigger
10. **Mobile App**: Native iOS/Android interactive builder

---

## Security & Performance Considerations

**Rate Limiting:**
- Limit preview API calls to 30/minute per user
- Cache preview results for 5 minutes (same params)

**Data Storage:**
- Cache historical price data in Redis (1-day TTL)
- Store algorithm configurations in PostgreSQL (same as current)

**Client-Side Security:**
- Validate all inputs before sending to backend
- Sanitize user-provided threshold values
- Prevent XSS in chart tooltips

**Performance Optimization:**
- Use Web Workers for heavy calculations
- Implement virtual scrolling for large datasets
- Lazy load indicator libraries
- Compress API responses (gzip)

---

## Rollout Strategy

### Phase 1: Internal Beta (2 weeks)
- Deploy to staging environment
- Internal team testing (5-10 users)
- Collect feedback, fix critical bugs

### Phase 2: Limited Beta (4 weeks)
- Invite 50 active users
- Feature flag: `enable_interactive_chart_builder`
- Monitor usage metrics and performance
- Iterate based on feedback

### Phase 3: Public Launch (Week 12)
- Announce in product updates
- Create tutorial videos
- Monitor adoption rates
- Gather user feedback for iteration

---

## Conclusion

The Interactive Chart Builder transforms algorithm creation from a **text-based form experience** into a **visual, real-time, interactive experience**. Users will see exactly how their strategies would have performed on historical data before committing to backtests or live trading.

**Core Value Proposition:**
> "Build trading strategies visually. See signals as you configure them. Save time. Trade with confidence."

This feature positions the platform competitively with professional tools like TradingView, QuantConnect, and Quantopian while maintaining ease of use for beginners.
