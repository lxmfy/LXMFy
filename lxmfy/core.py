"""
Core module for LXMFy bot framework.

This module provides the main LXMFBot class that handles message routing,
command processing, and bot lifecycle management for LXMF-based bots on
the Reticulum Network.
"""

# Standard library imports
import os
import sys
import time
import inspect
import importlib
import logging
from queue import Queue
from types import SimpleNamespace
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Reticulum and LXMF imports
import RNS
from LXMF import LXMRouter, LXMessage

# Local imports
from .commands import Command
from .moderation import SpamProtection
from .transport import Transport
from .storage import JSONStorage, Storage


@dataclass
class BotConfig:
    """Configuration settings for LXMFBot."""

    name: str = "LXMFBot"
    announce: int = 600
    announce_immediately: bool = True
    admins: set = None
    hot_reloading: bool = False
    rate_limit: int = 5
    cooldown: int = 60
    max_warnings: int = 3
    warning_timeout: int = 300
    command_prefix: str = "/"
    cogs_dir: str = "cogs"


class LXMFBot:
    """
    Main bot class for handling LXMF messages and commands.

    This class manages the bot's lifecycle, including:
    - Message routing and delivery
    - Command registration and execution
    - Cog (extension) loading and management
    - Spam protection
    - Admin privileges
    """

    delivery_callbacks = []
    receipts = []
    queue = Queue(maxsize=5)
    announce_time = 600
    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        """
        Initialize a new LXMFBot instance.

        Args:
            **kwargs: Override default configuration settings
        """
        config = BotConfig(**kwargs)

        # Setup paths
        self.config_path = os.path.join(os.getcwd(), "config")
        os.makedirs(self.config_path, exist_ok=True)

        # Setup cogs
        self.cogs_dir = os.path.join(self.config_path, config.cogs_dir)
        os.makedirs(self.cogs_dir, exist_ok=True)

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(self.cogs_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                pass

        # Setup identity
        identity_file = os.path.join(self.config_path, "identity")
        if not os.path.isfile(identity_file):
            RNS.log("No Primary Identity file found, creating new...", RNS.LOG_INFO)
            identity = RNS.Identity(True)
            identity.to_file(identity_file)
        self.identity = RNS.Identity.from_file(identity_file)
        RNS.log("Loaded identity from file", RNS.LOG_INFO)

        # Handle immediate announce
        if config.announce_immediately:
            announce_file = os.path.join(self.config_path, "announce")
            if os.path.isfile(announce_file):
                os.remove(announce_file)
                RNS.log("Announcing now. Timer reset.", RNS.LOG_INFO)

        # Initialize LXMF router
        RNS.Reticulum(loglevel=RNS.LOG_VERBOSE)
        self.router = LXMRouter(identity=self.identity, storagepath=self.config_path)
        self.local = self.router.register_delivery_identity(
            self.identity, display_name=config.name
        )
        self.router.register_delivery_callback(self._message_received)
        RNS.log(
            f"LXMF Router ready to receive on: {RNS.prettyhexrep(self.local.hash)}",
            RNS.LOG_INFO,
        )

        # Initialize bot state
        self._announce()
        self.commands = {}
        self.cogs = {}
        self.admins = set(config.admins) if config.admins else set()
        self.hot_reloading = config.hot_reloading
        self.announce_time = config.announce
        self.command_prefix = config.command_prefix

        # Initialize services
        self.storage = Storage(JSONStorage(os.path.join(self.config_path, "storage")))
        self.spam_protection = SpamProtection(
            storage=self.storage,
            rate_limit=config.rate_limit,
            cooldown=config.cooldown,
            max_warnings=config.max_warnings,
            warning_timeout=config.warning_timeout,
        )
        self.transport = Transport(storage=self.storage)

    def command(self, *args, **kwargs):
        def decorator(func):
            if len(args) > 0:
                name = args[0]
            else:
                name = kwargs.get("name", func.__name__)

            description = kwargs.get("description", "No description provided")
            admin_only = kwargs.get("admin_only", False)

            cmd = Command(name=name, description=description, admin_only=admin_only)
            cmd.callback = func
            self.commands[name] = cmd
            return func

        return decorator

    def load_extension(self, name):
        if self.hot_reloading and name in sys.modules:
            module = importlib.reload(sys.modules[name])
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

            obj = {
                "lxmf": message,
                "reply": reply,
                "sender": sender,
                "content": content,
                "hash": receipt,
            }
            msg = SimpleNamespace(**obj)

            if not self.is_admin(sender):
                allowed, reason = self.spam_protection.check_spam(sender)
                if not allowed:
                    self.send(sender, reason)
                    return

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
        self.delivery_callbacks.append(function)
        return function

    def request_page(
        self, destination_hash: str, page_path: str, field_data: Optional[Dict] = None
    ) -> Dict:
        try:
            dest_hash_bytes = bytes.fromhex(destination_hash)
            return self.transport.request_page(dest_hash_bytes, page_path, field_data)
        except Exception as e:
            self.logger.error("Error requesting page: %s", str(e))
            raise

    def cleanup(self):
        self.transport.cleanup()
