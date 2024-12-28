from lxmfy import Command, Cog
from datetime import datetime
import time


class TimeCog(Cog):
    def __init__(self, bot):
        super().__init__(bot)

    @Command(name="time", description="Show current time")
    def time(self, ctx):
        current_time = datetime.now().strftime("%H:%M:%S")
        ctx.reply(f"Current time: {current_time}")

    @Command(name="date", description="Show current date")
    def date(self, ctx):
        current_date = datetime.now().strftime("%Y-%m-%d")
        ctx.reply(f"Current date: {current_date}")

    @Command(name="timestamp", description="Show Unix timestamp")
    def timestamp(self, ctx):
        ctx.reply(f"Unix timestamp: {int(time.time())}")

    @Command(name="datetime", description="Show full date and time")
    def datetime(self, ctx):
        full_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ctx.reply(f"Current date and time: {full_datetime}")


def setup(bot):
    bot.add_cog(TimeCog(bot))
