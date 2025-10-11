import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Trash2, GitMerge } from 'lucide-react';

interface RuleBlockProps {
  condition: any;
  availableBlocks: any;
  onChange: (updates: any) => void;
  onRemove: () => void;
  showLogicalOperator?: boolean;
}

export function RuleBlock({
  condition,
  availableBlocks,
  onChange,
  onRemove,
  showLogicalOperator = false,
}: RuleBlockProps) {
  // Debug: Log when component renders with crossover condition
  if (condition.type === 'indicator_crossover') {
    console.log('RuleBlock crossover condition:', {
      indicator1: condition.indicator1,
      indicator2: condition.indicator2,
      hasBlocks: !!availableBlocks,
      indicatorCount: availableBlocks?.indicators?.length
    });
  }

  const conditionTypes = [
    { value: 'indicator_comparison', label: 'Indicator Comparison' },
    { value: 'price_comparison', label: 'Price Comparison' },
    { value: 'indicator_crossover', label: 'Indicator Crossover' },
    { value: 'volume_comparison', label: 'Volume Comparison' },
  ];

  const renderConditionFields = () => {
    switch (condition.type) {
      case 'indicator_comparison':
        return (
          <>
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">Indicator</Label>
                <Select
                  value={condition.indicator || undefined}
                  onValueChange={(value) => onChange({ indicator: value })}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select indicator" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.indicators?.map((ind: any) => (
                      <SelectItem key={ind.id} value={ind.id}>
                        {ind.name}
                      </SelectItem>
                    )) || []}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Operator</Label>
                <Select
                  value={condition.operator || undefined}
                  onValueChange={(value) => onChange({ operator: value })}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select operator" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.comparisons?.map((comp: any) => (
                      <SelectItem key={comp.id} value={comp.id}>
                        {comp.name}
                      </SelectItem>
                    )) || []}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Value</Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.value || ''}
                  onChange={(e) => onChange({ value: parseFloat(e.target.value) })}
                  placeholder="e.g., 30"
                />
              </div>
            </div>

            {condition.indicator && condition.indicator !== 'VOLUME' && (
              <div className="space-y-1">
                <Label className="text-xs">Period</Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.period || 14}
                  onChange={(e) => onChange({ period: parseInt(e.target.value) })}
                  placeholder="e.g., 14"
                />
              </div>
            )}
          </>
        );

      case 'price_comparison':
        return (
          <>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">Compare Price To</Label>
                <Select
                  value={condition.reference || undefined}
                  onValueChange={(value) => onChange({ reference: value })}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select reference" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.references?.map((ref: any) => (
                      <SelectItem key={ref.id} value={ref.id}>
                        {ref.name}
                      </SelectItem>
                    )) || []}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Operator</Label>
                <Select
                  value={condition.operator || undefined}
                  onValueChange={(value) => onChange({ operator: value })}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select operator" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.comparisons?.map((comp: any) => (
                      <SelectItem key={comp.id} value={comp.id}>
                        {comp.name}
                      </SelectItem>
                    )) || []}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {condition.reference === 'price' && (
              <div className="space-y-1">
                <Label className="text-xs">Value</Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.value || ''}
                  onChange={(e) => onChange({ value: parseFloat(e.target.value) })}
                  placeholder="Price value"
                />
              </div>
            )}

            {(condition.reference === 'SMA' ||
              condition.reference === 'highest_high' ||
              condition.reference === 'lowest_low') && (
              <div className="space-y-1">
                <Label className="text-xs">
                  {condition.reference === 'SMA' ? 'Period' : 'Lookback Period'}
                </Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.period || condition.lookback_period || 20}
                  onChange={(e) =>
                    onChange(
                      condition.reference === 'SMA'
                        ? { period: parseInt(e.target.value) }
                        : { lookback_period: parseInt(e.target.value) }
                    )
                  }
                  placeholder="e.g., 20"
                />
              </div>
            )}
          </>
        );

      case 'indicator_crossover':
        return (
          <>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">Fast Indicator</Label>
                <Select
                  value={condition.indicator1 || ''}
                  onValueChange={(value) => {
                    console.log('Fast indicator changed to:', value, 'current:', condition.indicator1);
                    onChange({ indicator1: value });
                  }}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select fast indicator">
                      {condition.indicator1 && (
                        availableBlocks?.indicators
                          ?.find((ind: any) => ind.id === condition.indicator1)?.name || condition.indicator1
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.indicators
                      ?.filter((ind: any) => ind.id !== 'VOLUME')
                      .map((ind: any) => (
                        <SelectItem key={ind.id} value={ind.id}>
                          {ind.name}
                        </SelectItem>
                      )) || []}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Fast Period</Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.period1 || 10}
                  onChange={(e) => onChange({ period1: parseInt(e.target.value) })}
                  placeholder="e.g., 10"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">Slow Indicator</Label>
                <Select
                  value={condition.indicator2 || ''}
                  onValueChange={(value) => {
                    console.log('Slow indicator changed to:', value, 'current:', condition.indicator2);
                    onChange({ indicator2: value });
                  }}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select slow indicator">
                      {condition.indicator2 && (
                        availableBlocks?.indicators
                          ?.find((ind: any) => ind.id === condition.indicator2)?.name || condition.indicator2
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {availableBlocks?.indicators
                      ?.filter((ind: any) => ind.id !== 'VOLUME')
                      .map((ind: any) => (
                        <SelectItem key={ind.id} value={ind.id}>
                          {ind.name}
                        </SelectItem>
                      )) || []}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Slow Period</Label>
                <Input
                  type="number"
                  className="h-9"
                  value={condition.period2 || 20}
                  onChange={(e) => onChange({ period2: parseInt(e.target.value) })}
                  placeholder="e.g., 20"
                />
              </div>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">Direction</Label>
              <Select
                value={condition.direction || 'above'}
                onValueChange={(value) => onChange({ direction: value })}
              >
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="above">Crosses Above</SelectItem>
                  <SelectItem value="below">Crosses Below</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        );

      case 'volume_comparison':
        return (
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="text-xs">Operator</Label>
              <Select
                value={condition.operator || undefined}
                onValueChange={(value) => onChange({ operator: value })}
              >
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Select operator" />
                </SelectTrigger>
                <SelectContent>
                  {availableBlocks?.comparisons?.map((comp: any) => (
                    <SelectItem key={comp.id} value={comp.id}>
                      {comp.name}
                    </SelectItem>
                  )) || []}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">Avg Volume Multiplier</Label>
              <Input
                type="number"
                step="0.1"
                className="h-9"
                value={condition.multiplier || 1.5}
                onChange={(e) => onChange({ multiplier: parseFloat(e.target.value) })}
                placeholder="e.g., 1.5"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className="p-4">
      {showLogicalOperator && (
        <div className="flex items-center gap-2 mb-3 pb-3 border-b">
          <GitMerge className="h-4 w-4 text-muted-foreground" />
          <Select
            value={condition.logicalOp || 'AND'}
            onValueChange={(value) => onChange({ logicalOp: value })}
          >
            <SelectTrigger className="h-8 w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="AND">AND</SelectItem>
              <SelectItem value="OR">OR</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground">combine with previous</span>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <Label className="text-xs">Condition Type</Label>
            <Select value={condition.type} onValueChange={(value) => onChange({ type: value })}>
              <SelectTrigger className="h-9 mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {conditionTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button variant="ghost" size="sm" onClick={onRemove} className="ml-2 mt-5">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        {renderConditionFields()}
      </div>
    </Card>
  );
}
