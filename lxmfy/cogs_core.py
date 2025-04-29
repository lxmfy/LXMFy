"""
Cogs management module for LXMFy.

This module provides functionality for loading and managing cogs (extension modules)
in LXMFy bots. It handles dynamic loading of Python modules from a specified directory
and manages their integration with the bot system.
"""

import os
import sys

import RNS


def load_cogs_from_directory(bot, directory="cogs"):
    """
    Loads all Python modules from a specified directory as bot extensions (cogs).

    Args:
        bot: The LXMFBot instance to load the cogs into.
        directory (str): The directory name relative to the bot's config path. Defaults to "cogs".

    Raises:
        Exception: If there's an error loading any cog.
    """
    cogs_dir = os.path.join(bot.config_path, directory)

    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
        RNS.log(f"Created cogs directory: {cogs_dir}", RNS.LOG_INFO)
        return

    if cogs_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(cogs_dir))

    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog_name = f"{directory}.{filename[:-3]}"
            try:
                bot.load_extension(cog_name)
                RNS.log(f"Loaded extension: {cog_name}", RNS.LOG_INFO)
            except Exception as e:  # pylint: disable=broad-except
                RNS.log(f"Failed to load extension {cog_name}: {str(e)}", RNS.LOG_ERROR)
