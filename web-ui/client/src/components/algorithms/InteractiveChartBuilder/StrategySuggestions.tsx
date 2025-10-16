import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, TrendingUp, TrendingDown, Target, Award, AlertCircle } from 'lucide-react';
import { Separator } from '@/components/ui/separator';

interface Strategy {
  rank: number;
  name: string;
  description: string;
  entry_conditions: any[];
  exit_conditions: any[];
  backtest_results: {
    win_rate: number;
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    total_signals: number;
    winning_trades: number;
    losing_trades: number;
  };
  confidence: 'high' | 'medium' | 'low';
  strategy_type: string;
  score: number;
}

interface StrategySuggestionsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  symbol: string;
  timeRange: string;
  onSelectStrategy: (strategy: Strategy) => void;
}

export function StrategySuggestions({
  open,
  onOpenChange,
  symbol,
  timeRange,
  onSelectStrategy,
}: StrategySuggestionsProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<Strategy[]>([]);
  const [style, setStyle] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced');
  const [analysisInfo, setAnalysisInfo] = useState<any>(null);

  const fetchSuggestions = async (tradingStyle: 'conservative' | 'balanced' | 'aggressive') => {
    setLoading(true);
    setError(null);

    try {
      // Map time ranges to days
      const daysMap: Record<string, number> = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365,
      };

      const days = daysMap[timeRange] || 90;

      const response = await fetch(
        `/api/v1/algorithms/visual/suggest-strategies?symbol=${symbol}&days=${days}&style=${tradingStyle}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      const data = await response.json();

      if (data.success) {
        setSuggestions(data.data.suggestions);
        setAnalysisInfo({
          period: data.data.analysis_period,
          dataPoints: data.data.data_points,
          strategiesTested: data.data.strategies_tested,
        });
      } else {
        setError(data.error || 'Failed to generate suggestions');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate suggestions');
    } finally {
      setLoading(false);
    }
  };

  // Fetch suggestions when dialog opens or style changes
  const handleStyleChange = (newStyle: 'conservative' | 'balanced' | 'aggressive') => {
    setStyle(newStyle);
    fetchSuggestions(newStyle);
  };

  // Auto-fetch on open
  if (open && !loading && suggestions.length === 0 && !error) {
    fetchSuggestions(style);
  }

  const getConfidenceBadgeVariant = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'default';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const getWinRateColor = (winRate: number) => {
    if (winRate >= 60) return 'text-green-600';
    if (winRate >= 45) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Smart Strategy Suggestions</DialogTitle>
          <DialogDescription>
            Statistically optimized strategies based on historical data for {symbol}
          </DialogDescription>
        </DialogHeader>

        {/* Style selector */}
        <Tabs value={style} onValueChange={(v) => handleStyleChange(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="conservative">Conservative</TabsTrigger>
            <TabsTrigger value="balanced">Balanced</TabsTrigger>
            <TabsTrigger value="aggressive">Aggressive</TabsTrigger>
          </TabsList>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center space-y-3">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">
                  Analyzing {timeRange} of historical data...
                </p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center space-y-3">
                <AlertCircle className="h-8 w-8 mx-auto text-destructive" />
                <p className="text-sm text-muted-foreground">{error}</p>
                <Button onClick={() => fetchSuggestions(style)} variant="outline" size="sm">
                  Try Again
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4 mt-4">
              {analysisInfo && (
                <div className="text-xs text-muted-foreground">
                  Analyzed {analysisInfo.dataPoints} days ({analysisInfo.period}) • Tested{' '}
                  {analysisInfo.strategiesTested} strategies
                </div>
              )}

              {suggestions.map((strategy) => (
                <Card key={strategy.rank} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="font-mono">
                            #{strategy.rank}
                          </Badge>
                          <CardTitle className="text-lg">{strategy.name}</CardTitle>
                          <Badge variant={getConfidenceBadgeVariant(strategy.confidence)}>
                            {strategy.confidence} confidence
                          </Badge>
                        </div>
                        <CardDescription>{strategy.description}</CardDescription>
                      </div>
                      <Button onClick={() => onSelectStrategy(strategy)} size="sm">
                        Apply Strategy
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Win Rate</div>
                        <div className={`text-2xl font-bold ${getWinRateColor(strategy.backtest_results.win_rate)}`}>
                          {strategy.backtest_results.win_rate.toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {strategy.backtest_results.winning_trades}W / {strategy.backtest_results.losing_trades}L
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Total Return</div>
                        <div
                          className={`text-2xl font-bold ${
                            strategy.backtest_results.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {strategy.backtest_results.total_return >= 0 ? '+' : ''}
                          {strategy.backtest_results.total_return.toFixed(1)}%
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Sharpe Ratio</div>
                        <div className="text-2xl font-bold">
                          {strategy.backtest_results.sharpe_ratio.toFixed(2)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {strategy.backtest_results.sharpe_ratio > 1.5
                            ? 'Excellent'
                            : strategy.backtest_results.sharpe_ratio > 1
                            ? 'Good'
                            : 'Fair'}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">Max Drawdown</div>
                        <div className="text-2xl font-bold text-red-600">
                          {strategy.backtest_results.max_drawdown.toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {strategy.backtest_results.total_signals} signals
                        </div>
                      </div>
                    </div>

                    <Separator className="my-3" />

                    <div className="text-xs space-y-2">
                      <div>
                        <span className="font-medium">Strategy Type:</span>{' '}
                        <Badge variant="outline" className="ml-1">
                          {strategy.strategy_type.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div>
                        <span className="font-medium">Score:</span> {(strategy.score * 100).toFixed(1)}/100
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {suggestions.length === 0 && !loading && (
                <div className="text-center py-8 text-muted-foreground">
                  No strategies found. Try a different time range or symbol.
                </div>
              )}
            </div>
          )}
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
