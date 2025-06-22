"""CLI module for LXMFy bot framework.

Provides an interactive and colorful command-line interface for creating and managing LXMF bots,
including bot file creation and example cog generation.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from .templates import CogTestBot, EchoBot, NoteBot, ReminderBot
from .validation import validate_bot


# Custom colors for CLI
class Colors:
    """Custom color codes for CLI output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header with custom styling."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(50)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 50}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message with custom styling."""
    print(f"{Colors.GREEN}{Colors.BOLD}✓ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message with custom styling."""
    print(f"{Colors.RED}{Colors.BOLD}✗ {text}{Colors.ENDC}")

def print_info(text: str) -> None:
    """Print an info message with custom styling."""
    print(f"{Colors.BLUE}{Colors.BOLD}ℹ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message with custom styling."""
    print(f"{Colors.YELLOW}{Colors.BOLD}⚠ {text}{Colors.ENDC}")

def print_menu() -> None:
    """Print the interactive menu."""
    print_header("LXMFy Bot Framework")
    print(f"{Colors.CYAN}Available Commands:{Colors.ENDC}")
    print(f"{Colors.BOLD}1.{Colors.ENDC} Create a new bot")
    print(f"{Colors.BOLD}2.{Colors.ENDC} Run a template bot")
    print(f"{Colors.BOLD}3.{Colors.ENDC} Exit")
    print()

def get_user_choice() -> str:
    """Get user's choice from the menu."""
    while True:
        choice = input(f"{Colors.CYAN}Enter your choice (1-3): {Colors.ENDC}")
        if choice in ['1', '2', '3']:
            return choice
        print_error("Invalid choice. Please enter a number between 1 and 3.")

def get_bot_name() -> str:
    """Get bot name from user input."""
    while True:
        name = input(f"{Colors.CYAN}Enter bot name: {Colors.ENDC}")
        try:
            return validate_bot_name(name)
        except ValueError as ve:
            print_error(f"Invalid bot name: {ve}")

def get_template_choice() -> str:
    """Get template choice from user input."""
    templates = ["basic", "echo", "reminder", "note", "cogtest"]
    print(f"\n{Colors.CYAN}Available templates:{Colors.ENDC}")
    for i, template in enumerate(templates, 1):
        print(f"{Colors.BOLD}{i}.{Colors.ENDC} {template}")

    while True:
        choice = input(f"\n{Colors.CYAN}Select template (1-5): {Colors.ENDC}")
        if choice in ['1', '2', '3', '4', '5']:
            return templates[int(choice) - 1]
        print_error("Invalid choice. Please enter a number between 1 and 5.")

def interactive_create() -> None:
    """Interactive bot creation process."""
    print_header("Create New Bot")
    bot_name = get_bot_name()
    template = get_template_choice()

    output_path = input(f"{Colors.CYAN}Enter output path (default: {bot_name}.py): {Colors.ENDC}") or f"{bot_name}.py"

    try:
        bot_path = create_from_template(template, output_path, bot_name)
        if template == "basic":
            create_example_cog(bot_path)
            print_success("Bot created successfully!")
            print_info(f"""
Files created:
  - {bot_path} (main bot file)
  - {os.path.join(os.path.dirname(bot_path), 'cogs')}
    - __init__.py
    - basic.py (example cog)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
            """)
        else:
            print_success("Bot created successfully!")
            print_info(f"""
Files created:
  - {bot_path} (main bot file)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
            """)
    except Exception as e:
        print_error(f"Error creating bot: {str(e)}")

def interactive_run() -> None:
    """Interactive bot running process."""
    print_header("Run Template Bot")
    template = get_template_choice()

    custom_name = input(f"{Colors.CYAN}Enter custom name (optional): {Colors.ENDC}")
    if custom_name:
        try:
            custom_name = validate_bot_name(custom_name)
        except ValueError as ve:
            print_warning(f"Invalid custom name provided. Using default. ({ve})")
            custom_name = None

    try:
        template_map = {
            "echo": EchoBot,
            "reminder": ReminderBot,
            "note": NoteBot,
            "cogtest": CogTestBot
        }

        BotClass = template_map[template]
        print_header(f"Starting {template} Bot")
        bot_instance = BotClass()

        if custom_name:
            if hasattr(bot_instance, 'bot'):
                bot_instance.bot.config.name = custom_name
                bot_instance.bot.name = custom_name
            else:
                bot_instance.config.name = custom_name
                bot_instance.name = custom_name
            print_info(f"Running with custom name: {custom_name}")

        bot_instance.run()
    except Exception as e:
        print_error(f"Error running template bot: {str(e)}")

def interactive_mode() -> None:
    """Run the CLI in interactive mode."""
    while True:
        print_menu()
        choice = get_user_choice()

        if choice == '1':
            interactive_create()
        elif choice == '2':
            interactive_run()
        elif choice == '3':
            print_success("Goodbye!")
            sys.exit(0)

        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

def sanitize_filename(filename: str) -> str:
    """Sanitizes the filename while preserving the extension.

    Args:
        filename: The filename to sanitize.

    Returns:
        Sanitized filename with proper extension.
    """
    base, ext = os.path.splitext(os.path.basename(filename))
    base = re.sub(r"[^a-zA-Z0-9\-_]", "", base)

    if not ext or ext != ".py":
        ext = ".py"

    return f"{base}{ext}"

def validate_bot_name(name: str) -> str:
    """Validates and sanitizes a bot name.

    Args:
        name: The proposed bot name.

    Returns:
        The sanitized bot name.

    Raises:
        ValueError: If the name is invalid.
    """
    if not name:
        raise ValueError("Bot name cannot be empty")

    sanitized = "".join(c for c in name if c.isalnum() or c in " -_")
    if not sanitized:
        raise ValueError("Bot name must contain valid characters")

    return sanitized

def create_bot_file(name: str, output_path: str, no_cogs: bool = False) -> str:
    """Creates a new bot file from a template.

    Args:
        name: The name for the bot.
        output_path: The desired output path.
        no_cogs: Whether to disable cogs loading.

    Returns:
        The path to the created bot file.

    Raises:
        RuntimeError: If file creation fails.
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

        template = f"""from lxmfy import LXMFBot

bot = LXMFBot(
    name="{name}",
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
    cogs_enabled={not no_cogs},
    permissions_enabled=False,
    storage_type="json",
    storage_path="data",
    first_message_enabled=True,
    event_logging_enabled=True,
    max_logged_events=1000,
    event_middleware_enabled=True,
    announce_enabled=True
)

if __name__ == "__main__":
    bot.run()
"""
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(template)

        return os.path.relpath(safe_path)

    except Exception as e:
        raise RuntimeError(f"Failed to create bot file: {str(e)}") from e

def create_example_cog(bot_path: str) -> None:
    """Creates an example cog and the necessary directory structure.

    Args:
        bot_path: The path to the bot file to determine the cogs location.
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

def create_from_template(template_name: str, output_path: str, bot_name: str) -> str:
    """Creates a bot from a template.

    Args:
        template_name: The name of the template to use.
        output_path: The desired output path.
        bot_name: The name for the bot.

    Returns:
        The path to the created bot file.

    Raises:
        ValueError: If the template is invalid.
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
            "note": NoteBot,
            "cogtest": CogTestBot
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

def is_safe_path(path: str, base_path: str = None) -> bool:
    """Checks if a path is safe and within the allowed directory.

    Args:
        path: The path to check.
        base_path: The base path to check against. If None, all paths are considered safe.

    Returns:
        True if the path is safe, False otherwise.
    """
    try:
        if base_path:
            base_path = os.path.abspath(base_path)
            path = os.path.abspath(path)
            return path.startswith(base_path)
        return True
    except Exception:
        return False

def main() -> None:
    """Main CLI entry point."""
    try:
        if len(sys.argv) == 1:
            interactive_mode()
            return

        print_header("LXMFy Bot Framework")

        parser = argparse.ArgumentParser(
            description="LXMFy Bot Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  lxmfy create                          # Create basic bot file 'bot.py'
  lxmfy create mybot                    # Create basic bot file 'mybot.py'
  lxmfy create --template echo mybot    # Create echo bot file 'mybot.py'
  lxmfy create --template reminder bot  # Create reminder bot file 'bot.py'
  lxmfy create --template note notes    # Create note-taking bot file 'notes.py'
  lxmfy create --template cogtest test  # Create cog test bot file 'test.py'

  lxmfy run echo                        # Run the built-in echo bot
  lxmfy run reminder --name "MyReminder"  # Run the reminder bot with a custom name
  lxmfy run note                        # Run the built-in note bot
  lxmfy run cogtest                     # Run the cog test bot
            """,
        )

        parser.add_argument(
            "command",
            choices=["create", "run"],
            help="Create a bot file or run a template bot",
        )
        parser.add_argument(
            "name",
            nargs="?",
            default=None,
            help="Name for 'create' (bot name/path) or 'run' (template name: echo, reminder, note)",
        )
        parser.add_argument(
            "directory",
            nargs="?",
            default=None,
            help="Output directory for 'create' command (optional)",
        )
        parser.add_argument(
            "--template",
            choices=["basic", "echo", "reminder", "note", "cogtest"],
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
        parser.add_argument(
            "--no-cogs",
            action="store_true",
            help="Disable cogs loading for 'create' command",
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
                    if '.' in args.name:
                         output_path = args.name
                         if not args.name_opt:
                             bot_name = os.path.splitext(os.path.basename(args.name))[0]
                    else:
                        output_path = f"{args.name}.py"
                else:
                    output_path = "bot.py"

                try:
                    bot_name = validate_bot_name(bot_name)
                except ValueError as ve:
                    print_error(f"Invalid bot name '{bot_name}'. {ve}")
                    sys.exit(1)

                print_header("Creating New Bot")
                bot_path = create_from_template(args.template, output_path, bot_name)

                if args.template == "basic":
                    create_example_cog(bot_path)
                    print_success("Bot created successfully!")
                    print_info(f"""
Files created:
  - {bot_path} (main bot file)
  - {os.path.join(os.path.dirname(bot_path), 'cogs')}
    - __init__.py
    - basic.py (example cog)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
                    """)
                else:
                    print_success("Bot created successfully!")
                    print_info(f"""
Files created:
  - {bot_path} (main bot file)

To start your bot:
  python {bot_path}

To add admin rights, edit {bot_path} and add your LXMF hash to the admins list.
                    """)
            except Exception as e:
                print_error(f"Error creating bot: {str(e)}")
                sys.exit(1)

        elif args.command == "run":
            template_name = args.name
            if not template_name:
                print_error("Please specify a template name to run (echo, reminder, note, cogtest)")
                sys.exit(1)

            template_map = {
                "echo": EchoBot,
                "reminder": ReminderBot,
                "note": NoteBot,
                "cogtest": CogTestBot
            }

            if template_name not in template_map:
                 print_error(f"Invalid template name '{template_name}'. Choose from: {', '.join(template_map.keys())}")
                 sys.exit(1)

            try:
                BotClass = template_map[template_name]
                print_header(f"Starting {template_name} Bot")
                bot_instance = BotClass()

                custom_name = args.name_opt
                if custom_name:
                     try:
                         validated_name = validate_bot_name(custom_name)
                         if hasattr(bot_instance, 'bot'):
                             bot_instance.bot.config.name = validated_name
                             bot_instance.bot.name = validated_name
                         else:
                             bot_instance.config.name = validated_name
                             bot_instance.name = validated_name
                         print_info(f"Running with custom name: {validated_name}")
                     except ValueError as ve:
                         print_warning(f"Invalid custom name '{custom_name}' provided. Using default. ({ve})")

                bot_instance.run()

            except Exception as e:
                print_error(f"Error running template bot '{template_name}': {str(e)}")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
