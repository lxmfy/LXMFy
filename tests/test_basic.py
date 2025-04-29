import base64
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from LXMF import LXMessage

from lxmfy.core import BotConfig, LXMFBot
from lxmfy.events import Event, EventManager, EventPriority
from lxmfy.permissions import DefaultPerms, PermissionManager
from lxmfy.storage import (
    JSONStorage,
    SQLiteStorage,
    Storage,
    deserialize_value,
    serialize_value,
)
from lxmfy.validation import (  # Added imports
    ValidationResult,
    format_validation_results,
)


# Mock RNS and LXMF dependencies to avoid network/filesystem interactions during tests
@pytest.fixture(autouse=True)
def mock_rns_lxmf(tmp_path):
    """Mocks RNS, LXMRouter, and basic filesystem operations for tests."""
    # Use tmp_path provided by pytest for isolated test directories
    mock_config_path = tmp_path / "config"
    # We still need the config dir for the identity file
    mock_config_path.mkdir(parents=True, exist_ok=True)
    # Create a dummy identity file to prevent creation attempt
    (mock_config_path / "identity").touch()

    # Removed patch for os.makedirs
    with patch('lxmfy.core.RNS') as mock_rns, \
         patch('lxmfy.core.LXMRouter') as mock_lxmrouter, \
         patch('lxmfy.core.os.remove'): # Keep patch for os.remove if needed

        # Mock RNS Identity
        mock_identity = MagicMock()
        mock_identity.to_file.return_value = None
        # Make sure from_file uses the mock identity path correctly
        # The bot init uses os.path.join(self.config_path, "identity")
        # So we need Identity.from_file to handle that path.
        # Instead of complex mocking, let's just ensure the dummy file exists
        # relative to the *actual* config_path created by the bot later.
        # This is handled by mocking getcwd in the bot fixtures.

        mock_rns.Identity.from_file.return_value = mock_identity # Keep this simple
        mock_rns.Identity.return_value = mock_identity

        # Mock LXMRouter
        mock_router_instance = MagicMock()
        mock_local_delivery_identity = MagicMock()
        mock_local_delivery_identity.hash = b'mock_hash'
        mock_router_instance.register_delivery_identity.return_value = mock_local_delivery_identity
        mock_lxmrouter.return_value = mock_router_instance

        # Mock RNS utils
        mock_rns.log = MagicMock()
        mock_rns.Reticulum = MagicMock()
        mock_rns.prettyhexrep = lambda x: x.hex() if isinstance(x, bytes) else str(x) # Handle non-bytes input

        # os.path.exists and os.path.isfile will now use the real functions
        # interacting with the tmp_path filesystem created by pytest.
        # os.makedirs will also use the real function.

        # We still need to mock getcwd specifically in fixtures where the bot is created
        # to control the base path.

        yield mock_rns, mock_lxmrouter


@pytest.fixture
def default_bot(tmp_path):
    """Fixture for a default LXMFBot instance using tmp_path."""
    mock_cwd = tmp_path / "bot_instance_default"
    mock_cwd.mkdir()
    # Default config uses 'data', relative to CWD
    expected_storage_path = mock_cwd / BotConfig.storage_path
    # Ensure the dummy identity file exists where the bot expects it
    (mock_cwd / "config").mkdir()
    (mock_cwd / "config" / "identity").touch()

    with patch('lxmfy.core.os.getcwd', return_value=str(mock_cwd)):
        # Explicitly pass the absolute storage path
        bot = LXMFBot(storage_path=str(expected_storage_path))
    return bot

@pytest.fixture
def custom_bot(tmp_path):
    """Fixture for an LXMFBot instance with custom settings using tmp_path."""
    mock_cwd = tmp_path / "bot_instance_custom"
    mock_cwd.mkdir()
    custom_db_path = tmp_path / "test_bot.db"
    # Ensure the dummy identity file exists where the bot expects it
    (mock_cwd / "config").mkdir()
    (mock_cwd / "config" / "identity").touch()

    with patch('lxmfy.core.os.getcwd', return_value=str(mock_cwd)):
        bot = LXMFBot(
            storage_type="sqlite",
            storage_path=str(custom_db_path), # Pass absolute path for custom storage
            admins=["admin1_hash", "admin2_hash"],
            command_prefix="!",
            announce_enabled=False
        )
    return bot

