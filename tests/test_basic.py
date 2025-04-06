import pytest
import os
from pathlib import Path
from datetime import datetime
import base64
from lxmfy.core import LXMFBot, BotConfig
from lxmfy.storage import Storage, JSONStorage, SQLiteStorage, serialize_value, deserialize_value
from lxmfy.attachments import Attachment, AttachmentType, pack_attachment
from lxmfy.events import EventManager, Event, EventPriority
from lxmfy.permissions import PermissionManager, DefaultPerms
from lxmfy.moderation import SpamProtection # Added imports
from lxmfy.validation import ValidationResult, format_validation_results # Added imports
from LXMF import LXMessage
from unittest.mock import patch, MagicMock

# Mock RNS and LXMF dependencies to avoid network/filesystem interactions during tests
@pytest.fixture(autouse=True)
def mock_rns_lxmf():
    with patch('lxmfy.core.RNS') as mock_rns, \
         patch('lxmfy.core.LXMRouter') as mock_lxmrouter:
        
        # Mock RNS Identity
        mock_identity = MagicMock()
        mock_identity.to_file.return_value = None
        mock_rns.Identity.from_file.return_value = mock_identity
        mock_rns.Identity.return_value = mock_identity # For new identity creation

        # Mock LXMRouter and related calls
        mock_router_instance = MagicMock()
        mock_local_delivery_identity = MagicMock()
        mock_local_delivery_identity.hash = b'mock_hash'
        mock_router_instance.register_delivery_identity.return_value = mock_local_delivery_identity
        mock_router_instance.register_delivery_callback.return_value = None
        mock_lxmrouter.return_value = mock_router_instance
        
        # Mock RNS logging and Reticulum instance if needed
        mock_rns.log = MagicMock()
        mock_rns.Reticulum = MagicMock()
        mock_rns.prettyhexrep = lambda x: x.hex() # Simple hex representation

        # Mock os.makedirs and os.path.exists to simulate filesystem
        with patch('lxmfy.core.os.makedirs') as mock_makedirs, \
             patch('lxmfy.core.os.path.exists') as mock_exists, \
             patch('lxmfy.core.os.path.isfile') as mock_isfile, \
             patch('lxmfy.core.open', MagicMock()), \
             patch('lxmfy.core.os.remove'): # Mock file removal for announce_immediately

            mock_exists.return_value = True # Assume paths/files exist by default
            mock_isfile.return_value = True # Assume identity file exists
            yield mock_rns, mock_lxmrouter


@pytest.fixture
def default_bot():
    """Fixture for a default LXMFBot instance."""
    mock_cwd = '/tmp/lxmfy_test'
    # Explicitly construct the absolute path for the default 'data' directory
    # based on the default config value 'data' and the mocked CWD.
    default_storage_dir_name = BotConfig.storage_path # Get default from class
    absolute_storage_path = os.path.join(mock_cwd, default_storage_dir_name)
    with patch('lxmfy.core.os.getcwd', return_value=mock_cwd):
        # Pass the absolute path to the constructor to ensure JSONStorage gets it
        # This also overrides the path stored in this specific bot.config instance
        bot = LXMFBot(storage_path=absolute_storage_path)
    return bot

@pytest.fixture
def custom_bot():
    """Fixture for an LXMFBot instance with custom settings."""
    with patch('lxmfy.core.os.getcwd', return_value='/tmp/lxmfy_test'):
        bot = LXMFBot(
            storage_type="sqlite", 
            storage_path="/tmp/test_bot.db",
            admins=["admin1_hash", "admin2_hash"],
            command_prefix="!",
            announce_enabled=False
        )
    return bot

