"""LXMFy - A bot framework for creating LXMF bots on the Reticulum Network.

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
from .signatures import (
    FIELD_SIGNATURE,
    SignatureManager,
    sign_outgoing_message,
    verify_incoming_message,
)
from .storage import JSONStorage, SQLiteStorage, Storage
from .validation import format_validation_results, validate_bot
from .voice import VoiceCallManager

__all__ = [
    "FIELD_SIGNATURE",
    "Attachment",
    "AttachmentType",
    "BotConfig",
    "Command",
    "DefaultPerms",
    "Event",
    "EventManager",
    "EventPriority",
    "HelpFormatter",
    "HelpSystem",
    "IconAppearance",
    "JSONStorage",
    "LXMFBot",
    "MiddlewareContext",
    "MiddlewareManager",
    "MiddlewareType",
    "PermissionManager",
    "Role",
    "SQLiteStorage",
    "ScheduledTask",
    "SignatureManager",
    "Storage",
    "TaskScheduler",
    "VoiceCallManager",
    "__version__",
    "command",
    "format_validation_results",
    "load_cogs_from_directory",
    "pack_attachment",
    "pack_icon_appearance_field",
    "sign_outgoing_message",
    "validate_bot",
    "verify_incoming_message",
]

from .__version__ import __version__
