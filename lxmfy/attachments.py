from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import LXMF


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


def create_file_attachment(filename: str, data: bytes) -> list:
    return [filename, data]


def create_image_attachment(format: str, data: bytes) -> list:
    return [format, data]


def create_audio_attachment(mode: int, data: bytes) -> list:
    return [mode, data]


def pack_attachment(attachment: Attachment) -> dict:
    if attachment.type == AttachmentType.FILE:
        return {LXMF.FIELD_FILE_ATTACHMENTS: [create_file_attachment(attachment.name, attachment.data)]}
    if attachment.type == AttachmentType.IMAGE:
        return {LXMF.FIELD_IMAGE: create_image_attachment(attachment.format or "webp", attachment.data)}
    if attachment.type == AttachmentType.AUDIO:
        return {LXMF.FIELD_AUDIO: create_audio_attachment(int(attachment.format or 0), attachment.data)}
    raise ValueError(f"Unsupported attachment type: {attachment.type}") 