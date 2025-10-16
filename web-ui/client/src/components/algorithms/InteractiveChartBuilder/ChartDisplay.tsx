import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, TrendingUp } from 'lucide-react';
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
import { Condition } from './index';

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

interface ChartDisplayProps {
  symbol: string;
  timeRange: string;
  priceData: PriceDataPoint[];
  entryConditions: Condition[];
  exitConditions: Condition[];
  signals: Signal[];
  loading: boolean;
  onSymbolChange: (symbol: string) => void;
  onTimeRangeChange: (range: string) => void;
}

const POPULAR_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'SPY', 'QQQ'];

export function ChartDisplay({
  symbol,
  timeRange,
  priceData,
  signals,
  loading,
  onSymbolChange,
  onTimeRangeChange,
}: ChartDisplayProps) {
  // Prepare chart data with signals
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

    return priceData.map((point) => {
      const dateKey = new Date(point.date).toISOString().split('T')[0];
      const daySignals = signalMap.get(dateKey) || [];
      const buySignals = daySignals.filter((s) => s.type === 'buy');
      const sellSignals = daySignals.filter((s) => s.type === 'sell');

      return {
        date: new Date(point.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        fullDate: point.date,
        close: point.close,
        high: point.high,
        low: point.low,
        volume: point.volume,
        rsi: point.rsi,
        sma_20: point.sma_20,
        sma_50: point.sma_50,
        ema_20: point.ema_20,
        buySignal: buySignals.length > 0 ? point.low * 0.98 : null,
        sellSignal: sellSignals.length > 0 ? point.high * 1.02 : null,
        buySignalData: buySignals[0] || null,
        sellSignalData: sellSignals[0] || null,
      };
    });
  }, [priceData, signals]);

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
            {/* Symbol Selector */}
            <Select value={symbol} onValueChange={onSymbolChange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {POPULAR_SYMBOLS.map((sym) => (
                  <SelectItem key={sym} value={sym}>
                    {sym}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Time Range Selector */}
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
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-[600px]">
            <p className="text-muted-foreground">No data available</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Price Chart */}
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    yAxisId="price"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
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
                              <span className="text-muted-foreground">Close:</span>
                              <span className="font-medium">${data.close.toFixed(2)}</span>
                            </div>
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

                  {/* Price Line */}
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="close"
                    stroke="rgb(59, 130, 246)"
                    strokeWidth={2}
                    dot={false}
                    name="Price"
                  />

                  {/* Moving Averages */}
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

                  {/* Buy Signals */}
                  <Scatter
                    yAxisId="price"
                    dataKey="buySignal"
                    fill="rgb(34, 197, 94)"
                    shape="triangle"
                    name="Buy"
                  />

                  {/* Sell Signals */}
                  <Scatter
                    yAxisId="price"
                    dataKey="sellSignal"
                    fill="rgb(239, 68, 68)"
                    shape="triangleDown"
                    name="Sell"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* RSI Chart (if RSI data exists) */}
            {chartData.some((d) => d.rsi) && (
              <div className="h-[150px]">
                <p className="text-sm font-medium mb-2">RSI</p>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <ReferenceLine y={70} stroke="red" strokeDasharray="3 3" />
                    <ReferenceLine y={30} stroke="green" strokeDasharray="3 3" />
                    <Line
                      type="monotone"
                      dataKey="rsi"
                      stroke="rgb(147, 51, 234)"
                      strokeWidth={2}
                      dot={false}
                      name="RSI"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Volume Chart */}
            <div className="h-[100px]">
              <p className="text-sm font-medium mb-2">Volume</p>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
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
