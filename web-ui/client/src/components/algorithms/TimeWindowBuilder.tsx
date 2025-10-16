import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, X, Clock } from 'lucide-react';

interface TimeWindow {
  start: string;
  end: string;
}

interface TimeWindowBuilderProps {
  windows: TimeWindow[];
  onChange: (windows: TimeWindow[]) => void;
}

export function TimeWindowBuilder({ windows, onChange }: TimeWindowBuilderProps) {
  const [newStart, setNewStart] = useState('09:30');
  const [newEnd, setNewEnd] = useState('10:30');
  const [error, setError] = useState('');

  const validateWindow = (start: string, end: string): boolean => {
    // Convert to minutes for comparison
    const [startHour, startMin] = start.split(':').map(Number);
    const [endHour, endMin] = end.split(':').map(Number);

    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;

    return endMinutes > startMinutes;
  };

  const handleAdd = () => {
    if (!newStart || !newEnd) {
      setError('Please enter both start and end times');
      return;
    }

    if (!validateWindow(newStart, newEnd)) {
      setError('End time must be after start time');
      return;
    }

    // Check for overlapping windows
    const overlaps = windows.some(window => {
      const [newStartHour, newStartMin] = newStart.split(':').map(Number);
      const [newEndHour, newEndMin] = newEnd.split(':').map(Number);
      const [winStartHour, winStartMin] = window.start.split(':').map(Number);
      const [winEndHour, winEndMin] = window.end.split(':').map(Number);

      const newStartMinutes = newStartHour * 60 + newStartMin;
      const newEndMinutes = newEndHour * 60 + newEndMin;
      const winStartMinutes = winStartHour * 60 + winStartMin;
      const winEndMinutes = winEndHour * 60 + winEndMin;

      return (
        (newStartMinutes >= winStartMinutes && newStartMinutes < winEndMinutes) ||
        (newEndMinutes > winStartMinutes && newEndMinutes <= winEndMinutes) ||
        (newStartMinutes <= winStartMinutes && newEndMinutes >= winEndMinutes)
      );
    });

    if (overlaps) {
      setError('This time window overlaps with an existing window');
      return;
    }

    setError('');
    onChange([...windows, { start: newStart, end: newEnd }]);
    setNewStart('09:30');
    setNewEnd('10:30');
  };

  const handleRemove = (index: number) => {
    onChange(windows.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Add Time Window</Label>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Label htmlFor="window-start" className="text-xs text-muted-foreground">
              Start Time
            </Label>
            <Input
              id="window-start"
              type="time"
              value={newStart}
              onChange={(e) => setNewStart(e.target.value)}
              className="mt-1"
            />
          </div>
          <div className="flex-1">
            <Label htmlFor="window-end" className="text-xs text-muted-foreground">
              End Time
            </Label>
            <Input
              id="window-end"
              type="time"
              value={newEnd}
              onChange={(e) => setNewEnd(e.target.value)}
              className="mt-1"
            />
          </div>
          <Button type="button" onClick={handleAdd} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>

      {windows.length > 0 ? (
        <div className="space-y-2">
          <Label className="text-sm">Active Time Windows</Label>
          <div className="space-y-2">
            {windows.map((window, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 rounded-md bg-muted/50 border"
              >
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-mono">
                    {window.start} - {window.end}
                  </span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemove(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-sm text-muted-foreground text-center py-4 border rounded-md border-dashed">
          No time windows configured. Algorithm will run throughout market hours.
        </div>
      )}
    </div>
  );
}
