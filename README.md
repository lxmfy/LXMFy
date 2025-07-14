# LXMFy

[![Socket Badge](https://socket.dev/api/badge/pypi/package/lxmfy/0.7.6?artifact_id=tar-gz)](https://socket.dev/pypi/package/lxmfy/overview)
[![DeepSource](https://app.deepsource.com/gh/lxmfy/LXMFy.svg/?label=active+issues&show_trend=true&token=H2_dIwKdYo9BgJkKMdhIORRD)](https://app.deepsource.com/gh/lxmfy/LXMFy/)
[![Build Test](https://github.com/lxmfy/LXMFy/actions/workflows/build-test.yml/badge.svg)](https://github.com/lxmfy/LXMFy/actions/workflows/build-test.yml)
[![Publish Python distribution to PyPI](https://github.com/lxmfy/LXMFy/actions/workflows/publish.yml/badge.svg)](https://github.com/lxmfy/LXMFy/actions/workflows/publish.yml)
[![Safety](https://github.com/lxmfy/LXMFy/actions/workflows/safety.yml/badge.svg)](https://github.com/lxmfy/LXMFy/actions/workflows/safety.yml)

Easily create LXMF bots for the Reticulum Network with this extensible framework.

[Docs](https://lxmfy.quad4.io) | [Road to V1](https://plane.quad4.io/spaces/issues/43d0b80cfd864a1b94025b175d1fdf64)

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
- Threading support for commands.

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

## Docker

To build the Docker image, navigate to the root of the project and run:

```bash
docker build -t lxmfy-test .
```

Once built, you can run the Docker image:

```
docker run -d \
    --name lxmfy-test-bot \
    -v $(pwd)/config:/bot/config \
    -v $(pwd)/.reticulum:/root/.reticulum \
    --restart unless-stopped \
    lxmfy-test
```

Auto-Interface support (network host):

```
docker run -d \
    --name lxmfy-test-bot \
    --network host \
    -v $(pwd)/config:/bot/config \
    -v $(pwd)/.reticulum:/root/.reticulum \
    --restart unless-stopped \
    lxmfy-test
```

### Building Wheels with Dockerfile.Build

The `Dockerfile.Build` is used to build the `lxmfy` Python package into a wheel file within a Docker image.

```bash
docker build -f Dockerfile.Build -t lxmfy-wheel-builder .
```

This will create an image named `lxmfy-wheel-builder`. To extract the built wheel file from the image, you can run a container from this image and copy the `dist` directory:

```bash
docker run --rm -v "$(pwd)/dist_output:/output" lxmfy-wheel-builder
```

This command will create a `dist_output` directory in your current working directory and copy the built wheel file into it.

## Example

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

## Development

- poetry
- python 3.11 or higher

```
poetry install
poetry run lxmfy run echo
```

## Contributing

Pull requests are welcome.

## Part of Quad4

LXMFy is a [Quad4](https://github.com/Quad4-Software) project.

## License

[MIT](LICENSE)
