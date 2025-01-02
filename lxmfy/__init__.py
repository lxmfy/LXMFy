"""
LXMFy - A bot framework for creating LXMF bots on the Reticulum Network.

This package provides tools and utilities for creating and managing LXMF bots,
including command handling, storage management, moderation features, and role-based permissions.
"""

from .core import LXMFBot
from .storage import Storage, JSONStorage
from .commands import Command, command
from .cogs_core import load_cogs_from_directory
from .help import HelpSystem, HelpFormatter
from .permissions import DefaultPerms, Role, PermissionManager

__all__ = [
    "LXMFBot",
    "Storage",
    "JSONStorage",
    "Command",
    "command",
    "load_cogs_from_directory",
    "HelpSystem",
    "HelpFormatter",
    "DefaultPerms",
    "Role",
    "PermissionManager",
]
