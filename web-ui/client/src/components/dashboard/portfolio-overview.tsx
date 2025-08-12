import { TrendingUp, Wallet, List, DollarSign } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { Portfolio } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioOverview() {
  const { data: portfolios, isLoading } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="stat-card">
            <CardContent className="p-6">
              <Skeleton className="h-4 w-32 mb-4" />
              <Skeleton className="h-8 w-24 mb-2" />
              <Skeleton className="h-4 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const portfolio = portfolios?.[0];
  if (!portfolio) return null;

  const totalValue = parseFloat(portfolio.totalValue);
  const dayPnL = parseFloat(portfolio.dayPnL);
  const dayPnLPercent = parseFloat(portfolio.dayPnLPercent);
  const cashAvailable = parseFloat(portfolio.cashAvailable);
  const cashPercent = ((cashAvailable / totalValue) * 100).toFixed(2);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card className="stat-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">Total Portfolio Value</h3>
            <Wallet className="w-4 h-4 carbon-blue" />
          </div>
          <div className="text-2xl font-bold text-white">
            ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center mt-2">
            <TrendingUp className="w-3 h-3 success-text mr-1" />
            <span className="success-text text-sm">
              +{dayPnLPercent}% (+${Math.abs(dayPnL).toLocaleString()})
            </span>
          </div>
        </CardContent>
      </Card>

      <Card className="stat-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">Day P&L</h3>
            <TrendingUp className="w-4 h-4 success-text" />
          </div>
          <div className="text-2xl font-bold success-text">
            +${Math.abs(dayPnL).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center mt-2">
            <TrendingUp className="w-3 h-3 success-text mr-1" />
            <span className="success-text text-sm">+{dayPnLPercent}%</span>
          </div>
        </CardContent>
      </Card>

      <Card className="stat-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">Active Positions</h3>
            <List className="w-4 h-4 carbon-blue" />
          </div>
          <div className="text-2xl font-bold text-white">247</div>
          <div className="flex items-center mt-2">
            <span className="text-gray-400 text-sm">Across 8 strategies</span>
          </div>
        </CardContent>
      </Card>

      <Card className="stat-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-400">Cash Available</h3>
            <DollarSign className="w-4 h-4 warning-text" />
          </div>
          <div className="text-2xl font-bold text-white">
            ${cashAvailable.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center mt-2">
            <span className="text-gray-400 text-sm">{cashPercent}% allocation</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
