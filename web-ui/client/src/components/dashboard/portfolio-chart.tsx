import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI } from "@/lib/api";

interface PerformanceData {
  timeframe: string;
  start_date: string;
  end_date: string;
  chart_data: Array<{
    date: string;
    value: number;
    invested: number;
    pnl: number;
  }>;
  metrics: {
    current_value: number;
    total_invested: number;
    period_return: number;
    period_return_percent: number;
    total_return: number;
    total_return_percent: number;
    period_high: number;
    period_low: number;
  };
}

export function PortfolioChart() {
  const [timeframe, setTimeframe] = useState("1D");
  const [portfolioId, setPortfolioId] = useState<string | null>(null);

  // Get default portfolio ID from localStorage or API
  useEffect(() => {
    const fetchPortfolioId = async () => {
      try {
        const result = await portfolioAPI.getPortfolios();
        if (result.success && result.data && result.data.length > 0) {
          setPortfolioId(result.data[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch portfolios:", error);
      }
    };
    fetchPortfolioId();
  }, []);

  // Fetch performance data
  const { data, isLoading, error, refetch } = useQuery<PerformanceData>({
    queryKey: ['portfolio-performance', portfolioId, timeframe],
    queryFn: async () => {
      if (!portfolioId) throw new Error("No portfolio selected");
      const result = await portfolioAPI.getPerformance(portfolioId, timeframe);
      return result.data;
    },
    enabled: !!portfolioId,
    refetchInterval: 60000, // Refetch every 60 seconds
  });

  // Handle timeframe change
  const handleTimeframeChange = (newTimeframe: string) => {
    setTimeframe(newTimeframe);
  };

  // Format chart data for display
  const formatChartData = (chartData: PerformanceData['chart_data']) => {
    if (!chartData || chartData.length === 0) return [];

    return chartData.map((point) => ({
      date: new Date(point.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        ...(timeframe === '1D' ? { hour: 'numeric', minute: '2-digit' } : {})
      }),
      value: point.value,
      invested: point.invested,
      pnl: point.pnl,
    }));
  };

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`;
    }
    return `$${value.toFixed(2)}`;
  };

  // Determine line color based on performance
  const getLineColor = () => {
    if (!data?.metrics) return "var(--carbon-blue)";
    return data.metrics.period_return >= 0 ? "#10b981" : "#ef4444";
  };

  return (
    <Card className="chart-container">
      <CardHeader className="border-b border-[var(--carbon-gray-80)]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">
            Portfolio Performance
          </CardTitle>
          <Select value={timeframe} onValueChange={handleTimeframeChange}>
            <SelectTrigger className="w-24 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
              <SelectItem value="1D" className="text-white hover:bg-[var(--carbon-gray-70)]">1D</SelectItem>
              <SelectItem value="1W" className="text-white hover:bg-[var(--carbon-gray-70)]">1W</SelectItem>
              <SelectItem value="1M" className="text-white hover:bg-[var(--carbon-gray-70)]">1M</SelectItem>
              <SelectItem value="3M" className="text-white hover:bg-[var(--carbon-gray-70)]">3M</SelectItem>
              <SelectItem value="1Y" className="text-white hover:bg-[var(--carbon-gray-70)]">1Y</SelectItem>
              <SelectItem value="YTD" className="text-white hover:bg-[var(--carbon-gray-70)]">YTD</SelectItem>
              <SelectItem value="OPEN" className="text-white hover:bg-[var(--carbon-gray-70)]">OPEN</SelectItem>
              <SelectItem value="ALL" className="text-white hover:bg-[var(--carbon-gray-70)]">ALL</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Performance metrics */}
        {data?.metrics && (
          <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-[var(--carbon-gray-40)] text-xs">Current Value</div>
              <div className="text-white font-semibold">{formatCurrency(data.metrics.current_value)}</div>
            </div>
            <div>
              <div className="text-[var(--carbon-gray-40)] text-xs">Period Return</div>
              <div className={`font-semibold ${data.metrics.period_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {formatCurrency(data.metrics.period_return)} ({data.metrics.period_return_percent.toFixed(2)}%)
              </div>
            </div>
            <div>
              <div className="text-[var(--carbon-gray-40)] text-xs">High</div>
              <div className="text-white font-semibold">{formatCurrency(data.metrics.period_high)}</div>
            </div>
            <div>
              <div className="text-[var(--carbon-gray-40)] text-xs">Low</div>
              <div className="text-white font-semibold">{formatCurrency(data.metrics.period_low)}</div>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-[var(--carbon-gray-40)]">Loading performance data...</div>
          </div>
        ) : error ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-red-500">Failed to load performance data</div>
          </div>
        ) : !data || !data.chart_data || data.chart_data.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-[var(--carbon-gray-40)]">No performance data available</div>
          </div>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formatChartData(data.chart_data)}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#a1a1aa', fontSize: 12 }}
                  axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                  tickLine={{ stroke: 'var(--carbon-gray-70)' }}
                />
                <YAxis
                  tick={{ fill: '#a1a1aa', fontSize: 12 }}
                  axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                  tickLine={{ stroke: 'var(--carbon-gray-70)' }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--carbon-gray-90)',
                    border: '1px solid var(--carbon-gray-70)',
                    borderRadius: '4px',
                  }}
                  labelStyle={{ color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                  formatter={(value: number) => formatCurrency(value)}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={getLineColor()}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: getLineColor() }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
