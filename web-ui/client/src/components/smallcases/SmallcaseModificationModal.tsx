// src/components/smallcases/SmallcaseModificationModal.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { apiRequest } from '@/lib/axios';
import { 
  Edit, 
  TrendingUp, 
  Zap, 
  Shield, 
  BarChart3, 
  Info,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  ChevronRight
} from 'lucide-react';

// Types (same as before)
interface UserInvestment {
  id: string;
  investmentAmount: number;
  currentValue: number;
  unrealizedPnL: number;
  smallcase: {
    id: string;
    name: string;
    theme: string;
    riskLevel: string;
  };
}

interface Stock {
  stock_id: string;
  symbol: string;
  stock_name: string;
  sector: string;
  current_price: number;
  target_weight: number;
  market_cap?: number;
  performance?: {
    price_change_1d: number;
    price_change_7d: number;
    price_change_30d: number;
    volatility_30d: number;
  };
}

interface Composition {
  smallcase_id: string;
  total_stocks: number;
  total_market_value: number;
  total_target_weight: number;
  stocks: Stock[];
}

interface Suggestion {
  stock_id: string;
  symbol: string;
  current_weight: number;
  suggested_weight: number;
  weight_change: number;
  action: 'increase' | 'decrease' | 'hold';
  reason: string;
}

interface RebalancingSuggestions {
  smallcase_id: string;
  strategy: string;
  suggestions: Suggestion[];
  summary: {
    total_weight_changes: number;
    significant_changes: number;
    strategy_description: string;
  };
}

interface SmallcaseModificationModalProps {
  investment: UserInvestment | null;
  isOpen: boolean;
  onClose: () => void;
  onApplyRebalancing: (result: any) => void;
}

const strategies = [
  {
    id: 'equal_weight',
    name: 'Equal Weight',
    description: 'Distribute investments equally across all stocks',
    icon: BarChart3,
    riskLevel: 'Medium',
    bestFor: 'Balanced diversification'
  },
  {
    id: 'market_cap',
    name: 'Market Cap Weighted',
    description: 'Weight stocks by their market capitalization',
    icon: TrendingUp,
    riskLevel: 'Medium-Low',
    bestFor: 'Index-like exposure'
  },
  {
    id: 'momentum',
    name: 'Momentum Based',
    description: 'Favor recent outperformers with volatility adjustment',
    icon: Zap,
    riskLevel: 'Medium-High',
    bestFor: 'Growth-oriented investors'
  },
  {
    id: 'volatility_adjusted',
    name: 'Risk Adjusted',
    description: 'Inverse volatility weighting to minimize risk',
    icon: Shield,
    riskLevel: 'Low-Medium',
    bestFor: 'Conservative investors'
  }
];