def test_default_bot_initialization(default_bot, tmp_path):
    """Test if the bot initializes with default settings."""
    mock_cwd = tmp_path / "bot_instance_default"
    expected_storage_path = mock_cwd / BotConfig.storage_path
    expected_config_path = mock_cwd / "config"
    expected_cogs_path = expected_config_path / "cogs"

    assert isinstance(default_bot, LXMFBot)
    assert isinstance(default_bot.storage, JSONStorage)
    # Check paths are correctly set relative to the mocked CWD
    # Storage path might be absolute or relative depending on how JSONStorage handles it
    # Let's check the resolved path
    assert Path(default_bot.storage.directory).resolve() == expected_storage_path.resolve()
    assert Path(default_bot.config_path).resolve() == expected_config_path.resolve()
    assert Path(default_bot.cogs_dir).resolve() == expected_cogs_path.resolve()
    assert default_bot.admins == set()
    assert default_bot.command_prefix == default_bot.config.command_prefix
    # Verify the cogs directory and init file were created by real os.makedirs/open
    assert expected_cogs_path.is_dir()
    assert (expected_cogs_path / "__init__.py").is_file()

def test_custom_bot_initialization(custom_bot, tmp_path):
    """Test if the bot initializes with custom settings."""
    custom_db_path = tmp_path / "test_bot.db"
    mock_cwd = tmp_path / "bot_instance_custom"
    expected_config_path = mock_cwd / "config"
    expected_cogs_path = expected_config_path / "cogs"

    assert isinstance(custom_bot, LXMFBot)
    assert isinstance(custom_bot.storage, SQLiteStorage)
    # SQLiteStorage expects an absolute path usually
    assert Path(custom_bot.storage.database_path).resolve() == custom_db_path.resolve()
    assert Path(custom_bot.config_path).resolve() == expected_config_path.resolve()
    assert Path(custom_bot.cogs_dir).resolve() == expected_cogs_path.resolve()
    assert custom_bot.admins == {"admin1_hash", "admin2_hash"}
    assert custom_bot.command_prefix == "!"
    assert not custom_bot.announce_enabled
    assert expected_cogs_path.is_dir()
    assert (expected_cogs_path / "__init__.py").is_file()

def test_command_registration(default_bot):
    """Test command registration using the decorator."""
    @default_bot.command(name="testcmd", description="A test command")
    def dummy_command():
        pass

    assert "testcmd" in default_bot.commands
    cmd = default_bot.commands["testcmd"]
    assert cmd.name == "testcmd"
    assert cmd.description == "A test command"
    assert cmd.callback == dummy_command
    assert not cmd.admin_only # Default should be False

def test_admin_command_registration(default_bot):
    """Test admin-only command registration."""
    @default_bot.command(admin_only=True)
    def admin_only_cmd():
        pass

    assert "admin_only_cmd" in default_bot.commands
    cmd = default_bot.commands["admin_only_cmd"]
    assert cmd.name == "admin_only_cmd"
    assert cmd.admin_only

def test_is_admin(custom_bot):
    """Test the is_admin check."""
    assert custom_bot.is_admin("admin1_hash")
    assert custom_bot.is_admin("admin2_hash")
    assert not custom_bot.is_admin("non_admin_hash")

def test_bot_config_post_init():
    """Test that BotConfig initializes admins as a set even if None is passed."""
    config_none = BotConfig(admins=None)
    assert config_none.admins == set()
    config_set = BotConfig(admins={"admin1"})
    assert config_set.admins == {"admin1"}

# Test storage serialization/deserialization
def test_serialize_deserialize_basic():
    """Test basic types serialization and deserialization."""
    data = {
        "string": "test",
        "number": 123,
        "boolean": True,
        "list": [1, "a", None],
        "dict": {"key": "value"}
    }
    serialized = serialize_value(data)
    # Basic types should remain unchanged for JSON compatibility
    assert serialized == data
    deserialized = deserialize_value(serialized)
    assert deserialized == data

def test_serialize_deserialize_complex():
    """Test complex types (bytes, datetime) serialization and deserialization."""
    now = datetime.now()
    data = {
        "bytes_data": b"\x01\x02\x03",
        "datetime_data": now
    }
    serialized = serialize_value(data)
    expected_serialized = {
        "bytes_data": {"__type": "bytes", "data": base64.b64encode(b"\x01\x02\x03").decode()},
        "datetime_data": {"__type": "datetime", "data": now.isoformat()}
    }
    assert serialized == expected_serialized

    deserialized = deserialize_value(serialized)
    assert deserialized == data

def test_serialize_deserialize_nested():
    """Test nested complex types serialization and deserialization."""
    now = datetime.now()
    data = {
        "nested_list": [b"bytes1", now, {"inner_bytes": b"bytes2"}]
    }
    serialized = serialize_value(data)
    deserialized = deserialize_value(serialized)
    assert deserialized == data

# Test EventManager
@pytest.fixture
def event_manager():
    """Fixture for an EventManager instance with mock storage."""
    mock_storage = MagicMock(spec=Storage)
    return EventManager(storage=mock_storage)

def test_event_registration(event_manager):
    """Test registering an event handler."""
    handler_called = False
    def my_handler(event):
        nonlocal handler_called
        handler_called = True

    event_manager.on("test_event")(my_handler)
    assert "test_event" in event_manager.handlers
    assert len(event_manager.handlers["test_event"]) == 1
    assert event_manager.handlers["test_event"][0][1] == my_handler

