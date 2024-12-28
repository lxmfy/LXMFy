import os
import argparse
import sys

def create_bot_file(name, output_file):
    template = f'''from lxmfy import LXMFBot, load_cogs_from_directory

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
'''
    
    with open(output_file, 'w') as f:
        f.write(template)

def create_example_cog():
    if not os.path.exists('cogs'):
        os.makedirs('cogs')
        
    # Create __init__.py
    with open('cogs/__init__.py', 'w') as f:
        f.write('')
    
    # Create example cog
    template = '''from lxmfy import Command

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
'''
    
    with open('cogs/basic.py', 'w') as f:
        f.write(template)

def main():
    parser = argparse.ArgumentParser(description='LXMFy Bot Creator')
    parser.add_argument('command', choices=['starter'], help='Command to execute')
    parser.add_argument('--name', default='MyLXMFBot', help='Name of the bot')
    parser.add_argument('--output', default='mybot.py', help='Output file name')
    
    args = parser.parse_args()
    
    if args.command == 'starter':
        try:
            create_bot_file(args.name, args.output)
            create_example_cog()
            print(f"""
✨ Successfully created new LXMFy bot!

Files created:
  - {args.output} (main bot file)
  - cogs/
    - __init__.py
    - basic.py (example cog)

To start your bot:
  python {args.output}

To add admin rights, edit {args.output} and add your LXMF hash to the admins list.
            """)
        except Exception as e:
            print(f"Error creating bot: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main() 