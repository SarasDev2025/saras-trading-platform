import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { useBuyingPowerCheck } from "@/hooks/useBuyingPowerCheck";
import { InsufficientFundsDialog } from "./insufficient-funds-dialog";

interface QuickTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function QuickTradeModal({ isOpen, onClose }: QuickTradeModalProps) {
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState("MARKET");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const {
    checkBuyingPower,
    buyingPower,
    showInsufficientDialog,
    insufficientDetails,
    closeInsufficientDialog,
    savePendingOrder,
    getPendingOrder,
    clearPendingOrder,
  } = useBuyingPowerCheck();

  const createTradeMutation = useMutation({
    mutationFn: async (tradeData: any) => {
      const response = await apiRequest(
        "POST",
        "/api/portfolios/portfolio-id/trades",
        tradeData
      );
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Trade Submitted",
        description: "Your trade order has been placed successfully.",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/portfolios"] });
      clearPendingOrder(); // Clear any saved pending order
      handleClose();
    },
    onError: (error: any) => {
      // Check if error is due to insufficient buying power
      const errorMessage = error?.message || "";
      if (errorMessage.includes("Insufficient buying power")) {
        toast({
          title: "Insufficient Funds",
          description: errorMessage,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Trade Failed",
          description: "Failed to place trade order. Please try again.",
          variant: "destructive",
        });
      }
    },
  });

  // Restore pending order on mount
  useEffect(() => {
    if (isOpen) {
      const pending = getPendingOrder();
      if (pending && pending.type === "quick_trade") {
        const { symbol, side, orderType, quantity, price } = pending.data;
        setSymbol(symbol);
        setSide(side);
        setOrderType(orderType);
        setQuantity(quantity);
        setPrice(price);

        toast({
          title: "Order Restored",
          description: "Your pending order has been restored. Review and submit when ready.",
        });
      }
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!symbol || !quantity) {
      toast({
        title: "Invalid Input",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    const tradeData = {
      symbol: symbol.toUpperCase(),
      side,
      orderType,
      quantity,
      price: orderType === "MARKET" ? "0" : price,
    };

    // For BUY orders, check buying power first
    if (side === "BUY") {
      const qty = parseFloat(quantity);
      const unitPrice = orderType === "MARKET" ? 100 : parseFloat(price); // Estimate $100 for market orders
      const estimatedTotal = qty * unitPrice;
      const feeEstimate = estimatedTotal * 0.001; // 0.1% fee
      const requiredAmount = estimatedTotal + feeEstimate;

      // Check buying power
      if (!checkBuyingPower(requiredAmount)) {
        // Save pending order before showing insufficient funds dialog
        savePendingOrder("quick_trade", tradeData, requiredAmount);
        return;
      }
    }

    createTradeMutation.mutate(tradeData);
  };

  const handleClose = () => {
    setSymbol("");
    setSide("BUY");
    setOrderType("MARKET");
    setQuantity("");
    setPrice("");
    onClose();
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-80)] text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-semibold">Quick Trade</DialogTitle>
          </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-sm font-medium text-gray-400">Symbol</Label>
            <Input
              type="text"
              placeholder="e.g., AAPL"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white focus:border-[var(--carbon-blue)]"
            />
          </div>

          <div>
            <Label className="text-sm font-medium text-gray-400">Order Type</Label>
            <Select value={orderType} onValueChange={setOrderType}>
              <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white focus:border-[var(--carbon-blue)]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                <SelectItem value="MARKET" className="text-white">Market</SelectItem>
                <SelectItem value="LIMIT" className="text-white">Limit</SelectItem>
                <SelectItem value="STOP" className="text-white">Stop</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium text-gray-400">Side</Label>
              <Select value={side} onValueChange={(value: "BUY" | "SELL") => setSide(value)}>
                <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white focus:border-[var(--carbon-blue)]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                  <SelectItem value="BUY" className="text-white">Buy</SelectItem>
                  <SelectItem value="SELL" className="text-white">Sell</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-400">Quantity</Label>
              <Input
                type="number"
                placeholder="100"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white focus:border-[var(--carbon-blue)]"
              />
            </div>
          </div>

          {orderType !== "MARKET" && (
            <div>
              <Label className="text-sm font-medium text-gray-400">Price</Label>
              <Input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white focus:border-[var(--carbon-blue)]"
              />
            </div>
          )}

          <div className="flex space-x-3 pt-4">
            <Button 
              type="button" 
              onClick={handleClose} 
              variant="outline"
              className="flex-1 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]"
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              className="flex-1 btn-primary"
              disabled={createTradeMutation.isPending}
            >
              {createTradeMutation.isPending ? "Placing..." : "Place Order"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>

    {insufficientDetails && (
      <InsufficientFundsDialog
        isOpen={showInsufficientDialog}
        onClose={closeInsufficientDialog}
        required={insufficientDetails.required}
        available={insufficientDetails.available}
        shortfall={insufficientDetails.shortfall}
      />
    )}
    </>
  );
}
