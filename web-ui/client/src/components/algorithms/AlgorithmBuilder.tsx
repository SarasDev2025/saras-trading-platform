import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Code, Play, Save, AlertCircle, CheckCircle2, Loader2, Blocks } from 'lucide-react';
import { NoCodeAlgorithmBuilder } from './NoCodeAlgorithmBuilder';

interface AlgorithmBuilderProps {
  algorithm?: any;
  onSave: (algorithm: any) => Promise<void>;
  onCancel: () => void;
}

const DEFAULT_TEMPLATE = `# Trading Algorithm Template
# Available helpers: generate_signal(symbol, signal_type, quantity, reason)
# Available data: positions, market_data, parameters

# Example: Simple Moving Average Crossover
# Get parameters
short_period = parameters.get('short_period', 10)
long_period = parameters.get('long_period', 20)

# Iterate through available market data
for symbol, data in market_data.items():
    current_price = data.get('price', 0)

    # Your trading logic here
    # Example: Buy if price > threshold
    threshold = parameters.get('price_threshold', 100)

    if current_price > threshold:
        # Check if we don't already have a position
        existing_position = next((p for p in positions if p['symbol'] == symbol), None)

        if not existing_position:
            # Generate buy signal
            quantity = parameters.get('position_size', 10)
            generate_signal(
                symbol=symbol,
                signal_type='buy',
                quantity=quantity,
                reason=f'Price {current_price} crossed threshold {threshold}'
            )
`;

export function AlgorithmBuilder({ algorithm, onSave, onCancel }: AlgorithmBuilderProps) {
  const [builderMode, setBuilderMode] = useState<'code' | 'visual'>(
    algorithm?.builder_type || 'code'
  );
  const [name, setName] = useState(algorithm?.name || '');
  const [strategyCode, setStrategyCode] = useState(algorithm?.strategy_code || DEFAULT_TEMPLATE);
  const [autoRun, setAutoRun] = useState(algorithm?.auto_run || false);
  const [executionInterval, setExecutionInterval] = useState(algorithm?.execution_interval || 'manual');
  const [maxPositions, setMaxPositions] = useState(algorithm?.max_positions || 5);
  const [riskPerTrade, setRiskPerTrade] = useState(algorithm?.risk_per_trade || 2);
  const [parameters, setParameters] = useState(algorithm?.parameters || {});

  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const handleValidate = async () => {
    setValidating(true);
    try {
      const response = await fetch('/api/v1/algorithms/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ strategy_code: strategyCode }),
      });

      const data = await response.json();
      setValidation(data);
    } catch (error) {
      setValidation({ valid: false, error: 'Failed to validate code' });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        id: algorithm?.id,
        name,
        strategy_code: strategyCode,
        auto_run: autoRun,
        execution_interval: executionInterval,
        max_positions: maxPositions,
        risk_per_trade: riskPerTrade,
        parameters,
      });
    } finally {
      setSaving(false);
    }
  };

  const addParameter = (key: string, value: any) => {
    setParameters({ ...parameters, [key]: value });
  };

  // If visual mode, show NoCodeAlgorithmBuilder
  if (builderMode === 'visual') {
    return <NoCodeAlgorithmBuilder algorithm={algorithm} onSave={onSave} onCancel={onCancel} />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                {algorithm ? 'Edit Algorithm' : 'Create Algorithm'}
              </CardTitle>
              <CardDescription>
                Build your custom trading algorithm with Python
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={builderMode === 'code' ? 'default' : 'outline' as const}
                size="sm"
                onClick={() => setBuilderMode('code')}
              >
                <Code className="h-4 w-4 mr-1" />
                Code
              </Button>
              <Button
                variant={builderMode === 'visual' ? 'default' : 'outline' as const}
                size="sm"
                onClick={() => setBuilderMode('visual')}
              >
                <Blocks className="h-4 w-4 mr-1" />
                Visual
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="code" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="config">Configuration</TabsTrigger>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
            </TabsList>

            <TabsContent value="code" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Algorithm Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., SMA Crossover Strategy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="code">Strategy Code</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleValidate}
                    disabled={validating}
                  >
                    {validating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Validating...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        Validate
                      </>
                    )}
                  </Button>
                </div>
                <Textarea
                  id="code"
                  placeholder="Enter your Python algorithm code..."
                  value={strategyCode}
                  onChange={(e) => setStrategyCode(e.target.value)}
                  className="font-mono text-sm min-h-[400px]"
                />
              </div>

              {validation && (
                <Alert variant={validation.valid ? 'default' : 'destructive'}>
                  {validation.valid ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>
                    {validation.valid ? validation.message : validation.error}
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            <TabsContent value="config" className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto Run</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable automatic execution on schedule
                    </p>
                  </div>
                  <Switch checked={autoRun} onCheckedChange={setAutoRun} />
                </div>

                {autoRun && (
                  <div className="space-y-2">
                    <Label htmlFor="interval">Execution Interval</Label>
                    <Select value={executionInterval} onValueChange={setExecutionInterval}>
                      <SelectTrigger id="interval">
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

                <div className="space-y-2">
                  <Label htmlFor="max-positions">Max Positions</Label>
                  <Input
                    id="max-positions"
                    type="number"
                    min={1}
                    max={50}
                    value={maxPositions}
                    onChange={(e) => setMaxPositions(parseInt(e.target.value))}
                  />
                  <p className="text-sm text-muted-foreground">
                    Maximum number of concurrent positions
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="risk-per-trade">Risk Per Trade (%)</Label>
                  <Input
                    id="risk-per-trade"
                    type="number"
                    min={0.1}
                    max={10}
                    step={0.1}
                    value={riskPerTrade}
                    onChange={(e) => setRiskPerTrade(parseFloat(e.target.value))}
                  />
                  <p className="text-sm text-muted-foreground">
                    Maximum portfolio risk per individual trade
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="parameters" className="space-y-4">
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  Add custom parameters that your algorithm can access
                </div>

                <div className="space-y-2">
                  {Object.entries(parameters).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2">
                      <Badge variant="secondary">{key}</Badge>
                      <span className="text-sm">=</span>
                      <code className="text-sm">{JSON.stringify(value)}</code>
                    </div>
                  ))}

                  {Object.keys(parameters).length === 0 && (
                    <p className="text-sm text-muted-foreground">No parameters defined</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Parameter Name</Label>
                    <Input
                      id="param-key"
                      placeholder="e.g., short_period"
                    />
                  </div>
                  <div>
                    <Label>Value</Label>
                    <Input
                      id="param-value"
                      placeholder="e.g., 10"
                    />
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const keyInput = document.getElementById('param-key') as HTMLInputElement;
                    const valueInput = document.getElementById('param-value') as HTMLInputElement;

                    if (keyInput.value && valueInput.value) {
                      let value: any = valueInput.value;

                      // Try to parse as number
                      if (!isNaN(Number(value))) {
                        value = Number(value);
                      }

                      addParameter(keyInput.value, value);
                      keyInput.value = '';
                      valueInput.value = '';
                    }
                  }}
                >
                  Add Parameter
                </Button>
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex justify-end gap-2 mt-6 pt-6 border-t">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || !name || !strategyCode}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Algorithm
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
