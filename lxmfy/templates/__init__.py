"""
Templates module for LXMFy bot framework.

This module provides ready-to-use bot templates with different feature sets.
"""

from .echo_bot import EchoBot
from .reminder_bot import ReminderBot
from .note_bot import NoteBot

__all__ = ["EchoBot", "ReminderBot", "NoteBot"]
