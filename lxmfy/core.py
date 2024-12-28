import os, time
import RNS
from LXMF import LXMRouter, LXMessage
from queue import Queue
from types import SimpleNamespace
from .commands import Command
import sys
import importlib
import inspect
from .moderation import SpamProtection


class LXMFBot:
    delivery_callbacks = []
    receipts = []
    queue = Queue(maxsize=5)
    announce_time = 600

    def __init__(
        self,
        name="LXMFBot",
        announce=600,
        announce_immediately=True,
        admins=None,
        hot_reloading=False,
        rate_limit=5,
        cooldown=60,
        max_warnings=3,
        warning_timeout=300,
        command_prefix="/",
        cogs_dir="cogs",
    ):
        self.config_path = os.path.join(os.getcwd(), "config")
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # Setup cogs directory
        self.cogs_dir = os.path.join(self.config_path, cogs_dir)
        if not os.path.exists(self.cogs_dir):
            os.makedirs(self.cogs_dir)

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(self.cogs_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

        idfile = os.path.join(self.config_path, "identity")
        if not os.path.isfile(idfile):
            RNS.log("No Primary Identity file found, creating new...", RNS.LOG_INFO)
            id = RNS.Identity(True)
            id.to_file(idfile)
        self.id = RNS.Identity.from_file(idfile)
        RNS.log("Loaded identity from file", RNS.LOG_INFO)
        if announce_immediately:
            af = os.path.join(self.config_path, "announce")
            if os.path.isfile(af):
                os.remove(af)
                RNS.log("Announcing now. Timer reset.", RNS.LOG_INFO)
        RNS.Reticulum(loglevel=RNS.LOG_VERBOSE)
        self.router = LXMRouter(identity=self.id, storagepath=self.config_path)
        self.local = self.router.register_delivery_identity(self.id, display_name=name)
        self.router.register_delivery_callback(self._message_received)
        RNS.log(
            "LXMF Router ready to receive on: {}".format(
                RNS.prettyhexrep(self.local.hash)
            ),
            RNS.LOG_INFO,
        )
        self._announce()
        self.commands = {}
        self.cogs = {}
        self.admins = set(admins) if admins else set()
        self.hot_reloading = hot_reloading
        self.announce_time = announce
        self.spam_protection = SpamProtection(
            rate_limit=rate_limit,
            cooldown=cooldown,
            max_warnings=max_warnings,
            warning_timeout=warning_timeout,
        )
        self.command_prefix = command_prefix

    def command(self, *args, **kwargs):
        def decorator(func):
            # Create a new Command instance
            if len(args) > 0:
                name = args[0]
            else:
                name = kwargs.get("name", func.__name__)

            description = kwargs.get("description", "No description provided")
            admin_only = kwargs.get("admin_only", False)

            cmd = Command(name=name, description=description, admin_only=admin_only)
            cmd.callback = func
            self.commands[name] = cmd
            return func  # Return the original function, not the command object

        return decorator

    def load_extension(self, name):
        if self.hot_reloading:
            # Reload module if it's already loaded
            if name in sys.modules:
                module = importlib.reload(sys.modules[name])
            else:
                module = importlib.import_module(name)
        else:
            module = importlib.import_module(name)

        if not hasattr(module, "setup"):
            raise ImportError(f"Extension {name} missing setup function")
        module.setup(self)

    def add_cog(self, cog):
        self.cogs[cog.__class__.__name__] = cog
        for name, method in inspect.getmembers(
            cog, predicate=lambda x: hasattr(x, "_command")
        ):
            cmd = method._command
            cmd.callback = method
            self.commands[cmd.name] = cmd

    def is_admin(self, sender):
        return sender in self.admins

    def _message_received(self, message):
        sender = RNS.hexrep(message.source_hash, delimit=False)
        receipt = RNS.hexrep(message.hash, delimit=False)
        RNS.log(f"Message receipt <{receipt}>", RNS.LOG_INFO)

        def reply(msg):
            self.send(sender, msg)

        if receipt not in self.receipts:
            self.receipts.append(receipt)
            if len(self.receipts) > 100:
                self.receipts.pop(0)

            content = message.content.decode("utf-8").strip()

            # Create context object
            obj = {
                "lxmf": message,
                "reply": reply,
                "sender": sender,
                "content": content,
                "hash": receipt,
            }
            msg = SimpleNamespace(**obj)

            # Skip spam check for admins
            if not self.is_admin(sender):
                allowed, reason = self.spam_protection.check_spam(sender)
                if not allowed:
                    self.send(sender, reason)
                    return

            # Handle commands if prefix is set, otherwise process all messages
            if self.command_prefix is None or content.startswith(self.command_prefix):
                command_name = (
                    content.split()[0][len(self.command_prefix) :]
                    if self.command_prefix
                    else content.split()[0]
                )
                if command_name in self.commands:
                    cmd = self.commands[command_name]
                    if getattr(cmd, "admin_only", False) and not self.is_admin(sender):
                        self.send(sender, "This command is for administrators only.")
                        return

                    ctx = SimpleNamespace(
                        bot=self,
                        sender=sender,
                        content=content,
                        args=content.split()[1:],
                        is_admin=self.is_admin(sender),
                        reply=reply,
                        message=msg,
                    )

                    try:
                        cmd.callback(ctx)
                    except Exception as e:
                        RNS.log(
                            f"Error executing command {command_name}: {str(e)}",
                            RNS.LOG_ERROR,
                        )
                        self.send(sender, f"Error executing command: {str(e)}")

            # Call legacy delivery callbacks
            for callback in self.delivery_callbacks:
                callback(msg)

    def _announce(self):
        announce_path = os.path.join(self.config_path, "announce")
        if os.path.isfile(announce_path):
            with open(announce_path, "r") as f:
                announce = int(f.readline())
        else:
            announce = 1

        if announce > int(time.time()):
            RNS.log("Recent announcement", RNS.LOG_DEBUG)
        else:
            with open(announce_path, "w+") as af:
                next_announce = int(time.time()) + self.announce_time
                af.write(str(next_announce))
            self.local.announce()
            RNS.log("Announcement sent, expr set 1800 seconds", RNS.LOG_INFO)

    def send(self, destination, message, title="Reply"):
        try:
            hash = bytes.fromhex(destination)
        except Exception as e:
            RNS.log("Invalid destination hash", RNS.LOG_ERROR)
            return

        if not len(hash) == RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
            RNS.log("Invalid destination hash length", RNS.LOG_ERROR)
        else:
            id = RNS.Identity.recall(hash)
            if id == None:
                RNS.log(
                    "Could not recall an Identity for the requested address. You have probably never received an announce from it. Try requesting a path from the network first. In fact, let's do this now :)",
                    RNS.LOG_ERROR,
                )
                RNS.Transport.request_path(hash)
                RNS.log(
                    "OK, a path was requested. If the network knows a path, you will receive an announce with the Identity data shortly.",
                    RNS.LOG_INFO,
                )
            else:
                lxmf_destination = RNS.Destination(
                    id, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery"
                )
                lxm = LXMessage(
                    lxmf_destination,
                    self.local,
                    message,
                    title=title,
                    desired_method=LXMessage.DIRECT,
                )
                lxm.try_propagation_on_fail = True
                self.queue.put(lxm)

    def run(self, delay=10):
        RNS.log(
            f"LXMF Bot `{self.local.display_name}` reporting for duty and awaiting messages...",
            RNS.LOG_INFO,
        )
        while True:
            for i in list(self.queue.queue):
                lxm = self.queue.get()
                self.router.handle_outbound(lxm)
            self._announce()
            time.sleep(delay)

    def received(self, function):
        """Legacy decorator for backward compatibility"""
        self.delivery_callbacks.append(function)
        return function
