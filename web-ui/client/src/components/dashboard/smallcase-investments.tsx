import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "@/components/ui/skeleton";
import { Package, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";

// API Response types
interface ApiSmallcaseInvestment {
  id: string;
  investmentAmount: number;
  currentValue: number;
  unrealizedPnL: number;
  status: string;
  smallcase: {
    id: string;
    name: string;
    category: string;
    theme: string;
    riskLevel: string;
  };
  portfolio: {
    id: string;
    name: string;
  };
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  message?: string;
}

export function SmallcaseInvestments() {
  const { data: investments = [], isLoading, isError, error } = useQuery<ApiSmallcaseInvestment[], Error>({
    queryKey: ["smallcase-investments"],
    queryFn: async (): Promise<ApiSmallcaseInvestment[]> => {
      console.log('[SmallcaseInvestments] Fetching user investments');

      try {
        const res = await api.get<ApiResponse<ApiSmallcaseInvestment[]>>('/smallcases/user/investments');
        console.log('[SmallcaseInvestments] API Response Status:', res.status);

        const apiResponse = res.data;
        console.log('[SmallcaseInvestments] API Response Data:', JSON.stringify(apiResponse, null, 2));

        if (!apiResponse) {
          const errorMsg = 'Empty response from server';
          console.error('[SmallcaseInvestments] Error:', errorMsg);
          throw new Error(errorMsg);
        }

        if (!apiResponse.success) {
          const errorMsg = apiResponse.error || 'Smallcase investments API did not return valid data';
          console.error('[SmallcaseInvestments] API Error:', errorMsg);
          throw new Error(errorMsg);
        }

        if (!Array.isArray(apiResponse.data)) {
          const errorMsg = `Smallcase investments API did not return an array. Received: ${typeof apiResponse.data}`;
          console.error('[SmallcaseInvestments] Error:', errorMsg, 'Data:', apiResponse.data);
          throw new Error(errorMsg);
        }

        console.log(`[SmallcaseInvestments] Received ${apiResponse.data.length} investments`);
        return apiResponse.data;
      } catch (error) {
        console.error('[SmallcaseInvestments] Error fetching investments:', error);
        throw error;
      }
    },
  });

  const formatCurrency = (value: number) =>
    value.toLocaleString("en-US", { style: "currency", currency: "USD" });

  const formatPercentage = (pnl: number, investment: number) => {
    if (investment === 0) return "0.00";
    return ((pnl / investment) * 100).toFixed(2);
  };

  const getTotalInvestment = () => {
    return investments.reduce((sum, inv) => sum + inv.investmentAmount, 0);
  };

  const getTotalCurrentValue = () => {
    return investments.reduce((sum, inv) => sum + inv.currentValue, 0);
  };

  const getTotalPnL = () => {
    return investments.reduce((sum, inv) => sum + inv.unrealizedPnL, 0);
  };

  return (
    <Card className="chart-container">
      <CardHeader className="border-b border-[var(--carbon-gray-80)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Package className="w-5 h-5 carbon-blue" />
            <CardTitle className="text-white">Smallcase Investments</CardTitle>
          </div>
          {!isLoading && investments.length > 0 && (
            <div className="flex items-center space-x-6 text-sm">
              <div>
                <span className="text-gray-400">Total Invested: </span>
                <span className="text-white font-medium">{formatCurrency(getTotalInvestment())}</span>
              </div>
              <div>
                <span className="text-gray-400">Current Value: </span>
                <span className="text-white font-medium">{formatCurrency(getTotalCurrentValue())}</span>
              </div>
              <div>
                <span className="text-gray-400">Total P&L: </span>
                <span className={`font-medium ${getTotalPnL() >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                  {getTotalPnL() >= 0 ? '+' : ''}{formatCurrency(getTotalPnL())}
                  ({getTotalPnL() >= 0 ? '+' : ''}{formatPercentage(getTotalPnL(), getTotalInvestment())}%)
                </span>
              </div>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {isError && (
          <p className="text-red-400 mb-3">Failed to load smallcase investments: {(error as Error)?.message}</p>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="stat-card">
                <CardContent className="p-4">
                  <Skeleton className="h-6 w-32 mb-2" />
                  <Skeleton className="h-4 w-24 mb-4" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : investments.length === 0 ? (
          <div className="text-center py-12">
            <Package className="w-12 h-12 carbon-blue mx-auto mb-4" />
            <p className="text-gray-400 mb-2">No Smallcase Investments Yet</p>
            <p className="text-sm text-gray-500">Start investing in smallcases to see them here</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {investments.map((investment) => (
              <Card key={investment.id} className="stat-card hover:border-[var(--carbon-blue)] transition-colors cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-white font-medium mb-1">{investment.smallcase.name}</h4>
                      <p className="text-xs text-gray-400">{investment.smallcase.theme}</p>
                    </div>
                    <Badge
                      variant="secondary"
                      className={`
                        ${investment.smallcase.riskLevel === 'low' ? 'bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]' : ''}
                        ${investment.smallcase.riskLevel === 'medium' ? 'bg-[var(--warning-yellow)] bg-opacity-20 text-[var(--warning-yellow)]' : ''}
                        ${investment.smallcase.riskLevel === 'high' ? 'bg-[var(--danger-red)] bg-opacity-20 text-[var(--danger-red)]' : ''}
                      `}
                    >
                      {investment.smallcase.riskLevel}
                    </Badge>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Invested:</span>
                      <span className="text-white">{formatCurrency(investment.investmentAmount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Current:</span>
                      <span className="text-white font-medium">{formatCurrency(investment.currentValue)}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-[var(--carbon-gray-80)]">
                      <span className="text-gray-400">P&L:</span>
                      <div className="flex items-center space-x-1">
                        {investment.unrealizedPnL >= 0 ? (
                          <TrendingUp className="w-3 h-3 text-[var(--success-green)]" />
                        ) : (
                          <TrendingDown className="w-3 h-3 text-[var(--danger-red)]" />
                        )}
                        <span className={`font-medium ${investment.unrealizedPnL >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                          {investment.unrealizedPnL >= 0 ? '+' : ''}{formatCurrency(investment.unrealizedPnL)}
                        </span>
                        <span className={`text-xs ${investment.unrealizedPnL >= 0 ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
                          ({investment.unrealizedPnL >= 0 ? '+' : ''}{formatPercentage(investment.unrealizedPnL, investment.investmentAmount)}%)
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-[var(--carbon-gray-80)] flex items-center justify-between">
                    <span className="text-xs text-gray-400">{investment.portfolio.name}</span>
                    <Badge
                      variant="secondary"
                      className={`text-xs
                        ${investment.status === 'active' ? 'bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]' : ''}
                        ${investment.status === 'closed' ? 'bg-gray-500 bg-opacity-20 text-gray-400' : ''}
                      `}
                    >
                      {investment.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