def test_default_bot_initialization(default_bot):
    """Test if the bot initializes with default settings."""
    mock_cwd = '/tmp/lxmfy_test'
    expected_absolute_path = Path(os.path.join(mock_cwd, BotConfig.storage_path))

    assert isinstance(default_bot, LXMFBot)
    assert isinstance(default_bot.storage.backend, JSONStorage)
    # Check that the bot's config instance reflects the path we passed
    assert default_bot.config.storage_path == str(expected_absolute_path) 
    # Check the actual directory used by JSONStorage
    assert default_bot.storage.backend.directory == expected_absolute_path
    assert default_bot.admins == set() # Default admins should be empty initially from config defaults
    assert default_bot.command_prefix == default_bot.config.command_prefix # Check default prefix

def test_custom_bot_initialization(custom_bot):
    """Test if the bot initializes with custom settings."""
    assert isinstance(custom_bot, LXMFBot)
    assert isinstance(custom_bot.storage.backend, SQLiteStorage)
    assert custom_bot.config.storage_path == "/tmp/test_bot.db"
    assert custom_bot.admins == {"admin1_hash", "admin2_hash"}
    assert custom_bot.command_prefix == "!"
    assert not custom_bot.announce_enabled

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

def test_pack_file_attachment():
    """Test packing a file attachment."""
    att = Attachment(type=AttachmentType.FILE, name="test.txt", data=b"hello")
    packed = pack_attachment(att)
    assert LXMessage.FIELD_FILE_ATTACHMENTS in packed
    assert packed[LXMessage.FIELD_FILE_ATTACHMENTS] == [["test.txt", b"hello"]]

def test_pack_image_attachment():
    """Test packing an image attachment."""
    att = Attachment(type=AttachmentType.IMAGE, name="", data=b"imagedata", format="png")
    packed = pack_attachment(att)
    assert LXMessage.FIELD_IMAGE in packed
    assert packed[LXMessage.FIELD_IMAGE] == ["png", b"imagedata"]

def test_pack_audio_attachment():
    """Test packing an audio attachment."""
    att = Attachment(type=AttachmentType.AUDIO, name="", data=b"audiodata", format="1") # Format as mode
    packed = pack_attachment(att)
    assert LXMessage.FIELD_AUDIO in packed
    assert packed[LXMessage.FIELD_AUDIO] == [1, b"audiodata"]

def test_pack_unsupported_attachment():
    """Test packing an unsupported attachment type raises ValueError."""
    att = Attachment(type=999, name="test", data=b"data") # Invalid type
    with pytest.raises(ValueError):
        pack_attachment(att)

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

# Test SpamProtection
@pytest.fixture
def spam_protection():
    """Fixture for SpamProtection with mock storage, bot, and permissions."""
    mock_storage = MagicMock(spec=Storage)
    # Return specific empty defaults for keys loaded by SpamProtection
    def mock_get_side_effect(key, default=None):
        if key == "spam:message_counts":
            return default or {}
        if key == "spam:warnings":
            return default or {}
        if key == "spam:banned_users":
            return default or []
        if key == "spam:warning_times":
            return default or {}
        return default
    mock_storage.get.side_effect = mock_get_side_effect
    
    mock_bot = MagicMock(spec=LXMFBot)
    mock_permission_manager = MagicMock(spec=PermissionManager)
    mock_permission_manager.has_permission.return_value = False # Default: no bypass
    mock_bot.permissions = mock_permission_manager
    
    # Use small, testable config values
    config_overrides = {
        "rate_limit": 2, 
        "cooldown": 10,
        "max_warnings": 1,
        "warning_timeout": 20
    }
    sp = SpamProtection(storage=mock_storage, bot=mock_bot, **config_overrides)
    sp.save_data = MagicMock() # Mock save_data
    return sp, mock_permission_manager

@patch('lxmfy.moderation.time')
def test_spam_protection_allow(mock_time_func, spam_protection):
    """Test that messages within the rate limit are allowed."""
    sp, _ = spam_protection
    sender = "user1"
    mock_time_func.return_value = 100.0 # Set return value directly on the mocked function
    allowed1, msg1 = sp.check_spam(sender)
    mock_time_func.return_value = 101.0
    allowed2, msg2 = sp.check_spam(sender)
    
    assert allowed1
    assert msg1 is None
    assert allowed2
    assert msg2 is None
    assert len(sp.message_counts[sender]) == 2

