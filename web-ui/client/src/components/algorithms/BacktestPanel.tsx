import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart as LineChartIcon, TrendingUp, TrendingDown, Activity, DollarSign, Target, BarChart3, Loader2, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { PriceChartWithSignals } from './PriceChartWithSignals';

interface BacktestPanelProps {
  algorithmId: string;
}

export function BacktestPanel({ algorithmId }: BacktestPanelProps) {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 1);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [initialCapital, setInitialCapital] = useState(100000);

  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunBacktest = async () => {
    setRunning(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/algorithms/${algorithmId}/backtest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setResults(data.data);
      } else {
        setError(data.message || 'Backtest failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to run backtest');
    } finally {
      setRunning(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const renderEquityCurve = () => {
    if (!results?.equity_curve) return null;

    const equityCurve = results.equity_curve;

    return (
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={equityCurve}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value: any) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="rgb(75, 192, 192)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Backtest Configuration
          </CardTitle>
          <CardDescription>Run historical simulation of your algorithm</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="initial-capital">Initial Capital ($)</Label>
              <Input
                id="initial-capital"
                type="number"
                min={1000}
                step={1000}
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseInt(e.target.value))}
              />
            </div>
          </div>

          <Button
            className="mt-4 w-full"
            onClick={handleRunBacktest}
            disabled={running}
          >
            {running ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Backtest...
              </>
            ) : (
              <>
                <Activity className="mr-2 h-4 w-4" />
                Run Backtest
              </>
            )}
          </Button>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Backtest Results</CardTitle>
            <CardDescription>
              Simulation from {startDate} to {endDate}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="returns">Returns</TabsTrigger>
                <TabsTrigger value="risk">Risk</TabsTrigger>
                <TabsTrigger value="trades">Trades</TabsTrigger>
                <TabsTrigger value="signals">Price & Signals</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                {renderEquityCurve()}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Final Value</p>
                    <p className="text-2xl font-bold">
                      {formatCurrency(results.final_portfolio_value)}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Total Return</p>
                    <p className={`text-2xl font-bold ${results.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(results.total_return_pct)}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Total Trades</p>
                    <p className="text-2xl font-bold">{results.total_trades}</p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-2xl font-bold">{formatPercent(results.win_rate)}</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="returns" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Total Return</span>
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-2xl font-bold">{formatCurrency(results.total_return)}</p>
                    <Badge variant={results.total_return >= 0 ? 'default' : 'destructive'}>
                      {formatPercent(results.total_return_pct)}
                    </Badge>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Annualized Return</span>
                      <Target className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-2xl font-bold">
                      {formatPercent(results.annualized_return)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Best Trade</span>
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    </div>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(results.best_trade)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Worst Trade</span>
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    </div>
                    <p className="text-2xl font-bold text-red-600">
                      {formatCurrency(results.worst_trade)}
                    </p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="risk" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Max Drawdown</span>
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    </div>
                    <p className="text-2xl font-bold text-red-600">
                      {formatPercent(results.max_drawdown_pct)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {formatCurrency(results.max_drawdown)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Volatility</span>
                      <Activity className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-2xl font-bold">
                      {formatPercent(results.volatility)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                      <Target className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-2xl font-bold">{results.sharpe_ratio.toFixed(2)}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Sortino Ratio</span>
                      <Target className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-2xl font-bold">{results.sortino_ratio.toFixed(2)}</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="trades" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Total Trades</p>
                    <p className="text-2xl font-bold">{results.total_trades}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Winning Trades</p>
                    <p className="text-2xl font-bold text-green-600">{results.winning_trades}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Losing Trades</p>
                    <p className="text-2xl font-bold text-red-600">{results.losing_trades}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-2xl font-bold">{formatPercent(results.win_rate)}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Avg Win</p>
                    <p className="text-lg font-bold text-green-600">
                      {formatCurrency(results.avg_win)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Avg Loss</p>
                    <p className="text-lg font-bold text-red-600">
                      {formatCurrency(results.avg_loss)}
                    </p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Profit Factor</p>
                    <p className="text-lg font-bold">{results.profit_factor.toFixed(2)}</p>
                  </div>

                  <div className="space-y-2 p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Win Streak</p>
                    <p className="text-lg font-bold">{results.longest_winning_streak}</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="signals" className="space-y-4">
                {results.price_data && results.trades ? (
                  <div className="space-y-6">
                    {Object.entries(results.price_data).map(([symbol, priceData]: [string, any]) => (
                      <PriceChartWithSignals
                        key={symbol}
                        symbol={symbol}
                        priceData={priceData}
                        trades={results.trades}
                      />
                    ))}
                  </div>
                ) : (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      No price or trade data available for visualization.
                    </AlertDescription>
                  </Alert>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
