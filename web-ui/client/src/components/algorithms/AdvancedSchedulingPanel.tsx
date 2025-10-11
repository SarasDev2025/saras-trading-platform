import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Calendar, Clock, Infinity, Plus, Trash2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface TimeWindow {
  start: string;
  end: string;
}

interface AdvancedSchedulingConfig {
  scheduling_type: 'interval' | 'time_windows' | 'single_time' | 'continuous';
  execution_interval?: string;
  execution_time_windows: TimeWindow[];
  execution_times: string[];
  run_continuously: boolean;
  run_duration_type: 'forever' | 'days' | 'months' | 'years' | 'until_date';
  run_duration_value?: number;
  run_start_date?: string;
  run_end_date?: string;
  auto_stop_on_loss: boolean;
  auto_stop_loss_threshold?: number;
}

interface AdvancedSchedulingPanelProps {
  config: Partial<AdvancedSchedulingConfig>;
  onChange: (config: Partial<AdvancedSchedulingConfig>) => void;
}

export function AdvancedSchedulingPanel({ config, onChange }: AdvancedSchedulingPanelProps) {
  const [schedulingType, setSchedulingType] = useState<string>(config.scheduling_type || 'interval');
  const [timeWindows, setTimeWindows] = useState<TimeWindow[]>(config.execution_time_windows || []);
  const [executionTimes, setExecutionTimes] = useState<string[]>(config.execution_times || []);
  const [durationType, setDurationType] = useState<string>(config.run_duration_type || 'forever');
  const [durationValue, setDurationValue] = useState<number | undefined>(config.run_duration_value);
  const [endDate, setEndDate] = useState<string | undefined>(config.run_end_date);
  const [autoStopEnabled, setAutoStopEnabled] = useState(config.auto_stop_on_loss || false);
  const [lossThreshold, setLossThreshold] = useState<number | undefined>(config.auto_stop_loss_threshold);
  const [executionInterval, setExecutionInterval] = useState<string>(config.execution_interval || '5min');

  const updateConfig = (updates: Partial<AdvancedSchedulingConfig>) => {
    onChange({ ...config, ...updates });
  };

  const handleSchedulingTypeChange = (value: string) => {
    setSchedulingType(value);
    updateConfig({
      scheduling_type: value as AdvancedSchedulingConfig['scheduling_type'],
      run_continuously: value === 'continuous'
    });
  };

  const addTimeWindow = () => {
    const newWindows = [...timeWindows, { start: '09:30', end: '10:30' }];
    setTimeWindows(newWindows);
    updateConfig({ execution_time_windows: newWindows });
  };

  const removeTimeWindow = (index: number) => {
    const newWindows = timeWindows.filter((_, i) => i !== index);
    setTimeWindows(newWindows);
    updateConfig({ execution_time_windows: newWindows });
  };

  const updateTimeWindow = (index: number, field: 'start' | 'end', value: string) => {
    const newWindows = [...timeWindows];
    newWindows[index][field] = value;
    setTimeWindows(newWindows);
    updateConfig({ execution_time_windows: newWindows });
  };

  const addExecutionTime = () => {
    const newTimes = [...executionTimes, '10:00'];
    setExecutionTimes(newTimes);
    updateConfig({ execution_times: newTimes });
  };

  const removeExecutionTime = (index: number) => {
    const newTimes = executionTimes.filter((_, i) => i !== index);
    setExecutionTimes(newTimes);
    updateConfig({ execution_times: newTimes });
  };

  const updateExecutionTime = (index: number, value: string) => {
    const newTimes = [...executionTimes];
    newTimes[index] = value;
    setExecutionTimes(newTimes);
    updateConfig({ execution_times: newTimes });
  };

  const handleDurationTypeChange = (value: string) => {
    setDurationType(value);
    updateConfig({
      run_duration_type: value as AdvancedSchedulingConfig['run_duration_type'],
      run_duration_value: value === 'forever' ? undefined : durationValue,
      run_end_date: value === 'until_date' ? endDate : undefined
    });
  };

  const handleDurationValueChange = (value: number) => {
    setDurationValue(value);
    updateConfig({ run_duration_value: value });
  };

  const handleEndDateChange = (value: string) => {
    setEndDate(value);
    updateConfig({ run_end_date: value });
  };

  const handleAutoStopChange = (enabled: boolean) => {
    setAutoStopEnabled(enabled);
    updateConfig({
      auto_stop_on_loss: enabled,
      auto_stop_loss_threshold: enabled ? lossThreshold : undefined
    });
  };

  const handleLossThresholdChange = (value: number) => {
    setLossThreshold(value);
    updateConfig({ auto_stop_loss_threshold: value });
  };

  const handleIntervalChange = (value: string) => {
    setExecutionInterval(value);
    updateConfig({ execution_interval: value });
  };

  return (
    <div className="space-y-6">
      {/* Scheduling Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Execution Schedule
          </CardTitle>
          <CardDescription>
            Configure when and how often your algorithm should run
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup value={schedulingType} onValueChange={handleSchedulingTypeChange}>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <RadioGroupItem value="interval" id="interval" />
                <div className="flex-1">
                  <Label htmlFor="interval" className="cursor-pointer font-medium">
                    Regular Intervals
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Run every X minutes/hours throughout market hours
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="time_windows" id="time_windows" />
                <div className="flex-1">
                  <Label htmlFor="time_windows" className="cursor-pointer font-medium">
                    Time Windows
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Run at intervals within specific time windows (e.g., 9:30-10:30, 14:30-15:30)
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="single_time" id="single_time" />
                <div className="flex-1">
                  <Label htmlFor="single_time" className="cursor-pointer font-medium">
                    Specific Times
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Run once per day at specific times (e.g., 10:00 AM, 2:30 PM)
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="continuous" id="continuous" />
                <div className="flex-1">
                  <Label htmlFor="continuous" className="cursor-pointer font-medium">
                    Continuous
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Run non-stop throughout market hours (high frequency)
                  </p>
                </div>
              </div>
            </div>
          </RadioGroup>

          {/* Interval Configuration */}
          {schedulingType === 'interval' && (
            <div className="mt-4 space-y-2">
              <Label>Execution Interval</Label>
              <Select value={executionInterval} onValueChange={handleIntervalChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1min">Every 1 minute</SelectItem>
                  <SelectItem value="5min">Every 5 minutes</SelectItem>
                  <SelectItem value="15min">Every 15 minutes</SelectItem>
                  <SelectItem value="hourly">Every hour</SelectItem>
                  <SelectItem value="daily">Once per day</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Time Windows Configuration */}
          {schedulingType === 'time_windows' && (
            <div className="mt-4 space-y-4">
              <div className="space-y-2">
                <Label>Execution Interval</Label>
                <Select value={executionInterval} onValueChange={handleIntervalChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1min">Every 1 minute</SelectItem>
                    <SelectItem value="5min">Every 5 minutes</SelectItem>
                    <SelectItem value="15min">Every 15 minutes</SelectItem>
                    <SelectItem value="hourly">Every hour</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Time Windows (Market Local Time)</Label>
                {timeWindows.map((window, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      type="time"
                      value={window.start}
                      onChange={(e) => updateTimeWindow(index, 'start', e.target.value)}
                      className="w-32"
                    />
                    <span className="text-muted-foreground">to</span>
                    <Input
                      type="time"
                      value={window.end}
                      onChange={(e) => updateTimeWindow(index, 'end', e.target.value)}
                      className="w-32"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeTimeWindow(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addTimeWindow}
                  className="w-full"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Time Window
                </Button>
              </div>
            </div>
          )}

          {/* Specific Times Configuration */}
          {schedulingType === 'single_time' && (
            <div className="mt-4 space-y-2">
              <Label>Execution Times (Market Local Time)</Label>
              {executionTimes.map((time, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Input
                    type="time"
                    value={time}
                    onChange={(e) => updateExecutionTime(index, e.target.value)}
                    className="w-32"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeExecutionTime(index)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addExecutionTime}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Execution Time
              </Button>
            </div>
          )}

          {/* Continuous Mode Info */}
          {schedulingType === 'continuous' && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Continuous mode runs your algorithm non-stop during market hours. Use with caution as
                this can generate high trading volume and broker API usage.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Duration Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Duration Controls
          </CardTitle>
          <CardDescription>
            Set how long the algorithm should run
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup value={durationType} onValueChange={handleDurationTypeChange}>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <RadioGroupItem value="forever" id="forever" />
                <div className="flex-1">
                  <Label htmlFor="forever" className="cursor-pointer font-medium flex items-center gap-2">
                    <Infinity className="h-4 w-4" />
                    Run Forever
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Algorithm will run indefinitely until manually stopped
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="days" id="days" />
                <div className="flex-1">
                  <Label htmlFor="days" className="cursor-pointer font-medium">
                    Number of Days
                  </Label>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="months" id="months" />
                <div className="flex-1">
                  <Label htmlFor="months" className="cursor-pointer font-medium">
                    Number of Months
                  </Label>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="years" id="years" />
                <div className="flex-1">
                  <Label htmlFor="years" className="cursor-pointer font-medium">
                    Number of Years
                  </Label>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <RadioGroupItem value="until_date" id="until_date" />
                <div className="flex-1">
                  <Label htmlFor="until_date" className="cursor-pointer font-medium">
                    Until Specific Date
                  </Label>
                </div>
              </div>
            </div>
          </RadioGroup>

          {['days', 'months', 'years'].includes(durationType) && (
            <div className="space-y-2">
              <Label>Duration Value</Label>
              <Input
                type="number"
                min="1"
                value={durationValue || ''}
                onChange={(e) => handleDurationValueChange(Number(e.target.value))}
                placeholder={`Number of ${durationType}`}
              />
            </div>
          )}

          {durationType === 'until_date' && (
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={endDate || ''}
                onChange={(e) => handleEndDateChange(e.target.value)}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Auto-Stop on Loss */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Controls</CardTitle>
          <CardDescription>
            Automatically stop algorithm based on performance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-Stop on Loss</Label>
              <p className="text-sm text-muted-foreground">
                Stop algorithm when cumulative losses exceed threshold
              </p>
            </div>
            <Switch
              checked={autoStopEnabled}
              onCheckedChange={handleAutoStopChange}
            />
          </div>

          {autoStopEnabled && (
            <div className="space-y-2">
              <Label>Maximum Loss Threshold ($)</Label>
              <Input
                type="number"
                min="0"
                step="100"
                value={lossThreshold || ''}
                onChange={(e) => handleLossThresholdChange(Number(e.target.value))}
                placeholder="e.g., 1000"
              />
              <p className="text-xs text-muted-foreground">
                Algorithm will stop when cumulative losses reach this amount
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
