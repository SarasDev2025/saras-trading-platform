import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot, TooltipProps } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface Trade {
  id: string;
  symbol: string;
  action: string;
  executed_at: string;
  price: number;
  quantity: number;
}

interface EquityCurveData {
  date: string;
  equity: number;
  cumulative_pnl: number;
  daily_pnl: number;
}

interface EquityCurveChartProps {
  data: EquityCurveData[];
  trades?: Trade[];
  title?: string;
}

export function EquityCurveChart({ data, trades = [], title = "Algorithm Performance" }: EquityCurveChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card className="chart-container">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 carbon-blue" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-400">
            No performance data available yet
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate summary stats
  const startEquity = data[0]?.equity || 0;
  const endEquity = data[data.length - 1]?.equity || 0;
  const totalReturn = endEquity - startEquity;
  const totalReturnPct = startEquity > 0 ? ((endEquity - startEquity) / startEquity) * 100 : 0;

  // Merge trades with equity data by date
  const tradesByDate = new Map<string, Trade[]>();
  trades.forEach(trade => {
    const tradeDate = trade.executed_at.split('T')[0];
    if (!tradesByDate.has(tradeDate)) {
      tradesByDate.set(tradeDate, []);
    }
    tradesByDate.get(tradeDate)!.push(trade);
  });

  // Enhance data with trade markers
  const enhancedData = data.map(point => {
    const pointDate = point.date.split('T')[0];
    const dayTrades = tradesByDate.get(pointDate) || [];
    return {
      ...point,
      hasTrades: dayTrades.length > 0,
      trades: dayTrades,
      buyTrades: dayTrades.filter(t => t.action === 'buy').length,
      sellTrades: dayTrades.filter(t => t.action === 'sell').length,
    };
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (!active || !payload || !payload[0]) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-70)] p-3 rounded-lg shadow-lg">
        <p className="text-white font-medium mb-2">{formatDate(data.date)}</p>
        <div className="space-y-1 text-sm">
          <p className="text-gray-300">
            Equity: <span className="text-white font-medium">{formatCurrency(data.equity)}</span>
          </p>
          <p className="text-gray-300">
            Daily P&L: <span className={`font-medium ${data.daily_pnl >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
              {data.daily_pnl >= 0 ? '+' : ''}{formatCurrency(data.daily_pnl)}
            </span>
          </p>
          <p className="text-gray-300">
            Cumulative P&L: <span className={`font-medium ${data.cumulative_pnl >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
              {data.cumulative_pnl >= 0 ? '+' : ''}{formatCurrency(data.cumulative_pnl)}
            </span>
          </p>
          {data.hasTrades && (
            <div className="mt-2 pt-2 border-t border-[var(--carbon-gray-70)]">
              <p className="text-[var(--carbon-blue)] font-medium">
                {data.buyTrades} Buy, {data.sellTrades} Sell
              </p>
              <div className="mt-1 space-y-1">
                {data.trades.slice(0, 3).map((trade: Trade, i: number) => (
                  <p key={i} className="text-xs text-gray-400">
                    {trade.action.toUpperCase()} {trade.quantity} {trade.symbol} @ {formatCurrency(trade.price)}
                  </p>
                ))}
                {data.trades.length > 3 && (
                  <p className="text-xs text-gray-500">+{data.trades.length - 3} more...</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className="chart-container">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 carbon-blue" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-gray-400">Total Return</p>
              <p className={`text-lg font-bold ${totalReturn >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                {totalReturn >= 0 ? '+' : ''}{formatCurrency(totalReturn)}
              </p>
              <p className={`text-xs ${totalReturn >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                ({totalReturn >= 0 ? '+' : ''}{totalReturnPct.toFixed(2)}%)
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-400">Current Equity</p>
              <p className="text-lg font-bold text-white">
                {formatCurrency(endEquity)}
              </p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={enhancedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--carbon-gray-70)"
              opacity={0.3}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--carbon-gray-50)"
              tick={{ fill: 'var(--carbon-gray-50)' }}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="var(--carbon-gray-50)"
              tick={{ fill: 'var(--carbon-gray-50)' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ color: 'var(--carbon-gray-50)' }}
              iconType="line"
            />

            {/* Main equity curve */}
            <Line
              type="monotone"
              dataKey="equity"
              stroke="var(--carbon-blue)"
              strokeWidth={2}
              dot={false}
              name="Portfolio Value"
              activeDot={{ r: 6, fill: 'var(--carbon-blue)' }}
            />

            {/* Trade markers */}
            {enhancedData.map((point, index) => {
              if (!point.hasTrades) return null;

              return (
                <ReferenceDot
                  key={`trade-${index}`}
                  x={point.date}
                  y={point.equity}
                  r={point.buyTrades > 0 && point.sellTrades > 0 ? 6 : 5}
                  fill={point.buyTrades > point.sellTrades ? 'var(--success-green)' : 'var(--danger-red)'}
                  stroke="white"
                  strokeWidth={2}
                  opacity={0.8}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>

        {/* Legend for trade markers */}
        {trades.length > 0 && (
          <div className="flex items-center justify-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[var(--success-green)] border-2 border-white"></div>
              <span className="text-gray-400">Buy Trades</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[var(--danger-red)] border-2 border-white"></div>
              <span className="text-gray-400">Sell Trades</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
