import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, DollarSign } from "lucide-react";
import { useLocation } from "wouter";

interface InsufficientFundsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  required: number;
  available: number;
  shortfall: number;
  onAddFunds?: () => void;
}

export function InsufficientFundsDialog({
  isOpen,
  onClose,
  required,
  available,
  shortfall,
  onAddFunds,
}: InsufficientFundsDialogProps) {
  const [, setLocation] = useLocation();

  const handleAddFunds = () => {
    if (onAddFunds) {
      onAddFunds();
    } else {
      setLocation("/");
    }
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-orange-600">
            <AlertTriangle className="h-5 w-5" />
            Insufficient Funds
          </DialogTitle>
          <DialogDescription>
            You don't have enough cash to complete this transaction.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <Alert variant="destructive" className="border-orange-200 bg-orange-50">
            <AlertTriangle className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800">
              <strong>Action Required:</strong> Add funds to your portfolio to proceed with this transaction.
            </AlertDescription>
          </Alert>

          <div className="space-y-3 rounded-lg bg-gray-50 p-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Required Amount:</span>
              <span className="font-semibold text-gray-900">
                ${required.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Available Balance:</span>
              <span className="font-semibold text-gray-900">
                ${available.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>

            <div className="border-t border-gray-200 pt-3 flex justify-between items-center">
              <span className="text-sm font-medium text-orange-600">Shortfall:</span>
              <span className="font-bold text-orange-600 text-lg">
                ${shortfall.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          <div className="text-xs text-gray-500 flex items-start gap-2">
            <DollarSign className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p>
              Your order details will be saved. After adding funds, you can return to complete this transaction.
            </p>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleAddFunds}
            className="w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white"
          >
            <DollarSign className="h-4 w-4 mr-2" />
            Add Funds
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
