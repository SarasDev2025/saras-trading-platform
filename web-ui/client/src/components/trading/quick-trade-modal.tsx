import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

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
      handleClose();
    },
    onError: () => {
      toast({
        title: "Trade Failed",
        description: "Failed to place trade order. Please try again.",
        variant: "destructive",
      });
    },
  });

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
  );
}
