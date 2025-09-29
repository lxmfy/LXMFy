"""Tests for LXMFy signature functionality."""

from unittest.mock import MagicMock, patch

import pytest
import RNS

from lxmfy.signatures import (
    FIELD_SIGNATURE,
    SignatureManager,
    sign_outgoing_message,
    verify_incoming_message,
)


class TestSignatureManager:
    """Test SignatureManager class."""

    def test_init(self):
        """Test SignatureManager initialization."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot, verification_enabled=True, require_signatures=True)

        assert sig_manager.bot == bot
        assert sig_manager.verification_enabled is True
        assert sig_manager.require_signatures is True

    def test_init_defaults(self):
        """Test SignatureManager initialization with defaults."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        assert sig_manager.verification_enabled is False
        assert sig_manager.require_signatures is False

    def test_sign_message_success(self):
        """Test successful message signing."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)
        identity = RNS.Identity()

        # Create a proper mock message
        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"
        mock_message.destination_hash = b"dest_hash"
        mock_message.content = b"test content"
        mock_message.title = b"test title"
        mock_message.fields = {}

        # Mock the canonicalize method to return predictable data
        expected_data = b"source:source_hash|dest:dest_hash|content:test content|title:test title"
        with patch.object(sig_manager, "_canonicalize_message", return_value=expected_data):
            result = sig_manager.sign_message(mock_message, identity)

            assert isinstance(result, bytes)
            assert len(result) > 0  # Should have a signature

    def test_sign_message_exception(self):
        """Test sign_message with exception."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)
        identity = RNS.Identity()
        mock_message = MagicMock()

        # Mock the _canonicalize_message to raise an exception
        with patch.object(sig_manager, "_canonicalize_message", side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                sig_manager.sign_message(mock_message, identity)

    def test_verify_message_signature_success(self):
        """Test successful signature verification."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)
        identity = RNS.Identity()

        # Create a message and sign it
        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"
        mock_message.destination_hash = b"dest_hash"
        mock_message.content = b"test content"
        mock_message.title = b"test title"
        mock_message.fields = {}

        # Sign the message
        signature = sig_manager.sign_message(mock_message, identity)
        mock_message.fields[FIELD_SIGNATURE] = signature

        # Verify the signature
        sender_hash = RNS.hexrep(identity.hash, delimit=False)
        result = sig_manager.verify_message_signature(mock_message, signature, sender_hash, identity)

        assert result is True

    def test_verify_message_signature_invalid(self):
        """Test signature verification with invalid signature."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)
        identity = RNS.Identity()

        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"
        mock_message.destination_hash = b"dest_hash"
        mock_message.content = b"test content"
        mock_message.title = b"test title"
        mock_message.fields = {}

        # Use a fake signature
        fake_signature = b"fake_signature"

        sender_hash = RNS.hexrep(identity.hash, delimit=False)
        result = sig_manager.verify_message_signature(mock_message, fake_signature, sender_hash, identity)

        assert result is False

    def test_verify_message_signature_no_identity_recall(self):
        """Test signature verification when identity recall fails."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"
        mock_message.destination_hash = b"dest_hash"
        mock_message.content = b"test content"
        mock_message.title = b"test title"

        # Use a non-existent hash
        fake_hash = "nonexistent"
        fake_signature = b"fake_signature"

        result = sig_manager.verify_message_signature(mock_message, fake_signature, fake_hash)

        assert result is False

    def test_verify_message_signature_exception(self):
        """Test signature verification with exception."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"

        # Mock _canonicalize_message to raise exception
        with patch.object(sig_manager, "_canonicalize_message", side_effect=Exception("Test error")):
            result = sig_manager.verify_message_signature(mock_message, b"signature", "fake_hash")
            assert result is False

    def test_canonicalize_message_basic(self):
        """Test basic message canonicalization."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        mock_message = MagicMock()
        mock_message.source_hash = b"source_hash"
        mock_message.destination_hash = b"dest_hash"
        mock_message.content = b"test content"
        mock_message.title = b"test title"
        mock_message.timestamp = 1234567890
        mock_message.fields = {1: b"field1", FIELD_SIGNATURE: b"signature"}

        result = sig_manager._canonicalize_message(mock_message)

        expected_parts = [
            b"source:736f757263655f68617368",  # hex of b"source_hash"
            b"dest:646573745f68617368",      # hex of b"dest_hash"
            b"content:test content",
            b"title:test title",
            b"timestamp:1234567890",
            b"field_1:b'field1'",
        ]
        expected = b"|".join(expected_parts)

        assert result == expected

    def test_canonicalize_message_minimal(self):
        """Test message canonicalization with minimal fields."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        mock_message = MagicMock()
        mock_message.source_hash = None
        mock_message.destination_hash = None
        mock_message.content = None
        mock_message.title = None
        mock_message.timestamp = None
        mock_message.fields = None

        result = sig_manager._canonicalize_message(mock_message)

        assert result == b""

    def test_should_verify_message_enabled(self):
        """Test should_verify_message when verification is enabled."""
        bot = MagicMock()
        # Remove permissions attribute to simulate no permissions system
        del bot.permissions
        sig_manager = SignatureManager(bot, verification_enabled=True)

        result = sig_manager.should_verify_message("sender_hash")
        assert result is True

    def test_should_verify_message_disabled(self):
        """Test should_verify_message when verification is disabled."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot, verification_enabled=False)

        result = sig_manager.should_verify_message("sender_hash")
        assert result is False

    def test_should_verify_message_bypass_permission(self):
        """Test should_verify_message with bypass permission."""
        bot = MagicMock()
        bot.permissions = MagicMock()
        bot.permissions.enabled = True
        bot.permissions.has_permission.return_value = True

        sig_manager = SignatureManager(bot, verification_enabled=True)

        result = sig_manager.should_verify_message("sender_hash")
        assert result is False
        bot.permissions.has_permission.assert_called_once()

    def test_should_verify_message_no_bypass(self):
        """Test should_verify_message without bypass permission."""
        bot = MagicMock()
        bot.permissions = MagicMock()
        bot.permissions.enabled = True
        bot.permissions.has_permission.return_value = False

        sig_manager = SignatureManager(bot, verification_enabled=True)

        result = sig_manager.should_verify_message("sender_hash")
        assert result is True

    def test_handle_unsigned_message_require_signatures(self):
        """Test handle_unsigned_message when signatures are required."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot, require_signatures=True)

        result = sig_manager.handle_unsigned_message("sender_hash", "message_hash")
        assert result is False

    def test_handle_unsigned_message_verification_enabled(self):
        """Test handle_unsigned_message when verification is enabled but not required."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot, verification_enabled=True, require_signatures=False)

        result = sig_manager.handle_unsigned_message("sender_hash", "message_hash")
        assert result is True

    def test_handle_unsigned_message_disabled(self):
        """Test handle_unsigned_message when verification is disabled."""
        bot = MagicMock()
        sig_manager = SignatureManager(bot)

        result = sig_manager.handle_unsigned_message("sender_hash", "message_hash")
        assert result is True


class TestSignatureFunctions:
    """Test signature utility functions."""

    def test_sign_outgoing_message_enabled(self):
        """Test sign_outgoing_message when signature verification is enabled."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.verification_enabled = True
        bot.signature_manager.sign_message.return_value = b"signature"
        bot.identity = RNS.Identity()

        mock_message = MagicMock()
        mock_message.fields = {}

        result = sign_outgoing_message(bot, mock_message)

        assert result == mock_message
        assert mock_message.fields[FIELD_SIGNATURE] == b"signature"
        bot.signature_manager.sign_message.assert_called_once()

    def test_sign_outgoing_message_disabled(self):
        """Test sign_outgoing_message when signature verification is disabled."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.verification_enabled = False

        mock_message = MagicMock()

        result = sign_outgoing_message(bot, mock_message)

        assert result == mock_message
        bot.signature_manager.sign_message.assert_not_called()

    def test_sign_outgoing_message_no_manager(self):
        """Test sign_outgoing_message when no signature manager exists."""
        bot = MagicMock()
        # No signature_manager attribute

        mock_message = MagicMock()

        result = sign_outgoing_message(bot, mock_message)

        assert result == mock_message

    def test_sign_outgoing_message_exception(self):
        """Test sign_outgoing_message with exception."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.verification_enabled = True
        bot.signature_manager.sign_message.side_effect = Exception("Sign error")
        bot.identity = RNS.Identity()

        mock_message = MagicMock()
        mock_message.fields = {}

        result = sign_outgoing_message(bot, mock_message)

        assert result == mock_message
        # Should not crash, just return the message

    def test_verify_incoming_message_should_verify(self):
        """Test verify_incoming_message when verification should happen."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.should_verify_message.return_value = True
        bot.signature_manager.verify_message_signature.return_value = True

        mock_message = MagicMock()
        mock_message.fields = {FIELD_SIGNATURE: b"signature"}

        result = verify_incoming_message(bot, mock_message, "sender_hash")

        assert result is True
        bot.signature_manager.verify_message_signature.assert_called_once()

    def test_verify_incoming_message_skip_verification(self):
        """Test verify_incoming_message when verification should be skipped."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.should_verify_message.return_value = False

        mock_message = MagicMock()

        result = verify_incoming_message(bot, mock_message, "sender_hash")

        assert result is True
        bot.signature_manager.verify_message_signature.assert_not_called()

    def test_verify_incoming_message_no_signature(self):
        """Test verify_incoming_message when message has no signature."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.should_verify_message.return_value = True
        bot.signature_manager.handle_unsigned_message.return_value = True

        mock_message = MagicMock()
        mock_message.fields = {}  # No signature field

        result = verify_incoming_message(bot, mock_message, "sender_hash")

        assert result is True
        bot.signature_manager.handle_unsigned_message.assert_called_once()

    def test_verify_incoming_message_invalid_signature(self):
        """Test verify_incoming_message when signature is invalid."""
        bot = MagicMock()
        bot.signature_manager = MagicMock()
        bot.signature_manager.should_verify_message.return_value = True
        bot.signature_manager.verify_message_signature.return_value = False

        mock_message = MagicMock()
        mock_message.fields = {FIELD_SIGNATURE: b"signature"}

        result = verify_incoming_message(bot, mock_message, "sender_hash")

        assert result is False

    def test_verify_incoming_message_no_manager(self):
        """Test verify_incoming_message when no signature manager exists."""
        bot = MagicMock()
        # Remove signature_manager attribute to simulate it not existing
        del bot.signature_manager

        mock_message = MagicMock()

        result = verify_incoming_message(bot, mock_message, "sender_hash")

        assert result is True
