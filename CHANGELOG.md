# Changelog

## [0.4.4] - 2025-01-17

### Major Features
- **Bot Analysis**
  - Validate bot configuration and best practices
  - Analyze bot file and provide recommendations
  - Validate bot file syntax and structure
  - Check for common issues and suggest improvements

- **Update rns to 0.9.0**

  cli command: `lxmfy analyze bot.py`


## [0.4.3] - 2025-01-04

### Major Features
- **First Message Handler**
- **SQLite3 Storage Backend**
- **Simpler and Better Bot Templates**

Templates Added: EchoBot, ReminderBot, NoteBot
Templates Removed: FullBot

On First Message Handler:

```python

@bot.on_first_message()
def welcome_message(sender, message):
    # Custom welcome message handler
    bot.send(sender, "Welcome to the bot! Type /help to see available commands.")
    return True  # Return True to indicate message was handled
```

SQLite3 Storage Backend:

```python
bot = LXMFBot(
    name="mybot",
    announce=600,  # Announce every 600 seconds (10 minutes)
    admins=[],  # Add your LXMF hashes here
    hot_reloading=True,
    command_prefix="/",
    first_message_enabled=True,
    storage_type="sqlite",
    storage_path="mybot.db",
)
```

## [0.4.2] - 2025-01-01

### Major Features - Non-Breaking to existing bots
- **Permission System**
  - Role-based access control with hierarchical permissions
  - Default and admin role system
  - Custom role creation and management
  - Persistent permission storage
  - Command-specific permission requirements
  - Permission flags: READ, WRITE, EXECUTE, MANAGE
  - Built-in permission sets: USE_BOT, SEND_MESSAGES, USE_COMMANDS, etc.
  - Permission inheritance through roles
  - Permission priority system
  - Integration with existing admin system
  - Permission system can be disabled/enabled

### Code Quality
- **Enhanced Command System**
  - Permission-aware command decorator
  - Improved command metadata
  - Better permission validation
  - Integration with help system for permission display

### Core Features
- **Permission Management**
  - `PermissionManager` class for centralized permission handling
  - Role assignment and removal
  - Permission checking utilities
  - User permission calculation
  - Role persistence and storage

## [0.4.1] - 2024-31-12

### Major Features
- **Help Commands**
  - Detection of existing commands and creates a help command.

## [0.4.0] - 2024-12-29

### Major Features
- **CLI Templates Command**
  - Basic bot template with example cogs
  - Full-featured bot template with storage and admin commands
  - Template selection via CLI: `lxmfy create --template full mybot`

- **CLI Verification Command**
  - Using `lxmfy verify` to verify a .whl file using a sigstore hash.

- **Fix Rate Limiting and Spam Protection**
  - Dont process recieved messages at all if banned.


## [0.3.3] - 2024-12-28

### Major Features
- **Simplified CLI Interface**
  - New streamlined command: `lxmfy create mybot ./mybot`
  - Removed complex flag requirements (`--name`, `--output`)
  - Intuitive directory structure creation

### Code Quality
- **Enhanced Code Quality**
  - Full Pylint compliance
  - Improved type hints
  - Better error handling
  - Consistent code style

### Core Features
- **Transport Layer**
  - Automatic path discovery
  - Link caching and management
  - Request handling system
  - Configurable timeouts
  - Path persistence

- **Storage System**
  - JSON file-based persistence
  - In-memory caching
  - Key-value operations
  - Prefix scanning
  - Custom backend support

### Documentation
- **Comprehensive Documentation**
  - Quick start guide
  - Command creation examples
  - Storage system usage
  - Transport layer integration
  - Moderation tools overview
  - Cog system tutorials
- **Website Updates**
  - Mobile-responsive design (some more improvements to come)
  - Improved code block readability
  - Better navigation structure

### Bug Fixes
- Fixed mobile navigation menu positioning
- Improved code block scrolling on mobile devices
- Enhanced responsive layout for feature cards
- Fixed documentation link accessibility

[0.3.3]: https://github.com/lxmfy/lxmfy/releases/tag/v0.3.3
[0.4.0]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.0
[0.4.1]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.1
[0.4.2]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.2
[0.4.3]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.3
[0.4.4]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.4