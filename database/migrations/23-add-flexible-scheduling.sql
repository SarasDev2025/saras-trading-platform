-- Migration: Add Flexible Scheduling and Duration Controls
-- Purpose: Support multiple time windows, continuous trading, and flexible duration settings
-- Date: 2025-10-11

-- =====================================================
-- Drop old constraints
-- =====================================================
ALTER TABLE trading_algorithms
DROP CONSTRAINT IF EXISTS trading_algorithms_interval_check;

-- =====================================================
-- Add Flexible Scheduling Fields
-- =====================================================

-- Scheduling configuration
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS scheduling_type VARCHAR(30) DEFAULT 'interval',
ADD COLUMN IF NOT EXISTS execution_time_windows JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS execution_times JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS run_continuously BOOLEAN DEFAULT false;

-- Duration controls
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS run_duration_type VARCHAR(20) DEFAULT 'forever',
ADD COLUMN IF NOT EXISTS run_duration_value INTEGER,
ADD COLUMN IF NOT EXISTS run_start_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS run_end_date TIMESTAMP WITH TIME ZONE;

-- Auto-stop controls
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS auto_stop_on_loss BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS auto_stop_loss_threshold NUMERIC(15,2);

-- Real-time execution state
ALTER TABLE trading_algorithms
ADD COLUMN IF NOT EXISTS currently_executing BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS next_scheduled_run TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS auto_stopped_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS auto_stop_reason VARCHAR(255);

-- =====================================================
-- Add Constraints
-- =====================================================

-- Scheduling type constraint
ALTER TABLE trading_algorithms
ADD CONSTRAINT trading_algorithms_scheduling_type_check
CHECK (scheduling_type IN ('interval', 'time_windows', 'single_time', 'continuous'));

-- Duration type constraint
ALTER TABLE trading_algorithms
ADD CONSTRAINT trading_algorithms_duration_type_check
CHECK (run_duration_type IN ('forever', 'days', 'months', 'years', 'until_date'));

-- =====================================================
-- Create Indexes
-- =====================================================

-- Index for finding scheduled algorithms
CREATE INDEX IF NOT EXISTS idx_algorithms_next_run
ON trading_algorithms(next_scheduled_run)
WHERE auto_run = true AND status = 'active';

-- Index for duration-limited algorithms
CREATE INDEX IF NOT EXISTS idx_algorithms_run_end_date
ON trading_algorithms(run_end_date)
WHERE run_end_date IS NOT NULL;

-- Index for currently executing algorithms
CREATE INDEX IF NOT EXISTS idx_algorithms_currently_executing
ON trading_algorithms(currently_executing)
WHERE currently_executing = true;

-- =====================================================
-- Add Comments
-- =====================================================

COMMENT ON COLUMN trading_algorithms.scheduling_type IS
'Type of scheduling: interval (regular intervals), time_windows (specific windows), single_time (once at specific times), continuous (throughout market hours)';

COMMENT ON COLUMN trading_algorithms.execution_time_windows IS
'Array of time window objects: [{"start": "09:30", "end": "10:30"}, {"start": "14:30", "end": "15:30"}]';

COMMENT ON COLUMN trading_algorithms.execution_times IS
'Array of specific times for single_time scheduling: ["10:00", "14:00", "15:30"]';

COMMENT ON COLUMN trading_algorithms.run_continuously IS
'Run non-stop during market hours without waiting between executions';

COMMENT ON COLUMN trading_algorithms.run_duration_type IS
'Duration control type: forever (indefinite), days, months, years, until_date';

COMMENT ON COLUMN trading_algorithms.run_duration_value IS
'Numeric value for days/months/years duration (e.g., 30 for 30 days, 3 for 3 months)';

COMMENT ON COLUMN trading_algorithms.run_start_date IS
'When auto-trading started (for calculating duration)';

COMMENT ON COLUMN trading_algorithms.run_end_date IS
'Auto-stop date when run_duration_type is "until_date"';

COMMENT ON COLUMN trading_algorithms.auto_stop_on_loss IS
'Automatically stop algorithm if cumulative losses exceed threshold';

COMMENT ON COLUMN trading_algorithms.auto_stop_loss_threshold IS
'Maximum cumulative loss amount before auto-stopping ($)';

COMMENT ON COLUMN trading_algorithms.currently_executing IS
'True while algorithm execution is actively in progress';

COMMENT ON COLUMN trading_algorithms.next_scheduled_run IS
'Calculated timestamp for next scheduled execution (for UI display)';

COMMENT ON COLUMN trading_algorithms.auto_stopped_at IS
'Timestamp when algorithm was automatically stopped';

COMMENT ON COLUMN trading_algorithms.auto_stop_reason IS
'Reason for automatic stop (e.g., "Duration limit reached", "Loss threshold exceeded")';

-- =====================================================
-- Update existing algorithms with defaults
-- =====================================================

UPDATE trading_algorithms
SET
    scheduling_type = 'interval',
    execution_time_windows = '[]'::jsonb,
    execution_times = '[]'::jsonb,
    run_continuously = false,
    run_duration_type = 'forever',
    currently_executing = false
WHERE scheduling_type IS NULL;

-- =====================================================
-- Example Data Structures
-- =====================================================

/*
Example 1: Time Windows with Interval
Run every 5 minutes, but only between 9:30-10:30 AM and 2:30-3:30 PM

{
  "scheduling_type": "time_windows",
  "execution_interval": "5min",
  "execution_time_windows": [
    {"start": "09:30", "end": "10:30"},
    {"start": "14:30", "end": "15:30"}
  ],
  "run_duration_type": "months",
  "run_duration_value": 3
}

Example 2: Continuous Trading
Run non-stop throughout market hours for 30 days

{
  "scheduling_type": "continuous",
  "run_continuously": true,
  "run_duration_type": "days",
  "run_duration_value": 30
}

Example 3: Daily at Specific Times
Run once per day at 10:00 AM and 2:30 PM forever

{
  "scheduling_type": "single_time",
  "execution_times": ["10:00", "14:30"],
  "run_duration_type": "forever"
}

Example 4: Regular Intervals Throughout Day
Run every 15 minutes all day for 1 year

{
  "scheduling_type": "interval",
  "execution_interval": "15min",
  "run_duration_type": "years",
  "run_duration_value": 1
}
*/
