import { useEffect, useState } from 'react';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlgorithmBuilder } from '@/components/algorithms/AlgorithmBuilder';
import { BacktestPanel } from '@/components/algorithms/BacktestPanel';
import { AlgorithmCard } from '@/components/algorithms/AlgorithmCard';
import { algorithmAPI } from '@/lib/api';
import { Code, TrendingUp, Activity, DollarSign, Target, Loader2, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function Algorithms() {
  const [algorithms, setAlgorithms] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showBuilder, setShowBuilder] = useState(false);
  const [showBacktest, setShowBacktest] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<any>(null);

  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [algoResponse, dashResponse] = await Promise.all([
        algorithmAPI.getAlgorithms(),
        algorithmAPI.getDashboard(),
      ]);

      if (algoResponse.success) {
        setAlgorithms(algoResponse.data);
      }

      if (dashResponse.success) {
        setDashboard(dashResponse.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load algorithms');
      toast({
        title: 'Error',
        description: 'Failed to load algorithms',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setSelectedAlgorithm(null);
    setShowBuilder(true);
  };

  const handleEdit = async (id: string) => {
    try {
      const response = await algorithmAPI.getAlgorithm(id);
      if (response.success) {
        setSelectedAlgorithm(response.data);
        setShowBuilder(true);
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to load algorithm',
        variant: 'destructive',
      });
    }
  };

  const handleSave = async (algorithm: any) => {
    try {
      if (algorithm.id) {
        // Update existing
        await algorithmAPI.updateAlgorithm(algorithm.id, algorithm);
        toast({
          title: 'Success',
          description: 'Algorithm updated successfully',
        });
      } else {
        // Create new
        await algorithmAPI.createAlgorithm(algorithm);
        toast({
          title: 'Success',
          description: 'Algorithm created successfully',
        });
      }

      setShowBuilder(false);
      loadData();
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.message || 'Failed to save algorithm',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this algorithm?')) return;

    try {
      await algorithmAPI.deleteAlgorithm(id);
      toast({
        title: 'Success',
        description: 'Algorithm deleted successfully',
      });
      loadData();
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to delete algorithm',
        variant: 'destructive',
      });
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await algorithmAPI.toggleAlgorithm(id);
      toast({
        title: 'Success',
        description: 'Algorithm status updated',
      });
      loadData();
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to toggle algorithm',
        variant: 'destructive',
      });
    }
  };

  const handleExecute = async (id: string) => {
    try {
      const response = await algorithmAPI.executeAlgorithm(id, false);

      if (response.success) {
        toast({
          title: 'Success',
          description: `Generated ${response.data.signals_generated} signals`,
        });
        loadData();
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.message || 'Execution failed',
        variant: 'destructive',
      });
    }
  };

  const handleBacktest = (id: string) => {
    setSelectedAlgorithm({ id });
    setShowBacktest(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Header title="Algorithms" subtitle="Manage and monitor your trading algorithms" />
          <div className="p-6 h-full flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <Sidebar />

      <main className="flex-1 overflow-hidden">
        <Header title="Algorithms" subtitle="Manage and monitor your trading algorithms" />

        <div className="p-6 h-full overflow-y-auto">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Your Algorithms</h2>
            <Button onClick={handleCreateNew} className="btn-primary">
              <Code className="w-4 h-4 mr-2" />
              New Algorithm
            </Button>
          </div>

          {/* Dashboard Stats */}
          {dashboard && (
            <Card className="chart-container mb-6">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Algorithm Performance Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Activity className="w-5 h-5 text-[var(--success-green)]" />
                    </div>
                    <div className="text-2xl font-bold success-text">
                      {dashboard.active_algorithms || 0}
                    </div>
                    <div className="text-sm text-gray-400">Active Algorithms</div>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Target className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {dashboard.today_trades || 0}
                    </div>
                    <div className="text-sm text-gray-400">Today's Trades</div>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <DollarSign className="w-5 h-5 text-[var(--success-green)]" />
                    </div>
                    <div
                      className={`text-2xl font-bold ${
                        (dashboard.today_pnl || 0) >= 0 ? 'success-text' : 'danger-text'
                      }`}
                    >
                      ${(dashboard.today_pnl || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-400">Today's P&L</div>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <TrendingUp className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {dashboard.avg_win_rate?.toFixed(1) || 0}%
                    </div>
                    <div className="text-sm text-gray-400">Avg Win Rate</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Algorithms Grid */}
          {algorithms.length === 0 ? (
            <Card className="chart-container">
              <CardContent className="py-12 text-center">
                <Code className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-400 mb-4">No algorithms yet</p>
                <Button onClick={handleCreateNew} className="btn-primary">
                  Create Your First Algorithm
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {algorithms.map((algorithm) => (
                <AlgorithmCard
                  key={algorithm.id}
                  algorithm={algorithm}
                  onExecute={handleExecute}
                  onToggle={handleToggle}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onBacktest={handleBacktest}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Algorithm Builder Dialog */}
      <Dialog open={showBuilder} onOpenChange={setShowBuilder}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedAlgorithm ? 'Edit Algorithm' : 'Create Algorithm'}
            </DialogTitle>
          </DialogHeader>
          <AlgorithmBuilder
            algorithm={selectedAlgorithm}
            onSave={handleSave}
            onCancel={() => setShowBuilder(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Backtest Dialog */}
      <Dialog open={showBacktest} onOpenChange={setShowBacktest}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Backtest Algorithm</DialogTitle>
          </DialogHeader>
          {selectedAlgorithm && <BacktestPanel algorithmId={selectedAlgorithm.id} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
