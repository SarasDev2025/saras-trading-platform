import { useMemo, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, TrendingUp, Activity, DollarSign } from 'lucide-react';
import {
  ComposedChart,
  Line,
  Scatter,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface PriceDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi?: number;
  sma_20?: number;
  sma_50?: number;
  ema_20?: number;
}

interface Signal {
  date: string;
  type: 'buy' | 'sell';
  price: number;
  reason: string;
}

interface CompositePoint {
  date: string;
  composite_index: number;
}

interface ChartDisplayProps {
  symbol: string;
  selectedSymbols: string[];
  timeRange: string;
  priceDataMap: Record<string, PriceDataPoint[]>;
  compositeData: CompositePoint[];
  signals: Signal[];
  loading: boolean;
  onSymbolChange: (symbol: string) => void;
  onTimeRangeChange: (range: string) => void;
}

const POPULAR_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'SPY', 'QQQ'];

const SYMBOL_COLORS = [
  'rgb(59, 130, 246)',   // Blue (primary)
  'rgb(239, 68, 68)',    // Red
  'rgb(34, 197, 94)',    // Green
  'rgb(251, 146, 60)',   // Orange
  'rgb(168, 85, 247)',   // Purple
  'rgb(236, 72, 153)',   // Pink
  'rgb(14, 165, 233)',   // Cyan
  'rgb(234, 179, 8)',    // Yellow
  'rgb(20, 184, 166)',   // Teal
];

