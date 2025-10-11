import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Blocks, Plus, Trash2, Eye, Save, Loader2, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react';
import { RuleBlock } from './RuleBlock';
import { StrategyTemplateSelector } from './StrategyTemplateSelector';
import { AdvancedSchedulingPanel } from './AdvancedSchedulingPanel';

interface NoCodeAlgorithmBuilderProps {
  algorithm?: any;
  onSave: (algorithm: any) => Promise<void>;
  onCancel: () => void;
}

interface Condition {
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
  multiplier?: number;
  lookback_period?: number;
}

export function NoCodeAlgorithmBuilder({ algorithm, onSave, onCancel }: NoCodeAlgorithmBuilderProps) {
  const [name, setName] = useState(algorithm?.name || '');
  const [entryConditions, setEntryConditions] = useState<Condition[]>(
    algorithm?.visual_config?.entry_conditions || []
  );
  const [exitConditions, setExitConditions] = useState<Condition[]>(
    algorithm?.visual_config?.exit_conditions || []
  );
  const [positionSizing, setPositionSizing] = useState(
    algorithm?.visual_config?.position_sizing || { type: 'fixed', quantity: 10 }
  );
  const [maxPositions, setMaxPositions] = useState(algorithm?.max_positions || 5);
  const [riskPerTrade, setRiskPerTrade] = useState(algorithm?.risk_per_trade || 2);

  // Stock universe configuration
  const [stockUniverseType, setStockUniverseType] = useState<'all' | 'specific'>(
    algorithm?.stock_universe?.type || 'all'
  );
  const [selectedSymbols, setSelectedSymbols] = useState<string>(
    algorithm?.stock_universe?.symbols?.join(', ') || ''
  );

  // Scheduling configuration
  const [schedulingConfig, setSchedulingConfig] = useState({
    scheduling_type: algorithm?.scheduling_type || 'interval',
    execution_interval: algorithm?.execution_interval || '5min',
    execution_time_windows: algorithm?.execution_time_windows || [],
    execution_times: algorithm?.execution_times || [],
    run_continuously: algorithm?.run_continuously || false,
    run_duration_type: algorithm?.run_duration_type || 'forever',
    run_duration_value: algorithm?.run_duration_value,
    run_start_date: algorithm?.run_start_date,
    run_end_date: algorithm?.run_end_date,
    auto_stop_on_loss: algorithm?.auto_stop_on_loss || false,
    auto_stop_loss_threshold: algorithm?.auto_stop_loss_threshold
  });

  const [availableBlocks, setAvailableBlocks] = useState<any>(null);
  const [compiledCode, setCompiledCode] = useState<string>('');
  const [showPreview, setShowPreview] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);

  useEffect(() => {
    fetchAvailableBlocks();
  }, []);

  const fetchAvailableBlocks = async () => {
    try {
      const response = await fetch('/api/v1/algorithms/visual-blocks', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      const data = await response.json();
      if (data.success) {
        setAvailableBlocks(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch blocks:', error);
    }
  };

  const addEntryCondition = () => {
    setEntryConditions([
      ...entryConditions,
      { id: Math.random().toString(), type: 'indicator_comparison' },
    ]);
  };

  const addExitCondition = () => {
    setExitConditions([
      ...exitConditions,
      { id: Math.random().toString(), type: 'indicator_comparison' },
    ]);
  };

  const removeEntryCondition = (id: string) => {
    setEntryConditions(entryConditions.filter((c) => c.id !== id));
  };

  const removeExitCondition = (id: string) => {
    setExitConditions(exitConditions.filter((c) => c.id !== id));
  };

  const updateEntryCondition = (id: string, updates: Partial<Condition>) => {
    setEntryConditions(
      entryConditions.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  };

  const updateExitCondition = (id: string, updates: Partial<Condition>) => {
    setExitConditions(
      exitConditions.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  };

  const handlePreviewCode = async () => {
    setValidating(true);
    try {
      const visualConfig = {
        entry_conditions: entryConditions,
        exit_conditions: exitConditions,
        position_sizing: positionSizing,
      };

      const response = await fetch('/api/v1/algorithms/visual/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(visualConfig),
      });

      const data = await response.json();
      if (data.success) {
        setCompiledCode(data.data.code);
        setValidation(data.data.validation);
        setShowPreview(true);
      } else {
        setValidation({ valid: false, error: data.message });
      }
    } catch (error: any) {
      setValidation({ valid: false, error: error.message });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const visualConfig = {
        entry_conditions: entryConditions,
        exit_conditions: exitConditions,
        position_sizing: positionSizing,
      };

      // Parse selected symbols
      const symbolsList = stockUniverseType === 'specific'
        ? selectedSymbols.split(',').map(s => s.trim()).filter(s => s.length > 0)
        : [];

      const stockUniverse = {
        type: stockUniverseType,
        symbols: symbolsList,
        filters: {}
      };

      await onSave({
        id: algorithm?.id,
        name,
        builder_type: 'visual',
        visual_config: visualConfig,
        stock_universe: stockUniverse,
        max_positions: maxPositions,
        risk_per_trade: riskPerTrade,
        ...schedulingConfig,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUseTemplate = (template: any) => {
    setName(template.name);
    setEntryConditions(
      template.visual_config.entry_conditions.map((c: any) => ({
        ...c,
        id: Math.random().toString(),
      }))
    );
    setExitConditions(
      template.visual_config.exit_conditions.map((c: any) => ({
        ...c,
        id: Math.random().toString(),
      }))
    );
    setPositionSizing(template.visual_config.position_sizing);
    setShowTemplateSelector(false);
  };

  if (!availableBlocks) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showTemplateSelector ? (
        <StrategyTemplateSelector
          onSelect={handleUseTemplate}
          onCancel={() => setShowTemplateSelector(false)}
        />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Blocks className="h-5 w-5" />
                {algorithm ? 'Edit Visual Algorithm' : 'Create Visual Algorithm'}
              </CardTitle>
              <CardDescription>
                Build your trading strategy without writing code
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowTemplateSelector(true)}
                  className="flex items-center gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  Use Template
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Strategy Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., RSI Oversold Strategy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <Tabs defaultValue="entry" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="entry">Entry Rules</TabsTrigger>
                  <TabsTrigger value="exit">Exit Rules</TabsTrigger>
                  <TabsTrigger value="config">Configuration</TabsTrigger>
                  <TabsTrigger value="schedule">Scheduling</TabsTrigger>
                </TabsList>

                <TabsContent value="entry" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Entry Conditions</Label>
                    <Button size="sm" onClick={addEntryCondition}>
                      <Plus className="h-4 w-4 mr-1" />
                      Add Condition
                    </Button>
                  </div>

                  {entryConditions.length === 0 ? (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Add at least one entry condition to define when to buy
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      {entryConditions.map((condition, index) => (
                        <RuleBlock
                          key={condition.id}
                          condition={condition}
                          availableBlocks={availableBlocks}
                          onChange={(updates) =>
                            updateEntryCondition(condition.id, updates)
                          }
                          onRemove={() => removeEntryCondition(condition.id)}
                          showLogicalOperator={index > 0}
                        />
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="exit" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Exit Conditions</Label>
                    <Button size="sm" onClick={addExitCondition}>
                      <Plus className="h-4 w-4 mr-1" />
                      Add Condition
                    </Button>
                  </div>

                  {exitConditions.length === 0 ? (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Add at least one exit condition to define when to sell
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      {exitConditions.map((condition, index) => (
                        <RuleBlock
                          key={condition.id}
                          condition={condition}
                          availableBlocks={availableBlocks}
                          onChange={(updates) =>
                            updateExitCondition(condition.id, updates)
                          }
                          onRemove={() => removeExitCondition(condition.id)}
                          showLogicalOperator={index > 0}
                        />
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="config" className="space-y-4">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Position Sizing</Label>
                      <Select
                        value={positionSizing.type}
                        onValueChange={(value) =>
                          setPositionSizing({ ...positionSizing, type: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="fixed">Fixed Quantity</SelectItem>
                          <SelectItem value="percent_portfolio">
                            Percent of Portfolio
                          </SelectItem>
                          <SelectItem value="risk_based">Risk Based</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {positionSizing.type === 'fixed' && (
                      <div className="space-y-2">
                        <Label>Quantity</Label>
                        <Input
                          type="number"
                          value={positionSizing.quantity}
                          onChange={(e) =>
                            setPositionSizing({
                              ...positionSizing,
                              quantity: parseInt(e.target.value),
                            })
                          }
                        />
                      </div>
                    )}

                    <div className="space-y-2">
                      <Label>Max Positions</Label>
                      <Input
                        type="number"
                        value={maxPositions}
                        onChange={(e) => setMaxPositions(parseInt(e.target.value))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Risk Per Trade (%)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={riskPerTrade}
                        onChange={(e) => setRiskPerTrade(parseFloat(e.target.value))}
                      />
                    </div>

                    <div className="space-y-3 pt-4 border-t">
                      <div className="space-y-2">
                        <Label>Stock Universe</Label>
                        <p className="text-sm text-muted-foreground">
                          Select which stocks this algorithm will trade
                        </p>
                        <Select
                          value={stockUniverseType}
                          onValueChange={(value: 'all' | 'specific') =>
                            setStockUniverseType(value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Available Stocks</SelectItem>
                            <SelectItem value="specific">Specific Symbols</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {stockUniverseType === 'specific' && (
                        <div className="space-y-2">
                          <Label>Stock Symbols (comma-separated)</Label>
                          <Input
                            placeholder="e.g., AAPL, MSFT, GOOGL"
                            value={selectedSymbols}
                            onChange={(e) => setSelectedSymbols(e.target.value)}
                          />
                          {selectedSymbols && (
                            <p className="text-sm text-muted-foreground">
                              Trading {selectedSymbols.split(',').filter(s => s.trim()).length} symbols: {selectedSymbols}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="schedule" className="space-y-4">
                  <AdvancedSchedulingPanel
                    config={schedulingConfig}
                    onChange={setSchedulingConfig}
                  />
                </TabsContent>
              </Tabs>

              {validation && !validation.valid && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{validation.error}</AlertDescription>
                </Alert>
              )}

              {validation && validation.valid && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>{validation.message}</AlertDescription>
                </Alert>
              )}

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={handlePreviewCode}
                  disabled={validating}
                >
                  {validating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Eye className="mr-2 h-4 w-4" />
                  )}
                  Preview Code
                </Button>
                <Button onClick={handleSave} disabled={saving || !name}>
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Strategy
                </Button>
              </div>
            </CardContent>
          </Card>

          {showPreview && compiledCode && (
            <Card>
              <CardHeader>
                <CardTitle>Generated Python Code</CardTitle>
                <CardDescription>
                  This is the code that will be executed for your visual strategy
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{compiledCode}</code>
                </pre>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
