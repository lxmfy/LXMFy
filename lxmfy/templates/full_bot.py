from lxmfy import LXMFBot, load_cogs_from_directory
from datetime import datetime


class FullBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="LXMFy Full Bot",
            announce=600,
            admins=["lxmf_hash"],  # Replace with your admin hash
            hot_reloading=True,
            # Moderation settings
            rate_limit=5,
            cooldown=5,
            max_warnings=3,
            warning_timeout=300,
            command_prefix="/",
            cogs_dir="cogs",
        )

        # Load all cogs
        load_cogs_from_directory(self.bot)

        # Register built-in commands
        self.setup_commands()

    def setup_commands(self):
        # Basic Commands
        @self.bot.command(name="ping", description="Test if bot is responsive")
        def ping(ctx):
            ctx.reply("Pong!")

        @self.bot.command(name="echo", description="Echo back your message")
        def echo(ctx):
            if ctx.args:
                ctx.reply(" ".join(ctx.args))
            else:
                ctx.reply("Please provide a message to echo")

        # Stats & Storage Commands
        @self.bot.command(name="stats", description="Show your message statistics")
        def stats(ctx):
            user_stats = ctx.bot.storage.get(
                f"stats:{ctx.sender}", {"messages": 0, "commands": 0, "last_seen": None}
            )
            response = (
                f"Your Stats:\n"
                f"Messages: {user_stats['messages']}\n"
                f"Commands: {user_stats['commands']}\n"
                f"Last Seen: {user_stats['last_seen'] or 'First time!'}"
            )
            ctx.reply(response)

        @self.bot.command(name="note", description="Save a personal note")
        def save_note(ctx):
            if not ctx.args:
                ctx.reply("Usage: /note <your note>")
                return

            note = " ".join(ctx.args)
            notes = ctx.bot.storage.get(f"notes:{ctx.sender}", [])
            notes.append({"text": note, "timestamp": datetime.now().isoformat()})
            ctx.bot.storage.set(f"notes:{ctx.sender}", notes)
            ctx.reply("Note saved!")

        @self.bot.command(name="notes", description="List all your saved notes")
        def list_notes(ctx):
            notes = ctx.bot.storage.get(f"notes:{ctx.sender}", [])
            if not notes:
                ctx.reply("You haven't saved any notes yet!")
                return

            response = "Your Notes:\n"
            for i, note in enumerate(notes, 1):
                response += f"{i}. {note['text']} (saved: {note['timestamp']})\n"
            ctx.reply(response)

        @self.bot.command(name="clear_notes", description="Clear all your saved notes")
        def clear_notes(ctx):
            ctx.bot.storage.delete(f"notes:{ctx.sender}")
            ctx.reply("All notes cleared!")

        # Admin Commands
        @self.bot.command(
            name="broadcast", description="Send message to all users", admin_only=True
        )
        def broadcast(ctx):
            if not ctx.args:
                ctx.reply("Usage: /broadcast <message>")
                return
            message = " ".join(ctx.args)
            ctx.broadcast(message)
            ctx.reply("Broadcast sent!")

        @self.bot.command(
            name="stats_all", description="Show all user statistics", admin_only=True
        )
        def stats_all(ctx):
            all_stats = {}
            for key in ctx.bot.storage.scan("stats:*"):
                user_hash = key.split(":")[1]
                stats = ctx.bot.storage.get(key)
                all_stats[user_hash] = stats

            response = "All User Statistics:\n"
            for user_hash, stats in all_stats.items():
                response += f"\nUser {user_hash[:8]}:\n"
                response += f"Messages: {stats['messages']}\n"
                response += f"Commands: {stats['commands']}\n"
                response += f"Last Seen: {stats['last_seen']}\n"
            ctx.reply(response)

        @self.bot.command(
            name="system", description="Show system information", admin_only=True
        )
        def system(ctx):
            response = (
                f"System Information:\n"
                f"Bot Name: {self.bot.name}\n"
                f"Uptime: {self.bot.uptime()}\n"
                f"Active Users: {len(self.bot.storage.scan('stats:*'))}\n"
                f"Total Notes: {len(self.bot.storage.scan('notes:*'))}\n"
                f"Rate Limit: {self.bot.rate_limit} msg/min\n"
                f"Cooldown: {self.bot.cooldown}s\n"
                f"Warning Timeout: {self.bot.warning_timeout}s\n"
            )
            ctx.reply(response)

    def update_user_stats(self, sender):
        """Update user statistics"""
        stats = self.bot.storage.get(
            f"stats:{sender}", {"messages": 0, "commands": 0, "last_seen": None}
        )
        stats["messages"] += 1
        stats["last_seen"] = datetime.now().isoformat()
        self.bot.storage.set(f"stats:{sender}", stats)

    def run(self):
        # Override message handler to track stats
        original_handler = self.bot._message_received

        def message_handler(message):
            self.update_user_stats(message.source_hash)
            original_handler(message)

        self.bot._message_received = message_handler
        self.bot.run()


if __name__ == "__main__":
    bot = FullBot()
    bot.run()
