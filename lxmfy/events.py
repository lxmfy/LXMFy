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
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    MONITOR = 5

@dataclass
class Event:
    """Base event class"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def cancel(self):
        """Cancel the event"""
        self.cancelled = True

@dataclass
class EventHandler:
    """Event handler container"""
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    middleware: List[Callable] = field(default_factory=list)

class EventManager:
    """Manages event registration, dispatching and middleware"""
    
    def __init__(self, storage=None):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.middleware: List[Callable] = []
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
    def on(self, event_name: str, priority: EventPriority = EventPriority.NORMAL):
        """Decorator to register an event handler"""
        def decorator(func):
            self.register_handler(event_name, func, priority)
            return func
        return decorator
        
    def register_handler(self, event_name: str, callback: Callable, 
                        priority: EventPriority = EventPriority.NORMAL):
        """Register an event handler"""
        if event_name not in self.handlers:
            self.handlers[event_name] = []
            
        handler = EventHandler(callback=callback, priority=priority)
        self.handlers[event_name].append(handler)
        
        # Sort handlers by priority
        self.handlers[event_name].sort(key=lambda h: h.priority.value, reverse=True)
        
    def use(self, middleware: Callable):
        """Add middleware to the event pipeline"""
        self.middleware.append(middleware)
        
    def dispatch(self, event: Event) -> Event:
        """Dispatch an event through middleware and to handlers"""
        try:
            # Run through middleware
            for mw in self.middleware:
                event = mw(event)
                if event.cancelled:
                    return event
                    
            if event.name in self.handlers:
                for handler in self.handlers[event.name]:
                    try:
                        # Run handler middleware
                        for mw in handler.middleware:
                            event = mw(event)
                            if event.cancelled:
                                return event
                                
                        # Execute handler
                        handler.callback(event)
                        if event.cancelled:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error in event handler: {str(e)}")
                        
            # Log event if storage is configured
            if self.storage:
                self._log_event(event)
                
            return event
            
        except Exception as e:
            self.logger.error(f"Error dispatching event: {str(e)}")
            raise
            
    def _log_event(self, event: Event):
        """Log event to storage"""
        try:
            events = self.storage.get("events:log", [])
            events.append({
                "name": event.name,
                "timestamp": event.timestamp.isoformat(),
                "cancelled": event.cancelled,
                "data": event.data
            })
            self.storage.set("events:log", events[-1000:])  # Keep last 1000 events
        except Exception as e:
            self.logger.error(f"Error logging event: {str(e)}") 