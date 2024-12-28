import os
import argparse
import sys
import re

def sanitize_filename(filename):
    """Sanitize the filename"""
    filename = os.path.basename(filename)
    
    filename = re.sub(r'[^a-zA-Z0-9\-_.]', '', filename)
    
    if not filename.endswith('.py'):
        filename += '.py'
    
    return filename

def validate_bot_name(name):
    """Validate bot name"""
    if not re.match(r'^[a-zA-Z0-9\s-_]+$', name):
        raise ValueError("Bot name can only contain alphanumeric characters, spaces, dash, and underscore")
    return name

def create_bot_file(name, output_file):
    """Create the bot file."""
    try:
        name = validate_bot_name(name)
        safe_filename = sanitize_filename(output_file)
        
        safe_path = os.path.join(os.getcwd(), safe_filename)
        
        template = f"""from lxmfy import LXMFBot, load_cogs_from_directory

bot = LXMFBot(
    name="{name}",
    announce=600,  # Announce every 600 seconds (10 minutes)
    admins=[],  # Add your LXMF hashes here
    hot_reloading=True,
    command_prefix="/",
    # Moderation settings
    rate_limit=5,      # 5 messages per minute
    cooldown=5,        # 5 seconds cooldown
    max_warnings=3,    # 3 warnings before ban
    warning_timeout=300,  # Warnings reset after 5 minutes
)

# Load all cogs from the cogs directory
load_cogs_from_directory(bot)

@bot.command(name="ping", description="Test if bot is responsive")
def ping(ctx):
    ctx.reply("Pong!")

if __name__ == "__main__":
    bot.run()
"""
        with open(safe_path, "w") as f:
            f.write(template)
            
        return safe_filename
            
    except Exception as e:
        raise RuntimeError(f"Failed to create bot file: {str(e)}")

def create_example_cog():
    """Create example cog."""
    try:
        cogs_dir = os.path.join(os.getcwd(), "cogs")
        
        os.makedirs(cogs_dir, exist_ok=True)

        init_path = os.path.join(cogs_dir, "__init__.py")
        with open(init_path, "w") as f:
            f.write("")

        template = """from lxmfy import Command

class BasicCommands:
    def __init__(self, bot):
        self.bot = bot
    
    @Command(name="hello", description="Says hello")
    async def hello(self, ctx):
        ctx.reply(f"Hello {ctx.sender}!")
    
    @Command(name="about", description="About this bot")
    async def about(self, ctx):
        ctx.reply("I'm a bot created with LXMFy!")

def setup(bot):
    bot.add_cog(BasicCommands(bot))
"""
        basic_path = os.path.join(cogs_dir, "basic.py")
        with open(basic_path, "w") as f:
            f.write(template)
            
    except Exception as e:
        raise RuntimeError(f"Failed to create example cog: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="LXMFy Bot Creator")
    parser.add_argument("command", choices=["create"], help="Create a new LXMF bot")
    parser.add_argument("--name", default="MyLXMFBot", help="Name of the bot")
    parser.add_argument("--output", default="mybot.py", help="Output file name")

    args = parser.parse_args()

    if args.command == "create":
        try:
            safe_filename = create_bot_file(args.name, args.output)
            create_example_cog()
            print(
                f"""
✨ Successfully created new LXMFy bot!

Files created:
  - {safe_filename} (main bot file)
  - cogs/
    - __init__.py
    - basic.py (example cog)

To start your bot:
  python {safe_filename}

To add admin rights, edit {safe_filename} and add your LXMF hash to the admins list.
            """
            )
        except Exception as e:
            print(f"Error creating bot: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
