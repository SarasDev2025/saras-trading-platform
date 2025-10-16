import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';

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

interface PortfolioSimulatorProps {
  initialCapital: number;
  startDate: string;
  simulation: PortfolioSimulation | null;
  onInitialCapitalChange: (value: number) => void;
  onStartDateChange: (value: string) => void;
}

export function PortfolioSimulator({
  initialCapital,
  startDate,
  simulation,
  onInitialCapitalChange,
  onStartDateChange,
}: PortfolioSimulatorProps) {
  const isProfitable = simulation && simulation.total_pnl_dollar >= 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Portfolio Simulator
        </CardTitle>
        <CardDescription>What if you started investing on a specific date?</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Input Controls */}
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="initial-capital">Initial Investment ($)</Label>
            <Input
              id="initial-capital"
              type="number"
              min="100"
              step="100"
              value={initialCapital}
              onChange={(e) => onInitialCapitalChange(Number(e.target.value))}
              placeholder="10000"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date</Label>
            <Input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => onStartDateChange(e.target.value)}
            />
          </div>
        </div>

        {/* Simulation Results */}
        {simulation ? (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Period</span>
                <span className="text-sm font-medium">
                  {simulation.start_date} → {simulation.end_date}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Initial Investment</span>
                <span className="text-sm font-medium">${simulation.initial_capital.toLocaleString()}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Final Value</span>
                <Badge variant="secondary" className="font-mono text-sm">
                  ${simulation.final_value.toLocaleString()}
                </Badge>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold flex items-center gap-1">
                  {isProfitable ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  Total P&L
                </span>
                <div className="text-right">
                  <div className={`text-lg font-bold ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                    {isProfitable ? '+' : ''}${simulation.total_pnl_dollar.toLocaleString()}
                  </div>
                  <div className={`text-sm ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                    {isProfitable ? '+' : ''}{simulation.total_pnl_percent.toFixed(2)}%
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Trades Executed:</span>
                  <Badge variant="outline" className="font-mono">
                    {simulation.trades_executed}
                  </Badge>
                </div>

                {simulation.current_position.shares > 0 ? (
                  <div className="flex items-center justify-between">
                    <span>Current Position:</span>
                    <span className="font-medium">
                      {simulation.current_position.shares.toFixed(4)} shares
                      <br />
                      <span className="text-xs">
                        (${simulation.current_position.value.toLocaleString()})
                      </span>
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span>Cash Remaining:</span>
                    <span className="font-medium">${simulation.cash_remaining.toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center text-sm text-muted-foreground py-4">
            Add conditions and set parameters above to see simulation
          </div>
        )}
      </CardContent>
    </Card>
  );
}
