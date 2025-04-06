"""
Core module for LXMFy bot framework.

This module provides the main LXMFBot class that handles message routing,
command processing, and bot lifecycle management for LXMF-based bots on
the Reticulum Network.
"""

# Standard library imports
import importlib
import inspect
import logging
import os
import sys
import time
from queue import Queue
from types import SimpleNamespace
from typing import Optional

# Reticulum and LXMF imports
import RNS
from LXMF import LXMessage, LXMRouter

from .attachments import Attachment, pack_attachment

# Local imports
from .commands import Command
from .config import BotConfig
from .events import Event, EventManager, EventPriority
from .help import HelpSystem
from .middleware import MiddlewareContext, MiddlewareManager, MiddlewareType
from .moderation import SpamProtection
from .permissions import DefaultPerms, PermissionManager
from .storage import JSONStorage, SQLiteStorage, Storage
from .transport import Transport
from .validation import format_validation_results, validate_bot


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
        self.config = BotConfig(**kwargs)

        # Set up storage with configured backend
        storage_type = kwargs.get("storage_type", self.config.storage_type)
        storage_path = kwargs.get("storage_path", self.config.storage_path)

        if storage_type == "sqlite":
            self.storage = Storage(SQLiteStorage(storage_path))
        else:  # default to json
            self.storage = Storage(JSONStorage(storage_path))

        # Initialize spam protection with config values
        self.spam_protection = SpamProtection(
            storage=self.storage,
            bot=self,
            rate_limit=self.config.rate_limit,
            cooldown=self.config.cooldown,
            max_warnings=self.config.max_warnings,
            warning_timeout=self.config.warning_timeout,
        )

        # Setup paths
        self.config_path = os.path.join(os.getcwd(), "config")
        os.makedirs(self.config_path, exist_ok=True)

        # Setup cogs
        self.cogs_dir = os.path.join(self.config_path, self.config.cogs_dir)
        os.makedirs(self.cogs_dir, exist_ok=True)

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(self.cogs_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w", encoding="utf-8").close()

        # Setup identity
        identity_file = os.path.join(self.config_path, "identity")
        if not os.path.isfile(identity_file):
            RNS.log("No Primary Identity file found, creating new...", RNS.LOG_INFO)
            identity = RNS.Identity(True)
            identity.to_file(identity_file)
        self.identity = RNS.Identity.from_file(identity_file)
        RNS.log("Loaded identity from file", RNS.LOG_INFO)

        # Initialize LXMF router
        RNS.Reticulum(loglevel=RNS.LOG_VERBOSE)
        self.router = LXMRouter(identity=self.identity, storagepath=self.config_path)
        self.local = self.router.register_delivery_identity(
            self.identity, display_name=self.config.name
        )
        self.router.register_delivery_callback(self._message_received)
        RNS.log(
            f"LXMF Router ready to receive on: {RNS.prettyhexrep(self.local.hash)}",
            RNS.LOG_INFO,
        )

        # Set announce settings from config
        self.announce_enabled = self.config.announce_enabled
        self.announce_time = self.config.announce

        # Handle initial announce
        if self.config.announce_immediately and self.announce_enabled:
            announce_file = os.path.join(self.config_path, "announce")
            if os.path.isfile(announce_file):
                os.remove(announce_file)
                RNS.log("Announcing now. Timer reset.", RNS.LOG_INFO)
            self.local.announce()
            RNS.log("Initial announce sent", RNS.LOG_INFO)

        # Initialize bot state
        self.commands = {}
        self.cogs = {}
        self.admins = set(self.config.admins or [])
        self.hot_reloading = self.config.hot_reloading
        self.command_prefix = self.config.command_prefix

        # Initialize services
        self.transport = Transport(storage=self.storage)

        # Initialize help system
        self.help_system = HelpSystem(self)

        # Initialize permission manager
        self.permissions = PermissionManager(
            storage=self.storage,
            enabled=self.config.permissions_enabled
        )

        # Add admins to admin role
        for admin in self.admins:
            self.permissions.assign_role(admin, "admin")

        # Add first message handler storage
        self.first_message_handlers = []
        self.first_message_enabled = kwargs.get("first_message_enabled", True)

        # Initialize event system
        self.events = EventManager(self.storage)

        # Register built-in events
        self._register_builtin_events()

        # Initialize middleware
        self.middleware = MiddlewareManager()

    def command(self, *args, **kwargs):
        def decorator(func):
            name = args[0] if len(args) > 0 else kwargs.get("name", func.__name__)

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
        for _name, method in inspect.getmembers(
            cog, predicate=lambda x: hasattr(x, "_command")
        ):
            cmd = method._command
            cmd.callback = method
            self.commands[cmd.name] = cmd

    def is_admin(self, sender):
        return sender in self.admins

    def _register_builtin_events(self):
        """Register built-in event handlers"""
        @self.events.on("message_received", EventPriority.HIGHEST)
        def handle_message(event):
            sender = event.data["sender"]

            # Check spam protection
            if not self.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM):
                allowed, msg = self.spam_protection.check_spam(sender)
                if not allowed:
                    event.cancel()
                    self.send(sender, msg)
                    return

    def _process_message(self, message, sender):
        """Process an incoming message"""
        try:
            content = message.content.decode('utf-8')
            receipt = RNS.hexrep(message.hash, delimit=False)

            def reply(response):
                self.send(sender, response)

            # Check if this is a first message from the user
            if self.config.first_message_enabled:
                first_messages = self.storage.get("first_messages", {})
                if sender not in first_messages:
                    first_messages[sender] = True
                    self.storage.set("first_messages", first_messages)
                    for handler in self.first_message_handlers:
                        if handler(sender, message):
                            break
                    return  # Return after handling first message

            # Check basic bot permission
            if not self.permissions.has_permission(sender, DefaultPerms.USE_BOT):
                return

            # Create message context
            msg_ctx = {
                "lxmf": message,
                "reply": reply,
                "sender": sender,
                "content": content,
                "hash": receipt,
            }
            msg = SimpleNamespace(**msg_ctx)

            # Run through pre-command middleware
            ctx = MiddlewareContext(MiddlewareType.PRE_COMMAND, msg)
            if self.middleware.execute(MiddlewareType.PRE_COMMAND, ctx) is None:
                return

            # Process commands
            if self.command_prefix is None or content.startswith(self.command_prefix):
                command_name = (
                    content.split()[0][len(self.command_prefix):]
                    if self.command_prefix
                    else content.split()[0]
                )
                if command_name in self.commands:
                    cmd = self.commands[command_name]

                    if not self.permissions.has_permission(sender, cmd.permissions):
                        self.send(sender, "You don't have permission to use this command.")
                        return

                    try:
                        args = content.split()[1:] if len(content.split()) > 1 else []
                        msg.args = args
                        msg.is_admin = sender in self.admins

                        cmd.callback(msg)

                        # Run post-command middleware
                        self.middleware.execute(MiddlewareType.POST_COMMAND, msg)
                        return

                    except Exception as e:
                        self.logger.error(f"Error executing command {command_name}: {str(e)}")
                        self.send(sender, f"Error executing command: {str(e)}")
                        return

            # Run delivery callbacks only if not a command
            for callback in self.delivery_callbacks:
                callback(msg)

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def _message_received(self, message):
        """Handle received messages"""
        try:
            sender = RNS.hexrep(message.source_hash, delimit=False)
            receipt = RNS.hexrep(message.hash, delimit=False)

            # Check if message was already processed
            if receipt in self.receipts:
                return

            # Add to receipts list
            self.receipts.append(receipt)
            if len(self.receipts) > 100:
                self.receipts = self.receipts[-100:]

            # Create event data
            event_data = {
                "message": message,
                "sender": sender,
                "receipt": receipt
            }

            # Run through middleware first
            ctx = MiddlewareContext(MiddlewareType.PRE_EVENT, event_data)
            if self.middleware.execute(MiddlewareType.PRE_EVENT, ctx) is None:
                return

            # Dispatch message received event and process message
            event = Event("message_received", event_data)
            self.events.dispatch(event)

            # Only process message if event wasn't cancelled
            if not event.cancelled:
                self._process_message(message, sender)

        except Exception as e:
            self.logger.error(f"Error handling received message: {str(e)}")

    def _announce(self):
        """Send an announce if the configured interval has passed."""
        if self.announce_time == 0 or not self.announce_enabled:
            RNS.log("Announcements disabled", RNS.LOG_DEBUG)
            return

        announce_path = os.path.join(self.config_path, "announce")
        if os.path.isfile(announce_path):
            with open(announce_path) as f:
                try:
                    announce = int(f.readline())
                except ValueError:
                    announce = 0
        else:
            announce = 0

        if announce > int(time.time()):
            RNS.log("Recent announcement", RNS.LOG_DEBUG)
        else:
            with open(announce_path, "w+") as af:
                next_announce = int(time.time()) + self.announce_time
                af.write(str(next_announce))
            self.local.announce()
            RNS.log(f"Announcement sent, next announce in {self.announce_time} seconds", RNS.LOG_INFO)

    def send(self, destination, message, title="Reply"):
        try:
            hash = bytes.fromhex(destination)
        except Exception:
            RNS.log("Invalid destination hash", RNS.LOG_ERROR)
            return

        if len(hash) != RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
            RNS.log("Invalid destination hash length", RNS.LOG_ERROR)
        else:
            id = RNS.Identity.recall(hash)
            if id is None:
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

    def send_with_attachment(self, destination: str, message: str, attachment: Attachment, title: str = "Reply"):
        try:
            hash = bytes.fromhex(destination)
            if len(hash) != RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
                RNS.log("Invalid destination hash length", RNS.LOG_ERROR)
                return

            id = RNS.Identity.recall(hash)
            if id is None:
                RNS.log("Could not recall Identity, requesting path...", RNS.LOG_ERROR)
                RNS.Transport.request_path(hash)
                return

            lxmf_destination = RNS.Destination(
                id, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery"
            )

            fields = pack_attachment(attachment)

            lxm = LXMessage(
                lxmf_destination,
                self.local,
                message,
                title=title,
                desired_method=LXMessage.DIRECT,
                fields=fields
            )
            lxm.try_propagation_on_fail = True
            self.queue.put(lxm)

        except Exception as e:
            self.logger.error(f"Error sending message with attachment: {str(e)}")

    def run(self, delay=10):
        """Run the bot"""
        try:
            while True:
                # Process outbound queue
                for _i in list(self.queue.queue):
                    lxm = self.queue.get()
                    self.router.handle_outbound(lxm)

                self._announce()
                time.sleep(delay)

        except KeyboardInterrupt:
            self.transport.cleanup()

    def received(self, function):
        self.delivery_callbacks.append(function)
        return function

    def request_page(
        self, destination_hash: str, page_path: str, field_data: Optional[dict] = None
    ) -> dict:
        try:
            dest_hash_bytes = bytes.fromhex(destination_hash)
            return self.transport.request_page(dest_hash_bytes, page_path, field_data)
        except Exception as e:
            self.logger.error("Error requesting page: %s", str(e))
            raise

    def cleanup(self):
        self.transport.cleanup()

    def on_first_message(self):
        """Decorator for registering first message handlers"""
        def decorator(func):
            self.first_message_handlers.append(func)
            return func
        return decorator

    def validate(self) -> str:
        """Run validation checks and return formatted results."""
        results = validate_bot(self)
        return format_validation_results(results)
