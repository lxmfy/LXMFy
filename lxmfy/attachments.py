from enum import IntEnum
from typing import List, Optional
from dataclasses import dataclass
from LXMF import LXMessage


class AttachmentType(IntEnum):
    FILE = 0x05
    IMAGE = 0x06
    AUDIO = 0x07


@dataclass
class Attachment:
    type: AttachmentType
    name: str
    data: bytes
    format: Optional[str] = None


def create_file_attachment(filename: str, data: bytes) -> List:
    return [filename, data]


def create_image_attachment(format: str, data: bytes) -> List:
    return [format, data]


def create_audio_attachment(mode: int, data: bytes) -> List:
    return [mode, data]


def pack_attachment(attachment: Attachment) -> dict:
    if attachment.type == AttachmentType.FILE:
        return {LXMessage.FIELD_FILE_ATTACHMENTS: [create_file_attachment(attachment.name, attachment.data)]}
    elif attachment.type == AttachmentType.IMAGE:
        return {LXMessage.FIELD_IMAGE: create_image_attachment(attachment.format or "webp", attachment.data)}
    elif attachment.type == AttachmentType.AUDIO:
        return {LXMessage.FIELD_AUDIO: create_audio_attachment(int(attachment.format or 0), attachment.data)}
    raise ValueError(f"Unsupported attachment type: {attachment.type}") 