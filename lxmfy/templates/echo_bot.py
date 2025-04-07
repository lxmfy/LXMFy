"""Simple echo bot template."""

from lxmfy import LXMFBot


class EchoBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="Echo Bot",
            announce=600,
            command_prefix="",
            first_message_enabled=True
        )
        self.setup_commands()

    def setup_commands(self):
        @self.bot.command(name="echo", description="Echo back your message")
        def echo(ctx):
            if ctx.args:
                ctx.reply(" ".join(ctx.args))
            else:
                ctx.reply("Usage: echo <message>")

        @self.bot.on_first_message()
        def welcome(sender, message):
            content = message.content.decode("utf-8").strip()
            self.bot.send(sender, f"Hi! I'm an echo bot. You said: {content}\n\nTry echo <message> to make me repeat things!")
            return True

    def run(self):
        self.bot.run() 
