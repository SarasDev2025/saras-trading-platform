import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, AlertCircle, Save, Maximize, Minimize, LineChart, Settings } from 'lucide-react';
import { ChartDisplay } from './ChartDisplay';
import { ControlPanel } from './ControlPanel';
import { StrategySuggestions } from './StrategySuggestions';
import { AutoTradingConfig } from './AutoTradingConfig';
import { useChartData } from './hooks/useChartData';
import { useSignalSimulation } from './hooks/useSignalSimulation';

interface InteractiveChartBuilderProps {
  algorithm?: any;
  onSave: (algorithm: any) => Promise<void>;
  onCancel: () => void;
}

export interface Condition {
  id: string;
  type: string;
  indicator?: string;
  operator?: string;
  value?: number;
  period?: number;
  reference?: string;
  indicator1?: string;
  indicator2?: string;
  period1?: number;
  period2?: number;
  direction?: string;
}

export function InteractiveChartBuilder({ algorithm, onSave, onCancel }: InteractiveChartBuilderProps) {
  // Algorithm configuration
  const [name, setName] = useState(algorithm?.name || 'New Strategy');
  const [symbol, setSymbol] = useState('AAPL');
  const [timeRange, setTimeRange] = useState('3M'); // 1M, 3M, 6M, 1Y

  // Stock Universe - track symbols to monitor (auto-populate with analyzed symbol)
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(
    () => algorithm?.stock_universe?.symbols?.map((s: string) => s.toUpperCase()) || ['AAPL']
  );

  // Conditions
  const [entryConditions, setEntryConditions] = useState<Condition[]>(
    algorithm?.visual_config?.entry_conditions || []
  );
  const [exitConditions, setExitConditions] = useState<Condition[]>(
    algorithm?.visual_config?.exit_conditions || []
  );

  // Position sizing
  const [maxPositions, setMaxPositions] = useState(algorithm?.max_positions || 5);
  const [riskPerTrade, setRiskPerTrade] = useState(algorithm?.risk_per_trade || 2);

  // Auto-trading scheduling state
  const [autoRun, setAutoRun] = useState(algorithm?.auto_run || false);
  const [executionInterval, setExecutionInterval] = useState(algorithm?.execution_interval || '5min');
  const [schedulingType, setSchedulingType] = useState(algorithm?.scheduling_type || 'interval');
  const [executionTimeWindows, setExecutionTimeWindows] = useState<Array<{ start: string; end: string }>>(
    algorithm?.execution_time_windows || []
  );
  const [executionTimes, setExecutionTimes] = useState<string[]>(algorithm?.execution_times || []);
  const [runContinuously, setRunContinuously] = useState(algorithm?.run_continuously || false);
  const [runDurationType, setRunDurationType] = useState(algorithm?.run_duration_type || 'forever');
  const [runDurationValue, setRunDurationValue] = useState(algorithm?.run_duration_value || 30);
  const [runStartDate, setRunStartDate] = useState(algorithm?.run_start_date || '');
  const [runEndDate, setRunEndDate] = useState(algorithm?.run_end_date || '');
  const [autoStopOnLoss, setAutoStopOnLoss] = useState(algorithm?.auto_stop_on_loss || false);
  const [autoStopLossThreshold, setAutoStopLossThreshold] = useState(
    algorithm?.auto_stop_loss_threshold || 500
  );

  // Chart data and preview
  const {
    priceDataMap,
    compositeData,
    primarySymbol,
    loading: loadingData,
    error: dataError,
    fetchData,
  } = useChartData();
  const { signals, stats, portfolioSimulation, loading: simulatingSignals, runSimulation } = useSignalSimulation();

  const [saving, setSaving] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Portfolio simulation parameters
  const [initialCapital, setInitialCapital] = useState(10000);
  const [startDate, setStartDate] = useState('');

  const handleAddSymbol = (sym: string) => {
    const upper = sym.trim().toUpperCase();
    if (!upper) return;
    setSelectedSymbols((prev) => (prev.includes(upper) ? prev : [...prev, upper]));
  };

  const handleRemoveSymbol = (sym: string) => {
    setSelectedSymbols((prev) => {
      const updated = prev.filter((s) => s !== sym);
      if (updated.length === 0) {
        setSymbol('');
      } else if (!updated.includes(symbol)) {
        setSymbol(updated[0]);
      }
      return updated;
    });
  };

  const handleSymbolChange = (sym: string) => {
    const upper = sym.toUpperCase();
    if (!selectedSymbols.includes(upper)) {
      setSelectedSymbols((prev) => [...prev, upper]);
    }
    setSymbol(upper);
  };

  useEffect(() => {
    if (selectedSymbols.length > 0 && !selectedSymbols.includes(symbol)) {
      setSymbol(selectedSymbols[0]);
    }
  }, [selectedSymbols, symbol]);

  useEffect(() => {
    if (primarySymbol && selectedSymbols.length > 0 && !selectedSymbols.includes(symbol)) {
      setSymbol(primarySymbol);
    }
  }, [primarySymbol, selectedSymbols, symbol]);

  useEffect(() => {
    if (selectedSymbols.length > 0) {
      fetchData(selectedSymbols, timeRange);
    }
  }, [selectedSymbols, timeRange, fetchData]);

  const activePriceData = priceDataMap[symbol] || [];

  // Sync startDate with priceData when it loads
  useEffect(() => {
    if (activePriceData && activePriceData.length > 0 && !startDate) {
      setStartDate(activePriceData[0].date);
    }
  }, [activePriceData, startDate]);

  // Run simulation when conditions or data change
  useEffect(() => {
    if (activePriceData && activePriceData.length > 0 && (entryConditions.length > 0 || exitConditions.length > 0)) {
      console.log('Running simulation with startDate:', startDate, 'with composite:', compositeData.length, 'points');
      runSimulation(activePriceData, entryConditions, exitConditions, initialCapital, startDate, compositeData);
    }
  }, [activePriceData, entryConditions, exitConditions, initialCapital, startDate, compositeData, runSimulation]);

  const handleSave = async () => {
    if (!name.trim()) {
      alert('Please enter a strategy name');
      return;
    }

    if (entryConditions.length === 0) {
      alert('Please add at least one entry condition');
      return;
    }

    if (selectedSymbols.length === 0) {
      alert('Please analyze at least one symbol. The algorithm needs symbols to monitor.');
      return;
    }

    setSaving(true);
    try {
      const uniqueSymbols = Array.from(
        new Set(selectedSymbols.map((s) => s.toUpperCase()).filter((s) => s))
      );

      const visualConfig = {
        entry_conditions: entryConditions,
        exit_conditions: exitConditions,
        position_sizing: { type: 'fixed', quantity: 10 },
        _ui_mode: 'interactive', // Flag to distinguish from visual mode
      };

      await onSave({
        id: algorithm?.id,
        name,
        builder_type: 'visual',
        visual_config: visualConfig,
        max_positions: maxPositions,
        risk_per_trade: riskPerTrade,
        // Stock Universe - include analyzed symbols
        stock_universe: {
          type: 'specific',
          symbols: uniqueSymbols,
          filters: {}
        },
        // Auto-trading scheduling
        auto_run: autoRun,
        execution_interval: executionInterval,
        scheduling_type: schedulingType,
        execution_time_windows: executionTimeWindows,
        execution_times: executionTimes,
        run_continuously: runContinuously,
        // Duration controls
        run_duration_type: runDurationType,
        run_duration_value: runDurationValue,
        run_start_date: runStartDate || null,
        run_end_date: runEndDate || null,
        // Auto-stop
        auto_stop_on_loss: autoStopOnLoss,
        auto_stop_loss_threshold: autoStopLossThreshold,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleAddEntryCondition = () => {
    setEntryConditions([
      ...entryConditions,
      {
        id: Math.random().toString(),
        type: 'indicator_comparison',
        indicator: 'RSI',
        period: 14,
        operator: 'below',
        value: 30
      },
    ]);
  };

  const handleAddExitCondition = () => {
    setExitConditions([
      ...exitConditions,
      {
        id: Math.random().toString(),
        type: 'indicator_comparison',
        indicator: 'RSI',
        period: 14,
        operator: 'above',
        value: 70
      },
    ]);
  };

  const handleRemoveEntryCondition = (id: string) => {
    setEntryConditions(entryConditions.filter((c) => c.id !== id));
  };

  const handleRemoveExitCondition = (id: string) => {
    setExitConditions(exitConditions.filter((c) => c.id !== id));
  };

  const handleUpdateEntryCondition = (id: string, updates: Partial<Condition>) => {
    setEntryConditions(
      entryConditions.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  };

  const handleUpdateExitCondition = (id: string, updates: Partial<Condition>) => {
    setExitConditions(
      exitConditions.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  };

  const handleSelectStrategy = (strategy: any) => {
    // Apply suggested strategy
    setEntryConditions(strategy.entry_conditions.map((c: any) => ({ ...c, id: Math.random().toString() })));
    setExitConditions(strategy.exit_conditions.map((c: any) => ({ ...c, id: Math.random().toString() })));
    setName(strategy.name);
    setShowSuggestions(false);
  };

  // Reusable content for both normal and fullscreen modes
  const mainContent = (
    <>
      {/* Error Alert */}
      {dataError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{dataError}</AlertDescription>
        </Alert>
      )}

      {/* Tabs: Strategy Builder vs Auto-Trading */}
      <Tabs defaultValue="strategy" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="strategy" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Strategy Builder
          </TabsTrigger>
          <TabsTrigger value="autotrading" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Auto-Trading
          </TabsTrigger>
        </TabsList>

        <TabsContent value="strategy" className="mt-4">
          {/* Main Content: Split Screen */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Chart Display - 70% width */}
            <div className="lg:col-span-2">
        <ChartDisplay
          symbol={symbol}
          selectedSymbols={selectedSymbols}
          timeRange={timeRange}
          priceDataMap={priceDataMap}
          compositeData={compositeData}
          signals={signals}
          loading={loadingData}
          onSymbolChange={handleSymbolChange}
          onTimeRangeChange={setTimeRange}
        />
            </div>

            {/* Control Panel - 30% width */}
            <div className="lg:col-span-1">
              <ControlPanel
                name={name}
                entryConditions={entryConditions}
                exitConditions={exitConditions}
                stats={stats}
                portfolioSimulation={portfolioSimulation}
                simulatingSignals={simulatingSignals}
                initialCapital={initialCapital}
                startDate={startDate}
                onNameChange={setName}
                onAddEntryCondition={handleAddEntryCondition}
                onAddExitCondition={handleAddExitCondition}
                onRemoveEntryCondition={handleRemoveEntryCondition}
                onRemoveExitCondition={handleRemoveExitCondition}
                onUpdateEntryCondition={handleUpdateEntryCondition}
                onUpdateExitCondition={handleUpdateExitCondition}
                onOpenSuggestions={() => setShowSuggestions(true)}
                onInitialCapitalChange={setInitialCapital}
                onStartDateChange={setStartDate}
                selectedSymbols={selectedSymbols}
                onAddSymbol={handleAddSymbol}
                onRemoveSymbol={handleRemoveSymbol}
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="autotrading" className="mt-4">
          <AutoTradingConfig
            autoRun={autoRun}
            executionInterval={executionInterval}
            schedulingType={schedulingType}
            executionTimeWindows={executionTimeWindows}
            executionTimes={executionTimes}
            runContinuously={runContinuously}
            runDurationType={runDurationType}
            runDurationValue={runDurationValue}
            runStartDate={runStartDate}
            runEndDate={runEndDate}
            autoStopOnLoss={autoStopOnLoss}
            autoStopLossThreshold={autoStopLossThreshold}
            onAutoRunChange={setAutoRun}
            onExecutionIntervalChange={setExecutionInterval}
            onSchedulingTypeChange={setSchedulingType}
            onExecutionTimeWindowsChange={setExecutionTimeWindows}
            onExecutionTimesChange={setExecutionTimes}
            onRunContinuouslyChange={setRunContinuously}
            onRunDurationTypeChange={setRunDurationType}
            onRunDurationValueChange={setRunDurationValue}
            onRunStartDateChange={setRunStartDate}
            onRunEndDateChange={setRunEndDate}
            onAutoStopOnLossChange={setAutoStopOnLoss}
            onAutoStopLossThresholdChange={setAutoStopLossThreshold}
          />
        </TabsContent>
      </Tabs>
    </>
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Interactive Chart Builder</CardTitle>
              <CardDescription>
                Build your strategy visually - see signals as you configure them
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? (
                  <>
                    <Minimize className="h-4 w-4 mr-2" />
                    Exit Fullscreen
                  </>
                ) : (
                  <>
                    <Maximize className="h-4 w-4 mr-2" />
                    Fullscreen
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={onCancel} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving || loadingData}>
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Algorithm
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Normal mode: render content directly */}
      {!isFullscreen && mainContent}

      {/* Fullscreen mode: render content in Dialog */}
      <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] overflow-auto">
          <div className="space-y-4">
            {/* Fullscreen Header with Actions */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div>
                <h2 className="text-lg font-semibold">Interactive Chart Builder</h2>
                <p className="text-sm text-muted-foreground">
                  Build your strategy visually - see signals as you configure them
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onCancel} disabled={saving} size="sm">
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={saving || loadingData} size="sm">
                  {saving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Algorithm
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Main Content */}
            {mainContent}
          </div>
        </DialogContent>
      </Dialog>

      {/* Strategy Suggestions Modal */}
      <StrategySuggestions
        open={showSuggestions}
        onOpenChange={setShowSuggestions}
        symbol={symbol}
        timeRange={timeRange}
        onSelectStrategy={handleSelectStrategy}
      />
    </div>
  );
}
