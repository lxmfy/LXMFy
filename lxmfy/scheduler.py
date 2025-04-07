"""Task scheduling system for LXMFy.

This module provides cron-style scheduling and background task management
for LXMFy bots.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Event, Thread
from typing import Callable, Optional

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """A scheduled task with cron-style timing"""
    name: str
    callback: Callable
    cron_expr: str  # "* * * * *" (min hour day month weekday)
    last_run: Optional[datetime] = None
    enabled: bool = True

    def should_run(self, current_time: datetime) -> bool:
        """Check if task should run at given time"""
        if not self.enabled:
            return False

        if self.last_run and current_time - self.last_run < timedelta(minutes=1):
            return False

        return self._match_cron(current_time)

    def _match_cron(self, dt: datetime) -> bool:
        """Match datetime against cron expression"""
        parts = self.cron_expr.split()
        if len(parts) != 5:
            return False

        minute, hour, day, month, weekday = parts

        return (
            self._match_field(minute, dt.minute, 0, 59) and
            self._match_field(hour, dt.hour, 0, 23) and
            self._match_field(day, dt.day, 1, 31) and
            self._match_field(month, dt.month, 1, 12) and
            ScheduledTask._match_field(weekday, dt.weekday(), 0, 6)
        )

    @staticmethod
    def _match_field(pattern: str, value: int, min_val: int, max_val: int) -> bool:
        """Match a cron field pattern"""
        if pattern == "*":
            return True

        parts = pattern.split(",")
        for part in parts:
            if "-" in part:
                start, end = map(int, part.split("-"))
                if min_val <= start <= value <= end <= max_val:
                    return True
            elif "/" in part:
                step = int(part.split("/")[1])
                if value % step == 0:
                    return True
            elif int(part) == value:
                return True

        return False

class TaskScheduler:
    """Manages scheduled tasks and background processes"""

    def __init__(self, bot):
        self.bot = bot
        self.tasks: dict[str, ScheduledTask] = {}
        self.background_tasks: list[Thread] = []
        self.stop_event = Event()
        self.logger = logging.getLogger(__name__)

    def schedule(self, name: str, cron_expr: str):
        """Decorator to schedule a task"""
        def decorator(func):
            self.add_task(name, func, cron_expr)
            return func
        return decorator

    def add_task(self, name: str, callback: Callable, cron_expr: str):
        """Add a scheduled task"""
        self.tasks[name] = ScheduledTask(name, callback, cron_expr)

    def remove_task(self, name: str):
        """Remove a scheduled task"""
        self.tasks.pop(name, None)

    def start(self):
        """Start the scheduler"""
        self.stop_event.clear()
        scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        scheduler_thread.start()
        self.background_tasks.append(scheduler_thread)

    def stop(self):
        """Stop the scheduler"""
        self.stop_event.set()
        for task in self.background_tasks:
            task.join()
        self.background_tasks.clear()

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while not self.stop_event.is_set():
            current_time = datetime.now()

            for task in self.tasks.values():
                try:
                    if task.should_run(current_time):
                        task.callback()
                        task.last_run = current_time
                except Exception as e:
                    self.logger.error("Error running task %s: %s", task.name, str(e))

            time.sleep(60 - datetime.now().second)  # Wait until start of next minute 