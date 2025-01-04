"""Note-taking bot with JSON storage."""

from lxmfy import LXMFBot
from datetime import datetime

class NoteBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="Note Bot",
            announce=600,
            command_prefix="/",
            storage_type="json",
            storage_path="data/notes"
        )
        self.setup_commands()

    def setup_commands(self):
        @self.bot.command(name="note", description="Save a note")
        def save_note(ctx):
            if not ctx.args:
                ctx.reply("Usage: /note <your note>")
                return

            note = {
                "text": " ".join(ctx.args),
                "timestamp": datetime.now().isoformat(),
                "tags": [w[1:] for w in ctx.args if w.startswith("#")]
            }

            notes = self.bot.storage.get(f"notes:{ctx.sender}", [])
            notes.append(note)
            self.bot.storage.set(f"notes:{ctx.sender}", notes)
            ctx.reply("Note saved!")

        @self.bot.command(name="notes", description="List your notes")
        def list_notes(ctx):
            if not ctx.args:
                notes = self.bot.storage.get(f"notes:{ctx.sender}", [])
                if not notes:
                    ctx.reply("You haven't saved any notes yet!")
                    return

                response = "Your Notes:\n"
                for i, note in enumerate(notes[-10:], 1):
                    tags = " ".join(f"#{tag}" for tag in note["tags"]) if note["tags"] else ""
                    response += f"{i}. {note['text']} {tags}\n"
                
                if len(notes) > 10:
                    response += f"\nShowing last 10 of {len(notes)} notes. Use /notes all to see all."
                ctx.reply(response)
            elif ctx.args[0] == "all":
                notes = self.bot.storage.get(f"notes:{ctx.sender}", [])
                if not notes:
                    ctx.reply("You haven't saved any notes yet!")
                    return

                response = "All Your Notes:\n"
                for i, note in enumerate(notes, 1):
                    tags = " ".join(f"#{tag}" for tag in note["tags"]) if note["tags"] else ""
                    response += f"{i}. {note['text']} {tags}\n"
                ctx.reply(response)
            elif ctx.args[0].startswith("#"):
                tag = ctx.args[0][1:]
                notes = self.bot.storage.get(f"notes:{ctx.sender}", [])
                tagged_notes = [n for n in notes if tag in n["tags"]]
                
                if not tagged_notes:
                    ctx.reply(f"No notes found with tag #{tag}")
                    return

                response = f"Notes tagged #{tag}:\n"
                for i, note in enumerate(tagged_notes, 1):
                    tags = " ".join(f"#{t}" for t in note["tags"]) if note["tags"] else ""
                    response += f"{i}. {note['text']} {tags}\n"
                ctx.reply(response)

        @self.bot.command(name="search", description="Search your notes")
        def search_notes(ctx):
            if not ctx.args:
                ctx.reply("Usage: /search <text>")
                return

            search_term = " ".join(ctx.args).lower()
            notes = self.bot.storage.get(f"notes:{ctx.sender}", [])
            matches = [n for n in notes if search_term in n["text"].lower()]

            if not matches:
                ctx.reply(f"No notes found containing '{search_term}'")
                return

            response = f"Notes containing '{search_term}':\n"
            for i, note in enumerate(matches, 1):
                tags = " ".join(f"#{tag}" for tag in note["tags"]) if note["tags"] else ""
                response += f"{i}. {note['text']} {tags}\n"
            ctx.reply(response)

    def run(self):
        self.bot.run() 