import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
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

export default function SmallcasesPage() {
  const [selectedSmallcase, setSelectedSmallcase] = useState<Smallcase | null>(null);
  const [investmentAmount, setInvestmentAmount] = useState<number>(10000);
  const [isInvesting, setIsInvesting] = useState(false);
  const [isAddingToWatchlist, setIsAddingToWatchlist] = useState(false);
  const { toast } = useToast();

  // Fetch all smallcases
  const { data: smallcases = [], isLoading } = useQuery<Smallcase[]>({
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

  // Select first smallcase by default
  useEffect(() => {
    if (smallcases.length > 0 && !selectedSmallcase) {
      setSelectedSmallcase(smallcases[0]);
    }
  }, [smallcases, selectedSmallcase]);

  const handleInvest = async () => {
    if (!selectedSmallcase) return;
    
    try {
      setIsInvesting(true);
      await apiRequest.post('/smallcases/invest', {
        smallcaseId: selectedSmallcase.id,
        amount: investmentAmount,
      });
      
      toast({
        title: "Investment Successful",
        description: `You've successfully invested ₹${investmentAmount} in ${selectedSmallcase.name}`,
      });
    } catch (error: any) {
      console.error('Investment failed:', error);
      const errorMessage = error.response?.data?.message || "Failed to process investment";
      toast({
        title: "Investment Failed",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        variant: "destructive",
      });
    } finally {
      setIsInvesting(false);
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
      const errorMessage = error.response?.data?.message || "Failed to add to watchlist";
      toast({
        title: "Failed to Add to Watchlist",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        variant: "destructive",
      });
    } finally {
      setIsAddingToWatchlist(false);
    }
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Smallcase List */}
            <div className="lg:col-span-1 space-y-4">
              <h2 className="text-xl font-semibold">Available Smallcases</h2>
              {isLoading ? (
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
                          <span className="text-sm px-2 py-1 bg-secondary rounded-md">
                            {smallcase.riskLevel}
                          </span>
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
                            ₹{selectedSmallcase.estimatedNAV.toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Min. ₹{selectedSmallcase.minimumInvestment.toLocaleString()}
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
                                      ₹{asset.currentPrice.toLocaleString()}
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
                            Minimum investment: ₹{selectedSmallcase.minimumInvestment.toLocaleString()}
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
        </div>
      </main>
    </div>
  );
}
