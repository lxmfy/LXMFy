"""
Command handling module for LXMFy.

This module provides the core command handling functionality for LXMFy bots,
including command registration, method decoration, and cog support.
"""


class Command:
    """
    A decorator class for bot commands.

    This class is used to mark methods as bot commands and provide metadata
    about the command such as its name, description, and permission requirements.

    Attributes:
        name (str): The name of the command
        description (str): A description of what the command does
        admin_only (bool): Whether the command is restricted to admin users
        callback (callable): The function that implements the command
    """

    def __init__(self, name, description="No description provided", admin_only=False):
        """
        Initialize a new Command.

        Args:
            name (str): The name of the command
            description (str, optional): Description of the command. Defaults to "No description provided"
            admin_only (bool, optional): Whether the command requires admin privileges. Defaults to False
        """
        self.name = name
        self.description = description
        self.admin_only = admin_only
        self.callback = None

    def __call__(self, func):
        """
        Decorate a function as a command.

        Args:
            func (callable): The function to be decorated

        Returns:
            callable: The decorated function
        """
        self.callback = func
        func._command = self
        return func

    def __get__(self, obj, objtype=None):
        """
        Support instance methods in command definitions.

        This method enables the command decorator to work with instance methods
        by properly binding the method to the instance.

        Args:
            obj: The instance that the command is bound to
            objtype: The type of the instance

        Returns:
            Command: A new Command instance bound to the object
        """
        if obj is None:
            return self
        return self.__class__(self.name, self.description, self.admin_only).__call__(
            self.callback.__get__(obj, objtype)
        )


def command(*args, **kwargs):
    """
    Shorthand decorator for creating Command instances.

    This function provides a more concise way to create commands using the
    @command decorator syntax instead of @Command().

    Args:
        *args: Positional arguments to pass to Command constructor
        **kwargs: Keyword arguments to pass to Command constructor

    Returns:
        Command: A new Command instance
    """
    return Command(*args, **kwargs)


class Cog:
    """
    Base class for bot extension modules (cogs).

    Cogs are used to organize bot commands and listeners into modular components.
    Each cog represents a collection of related commands and functionality.

    Attributes:
        bot: The bot instance that this cog is attached to
    """

    def __init__(self, bot):
        """
        Initialize a new Cog.

        Args:
            bot: The bot instance that this cog will be registered to
        """
        self.bot = bot
