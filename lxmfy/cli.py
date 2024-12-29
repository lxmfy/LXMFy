"""
CLI module for LXMFy bot framework.

This module provides command-line interface functionality for creating and managing
LXMF bots, including bot file creation and example cog generation.
"""

import os
import argparse
import sys
import re
import json
import hashlib
from pathlib import Path
from glob import glob


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


def verify_wheel_signature(whl_path: str, sigstore_path: str) -> bool:
    """
    Verify the signature of a wheel file.

    Args:
        whl_path: Path to the wheel file
        sigstore_path: Path to the sigstore file

    Returns:
        bool: True if the signature is valid, False otherwise
    """
    try:
        with open(sigstore_path, "r") as f:
            sigstore_data = json.load(f)

        with open(whl_path, "rb") as f:
            whl_content = f.read()
            whl_hash = hashlib.sha256(whl_content).hexdigest()

        if "hash" not in sigstore_data:
            print(f"Error: No hash found in {sigstore_path}")
            return False

        if whl_hash != sigstore_data["hash"]:
            print(f"Hash verification failed!")
            print(f"Wheel hash: {whl_hash}")
            print(f"Sigstore hash: {sigstore_data['hash']}")
            return False

        print("✓ Signature verification successful!")
        return True

    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False


def find_latest_wheel():
    wheels = glob("*.whl")
    if not wheels:
        return None
    return sorted(wheels)[-1]


def create_from_template(template_name: str, output_path: str, bot_name: str) -> str:
    """
    Create a bot from a template.

    Args:
        template_name: Name of the template to use
        output_path: Desired output path
        bot_name: Name for the bot

    Returns:
        str: Path to created bot file

    Raises:
        ValueError: If template is invalid
    """
    templates = {
        "basic": create_bot_file,
        "full": create_full_bot,
    }

    if template_name not in templates:
        raise ValueError(
            f"Invalid template: {template_name}. Available templates: {', '.join(templates.keys())}"
        )

    return templates[template_name](bot_name, output_path)


def create_full_bot(name: str, output_path: str) -> str:
    """Create a full-featured bot with storage and admin commands."""
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

        template = f"""from lxmfy.templates import FullBot

if __name__ == "__main__":
    bot = FullBot()
    bot.bot.name = "{name}"  # Set custom name
    bot.run()
"""
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(template)

        return os.path.relpath(safe_path)

    except Exception as e:
        raise RuntimeError(f"Failed to create full bot: {str(e)}") from e


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LXMFy Bot Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lxmfy create                          # Create basic bot in current directory
  lxmfy create mybot                    # Create basic bot with name 'mybot'
  lxmfy create --template full mybot    # Create full-featured bot
  lxmfy verify                          # Verify latest wheel in current directory
  lxmfy verify package.whl sigstore.json # Verify specific wheel and signature
        """,
    )

    parser.add_argument(
        "command",
        choices=["create", "verify"],
        help="Create a new LXMF bot or verify wheel signature",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name of the bot or path to wheel file (optional)",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Output directory or path to sigstore file (optional)",
    )
    parser.add_argument(
        "--template",
        choices=["basic", "full"],
        default="basic",
        help="Bot template to use (default: basic)",
    )
    parser.add_argument(
        "--name",
        dest="name_opt",
        default=None,
        help="Name of the bot (alphanumeric, spaces, dash, underscore)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path or directory",
    )

    args = parser.parse_args()

    if args.command == "create":
        try:
            bot_name = args.name_opt or args.name or "MyLXMFBot"

            if args.output:
                output_path = args.output
            elif args.directory:
                output_path = os.path.join(args.directory, "bot.py")
            elif args.name:
                output_path = f"{args.name}.py"
            else:
                output_path = "bot.py"

            bot_path = create_from_template(args.template, output_path, bot_name)

            # Only create example cog for basic template
            if args.template == "basic":
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
            else:
                print(
                    f"""
✨ Successfully created new LXMFy bot!

Files created:
  - {bot_path} (main bot file)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
                """
                )
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "verify":
        whl_path = args.name
        sigstore_path = args.directory

        if not whl_path:
            whl_path = find_latest_wheel()
            if not whl_path:
                print("Error: No wheel files found in current directory")
                sys.exit(1)

        if not sigstore_path:
            sigstore_path = "sigstore.json"

        if not os.path.exists(whl_path):
            print(f"Error: Wheel file not found: {whl_path}")
            sys.exit(1)

        if not os.path.exists(sigstore_path):
            print(f"Error: Sigstore file not found: {sigstore_path}")
            sys.exit(1)

        if not verify_wheel_signature(whl_path, sigstore_path):
            sys.exit(1)


if __name__ == "__main__":
    main()
