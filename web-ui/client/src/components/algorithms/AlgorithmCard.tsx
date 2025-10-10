import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Play,
  Pause,
  Edit,
  Trash2,
  MoreVertical,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  BarChart3,
  Code,
} from 'lucide-react';

interface AlgorithmCardProps {
  algorithm: any;
  onExecute: (id: string) => void;
  onToggle: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onBacktest: (id: string) => void;
}

export function AlgorithmCard({
  algorithm,
  onExecute,
  onToggle,
  onEdit,
  onDelete,
  onBacktest,
}: AlgorithmCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatInterval = (interval: string) => {
    const intervalMap: Record<string, string> = {
      '1min': '1 min',
      '5min': '5 min',
      '15min': '15 min',
      hourly: 'Hourly',
      daily: 'Daily',
      manual: 'Manual',
    };
    return intervalMap[interval] || interval;
  };

  const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'active':
        return 'default';
      case 'inactive':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const totalPnL = algorithm.total_pnl || 0;
  const todayPnL = algorithm.today_pnl || 0;
  const winRate = algorithm.win_rate || 0;

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5 text-muted-foreground" />
              {algorithm.name}
            </CardTitle>
            <CardDescription className="line-clamp-1">
              {algorithm.description || 'No description'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusVariant(algorithm.status)}>
              {algorithm.status}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(algorithm.id)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onBacktest(algorithm.id)}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Backtest
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => onToggle(algorithm.id)}
                  className={algorithm.status === 'active' ? 'text-orange-600' : 'text-green-600'}
                >
                  {algorithm.status === 'active' ? (
                    <>
                      <Pause className="mr-2 h-4 w-4" />
                      Deactivate
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Activate
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => onDelete(algorithm.id)}
                  className="text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Performance Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Activity className="h-3 w-3" />
                Total P&L
              </div>
              <p className={`text-lg font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(totalPnL)}
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <TrendingUp className="h-3 w-3" />
                Today
              </div>
              <p className={`text-lg font-bold ${todayPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(todayPnL)}
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <BarChart3 className="h-3 w-3" />
                Win Rate
              </div>
              <p className="text-lg font-bold">{formatPercent(winRate)}</p>
            </div>
          </div>

          {/* Configuration */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatInterval(algorithm.execution_interval)}
              </div>
              <div className="flex items-center gap-1">
                <Activity className="h-3 w-3" />
                {algorithm.total_executions || 0} runs
              </div>
            </div>

            <Button
              size="sm"
              onClick={() => onExecute(algorithm.id)}
              disabled={algorithm.status !== 'active'}
            >
              <Play className="mr-1 h-3 w-3" />
              Execute
            </Button>
          </div>

          {/* Auto-run indicator */}
          {algorithm.auto_run && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2 border-t">
              <Badge variant="outline" className="text-xs">
                Auto-run enabled
              </Badge>
              {algorithm.last_run_at && (
                <span>
                  Last run: {new Date(algorithm.last_run_at).toLocaleString()}
                </span>
              )}
            </div>
          )}

          {/* Error message if any */}
          {algorithm.last_error && (
            <div className="flex items-center gap-2 text-xs text-red-600 pt-2 border-t">
              <Activity className="h-3 w-3" />
              {algorithm.last_error}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