export const SmallcaseModificationModal: React.FC<SmallcaseModificationModalProps> = ({
  investment,
  isOpen,
  onClose,
  onApplyRebalancing
}) => {
  const [currentComposition, setCurrentComposition] = useState<Composition | null>(null);
  const [rebalancingSuggestions, setRebalancingSuggestions] = useState<RebalancingSuggestions | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState('equal_weight');
  const [isLoadingComposition, setIsLoadingComposition] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [activeTab, setActiveTab] = useState('current');
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen && investment) {
      loadCurrentComposition();
      setActiveTab('current');
      setRebalancingSuggestions(null);
    }
  }, [isOpen, investment]);

  const loadCurrentComposition = async () => {
    if (!investment) return;
    
    setIsLoadingComposition(true);
    try {
      const response = await apiRequest.get(`/smallcases/${investment.smallcase.id}/composition`);
      setCurrentComposition(response.data.data);
    } catch (error) {
      console.error('Failed to load composition:', error);
      toast({
        title: "Failed to Load",
        description: "Could not load smallcase composition. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoadingComposition(false);
    }
  };

  const loadRebalancingSuggestions = async (strategy: string) => {
    if (!investment) return;
    
    setIsLoadingSuggestions(true);
    try {
      const response = await apiRequest.post(`/api/v1/smallcases/${investment.smallcase.id}/rebalance/suggestions`, {
        strategy
      });
      setRebalancingSuggestions(response.data.data);
      setActiveTab('preview'); // Switch to preview tab
      toast({
        title: "Suggestions Generated",
        description: "AI rebalancing suggestions are ready for review.",
      });
    } catch (error) {
      console.error('Failed to load suggestions:', error);
      toast({
        title: "Failed to Generate Suggestions",
        description: "Could not generate rebalancing suggestions. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const applyRebalancing = async () => {
    if (!rebalancingSuggestions || !investment) return;
    
    setIsApplying(true);
    try {
      const response = await apiRequest.post(`/api/v1/smallcases/${investment.smallcase.id}/rebalance/apply`, {
        suggestions: rebalancingSuggestions.suggestions
      });
      
      if (response.data.success) {
        onApplyRebalancing(response.data.data);
        toast({
          title: "Rebalancing Applied",
          description: "Your smallcase has been successfully rebalanced.",
        });
        onClose();
      }
    } catch (error) {
      console.error('Failed to apply rebalancing:', error);
      toast({
        title: "Failed to Apply Rebalancing",
        description: "Could not apply rebalancing changes. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsApplying(false);
    }
  };

  const getWeightChangeIcon = (change: number) => {
    if (change > 0) return <ArrowUpRight className="w-3 h-3 text-green-600" />;
    if (change < 0) return <ArrowDownRight className="w-3 h-3 text-red-600" />;
    return null;
  };

  const getActionBadge = (action: string) => {
    const colors = {
      increase: 'bg-green-100 text-green-800 border-green-200',
      decrease: 'bg-red-100 text-red-800 border-red-200',
      hold: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return (
      <Badge className={`text-xs border ${colors[action as keyof typeof colors]}`}>
        {action.charAt(0).toUpperCase() + action.slice(1)}
      </Badge>
    );
  };

  // Create preview composition with suggested weights
  const getPreviewComposition = () => {
    if (!currentComposition || !rebalancingSuggestions) return null;
    
    const previewStocks = currentComposition.stocks.map(stock => {
      const suggestion = rebalancingSuggestions.suggestions.find(s => s.stock_id === stock.stock_id);
      return {
        ...stock,
        target_weight: suggestion ? suggestion.suggested_weight : stock.target_weight,
        weight_change: suggestion ? suggestion.weight_change : 0,
        action: suggestion ? suggestion.action : 'hold'
      };
    });
    
    return {
      ...currentComposition,
      stocks: previewStocks
    };
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="w-5 h-5" />
            Modify {investment?.smallcase?.name}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="current">Current</TabsTrigger>
            <TabsTrigger value="strategies">Strategies</TabsTrigger>
            <TabsTrigger value="preview" disabled={!rebalancingSuggestions}>
              Preview
            </TabsTrigger>
            <TabsTrigger value="apply" disabled={!rebalancingSuggestions}>
              Apply
            </TabsTrigger>
          </TabsList>

          {/* Current Holdings Tab */}
          <TabsContent value="current" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Current Portfolio Composition
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingComposition ? (
                  <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : currentComposition ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {currentComposition.total_stocks}
                        </div>
                        <div className="text-sm text-muted-foreground">Stocks</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          ₹{currentComposition.total_market_value?.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">Market Value</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {currentComposition.total_target_weight?.toFixed(1)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Total Weight</div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {currentComposition.stocks?.map((stock) => (
                        <div key={stock.stock_id} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <div className="font-semibold">{stock.symbol}</div>
                              <div className="text-sm text-muted-foreground">{stock.stock_name}</div>
                              <Badge variant="outline" className="text-xs mt-1">
                                {stock.sector}
                              </Badge>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">₹{stock.current_price}</div>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm">Weight</span>
                              <span className="font-medium">{stock.target_weight}%</span>
                            </div>
                            <Progress value={stock.target_weight} className="h-2" />
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="flex justify-end pt-4">
                      <Button onClick={() => setActiveTab('strategies')}>
                        Choose Rebalancing Strategy
                        <ChevronRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">Failed to load composition</p>
                    <Button variant="outline" onClick={loadCurrentComposition} className="mt-2">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Strategies Tab */}
          <TabsContent value="strategies" className="space-y-4">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Choose a rebalancing strategy based on your investment goals and risk tolerance. 
                Our AI will analyze your portfolio and suggest optimal weight adjustments.
              </AlertDescription>
            </Alert>

            <div className="grid gap-4">
              {strategies.map((strategy) => {
                const Icon = strategy.icon;
                const isSelected = selectedStrategy === strategy.id;
                
                return (
                  <Card 
                    key={strategy.id} 
                    className={`cursor-pointer transition-all border-2 ${
                      isSelected 
                        ? 'border-blue-500 bg-blue-50 shadow-md' 
                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }`}
                    onClick={() => setSelectedStrategy(strategy.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${
                          isSelected 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className={`font-semibold ${
                              isSelected ? 'text-blue-900' : 'text-gray-900'
                            }`}>
                              {strategy.name}
                            </h3>
                            <Badge variant="outline" className="text-xs">
                              {strategy.riskLevel}
                            </Badge>
                          </div>
                          <p className={`text-sm mb-2 ${
                            isSelected ? 'text-blue-800' : 'text-gray-600'
                          }`}>
                            {strategy.description}
                          </p>
                          <p className="text-xs font-medium text-blue-600">
                            Best for: {strategy.bestFor}
                          </p>
                        </div>
                        {isSelected && <CheckCircle className="w-5 h-5 text-blue-500" />}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <Button 
              onClick={() => loadRebalancingSuggestions(selectedStrategy)}
              disabled={isLoadingSuggestions || !currentComposition}
              className="w-full"
              size="lg"
            >
              {isLoadingSuggestions ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Generating AI Suggestions...
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4 mr-2" />
                  Preview Rebalanced Portfolio
                </>
              )}
            </Button>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-4">
            {rebalancingSuggestions ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Eye className="w-5 h-5 text-blue-500" />
                      Portfolio Preview After Rebalancing
                    </CardTitle>
                    <div className="text-sm text-muted-foreground">
                      Strategy: {strategies.find(s => s.id === selectedStrategy)?.name}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg mb-4">
                      <div className="text-center">
                        <div className="text-xl font-bold text-orange-600">
                          {rebalancingSuggestions.summary?.total_weight_changes?.toFixed(1)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Total Changes</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-blue-600">
                          {rebalancingSuggestions.summary?.significant_changes || 0}
                        </div>
                        <div className="text-sm text-muted-foreground">Significant Moves</div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {getPreviewComposition()?.stocks?.map((stock) => (
                        <div key={stock.stock_id} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="font-semibold flex items-center gap-2">
                                {stock.symbol}
                                {getWeightChangeIcon(stock.weight_change || 0)}
                              </div>
                              <div className="text-sm text-muted-foreground">{stock.stock_name}</div>
                            </div>
                            {getActionBadge(stock.action || 'hold')}
                          </div>

                          <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                            <div>
                              <div className="text-muted-foreground">Current</div>
                              <div className="font-medium">{currentComposition?.stocks?.find(s => s.stock_id === stock.stock_id)?.target_weight}%</div>
                            </div>
                            <div>
                              <div className="text-muted-foreground">New Weight</div>
                              <div className="font-medium text-blue-600">{stock.target_weight}%</div>
                            </div>
                            <div>
                              <div className="text-muted-foreground">Change</div>
                              <div className={`font-medium ${
                                (stock.weight_change || 0) > 0 ? 'text-green-600' : 
                                (stock.weight_change || 0) < 0 ? 'text-red-600' : 'text-gray-600'
                              }`}>
                                {(stock.weight_change || 0) > 0 ? '+' : ''}{(stock.weight_change || 0).toFixed(1)}%
                              </div>
                            </div>
                          </div>

                          <div className="mt-3">
                            <div className="flex justify-between text-xs text-muted-foreground mb-1">
                              <span>New allocation</span>
                              <span>{stock.target_weight}%</span>
                            </div>
                            <Progress value={stock.target_weight} className="h-2" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    onClick={() => setActiveTab('strategies')}
                    className="flex-1"
                  >
                    Try Different Strategy
                  </Button>
                  <Button 
                    onClick={() => setActiveTab('apply')}
                    className="flex-1"
                  >
                    Continue to Apply
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  Select a strategy first to see the preview
                </p>
              </div>
            )}
          </TabsContent>

          {/* Apply Tab */}
          <TabsContent value="apply" className="space-y-4">
            {rebalancingSuggestions ? (
              <>
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Ready to apply changes?</strong> This will update your smallcase composition 
                    with the new weights shown in the preview. This action cannot be undone.
                  </AlertDescription>
                </Alert>

                <Card>
                  <CardHeader>
                    <CardTitle>Rebalancing Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span>Strategy Selected:</span>
                        <span className="font-medium">{strategies.find(s => s.id === selectedStrategy)?.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Weight Changes:</span>
                        <span className="font-medium">{rebalancingSuggestions.summary?.total_weight_changes?.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Stocks Being Modified:</span>
                        <span className="font-medium">{rebalancingSuggestions.summary?.significant_changes}</span>
                      </div>
                      <div className="pt-2 border-t">
                        <p className="text-sm text-muted-foreground">
                          {rebalancingSuggestions.summary?.strategy_description}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    onClick={() => setActiveTab('preview')}
                    className="flex-1"
                  >
                    Back to Preview
                  </Button>
                  <Button 
                    onClick={applyRebalancing}
                    disabled={isApplying}
                    className="flex-1"
                  >
                    {isApplying ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Applying Changes...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Apply Rebalancing
                      </>
                    )}
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  Generate suggestions first to apply changes
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
