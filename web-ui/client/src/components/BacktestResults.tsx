import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  PieChart,
  BarChart3,
  Download,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

interface BacktestMetrics {
  // Return metrics
  total_return: number;
  total_return_pct: number;
  annualized_return_pct: number;
  cagr_pct: number;
  avg_daily_return_pct: number;
  avg_monthly_return_pct: number;
  best_day_pct: number;
  worst_day_pct: number;

  // Risk metrics
  volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  alpha_pct?: number;
  beta?: number;

  // Drawdown metrics
  max_drawdown_pct: number;
  current_drawdown_pct: number;
  max_drawdown_duration_days: number;
  calmar_ratio: number;

  // Trade metrics
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
  expectancy: number;
  payoff_ratio: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
}

interface BacktestTrade {
  timestamp: string;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission: number;
  total_cost?: number;
  total_proceeds?: number;
}

interface EquityCurvePoint {
  timestamp: string;
  equity: number;
  cash: number;
}

interface BacktestResults {
  backtest_id: string;
  algorithm_id: string;
  status: string;
  initial_capital: number;
  final_equity: number;
  start_date: string;
  end_date: string;
  metrics?: BacktestMetrics;
  equity_curve?: EquityCurvePoint[];
  trades?: BacktestTrade[];
  total_trades: number;
  created_at: string;
  completed_at?: string;
  error?: string;
}

interface BacktestResultsProps {
  backtestId?: string;
  algorithmId?: string;
  onClose?: () => void;
}

