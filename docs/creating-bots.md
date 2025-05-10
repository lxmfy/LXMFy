# Creating LXMFy Bots

This guide covers various ways to create and customize LXMFy bots.

## Basic Structure

A minimal LXMFy bot involves:

1.  Importing `LXMFBot`.
2.  Instantiating `LXMFBot` with desired configuration.
3.  Defining commands or event handlers.
4.  Running the bot using `bot.run()`.

```python
from lxmfy import LXMFBot

# 1. Instantiate the bot
bot = LXMFBot(
    name="SimpleBot",
    command_prefix="!",
    storage_path="simple_data"
)

# 2. Define commands
@bot.command(name="ping", description="Responds with pong")
def ping_command(ctx):
    # ctx is a context object containing message info
    # ctx.sender: Sender's LXMF hash
    # ctx.content: Full message content
    # ctx.args: List of arguments after the command
    # ctx.reply(message): Function to send a reply
    #   (can also take keyword arguments like title="My Title", lxmf_fields=some_fields)
    ctx.reply("Pong!")

@bot.command(name="greet", description="Greets the user")
def greet_command(ctx):
    if ctx.args:
        name = " ".join(ctx.args)
        ctx.reply(f"Hello, {name}!")
    else:
        ctx.reply("Hello there! Tell me your name: !greet <your_name>")

# 3. Run the bot
if __name__ == "__main__":
    print(f"Starting bot: {bot.config.name}")
    print(f"Bot LXMF Address: {bot.local.hash}")
    bot.run()
```

## Using Templates

LXMFy provides several templates for common bot types. You can use the CLI to generate a bot file based on a template.

```bash
# Create an echo bot
lxmfy create --template echo my_echo_bot

# Create a reminder bot (uses SQLite storage)
lxmfy create --template reminder my_reminder_bot

# Create a note-taking bot (uses JSON storage)
lxmfy create --template note my_note_bot

# Create a meme bot (fetches memes from an API)
lxmfy create --template meme my_meme_bot
```

Running these commands creates a Python file (e.g., `my_echo_bot.py`) that imports and runs the chosen template. You can then modify the generated file or the template code itself (`lxmfy/templates/...`).

**Example generated file (`my_meme_bot.py`):**
```python
from lxmfy.templates import MemeBot

if __name__ == "__main__":
    bot = MemeBot() # Creates an instance of the MemeBot template
    # You can optionally override the default name:
    # bot.bot.name = "My Awesome Meme Bot"
    bot.run()
```

## Bot Configuration

When creating an `LXMFBot` instance, you can pass various keyword arguments to configure its behavior. See the `BotConfig` section in the [API Reference](./api.md) or the [Quick Start Guide](./quick-start.md) for a list of common options.

```python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="ConfiguredBot",
    announce=3600, # Announce every hour
    admins={"your_admin_hash_here"}, # Set admin user(s)
    command_prefix="$", # Use '$' as prefix
    storage_type="sqlite", # Use SQLite database
    storage_path="data/my_bot_data.db", # Specify DB file path
    rate_limit=10, # Allow 10 messages / minute
    cooldown=30, # Cooldown of 30 seconds
    permissions_enabled=True # Enable role-based permissions
)

if __name__ == "__main__":
    # You can also modify config after instantiation
    # Note: some settings are best set during init
    bot.config.max_warnings = 5
    bot.spam_protection.config.max_warnings = 5 # Update spam protector too

    bot.run()
```

### Setting a Bot Icon (LXMF Field)

You can give your bot a custom icon that appears in compatible LXMF clients. This uses the `LXMF.FIELD_ICON_APPEARANCE` and can be set when sending messages.

First, ensure you have the necessary imports:
```python
from lxmfy import IconAppearance, pack_icon_appearance_field
```

Then, you can define and use the icon:
```python
# In your bot class or setup
icon_data = IconAppearance(
    icon_name="robot_2",  # Choose from Material Symbols
    fg_color=b'\x00\xFF\x00',  # Green
    bg_color=b'\x33\x33\x33'   # Dark Grey
)
self.bot_icon_field = pack_icon_appearance_field(icon_data)

# When sending a message or replying:
ctx.reply("Message from your bot!", lxmf_fields=self.bot_icon_field)
# or
# bot.send(destination, "Another message", lxmf_fields=self.bot_icon_field)
```
This `self.bot_icon_field` can be pre-calculated and reused for all messages sent by the bot.

## Using Cogs (Extensions)

Cogs allow you to organize your commands and event listeners into separate files (modules), keeping your main bot file cleaner.

1.  **Create a `cogs` directory** (or whatever you set `cogs_dir` to in `BotConfig`).
2.  **Create Python files** inside the `cogs` directory (e.g., `utility.py`).
3.  **Define a class** that inherits from `lxmfy.Cog` (optional but good practice) or is just a standard class.
4.  **Define commands** as methods within the class using the `@Command` decorator.
5.  **Create a `setup(bot)` function** in the cog file, which LXMFy will call to register the cog.

