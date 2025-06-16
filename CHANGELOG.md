# Changelog

## [0.7.3] - 2025-05-15

- **Update LXMF to 0.7.1**
- **Update RNS to 0.9.6**

## [0.7.2] - 2025-05-13

- **Update LXMF to 0.7.0**
- **Update dependencies**
- **Python 3.13 now required**

## [0.7.1] - 2025-05-09

- **Fixed workflow**

## [0.7.0] - 2025-05-09

- **Add LXMF fields support**
- **Update dependencies**
- **Update docs**

## [0.6.9] - 2025-05-07

- **Add opencontainers metadata**
- **Remove bot Scan (AST)**
- **Remove bot verification**
- **Update dependencies**
- **Performance fixes (Ruff PERF)**
- **cog loading validation and error handling**

## [0.6.8] - 2025-04-29

- **Update setup.py package name**
- **Add Dockerfile.Build**
- **CLI: Colors and Interactive**

## [0.6.7] - 2025-04-29

- **Fix Workflow**

## [0.6.6] - 2025-04-29

- **Fix Basic Tests**
- **Docstrings**
- **Code Cleanup**
- **Meme Bot Template**
- **Update dependencies**
- **Add ARMv7 and ARM64 Builds**
- **Remove Bandit**
- **Remove Meme Bot (Meme API no longer working)**
- **Remove Requests (Meme Bot dependency)**

## [0.6.5] - 2025-04-07

- **Fix Attachment System**
- **Add more storage error handling**

## [0.6.4] - 2025-04-06

- **Code refactoring for security and performance**

## [0.6.3] - 2025-04-06

- **Fix syntax errors**
- **Manual publish workflow**
- **Update Poetry.lock**

## [0.6.0] - 2025-04-06

- **Update lxmf to 0.6.3**
- **Update rns to 0.9.3**
- **Add docker-compose.yml file**
- **Run bot templates directly: lxmfy run echo**
- **Add basic tests**
- Fix linting errors
- **Add LXMF Attachment Support**

## [0.5.1] - 2025-02-14

- **Remove unused variables**
- **Fix version**

## [0.5.0] - 2025-02-14

- **Update config, cli and core**
  - Add missing values
  - Fix announce system

## [0.4.9] - 2025-02-14
- **Fix Announce System**
  - Add ability to disable announces on start.
  - Fix announcing interval

Bot configuration:

```python
    announce=600,  # Set the announce interval in seconds, set to 0 to disable periodic announces
    announce_enabled=True,  # Set to False to disable all announces (both initial and periodic)
```

- **Fix Duplicate Responses**

- **Update Dependencies**
  - Update LXMF from `0.6.1` to `0.6.2`
  - Regenerate poetry.lock

## [0.4.8] - 2025-01-25
- **Fix Storage System**
  - Serialization errors
  - SQLite3 Storage Backend

## [0.4.7] - 2025-01-25
- **Fix Storage System**
  - Serialization errors
  
- **Fix Event System**
  - Event handling of some attributes

## [0.4.6] - 2025-01-25

### Major Features
- **Middleware System**
  - Middleware system for processing messages and events
  - MiddlewareManager class for managing middleware
  - MiddlewareType enum for middleware types
  - MiddlewareContext class for passing data through middleware

- **Task Scheduler**
  - Task scheduler for scheduling tasks
  - TaskScheduler class for managing tasks
  - ScheduledTask class for representing scheduled tasks

- **Update lxmf to 0.6.1**

```python
from lxmfy import LXMFBot, MiddlewareType, TaskScheduler

bot = LXMFBot(name="MyBot")

# Add middleware
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def log_commands(ctx):
    print(f"Command received: {ctx.data}")
    return ctx.data

# Schedule task
@bot.scheduler.schedule("cleanup", "0 */2 * * *")  # Every 2 hours
def cleanup_task():
    print("Running cleanup...")
```

## [0.4.5] - 2025-01-20

### Major Features
- **Event System**
  - Event system for handling events and middleware
  - EventManager class for managing events and handlers
  - Event class for representing events
  - EventPriority enum for event priority levels
  - EventMiddleware for handling event middleware

```python
@bot.events.on("custom_event")
async def handle_custom_event(event):
    print(f"Custom event received: {event.data}")

# Dispatch custom event
await bot.events.dispatch(Event("custom_event", {"foo": "bar"}))
```

- **Update rns and lxmf**

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
[0.4.5]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.5
[0.4.6]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.6
[0.4.7]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.7
[0.4.8]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.8
[0.4.9]: https://github.com/lxmfy/lxmfy/releases/tag/v0.4.9
[0.5.0]: https://github.com/lxmfy/lxmfy/releases/tag/v0.5.0
[0.5.1]: https://github.com/lxmfy/lxmfy/releases/tag/v0.5.1
[0.6.0]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.0
[0.6.3]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.3
[0.6.4]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.4
[0.6.5]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.5
[0.6.6]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.6
[0.6.7]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.7
[0.6.8]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.8
[0.6.9]: https://github.com/lxmfy/lxmfy/releases/tag/v0.6.9
[0.7.0]: https://github.com/lxmfy/lxmfy/releases/tag/v0.7.0
[0.7.1]: https://github.com/lxmfy/lxmfy/releases/tag/v0.7.1
[0.7.2]: https://github.com/lxmfy/lxmfy/releases/tag/v0.7.2
[0.7.3]: https://github.com/lxmfy/lxmfy/releases/tag/v0.7.3