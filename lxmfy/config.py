"""Configuration module for LXMFy."""

from dataclasses import dataclass


@dataclass
class BotConfig:
    """
    Configuration settings for LXMFBot.

    Attributes:
        name (str): The name of the bot. Defaults to "LXMFBot".
        announce (int): The announce interval in seconds. Defaults to 600.
        announce_immediately (bool): Whether to announce immediately on startup. Defaults to True.
        admins (set): A set of admin identity hashes. Defaults to an empty set.
        hot_reloading (bool): Whether to enable hot reloading of cogs. Defaults to False.
        rate_limit (int): The maximum number of messages allowed per cooldown period. Defaults to 5.
        cooldown (int): The cooldown period in seconds. Defaults to 60.
        max_warnings (int): The maximum number of spam warnings before action is taken. Defaults to 3.
        warning_timeout (int): The duration in seconds for which a spam warning is active. Defaults to 300.
        command_prefix (str): The prefix for bot commands. Defaults to "/".
        cogs_dir (str): The directory to load cogs from. Defaults to "cogs".
        cogs_enabled (bool): Whether to enable cogs. Defaults to True.
        permissions_enabled (bool): Whether to enable the permission system. Defaults to False.
        storage_type (str): The type of storage to use ("json" or "sqlite"). Defaults to "json".
        storage_path (str): The path to the storage file or directory. Defaults to "data".
        first_message_enabled (bool): Whether to enable first message handling. Defaults to True.
        event_logging_enabled (bool): Whether to enable event logging. Defaults to True.
        max_logged_events (int): The maximum number of events to log. Defaults to 1000.
        event_middleware_enabled (bool): Whether to enable event middleware. Defaults to True.
	announce_enabled (bool): Whether to enable bot announcements. Defaults to True.
    """

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
        """Post-initialization to ensure admins is a set."""
        if self.admins is None:
            self.admins = set()

    def __str__(self):
        """Return a string representation of the BotConfig object."""
        return f"BotConfig(name={self.name}, announce={self.announce}, announce_immediately={self.announce_immediately}, admins={self.admins}, hot_reloading={self.hot_reloading}, rate_limit={self.rate_limit}, cooldown={self.cooldown}, max_warnings={self.max_warnings}, warning_timeout={self.warning_timeout}, command_prefix={self.command_prefix}, cogs_dir={self.cogs_dir}, cogs_enabled={self.cogs_enabled}, permissions_enabled={self.permissions_enabled}, storage_type={self.storage_type}, storage_path={self.storage_path}, first_message_enabled={self.first_message_enabled}, event_logging_enabled={self.event_logging_enabled}, max_logged_events={self.max_logged_events}, event_middleware_enabled={self.event_middleware_enabled}, announce_enabled={self.announce_enabled})"
