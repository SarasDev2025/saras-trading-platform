import { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { Position } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, List, Target, BarChart3 } from "lucide-react";
import { api } from "@/lib/api";

interface Portfolio {
  id: string;
  name: string;
  total_value: number;
  cash_balance: number;
}

export default function Portfolio() {
  const [activeTab, setActiveTab] = useState("all");

  // Fetch user's portfolios
  const { data: portfolios, isLoading: isLoadingPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
    queryFn: async () => {
      const response = await api.get("/portfolios");
      if (!response.data?.success || !Array.isArray(response.data.data)) {
        throw new Error(response.data?.message || "Failed to fetch portfolios");
      }
      return response.data.data;
    },
  });

  // Use the first portfolio (or could use default portfolio)
  const currentPortfolio = portfolios?.[0];
  const portfolioId = currentPortfolio?.id;

  const { data: positions, isLoading } = useQuery<Position[]>({
    queryKey: ["/api/portfolios", portfolioId, "positions"],
    enabled: !!portfolioId,
    queryFn: async () => {
      const response = await api.get(`/portfolios/${portfolioId}/positions`);
      if (!response.data?.success || !Array.isArray(response.data.data)) {
        throw new Error(response.data?.message || "Failed to fetch positions");
      }
      return response.data.data;
    },
  });

  // Fetch grouped positions from the new API endpoint
  const { data: groupedData, isLoading: isLoadingGrouped } = useQuery<{
    smallcases: Position[];
    algorithms: Position[];
    manual: Position[];
  }>({
    queryKey: ["/api/portfolios", portfolioId, "positions", "grouped"],
    enabled: !!portfolioId,
    queryFn: async () => {
      const response = await api.get(`/portfolios/${portfolioId}/positions/grouped`);
      if (!response.data?.success || !response.data.data) {
        throw new Error(response.data?.message || "Failed to fetch grouped positions");
      }
      return response.data.data;
    },
  });

  const formatCurrency = (value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return numValue.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  // Use grouped positions from API
  const groupedPositions = groupedData || {
    smallcases: [],
    algorithms: [],
    manual: [],
  };

  // Calculate metrics
  const totalValue = positions?.reduce((sum, p) => sum + parseFloat(p.marketValue), 0) || 0;
  const totalPnL = positions?.reduce((sum, p) => sum + parseFloat(p.unrealizedPnL), 0) || 0;
  const totalCost = totalValue - totalPnL;
  const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

  const renderPositionsTable = (positions: Position[], title?: string) => (
    <div className="overflow-x-auto">
      {title && <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>}
      <table className="w-full">
        <thead>
          <tr className="text-left border-b border-[var(--carbon-gray-80)]">
            <th className="pb-3 text-sm font-medium text-gray-400">Symbol</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Quantity</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Avg Price</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Current Price</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Market Value</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Unrealized P&L</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Asset Type</th>
            <th className="pb-3 text-sm font-medium text-gray-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-[var(--carbon-gray-80)]">
                <td className="py-4"><Skeleton className="h-4 w-16" /></td>
                <td className="py-4"><Skeleton className="h-4 w-12" /></td>
                <td className="py-4"><Skeleton className="h-4 w-16" /></td>
                <td className="py-4"><Skeleton className="h-4 w-16" /></td>
                <td className="py-4"><Skeleton className="h-4 w-20" /></td>
                <td className="py-4"><Skeleton className="h-4 w-20" /></td>
                <td className="py-4"><Skeleton className="h-6 w-16" /></td>
                <td className="py-4"><Skeleton className="h-8 w-20" /></td>
              </tr>
            ))
          ) : positions && positions.length === 0 ? (
            <tr>
              <td colSpan={8} className="py-8 text-center text-gray-400">
                No positions found
              </td>
            </tr>
          ) : (
            positions?.map((position) => {
              const unrealizedPnL = parseFloat(position.unrealizedPnL);
              const isProfit = unrealizedPnL >= 0;

              return (
                <tr key={position.id} className="border-b border-[var(--carbon-gray-80)]">
                  <td className="py-4 text-sm font-medium text-white">
                    {position.symbol}
                  </td>
                  <td className="py-4 text-sm text-white">
                    {parseFloat(position.quantity).toLocaleString()}
                  </td>
                  <td className="py-4 text-sm text-white">
                    {formatCurrency(position.avgPrice)}
                  </td>
                  <td className="py-4 text-sm text-white">
                    {formatCurrency(position.currentPrice)}
                  </td>
                  <td className="py-4 text-sm text-white">
                    {formatCurrency(position.marketValue)}
                  </td>
                  <td className="py-4">
                    <div className={`flex items-center space-x-1 ${isProfit ? 'success-text' : 'danger-text'}`}>
                      {isProfit ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      <span className="text-sm font-medium">
                        {formatCurrency(Math.abs(unrealizedPnL))}
                      </span>
                    </div>
                  </td>
                  <td className="py-4">
                    <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                      {position.assetType.charAt(0).toUpperCase() + position.assetType.slice(1)}
                    </Badge>
                  </td>
                  <td className="py-4">
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)] text-xs">
                        Trade
                      </Button>
                      <Button size="sm" variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)] text-xs">
                        Close
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="min-h-screen flex">
      <Sidebar />

      <main className="flex-1 overflow-hidden">
        <Header
          title="Portfolio"
          subtitle="View and manage your portfolio positions"
        />

        <div className="p-6 h-full overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Portfolio Overview</h2>
            <div className="space-x-2">
              <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                Export
              </Button>
              <Button className="btn-primary">
                Add Position
              </Button>
            </div>
          </div>

          {/* Portfolio Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-400">Total Value</h3>
                  <BarChart3 className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {formatCurrency(totalValue)}
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-400">Total P&L</h3>
                  {totalPnL >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-[var(--success-green)]" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-[var(--danger-red)]" />
                  )}
                </div>
                <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                  {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  {totalPnL >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-400">Total Positions</h3>
                  <List className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {positions?.length || 0}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabbed Content */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full max-w-2xl grid-cols-3 mb-6">
              <TabsTrigger value="all" className="flex items-center space-x-2">
                <List className="w-4 h-4" />
                <span>All Positions</span>
              </TabsTrigger>
              <TabsTrigger value="grouped" className="flex items-center space-x-2">
                <Target className="w-4 h-4" />
                <span>By Strategy</span>
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4" />
                <span>Performance</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">All Positions</CardTitle>
                </CardHeader>
                <CardContent>
                  {renderPositionsTable(positions || [])}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="grouped">
              <div className="space-y-6">
                {/* Smallcases Group */}
                <Card className="chart-container">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white flex items-center space-x-2">
                        <Target className="w-5 h-5 carbon-blue" />
                        <span>From Smallcases</span>
                      </CardTitle>
                      <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                        {groupedPositions.smallcases.length} positions
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {groupedPositions.smallcases.length > 0 ? (
                      renderPositionsTable(groupedPositions.smallcases)
                    ) : (
                      <p className="text-center text-gray-400 py-8">No positions from smallcases</p>
                    )}
                  </CardContent>
                </Card>

                {/* Algorithms Group */}
                <Card className="chart-container">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white flex items-center space-x-2">
                        <Target className="w-5 h-5 carbon-blue" />
                        <span>From Algorithms</span>
                      </CardTitle>
                      <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                        {groupedPositions.algorithms.length} positions
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {groupedPositions.algorithms.length > 0 ? (
                      renderPositionsTable(groupedPositions.algorithms)
                    ) : (
                      <p className="text-center text-gray-400 py-8">No positions from algorithms</p>
                    )}
                  </CardContent>
                </Card>

                {/* Manual Trades Group */}
                <Card className="chart-container">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white flex items-center space-x-2">
                        <Target className="w-5 h-5 carbon-blue" />
                        <span>Manual Trades</span>
                      </CardTitle>
                      <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                        {groupedPositions.manual.length} positions
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {groupedPositions.manual.length > 0 ? (
                      renderPositionsTable(groupedPositions.manual)
                    ) : (
                      <p className="text-center text-gray-400 py-8">No manual positions</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="performance">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Performance by Source */}
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Performance by Source</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                        <div>
                          <p className="text-sm text-gray-400">Smallcases</p>
                          <p className="text-lg font-medium text-white">{groupedPositions.smallcases.length} positions</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-[var(--success-green)]">
                            {formatCurrency(groupedPositions.smallcases.reduce((sum, p) => sum + parseFloat(p.unrealizedPnL), 0))}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                        <div>
                          <p className="text-sm text-gray-400">Algorithms</p>
                          <p className="text-lg font-medium text-white">{groupedPositions.algorithms.length} positions</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-[var(--success-green)]">
                            {formatCurrency(groupedPositions.algorithms.reduce((sum, p) => sum + parseFloat(p.unrealizedPnL), 0))}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                        <div>
                          <p className="text-sm text-gray-400">Manual Trades</p>
                          <p className="text-lg font-medium text-white">{groupedPositions.manual.length} positions</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-[var(--success-green)]">
                            {formatCurrency(groupedPositions.manual.reduce((sum, p) => sum + parseFloat(p.unrealizedPnL), 0))}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Top Performers */}
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Top Performers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {positions
                        ?.sort((a, b) => parseFloat(b.unrealizedPnL) - parseFloat(a.unrealizedPnL))
                        .slice(0, 5)
                        .map((position) => {
                          const pnl = parseFloat(position.unrealizedPnL);
                          const isProfit = pnl >= 0;
                          return (
                            <div key={position.id} className="flex items-center justify-between p-3 border border-[var(--carbon-gray-80)] rounded-lg">
                              <div>
                                <p className="font-medium text-white">{position.symbol}</p>
                                <p className="text-sm text-gray-400">{formatCurrency(position.marketValue)}</p>
                              </div>
                              <div className={`text-right ${isProfit ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                                <p className="font-bold">{isProfit ? '+' : ''}{formatCurrency(pnl)}</p>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </CardContent>
                </Card>

                {/* Asset Allocation */}
                <Card className="chart-container lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-white">Asset Allocation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 flex items-center justify-center bg-[var(--carbon-gray-90)] rounded-lg">
                      <p className="text-gray-400">Asset allocation chart will be displayed here</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