**Example (`cogs/utility.py`):**
```python
from lxmfy import Command, Cog # Import Cog if inheriting
import time

class UtilityCog: # Or class UtilityCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @Command(name="uptime", description="Shows bot uptime")
    # Note: Methods in cogs often take 'self' and 'ctx'
    def uptime_command(self, ctx):
        uptime_seconds = time.time() - self.start_time
        ctx.reply(f"Bot has been running for {uptime_seconds:.2f} seconds.")

    @Command(name="info", description="Shows bot info")
    def info_command(self, ctx):
        info = (
            f"Bot Name: {self.bot.config.name}\n"
            f"Owner(s): {', '.join(self.bot.config.admins) or 'None'}\n"
            f"Prefix: {self.bot.config.command_prefix}"
        )
        ctx.reply(info)

# This function is required for the cog to be loaded
def setup(bot):
    cog_instance = UtilityCog(bot)
    bot.add_cog(cog_instance) # Register the cog instance with the bot
```

**Main Bot File (`my_bot.py`):**
```python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="CogBot",
    cogs_enabled=True, # Make sure cogs are enabled (default)
    cogs_dir="cogs" # Point to the directory
)

if __name__ == "__main__":
    # Cogs are loaded automatically during LXMFBot initialization
    # if cogs_enabled is True.
    bot.run()
```

When the bot starts, it will automatically find `utility.py`, call its `setup` function, which creates an instance of `UtilityCog` and registers it using `bot.add_cog()`. The commands defined in the cog (`uptime`, `info`) will then be available.

## Handling Events

You can register handlers for various bot events using the `@bot.events.on()` decorator.

```python
from lxmfy import LXMFBot
from lxmfy.events import EventPriority # Optional for priority

bot = LXMFBot(name="EventBot")

@bot.events.on("message_received")
def log_message(event):
    # Event object contains details
    sender = event.data.get("sender")
    message_content = event.data.get("message").content.decode('utf-8', errors='ignore')
    print(f"Received message from {sender}: {message_content}")

    # You can cancel event processing (e.g., stop message handling)
    # if sender == "some_blocked_hash":
    #    event.cancel()

@bot.events.on("command_executed", priority=EventPriority.LOW)
def log_command(event):
    # Example: event.data might contain {'command_name': 'ping', 'sender': '...', ...}
    command_name = event.data.get('command_name', 'unknown')
    sender = event.data.get('sender', 'unknown')
    print(f"Command '{command_name}' executed by {sender}")

# You can define custom events too
@bot.command(name="special")
def special_command(ctx):
    ctx.reply("Doing something special!")
    # Dispatch a custom event
    bot.events.dispatch(Event("special_action_taken", data={"user": ctx.sender}))

@bot.events.on("special_action_taken")
def handle_special(event):
    user = event.data.get("user")
    print(f"Special action was taken by user: {user}")


if __name__ == "__main__":
    bot.run()

```

See `lxmfy/events.py` for more details on the `Event` structure and priorities.

## Storage

LXMFy provides JSON and SQLite storage backends.

*   **JSON:** Simple, human-readable. Good for small datasets. Configure with `storage_type="json"` and `storage_path="your_data_dir"`.
*   **SQLite:** More efficient for larger datasets or frequent writes. Configure with `storage_type="sqlite"` and `storage_path="your_db_file.db"`.

You can access the storage interface via `bot.storage`:

```python
# Save data
bot.storage.set("user_prefs:" + ctx.sender, {"theme": "dark"})

# Get data (with a default value)
prefs = bot.storage.get("user_prefs:" + ctx.sender, {})
theme = prefs.get("theme", "light")

# Check if data exists
if bot.storage.exists("some_key"):
    print("Key exists!")

# Delete data
bot.storage.delete("old_data_key")

# Scan for keys with a prefix (useful for listing user data)
user_keys = bot.storage.scan("user_prefs:")
for key in user_keys:
    user_data = bot.storage.get(key)
    print(f"Data for {key}: {user_data}")
```

See `lxmfy/storage.py` and the API reference for more details.

## Permissions

LXMFy includes an optional role-based permission system. Enable it with `permissions_enabled=True` during `LXMFBot` initialization.

*   **Roles:** Define roles with specific permissions (e.g., `DefaultPerms.MANAGE_USERS`).
*   **Permissions:** Granular flags defined in `DefaultPerms` (e.g., `USE_COMMANDS`, `BYPASS_SPAM`).
*   **Assignment:** Assign roles to user hashes.

See `lxmfy/permissions.py`, the API reference, and potentially example cogs (if any are created) for usage details. 