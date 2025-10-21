import { useLocation } from "wouter";
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
  Activity,
  Clock,
  BarChart3,
  Code,
  Calendar,
  AlertTriangle,
  Timer,
  ExternalLink,
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
  const [, navigate] = useLocation();

  const handleViewDetails = () => {
    navigate(`/algorithms/${algorithm.id}`);
  };

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

  const getSchedulingTypeBadge = (schedulingType: string) => {
    const typeMap: Record<string, string> = {
      interval: 'Interval',
      time_windows: 'Time Windows',
      single_time: 'Scheduled',
      continuous: 'Continuous',
    };
    return typeMap[schedulingType] || 'Interval';
  };

  const getDurationText = (algorithm: any) => {
    if (!algorithm.run_duration_type || algorithm.run_duration_type === 'forever') {
      return 'Indefinite';
    }

    if (algorithm.run_duration_type === 'until_date' && algorithm.run_end_date) {
      const endDate = new Date(algorithm.run_end_date);
      return `Until ${endDate.toLocaleDateString()}`;
    }

    if (algorithm.run_duration_value) {
      return `${algorithm.run_duration_value} ${algorithm.run_duration_type}`;
    }

    return 'Limited';
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
  const positionsCount = algorithm.positions_count || 0;
  const marketValue = algorithm.market_value || 0;
  const successRate = algorithm.total_executions > 0
    ? ((algorithm.successful_executions / algorithm.total_executions) * 100)
    : 0;

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={handleViewDetails}>
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
                <Button variant="ghost" size="icon" onClick={(e) => e.stopPropagation()}>
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleViewDetails}>
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(algorithm.id);
                  }}
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onBacktest(algorithm.id);
                  }}
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Backtest
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggle(algorithm.id);
                  }}
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
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(algorithm.id);
                  }}
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
                <TrendingUp className="h-3 w-3" />
                Total P&L
              </div>
              <p className={`text-lg font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(totalPnL)}
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Activity className="h-3 w-3" />
                Positions
              </div>
              <p className="text-lg font-bold">
                {positionsCount}
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <BarChart3 className="h-3 w-3" />
                Value
              </div>
              <p className="text-lg font-bold">{formatCurrency(marketValue)}</p>
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
              onClick={(e) => {
                e.stopPropagation();
                onExecute(algorithm.id);
              }}
              disabled={algorithm.status !== 'active'}
            >
              <Play className="mr-1 h-3 w-3" />
              Execute
            </Button>
          </div>

          {/* Scheduling Information */}
          {algorithm.auto_run && (
            <div className="space-y-2 pt-2 border-t">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  <Timer className="h-3 w-3 mr-1" />
                  {getSchedulingTypeBadge(algorithm.scheduling_type || 'interval')}
                </Badge>

                {algorithm.scheduling_type !== 'continuous' && (
                  <Badge variant="outline" className="text-xs">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatInterval(algorithm.execution_interval)}
                  </Badge>
                )}

                <Badge
                  variant="outline"
                  className={`text-xs ${
                    algorithm.run_duration_type !== 'forever' ? 'border-orange-500 text-orange-600' : ''
                  }`}
                >
                  <Calendar className="h-3 w-3 mr-1" />
                  {getDurationText(algorithm)}
                </Badge>

                {algorithm.auto_stop_on_loss && algorithm.auto_stop_loss_threshold && (
                  <Badge variant="outline" className="text-xs border-red-500 text-red-600">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Stop at ${algorithm.auto_stop_loss_threshold}
                  </Badge>
                )}
              </div>

              {algorithm.execution_time_windows && algorithm.execution_time_windows.length > 0 && (
                <div className="text-xs text-muted-foreground">
                  <span className="font-medium">Time windows:</span>{' '}
                  {algorithm.execution_time_windows
                    .map((w: any) => `${w.start}-${w.end}`)
                    .join(', ')}
                </div>
              )}

              {algorithm.execution_times && algorithm.execution_times.length > 0 && (
                <div className="text-xs text-muted-foreground">
                  <span className="font-medium">Execution times:</span>{' '}
                  {algorithm.execution_times.join(', ')}
                </div>
              )}

              {algorithm.last_run_at && (
                <div className="text-xs text-muted-foreground">
                  Last run: {new Date(algorithm.last_run_at).toLocaleString()}
                </div>
              )}

              {algorithm.next_scheduled_run && (
                <div className="text-xs text-muted-foreground">
                  Next run: {new Date(algorithm.next_scheduled_run).toLocaleString()}
                </div>
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
