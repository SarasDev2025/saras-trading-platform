"""
Flexible Scheduler Extensions
Advanced scheduling logic for time windows, continuous trading, and duration controls
"""
import json
import logging
from datetime import datetime, time, timedelta, timezone
from typing import Optional, Dict, List, Any
import pytz

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FlexibleSchedulerMixin:
    """Mixin class for advanced scheduling capabilities"""

    def _should_run_based_on_schedule(self, algo, market_config: Dict) -> bool:
        """
        Determine if algorithm should run based on scheduling type

        Types:
        - interval: Run every X minutes/hours (existing)
        - time_windows: Run within specific time windows
        - single_time: Run once per day at specific times
        - continuous: Run constantly during market hours or windows
        """
        now = datetime.now(timezone.utc)
        tz = pytz.timezone(market_config['timezone'])
        local_now = now.astimezone(tz)
        current_time = local_now.time()

        # Parse scheduling configuration
        scheduling_type = algo.scheduling_type or 'interval'

        if scheduling_type == 'continuous':
            return self._should_run_continuous(algo, current_time)

        elif scheduling_type == 'time_windows':
            return self._should_run_time_windows(algo, current_time)

        elif scheduling_type == 'single_time':
            return self._should_run_single_time(algo, current_time, local_now.date())

        elif scheduling_type == 'interval':
            # Check if within any time window (if specified)
            if algo.execution_time_windows and algo.execution_time_windows != '[]':
                in_window = self._is_in_time_window(current_time, algo.execution_time_windows)
                if not in_window:
                    return False

            # Use existing interval logic
            return self._should_run_now(algo.execution_interval, algo.last_run_at)

        return False

    def _should_run_continuous(self, algo, current_time: time) -> bool:
        """
        Run continuously during market hours or specific windows
        - No waiting, always ready to run
        - Throttled only by execution time itself
        """
        if not algo.run_continuously:
            return False

        # If has time windows, check if in window
        if algo.execution_time_windows and algo.execution_time_windows != '[]':
            return self._is_in_time_window(current_time, algo.execution_time_windows)

        # Otherwise run throughout market hours
        return True

    def _should_run_time_windows(self, algo, current_time: time) -> bool:
        """
        Run at specified interval within time windows
        Example: Run every 5 minutes, but only between 9:30-10:30 and 14:30-15:30
        """
        if not algo.execution_time_windows or algo.execution_time_windows == '[]':
            return False

        # Check if currently in any time window
        if not self._is_in_time_window(current_time, algo.execution_time_windows):
            return False

        # Check interval timing
        return self._should_run_now(algo.execution_interval, algo.last_run_at)

    def _should_run_single_time(self, algo, current_time: time, current_date) -> bool:
        """
        Run once per day at specific times
        Example: Run at 10:00 AM and 2:30 PM
        """
        if not algo.execution_times or algo.execution_times == '[]':
            return False

        execution_times = json.loads(algo.execution_times) if isinstance(algo.execution_times, str) else algo.execution_times

        # Check if already ran today
        if algo.last_run_at:
            last_run_date = algo.last_run_at.astimezone(timezone.utc).date()
            if last_run_date == current_date:
                # Already ran today, don't run again
                return False

        # Check if current time matches any execution time (within 1 minute window)
        for exec_time_str in execution_times:
            exec_time = datetime.strptime(exec_time_str, "%H:%M").time()

            # Create time range (1 minute window)
            time_diff = abs(
                (current_time.hour * 60 + current_time.minute) -
                (exec_time.hour * 60 + exec_time.minute)
            )

            if time_diff <= 1:  # Within 1 minute
                return True

        return False

    def _is_in_time_window(self, current_time: time, time_windows) -> bool:
        """Check if current time is within any of the specified windows"""
        if not time_windows:
            return False

        windows = json.loads(time_windows) if isinstance(time_windows, str) else time_windows

        if not windows or len(windows) == 0:
            return False

        for window in windows:
            start = datetime.strptime(window['start'], "%H:%M").time()
            end = datetime.strptime(window['end'], "%H:%M").time()

            if start <= current_time <= end:
                return True

        return False

    async def _should_auto_stop_duration(self, algo) -> bool:
        """Check if algorithm should stop based on duration settings"""
        if not algo.run_duration_type or algo.run_duration_type == 'forever':
            return False

        now = datetime.now(timezone.utc)
        start_date = algo.run_start_date or algo.created_at

        if not start_date:
            return False

        # Ensure start_date is timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        if algo.run_duration_type == 'until_date':
            if algo.run_end_date:
                # Ensure end_date is timezone-aware
                end_date = algo.run_end_date
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                return now >= end_date
            return False

        if algo.run_duration_type == 'days':
            days_elapsed = (now - start_date).days
            return days_elapsed >= (algo.run_duration_value or 0)

        if algo.run_duration_type == 'months':
            months_elapsed = (now.year - start_date.year) * 12 + (now.month - start_date.month)
            return months_elapsed >= (algo.run_duration_value or 0)

        if algo.run_duration_type == 'years':
            years_elapsed = now.year - start_date.year
            if now.month < start_date.month or (now.month == start_date.month and now.day < start_date.day):
                years_elapsed -= 1
            return years_elapsed >= (algo.run_duration_value or 0)

        return False

    async def _should_stop_due_to_losses(self, db: AsyncSession, algo) -> bool:
        """Check if losses exceed auto-stop threshold"""
        if not algo.auto_stop_on_loss or not algo.auto_stop_loss_threshold:
            return False

        try:
            # Get cumulative P&L from performance snapshots
            result = await db.execute(text("""
                SELECT COALESCE(SUM(daily_pnl), 0) as total_pnl
                FROM algorithm_performance_snapshots
                WHERE algorithm_id = :algorithm_id
            """), {"algorithm_id": str(algo.id)})

            snapshot = result.fetchone()
            total_pnl = float(snapshot.total_pnl if snapshot and snapshot.total_pnl else 0)

            # Stop if loss exceeds threshold (negative P&L)
            return total_pnl <= -abs(float(algo.auto_stop_loss_threshold))

        except Exception as e:
            logger.error(f"Error checking loss threshold for algo {algo.id}: {e}")
            return False

    async def _auto_stop_algorithm(self, db: AsyncSession, algorithm_id, reason: str):
        """Auto-stop algorithm and record reason"""
        try:
            await db.execute(text("""
                UPDATE trading_algorithms
                SET
                    status = 'inactive',
                    auto_run = false,
                    auto_stopped_at = NOW(),
                    auto_stop_reason = :reason,
                    currently_executing = false,
                    updated_at = NOW()
                WHERE id = :algorithm_id
            """), {"algorithm_id": str(algorithm_id), "reason": reason})
            await db.commit()

            logger.warning(f"Auto-stopped algorithm {algorithm_id}: {reason}")

        except Exception as e:
            logger.error(f"Failed to auto-stop algorithm {algorithm_id}: {e}")
            await db.rollback()

    async def _mark_executing(self, db: AsyncSession, algorithm_id, is_executing: bool):
        """Mark algorithm as currently executing or not"""
        try:
            await db.execute(text("""
                UPDATE trading_algorithms
                SET currently_executing = :is_executing,
                    updated_at = NOW()
                WHERE id = :algorithm_id
            """), {"algorithm_id": str(algorithm_id), "is_executing": is_executing})
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to mark executing status for {algorithm_id}: {e}")
            await db.rollback()

    async def _update_next_scheduled_run(self, db: AsyncSession, algo):
        """Calculate and store next scheduled run time"""
        try:
            if not algo.auto_run or algo.scheduling_type == 'manual':
                return

            now = datetime.now(timezone.utc)
            next_run = None

            if algo.scheduling_type == 'continuous':
                # Continuous runs immediately
                next_run = now

            elif algo.scheduling_type == 'single_time':
                # Calculate next occurrence of execution time
                if algo.execution_times:
                    execution_times = json.loads(algo.execution_times) if isinstance(algo.execution_times, str) else algo.execution_times
                    if execution_times:
                        # Find next time today or tomorrow
                        market_config = self.MARKET_HOURS.get(algo.region, self.MARKET_HOURS['US'])
                        tz = pytz.timezone(market_config['timezone'])
                        local_now = now.astimezone(tz)

                        for exec_time_str in sorted(execution_times):
                            exec_time = datetime.strptime(exec_time_str, "%H:%M").time()
                            exec_datetime = datetime.combine(local_now.date(), exec_time)
                            exec_datetime = tz.localize(exec_datetime)

                            if exec_datetime > local_now:
                                next_run = exec_datetime.astimezone(timezone.utc)
                                break

                        # If no time today, use first time tomorrow
                        if not next_run and execution_times:
                            tomorrow = local_now.date() + timedelta(days=1)
                            first_time = datetime.strptime(execution_times[0], "%H:%M").time()
                            exec_datetime = datetime.combine(tomorrow, first_time)
                            exec_datetime = tz.localize(exec_datetime)
                            next_run = exec_datetime.astimezone(timezone.utc)

            elif algo.scheduling_type in ['interval', 'time_windows']:
                # Calculate based on interval
                interval_seconds = {
                    '1min': 60,
                    '5min': 300,
                    '15min': 900,
                    'hourly': 3600,
                    'daily': 86400
                }

                seconds = interval_seconds.get(algo.execution_interval, 300)
                next_run = now + timedelta(seconds=seconds)

            if next_run:
                await db.execute(text("""
                    UPDATE trading_algorithms
                    SET next_scheduled_run = :next_run
                    WHERE id = :algorithm_id
                """), {"algorithm_id": str(algo.id), "next_run": next_run})
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to update next scheduled run for {algo.id}: {e}")
            await db.rollback()
