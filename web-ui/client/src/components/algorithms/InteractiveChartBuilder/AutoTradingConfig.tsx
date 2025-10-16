import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { Settings } from 'lucide-react';
import { TimeWindowBuilder } from '../TimeWindowBuilder';
import { ExecutionTimePicker } from '../ExecutionTimePicker';
import { SchedulePreview } from '../SchedulePreview';

interface AutoTradingConfigProps {
  autoRun: boolean;
  executionInterval: string;
  schedulingType: string;
  executionTimeWindows: Array<{ start: string; end: string }>;
  executionTimes: string[];
  runContinuously: boolean;
  runDurationType: string;
  runDurationValue: number;
  runStartDate: string;
  runEndDate: string;
  autoStopOnLoss: boolean;
  autoStopLossThreshold: number;
  onAutoRunChange: (value: boolean) => void;
  onExecutionIntervalChange: (value: string) => void;
  onSchedulingTypeChange: (value: string) => void;
  onExecutionTimeWindowsChange: (value: Array<{ start: string; end: string }>) => void;
  onExecutionTimesChange: (value: string[]) => void;
  onRunContinuouslyChange: (value: boolean) => void;
  onRunDurationTypeChange: (value: string) => void;
  onRunDurationValueChange: (value: number) => void;
  onRunStartDateChange: (value: string) => void;
  onRunEndDateChange: (value: string) => void;
  onAutoStopOnLossChange: (value: boolean) => void;
  onAutoStopLossThresholdChange: (value: number) => void;
}

