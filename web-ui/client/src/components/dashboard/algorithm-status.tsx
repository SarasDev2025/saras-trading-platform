import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "@/components/ui/skeleton";
import { Bot, TrendingUp, TrendingDown, Activity, PlayCircle, StopCircle } from "lucide-react";
import { api } from "@/lib/api";

// API Response types
interface ApiAlgorithmDashboard {
  active_algorithms: number;
  total_algorithms: number;
  total_executions: number;
  successful_executions: number;
  today_pnl: number;
  today_trades: number;
  avg_win_rate: number;
}

interface ApiAlgorithm {
  id: string;
  name: string;
  description: string;
  status: string;
  auto_run: boolean;
  execution_interval: string;
  last_run_at: string | null;
  total_executions: number;
  successful_executions: number;
  total_pnl: number;
  unrealized_pnl: number;
  realized_pnl: number;
  positions_count: number;
  market_value: number;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  message?: string;
}

export function AlgorithmStatus() {
  const { data: dashboardData, isLoading: isDashboardLoading, isError: isDashboardError, error: dashboardError } = useQuery<ApiAlgorithmDashboard, Error>({
    queryKey: ["algorithm-dashboard"],
    queryFn: async (): Promise<ApiAlgorithmDashboard> => {
      console.log('[AlgorithmStatus] Fetching algorithm dashboard');

      try {
        const res = await api.get<ApiResponse<ApiAlgorithmDashboard>>('/api/v1/algorithms/dashboard');
        console.log('[AlgorithmStatus] Dashboard API Response Status:', res.status);

        const apiResponse = res.data;
        console.log('[AlgorithmStatus] Dashboard API Response Data:', JSON.stringify(apiResponse, null, 2));

        if (!apiResponse || !apiResponse.success) {
          const errorMsg = apiResponse?.error || 'Algorithm dashboard API did not return valid data';
          console.error('[AlgorithmStatus] API Error:', errorMsg);
          throw new Error(errorMsg);
        }

        return apiResponse.data;
      } catch (error) {
        console.error('[AlgorithmStatus] Error fetching dashboard:', error);
        throw error;
      }
    },
  });

  const { data: algorithms = [], isLoading: isAlgorithmsLoading } = useQuery<ApiAlgorithm[], Error>({
    queryKey: ["algorithms-list"],
    queryFn: async (): Promise<ApiAlgorithm[]> => {
      console.log('[AlgorithmStatus] Fetching algorithms list');

      try {
        const res = await api.get<ApiResponse<ApiAlgorithm[]>>('/api/v1/algorithms');
        console.log('[AlgorithmStatus] Algorithms API Response Status:', res.status);

        const apiResponse = res.data;

        if (!apiResponse || !apiResponse.success || !Array.isArray(apiResponse.data)) {
          const errorMsg = 'Algorithms API did not return valid data';
          console.error('[AlgorithmStatus] API Error:', errorMsg);
          throw new Error(errorMsg);
        }

        console.log(`[AlgorithmStatus] Received ${apiResponse.data.length} algorithms`);
        // Filter to show only active algorithms
        return apiResponse.data.filter(algo => algo.status === 'active').slice(0, 5);
      } catch (error) {
        console.error('[AlgorithmStatus] Error fetching algorithms:', error);
        throw error;
      }
    },
  });

  const formatCurrency = (value: number) =>
    value.toLocaleString("en-US", { style: "currency", currency: "USD" });

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isLoading = isDashboardLoading || isAlgorithmsLoading;

  return (
    <Card className="chart-container">
      <CardHeader className="border-b border-[var(--carbon-gray-80)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Bot className="w-5 h-5 carbon-blue" />
            <CardTitle className="text-white">Algorithm Performance</CardTitle>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {isDashboardError && (
          <p className="text-red-400 mb-3">Failed to load algorithm data: {(dashboardError as Error)?.message}</p>
        )}

        {/* Summary Cards */}
        {isDashboardLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="stat-card">
                <CardContent className="p-4">
                  <Skeleton className="h-4 w-20 mb-2" />
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : dashboardData ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Active Algorithms</span>
                  <Activity className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {dashboardData.active_algorithms}
                  <span className="text-sm text-gray-400 ml-2">/ {dashboardData.total_algorithms}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Today's P&L</span>
                  {dashboardData.today_pnl >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-[var(--success-green)]" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-[var(--danger-red)]" />
                  )}
                </div>
                <div className={`text-2xl font-bold ${dashboardData.today_pnl >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                  {dashboardData.today_pnl >= 0 ? '+' : ''}{formatCurrency(dashboardData.today_pnl)}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {dashboardData.today_trades} trades today
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Total Executions</span>
                  <PlayCircle className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {dashboardData.total_executions.toLocaleString()}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {dashboardData.successful_executions} successful
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Avg Win Rate</span>
                  <TrendingUp className="w-4 h-4 text-[var(--success-green)]" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {dashboardData.avg_win_rate.toFixed(1)}%
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}

        {/* Active Algorithms List */}
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-400 mb-4">Active Algorithms</h4>

          {isAlgorithmsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Card key={i} className="stat-card">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <Skeleton className="h-5 w-48 mb-2" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-6 w-16" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : algorithms.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="w-12 h-12 carbon-blue mx-auto mb-4" />
              <p className="text-gray-400 mb-2">No Active Algorithms</p>
              <p className="text-sm text-gray-500">Create and activate algorithms to see them here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {algorithms.map((algorithm) => (
                <Card key={algorithm.id} className="stat-card hover:border-[var(--carbon-blue)] transition-colors cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h5 className="text-white font-medium">{algorithm.name}</h5>
                          {algorithm.auto_run && (
                            <Badge
                              variant="secondary"
                              className="bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)] text-xs"
                            >
                              Auto
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 mb-2">{algorithm.description}</p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                          <span>Interval: {algorithm.execution_interval}</span>
                          <span>•</span>
                          <span>Last Run: {formatDate(algorithm.last_run_at)}</span>
                          <span>•</span>
                          <span>
                            Executions: {algorithm.successful_executions}/{algorithm.total_executions}
                            {algorithm.total_executions > 0 && (
                              <span className="ml-1 text-[var(--success-green)]">
                                ({((algorithm.successful_executions / algorithm.total_executions) * 100).toFixed(0)}%)
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-xs">
                          <span className={`font-medium ${algorithm.total_pnl >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                            {algorithm.total_pnl >= 0 ? '+' : ''}{formatCurrency(algorithm.total_pnl)} P&L
                          </span>
                          <span>•</span>
                          <span className="text-gray-400">{algorithm.positions_count} positions</span>
                          <span>•</span>
                          <span className="text-gray-400">{formatCurrency(algorithm.market_value)} value</span>
                        </div>
                      </div>
                      <Badge
                        variant="secondary"
                        className={`
                          ${algorithm.status === 'active' ? 'bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]' : ''}
                          ${algorithm.status === 'inactive' ? 'bg-gray-500 bg-opacity-20 text-gray-400' : ''}
                          ${algorithm.status === 'error' ? 'bg-[var(--danger-red)] bg-opacity-20 text-[var(--danger-red)]' : ''}
                        `}
                      >
                        {algorithm.status === 'active' ? <PlayCircle className="w-3 h-3 mr-1 inline" /> : <StopCircle className="w-3 h-3 mr-1 inline" />}
                        {algorithm.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
