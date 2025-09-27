"""Core module for LXMFy bot framework.

This module provides the main LXMFBot class that handles message routing,
command processing, and bot lifecycle management for LXMF-based bots on
the Reticulum Network.
"""

import importlib
import inspect
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from types import SimpleNamespace

import RNS
from LXMF import LXMessage, LXMRouter

from .attachments import Attachment, pack_attachment
from .cogs_core import load_cogs_from_directory
from .commands import Command
from .config import BotConfig
from .events import Event, EventManager, EventPriority
from .help import HelpSystem
from .middleware import MiddlewareContext, MiddlewareManager, MiddlewareType
from .moderation import SpamProtection
from .permissions import DefaultPerms, PermissionManager
from .scheduler import TaskScheduler
from .signatures import SignatureManager, sign_outgoing_message, verify_incoming_message
from .storage import JSONStorage, SQLiteStorage
from .transport import Transport
from .validation import format_validation_results, validate_bot


class LXMFBot:
    """Main bot class for handling LXMF messages and commands.

    This class manages the bot's lifecycle, including:
    - Message routing and delivery
    - Command registration and execution
    - Cog (extension) loading and management
    - Spam protection
    - Admin privileges
    """

    def __init__(self, **kwargs):
        """Initialize a new LXMFBot instance.

        Args:
            **kwargs: Override default configuration settings

        """
        self.config = BotConfig(**kwargs)
        self.commands = {}
        self.cogs = {}
        self.first_message_handlers = []
        self.delivery_callbacks = []
        self.receipts = []
        self.queue = Queue(maxsize=5)  # Outbound LXMF message queue
        self.announce_time = 600
        self.logger = logging.getLogger(__name__)
        self.thread_pool = ThreadPoolExecutor(
            max_workers=5,
        )  # For offloading CPU-bound or blocking I/O tasks
        self.scheduler = TaskScheduler(self)  # Initialize the scheduler

        self.config_path = os.path.join(os.getcwd(), "config")
        os.makedirs(self.config_path, exist_ok=True)

        if self.config.storage_type == "json":
            self.storage = JSONStorage(self.config.storage_path)
        elif self.config.storage_type == "sqlite":
            self.storage = SQLiteStorage(self.config.storage_path)

        self.permissions = PermissionManager(
            storage=self.storage,
            enabled=self.config.permissions_enabled,
        )

        self.events = EventManager(self.storage)

        self._register_builtin_events()

        self.middleware = MiddlewareManager()

        self.cogs_dir = os.path.join(self.config_path, self.config.cogs_dir)
        os.makedirs(self.cogs_dir, exist_ok=True)

        init_file = os.path.join(self.cogs_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w", encoding="utf-8").close()

        self.transport = Transport(self.storage)
        self.spam_protection = SpamProtection(
            storage=self.storage,
            bot=self,
            rate_limit=self.config.rate_limit,
            cooldown=self.config.cooldown,
            max_warnings=self.config.max_warnings,
            warning_timeout=self.config.warning_timeout,
        )

        if not self.config.test_mode:
            identity_file = os.path.join(self.config_path, "identity")
            if not os.path.isfile(identity_file):
                RNS.log("No Primary Identity file found, creating new...", RNS.LOG_INFO)
                identity = RNS.Identity(True)
                identity.to_file(identity_file)
            self.identity = RNS.Identity.from_file(identity_file)
            RNS.log("Loaded identity from file", RNS.LOG_INFO)

            # Initialize Reticulum (will raise exception if already running)
            try:
                RNS.Reticulum(loglevel=RNS.LOG_VERBOSE)
            except OSError as e:
                if "reinitialise" in str(e).lower():
                    # Reticulum already running, continue
                    pass
                else:
                    raise
            self.router = LXMRouter(identity=self.identity, storagepath=self.config_path)
            self.local = self.router.register_delivery_identity(
                self.identity,
                display_name=self.config.name,
            )
            self.router.register_delivery_callback(self._message_received)
            RNS.log(
                f"LXMF Router ready to receive on: {RNS.prettyhexrep(self.local.hash)}",
                RNS.LOG_INFO,
            )
        else:
            # Test mode - create mock components
            self.identity = RNS.Identity()  # Create a basic identity for testing
            self.router = None
            self.local = None

        self.announce_enabled = self.config.announce_enabled
        self.announce_time = self.config.announce

        if self.announce_enabled and not self.config.test_mode:
            # Schedule the announce task
            self.scheduler.add_task(
                "announce_task",
                self._announce,
                f"*/{self.announce_time // 60} * * * *",  # Convert seconds to minutes for cron
            )
            if self.config.announce_immediately:
                # Force an immediate announce if configured
                self._announce()
                RNS.log("Initial announce sent", RNS.LOG_INFO)

        self.admins = set(self.config.admins or [])
        self.hot_reloading = self.config.hot_reloading
        self.command_prefix = self.config.command_prefix

        self.help_system = HelpSystem(self)

        self.signature_manager = SignatureManager(
            self,
            verification_enabled=self.config.signature_verification_enabled,
            require_signatures=self.config.require_message_signatures,
        )

        if self.config.cogs_enabled:
            load_cogs_from_directory(self)

    def command(self, *args, **kwargs):
        """Decorator for registering commands.

        Args:
            *args: Command name (optional).
            **kwargs: Command attributes (name, description, admin_only).

        """

        def decorator(func):
            """The actual decorator that registers the command."""
            name = args[0] if len(args) > 0 else kwargs.get("name", func.__name__)

            description = kwargs.get("description", "No description provided")
            admin_only = kwargs.get("admin_only", False)

            cmd = Command(name=name, description=description, admin_only=admin_only)
            cmd.callback = func
            self.commands[name] = cmd
            return func

        return decorator

    def load_extension(self, name: str) -> None:
        """Load an extension (cog) by name.

        Args:
            name: The name of the extension to load.

        Raises:
            ValueError: If the module name contains invalid characters.
            ImportError: If the extension is missing setup function or fails to load.

        """
        if not re.match(r"^[a-zA-Z0-9_\.]+$", name):
            raise ValueError(f"Invalid module name format: {name}")

        if not name.startswith("cogs."):
            name = f"cogs.{name}"

        try:
            if self.hot_reloading and name in sys.modules:
                module = importlib.reload(sys.modules[name])
            else:
                module = importlib.import_module(name)

            if not hasattr(module, "setup"):
                raise ImportError(f"Extension {name} missing setup function")
            module.setup(self)
        except ImportError as e:
            raise ImportError(f"Failed to load extension {name}: {e!s}") from e

    def add_cog(self, cog):
        """Add a cog to the bot.

        Args:
            cog: The cog instance to add.

        """
        self.cogs[cog.__class__.__name__] = cog
        for _name, method in inspect.getmembers(
            cog,
            predicate=lambda x: hasattr(x, "command"),
        ):
            if _name.startswith("_") or _name == "bot":
                continue

            try:
                cmd_descriptor = method.command

                if hasattr(cmd_descriptor, "__get__") and hasattr(
                    cmd_descriptor, "name",
                ):
                    cmd = cmd_descriptor.__get__(cog, cog.__class__)
                elif hasattr(cmd_descriptor, "name"):
                    cmd = cmd_descriptor
                    if cmd.callback is None:
                        cmd.callback = method
                else:
                    self.logger.warning(
                        "Unexpected command type for %s: %s",
                        _name,
                        type(cmd_descriptor),
                    )
                    continue

                self.commands[cmd.name] = cmd
            except Exception as e:
                self.logger.error(
                    "Error adding command %s from cog %s: %s",
                    _name,
                    cog.__class__.__name__,
                    e,
                )
                continue

    def is_admin(self, sender):
        """Check if a sender is an admin.

        Args:
            sender: The sender's identity hash.

        Returns:
            True if the sender is an admin, False otherwise.

        """
        return sender in self.admins

    def _register_builtin_events(self):
        """Register built-in event handlers."""

        @self.events.on("message_received", EventPriority.HIGHEST)
        def handle_message(event):
            """Handles incoming messages, performing spam checks."""
            sender = event.data["sender"]
            if not self.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM):
                allowed, msg = self.spam_protection.check_spam(sender)
                if not allowed:
                    event.cancel()
                    self.send(sender, msg)
                    return

    def _process_message(self, message, sender):
        """Process an incoming message."""
        try:
            content = message.content.decode("utf-8")
            receipt = RNS.hexrep(message.hash, delimit=False)

            def reply(response, **kwargs):
                """Helper function to reply to a message."""
                self.send(sender, response, **kwargs)

            if self.config.first_message_enabled:
                first_messages = self.storage.get("first_messages", {})
                if sender not in first_messages:
                    first_messages[sender] = True
                    self.storage.set("first_messages", first_messages)
                    for handler in self.first_message_handlers:
                        if handler(sender, message):
                            break
                    return

            if not self.permissions.has_permission(sender, DefaultPerms.USE_BOT):
                return

            msg_ctx = {
                "lxmf": message,
                "reply": reply,
                "sender": sender,
                "content": content,
                "hash": receipt,
            }
            msg = SimpleNamespace(**msg_ctx)

            ctx = MiddlewareContext(MiddlewareType.PRE_COMMAND, msg)
            if self.middleware.execute(MiddlewareType.PRE_COMMAND, ctx) is None:
                return

            if self.command_prefix is None or content.startswith(self.command_prefix):
                command_name = (
                    content.split()[0][len(self.command_prefix) :]
                    if self.command_prefix
                    else content.split()[0]
                )
                if command_name in self.commands:
                    cmd = self.commands[command_name]

                    if not self.permissions.has_permission(sender, cmd.permissions):
                        self.send(
                            sender, "You don't have permission to use this command.",
                        )
                        return

                    try:
                        args = content.split()[1:] if len(content.split()) > 1 else []
                        msg.args = args
                        msg.is_admin = sender in self.admins

                        if cmd.threaded:
                            self.thread_pool.submit(cmd.callback, msg)
                            # Optionally, send an immediate "processing..." message to the user
                            # msg.reply("Processing your request in the background...")
                        else:
                            cmd.callback(msg)

                        self.middleware.execute(MiddlewareType.POST_COMMAND, msg)
                        return

                    except Exception as e:
                        self.logger.error(
                            "Error executing command %s: %s", command_name, str(e),
                        )
                        self.send(sender, "Error executing command: %s", str(e))
                        return

            for callback in self.delivery_callbacks:
                callback(msg)

        except Exception as e:
            self.logger.error("Error processing message: %s", str(e))

    def _message_received(self, message):
        """Handle received messages."""
        try:
            sender = RNS.hexrep(message.source_hash, delimit=False)
            receipt = RNS.hexrep(message.hash, delimit=False)

            if receipt in self.receipts:
                return

            self.receipts.append(receipt)
            if len(self.receipts) > 100:
                self.receipts = self.receipts[-100:]

            event_data = {
                "message": message,
                "sender": sender,
                "receipt": receipt,
            }

            ctx = MiddlewareContext(MiddlewareType.PRE_EVENT, event_data)
            if self.middleware.execute(MiddlewareType.PRE_EVENT, ctx) is None:
                return

            event = Event("message_received", event_data)
            self.events.dispatch(event)

            if not event.cancelled:
                # Verify message signature if enabled
                if verify_incoming_message(self, message, sender):
                    self._process_message(message, sender)
                else:
                    RNS.log(
                        f"Rejected message from {sender} due to invalid signature",
                        RNS.LOG_WARNING,
                    )

        except Exception as e:
            self.logger.error("Error handling received message: %s", str(e))

    def _announce(self):
        """Send an announce if the configured interval has passed."""
        if self.announce_time == 0 or not self.announce_enabled or self.config.test_mode:
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
            RNS.log(
                f"Announcement sent, next announce in {self.announce_time} seconds",
                RNS.LOG_INFO,
            )

    def send(
        self,
        destination: str,
        message: str,
        title: str = "Reply",
        lxmf_fields: dict | None = None,
    ):
        """Send a message to a destination, optionally with custom LXMF fields.

        Args:
            destination: The destination hash.
            message: The message content (will be utf-8 encoded).
            title: The message title (optional, will be utf-8 encoded).
            lxmf_fields: Optional dictionary of LXMF fields.

        """
        if self.config.test_mode:
            # In test mode, just queue a mock message
            from types import SimpleNamespace
            mock_message = SimpleNamespace()
            mock_message.content = message.encode("utf-8")
            mock_message.title = title.encode("utf-8") if title else None
            mock_message.fields = lxmf_fields
            self.queue.put(mock_message)
            return

        try:
            dest_hash_bytes = bytes.fromhex(destination)
        except ValueError:
            RNS.log(f"Invalid destination hash format: {destination}", RNS.LOG_ERROR)
            return

        if len(dest_hash_bytes) != RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
            RNS.log(f"Invalid destination hash length for {destination}", RNS.LOG_ERROR)
            return

        identity_instance = RNS.Identity.recall(dest_hash_bytes)
        if identity_instance is None:
            RNS.log(
                f"Could not recall an Identity for {destination}. Requesting path...",
                RNS.LOG_ERROR,
            )
            RNS.Transport.request_path(dest_hash_bytes)
            RNS.log(
                "Path requested. If the network knows a path, you will receive an announce shortly.",
                RNS.LOG_INFO,
            )
            return

        lxmf_destination_obj = RNS.Destination(
            identity_instance,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "lxmf",
            "delivery",
        )

        # Ensure message and title are bytes
        message_bytes = message.encode("utf-8")
        title_bytes = title.encode("utf-8") if title else None

        lxm = LXMessage(
            lxmf_destination_obj,
            self.local,
            message_bytes,
            title=title_bytes,
            desired_method=LXMessage.DIRECT,
            fields=lxmf_fields,
        )

        # Sign the message if signature verification is enabled
        lxm = sign_outgoing_message(self, lxm)

        lxm.try_propagation_on_fail = True
        self.queue.put(lxm)
        RNS.log(f"Message queued for {destination}", RNS.LOG_DEBUG)

    def send_with_attachment(
        self,
        destination: str,
        message: str,
        attachment: Attachment,
        title: str = "Reply",
    ):
        """Send a message with an attachment to a destination."""
        attachment_specific_fields = pack_attachment(attachment)
        self.send(
            destination, message, title=title, lxmf_fields=attachment_specific_fields,
        )

    def run(self, delay=10):
        """Run the bot"""
        self.scheduler.start()  # Start the scheduler
        try:
            while True:
                for _i in list(self.queue.queue):
                    lxm = self.queue.get()
                    self.router.handle_outbound(lxm)

                time.sleep(delay)

        except KeyboardInterrupt:
            self.cleanup()  # Call cleanup on KeyboardInterrupt

    def received(self, function):
        """Decorator for registering delivery callbacks.

        Args:
            function: The function to call when a message is delivered.

        """
        self.delivery_callbacks.append(function)
        return function

    def request_page(
        self,
        destination_hash: str,
        page_path: str,
        field_data: dict | None = None,
    ) -> dict:
        """Request a page from a destination.

        Args:
            destination_hash: The destination hash.
            page_path: The path to the page.
            field_data: Optional field data to send with the request.

        Returns:
            The response from the destination.

        """
        try:
            dest_hash_bytes = bytes.fromhex(destination_hash)
            return self.transport.request_page(dest_hash_bytes, page_path, field_data)
        except Exception as e:
            self.logger.error("Error requesting page: %s", str(e))
            raise

    def cleanup(self):
        """Clean up resources."""
        self.transport.cleanup()
        self.thread_pool.shutdown(wait=True)
        self.scheduler.stop()  # Stop the scheduler

    def on_first_message(self):
        """Decorator for registering first message handlers"""

        def decorator(func):
            """Registers a function to be called on the first message from a sender."""
            self.first_message_handlers.append(func)
            return func

        return decorator

    def validate(self) -> str:
        """Run validation checks and return formatted results."""
        results = validate_bot(self)
        return format_validation_results(results)
