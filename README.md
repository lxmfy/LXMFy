# LXMF-Bot-Framework

Easily create LXMF bots with this framework. Very similar to Discord.py.

## Features

- Hot reloading (Cog system)
- Moderation commands (unban, stats, etc.)
- Spam protection (rate limiting, command cooldown, warnings, banning)
- Command prefix (set to None to process all messages as commands)
- Announcements (announce every X seconds, set to 0 to disable)

## Installation

```bash
pip install git+https://github.com/Sudo-Ivan/LXMFy.git
```

or Poetry:

```bash
poetry add git+https://github.com/Sudo-Ivan/LXMFy.git
```

## Usage

```python
from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="LXMFy Test Bot", # Name of the bot that appears on the network.
    announce=600, # Announce every 600 seconds, set to 0 to disable.
    admins=["your_lxmf_hash_here"], # List of admin hashes.
    hot_reloading=True # Enable hot reloading.
)

@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")

@

bot.run()
```

Credit to https://github.com/randogoth/lxmf-bot, helped me learning to create LXMF bots.
