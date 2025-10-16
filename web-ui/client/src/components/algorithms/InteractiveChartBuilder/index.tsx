import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Save, Play } from 'lucide-react';
import { ChartDisplay } from './ChartDisplay';
import { ControlPanel } from './ControlPanel';
import { StrategySuggestions } from './StrategySuggestions';
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

  // Chart data and preview
  const { priceData, loading: loadingData, error: dataError, fetchData } = useChartData();
  const { signals, stats, loading: simulatingSignals, runSimulation } = useSignalSimulation();

  const [saving, setSaving] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Fetch initial data
  useEffect(() => {
    fetchData(symbol, timeRange);
  }, [symbol, timeRange]);

  // Run simulation when conditions or data change
  useEffect(() => {
    if (priceData && priceData.length > 0 && (entryConditions.length > 0 || exitConditions.length > 0)) {
      runSimulation(priceData, entryConditions, exitConditions);
    }
  }, [priceData, entryConditions, exitConditions]);

  const handleSave = async () => {
    if (!name.trim()) {
      alert('Please enter a strategy name');
      return;
    }

    if (entryConditions.length === 0) {
      alert('Please add at least one entry condition');
      return;
    }

    setSaving(true);
    try {
      const visualConfig = {
        entry_conditions: entryConditions,
        exit_conditions: exitConditions,
        position_sizing: { type: 'fixed', quantity: 10 },
      };

      await onSave({
        id: algorithm?.id,
        name,
        builder_type: 'visual',
        visual_config: visualConfig,
        max_positions: maxPositions,
        risk_per_trade: riskPerTrade,
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

      {/* Error Alert */}
      {dataError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{dataError}</AlertDescription>
        </Alert>
      )}

      {/* Main Content: Split Screen */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chart Display - 70% width */}
        <div className="lg:col-span-2">
          <ChartDisplay
            symbol={symbol}
            timeRange={timeRange}
            priceData={priceData}
            entryConditions={entryConditions}
            exitConditions={exitConditions}
            signals={signals}
            loading={loadingData}
            onSymbolChange={setSymbol}
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
            simulatingSignals={simulatingSignals}
            onNameChange={setName}
            onAddEntryCondition={handleAddEntryCondition}
            onAddExitCondition={handleAddExitCondition}
            onRemoveEntryCondition={handleRemoveEntryCondition}
            onRemoveExitCondition={handleRemoveExitCondition}
            onUpdateEntryCondition={handleUpdateEntryCondition}
            onUpdateExitCondition={handleUpdateExitCondition}
            onOpenSuggestions={() => setShowSuggestions(true)}
          />
        </div>
      </div>

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
