"""Event system module for LXMFy.

This module provides a comprehensive event handling system including:
- Custom event creation and dispatching
- Event middleware support
- Event logging and monitoring
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Priority levels for event handlers"""
    HIGHEST = 3
    HIGH = 2
    NORMAL = 1
    LOW = 0

@dataclass(frozen=True)
class Event:
    """Event data class"""
    name: str
    data: dict = field(default_factory=dict)
    cancelled: bool = False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return self.name == other.name

    def cancel(self):
        object.__setattr__(self, 'cancelled', True)

@dataclass
class EventHandler:
    """Event handler with priority"""
    callback: Callable
    priority: EventPriority

class EventManager:
    """Manages event registration, dispatching and middleware"""

    def __init__(self, storage):
        self.storage = storage
        self.handlers = {}  # Change to use event names as keys instead of Event objects
        self.logger = logging.getLogger(__name__)

    def on(self, event_name: str, priority: EventPriority = EventPriority.NORMAL):
        """Register an event handler"""
        def decorator(func):
            if event_name not in self.handlers:
                self.handlers[event_name] = []
            self.handlers[event_name].append((priority, func))
            self.handlers[event_name].sort(key=lambda x: x[0].value, reverse=True)
            return func
        return decorator

    def use(self, middleware: Callable):
        """Add middleware to the event pipeline"""
        # This method is no longer used in the new implementation
        pass

    def dispatch(self, event: Event):
        """Dispatch event to all registered handlers"""
        try:
            if event.name in self.handlers:
                for priority, handler in self.handlers[event.name]:
                    try:
                        handler(event)
                        # Check if the event was cancelled by the handler
                        if event.cancelled:
                            break # Stop processing further handlers for this event
                    except Exception as e:
                        self.logger.error("Error in event handler %s: %s", handler.__name__, str(e))
        except Exception as e:
            self.logger.error("Error dispatching event: %s", str(e))

    def _log_event(self, event: Event):
        """Log event to storage"""
        try:
            events = self.storage.get("events:log", [])
            events.append({
                "name": event.name,
                "data": event.data,
                "timestamp": datetime.now().isoformat()
            })
            self.storage.set("events:log", events[-1000:])
        except Exception as e:
            self.logger.error("Error logging event: %s", str(e)) 
