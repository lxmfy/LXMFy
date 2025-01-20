"""
LXMFy - A bot framework for creating LXMF bots on the Reticulum Network.

This package provides tools and utilities for creating and managing LXMF bots,
including command handling, storage management, moderation features, and role-based permissions.
"""

from .core import LXMFBot
from .storage import Storage, JSONStorage, SQLiteStorage
from .commands import Command, command
from .cogs_core import load_cogs_from_directory
from .help import HelpSystem, HelpFormatter
from .permissions import DefaultPerms, Role, PermissionManager
from .validation import validate_bot, format_validation_results
from .config import BotConfig
from .events import Event, EventManager, EventPriority

__all__ = [
    "LXMFBot",
    "Storage",
    "JSONStorage",
    "SQLiteStorage",
    "Command",
    "command",
    "load_cogs_from_directory",
    "HelpSystem",
    "HelpFormatter",
    "DefaultPerms",
    "Role",
    "PermissionManager",
    "validate_bot",
    "format_validation_results",
    "BotConfig",
    "Event",
    "EventManager",
    "EventPriority",
]
