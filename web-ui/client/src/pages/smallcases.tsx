// src/pages/smallcases.tsx

import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { SmallcaseModificationModal } from "@/components/smallcases/SmallcaseModificationModal";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { TrendingUp, TrendingDown, Eye, Plus, Edit, ArrowUpRight, X } from "lucide-react";
import { useBuyingPowerCheck } from "@/hooks/useBuyingPowerCheck";
import { InsufficientFundsDialog } from "@/components/trading/insufficient-funds-dialog";

type Smallcase = {
  id: string;
  name: string;
  description: string;
  category: string;
  theme: string;
  riskLevel: string;
  expectedReturnMin: number;
  expectedReturnMax: number;
  minimumInvestment: number;
  estimatedNAV: number;
  isActive: boolean;
  region: string;
  currency: string;
};

type SmallcaseDetails = Smallcase & {
  constituents: Array<{
    id: string;
    assetId: string;
    symbol: string;
    assetName: string;
    assetType: string;
    weightPercentage: number;
    currentPrice: number;
    exchange: string;
    value: number;
  }>;
};

// Helper function to get currency symbol
const getCurrencySymbol = (currency: string): string => {
  return currency === 'USD' ? '$' : currency === 'INR' ? '₹' : currency;
};

type UserInvestment = {
  id: string;
  investmentAmount: number;
  unitsPurchased: number;
  purchasePrice: number;
  currentValue: number;
  unrealizedPnL: number;
  status: string;
  investedAt: string;
  canClose: boolean;
  pendingOrders: number;
  orderStatus: 'pending_execution' | 'active';
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
};

