"""CLI module for LXMFy bot framework.

Provides an interactive and colorful command-line interface for creating and managing LXMF bots,
including bot file creation, example cog generation, and bot analysis.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
from glob import glob
from pathlib import Path
from typing import Any, Optional

from .templates import EchoBot, NoteBot, ReminderBot
from .validation import format_validation_results, validate_bot

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
    print(f"{Colors.BOLD}3.{Colors.ENDC} Analyze a bot")
    print(f"{Colors.BOLD}4.{Colors.ENDC} Verify wheel signature")
    print(f"{Colors.BOLD}5.{Colors.ENDC} Exit")
    print()

def get_user_choice() -> str:
    """Get user's choice from the menu."""
    while True:
        try:
            choice = input(f"{Colors.CYAN}Enter your choice (1-5): {Colors.ENDC}")
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print_error("Invalid choice. Please enter a number between 1 and 5.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

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
    templates = ["basic", "echo", "reminder", "note"]
    print(f"\n{Colors.CYAN}Available templates:{Colors.ENDC}")
    for i, template in enumerate(templates, 1):
        print(f"{Colors.BOLD}{i}.{Colors.ENDC} {template}")
    
    while True:
        try:
            choice = input(f"\n{Colors.CYAN}Select template (1-4): {Colors.ENDC}")
            if choice in ['1', '2', '3', '4']:
                return templates[int(choice) - 1]
            print_error("Invalid choice. Please enter a number between 1 and 4.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

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
            "note": NoteBot
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

def interactive_analyze() -> None:
    """Interactive bot analysis process."""
    print_header("Analyze Bot")
    bot_path = input(f"{Colors.CYAN}Enter bot file path: {Colors.ENDC}")
    
    if not os.path.exists(bot_path):
        print_error(f"Bot file not found: {bot_path}")
        return
    
    results = analyze_bot_file(bot_path)
    
    if results.get('errors'):
        print_error('Errors:')
        for error in results['errors']:
            print(f"  - {error}")
    
    if results.get('warnings'):
        print_warning('Warnings:')
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    print_info('Configuration:')
    for key, value in results.get('config', {}).items():
        print(f"  {key}: {value}")
    
    print_info('Commands: ' + ', '.join(results.get('commands', [])))
    print_info('Events: ' + ', '.join(results.get('events', [])))
    print_info('Middleware: ' + ', '.join(results.get('middleware', [])))
    print_info('Permissions: ' + ', '.join(results.get('permissions', [])))

def interactive_verify() -> None:
    """Interactive wheel verification process."""
    print_header("Verify Wheel Signature")
    whl_path = input(f"{Colors.CYAN}Enter wheel file path (or press Enter to use latest): {Colors.ENDC}")
    
    if not whl_path:
        whl_path = find_latest_wheel()
        if not whl_path:
            print_error("No wheel files found in current directory")
            return
    
    sigstore_path = input(f"{Colors.CYAN}Enter sigstore file path (default: sigstore.json): {Colors.ENDC}") or "sigstore.json"
    
    if not os.path.exists(whl_path):
        print_error(f"Wheel file not found: {whl_path}")
        return
    
    if not os.path.exists(sigstore_path):
        print_error(f"Sigstore file not found: {sigstore_path}")
        return
    
    if not verify_wheel_signature(whl_path, sigstore_path):
        print_error("Verification failed")

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
            interactive_analyze()
        elif choice == '4':
            interactive_verify()
        elif choice == '5':
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


def verify_wheel_signature(whl_path: str, sigstore_path: str) -> bool:
    """Verifies the signature of a wheel file.

    Args:
        whl_path: The path to the wheel file.
        sigstore_path: The path to the sigstore file.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        with open(sigstore_path) as f:
            sigstore_data = json.load(f)

        with open(whl_path, "rb") as f:
            whl_content = f.read()
            whl_hash = hashlib.sha256(whl_content).hexdigest()

        if "hash" not in sigstore_data:
            print_error(f"No hash found in {sigstore_path}")
            return False

        if whl_hash != sigstore_data["hash"]:
            print_error("Hash verification failed!")
            print_info(f"Wheel hash: {whl_hash}")
            print_info(f"Sigstore hash: {sigstore_data['hash']}")
            return False

        print_success("Signature verification successful!")
        return True

    except Exception as e:
        print_error(f"Error during verification: {str(e)}")
        return False


def find_latest_wheel():
    """Finds the latest wheel file in the current directory.

    Returns:
        The path to the latest wheel file, or None if no wheel files are found.
    """
    wheels = glob("*.whl")
    if not wheels:
        return None
    return sorted(wheels)[-1]


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
    """Creates a full-featured bot with storage and admin commands.

    Args:
        name: The name of the bot.
        output_path: The desired output path.

    Returns:
        The path to the created bot file.

    Raises:
        RuntimeError: If the bot creation fails.
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


def analyze_bot_file(file_path: str) -> dict[str, Any]:
    """Analyzes a bot file for configuration issues and best practices.

    Args:
        file_path: The path to the bot file to analyze.

    Returns:
        A dictionary containing the analysis results.
    """
    try:
        abs_path = os.path.abspath(file_path)
        if not is_safe_path(abs_path):
            return {'errors': ['Invalid file path']}

        if not os.path.exists(abs_path):
            return {'errors': ['File not found']}
        if not abs_path.endswith('.py'):
            return {'errors': ['Not a Python file']}

        with open(abs_path) as f:
            tree = ast.parse(f.read())

        results = {
            'commands': [],
            'events': [],
            'middleware': [],
            'permissions': [],
            'config': {},
            'warnings': [],
            'errors': []
        }

        class BotAnalyzer(ast.NodeVisitor):
            """A visitor class to analyze the bot file's AST."""

            def __init__(self, results):
                """Initializes the BotAnalyzer with the results dictionary."""
                self.results = results
                super().__init__()

            @staticmethod
            def _is_bot_call(node: ast.Call) -> bool:
                """Checks if the given call node is a call to LXMFBot."""
                return (isinstance(node.func, ast.Name) and
                       node.func.id == 'LXMFBot')

            @staticmethod
            def _is_bot_assign(node: ast.Assign) -> bool:
                """Checks if the given assignment node assigns a value to a variable named 'bot' by calling LXMFBot."""
                return (isinstance(node.targets[0], ast.Name) and
                       node.targets[0].id == 'bot' and
                       isinstance(node.value, ast.Call) and
                       isinstance(node.value.func, ast.Name) and
                       node.value.func.id == 'LXMFBot')

            def visit_Call(self, node):
                """Visits a call node in the AST."""
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'command':
                        self.results['commands'].append(node.args[0].value)
                    elif node.func.attr == 'on':
                        self.results['events'].append(node.args[0].value)
                    elif node.func.attr == 'middleware':
                        self.results['middleware'].append(node.args[0].value)
                    elif node.func.attr == 'permission':
                        self.results['permissions'].append(node.args[0].value)
                elif self._is_bot_call(node):
                    for kw in node.keywords:
                        self.results['config'][kw.arg] = kw.value.value

            def visit_Assign(self, node):
                """Visits an assignment node in the AST."""
                if self._is_bot_assign(node):
                    for kw in node.value.keywords:
                        self.results['config'][kw.arg] = kw.value.value

        analyzer = BotAnalyzer(results)
        analyzer.visit(tree)

        return results

    except Exception as e:
        return {'errors': [f'Error analyzing file: {str(e)}']}


def main() -> None:
    """Main CLI entry point."""
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

  lxmfy run echo                        # Run the built-in echo bot
  lxmfy run reminder --name "MyReminder"  # Run the reminder bot with a custom name
  lxmfy run note                        # Run the built-in note bot

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
    parser.add_argument(
        "--no-cogs",
        action="store_true",
        help="Disable cogs loading for 'create' command",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        if not args.name:
            print_error("Please specify a bot file to analyze")
            sys.exit(1)

        bot_path = args.name
        if not os.path.exists(bot_path):
            print_error(f"Bot file not found: {bot_path}")
            sys.exit(1)

        print_header("Bot Analysis Results")
        results = analyze_bot_file(bot_path)

        if results.get('errors'):
            print_error('Errors:')
            for error in results['errors']:
                print(f"  - {error}")

        if results.get('warnings'):
            print_warning('Warnings:')
            for warning in results['warnings']:
                print(f"  - {warning}")

        print_info('Configuration:')
        for key, value in results.get('config', {}).items():
            print(f"  {key}: {value}")

        print_info('Commands: ' + ', '.join(results.get('commands', [])))
        print_info('Events: ' + ', '.join(results.get('events', [])))
        print_info('Middleware: ' + ', '.join(results.get('middleware', [])))
        print_info('Permissions: ' + ', '.join(results.get('permissions', [])))

    elif args.command == "create":
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

    elif args.command == "verify":
        whl_path = args.name
        sigstore_path = args.directory

        if not whl_path:
            whl_path = find_latest_wheel()
            if not whl_path:
                print_error("No wheel files found in current directory")
                sys.exit(1)

        if not sigstore_path:
            sigstore_path = "sigstore.json"

        if not os.path.exists(whl_path):
            print_error(f"Wheel file not found: {whl_path}")
            sys.exit(1)

        if not os.path.exists(sigstore_path):
            print_error(f"Sigstore file not found: {sigstore_path}")
            sys.exit(1)

        print_header("Verifying Wheel Signature")
        if not verify_wheel_signature(whl_path, sigstore_path):
            sys.exit(1)

    elif args.command == "run":
        template_name = args.name
        if not template_name:
            print_error("Please specify a template name to run (echo, reminder, note)")
            sys.exit(1)

        template_map = {
            "echo": EchoBot,
            "reminder": ReminderBot,
            "note": NoteBot
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


if __name__ == "__main__":
    main()
