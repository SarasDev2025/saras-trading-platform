import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PriceDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Trade {
  date: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  value: number;
  pnl?: number;
}

interface PriceChartWithSignalsProps {
  symbol: string;
  priceData: PriceDataPoint[];
  trades: Trade[];
}

export function PriceChartWithSignals({ symbol, priceData, trades }: PriceChartWithSignalsProps) {
  // Combine price data with trade signals
  const chartData = useMemo(() => {
    if (!priceData || priceData.length === 0) return [];

    // Create a map of trades by date for quick lookup
    const tradesByDate = new Map<string, Trade[]>();
    trades
      .filter((t) => t.symbol === symbol)
      .forEach((trade) => {
        const dateKey = new Date(trade.date).toISOString().split('T')[0];
        if (!tradesByDate.has(dateKey)) {
          tradesByDate.set(dateKey, []);
        }
        tradesByDate.get(dateKey)!.push(trade);
      });

    // Combine price data with signals
    return priceData.map((point) => {
      const dateKey = new Date(point.date).toISOString().split('T')[0];
      const dayTrades = tradesByDate.get(dateKey) || [];

      const buyTrades = dayTrades.filter((t) => t.side === 'buy');
      const sellTrades = dayTrades.filter((t) => t.side === 'sell');

      return {
        date: new Date(point.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        fullDate: point.date,
        close: point.close,
        high: point.high,
        low: point.low,
        // Add buy signal marker
        buySignal: buyTrades.length > 0 ? point.low * 0.98 : null,
        buyTrade: buyTrades[0] || null,
        // Add sell signal marker
        sellSignal: sellTrades.length > 0 ? point.high * 1.02 : null,
        sellTrade: sellTrades[0] || null,
      };
    });
  }, [priceData, trades, symbol]);

  // Calculate statistics
  const stats = useMemo(() => {
    const symbolTrades = trades.filter((t) => t.symbol === symbol);
    const buyCount = symbolTrades.filter((t) => t.side === 'buy').length;
    const sellCount = symbolTrades.filter((t) => t.side === 'sell').length;
    const totalPnl = symbolTrades
      .filter((t) => t.pnl !== undefined)
      .reduce((sum, t) => sum + (t.pnl || 0), 0);

    return {
      trades: symbolTrades.length,
      buys: buyCount,
      sells: sellCount,
      pnl: totalPnl,
    };
  }, [trades, symbol]);

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">No price data available for {symbol}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {symbol}
              <Badge variant={stats.pnl >= 0 ? 'default' : 'destructive'}>
                {stats.pnl >= 0 ? '+' : ''}${stats.pnl.toFixed(2)}
              </Badge>
            </CardTitle>
            <CardDescription>
              {stats.trades} trades • {stats.buys} buys • {stats.sells} sells
            </CardDescription>
          </div>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-muted-foreground">Buy Signal</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-muted-foreground">Sell Signal</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
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
                tick={{ fontSize: 11 }}
                domain={['auto', 'auto']}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || payload.length === 0) return null;

                  const data = payload[0].payload;

                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-sm mb-2">
                        {new Date(data.fullDate).toLocaleDateString()}
                      </p>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Close:</span>
                          <span className="font-medium">${data.close.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">High:</span>
                          <span className="font-medium">${data.high.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Low:</span>
                          <span className="font-medium">${data.low.toFixed(2)}</span>
                        </div>

                        {data.buyTrade && (
                          <div className="pt-2 mt-2 border-t">
                            <div className="flex items-center gap-1 text-green-600 font-medium mb-1">
                              <TrendingUp className="h-3 w-3" />
                              BUY SIGNAL
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Qty:</span>
                              <span>{data.buyTrade.quantity}</span>
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Price:</span>
                              <span>${data.buyTrade.price.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Value:</span>
                              <span>${data.buyTrade.value.toFixed(2)}</span>
                            </div>
                          </div>
                        )}

                        {data.sellTrade && (
                          <div className="pt-2 mt-2 border-t">
                            <div className="flex items-center gap-1 text-red-600 font-medium mb-1">
                              <TrendingDown className="h-3 w-3" />
                              SELL SIGNAL
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Qty:</span>
                              <span>{data.sellTrade.quantity}</span>
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Price:</span>
                              <span>${data.sellTrade.price.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="text-muted-foreground">Value:</span>
                              <span>${data.sellTrade.value.toFixed(2)}</span>
                            </div>
                            {data.sellTrade.pnl !== undefined && (
                              <div className="flex justify-between gap-4">
                                <span className="text-muted-foreground">P&L:</span>
                                <span
                                  className={
                                    data.sellTrade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                                  }
                                >
                                  {data.sellTrade.pnl >= 0 ? '+' : ''}$
                                  {data.sellTrade.pnl.toFixed(2)}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }}
              />
              <Legend />

              {/* Price line */}
              <Line
                type="monotone"
                dataKey="close"
                stroke="rgb(59, 130, 246)"
                strokeWidth={2}
                dot={false}
                name="Price"
              />

              {/* Buy signals */}
              <Scatter
                dataKey="buySignal"
                fill="rgb(34, 197, 94)"
                shape="triangle"
                name="Buy"
              />

              {/* Sell signals */}
              <Scatter
                dataKey="sellSignal"
                fill="rgb(239, 68, 68)"
                shape="triangleDown"
                name="Sell"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
