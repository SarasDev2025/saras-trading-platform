import { TrendingUp, Wallet, List, DollarSign, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { Portfolio } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect } from "react";
import { AddFundsModal } from "./add-funds-modal";
import { useToast } from "@/hooks/use-toast";

export function PortfolioOverview() {
  const [isAddFundsOpen, setIsAddFundsOpen] = useState(false);
  const { toast } = useToast();

  const { data: portfolios, isLoading } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  // Fetch cash balance separately for paper trading
  const { data: cashBalanceData, isLoading: isCashLoading } = useQuery({
    queryKey: ["/api/portfolios/cash-balance"],
  });

  // Check for pending orders on mount and after funds are added
  useEffect(() => {
    const checkPendingOrders = () => {
      const stored = localStorage.getItem("pendingOrder");
      if (stored) {
        try {
          const pending = JSON.parse(stored);
          const orderType = pending.type === "quick_trade" ? "trade order" : "rebalancing";

          toast({
            title: "Pending Order Found",
            description: `You have a pending ${orderType}. Complete your transaction to restore it.`,
            duration: 8000,
          });
        } catch (error) {
          console.error("Failed to parse pending order:", error);
        }
      }
    };

    checkPendingOrders();
  }, []);

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

  const totalValue = portfolio.total_value || 0;
  const dayPnL = 0; // TODO: Calculate from positions
  const dayPnLPercent = 0; // TODO: Calculate from positions

  // Use cash balance from dedicated endpoint if available, otherwise fallback to portfolio data
  const cashAvailable = cashBalanceData?.data?.cash_balance || portfolio.cash_balance || 0;
  const buyingPower = cashBalanceData?.data?.buying_power || cashAvailable;
  const portfolioId = cashBalanceData?.data?.portfolio_id || portfolio.id;
  const cashPercent = totalValue > 0 ? ((cashAvailable / totalValue) * 100).toFixed(2) : "0";

  return (
    <>
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
          <div className="flex items-center justify-between mt-2">
            <span className="text-gray-400 text-sm">{cashPercent}% allocation</span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs text-green-500 hover:text-green-400 hover:bg-green-500/10"
              onClick={() => setIsAddFundsOpen(true)}
            >
              <Plus className="h-3 w-3 mr-1" />
              Add Funds
            </Button>
          </div>
        </CardContent>
      </Card>
      </div>

      <AddFundsModal
        isOpen={isAddFundsOpen}
        onClose={() => {
          setIsAddFundsOpen(false);
          // Check for pending orders after modal closes (funds might have been added)
          const stored = localStorage.getItem("pendingOrder");
          if (stored) {
            toast({
              title: "Resume Your Order",
              description: "Your pending order is waiting. Click on Trading or Smallcases to continue.",
              duration: 10000,
            });
          }
        }}
        portfolioId={portfolioId}
        currentBalance={cashAvailable}
      />
    </>
  );
}
