class Command:
    def __init__(self, name, description="No description provided", admin_only=False):
        self.name = name
        self.description = description
        self.admin_only = admin_only

    def __call__(self, func):
        self.callback = func
        func._command = self
        return func

    def __get__(self, obj, objtype=None):
        """Support instance methods"""
        if obj is None:
            return self
        return self.__class__(self.name, self.description, self.admin_only).__call__(
            self.callback.__get__(obj, objtype)
        )


def command(*args, **kwargs):
    return Command(*args, **kwargs)


class Cog:
    def __init__(self, bot):
        self.bot = bot
