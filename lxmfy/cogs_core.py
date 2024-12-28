import os
import importlib.util
import RNS
import sys


def load_cogs_from_directory(bot, directory="cogs"):
    # Get the absolute path to the cogs directory relative to config
    cogs_dir = os.path.join(bot.config_path, directory)

    # Ensure the directory exists
    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
        RNS.log(f"Created cogs directory: {cogs_dir}", RNS.LOG_INFO)
        return

    # Add cogs directory to Python path if not already there
    if cogs_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(cogs_dir))

    # Load each Python file in the cogs directory
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            # Convert filename to module path (e.g., 'cogs.admin')
            cog_name = f"{directory}.{filename[:-3]}"
            try:
                bot.load_extension(cog_name)
                RNS.log(f"Loaded extension: {cog_name}", RNS.LOG_INFO)
            except Exception as e:
                RNS.log(f"Failed to load extension {cog_name}: {str(e)}", RNS.LOG_ERROR)
