import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, X, Clock } from 'lucide-react';

interface ExecutionTimePickerProps {
  times: string[];
  onChange: (times: string[]) => void;
}

export function ExecutionTimePicker({ times, onChange }: ExecutionTimePickerProps) {
  const [newTime, setNewTime] = useState('10:00');
  const [error, setError] = useState('');

  const handleAdd = () => {
    if (!newTime) {
      setError('Please enter a time');
      return;
    }

    // Check if time already exists
    if (times.includes(newTime)) {
      setError('This time is already in the list');
      return;
    }

    setError('');
    // Add and sort times
    const updatedTimes = [...times, newTime].sort();
    onChange(updatedTimes);
    setNewTime('10:00');
  };

  const handleRemove = (index: number) => {
    onChange(times.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Add Execution Time</Label>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Input
              type="time"
              value={newTime}
              onChange={(e) => setNewTime(e.target.value)}
              onKeyPress={handleKeyPress}
            />
          </div>
          <Button type="button" onClick={handleAdd} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
        {error && <p className="text-xs text-destructive">{error}</p>}
        <p className="text-xs text-muted-foreground">
          Algorithm will run once per day at each specified time
        </p>
      </div>

      {times.length > 0 ? (
        <div className="space-y-2">
          <Label className="text-sm">Scheduled Times ({times.length})</Label>
          <div className="flex flex-wrap gap-2">
            {times.map((time, index) => (
              <Badge key={index} variant="secondary" className="flex items-center gap-2 px-3 py-1">
                <Clock className="h-3 w-3" />
                <span className="font-mono">{time}</span>
                <button
                  type="button"
                  onClick={() => handleRemove(index)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-sm text-muted-foreground text-center py-4 border rounded-md border-dashed">
          No execution times configured. Add at least one time to enable this mode.
        </div>
      )}
    </div>
  );
}