@patch('lxmfy.moderation.time')
def test_spam_protection_rate_limit_exceeded(mock_time_func, spam_protection):
    """Test that exceeding the rate limit triggers a warning."""
    sp, _ = spam_protection
    sender = "user2"
    # Send 2 allowed messages
    mock_time_func.return_value = 100.0
    sp.check_spam(sender)
    mock_time_func.return_value = 101.0
    sp.check_spam(sender)
    
    # Third message should exceed limit
    mock_time_func.return_value = 102.0
    allowed, msg = sp.check_spam(sender)
    
    assert not allowed
    assert "Rate limit exceeded" in msg
    assert "Warning 1/1" in msg # max_warnings is 1 in fixture
    assert sp.warnings[sender] == 1

@patch('lxmfy.moderation.time')
def test_spam_protection_ban(mock_time_func, spam_protection):
    """Test that exceeding max warnings results in a ban."""
    sp, _ = spam_protection
    sender = "user3"
    # Exceed rate limit once (1 warning)
    mock_time_func.return_value = 100.0; sp.check_spam(sender)
    mock_time_func.return_value = 101.0; sp.check_spam(sender)
    mock_time_func.return_value = 102.0; sp.check_spam(sender) # Warning 1
    assert sp.warnings[sender] == 1
    assert sender not in sp.banned_users
    
    # Exceed rate limit again (ban)
    # Need to advance time past cooldown to allow messages again before triggering next warning
    mock_time_func.return_value = 115.0; sp.check_spam(sender)
    mock_time_func.return_value = 116.0; sp.check_spam(sender)
    mock_time_func.return_value = 117.0 
    allowed, msg = sp.check_spam(sender) # Ban

    assert not allowed
    assert "banned for spamming" in msg
    assert sender in sp.banned_users

@patch('lxmfy.moderation.time')
def test_spam_protection_bypass(mock_time_func, spam_protection):
    """Test that users with bypass permission are not rate limited."""
    sp, mock_perms = spam_protection
    sender = "bypass_user"
    mock_perms.has_permission.return_value = True # User has bypass permission
    
    mock_time_func.return_value = 100.0
    # Send multiple messages quickly
    for i in range(5):
        allowed, msg = sp.check_spam(sender)
        assert allowed
        assert msg is None
    
    assert sp.warnings[sender] == 0
    assert sender not in sp.banned_users
    # Check that has_permission was called with the correct permission
    mock_perms.has_permission.assert_called_with(sender, DefaultPerms.BYPASS_SPAM)

@patch('lxmfy.moderation.time')
def test_spam_protection_warning_timeout(mock_time_func, spam_protection):
    """Test that warnings reset after the timeout."""
    sp, _ = spam_protection
    sender = "user4"
    # Trigger a warning
    mock_time_func.return_value = 100.0; sp.check_spam(sender)
    mock_time_func.return_value = 101.0; sp.check_spam(sender)
    mock_time_func.return_value = 102.0; allowed, msg = sp.check_spam(sender) # Warning 1
    assert sp.warnings[sender] == 1
    
    # Advance time past warning_timeout (20s in fixture)
    mock_time_func.return_value = 130.0
    # Send allowed messages again
    allowed1, msg1 = sp.check_spam(sender)
    allowed2, msg2 = sp.check_spam(sender)
    assert allowed1
    assert allowed2
    # Warning count should have reset to 0 before these messages
    assert sp.warnings[sender] == 0
    # Trigger another warning - it should be warning 1 again
    allowed3, msg3 = sp.check_spam(sender)
    assert not allowed3
    assert "Warning 1/1" in msg3
    assert sp.warnings[sender] == 1

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