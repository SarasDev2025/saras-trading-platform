import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { DollarSign, Plus } from "lucide-react";

interface AddFundsModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;
  currentBalance: number;
}

export function AddFundsModal({ isOpen, onClose, portfolioId, currentBalance }: AddFundsModalProps) {
  const [amount, setAmount] = useState<string>("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const addFundsMutation = useMutation({
    mutationFn: async (amount: number) => {
      const response = await api.post("/portfolios/add-funds", {
        portfolio_id: portfolioId,
        amount: amount,
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: "Funds Added Successfully",
        description: `Added $${parseFloat(amount).toLocaleString()} to your portfolio`,
      });
      queryClient.invalidateQueries({ queryKey: ["/api/portfolios/cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["/api/portfolios"] });
      setAmount("");
      onClose();
    },
    onError: (error: any) => {
      toast({
        title: "Failed to Add Funds",
        description: error.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amountNum = parseFloat(amount);

    if (isNaN(amountNum) || amountNum <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid amount greater than 0",
        variant: "destructive",
      });
      return;
    }

    if (amountNum < 100) {
      toast({
        title: "Amount Too Low",
        description: "Minimum deposit is $100",
        variant: "destructive",
      });
      return;
    }

    if (amountNum > 1000000) {
      toast({
        title: "Amount Too High",
        description: "Maximum deposit is $1,000,000",
        variant: "destructive",
      });
      return;
    }

    addFundsMutation.mutate(amountNum);
  };

  const presetAmounts = [1000, 5000, 10000, 25000, 50000];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-500" />
            Add Virtual Funds
          </DialogTitle>
          <DialogDescription>
            Add virtual money to your paper trading account. Current balance: ${currentBalance.toLocaleString()}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (USD)</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="amount"
                  type="number"
                  placeholder="Enter amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="pl-9"
                  min="100"
                  max="1000000"
                  step="100"
                />
              </div>
              <p className="text-xs text-gray-400">Min: $100 | Max: $1,000,000</p>
            </div>

            <div className="space-y-2">
              <Label>Quick Amounts</Label>
              <div className="grid grid-cols-3 gap-2">
                {presetAmounts.map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setAmount(preset.toString())}
                    className="text-xs"
                  >
                    ${(preset / 1000).toFixed(0)}k
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              className="btn-success"
              disabled={addFundsMutation.isPending}
            >
              {addFundsMutation.isPending ? (
                "Adding..."
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Funds
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