export function AutoTradingConfig({
  autoRun,
  executionInterval,
  schedulingType,
  executionTimeWindows,
  executionTimes,
  runContinuously,
  runDurationType,
  runDurationValue,
  runStartDate,
  runEndDate,
  autoStopOnLoss,
  autoStopLossThreshold,
  onAutoRunChange,
  onExecutionIntervalChange,
  onSchedulingTypeChange,
  onExecutionTimeWindowsChange,
  onExecutionTimesChange,
  onRunContinuouslyChange,
  onRunDurationTypeChange,
  onRunDurationValueChange,
  onRunStartDateChange,
  onRunEndDateChange,
  onAutoStopOnLossChange,
  onAutoStopLossThresholdChange,
}: AutoTradingConfigProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Auto-Trading Configuration
            </CardTitle>
            <CardDescription>
              Configure when and how your algorithm executes automatically
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Auto-Run Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable Auto-Trading</Label>
                <p className="text-sm text-muted-foreground">
                  Algorithm will execute automatically on schedule
                </p>
              </div>
              <Switch checked={autoRun} onCheckedChange={onAutoRunChange} />
            </div>

            {autoRun && (
              <>
                <Separator />

                {/* Scheduling Type */}
                <div className="space-y-3">
                  <Label>Scheduling Mode</Label>
                  <RadioGroup value={schedulingType} onValueChange={onSchedulingTypeChange}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="interval" id="auto-scheduling-interval" />
                      <Label htmlFor="auto-scheduling-interval" className="font-normal cursor-pointer">
                        Interval - Run every X minutes/hours
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="time_windows" id="auto-scheduling-windows" />
                      <Label htmlFor="auto-scheduling-windows" className="font-normal cursor-pointer">
                        Time Windows - Run within specific hours
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="single_time" id="auto-scheduling-single" />
                      <Label htmlFor="auto-scheduling-single" className="font-normal cursor-pointer">
                        Single Time - Run once per day at specific times
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="continuous" id="auto-scheduling-continuous" />
                      <Label htmlFor="auto-scheduling-continuous" className="font-normal cursor-pointer">
                        Continuous - Run as frequently as possible
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                {/* Interval Settings */}
                {(schedulingType === 'interval' || schedulingType === 'time_windows') && (
                  <div className="space-y-2">
                    <Label htmlFor="auto-interval">Execution Interval</Label>
                    <Select value={executionInterval} onValueChange={onExecutionIntervalChange}>
                      <SelectTrigger id="auto-interval">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1min">Every 1 Minute</SelectItem>
                        <SelectItem value="5min">Every 5 Minutes</SelectItem>
                        <SelectItem value="15min">Every 15 Minutes</SelectItem>
                        <SelectItem value="hourly">Hourly</SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Time Windows */}
                {(schedulingType === 'time_windows' ||
                  schedulingType === 'interval' ||
                  schedulingType === 'continuous') && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <Label>Time Windows {schedulingType === 'interval' && '(Optional)'}</Label>
                      <p className="text-xs text-muted-foreground">
                        {schedulingType === 'interval'
                          ? 'Optionally restrict execution to specific time windows'
                          : 'Define when the algorithm should run'}
                      </p>
                      <TimeWindowBuilder
                        windows={executionTimeWindows}
                        onChange={onExecutionTimeWindowsChange}
                      />
                    </div>
                  </>
                )}

                {/* Execution Times */}
                {schedulingType === 'single_time' && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <Label>Execution Times</Label>
                      <p className="text-xs text-muted-foreground">
                        Specify exact times to run once per day
                      </p>
                      <ExecutionTimePicker times={executionTimes} onChange={onExecutionTimesChange} />
                    </div>
                  </>
                )}

                <Separator />

                {/* Duration Controls */}
                <div className="space-y-3">
                  <Label>Run Duration</Label>
                  <Select value={runDurationType} onValueChange={onRunDurationTypeChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="forever">Run Indefinitely</SelectItem>
                      <SelectItem value="days">Run for X Days</SelectItem>
                      <SelectItem value="months">Run for X Months</SelectItem>
                      <SelectItem value="years">Run for X Years</SelectItem>
                      <SelectItem value="until_date">Run Until Specific Date</SelectItem>
                    </SelectContent>
                  </Select>

                  {runDurationType !== 'forever' && runDurationType !== 'until_date' && (
                    <Input
                      type="number"
                      min={1}
                      value={runDurationValue}
                      onChange={(e) => onRunDurationValueChange(parseInt(e.target.value))}
                      placeholder={`Number of ${runDurationType}`}
                    />
                  )}

                  {runDurationType === 'until_date' && (
                    <Input
                      type="date"
                      value={runEndDate}
                      onChange={(e) => onRunEndDateChange(e.target.value)}
                    />
                  )}
                </div>

                <Separator />

                {/* Auto-Stop on Loss */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Auto-Stop on Loss</Label>
                      <p className="text-xs text-muted-foreground">
                        Automatically stop if losses exceed threshold
                      </p>
                    </div>
                    <Switch checked={autoStopOnLoss} onCheckedChange={onAutoStopOnLossChange} />
                  </div>

                  {autoStopOnLoss && (
                    <div className="space-y-2">
                      <Label htmlFor="auto-loss-threshold">Loss Threshold ($)</Label>
                      <Input
                        id="auto-loss-threshold"
                        type="number"
                        min={0}
                        step={10}
                        value={autoStopLossThreshold}
                        onChange={(e) => onAutoStopLossThresholdChange(parseFloat(e.target.value))}
                        placeholder="500"
                      />
                      <p className="text-xs text-muted-foreground">
                        Algorithm will stop if cumulative loss exceeds this amount
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Schedule Preview */}
      <div>
        {autoRun && (
          <SchedulePreview
            schedulingType={schedulingType}
            executionInterval={executionInterval}
            executionTimeWindows={executionTimeWindows}
            executionTimes={executionTimes}
            runContinuously={runContinuously}
            runDurationType={runDurationType}
            runDurationValue={runDurationValue}
            runStartDate={runStartDate}
            runEndDate={runEndDate}
            autoStopOnLoss={autoStopOnLoss}
            autoStopLossThreshold={autoStopLossThreshold}
          />
        )}
      </div>
    </div>
  );
}
