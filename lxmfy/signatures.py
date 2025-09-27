"""Signature management module for LXMFy.

This module provides cryptographic signing and verification capabilities
for LXMF messages using RNS Identity.
"""

import logging

import LXMF
import RNS

from .permissions import DefaultPerms

logger = logging.getLogger(__name__)

FIELD_SIGNATURE = 0xFA


class SignatureManager:
    """Manages cryptographic signing and verification of messages."""

    def __init__(
        self, bot, verification_enabled: bool = False, require_signatures: bool = False,
    ):
        """Initialize the SignatureManager.

        Args:
            bot: The LXMFBot instance.
            verification_enabled: Whether signature verification is enabled.
            require_signatures: Whether to reject unsigned messages.

        """
        self.bot = bot
        self.verification_enabled = verification_enabled
        self.require_signatures = require_signatures
        self.logger = logging.getLogger(__name__)

    def sign_message(self, message: LXMF.LXMessage, identity: RNS.Identity) -> bytes:
        """Sign an LXMF message using the provided identity.

        Args:
            message: The LXMF message to sign.
            identity: The RNS identity to use for signing.

        Returns:
            The cryptographic signature as bytes.

        """
        try:
            message_data = self._canonicalize_message(message)
            signature = identity.sign(message_data)
            return signature
        except Exception as e:
            self.logger.error("Failed to sign message: %s", str(e))
            raise

    def verify_message_signature(
        self,
        message: LXMF.LXMessage,
        signature: bytes,
        sender_hash: str,
        sender_identity: RNS.Identity = None,
    ) -> bool:
        """Verify a message signature against a sender identity.

        Args:
            message: The LXMF message that was signed.
            signature: The cryptographic signature to verify.
            sender_hash: Hex string of the sender's identity hash.
            sender_identity: Optional RNS Identity object (for testing when recall fails).

        Returns:
            True if signature is valid, False otherwise.

        """
        try:
            identity_to_use = sender_identity
            if identity_to_use is None:
                sender_hash_bytes = bytes.fromhex(sender_hash)
                identity_to_use = RNS.Identity.recall(sender_hash_bytes)
                if identity_to_use is None:
                    self.logger.warning(
                        "Could not recall identity for sender: %s", sender_hash,
                    )
                    return False
            message_data = self._canonicalize_message(message)
            return identity_to_use.validate(signature, message_data)
        except Exception as e:
            self.logger.error("Failed to verify message signature: %s", str(e))
            return False

    @staticmethod
    def _canonicalize_message(message: LXMF.LXMessage) -> bytes:
        """Create a canonical byte representation of a message for signing.

        Args:
            message: The LXMF message to canonicalize.

        Returns:
            Canonical byte representation of the message.

        """
        canonical_data = []
        if message.source_hash:
            canonical_data.append(b"source:" + message.source_hash)
        if message.destination_hash:
            canonical_data.append(b"dest:" + message.destination_hash)
        if message.content:
            canonical_data.append(b"content:" + message.content)
        if message.title:
            canonical_data.append(b"title:" + message.title)
        if hasattr(message, "timestamp") and message.timestamp:
            canonical_data.append(b"timestamp:" + str(message.timestamp).encode())
        if hasattr(message, "fields") and message.fields:
            sorted_fields = sorted(
                (k, v) for k, v in message.fields.items() if k != FIELD_SIGNATURE
            )
            for field_id, field_data in sorted_fields:
                canonical_data.append(
                    f"field_{field_id}:".encode() + str(field_data).encode(),
                )
        return b"|".join(canonical_data)

    def should_verify_message(self, sender: str) -> bool:
        """Determine if a message from the given sender should be verified.

        Args:
            sender: The sender's identity hash.

        Returns:
            True if the message should be verified, False otherwise.

        """
        if not self.verification_enabled:
            return False
        # Only skip verification if permissions are enabled and user has bypass permission
        if (hasattr(self.bot, "permissions") and self.bot.permissions.enabled and
            self.bot.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM)):
            return False
        return True

    def handle_unsigned_message(self, sender: str, message_hash: str) -> bool:
        """Handle a message that lacks a valid signature.

        Args:
            sender: The sender's identity hash.
            message_hash: The message hash for logging.

        Returns:
            True if the message should be processed anyway, False if it should be rejected.

        """
        if self.require_signatures:
            self.logger.warning(
                "Rejected unsigned message from %s (hash: %s)", sender, message_hash,
            )
            return False
        if self.verification_enabled:
            self.logger.info(
                "Accepted unsigned message from %s (hash: %s)", sender, message_hash,
            )
        return True


def sign_outgoing_message(bot, message: LXMF.LXMessage) -> LXMF.LXMessage:
    """Sign an outgoing message if signature verification is enabled.

    Args:
        bot: The LXMFBot instance.
        message: The LXMF message to sign.

    Returns:
        The message with signature field added if signing is enabled.

    """
    if (
        not hasattr(bot, "signature_manager")
        or not bot.signature_manager.verification_enabled
    ):
        return message
    try:
        signature = bot.signature_manager.sign_message(message, bot.identity)
        if not hasattr(message, "fields") or message.fields is None:
            message.fields = {}
        message.fields[FIELD_SIGNATURE] = signature
        logger.debug("Added cryptographic signature to outgoing message")
    except Exception as e:
        logger.error("Failed to sign outgoing message: %s", str(e))
    return message


def verify_incoming_message(bot, message: LXMF.LXMessage, sender: str) -> bool:
    """Verify the signature of an incoming message.

    Args:
        bot: The LXMFBot instance.
        message: The incoming LXMF message.
        sender: The sender's identity hash.

    Returns:
        True if message should be processed, False if it should be rejected.

    """
    if not hasattr(bot, "signature_manager"):
        return True
    sig_manager = bot.signature_manager
    if not sig_manager.should_verify_message(sender):
        return True
    signature = None
    if (
        hasattr(message, "fields")
        and message.fields
        and FIELD_SIGNATURE in message.fields
    ):
        signature = message.fields[FIELD_SIGNATURE]
    if signature is None:
        return sig_manager.handle_unsigned_message(
            sender,
            getattr(message, "hash", "unknown").hex()
            if hasattr(message, "hash")
            else "unknown",
        )
    if sig_manager.verify_message_signature(message, signature, sender):
        logger.debug("Verified cryptographic signature for message from %s", sender)
        return True
    logger.warning("Invalid cryptographic signature for message from %s", sender)
    return False