def test_event_dispatch(event_manager):
    """Test dispatching an event calls the registered handler."""
    handler_calls = []
    def my_handler(event):
        handler_calls.append(event.data)

    event_manager.on("test_event")(my_handler)
    test_data = {"key": "value"}
    event = Event("test_event", data=test_data)
    event_manager.dispatch(event)

    assert len(handler_calls) == 1
    assert handler_calls[0] == test_data

def test_event_dispatch_priority(event_manager):
    """Test event dispatch respects handler priority."""
    call_order = []
    @event_manager.on("priority_event", priority=EventPriority.LOW)
    def low_priority_handler(event):
        call_order.append("low")

    @event_manager.on("priority_event", priority=EventPriority.HIGH)
    def high_priority_handler(event):
        call_order.append("high")

    @event_manager.on("priority_event", priority=EventPriority.NORMAL)
    def normal_priority_handler(event):
        call_order.append("normal")

    event = Event("priority_event")
    event_manager.dispatch(event)

    # Expected order: high -> normal -> low (based on Enum values)
    assert call_order == ["high", "normal", "low"]

def test_event_cancellation(event_manager):
    """Test that a cancelled event stops further handler execution."""
    call_order = []
    @event_manager.on("cancel_event", priority=EventPriority.HIGH)
    def cancelling_handler(event):
        call_order.append("cancelling")
        event.cancel()

    @event_manager.on("cancel_event", priority=EventPriority.LOW)
    def low_priority_handler(event):
        call_order.append("low")

    event = Event("cancel_event")
    event_manager.dispatch(event)

    assert call_order == ["cancelling"] # Low priority should not be called

# Test PermissionManager
@pytest.fixture
def permission_manager():
    """Fixture for a PermissionManager instance with mock storage."""
    mock_storage = MagicMock(spec=Storage)
    mock_storage.get.side_effect = lambda key, default: default # Return default on gets
    manager = PermissionManager(storage=mock_storage, enabled=True)
    # Mock save_data to avoid storage interaction during tests
    manager.save_data = MagicMock()
    return manager

def test_permission_manager_default(permission_manager):
    """Test default permissions for a new user."""
    user = "user_hash"
    assert permission_manager.has_permission(user, DefaultPerms.USE_BOT)
    assert permission_manager.has_permission(user, DefaultPerms.SEND_MESSAGES)
    assert permission_manager.has_permission(user, DefaultPerms.USE_COMMANDS)
    assert not permission_manager.has_permission(user, DefaultPerms.MANAGE_USERS)
    assert not permission_manager.has_permission(user, DefaultPerms.ALL)

def test_permission_manager_assign_admin(permission_manager):
    """Test assigning the admin role and checking permissions."""
    user = "admin_user_hash"
    permission_manager.assign_role(user, "admin")
    assert permission_manager.has_permission(user, DefaultPerms.USE_BOT)
    assert permission_manager.has_permission(user, DefaultPerms.MANAGE_USERS)
    assert permission_manager.has_permission(user, DefaultPerms.ALL)
    assert "admin" in permission_manager.user_roles[user]

def test_permission_manager_create_role(permission_manager):
    """Test creating a custom role and assigning it."""
    user = "custom_role_user"
    custom_perms = DefaultPerms.USE_BOT | DefaultPerms.VIEW_EVENTS
    permission_manager.create_role("viewer", custom_perms)
    permission_manager.assign_role(user, "viewer")

    assert permission_manager.has_permission(user, DefaultPerms.USE_BOT)
    assert permission_manager.has_permission(user, DefaultPerms.VIEW_EVENTS)
    assert not permission_manager.has_permission(user, DefaultPerms.MANAGE_EVENTS)
    assert "viewer" in permission_manager.user_roles[user]

def test_permission_manager_disabled(permission_manager):
    """Test that all permissions are granted when the manager is disabled."""
    user = "any_user"
    permission_manager.enabled = False
    assert permission_manager.has_permission(user, DefaultPerms.MANAGE_USERS)
    assert permission_manager.has_permission(user, DefaultPerms.ALL)

# Test Validation Formatting
def test_format_validation_results():
    """Test the formatting of validation results."""
    results = {
        "config": [
            ValidationResult(False, ["Bad config"], "error"),
            ValidationResult(True, ["Good config"], "info")
        ],
        "best_practices": [
            ValidationResult(False, ["Needs improvement"], "warning")
        ],
        "empty_category": []
    }

    formatted_string = format_validation_results(results)

    assert "=== CONFIG ===" in formatted_string
    assert "❌ Bad config" in formatted_string
    assert "ℹ️ Good config" in formatted_string
    assert "=== BEST_PRACTICES ===" in formatted_string
    assert "⚠️ Needs improvement" in formatted_string
    assert "=== EMPTY_CATEGORY ===" in formatted_string # Should still show empty categories 