export const BacktestResults: React.FC<BacktestResultsProps> = ({
  backtestId,
  algorithmId,
  onClose
}) => {
  const [results, setResults] = useState<BacktestResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (backtestId) {
      fetchBacktestResults();
    } else if (algorithmId) {
      fetchLatestBacktest();
    }
  }, [backtestId, algorithmId]);

  const fetchBacktestResults = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/backtests/${backtestId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch backtest results');

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestBacktest = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/backtests/algorithm/${algorithmId}?limit=1`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch backtest results');

      const data = await response.json();
      if (data.backtests && data.backtests.length > 0) {
        setResults(data.backtests[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number, decimals: number = 2) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const downloadCSV = () => {
    if (!results || !results.trades) return;

    const headers = ['Timestamp', 'Symbol', 'Action', 'Quantity', 'Price', 'Commission', 'Total'];
    const rows = results.trades.map(trade => [
      trade.timestamp,
      trade.symbol,
      trade.action,
      trade.quantity,
      trade.price,
      trade.commission,
      trade.total_cost || trade.total_proceeds || 0
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backtest-${results.backtest_id}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading backtest results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-500">{error}</p>
        {onClose && (
          <Button onClick={onClose} className="mt-4">Close</Button>
        )}
      </div>
    );
  }

  if (!results) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">No backtest results available</p>
        {onClose && (
          <Button onClick={onClose} className="mt-4">Close</Button>
        )}
      </div>
    );
  }

  const metrics = results.metrics;
  const equityCurve = results.equity_curve || [];
  const trades = results.trades || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Backtest Results</h2>
          <p className="text-sm text-gray-500">
            {formatDate(results.start_date)} - {formatDate(results.end_date)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={downloadCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose}>Close</Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Return</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(results.final_equity - results.initial_capital)}
            </div>
            <div className={`text-sm flex items-center ${
              metrics && metrics.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {metrics && metrics.total_return_pct >= 0 ? (
                <ArrowUpRight className="w-4 h-4 mr-1" />
              ) : (
                <ArrowDownRight className="w-4 h-4 mr-1" />
              )}
              {metrics && formatPercent(metrics.total_return_pct)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sharpe Ratio</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics ? metrics.sharpe_ratio.toFixed(2) : 'N/A'}
            </div>
            <div className="text-sm text-gray-500">Risk-adjusted return</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Max Drawdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {metrics ? formatPercent(metrics.max_drawdown_pct) : 'N/A'}
            </div>
            <div className="text-sm text-gray-500">
              {metrics ? `${metrics.max_drawdown_duration_days} days` : 'N/A'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Win Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics ? formatPercent(metrics.win_rate_pct, 1) : 'N/A'}
            </div>
            <div className="text-sm text-gray-500">
              {metrics ? `${metrics.winning_trades}/${metrics.total_trades} trades` : 'N/A'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for detailed analysis */}
      <Tabs defaultValue="equity-curve" className="w-full">
        <TabsList>
          <TabsTrigger value="equity-curve">Equity Curve</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
        </TabsList>

        {/* Equity Curve Tab */}
        <TabsContent value="equity-curve" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Value Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={equityCurve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => formatDate(value)}
                  />
                  <YAxis
                    tickFormatter={(value) => formatCurrency(value)}
                  />
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    labelFormatter={(label) => formatDate(label)}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="equity"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                    name="Portfolio Value"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Return Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Return Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {metrics && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Return</span>
                      <span className="font-medium">{formatPercent(metrics.total_return_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">CAGR</span>
                      <span className="font-medium">{formatPercent(metrics.cagr_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Avg Daily Return</span>
                      <span className="font-medium">{formatPercent(metrics.avg_daily_return_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Best Day</span>
                      <span className="font-medium text-green-600">{formatPercent(metrics.best_day_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Worst Day</span>
                      <span className="font-medium text-red-600">{formatPercent(metrics.worst_day_pct)}</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Risk Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {metrics && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Volatility</span>
                      <span className="font-medium">{formatPercent(metrics.volatility_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Sharpe Ratio</span>
                      <span className="font-medium">{metrics.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Sortino Ratio</span>
                      <span className="font-medium">{metrics.sortino_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Max Drawdown</span>
                      <span className="font-medium text-red-600">{formatPercent(metrics.max_drawdown_pct)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Calmar Ratio</span>
                      <span className="font-medium">{metrics.calmar_ratio.toFixed(2)}</span>
                    </div>
                    {metrics.beta !== undefined && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Beta</span>
                          <span className="font-medium">{metrics.beta.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Alpha</span>
                          <span className="font-medium">{formatPercent(metrics.alpha_pct || 0)}</span>
                        </div>
                      </>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Trade Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Trade Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {metrics && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Trades</span>
                      <span className="font-medium">{metrics.total_trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Win Rate</span>
                      <span className="font-medium">{formatPercent(metrics.win_rate_pct, 1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Profit Factor</span>
                      <span className="font-medium">{metrics.profit_factor.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Avg Win</span>
                      <span className="font-medium text-green-600">{formatCurrency(metrics.avg_win)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Avg Loss</span>
                      <span className="font-medium text-red-600">{formatCurrency(metrics.avg_loss)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Expectancy</span>
                      <span className="font-medium">{formatCurrency(metrics.expectancy)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Max Consecutive Wins</span>
                      <span className="font-medium">{metrics.max_consecutive_wins}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Max Consecutive Losses</span>
                      <span className="font-medium">{metrics.max_consecutive_losses}</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trades Tab */}
        <TabsContent value="trades" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trade History ({trades.length} trades)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Date</th>
                      <th className="text-left p-2">Symbol</th>
                      <th className="text-left p-2">Action</th>
                      <th className="text-right p-2">Quantity</th>
                      <th className="text-right p-2">Price</th>
                      <th className="text-right p-2">Commission</th>
                      <th className="text-right p-2">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="p-2">{formatDate(trade.timestamp)}</td>
                        <td className="p-2 font-medium">{trade.symbol}</td>
                        <td className="p-2">
                          <Badge variant={trade.action === 'buy' ? 'default' : 'secondary'}>
                            {trade.action.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="p-2 text-right">{trade.quantity.toFixed(2)}</td>
                        <td className="p-2 text-right">{formatCurrency(trade.price)}</td>
                        <td className="p-2 text-right">{formatCurrency(trade.commission)}</td>
                        <td className="p-2 text-right font-medium">
                          {formatCurrency(trade.total_cost || trade.total_proceeds || 0)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BacktestResults;
