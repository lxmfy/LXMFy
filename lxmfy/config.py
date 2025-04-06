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
    cogs_enabled: bool = True
    permissions_enabled: bool = False
    storage_type: str = "json"
    storage_path: str = "data"
    first_message_enabled: bool = True
    event_logging_enabled: bool = True
    max_logged_events: int = 1000
    event_middleware_enabled: bool = True
    announce_enabled: bool = True

    def __post_init__(self):
        if self.admins is None:
            self.admins = set()

    def __str__(self):
        return f"BotConfig(name={self.name}, announce={self.announce}, announce_immediately={self.announce_immediately}, admins={self.admins}, hot_reloading={self.hot_reloading}, rate_limit={self.rate_limit}, cooldown={self.cooldown}, max_warnings={self.max_warnings}, warning_timeout={self.warning_timeout}, command_prefix={self.command_prefix}, cogs_dir={self.cogs_dir}, cogs_enabled={self.cogs_enabled}, permissions_enabled={self.permissions_enabled}, storage_type={self.storage_type}, storage_path={self.storage_path}, first_message_enabled={self.first_message_enabled}, event_logging_enabled={self.event_logging_enabled}, max_logged_events={self.max_logged_events}, event_middleware_enabled={self.event_middleware_enabled}, announce_enabled={self.announce_enabled})" 