export function ChartDisplay({
  symbol,
  selectedSymbols,
  timeRange,
  priceDataMap,
  compositeData,
  signals,
  loading,
  onSymbolChange,
  onTimeRangeChange,
}: ChartDisplayProps) {
  const [chartMode, setChartMode] = useState<'normalized' | 'absolute'>('normalized');
  const [visibleSymbols, setVisibleSymbols] = useState<Set<string>>(new Set(selectedSymbols));

  // Sync visible symbols when selectedSymbols changes
  useEffect(() => {
    setVisibleSymbols(new Set(selectedSymbols));
  }, [selectedSymbols]);

  const toggleSymbolVisibility = (sym: string) => {
    setVisibleSymbols((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sym)) {
        newSet.delete(sym);
      } else {
        newSet.add(sym);
      }
      return newSet;
    });
  };

  const compositeMap = useMemo(() => {
    const map = new Map<string, number>();
    compositeData.forEach((point) => {
      const key = new Date(point.date).toISOString().split('T')[0];
      map.set(key, point.composite_index);
    });
    return map;
  }, [compositeData]);

  // Primary symbol data (with signals)
  const priceData = priceDataMap[symbol] || [];

  const chartData = useMemo(() => {
    if (!priceData || priceData.length === 0) return [];

    const signalMap = new Map<string, Signal[]>();
    signals.forEach((signal) => {
      const dateKey = new Date(signal.date).toISOString().split('T')[0];
      if (!signalMap.has(dateKey)) {
        signalMap.set(dateKey, []);
      }
      signalMap.get(dateKey)!.push(signal);
    });

    // Calculate base values for normalization
    const firstClose = priceData[0]?.close || 1;
    const firstSma20 = priceData.find(p => p.sma_20)?.sma_20 || 1;
    const firstSma50 = priceData.find(p => p.sma_50)?.sma_50 || 1;
    const firstEma20 = priceData.find(p => p.ema_20)?.ema_20 || 1;

    return priceData.map((point) => {
      const dateKey = new Date(point.date).toISOString().split('T')[0];
      const daySignals = signalMap.get(dateKey) || [];
      const buySignals = daySignals.filter((s) => s.type === 'buy');
      const sellSignals = daySignals.filter((s) => s.type === 'sell');
      const compositeValue = compositeMap.get(dateKey) || null;

      // Normalize or keep absolute values based on mode
      const normalizeValue = (value: number | undefined, baseValue: number) => {
        if (!value || chartMode === 'absolute') return value;
        return (value / baseValue) * 100;
      };

      const close = normalizeValue(point.close, firstClose);
      const high = normalizeValue(point.high, firstClose);
      const low = normalizeValue(point.low, firstClose);

      return {
        date: new Date(point.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        fullDate: point.date,
        close,
        high,
        low,
        absoluteClose: point.close,  // Keep absolute for tooltip
        volume: point.volume,
        rsi: point.rsi,
        sma_20: normalizeValue(point.sma_20, firstSma20),
        sma_50: normalizeValue(point.sma_50, firstSma50),
        ema_20: normalizeValue(point.ema_20, firstEma20),
        composite: compositeValue,
        // Enhanced signal positioning
        buySignal: buySignals.length > 0 ? (low ? low - (chartMode === 'normalized' ? 3 : low * 0.02) : null) : null,
        sellSignal: sellSignals.length > 0 ? (high ? high + (chartMode === 'normalized' ? 3 : high * 0.02) : null) : null,
        buySignalData: buySignals[0] || null,
        sellSignalData: sellSignals[0] || null,
      };
    });
  }, [priceData, signals, compositeMap, chartMode]);

  // Multi-symbol data for overlay
  const multiSymbolData = useMemo(() => {
    const result: Record<string, any[]> = {};

    visibleSymbols.forEach((sym) => {
      const symData = priceDataMap[sym];
      if (!symData || symData.length === 0) return;

      const firstClose = symData[0]?.close || 1;

      result[sym] = symData.map((point) => {
        const normalizeValue = (value: number | undefined, baseValue: number) => {
          if (!value || chartMode === 'absolute') return value;
          return (value / baseValue) * 100;
        };

        return {
          date: new Date(point.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          }),
          fullDate: point.date,
          close: normalizeValue(point.close, firstClose),
          absoluteClose: point.close,
        };
      });
    });

    return result;
  }, [priceDataMap, visibleSymbols, chartMode]);

  // Merge all symbol data into a unified timeline
  const unifiedChartData = useMemo(() => {
    if (chartData.length === 0) return [];

    // Start with primary symbol data (which has signals)
    const unified = chartData.map((point) => ({ ...point }));

    // Add data from other visible symbols
    visibleSymbols.forEach((sym) => {
      if (sym === symbol) return; // Skip primary symbol

      const symData = multiSymbolData[sym];
      if (!symData) return;

      // Create a map for quick lookup
      const symDataMap = new Map();
      symData.forEach((point) => {
        symDataMap.set(point.fullDate, point);
      });

      // Merge into unified data
      unified.forEach((point: any) => {
        const symPoint = symDataMap.get(point.fullDate);
        if (symPoint) {
          point[`${sym}_close`] = symPoint.close;
          point[`${sym}_absolute`] = symPoint.absoluteClose;
        }
      });
    });

    return unified;
  }, [chartData, multiSymbolData, visibleSymbols, symbol]);

  const symbolOptions = useMemo(
    () => Array.from(new Set([...selectedSymbols, ...POPULAR_SYMBOLS])),
    [selectedSymbols]
  );

  const getSymbolColor = (sym: string, index: number) => {
    return SYMBOL_COLORS[index % SYMBOL_COLORS.length];
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading chart data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Live Chart Preview
          </CardTitle>
          <div className="flex gap-2">
            <Select value={symbol} onValueChange={onSymbolChange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {symbolOptions.map((sym) => (
                  <SelectItem key={sym} value={sym}>
                    {sym}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Chart Mode Toggle */}
            <div className="flex gap-1">
              <Button
                variant={chartMode === 'normalized' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setChartMode('normalized')}
                className="flex items-center gap-1"
              >
                <Activity className="h-3 w-3" />
                Normalized
              </Button>
              <Button
                variant={chartMode === 'absolute' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setChartMode('absolute')}
                className="flex items-center gap-1"
              >
                <DollarSign className="h-3 w-3" />
                Absolute
              </Button>
            </div>

            <div className="flex gap-1">
              {['1M', '3M', '6M', '1Y'].map((range) => (
                <Button
                  key={range}
                  variant={timeRange === range ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onTimeRangeChange(range)}
                >
                  {range}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Multi-Symbol Checkboxes */}
        {selectedSymbols.length > 1 && (
          <div className="mt-4 pt-4 border-t">
            <Label className="text-sm font-medium mb-2 block">Visible Symbols</Label>
            <div className="flex flex-wrap gap-3">
              {selectedSymbols.map((sym, index) => (
                <div key={sym} className="flex items-center space-x-2">
                  <Checkbox
                    id={`symbol-${sym}`}
                    checked={visibleSymbols.has(sym)}
                    onCheckedChange={() => toggleSymbolVisibility(sym)}
                  />
                  <label
                    htmlFor={`symbol-${sym}`}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex items-center gap-2"
                  >
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getSymbolColor(sym, index) }}
                    />
                    {sym}
                  </label>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-[600px]">
            <p className="text-muted-foreground">No data available for the selected symbols.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={unifiedChartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                  <YAxis
                    yAxisId="price"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(value) => chartMode === 'normalized' ? `${value.toFixed(0)}` : `$${value.toFixed(0)}`}
                    label={chartMode === 'normalized' ? { value: 'Index (Base 100)', angle: -90, position: 'insideLeft', style: { fontSize: 11 } } : undefined}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload || payload.length === 0) return null;
                      const data = payload[0].payload;
                      return (
                        <div className="bg-background border rounded-lg p-3 shadow-lg">
                          <p className="font-semibold text-sm mb-2">{data.fullDate}</p>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">
                                {chartMode === 'normalized' ? 'Index:' : 'Close:'}
                              </span>
                              <span className="font-medium">
                                {chartMode === 'normalized'
                                  ? `${data.close?.toFixed(2)} (${data.absoluteClose ? '$' + data.absoluteClose.toFixed(2) : 'N/A'})`
                                  : `$${data.close?.toFixed(2)}`
                                }
                              </span>
                            </div>
                            {typeof data.composite === 'number' && (
                              <div className="flex justify-between gap-4">
                                <span className="text-muted-foreground">Composite:</span>
                                <span className="font-medium">{data.composite.toFixed(2)}</span>
                              </div>
                            )}
                            {data.buySignalData && (
                              <div className="pt-2 mt-2 border-t">
                                <div className="flex items-center gap-1 text-green-600 font-medium">
                                  ▲ BUY SIGNAL
                                </div>
                                <p className="text-muted-foreground">{data.buySignalData.reason}</p>
                              </div>
                            )}
                            {data.sellSignalData && (
                              <div className="pt-2 mt-2 border-t">
                                <div className="flex items-center gap-1 text-red-600 font-medium">
                                  ▼ SELL SIGNAL
                                </div>
                                <p className="text-muted-foreground">{data.sellSignalData.reason}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Legend />

                  {/* Primary Symbol Line */}
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="close"
                    stroke={getSymbolColor(symbol, selectedSymbols.indexOf(symbol))}
                    strokeWidth={2}
                    dot={false}
                    name={`${symbol} Close`}
                  />

                  {/* Additional Symbol Lines */}
                  {selectedSymbols.map((sym, index) => {
                    if (sym === symbol || !visibleSymbols.has(sym)) return null;
                    return (
                      <Line
                        key={sym}
                        yAxisId="price"
                        type="monotone"
                        dataKey={`${sym}_close`}
                        stroke={getSymbolColor(sym, index)}
                        strokeWidth={1.5}
                        dot={false}
                        name={`${sym} Close`}
                      />
                    );
                  })}

                  {typeof compositeData !== 'undefined' && compositeData.length > 0 && (
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="composite"
                      stroke="rgb(139, 92, 246)"
                      strokeWidth={1.5}
                      strokeDasharray="6 3"
                      dot={false}
                      name="Composite Index"
                    />
                  )}
                  {chartData.some((d) => d.sma_20) && (
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="sma_20"
                      stroke="rgb(251, 146, 60)"
                      strokeWidth={1.5}
                      dot={false}
                      name="SMA 20"
                    />
                  )}
                  {chartData.some((d) => d.sma_50) && (
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="sma_50"
                      stroke="rgb(34, 197, 94)"
                      strokeWidth={1.5}
                      dot={false}
                      name="SMA 50"
                    />
                  )}
                  <Scatter
                    yAxisId="price"
                    dataKey="buySignal"
                    fill="rgb(34, 197, 94)"
                    shape="triangle"
                    name="Buy Signal"
                    r={8}
                  />
                  <Scatter
                    yAxisId="price"
                    dataKey="sellSignal"
                    fill="rgb(239, 68, 68)"
                    shape="triangle"
                    name="Sell Signal"
                    r={8}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {unifiedChartData.some((d) => d.rsi) && (
              <div className="h-[150px]">
                <p className="text-sm font-medium mb-2">RSI</p>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={unifiedChartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <ReferenceLine y={70} stroke="red" strokeDasharray="3 3" />
                    <ReferenceLine y={30} stroke="green" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="rsi" stroke="rgb(147, 51, 234)" strokeWidth={2} dot={false} name="RSI" />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="h-[100px]">
              <p className="text-sm font-medium mb-2">Volume</p>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={unifiedChartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`} />
                  <Tooltip formatter={(value: any) => `${(value / 1000000).toFixed(2)}M`} />
                  <Bar dataKey="volume" fill="rgb(156, 163, 175)" opacity={0.6} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
