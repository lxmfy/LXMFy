# LXMFy

[![Socket Badge](https://socket.dev/api/badge/pypi/package/lxmfy/0.7.3?artifact_id=tar-gz)](https://socket.dev/pypi/package/lxmfy/overview)
[![DeepSource](https://app.deepsource.com/gh/lxmfy/LXMFy.svg/?label=active+issues&show_trend=true&token=H2_dIwKdYo9BgJkKMdhIORRD)](https://app.deepsource.com/gh/lxmfy/LXMFy/)

Easily create LXMF bots for the Reticulum Network with this extensible framework.

## Features

- Spam protection (rate limiting, command cooldown, warnings, banning)
- Command prefix (set to None to process all messages as commands)
- Announcements (announce in seconds, set to 0 to disable)
- Extensible Storage Backend (JSON, SQLite)
- Permission System (Role-based)
- Middleware System
- Task Scheduler (Cron-style)
- Event System
- Help on first message
- LXMF Attachments (File, Image, Audio)
- Customizable Bot Icon (via LXMF Icon Appearance field)

## Installation

```bash
pip install lxmfy
```
or pipx:

```bash
pipx install lxmfy
```

## Usage

```bash
lxmfy create
```

**Python**

```python
from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="LXMFy Test Bot", # Name of the bot that appears on the network.
    announce=600, # Announce every 600 seconds, set to 0 to disable.
    announce_enabled=True, # Set to False to disable all announces (both initial and periodic)
    announce_immediately=True, # Set to False to disable initial announce
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

### Development

```
poetry run ruff check .
poetry run bandit -c pyproject.toml -r .
```

### Docker

```
docker run -d \
    --name lxmfy-test-bot \
    -v $(pwd)/config:/bot/config \
    -v $(pwd)/.reticulum:/root/.reticulum \
    --restart unless-stopped \
    lxmfy-test
```

Auto-Interface support:

```
docker run -d \
    --name lxmfy-test-bot \
    --network host \
    -v $(pwd)/config:/bot/config \
    -v $(pwd)/.reticulum:/root/.reticulum \
    --restart unless-stopped \
    lxmfy-test
```

## Contributing

Pull requests are welcome.

## Donating

Ko-Fi https://ko-fi.com/X8X610E5JL

BTC: bc1qwgwdwj6d0cu50flptt0w8d3p8h2qatvzwjg40k 

Librepay: https://liberapay.com/Sudo-Ivan

## License

MIT