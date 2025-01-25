"""Event system module for LXMFy.

This module provides a comprehensive event handling system including:
- Custom event creation and dispatching
- Event middleware support
- Event logging and monitoring
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List
from enum import Enum
import logging
from datetime import datetime

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
            # Sort handlers by priority
            self.handlers[event_name].sort(key=lambda x: x[0].value)
            return func
        return decorator
        
    def use(self, middleware: Callable):
        """Add middleware to the event pipeline"""
        # This method is no longer used in the new implementation
        pass
        
    def dispatch(self, event: Event):
        """Dispatch an event to registered handlers"""
        try:
            if event.name in self.handlers:
                for priority, handler in self.handlers[event.name]:
                    if event.cancelled:
                        break
                    try:
                        handler(event)
                    except Exception as e:
                        self.logger.error(f"Error in event handler {handler.__name__}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error dispatching event: {str(e)}")
            
    def _log_event(self, event: Event):
        """Log event to storage"""
        try:
            if not self.storage:
                return
                
            events = self.storage.get("events:log", [])
            events.append({
                "name": event.name,
                "timestamp": event.timestamp.timestamp(),
                "cancelled": event.cancelled,
                "data": event.data
            })
            self.storage.set("events:log", events[-1000:])  # Keep last 1000 events
        except Exception as e:
            self.logger.error(f"Error logging event: {str(e)}") 