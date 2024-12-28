from lxmfy import LXMFBot, Storage, JSONStorage
from datetime import datetime


class MessageTrackingBot:
    def __init__(self):
        # Initialize bot with basic settings
        self.bot = LXMFBot(
            name="StorageBot",
            command_prefix="!",
        )

        # Register commands
        self.setup_commands()

    def setup_commands(self):
        @self.bot.command(name="stats")
        def stats(ctx):
            """Show user message statistics"""
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

        @self.bot.command(name="note")
        def save_note(ctx):
            """Save a personal note"""
            if not ctx.args:
                ctx.reply("Usage: !note <your note>")
                return

            note = " ".join(ctx.args)
            notes = ctx.bot.storage.get(f"notes:{ctx.sender}", [])
            notes.append({"text": note, "timestamp": datetime.now().isoformat()})
            ctx.bot.storage.set(f"notes:{ctx.sender}", notes)
            ctx.reply("Note saved!")

        @self.bot.command(name="notes")
        def list_notes(ctx):
            """List all saved notes"""
            notes = ctx.bot.storage.get(f"notes:{ctx.sender}", [])
            if not notes:
                ctx.reply("You haven't saved any notes yet!")
                return

            response = "Your Notes:\n"
            for i, note in enumerate(notes, 1):
                response += f"{i}. {note['text']} (saved: {note['timestamp']})\n"
            ctx.reply(response)

        @self.bot.command(name="clear_notes")
        def clear_notes(ctx):
            """Clear all saved notes"""
            ctx.bot.storage.delete(f"notes:{ctx.sender}")
            ctx.reply("All notes cleared!")

        @self.bot.command(name="leaderboard")
        def leaderboard(ctx):
            """Show most active users"""
            all_stats = {}
            for key in ctx.bot.storage.scan("stats:*"):
                user_hash = key.split(":")[1]
                stats = ctx.bot.storage.get(key)
                all_stats[user_hash] = stats["messages"]

            # Sort by message count
            sorted_users = sorted(all_stats.items(), key=lambda x: x[1], reverse=True)[
                :5
            ]

            response = "Top 5 Most Active Users:\n"
            for i, (user, count) in enumerate(sorted_users, 1):
                response += f"{i}. User {user[:8]}: {count} messages\n"
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
    bot = MessageTrackingBot()
    bot.run()
