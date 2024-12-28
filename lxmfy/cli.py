"""
CLI module for LXMFy bot framework.

This module provides command-line interface functionality for creating and managing
LXMF bots, including bot file creation and example cog generation.
"""

import os
import argparse
import sys
import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename while preserving the extension.

    Args:
        filename: The filename to sanitize

    Returns:
        str: Sanitized filename with proper extension
    """
    base, ext = os.path.splitext(os.path.basename(filename))

    base = re.sub(r"[^a-zA-Z0-9\-_]", "", base)

    if not ext or ext != ".py":
        ext = ".py"

    return f"{base}{ext}"


def validate_bot_name(name: str) -> str:
    """
    Validate bot name to ensure it's safe.

    Args:
        name: The bot name to validate

    Returns:
        str: The validated bot name

    Raises:
        ValueError: If the bot name is invalid
    """
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9 \-_]*$", name):
        raise ValueError(
            "Bot name must start with alphanumeric character and can only contain "
            "alphanumeric characters, spaces, dashes, and underscores"
        )
    return name


def create_bot_file(name: str, output_path: str) -> str:
    """
    Create the bot file with validated inputs.

    Args:
        name: Name of the bot
        output_path: Desired output path and filename

    Returns:
        str: The actual filename used

    Raises:
        RuntimeError: If file creation fails
    """
    try:
        name = validate_bot_name(name)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        if output_path.endswith("/") or output_path.endswith("\\"):
            base_name = "bot.py"
            output_path = os.path.join(output_path, base_name)
        elif not output_path.endswith(".py"):
            output_path += ".py"

        safe_path = os.path.abspath(output_path)

        template = f"""from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="{name}",
    announce=600,  # Announce every 600 seconds (10 minutes)
    admins=[],  # Add your LXMF hashes here
    hot_reloading=True,
    command_prefix="/",
    # Moderation settings
    rate_limit=5,      # 5 messages per minute
    cooldown=5,        # 5 seconds cooldown
    max_warnings=3,    # 3 warnings before ban
    warning_timeout=300,  # Warnings reset after 5 minutes
)

# Load all cogs from the cogs directory
load_cogs_from_directory(bot)

@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")

if __name__ == "__main__":
    bot.run()
"""
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(template)

        return os.path.relpath(safe_path)

    except Exception as e:
        raise RuntimeError(f"Failed to create bot file: {str(e)}") from e


def create_example_cog(bot_path: str) -> None:
    """
    Create example cog and necessary directory structure.

    Args:
        bot_path: Path to the bot file to determine cogs location
    """
    try:
        bot_dir = os.path.dirname(os.path.abspath(bot_path))
        cogs_dir = os.path.join(bot_dir, "cogs")
        os.makedirs(cogs_dir, exist_ok=True)

        init_path = os.path.join(cogs_dir, "__init__.py")
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("")

        template = """from lxmfy import Command

class BasicCommands:
    def __init__(self, bot):
        self.bot = bot
    
    @Command(name="hello", description="Says hello")
    async def hello(self, ctx):
        ctx.reply(f"Hello {ctx.sender}!")
    
    @Command(name="about", description="About this bot")
    async def about(self, ctx):
        ctx.reply("I'm a bot created with LXMFy!")

def setup(bot):
    bot.add_cog(BasicCommands(bot))
"""
        basic_path = os.path.join(cogs_dir, "basic.py")
        with open(basic_path, "w", encoding="utf-8") as f:
            f.write(template)

    except Exception as e:
        raise RuntimeError(f"Failed to create example cog: {str(e)}") from e


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LXMFy Bot Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lxmfy create                          # Create bot in current directory
  lxmfy create --name "My Cool Bot"     # Create bot with custom name
  lxmfy create --output path/to/bot.py  # Create bot in specific location
  lxmfy create --output path/to/dir/    # Create bot in directory
        """,
    )

    parser.add_argument("command", choices=["create"], help="Create a new LXMF bot")
    parser.add_argument(
        "--name",
        default="MyLXMFBot",
        help="Name of the bot (alphanumeric, spaces, dash, underscore)",
    )
    parser.add_argument(
        "--output", default="bot.py", help="Output file path or directory"
    )

    args = parser.parse_args()

    if args.command == "create":
        try:
            bot_path = create_bot_file(args.name, args.output)
            create_example_cog(bot_path)
            print(
                f"""
✨ Successfully created new LXMFy bot!

Files created:
  - {bot_path} (main bot file)
  - {os.path.join(os.path.dirname(bot_path), 'cogs')}
    - __init__.py
    - basic.py (example cog)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
            """
            )
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
