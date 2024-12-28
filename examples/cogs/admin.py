from lxmfy import Command, Cog


class AdminCog(Cog):
    def __init__(self, bot):
        super().__init__(bot)

    @Command(name="status", description="Show bot status", admin_only=True)
    def status(self, ctx):
        status = f"Bot Status:\n"
        status += f"Loaded cogs: {', '.join(self.bot.cogs.keys())}\n"
        status += f"Command count: {len(self.bot.commands)}\n"
        status += f"Command prefix: {self.bot.command_prefix or 'None (processing all messages)'}\n"
        status += (
            f"Hot reloading: {'enabled' if self.bot.hot_reloading else 'disabled'}\n"
        )
        status += f"Announce interval: {self.bot.announce_time} seconds\n"
        status += f"Moderation:\n"
        status += f"- Rate limit: {self.bot.spam_protection.rate_limit} msgs/{self.bot.spam_protection.cooldown}s\n"
        status += f"- Max warnings: {self.bot.spam_protection.max_warnings}\n"
        status += f"- Warning timeout: {self.bot.spam_protection.warning_timeout}s"
        ctx.reply(status)

    @Command(name="reload", description="Reload a cog", admin_only=True)
    def reload(self, ctx):
        if not ctx.args:
            ctx.reply("Please specify a cog to reload")
            return

        cog_name = ctx.args[0]
        try:
            self.bot.load_extension(cog_name)
            ctx.reply(f"Successfully reloaded {cog_name}")
        except Exception as e:
            ctx.reply(f"Error reloading {cog_name}: {str(e)}")

    @Command(name="cogs", description="List loaded cogs", admin_only=True)
    def cogs(self, ctx):
        cog_list = "Loaded cogs:\n"
        for cog_name in self.bot.cogs:
            cog_list += f"- {cog_name}\n"
        ctx.reply(cog_list)

    @Command(name="help", description="Show command help", admin_only=False)
    def help(self, ctx):
        if ctx.args:
            cmd_name = ctx.args[0]
            if cmd_name in self.bot.commands:
                cmd = self.bot.commands[cmd_name]
                help_text = f"Command: {cmd_name}\n"
                help_text += f"Description: {cmd.description}\n"
                help_text += f"Admin only: {'Yes' if cmd.admin_only else 'No'}"
                ctx.reply(help_text)
            else:
                ctx.reply(f"Command '{cmd_name}' not found")
        else:
            help_text = "Available commands:\n"
            for name, cmd in sorted(self.bot.commands.items()):
                if not cmd.admin_only or ctx.is_admin:
                    help_text += f"{name}: {cmd.description}\n"
            ctx.reply(help_text)


def setup(bot):
    bot.add_cog(AdminCog(bot))
