"""Help command system for LXMFy."""

from dataclasses import dataclass

from .permissions import DefaultPerms


@dataclass
class HelpFormatter:
    """Default help formatter for commands"""

    @staticmethod
    def format_command(command) -> str:
        """Format a single command's help"""
        help_text = [f"Command: {command.name}"]
        help_text.append(f"Description: {command.help.description}")

        if command.help.usage:
            help_text.append(f"Usage: {command.help.usage}")

        if command.help.examples:
            help_text.append("Examples:")
            help_text.extend(f"  {ex}" for ex in command.help.examples)

        if command.permissions != DefaultPerms.USE_COMMANDS:
            help_text.append("Required Permissions:")
            for perm in DefaultPerms:
                if perm.value & command.permissions:
                    help_text.append(f"  - {perm.name}")

        if command.admin_only:
            help_text.append("Note: Admin only command")

        return "\n".join(help_text)

    @staticmethod
    def format_category(category: str, commands: list) -> str:
        """Format a category of commands"""
        help_text = [f"\n=== {category} ==="]
        for cmd in commands:
            help_text.append(f"{cmd.name}: {cmd.help.description}")
        return "\n".join(help_text)

    @staticmethod
    def format_all_commands(categories: dict[str, list]) -> str:
        """Format the complete help listing"""
        help_text = ["Available Commands:"]

        for category, commands in categories.items():
            help_text.append(HelpFormatter.format_category(category, commands))

        return "\n".join(help_text)


class HelpSystem:
    def __init__(self, bot, formatter=None):
        self.bot = bot
        self.formatter = formatter or HelpFormatter()

        # Register the help command
        @bot.command(
            name="help",
            description="Show help for commands"
        )
        def help_command(ctx):
            args = ctx.args
            if not args:
                # Show all commands
                categories = self._get_categorized_commands(ctx.is_admin)
                response = self.formatter.format_all_commands(categories)
                ctx.reply(response)
                return  # Make sure to return after replying

            # Show specific command help
            command_name = args[0]
            if command_name in self.bot.commands:
                command = self.bot.commands[command_name]
                if command.admin_only and not ctx.is_admin:
                    ctx.reply("This command is for administrators only.")
                    return  # Make sure to return after replying
                response = self.formatter.format_command(command)
                ctx.reply(response)
                return  # Make sure to return after replying
            else:
                ctx.reply(f"Command '{command_name}' not found.")
                return  # Make sure to return after replying

    def _get_categorized_commands(self, is_admin: bool) -> dict[str, list]:
        """Group commands by category"""
        categories = {}

        for cmd in self.bot.commands.values():
            if cmd.admin_only and not is_admin:
                continue

            category = cmd.help.category or "General"
            if category not in categories:
                categories[category] = []
            categories[category].append(cmd)

        return categories
