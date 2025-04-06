"""
CLI module for LXMFy bot framework.

This module provides command-line interface functionality for creating and managing
LXMF bots, including bot file creation, example cog generation, and bot analysis.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from glob import glob

from .templates import EchoBot, NoteBot, ReminderBot
from .validation import format_validation_results, validate_bot


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
    Validate and sanitize bot name.

    Args:
        name: Proposed bot name

    Returns:
        str: Sanitized bot name

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError("Bot name cannot be empty")

    # Remove invalid characters
    sanitized = "".join(c for c in name if c.isalnum() or c in " -_")
    if not sanitized:
        raise ValueError("Bot name must contain valid characters")

    return sanitized


def create_bot_file(name: str, output_path: str) -> str:
    """
    Create a new bot file from template.

    Args:
        name: Name for the bot
        output_path: Desired output path

    Returns:
        str: Path to created bot file

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
    announce=600,  # Announce every 600 seconds (10 minutes), set to 0 to disable periodic announces
    announce_enabled=True,  # Set to False to disable all announces (both initial and periodic)
    announce_immediately=True,  # Set to False to disable initial announce
    admins=[],  # Add your LXMF hashes here
    hot_reloading=True,
    command_prefix="/",
    first_message_enabled=True,
)

# Load all cogs from the cogs directory
load_cogs_from_directory(bot)

@bot.on_first_message()
def welcome_message(sender, message):
    bot.send(sender, "Welcome to the bot! Type /help to see available commands.")
    return True

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
        with open(sigstore_path) as f:
            sigstore_data = json.load(f)

        with open(whl_path, "rb") as f:
            whl_content = f.read()
            whl_hash = hashlib.sha256(whl_content).hexdigest()

        if "hash" not in sigstore_data:
            print(f"Error: No hash found in {sigstore_path}")
            return False

        if whl_hash != sigstore_data["hash"]:
            print("Hash verification failed!")
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
    try:
        name = validate_bot_name(bot_name)
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        if output_path.endswith("/") or output_path.endswith("\\"):
            base_name = "bot.py"
            output_path = os.path.join(output_path, base_name)
        elif not output_path.endswith(".py"):
            output_path += ".py"

        safe_path = os.path.abspath(output_path)

        if template_name == "basic":
            return create_bot_file(name, safe_path)
        
        template_map = {
            "echo": EchoBot,
            "reminder": ReminderBot,
            "note": NoteBot
        }

        if template_name not in template_map:
            raise ValueError(
                f"Invalid template: {template_name}. Available templates: basic, {', '.join(template_map.keys())}"
            )

        template = f"""from lxmfy.templates import {template_map[template_name].__name__}

if __name__ == "__main__":
    bot = {template_map[template_name].__name__}()
    bot.bot.name = "{name}"  # Set custom name
    bot.run()
"""
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(template)

        return os.path.relpath(safe_path)

    except Exception as e:
        raise RuntimeError(f"Failed to create bot from template: {str(e)}") from e


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


