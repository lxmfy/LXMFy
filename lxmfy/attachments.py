from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import LXMF


class AttachmentType(IntEnum):
    """
    Enumerates the different types of attachments supported.

    FILE: Represents a generic file attachment.
    IMAGE: Represents an image attachment.
    AUDIO: Represents an audio attachment.
    """

    FILE = 0x05
    IMAGE = 0x06
    AUDIO = 0x07


@dataclass
class Attachment:
    """
    Represents a generic attachment.

    Attributes:
        type: The type of the attachment (AttachmentType).
        name: The name of the attachment.
        data: The binary data of the attachment.
        format: Optional format specifier (e.g., "png" for images).
    """

    type: AttachmentType
    name: str
    data: bytes
    format: Optional[str] = None


def create_file_attachment(filename: str, data: bytes) -> list:
    """Create a file attachment list."""
    return [filename, data]


def create_image_attachment(format: str, data: bytes) -> list:
    """Create an image attachment list."""
    return [format, data]


def create_audio_attachment(mode: int, data: bytes) -> list:
    """Create an audio attachment list."""
    return [mode, data]


def pack_attachment(attachment: Attachment) -> dict:
    """
    Packs an Attachment object into a dictionary suitable for LXMF transmission.

    Args:
        attachment: The Attachment object to pack.

    Returns:
        A dictionary containing the attachment data, formatted according to the
        attachment type.

    Raises:
        ValueError: If the attachment type is not supported.
    """
    if attachment.type == AttachmentType.FILE:
        return {LXMF.FIELD_FILE_ATTACHMENTS: [create_file_attachment(attachment.name, attachment.data)]}
    if attachment.type == AttachmentType.IMAGE:
        return {LXMF.FIELD_IMAGE: create_image_attachment(attachment.format or "webp", attachment.data)}
    if attachment.type == AttachmentType.AUDIO:
        return {LXMF.FIELD_AUDIO: create_audio_attachment(int(attachment.format or 0), attachment.data)}
    raise ValueError(f"Unsupported attachment type: {attachment.type}")