export default function SmallcasesPage() {
  const [selectedSmallcase, setSelectedSmallcase] = useState<Smallcase | null>(null);
  const [investmentAmount, setInvestmentAmount] = useState<number>(10000);
  const [isInvesting, setIsInvesting] = useState(false);
  const [isAddingToWatchlist, setIsAddingToWatchlist] = useState(false);
  const [activeTab, setActiveTab] = useState<'available' | 'investments'>('available');

  // Modification Modal State
  const [selectedInvestment, setSelectedInvestment] = useState<UserInvestment | null>(null);
  const [isModificationOpen, setIsModificationOpen] = useState(false);

  // Closure Modal State
  const [selectedInvestmentForClosure, setSelectedInvestmentForClosure] = useState<UserInvestment | null>(null);
  const [isClosureModalOpen, setIsClosureModalOpen] = useState(false);
  const [isClosingPosition, setIsClosingPosition] = useState(false);

  // Market Closed Dialog State
  const [showMarketClosedDialog, setShowMarketClosedDialog] = useState(false);
  const [pendingInvestment, setPendingInvestment] = useState<{
    smallcase: Smallcase;
    amount: number;
  } | null>(null);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Buying power validation
  const {
    checkBuyingPower,
    refetchBuyingPower,
    showInsufficientDialog,
    insufficientDetails,
    closeInsufficientDialog,
  } = useBuyingPowerCheck();

  // Fetch user's existing investments
  const { data: userInvestments = [], isLoading: isLoadingInvestments, refetch: refetchInvestments } = useQuery<UserInvestment[]>({
    queryKey: ['user-smallcase-investments'],
    queryFn: async () => {
      const response = await apiRequest.get('/smallcases/user/investments');
      return response.data.data;
    },
  });

  // Fetch all available smallcases
  const { data: smallcases = [], isLoading: isLoadingSmallcases } = useQuery<Smallcase[]>({
    queryKey: ['smallcases'],
    queryFn: async () => {
      const response = await apiRequest.get('/smallcases');
      return response.data.data;
    },
  });

  // Fetch details of selected smallcase
  const { data: smallcaseDetails, isLoading: isLoadingDetails } = useQuery<SmallcaseDetails>({
    queryKey: ['smallcase', selectedSmallcase?.id],
    queryFn: async () => {
      if (!selectedSmallcase) return null;
      const response = await apiRequest.get(`/smallcases/${selectedSmallcase.id}`);
      return response.data.data;
    },
    enabled: !!selectedSmallcase,
  });

  // Determine initial tab based on user investments
  useEffect(() => {
    if (userInvestments.length > 0 && activeTab === 'available') {
      setActiveTab('investments');
    }
  }, [userInvestments]);

  // Select first smallcase by default when viewing available
  useEffect(() => {
    if (activeTab === 'available' && smallcases.length > 0 && !selectedSmallcase) {
      setSelectedSmallcase(smallcases[0]);
    }
  }, [smallcases, selectedSmallcase, activeTab]);

  // Modification Handlers
  const handleModify = (investment: UserInvestment) => {
    setSelectedInvestment(investment);
    setIsModificationOpen(true);
  };

  const handleApplyRebalancing = (result: any) => {
    console.log('Rebalancing applied:', result);
    toast({
      title: "Rebalancing Applied",
      description: `Your ${selectedInvestment?.smallcase.name} smallcase has been successfully rebalanced.`,
    });
    
    // Refresh investments data
    refetchInvestments();
  };

  const handleInvest = () => {
    if (!selectedSmallcase) return;

    // Check buying power before investment
    if (!checkBuyingPower(investmentAmount)) {
      return; // Insufficient funds dialog will be shown automatically
    }

    // Show market closed warning dialog
    setPendingInvestment({
      smallcase: selectedSmallcase,
      amount: investmentAmount
    });
    setShowMarketClosedDialog(true);
  };

  const proceedWithInvestment = async () => {
    if (!pendingInvestment) return;

    setShowMarketClosedDialog(false);

    try {
      setIsInvesting(true);
      const response = await apiRequest.post(`/smallcases/${pendingInvestment.smallcase.id}/invest`, {
        amount: pendingInvestment.amount,
        portfolio_id: "default-portfolio-id" // You might want to get this dynamically
      });

      // Extract market status from response
      const marketStatus = response.data.data?.marketStatus;
      const isMarketOpen = marketStatus?.isOpen ?? true;
      const marketName = marketStatus?.marketName && marketStatus.marketName.trim().length > 0
        ? marketStatus.marketName
        : "the market";
      const currencySymbol = pendingInvestment.smallcase.currency === 'USD' ? '$' : pendingInvestment.smallcase.currency === 'INR' ? '₹' : pendingInvestment.smallcase.currency;

      toast({
        title: isMarketOpen ? "Investment Successful" : "Investment Queued",
        description: isMarketOpen
          ? `You've successfully invested ${currencySymbol}${pendingInvestment.amount.toLocaleString()} in ${pendingInvestment.smallcase.name}`
          : `Market is closed. Your ${currencySymbol}${pendingInvestment.amount.toLocaleString()} investment in ${pendingInvestment.smallcase.name} will execute when ${marketName} opens.`,
      });

      // Refresh investments data and buying power
      refetchInvestments();
      refetchBuyingPower(); // Force refresh cash balance

      // Invalidate all portfolio-related queries to update dashboard
      queryClient.invalidateQueries({ queryKey: ["/api/portfolios"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["portfolios", "cash-balance"] });

      // Switch to investments tab to show the new investment
      setActiveTab('investments');
    } catch (error: any) {
      console.error('Investment failed:', error);
      const errorMessage = error.response?.data?.detail || "Failed to process investment";

      // Check if error is due to insufficient buying power
      if (typeof errorMessage === 'string' && errorMessage.includes("Insufficient buying power")) {
        toast({
          title: "Insufficient Funds",
          description: errorMessage,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Investment Failed",
          description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
          variant: "destructive",
        });
      }
    } finally {
      setIsInvesting(false);
      setPendingInvestment(null);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!selectedSmallcase) return;
    
    try {
      setIsAddingToWatchlist(true);
      await apiRequest.post('/smallcases/watchlist', {
        smallcaseId: selectedSmallcase.id,
      });
      
      toast({
        title: "Added to Watchlist",
        description: `${selectedSmallcase.name} has been added to your watchlist`,
      });
    } catch (error: any) {
      console.error('Failed to add to watchlist:', error);
      const errorMessage = error.response?.data?.detail || "Failed to add to watchlist";
      toast({
        title: "Failed to Add to Watchlist",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        variant: "destructive",
      });
    } finally {
      setIsAddingToWatchlist(false);
    }
  };

  const handleAddMore = async (investment: UserInvestment) => {
    // Set the smallcase and switch to available tab for additional investment
    const smallcase = smallcases.find(sc => sc.id === investment.smallcase.id);
    if (smallcase) {
      setSelectedSmallcase(smallcase);
      setActiveTab('available');
    }
  };

  const handleClosePosition = (investment: UserInvestment) => {
    setSelectedInvestmentForClosure(investment);
    setIsClosureModalOpen(true);
  };

  const handleConfirmClosure = async () => {
    if (!selectedInvestmentForClosure) return;

    try {
      setIsClosingPosition(true);
      await apiRequest.post(`/smallcases/investments/${selectedInvestmentForClosure.id}/close`, {
        closure_reason: 'user_exit'
      });

      toast({
        title: "Position Closed Successfully",
        description: `Your ${selectedInvestmentForClosure.smallcase.name} position has been closed.`,
      });

      // Refresh investments data and cash balance
      refetchInvestments();
      refetchBuyingPower();

      // Invalidate all portfolio-related queries to update dashboard
      queryClient.invalidateQueries({ queryKey: ["/api/portfolios"] });
      queryClient.invalidateQueries({ queryKey: ["portfolios", "cash-balance"] });

      // Close modal
      setIsClosureModalOpen(false);
      setSelectedInvestmentForClosure(null);
    } catch (error: any) {
      console.error('Position closure failed:', error);
      const errorMessage = error.response?.data?.detail || "Failed to close position";
      toast({
        title: "Closure Failed",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        variant: "destructive",
      });
    } finally {
      setIsClosingPosition(false);
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPnL = (pnl: number) => {
    const isPositive = pnl >= 0;
    return (
      <span className={`flex items-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        {isPositive ? '+' : ''}₹{pnl.toLocaleString()}
      </span>
    );
  };

  const formatPercentage = (current: number, invested: number) => {
    const percentage = ((current - invested) / invested) * 100;
    const isPositive = percentage >= 0;
    return (
      <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
        {isPositive ? '+' : ''}{percentage.toFixed(2)}%
      </span>
    );
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Smallcases" 
          subtitle="Explore and invest in curated smallcase portfolios"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          {/* Navigation Tabs */}
          <div className="mb-6">
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'available' | 'investments')}>
              <TabsList className="grid w-full max-w-md grid-cols-2">
                <TabsTrigger value="available" className="flex items-center gap-2">
                  <Eye className="w-4 h-4" />
                  Available Smallcases
                </TabsTrigger>
                <TabsTrigger value="investments" className="flex items-center gap-2">
                  <ArrowUpRight className="w-4 h-4" />
                  My Investments ({userInvestments.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Content based on active tab */}
          {activeTab === 'investments' ? (
            /* My Investments View */
            <div className="space-y-6">
              {isLoadingInvestments ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-48 w-full rounded-lg" />
                  ))}
                </div>
              ) : userInvestments.length === 0 ? (
                <Card className="p-8">
                  <div className="text-center space-y-4">
                    <h3 className="text-lg font-semibold">No Investments Yet</h3>
                    <p className="text-muted-foreground">
                      You haven't invested in any smallcases yet. Explore available smallcases to get started.
                    </p>
                    <Button onClick={() => setActiveTab('available')} className="mt-4">
                      <Plus className="w-4 h-4 mr-2" />
                      Explore Smallcases
                    </Button>
                  </div>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {userInvestments.map((investment) => (
                    <Card key={investment.id} className="hover:shadow-md transition-shadow">
                      <CardHeader className="pb-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-lg">{investment.smallcase.name}</CardTitle>
                            <CardDescription>{investment.smallcase.theme}</CardDescription>
                          </div>
                          <Badge className={getRiskLevelColor(investment.smallcase.riskLevel)}>
                            {investment.smallcase.riskLevel}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Invested</span>
                            <span className="font-medium">₹{investment.investmentAmount.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Current Value</span>
                            <span className="font-medium">₹{investment.currentValue.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">P&L</span>
                            <div className="text-right">
                              {formatPnL(investment.unrealizedPnL)}
                              <div className="text-xs">
                                {formatPercentage(investment.currentValue, investment.investmentAmount)}
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-1.5 pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs px-1.5 min-w-0"
                            onClick={() => handleModify(investment)}
                          >
                            <Edit className="w-3 h-3 md:mr-1 shrink-0" />
                            <span className="hidden md:inline truncate">Modify</span>
                          </Button>
                          <Button
                            size="sm"
                            className="text-xs px-1.5 min-w-0"
                            onClick={() => handleAddMore(investment)}
                          >
                            <Plus className="w-3 h-3 md:mr-1 shrink-0" />
                            <span className="hidden md:inline truncate">Add</span>
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            className="text-xs px-1.5 min-w-0"
                            onClick={() => handleClosePosition(investment)}
                            disabled={!investment.canClose}
                          >
                            <X className="w-3 h-3 md:mr-1 shrink-0" />
                            <span className="hidden md:inline truncate">
                              {investment.canClose ? 'Close' : 'Executing'}
                            </span>
                          </Button>
                        </div>

                        <div className="text-xs text-muted-foreground pt-1">
                          Invested on {new Date(investment.investedAt).toLocaleDateString()}
                          {investment.pendingOrders > 0 && (
                            <Badge variant="outline" className="ml-2 text-xs">
                              ⏳ {investment.pendingOrders} order{investment.pendingOrders > 1 ? 's' : ''} pending
                            </Badge>
                          )}
                        </div>
                        {!investment.canClose && (
                          <p className="text-xs text-amber-600 mt-1">
                            Orders are being executed. You can close once all orders are filled.
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Available Smallcases View (Original functionality) */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Smallcase List */}
              <div className="lg:col-span-1 space-y-4">
                <h2 className="text-xl font-semibold">Available Smallcases</h2>
                {isLoadingSmallcases ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-24 w-full rounded-lg" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {smallcases.map((smallcase) => (
                      <Card 
                        key={smallcase.id}
                        className={`cursor-pointer transition-colors ${
                          selectedSmallcase?.id === smallcase.id ? 'border-primary' : 'hover:border-primary/50'
                        }`}
                        onClick={() => setSelectedSmallcase(smallcase)}
                      >
                        <CardHeader className="p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <CardTitle className="text-lg">{smallcase.name}</CardTitle>
                              <CardDescription>{smallcase.theme}</CardDescription>
                            </div>
                            <Badge className={getRiskLevelColor(smallcase.riskLevel)}>
                              {smallcase.riskLevel}
                            </Badge>
                          </div>
                          <div className="flex justify-between items-center mt-2">
                            <span className="text-sm text-muted-foreground">Min Investment</span>
                            <span className="font-medium">{getCurrencySymbol(smallcase.currency)}{smallcase.minimumInvestment.toLocaleString()}</span>
                          </div>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Smallcase Details */}
              <div className="lg:col-span-2 space-y-6">
                {selectedSmallcase ? (
                  <>
                    <Card>
                      <CardHeader>
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle>{selectedSmallcase.name}</CardTitle>
                            <CardDescription>{selectedSmallcase.description}</CardDescription>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold">
                              {getCurrencySymbol(selectedSmallcase.currency)}{selectedSmallcase.estimatedNAV.toLocaleString()}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              Min. {getCurrencySymbol(selectedSmallcase.currency)}{selectedSmallcase.minimumInvestment.toLocaleString()}
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      
                      {isLoadingDetails ? (
                        <CardContent>
                          <Skeleton className="h-24 w-full" />
                        </CardContent>
                      ) : smallcaseDetails ? (
                        <CardContent>
                          <Tabs defaultValue="constituents" className="w-full">
                            <TabsList>
                              <TabsTrigger value="constituents">Constituents</TabsTrigger>
                              <TabsTrigger value="performance">Performance</TabsTrigger>
                              <TabsTrigger value="about">About</TabsTrigger>
                            </TabsList>
                            
                            <TabsContent value="constituents" className="mt-4">
                              <div className="space-y-4">
                                {smallcaseDetails.constituents.map((asset) => (
                                  <div key={asset.id} className="flex items-center justify-between p-3 border rounded-lg">
                                    <div>
                                      <div className="font-medium">{asset.assetName}</div>
                                      <div className="text-sm text-muted-foreground">
                                        {asset.symbol} • {asset.exchange}
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <div className="font-medium">{asset.weightPercentage}%</div>
                                      <div className="text-sm">
                                        {getCurrencySymbol(smallcaseDetails.currency)}{asset.currentPrice.toLocaleString()}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </TabsContent>
                            
                            <TabsContent value="performance" className="mt-4">
                              <div className="h-64 flex items-center justify-center bg-muted/50 rounded-lg">
                                <p className="text-muted-foreground">Performance chart will be displayed here</p>
                              </div>
                            </TabsContent>
                            
                            <TabsContent value="about" className="mt-4">
                              <div className="space-y-4">
                                <div>
                                  <h4 className="font-medium">Category</h4>
                                  <p className="text-muted-foreground">{smallcaseDetails.category}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium">Theme</h4>
                                  <p className="text-muted-foreground">{smallcaseDetails.theme}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium">Risk Level</h4>
                                  <p className="text-muted-foreground">{smallcaseDetails.riskLevel}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium">Expected Returns</h4>
                                  <p className="text-muted-foreground">
                                    {smallcaseDetails.expectedReturnMin}% - {smallcaseDetails.expectedReturnMax}% p.a.
                                  </p>
                                </div>
                              </div>
                            </TabsContent>
                          </Tabs>
                        </CardContent>
                      ) : null}
                    </Card>

                    {/* Investment Form */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Invest in {selectedSmallcase.name}</CardTitle>
                        <CardDescription>
                          Enter the amount you want to invest in this smallcase
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <Label htmlFor="amount">Investment Amount (₹)</Label>
                            <Input
                              id="amount"
                              type="number"
                              value={investmentAmount}
                              onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                              min={selectedSmallcase.minimumInvestment}
                              step="1000"
                              className="text-lg font-medium"
                            />
                            <p className="text-sm text-muted-foreground">
                              Minimum investment: {getCurrencySymbol(selectedSmallcase.currency)}{selectedSmallcase.minimumInvestment.toLocaleString()}
                            </p>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 mt-6">
                            <Button 
                              variant="outline" 
                              className="w-full"
                              onClick={handleAddToWatchlist}
                              disabled={isAddingToWatchlist}
                            >
                              {isAddingToWatchlist ? 'Adding...' : 'Add to Watchlist'}
                            </Button>
                            <Button 
                              className="w-full" 
                              onClick={handleInvest}
                              disabled={isInvesting || investmentAmount < selectedSmallcase.minimumInvestment}
                            >
                              {isInvesting ? 'Processing...' : 'Invest Now'}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-64 bg-muted/50 rounded-lg">
                    <p className="text-muted-foreground">Select a smallcase to view details</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Closure Confirmation Modal */}
      <AlertDialog open={isClosureModalOpen} onOpenChange={setIsClosureModalOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Close Position</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to close your position in{' '}
              <span className="font-semibold">{selectedInvestmentForClosure?.smallcase.name}</span>?
            </AlertDialogDescription>
          </AlertDialogHeader>

          {selectedInvestmentForClosure && (
            <div className="space-y-3 py-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current Value:</span>
                <span className="font-medium">₹{selectedInvestmentForClosure.currentValue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Invested Amount:</span>
                <span className="font-medium">₹{selectedInvestmentForClosure.investmentAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">P&L:</span>
                <span className={`font-medium ${selectedInvestmentForClosure.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {selectedInvestmentForClosure.unrealizedPnL >= 0 ? '+' : ''}₹{selectedInvestmentForClosure.unrealizedPnL.toLocaleString()}
                </span>
              </div>
              <div className="border-t pt-3">
                <p className="text-sm text-muted-foreground">
                  This action cannot be undone. Your position will be sold at the current market price.
                </p>
              </div>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel disabled={isClosingPosition}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmClosure}
              disabled={isClosingPosition}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isClosingPosition ? 'Closing...' : 'Close Position'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modification Modal */}
      <SmallcaseModificationModal
        investment={selectedInvestment}
        isOpen={isModificationOpen}
        onClose={() => setIsModificationOpen(false)}
        onApplyRebalancing={handleApplyRebalancing}
      />

      {/* Market Closed Warning Dialog */}
      <AlertDialog open={showMarketClosedDialog} onOpenChange={setShowMarketClosedDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>⏰ Confirm Investment</AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              {pendingInvestment && (
                <>
                  <p>
                    You're about to invest <strong>{getCurrencySymbol(pendingInvestment.smallcase.currency)}{pendingInvestment.amount.toLocaleString()}</strong> in <strong>{pendingInvestment.smallcase.name}</strong>.
                  </p>
                  <div className="rounded-md bg-yellow-50 p-3 border border-yellow-200">
                    <p className="text-sm text-yellow-800">
                      <strong>Note:</strong> If the market is currently closed, your orders will be queued and executed when the market opens. You won't be able to cancel this investment until the orders are filled.
                    </p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Do you want to proceed?
                  </p>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setShowMarketClosedDialog(false);
              setPendingInvestment(null);
            }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={proceedWithInvestment}>
              Proceed with Investment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Insufficient Funds Dialog */}
      {insufficientDetails && (
        <InsufficientFundsDialog
          isOpen={showInsufficientDialog}
          onClose={closeInsufficientDialog}
          required={insufficientDetails.required}
          available={insufficientDetails.available}
          shortfall={insufficientDetails.shortfall}
        />
      )}
    </div>
  );
}
