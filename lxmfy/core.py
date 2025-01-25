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
from typing import Optional, Dict

# Reticulum and LXMF imports
import RNS
from LXMF import LXMRouter, LXMessage

# Local imports
from .commands import Command
from .moderation import SpamProtection
from .transport import Transport
from .storage import JSONStorage, Storage, SQLiteStorage
from .help import HelpSystem
from .permissions import PermissionManager, DefaultPerms
from .config import BotConfig
from .validation import validate_bot, format_validation_results
from .events import EventManager, Event, EventPriority


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

        # Handle immediate announce
        if self.config.announce_immediately:
            announce_file = os.path.join(self.config_path, "announce")
            if os.path.isfile(announce_file):
                os.remove(announce_file)
                RNS.log("Announcing now. Timer reset.", RNS.LOG_INFO)

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

        # Initialize bot state
        self._announce()
        self.commands = {}
        self.cogs = {}
        self.admins = set(self.config.admins or [])
        self.hot_reloading = self.config.hot_reloading
        self.announce_time = self.config.announce
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

    def _register_builtin_events(self):
        """Register built-in event handlers"""
        @self.events.on("message_received", EventPriority.HIGHEST)
        def handle_message(event):
            message = event.data["message"]
            sender = event.data["sender"]
            
            # Check spam protection
            if not self.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM):
                allowed, msg = self.spam_protection.check_spam(sender)
                if not allowed:
                    event.cancel()
                    self.send(sender, msg)
                    return
                    
            # Process message
            self._process_message(message, sender)

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
                            return
            
            # Check spam protection
            if not self.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM):
                allowed, reason = self.spam_protection.check_spam(sender)
                if not allowed:
                    reply(reason)
                    return
            
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

            # Process commands
            if self.command_prefix is None or content.startswith(self.command_prefix):
                command_name = (
                    content.split()[0][len(self.command_prefix):]
                    if self.command_prefix
                    else content.split()[0]
                )
                if command_name in self.commands:
                    cmd = self.commands[command_name]
                    
                    # Check command permissions
                    if not self.permissions.has_permission(sender, cmd.permissions):
                        self.send(sender, "You don't have permission to use this command.")
                        return

                    # Create command context
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
                        
                        # Dispatch command executed event
                        event = Event("command_executed", {
                            "command": command_name,
                            "sender": sender,
                            "args": ctx.args,
                            "content": content
                        })
                        self.events.dispatch(event)
                        
                    except Exception as e:
                        self.logger.error(
                            f"Error executing command {command_name}: {str(e)}"
                        )
                        self.send(sender, f"Error executing command: {str(e)}")

            # Run delivery callbacks
            for callback in self.delivery_callbacks:
                callback(msg)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def _message_received(self, message):
        """Handle received messages"""
        try:
            sender = RNS.hexrep(message.source_hash, delimit=False)
            receipt = RNS.hexrep(message.hash, delimit=False)
            
            if receipt in self.receipts:
                return
                
            # Add to receipts list
            self.receipts.append(receipt)
            if len(self.receipts) > 100:
                self.receipts = self.receipts[-100:]
            
            # Dispatch message received event
            event = Event("message_received", {
                "message": message,
                "sender": sender,
                "receipt": receipt
            })
            self.events.dispatch(event)
            
            # Process the message
            self._process_message(message, sender)
            
        except Exception as e:
            self.logger.error(f"Error handling received message: {str(e)}")

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
        except Exception:
            RNS.log("Invalid destination hash", RNS.LOG_ERROR)
            return

        if not len(hash) == RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
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

    def run(self, delay=10):
        """Run the bot"""
        try:
            while True:
                # Process outbound queue
                for i in list(self.queue.queue):
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
