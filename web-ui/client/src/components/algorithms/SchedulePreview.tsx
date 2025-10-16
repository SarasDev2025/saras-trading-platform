import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Calendar, Clock, AlertTriangle, TrendingDown, Info } from 'lucide-react';

interface SchedulePreviewProps {
  schedulingType: string;
  executionInterval?: string;
  executionTimeWindows?: Array<{ start: string; end: string }>;
  executionTimes?: string[];
  runContinuously?: boolean;
  runDurationType?: string;
  runDurationValue?: number;
  runStartDate?: string;
  runEndDate?: string;
  autoStopOnLoss?: boolean;
  autoStopLossThreshold?: number;
}

export function SchedulePreview({
  schedulingType,
  executionInterval,
  executionTimeWindows,
  executionTimes,
  runContinuously,
  runDurationType,
  runDurationValue,
  runStartDate,
  runEndDate,
  autoStopOnLoss,
  autoStopLossThreshold,
}: SchedulePreviewProps) {
  const getScheduleDescription = () => {
    switch (schedulingType) {
      case 'continuous':
        if (executionTimeWindows && executionTimeWindows.length > 0) {
          return `Runs continuously within ${executionTimeWindows.length} time window(s)`;
        }
        return 'Runs continuously during market hours';

      case 'time_windows':
        const windowCount = executionTimeWindows?.length || 0;
        return `Runs every ${executionInterval || '5min'} within ${windowCount} time window(s)`;

      case 'single_time':
        const timeCount = executionTimes?.length || 0;
        return `Runs once per day at ${timeCount} scheduled time(s)`;

      case 'interval':
      default:
        if (executionTimeWindows && executionTimeWindows.length > 0) {
          return `Runs every ${executionInterval || 'manual'} within time windows`;
        }
        return `Runs every ${executionInterval || 'manual'}`;
    }
  };

  const getDurationDescription = () => {
    if (!runDurationType || runDurationType === 'forever') {
      return 'Runs indefinitely';
    }

    if (runDurationType === 'until_date' && runEndDate) {
      return `Runs until ${new Date(runEndDate).toLocaleDateString()}`;
    }

    if (runDurationValue) {
      return `Runs for ${runDurationValue} ${runDurationType}`;
    }

    return 'Duration not configured';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Schedule Summary
        </CardTitle>
        <CardDescription>Preview of your algorithm's execution schedule</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Scheduling Type */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Scheduling Mode</span>
            <Badge variant="secondary" className="capitalize">
              {schedulingType.replace('_', ' ')}
            </Badge>
          </div>
          <p className="text-sm">{getScheduleDescription()}</p>
        </div>

        {/* Time Windows */}
        {executionTimeWindows && executionTimeWindows.length > 0 && (
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Active Time Windows
            </span>
            <div className="space-y-1">
              {executionTimeWindows.map((window, index) => (
                <div key={index} className="text-sm font-mono bg-muted/50 px-2 py-1 rounded">
                  {window.start} - {window.end}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Execution Times */}
        {executionTimes && executionTimes.length > 0 && (
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Daily Execution Times
            </span>
            <div className="flex flex-wrap gap-2">
              {executionTimes.map((time, index) => (
                <Badge key={index} variant="outline" className="font-mono">
                  {time}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Duration */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Duration</span>
            <Badge variant={runDurationType === 'forever' ? 'default' : 'secondary'}>
              {runDurationType === 'forever' ? 'Indefinite' : 'Limited'}
            </Badge>
          </div>
          <p className="text-sm">{getDurationDescription()}</p>
          {runStartDate && (
            <p className="text-xs text-muted-foreground">
              Start: {new Date(runStartDate).toLocaleDateString()}
            </p>
          )}
        </div>

        {/* Auto-Stop Warnings */}
        {(autoStopOnLoss || runDurationType !== 'forever') && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <strong>Auto-Stop Enabled</strong>
              <ul className="mt-2 space-y-1 text-xs">
                {autoStopOnLoss && autoStopLossThreshold && (
                  <li className="flex items-center gap-2">
                    <TrendingDown className="h-3 w-3" />
                    Stops if cumulative loss exceeds ${autoStopLossThreshold}
                  </li>
                )}
                {runDurationType !== 'forever' && (
                  <li className="flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    {getDurationDescription()}
                  </li>
                )}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Info */}
        {schedulingType === 'continuous' && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Continuous mode runs as frequently as possible. Actual frequency depends on algorithm
              execution time and market data updates.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
