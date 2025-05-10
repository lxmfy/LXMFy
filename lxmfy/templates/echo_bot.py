"""Simple echo bot template."""

import LXMF  # Added import for LXMF constants if needed by pack_icon_appearance_field

from lxmfy import IconAppearance, LXMFBot, pack_icon_appearance_field


class EchoBot:
    """
    A simple echo bot that repeats messages.
    """

    def __init__(self):
        """
        Initializes the EchoBot with basic configurations and sets up commands.
        """
        self.bot = LXMFBot(
            name="Echo Bot",
            announce=600,
            command_prefix="",
            first_message_enabled=True
        )
        self.setup_commands()

        # Define and pack the icon appearance for the bot
        icon_data = IconAppearance(icon_name="forum", fg_color=b'\xAD\xD8\xE6', bg_color=b'\x3B\x59\x98') # Light blue on dark blue
        self.icon_lxmf_field = pack_icon_appearance_field(icon_data)

    def setup_commands(self):
        """
        Sets up the bot's commands and event handlers.
        """
        @self.bot.command(name="echo", description="Echo back your message")
        def echo(ctx):
            """
            Echoes back the message provided by the user.

            Args:
                ctx: The command context.
            """
            if ctx.args:
                ctx.reply(" ".join(ctx.args), lxmf_fields=self.icon_lxmf_field)
            else:
                ctx.reply("Usage: echo <message>", lxmf_fields=self.icon_lxmf_field)

        @self.bot.on_first_message()
        def welcome(sender, message):
            """
            Greets the user on their first message and explains the bot's functionality.

            Args:
                sender: The sender of the message.
                message: The message received.

            Returns:
                True to indicate the message was handled.
            """
            content = message.content.decode("utf-8").strip()
            self.bot.send(sender, f"Hi! I'm an echo bot. You said: {content}\n\nTry echo <message> to make me repeat things!", lxmf_fields=self.icon_lxmf_field)
            return True

    def run(self):
        """
        Runs the bot.
        """
        self.bot.run()
