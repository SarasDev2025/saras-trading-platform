import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Plus, TrendingUp, TrendingDown, Target, Percent, Loader2, Lightbulb } from 'lucide-react';
import { RuleBlock } from '../RuleBlock';
import { Condition } from './index';
import { PortfolioSimulator } from './PortfolioSimulator';

interface PortfolioSimulation {
  initial_capital: number;
  start_date: string;
  end_date: string;
  final_value: number;
  total_pnl_dollar: number;
  total_pnl_percent: number;
  current_position: {
    shares: number;
    symbol: string;
    value: number;
  };
  trades_executed: number;
  cash_remaining: number;
}

interface ControlPanelProps {
  name: string;
  entryConditions: Condition[];
  exitConditions: Condition[];
  stats: {
    signalCount: number;
    buySignals: number;
    sellSignals: number;
    estimatedWinRate?: number;
    estimatedReturn?: number;
  } | null;
  portfolioSimulation: PortfolioSimulation | null;
  simulatingSignals: boolean;
  initialCapital: number;
  startDate: string;
  onNameChange: (name: string) => void;
  onAddEntryCondition: () => void;
  onAddExitCondition: () => void;
  onRemoveEntryCondition: (id: string) => void;
  onRemoveExitCondition: (id: string) => void;
  onUpdateEntryCondition: (id: string, updates: Partial<Condition>) => void;
  onUpdateExitCondition: (id: string, updates: Partial<Condition>) => void;
  onOpenSuggestions: () => void;
  onInitialCapitalChange: (value: number) => void;
  onStartDateChange: (value: string) => void;
}

const AVAILABLE_BLOCKS = {
  indicators: [
    { id: 'RSI', name: 'RSI (Relative Strength Index)', params: ['period'] },
    { id: 'SMA', name: 'Simple Moving Average', params: ['period'] },
    { id: 'EMA', name: 'Exponential Moving Average', params: ['period'] },
    { id: 'MACD', name: 'MACD', params: ['fast', 'slow', 'signal'] },
    { id: 'BB_UPPER', name: 'Bollinger Band Upper', params: ['period', 'std_dev'] },
    { id: 'BB_LOWER', name: 'Bollinger Band Lower', params: ['period', 'std_dev'] },
    { id: 'VOLUME', name: 'Volume', params: [] },
  ],
  comparisons: [
    { id: 'above', name: 'Above' },
    { id: 'below', name: 'Below' },
    { id: 'crosses_above', name: 'Crosses Above' },
    { id: 'crosses_below', name: 'Crosses Below' },
  ],
  references: [
    { id: 'price', name: 'Price' },
    { id: 'SMA', name: 'Simple Moving Average' },
    { id: 'highest_high', name: 'Highest High' },
    { id: 'lowest_low', name: 'Lowest Low' },
  ],
};

export function ControlPanel({
  name,
  entryConditions,
  exitConditions,
  stats,
  portfolioSimulation,
  simulatingSignals,
  initialCapital,
  startDate,
  onNameChange,
  onAddEntryCondition,
  onAddExitCondition,
  onRemoveEntryCondition,
  onRemoveExitCondition,
  onUpdateEntryCondition,
  onUpdateExitCondition,
  onOpenSuggestions,
  onInitialCapitalChange,
  onStartDateChange,
}: ControlPanelProps) {
  return (
    <div className="space-y-4">
      {/* Strategy Name */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Strategy Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="strategy-name">Strategy Name</Label>
            <Input
              id="strategy-name"
              placeholder="e.g., RSI Oversold Strategy"
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
            />
          </div>
          <Button onClick={onOpenSuggestions} variant="outline" className="w-full" size="sm">
            <Lightbulb className="h-4 w-4 mr-2" />
            Get Smart Suggestions
          </Button>
        </CardContent>
      </Card>

      {/* Live Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="h-5 w-5" />
            Live Statistics
          </CardTitle>
          <CardDescription>Real-time preview on historical data</CardDescription>
        </CardHeader>
        <CardContent>
          {simulatingSignals ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : stats ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Signals</span>
                <Badge variant="secondary" className="font-mono">
                  {stats.signalCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  Buy Signals
                </span>
                <Badge variant="secondary" className="font-mono text-green-600">
                  {stats.buySignals}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <TrendingDown className="h-4 w-4 text-red-600" />
                  Sell Signals
                </span>
                <Badge variant="secondary" className="font-mono text-red-600">
                  {stats.sellSignals}
                </Badge>
              </div>
              {stats.estimatedWinRate !== undefined && stats.estimatedWinRate !== null && (
                <>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground flex items-center gap-1">
                      <Percent className="h-4 w-4" />
                      Est. Win Rate
                    </span>
                    <Badge
                      variant={stats.estimatedWinRate >= 50 ? 'default' : 'secondary'}
                      className="font-mono"
                    >
                      {stats.estimatedWinRate.toFixed(1)}%
                    </Badge>
                  </div>
                </>
              )}
              {stats.estimatedReturn !== undefined && stats.estimatedReturn !== null && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Est. Return</span>
                  <Badge
                    variant={stats.estimatedReturn >= 0 ? 'default' : 'destructive'}
                    className="font-mono"
                  >
                    {stats.estimatedReturn >= 0 ? '+' : ''}
                    {stats.estimatedReturn.toFixed(2)}%
                  </Badge>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-sm text-muted-foreground py-8">
              Add conditions to see statistics
            </div>
          )}
        </CardContent>
      </Card>

      {/* Entry Conditions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Entry Conditions</CardTitle>
            <Button size="sm" onClick={onAddEntryCondition}>
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
          <CardDescription>Define when to enter trades</CardDescription>
        </CardHeader>
        <CardContent>
          {entryConditions.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-4">
              No entry conditions yet
            </div>
          ) : (
            <div className="space-y-3">
              {entryConditions.map((condition, index) => (
                <RuleBlock
                  key={condition.id}
                  condition={condition}
                  availableBlocks={AVAILABLE_BLOCKS}
                  onChange={(updates) => onUpdateEntryCondition(condition.id, updates)}
                  onRemove={() => onRemoveEntryCondition(condition.id)}
                  showLogicalOperator={index > 0}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Exit Conditions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Exit Conditions</CardTitle>
            <Button size="sm" onClick={onAddExitCondition}>
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
          <CardDescription>Define when to exit trades</CardDescription>
        </CardHeader>
        <CardContent>
          {exitConditions.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-4">
              No exit conditions yet
            </div>
          ) : (
            <div className="space-y-3">
              {exitConditions.map((condition, index) => (
                <RuleBlock
                  key={condition.id}
                  condition={condition}
                  availableBlocks={AVAILABLE_BLOCKS}
                  onChange={(updates) => onUpdateExitCondition(condition.id, updates)}
                  onRemove={() => onRemoveExitCondition(condition.id)}
                  showLogicalOperator={index > 0}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Portfolio Simulator */}
      <PortfolioSimulator
        initialCapital={initialCapital}
        startDate={startDate}
        simulation={portfolioSimulation}
        onInitialCapitalChange={onInitialCapitalChange}
        onStartDateChange={onStartDateChange}
      />
    </div>
  );
}
