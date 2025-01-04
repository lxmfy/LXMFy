"""Reminder bot with SQLite storage."""

from lxmfy import LXMFBot
import time
from datetime import datetime, timedelta
import re

class ReminderBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="Reminder Bot",
            announce=600,
            command_prefix="/",
            storage_type="sqlite",
            storage_path="data/reminders.db"
        )
        self.setup_commands()
        self.setup_reminder_check()

    def setup_commands(self):
        @self.bot.command(name="remind", description="Set a reminder")
        def remind(ctx):
            if not ctx.args or len(ctx.args) < 2:
                ctx.reply("Usage: /remind <time> <message>\nExample: /remind 1h30m Buy groceries")
                return

            time_str = ctx.args[0].lower()
            message = " ".join(ctx.args[1:])
            
            # Parse time string (e.g., 1h30m, 2d, 45m)
            total_minutes = 0
            time_parts = re.findall(r'(\d+)([dhm])', time_str)
            
            for value, unit in time_parts:
                if unit == 'd':
                    total_minutes += int(value) * 24 * 60
                elif unit == 'h':
                    total_minutes += int(value) * 60
                elif unit == 'm':
                    total_minutes += int(value)

            if total_minutes == 0:
                ctx.reply("Invalid time format. Use combinations of d (days), h (hours), m (minutes)")
                return

            remind_time = datetime.now() + timedelta(minutes=total_minutes)
            
            reminder = {
                "user": ctx.sender,
                "message": message,
                "time": remind_time.timestamp(),
                "created": time.time()
            }
            
            reminders = self.bot.storage.get("reminders", [])
            reminders.append(reminder)
            self.bot.storage.set("reminders", reminders)
            
            ctx.reply(f"I'll remind you about '{message}' at {remind_time.strftime('%Y-%m-%d %H:%M:%S')}")

        @self.bot.command(name="list", description="List your reminders")
        def list_reminders(ctx):
            reminders = self.bot.storage.get("reminders", [])
            user_reminders = [r for r in reminders if r["user"] == ctx.sender]
            
            if not user_reminders:
                ctx.reply("You have no active reminders")
                return
                
            response = "Your reminders:\n"
            for i, reminder in enumerate(user_reminders, 1):
                remind_time = datetime.fromtimestamp(reminder["time"])
                response += f"{i}. {reminder['message']} (at {remind_time.strftime('%Y-%m-%d %H:%M:%S')})\n"
            
            ctx.reply(response)

    def setup_reminder_check(self):
        def check_reminders():
            reminders = self.bot.storage.get("reminders", [])
            current_time = time.time()
            
            # Find due reminders
            due_reminders = [r for r in reminders if r["time"] <= current_time]
            remaining = [r for r in reminders if r["time"] > current_time]
            
            # Send notifications
            for reminder in due_reminders:
                self.bot.send(
                    reminder["user"],
                    f"Reminder: {reminder['message']}",
                    "Reminder"
                )
            
            # Update storage
            if due_reminders:
                self.bot.storage.set("reminders", remaining)

        def run_with_reminders(delay=10):
            while True:
                check_reminders()
                for i in list(self.bot.queue.queue):
                    lxm = self.bot.queue.get()
                    self.bot.router.handle_outbound(lxm)
                self.bot._announce()
                time.sleep(delay)
                
        # Replace the bot's run method
        self.bot.run = run_with_reminders

    def run(self):
        self.bot.run() 