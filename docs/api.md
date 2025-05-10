# LXMFy API Documentation

LXMFy is a bot framework for creating LXMF bots on the Reticulum Network. This document provides comprehensive API documentation for the framework's core components and features.

## Core Components

### LXMFBot

The main bot class that handles message routing, command processing, and bot lifecycle management.

```python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="MyBot",
    announce=600,
    announce_immediately=True,
    admins=set(),
    hot_reloading=False,
    rate_limit=5,
    cooldown=60,
    max_warnings=3,
    warning_timeout=300,
    command_prefix="/",
    cogs_dir="cogs",
    cogs_enabled=True,
    permissions_enabled=False,
    storage_type="json",
    storage_path="data",
    first_message_enabled=True,
    event_logging_enabled=True,
    max_logged_events=1000,
    event_middleware_enabled=True,
    announce_enabled=True
)
```

#### Key Methods

- `run(delay=10)`: Start the bot's main loop
- `send(destination, message, title="Reply", lxmf_fields=None)`: Send a message to a destination, optionally with custom LXMF fields.
- `send_with_attachment(destination, message, attachment, title="Reply")`: Send a message with an attachment
- `command(name, description="No description provided", admin_only=False)`: Decorator for registering commands
- `on_first_message()`: Decorator for handling first messages from users
- `validate()`: Run validation checks on the bot configuration

### Storage

The framework provides two storage backends:

#### JSONStorage

```python
from lxmfy import JSONStorage

storage = JSONStorage("data")
```

#### SQLiteStorage

```python
from lxmfy import SQLiteStorage

storage = SQLiteStorage("data/bot.db")
```

### Commands

Command registration and handling:

```python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Events

Event system for handling various bot events:

```python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Handle message event
    pass
```

### Permissions

Permission system for controlling access to bot features:

```python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

### Middleware

Middleware system for processing messages and events:

```python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Process before command execution
    pass
```

### Attachments

Support for sending files, images, and audio:

```python
from lxmfy import Attachment, AttachmentType

attachment = Attachment(
    type=AttachmentType.IMAGE,
    name="image.jpg",
    data=image_data,
    format="jpg"
)
bot.send_with_attachment(destination, "Here's an image", attachment)
```

### Icon Appearance (LXMF Field)

You can set a custom icon for your bot that compliant LXMF clients can display. This uses the `LXMF.FIELD_ICON_APPEARANCE`.

```python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Required for LXMF.FIELD_ICON_APPEARANCE

# Define the icon appearance
icon_data = IconAppearance(
    icon_name="smart_toy",  # Name from Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # White foreground (3 bytes)
    bg_color=b'\x4A\x90\xE2'   # Blue background (3 bytes)
)

# Pack it into the LXMF field format
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Send a message with this icon
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# You can also combine it with other fields, like attachments:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

### Scheduler

Task scheduling system:

```python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Run daily at midnight
    pass
```

## Templates

The framework includes several ready-to-use bot templates:

### EchoBot

Simple echo bot that repeats messages:

```python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

### MemeBot

Bot for sending random memes:

```python
from lxmfy.templates import MemeBot

bot = MemeBot()
bot.run()
```

### NoteBot

Note-taking bot with JSON storage:

```python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

### ReminderBot

Reminder bot with SQLite storage:

```python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## CLI Tools

The framework provides command-line tools for bot management:

```bash
# Create a new bot
lxmfy create mybot

# Create a bot from template
lxmfy create --template echo mybot

# Run a template bot
lxmfy run echo

# Analyze bot configuration
lxmfy analyze bot.py

# Verify package signature
lxmfy verify package.whl sigstore.json
```

## Best Practices

1. Always enable the permission system for better security
2. Use appropriate storage backend based on data size
3. Implement proper error handling in commands
4. Use middleware for cross-cutting concerns
5. Follow the event-driven architecture for extensibility
6. Use the validation system to ensure proper configuration
7. Implement proper spam protection
8. Use the scheduler for periodic tasks
9. Follow the template structure for new bots
10. Use the CLI tools for bot management

## Error Handling

The framework provides comprehensive error handling:

```python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

## Security Considerations

1. Always validate user input
2. Use the permission system
3. Implement rate limiting
4. Use spam protection
5. Validate attachments
6. Use secure storage
7. Implement proper error handling
8. Use the validation system
9. Follow security best practices
10. Keep dependencies updated 