import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Award,
  Target,
  BarChart3
} from 'lucide-react';

interface AlgorithmPerformance {
  algorithm_id: string;
  algorithm_name?: string;
  return_metrics: {
    total_return_pct: number;
    cagr_pct: number;
    avg_daily_return_pct: number;
  };
  risk_metrics: {
    sharpe_ratio: number;
    sortino_ratio: number;
    volatility_pct: number;
    max_drawdown_pct?: number;
  };
  trade_metrics: {
    total_trades: number;
    win_rate_pct: number;
    profit_factor: number;
  };
  drawdown_metrics?: {
    max_drawdown_pct: number;
    calmar_ratio: number;
  };
  equity_curve?: Array<{
    date: string;
    equity: number;
    cumulative_return: number;
  }>;
}

interface StrategyComparisonProps {
  algorithmIds?: string[];
  onClose?: () => void;
}

export const StrategyComparison: React.FC<StrategyComparisonProps> = ({
  algorithmIds = [],
  onClose
}) => {
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<string[]>(algorithmIds);
  const [availableAlgorithms, setAvailableAlgorithms] = useState<Array<{ id: string; name: string }>>([]);
  const [performanceData, setPerformanceData] = useState<AlgorithmPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAvailableAlgorithms();
  }, []);

  useEffect(() => {
    if (selectedAlgorithms.length > 0) {
      fetchPerformanceData();
    }
  }, [selectedAlgorithms]);

  const fetchAvailableAlgorithms = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/algorithms/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch algorithms');

      const data = await response.json();
      if (data.success && data.data) {
        setAvailableAlgorithms(data.data.map((algo: any) => ({
          id: algo.id,
          name: algo.name
        })));
      }
    } catch (err) {
      console.error('Error fetching algorithms:', err);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const promises = selectedAlgorithms.map(async (algoId) => {
        const response = await fetch(`http://localhost:8000/api/v1/algorithms/${algoId}/performance`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) throw new Error(`Failed to fetch performance for ${algoId}`);

        const data = await response.json();
        return {
          algorithm_id: algoId,
          algorithm_name: availableAlgorithms.find(a => a.id === algoId)?.name || algoId,
          ...data.data
        };
      });

      const results = await Promise.all(promises);
      setPerformanceData(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAlgorithm = (algorithmId: string) => {
    if (!selectedAlgorithms.includes(algorithmId) && selectedAlgorithms.length < 4) {
      setSelectedAlgorithms([...selectedAlgorithms, algorithmId]);
    }
  };

  const handleRemoveAlgorithm = (algorithmId: string) => {
    setSelectedAlgorithms(selectedAlgorithms.filter(id => id !== algorithmId));
  };

  const formatPercent = (value: number, decimals: number = 2) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
  };

  const formatNumber = (value: number, decimals: number = 2) => {
    return value.toFixed(decimals);
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1: return 'text-yellow-600 bg-yellow-50';
      case 2: return 'text-gray-600 bg-gray-50';
      case 3: return 'text-orange-600 bg-orange-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  const getRankBadge = (rank: number) => {
    const medals = ['🥇', '🥈', '🥉', ''];
    return medals[rank - 1] || '';
  };

  // Prepare comparison data
  const comparisonMetrics = [
    {
      name: 'Total Return',
      key: 'total_return_pct',
      type: 'return',
      format: formatPercent,
      higherIsBetter: true
    },
    {
      name: 'CAGR',
      key: 'cagr_pct',
      type: 'return',
      format: formatPercent,
      higherIsBetter: true
    },
    {
      name: 'Sharpe Ratio',
      key: 'sharpe_ratio',
      type: 'risk',
      format: formatNumber,
      higherIsBetter: true
    },
    {
      name: 'Sortino Ratio',
      key: 'sortino_ratio',
      type: 'risk',
      format: formatNumber,
      higherIsBetter: true
    },
    {
      name: 'Max Drawdown',
      key: 'max_drawdown_pct',
      type: 'drawdown',
      format: formatPercent,
      higherIsBetter: false
    },
    {
      name: 'Volatility',
      key: 'volatility_pct',
      type: 'risk',
      format: formatPercent,
      higherIsBetter: false
    },
    {
      name: 'Win Rate',
      key: 'win_rate_pct',
      type: 'trade',
      format: formatPercent,
      higherIsBetter: true
    },
    {
      name: 'Profit Factor',
      key: 'profit_factor',
      type: 'trade',
      format: formatNumber,
      higherIsBetter: true
    }
  ];

  const getMetricValue = (algo: AlgorithmPerformance, metric: any) => {
    const { key, type } = metric;
    switch (type) {
      case 'return':
        return algo.return_metrics?.[key as keyof typeof algo.return_metrics];
      case 'risk':
        return algo.risk_metrics?.[key as keyof typeof algo.risk_metrics];
      case 'trade':
        return algo.trade_metrics?.[key as keyof typeof algo.trade_metrics];
      case 'drawdown':
        return algo.drawdown_metrics?.[key as keyof typeof algo.drawdown_metrics];
      default:
        return 0;
    }
  };

  const rankAlgorithms = (metric: any) => {
    const values = performanceData.map(algo => ({
      id: algo.algorithm_id,
      value: getMetricValue(algo, metric) || 0
    }));

    values.sort((a, b) =>
      metric.higherIsBetter ? b.value - a.value : a.value - b.value
    );

    const ranks: { [key: string]: number } = {};
    values.forEach((item, index) => {
      ranks[item.id] = index + 1;
    });

    return ranks;
  };

  // Prepare radar chart data
  const radarData = comparisonMetrics.slice(0, 6).map(metric => {
    const data: any = { metric: metric.name };
    performanceData.forEach(algo => {
      const value = getMetricValue(algo, metric);
      // Normalize to 0-100 scale for radar chart
      data[algo.algorithm_name || algo.algorithm_id] = Math.abs(value || 0);
    });
    return data;
  });

  // Prepare equity curve comparison
  const equityCurveData = (() => {
    if (performanceData.length === 0) return [];

    const allDates = new Set<string>();
    performanceData.forEach(algo => {
      algo.equity_curve?.forEach(point => allDates.add(point.date));
    });

    return Array.from(allDates).sort().map(date => {
      const point: any = { date };
      performanceData.forEach(algo => {
        const curvePoint = algo.equity_curve?.find(p => p.date === date);
        point[algo.algorithm_name || algo.algorithm_id] = curvePoint?.cumulative_return || 0;
      });
      return point;
    });
  })();

  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c'];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <BarChart3 className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading comparison data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Strategy Comparison</h2>
          <p className="text-sm text-gray-500">
            Compare up to 4 algorithms side-by-side
          </p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>Close</Button>
        )}
      </div>

      {/* Algorithm Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Algorithms to Compare</CardTitle>
          <CardDescription>
            Choose up to 4 algorithms ({selectedAlgorithms.length}/4 selected)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedAlgorithms.map((algoId) => (
              <Badge key={algoId} variant="secondary" className="px-3 py-1">
                {availableAlgorithms.find(a => a.id === algoId)?.name || algoId}
                <button
                  onClick={() => handleRemoveAlgorithm(algoId)}
                  className="ml-2 text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>

          {selectedAlgorithms.length < 4 && (
            <Select onValueChange={handleAddAlgorithm}>
              <SelectTrigger>
                <SelectValue placeholder="Add algorithm..." />
              </SelectTrigger>
              <SelectContent>
                {availableAlgorithms
                  .filter(algo => !selectedAlgorithms.includes(algo.id))
                  .map(algo => (
                    <SelectItem key={algo.id} value={algo.id}>
                      {algo.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          )}
        </CardContent>
      </Card>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg">
          {error}
        </div>
      )}

      {performanceData.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            Select algorithms to begin comparison
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Metric</th>
                      {performanceData.map((algo, idx) => (
                        <th key={algo.algorithm_id} className="text-right p-2">
                          <div className="flex items-center justify-end gap-2">
                            <span>{algo.algorithm_name}</span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonMetrics.map((metric) => {
                      const ranks = rankAlgorithms(metric);
                      return (
                        <tr key={metric.key} className="border-b hover:bg-gray-50">
                          <td className="p-2 font-medium">{metric.name}</td>
                          {performanceData.map((algo) => {
                            const value = getMetricValue(algo, metric);
                            const rank = ranks[algo.algorithm_id];
                            return (
                              <td key={algo.algorithm_id} className="p-2 text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <span className={rank === 1 ? 'font-bold' : ''}>
                                    {metric.format(value || 0)}
                                  </span>
                                  {rank <= 3 && (
                                    <span className="text-xs">{getRankBadge(rank)}</span>
                                  )}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Equity Curve Comparison */}
          {equityCurveData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Cumulative Returns Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={equityCurveData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                    />
                    <Tooltip
                      formatter={(value: number) => `${value.toFixed(2)}%`}
                      labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    />
                    <Legend />
                    {performanceData.map((algo, idx) => (
                      <Line
                        key={algo.algorithm_id}
                        type="monotone"
                        dataKey={algo.algorithm_name || algo.algorithm_id}
                        stroke={colors[idx % colors.length]}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Radar</CardTitle>
              <CardDescription>
                Multi-dimensional performance comparison
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis />
                  {performanceData.map((algo, idx) => (
                    <Radar
                      key={algo.algorithm_id}
                      name={algo.algorithm_name || algo.algorithm_id}
                      dataKey={algo.algorithm_name || algo.algorithm_id}
                      stroke={colors[idx % colors.length]}
                      fill={colors[idx % colors.length]}
                      fillOpacity={0.3}
                    />
                  ))}
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Rankings Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['Total Return', 'Sharpe Ratio', 'Max Drawdown'].map((metricName) => {
              const metric = comparisonMetrics.find(m => m.name === metricName);
              if (!metric) return null;

              const ranks = rankAlgorithms(metric);
              const sortedAlgos = [...performanceData].sort((a, b) =>
                ranks[a.algorithm_id] - ranks[b.algorithm_id]
              );

              return (
                <Card key={metricName}>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Award className="w-4 h-4" />
                      Best {metricName}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {sortedAlgos.slice(0, 3).map((algo) => {
                        const rank = ranks[algo.algorithm_id];
                        const value = getMetricValue(algo, metric);
                        return (
                          <div key={algo.algorithm_id} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{getRankBadge(rank)}</span>
                              <span className="text-sm">{algo.algorithm_name}</span>
                            </div>
                            <span className="text-sm font-medium">
                              {metric.format(value || 0)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default StrategyComparison;
