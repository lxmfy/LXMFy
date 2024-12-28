# LXMFy

Easily create LXMF bots for the Reticulum Network with this framework. Very similar to Discord.py.

## Features

- Hot reloading (Cog system)
- Moderation commands (unban, stats, etc.)
- Spam protection (rate limiting, command cooldown, warnings, banning)
- Command prefix (set to None to process all messages as commands)
- Announcements (announce in seconds, set to 0 to disable)
- Extensible Storage Backend

## Installation

```bash
pip install lxmfy
```

## Usage

**CLI Tool**

```bash
lxmfy create
```

**Python**

```python
from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="LXMFy Test Bot", # Name of the bot that appears on the network.
    announce=600, # Announce every 600 seconds, set to 0 to disable.
    admins=["your_lxmf_hash_here"], # List of admin hashes.
    hot_reloading=True, # Enable hot reloading.
    command_prefix="/", # Set to None to process all messages as commands.
    cogs_dir="cogs", # Specify cogs directory name.
    rate_limit=5, # 5 messages per minute
    cooldown=5, # 5 seconds cooldown
    max_warnings=3, # 3 warnings before ban
    warning_timeout=300, # Warnings reset after 5 minutes
)

# Dynamically load all cogs
load_cogs_from_directory(bot)

@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")

# Admin Only Command
@bot.command(name="echo", description="Echo a message", admin_only=True)
def echo(ctx, message: str):
    ctx.reply(message)

bot.run()
```

## Framework Development

```
git clone https://github.com/lxmfy/lxmfy.git
cd lxmfy
poetry install
```

Credit to https://github.com/randogoth/lxmf-bot, helped me learning to create LXMF bots. - Sudo-Ivan