def analyze_bot_file(file_path: str) -> None:
    """
    Analyze a bot file for configuration issues and best practices.

    Args:
        file_path: Path to the bot file to analyze
    """
    try:
        # Load the bot module
        spec = importlib.util.spec_from_file_location("bot_module", file_path)
        if not spec or not spec.loader:
            raise ImportError("Could not load bot file")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the bot instance
        bot = None
        for attr in dir(module):
            obj = getattr(module, attr)
            if hasattr(obj, '__class__') and 'LXMFBot' in str(obj.__class__):
                bot = obj
                break
            elif hasattr(obj, 'bot') and hasattr(obj.bot, '__class__') and 'LXMFBot' in str(obj.bot.__class__):
                bot = obj.bot
                break

        if not bot:
            print("Error: No LXMFBot instance found in the file")
            return

        # Run validation
        results = validate_bot(bot)
        print("\n=== Bot Analysis Results ===")
        print(format_validation_results(results))

    except Exception as e:
        print(f"Error analyzing bot file: {str(e)}")
        return


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LXMFy Bot Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Creating Bots
  lxmfy create                          # Create basic bot file 'bot.py'
  lxmfy create mybot                    # Create basic bot file 'mybot.py'
  lxmfy create --template echo mybot    # Create echo bot file 'mybot.py'
  lxmfy create --template reminder bot  # Create reminder bot file 'bot.py'
  lxmfy create --template note notes    # Create note-taking bot file 'notes.py'

  # Running Template Bots Directly
  lxmfy run echo                        # Run the built-in echo bot
  lxmfy run reminder --name "MyReminder"  # Run the reminder bot with a custom name
  lxmfy run note                        # Run the built-in note bot

  # Analyzing and Verifying
  lxmfy analyze bot.py                  # Analyze bot configuration
  lxmfy verify                          # Verify latest wheel in current directory
  lxmfy verify package.whl sigstore.json # Verify specific wheel and signature
        """,
    )

    parser.add_argument(
        "command",
        choices=["create", "verify", "analyze", "run"],
        help="Create a bot file, verify signature, analyze config, or run a template bot",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name for 'create' (bot name/path), 'analyze' (file path), 'verify' (wheel path), or 'run' (template name: echo, reminder, note)",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Output directory for 'create', or sigstore path for 'verify' (optional)",
    )
    parser.add_argument(
        "--template",
        choices=["basic", "echo", "reminder", "note"],
        default="basic",
        help="Bot template to use for 'create' command (default: basic)",
    )
    parser.add_argument(
        "--name",
        dest="name_opt",
        default=None,
        help="Optional custom name for the bot (used with 'create' or 'run')",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path or directory for 'create' command",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        if not args.name:
            print("Error: Please specify a bot file to analyze")
            sys.exit(1)
        
        bot_path = args.name
        if not os.path.exists(bot_path):
            print(f"Error: Bot file not found: {bot_path}")
            sys.exit(1)
            
        analyze_bot_file(bot_path)
        
    elif args.command == "create":
        try:
            bot_name = args.name_opt or args.name or "MyLXMFBot"

            if args.output:
                output_path = args.output
            elif args.directory:
                output_path = os.path.join(args.directory, "bot.py")
            elif args.name:
                # Handle case where name might be intended as filename
                if '.' in args.name:
                     output_path = args.name
                     # Attempt to extract a bot name if none was provided via --name
                     if not args.name_opt:
                         bot_name = os.path.splitext(os.path.basename(args.name))[0]
                else:
                    output_path = f"{args.name}.py"

            else:
                output_path = "bot.py"

            # Ensure bot_name is valid if extracted from filename
            try:
                bot_name = validate_bot_name(bot_name)
            except ValueError as ve:
                print(f"Error: Invalid bot name '{bot_name}'. {ve}", file=sys.stderr)
                sys.exit(1)

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
            print(f"Error creating bot: {str(e)}", file=sys.stderr)
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

    elif args.command == "run":
        template_name = args.name
        if not template_name:
            print("Error: Please specify a template name to run (echo, reminder, note)")
            sys.exit(1)

        template_map = {
            "echo": EchoBot,
            "reminder": ReminderBot,
            "note": NoteBot
        }

        if template_name not in template_map:
             print(f"Error: Invalid template name '{template_name}'. Choose from: echo, reminder, note")
             sys.exit(1)

        try:
            BotClass = template_map[template_name]
            print(f"Starting {template_name} bot...")
            bot_instance = BotClass() # Instantiate the template class

            # Set custom name if provided
            custom_name = args.name_opt
            if custom_name:
                 try:
                     validated_name = validate_bot_name(custom_name)
                     # Templates might wrap the actual bot, check for .bot attribute
                     if hasattr(bot_instance, 'bot'):
                         bot_instance.bot.config.name = validated_name
                         bot_instance.bot.name = validated_name # Also update potential direct attribute if exists
                     else:
                         bot_instance.config.name = validated_name # Assume direct config if no .bot
                         bot_instance.name = validated_name # Also update potential direct attribute if exists
                     print(f"Running with custom name: {validated_name}")
                 except ValueError as ve:
                     print(f"Warning: Invalid custom name '{custom_name}' provided. Using default. ({ve})")

            bot_instance.run() # Call run on the instance

        except Exception as e:
            print(f"Error running template bot '{template_name}': {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
