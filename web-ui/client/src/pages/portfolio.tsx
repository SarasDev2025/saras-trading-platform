import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { Position } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown } from "lucide-react";

export default function Portfolio() {
  const { data: positions, isLoading } = useQuery<Position[]>({
    queryKey: ["/api/portfolios", "portfolio-id", "positions"],
  });

  const formatCurrency = (value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return numValue.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

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
            <h2 className="text-xl font-semibold text-white">Your Positions</h2>
            <div className="space-x-2">
              <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                Export
              </Button>
              <Button className="btn-primary">
                Add Position
              </Button>
            </div>
          </div>

          <Card className="chart-container">
            <CardHeader>
              <CardTitle className="text-white">Active Positions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
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
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
