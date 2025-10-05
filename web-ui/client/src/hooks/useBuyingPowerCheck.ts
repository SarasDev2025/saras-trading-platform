import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";

interface BuyingPowerData {
  portfolio_id: string;
  cash_balance: number;
  buying_power: number;
  total_value: number;
}

interface PendingOrder {
  type: "quick_trade" | "smallcase_rebalance";
  data: any;
  requiredAmount: number;
  timestamp: number;
}

export function useBuyingPowerCheck() {
  const { toast } = useToast();
  const [showInsufficientDialog, setShowInsufficientDialog] = useState(false);
  const [insufficientDetails, setInsufficientDetails] = useState<{
    required: number;
    available: number;
    shortfall: number;
  } | null>(null);

  // Fetch current cash balance
  // Note: queryClient.ts already unwraps the response, so we get BuyingPowerData directly
  const { data: buyingPowerData, refetch: refetchBuyingPower, error, isError, isLoading } = useQuery<BuyingPowerData>({
    queryKey: ["/api/portfolios/cash-balance"],
    staleTime: 0, // Always fetch fresh data for buying power checks
  });

  // Log query state for debugging
  if (isError) {
    console.error('[BuyingPowerCheck] Query error:', error);
  }
  if (isLoading) {
    console.log('[BuyingPowerCheck] Loading cash balance...');
  }
  if (buyingPowerData) {
    console.log('[BuyingPowerCheck] Cash balance data:', buyingPowerData);
  }

  /**
   * Check if user has sufficient buying power for a transaction
   */
  const checkBuyingPower = (requiredAmount: number): boolean => {
    if (!buyingPowerData) {
      toast({
        title: "Unable to Verify Funds",
        description: "Could not fetch your current balance. Please try again.",
        variant: "destructive",
      });
      return false;
    }

    const available = buyingPowerData.buying_power;

    if (available < requiredAmount) {
      const shortfall = requiredAmount - available;
      setInsufficientDetails({
        required: requiredAmount,
        available,
        shortfall,
      });
      setShowInsufficientDialog(true);
      return false;
    }

    return true;
  };

  /**
   * Save pending order to localStorage for restoration after adding funds
   */
  const savePendingOrder = (orderType: "quick_trade" | "smallcase_rebalance", orderData: any, requiredAmount: number) => {
    const pendingOrder: PendingOrder = {
      type: orderType,
      data: orderData,
      requiredAmount,
      timestamp: Date.now(),
    };
    localStorage.setItem("pendingOrder", JSON.stringify(pendingOrder));
  };

  /**
   * Get pending order from localStorage
   */
  const getPendingOrder = (): PendingOrder | null => {
    const stored = localStorage.getItem("pendingOrder");
    if (!stored) return null;

    try {
      const pending: PendingOrder = JSON.parse(stored);

      // Expire pending orders after 1 hour
      const oneHour = 60 * 60 * 1000;
      if (Date.now() - pending.timestamp > oneHour) {
        localStorage.removeItem("pendingOrder");
        return null;
      }

      return pending;
    } catch (error) {
      console.error("Failed to parse pending order:", error);
      localStorage.removeItem("pendingOrder");
      return null;
    }
  };

  /**
   * Clear pending order from localStorage
   */
  const clearPendingOrder = () => {
    localStorage.removeItem("pendingOrder");
  };

  /**
   * Handle closing the insufficient funds dialog
   */
  const closeInsufficientDialog = () => {
    setShowInsufficientDialog(false);
    setInsufficientDetails(null);
  };

  return {
    // Data
    buyingPowerData: buyingPowerData || null,
    cashBalance: buyingPowerData?.cash_balance || 0,
    buyingPower: buyingPowerData?.buying_power || 0,

    // Dialog state
    showInsufficientDialog,
    insufficientDetails,
    closeInsufficientDialog,

    // Functions
    checkBuyingPower,
    refetchBuyingPower,
    savePendingOrder,
    getPendingOrder,
    clearPendingOrder,
  };
}
