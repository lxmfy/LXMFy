from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="Test LXMFy Bot",
    announce=600,
    admins=["3832c4ec19ac161a6c6e18baa5cff5cb"],
    hot_reloading=True,
    # Moderation settings
    rate_limit=5,  # 5 messages per minute
    cooldown=5,  # 5 seconds cooldown
    max_warnings=3,  # 3 warnings before ban
    warning_timeout=300,  # Warnings reset after 5 minutes
    command_prefix="/",  # Set to None to process all messages as commands
    cogs_dir="cogs",  # Specify cogs directory name
)

# Dynamically load all cogs
load_cogs_from_directory(bot)


# Basic commands can still be defined here
@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")


@bot.command(name="echo", description="Echo back your message")
def echo(ctx):
    if ctx.args:
        ctx.reply(" ".join(ctx.args))
    else:
        ctx.reply("Please provide a message to echo")


bot.run()
