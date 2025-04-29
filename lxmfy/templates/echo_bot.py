"""Simple echo bot template."""

from lxmfy import LXMFBot


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
                ctx.reply(" ".join(ctx.args))
            else:
                ctx.reply("Usage: echo <message>")

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
            self.bot.send(sender, f"Hi! I'm an echo bot. You said: {content}\n\nTry echo <message> to make me repeat things!")
            return True

    def run(self):
        """
        Runs the bot.
        """
        self.bot.run()
