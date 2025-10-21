import { useEffect, useState } from 'react';
import { useLocation, useRoute } from 'wouter';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { EquityCurveChart } from '@/components/algorithms/EquityCurveChart';
import { algorithmAPI } from '@/lib/api';
import { Loader2, ArrowLeft, TrendingUp, Activity, DollarSign, Play, Pause } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function AlgorithmDetail() {
  const [, navigate] = useLocation();
  const [match, params] = useRoute('/algorithms/:id');
  const id = params?.id;
  const { toast } = useToast();

  const [algorithm, setAlgorithm] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [pnl, setPnl] = useState<any>(null);
  const [equityCurve, setEquityCurve] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!match) {
      setLoading(false);
      return;
    }
    if (id) {
      loadAlgorithmData();
    }
  }, [id, match]);

  const loadAlgorithmData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [algoRes, posRes, tradesRes, pnlRes, equityRes] = await Promise.all([
        algorithmAPI.getAlgorithm(id),
        algorithmAPI.getPositions(id),
        algorithmAPI.getTradeHistory(id),
        algorithmAPI.getPnL(id),
        algorithmAPI.getEquityCurve(id),
      ]);

      if (algoRes.success) setAlgorithm(algoRes.data);
      if (posRes.success) setPositions(posRes.data.positions || []);
      if (tradesRes.success) setTrades(tradesRes.data.trades || []);
      if (pnlRes.success) setPnl(pnlRes.data);
      if (equityRes.success) setEquityCurve(equityRes.data.equity_curve || []);
    } catch (err: any) {
      toast({
        title: 'Error',
        description: 'Failed to load algorithm details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async () => {
    try {
      if (!id) return;
      await algorithmAPI.toggleAlgorithm(id);
      toast({
        title: 'Success',
        description: 'Algorithm status updated',
      });
      loadAlgorithmData();
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to toggle algorithm',
        variant: 'destructive',
      });
    }
  };

  const handleExecute = async () => {
    try {
      if (!id) return;
      const response = await algorithmAPI.executeAlgorithm(id, false);
      if (response.success) {
        toast({
          title: 'Success',
          description: `Generated ${response.data.signals_count || 0} signals`,
        });
        loadAlgorithmData();
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Execution failed',
        variant: 'destructive',
      });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Header title="Algorithm Details" subtitle="Loading..." />
          <div className="p-6 h-full flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </main>
      </div>
    );
  }

  if (!algorithm) {
    return (
      <div className="min-h-screen flex">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Header title="Algorithm Details" subtitle="Not found" />
          <div className="p-6">
            <Button onClick={() => navigate('/algorithms')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Algorithms
            </Button>
          </div>
        </main>
      </div>
    );
  }

  const totalPnL = pnl?.total_pnl || 0;
  const unrealizedPnL = pnl?.unrealized_pnl || 0;
  const realizedPnL = pnl?.realized_pnl || 0;
  const marketValue = pnl?.total_market_value || 0;
  const positionsCount = positions.length;

  return (
    <div className="min-h-screen flex">
      <Sidebar />

      <main className="flex-1 overflow-hidden">
        <Header
          title={algorithm.name}
          subtitle={algorithm.description || 'No description'}
        />

        <div className="p-6 h-full overflow-y-auto">
          {/* Header Actions */}
          <div className="flex items-center justify-between mb-6">
            <Button onClick={() => navigate('/algorithms')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            <div className="flex items-center gap-4">
              <Badge variant={algorithm.status === 'active' ? 'default' : 'secondary'}>
                {algorithm.status}
              </Badge>
              <Button onClick={handleToggle} variant="outline">
                {algorithm.status === 'active' ? (
                  <>
                    <Pause className="w-4 h-4 mr-2" />
                    Deactivate
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Activate
                  </>
                )}
              </Button>
              <Button onClick={handleExecute} disabled={algorithm.status !== 'active'}>
                <Play className="w-4 h-4 mr-2" />
                Execute Now
              </Button>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Total P&L</span>
                  {totalPnL >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-[var(--success-green)]" />
                  ) : (
                    <TrendingUp className="w-4 h-4 text-[var(--danger-red)] rotate-180" />
                  )}
                </div>
                <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                  {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Unrealized: {formatCurrency(unrealizedPnL)}
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Market Value</span>
                  <DollarSign className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {formatCurrency(marketValue)}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {positionsCount} positions
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Executions</span>
                  <Activity className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {algorithm.total_executions || 0}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {algorithm.successful_executions || 0} successful
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Last Run</span>
                  <Activity className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-sm font-bold text-white">
                  {formatDate(algorithm.last_run_at)}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Interval: {algorithm.execution_interval}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="performance" className="space-y-4">
            <TabsList className="bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-80)]">
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="positions">Positions ({positionsCount})</TabsTrigger>
              <TabsTrigger value="trades">Trade History ({trades.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="performance" className="space-y-4">
              <EquityCurveChart
                data={equityCurve}
                trades={trades}
                title={`${algorithm.name} Performance`}
              />
            </TabsContent>

            <TabsContent value="positions" className="space-y-4">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">Current Positions</CardTitle>
                </CardHeader>
                <CardContent>
                  {positions.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      No positions yet
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-[var(--carbon-gray-80)]">
                            <th className="text-left p-3 text-gray-400 font-medium">Symbol</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Quantity</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Avg Cost</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Current</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Value</th>
                            <th className="text-right p-3 text-gray-400 font-medium">P&L</th>
                          </tr>
                        </thead>
                        <tbody>
                          {positions.map((pos) => (
                            <tr key={pos.symbol} className="border-b border-[var(--carbon-gray-80)] hover:bg-[var(--carbon-gray-90)]">
                              <td className="p-3">
                                <div className="text-white font-medium">{pos.symbol}</div>
                                <div className="text-xs text-gray-400">{pos.asset_name}</div>
                              </td>
                              <td className="p-3 text-right text-white">{pos.quantity.toFixed(2)}</td>
                              <td className="p-3 text-right text-white">{formatCurrency(pos.avg_cost)}</td>
                              <td className="p-3 text-right text-white">{formatCurrency(pos.current_price)}</td>
                              <td className="p-3 text-right text-white font-medium">{formatCurrency(pos.market_value)}</td>
                              <td className={`p-3 text-right font-medium ${pos.unrealized_pnl >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                                {pos.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(pos.unrealized_pnl)}
                                <div className="text-xs">
                                  ({pos.unrealized_pnl_pct >= 0 ? '+' : ''}{pos.unrealized_pnl_pct.toFixed(2)}%)
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="trades" className="space-y-4">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">Trade History</CardTitle>
                </CardHeader>
                <CardContent>
                  {trades.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      No trades yet
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-[var(--carbon-gray-80)]">
                            <th className="text-left p-3 text-gray-400 font-medium">Date</th>
                            <th className="text-left p-3 text-gray-400 font-medium">Symbol</th>
                            <th className="text-left p-3 text-gray-400 font-medium">Action</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Quantity</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Price</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Total</th>
                            <th className="text-right p-3 text-gray-400 font-medium">Fees</th>
                          </tr>
                        </thead>
                        <tbody>
                          {trades.map((trade) => (
                            <tr key={trade.id} className="border-b border-[var(--carbon-gray-80)] hover:bg-[var(--carbon-gray-90)]">
                              <td className="p-3 text-white text-sm">{formatDate(trade.executed_at)}</td>
                              <td className="p-3 text-white font-medium">{trade.symbol}</td>
                              <td className="p-3">
                                <Badge variant={trade.action === 'buy' ? 'default' : 'secondary'} className={trade.action === 'buy' ? 'bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]' : 'bg-[var(--danger-red)] bg-opacity-20 text-[var(--danger-red)]'}>
                                  {trade.action.toUpperCase()}
                                </Badge>
                              </td>
                              <td className="p-3 text-right text-white">{trade.quantity.toFixed(2)}</td>
                              <td className="p-3 text-right text-white">{formatCurrency(trade.price)}</td>
                              <td className="p-3 text-right text-white font-medium">{formatCurrency(trade.total_amount)}</td>
                              <td className="p-3 text-right text-gray-400">{formatCurrency(trade.fees)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
