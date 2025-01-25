"""Middleware system for LXMFy.

This module provides a flexible middleware system for processing messages
and events, allowing users to add custom processing logic to the bot's
message handling pipeline.
"""

from typing import Any, Callable, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MiddlewareType(Enum):
    """Types of middleware execution points"""
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    PRE_EVENT = "pre_event"
    POST_EVENT = "post_event"
    REQUEST = "request"
    RESPONSE = "response"

@dataclass
class MiddlewareContext:
    """Context passed through middleware chain"""
    type: MiddlewareType
    data: Any
    metadata: dict = field(default_factory=dict)
    cancelled: bool = False
    
    def cancel(self):
        """Cancel middleware processing"""
        self.cancelled = True

class MiddlewareManager:
    """Manages middleware registration and execution"""
    
    def __init__(self):
        self.middleware: dict[MiddlewareType, List[Callable]] = {
            t: [] for t in MiddlewareType
        }
        self.logger = logging.getLogger(__name__)
        
    def register(self, middleware_type: MiddlewareType, func: Callable):
        """Register a middleware function"""
        self.middleware[middleware_type].append(func)
        
    def remove(self, middleware_type: MiddlewareType, func: Callable):
        """Remove a middleware function"""
        if func in self.middleware[middleware_type]:
            self.middleware[middleware_type].remove(func)
            
    def execute(self, middleware_type: MiddlewareType, data: Any) -> Optional[Any]:
        """Execute middleware chain"""
        try:
            ctx = MiddlewareContext(middleware_type, data)
            
            for mw in self.middleware[middleware_type]:
                try:
                    result = mw(ctx)
                    if result is not None:
                        ctx.data = result
                    if ctx.cancelled:
                        break
                except Exception as e:
                    self.logger.error(f"Error in middleware {mw.__name__}: {str(e)}")
                    
            return None if ctx.cancelled else ctx.data
            
        except Exception as e:
            self.logger.error(f"Error executing middleware chain: {str(e)}")
            return data 