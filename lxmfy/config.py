"""Configuration module for LXMFy."""

from dataclasses import dataclass

@dataclass
class BotConfig:
    """Configuration settings for LXMFBot."""

    name: str = "LXMFBot"
    announce: int = 600
    announce_immediately: bool = True
    admins: set = None
    hot_reloading: bool = False
    rate_limit: int = 5
    cooldown: int = 60
    max_warnings: int = 3
    warning_timeout: int = 300
    command_prefix: str = "/"
    cogs_dir: str = "cogs"
    permissions_enabled: bool = False
    storage_type: str = "json"
    storage_path: str = "data"
    first_message_enabled: bool = True 