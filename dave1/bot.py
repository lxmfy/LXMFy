from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="mybot",
    announce=600,  # Announce every 600 seconds (10 minutes)
    admins=[],  # Add your LXMF hashes here
    hot_reloading=True,
    command_prefix="/",
    # Moderation settings
    rate_limit=5,      # 5 messages per minute
    cooldown=5,        # 5 seconds cooldown
    max_warnings=3,    # 3 warnings before ban
    warning_timeout=300,  # Warnings reset after 5 minutes
    # Permission settings
    permissions_enabled=False,  # Set to True to enable role-based permissions
)

# Load all cogs from the cogs directory
load_cogs_from_directory(bot)

@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")

if __name__ == "__main__":
    bot.run()
