"""
LXMFy - A bot framework for creating LXMF bots on the Reticulum Network.

This package provides tools and utilities for creating and managing LXMF bots,
including command handling, storage management, moderation features, and role-based permissions.
"""

from .attachments import (
    Attachment,
    AttachmentType,
    IconAppearance,
    pack_attachment,
    pack_icon_appearance_field,
)
from .cogs_core import load_cogs_from_directory
from .commands import Command, command
from .config import BotConfig
from .core import LXMFBot
from .events import Event, EventManager, EventPriority
from .help import HelpFormatter, HelpSystem
from .middleware import MiddlewareContext, MiddlewareManager, MiddlewareType
from .permissions import DefaultPerms, PermissionManager, Role
from .scheduler import ScheduledTask, TaskScheduler
from .storage import JSONStorage, SQLiteStorage, Storage
from .validation import format_validation_results, validate_bot

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
    "MiddlewareManager",
    "MiddlewareType",
    "MiddlewareContext",
    "TaskScheduler",
    "ScheduledTask",
    "Attachment",
    "AttachmentType",
    "pack_attachment",
    "IconAppearance",
    "pack_icon_appearance_field"
]

__version__ = "0.7.4"
