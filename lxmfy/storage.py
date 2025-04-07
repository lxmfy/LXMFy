"""
Storage module for LXMFy bot framework.

This module provides abstract and concrete storage implementations for persistent data storage.
It includes a base StorageBackend interface and a JSON file-based implementation.
The Storage class serves as a facade for the underlying storage backend.
"""

import base64
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import RNS
from LXMF import LXMessage

from .attachments import Attachment, AttachmentType


def serialize_value(obj: Any) -> Any:
    """Serialize complex objects to JSON-compatible format."""
    if isinstance(obj, (bytes, bytearray)):
        return {"__type": "bytes", "data": base64.b64encode(obj).decode()}
    if isinstance(obj, datetime):
        return {"__type": "datetime", "data": obj.isoformat()}
    if isinstance(obj, LXMessage):
        msg_data = {
            "__type": "LXMessage",
            "source_hash": RNS.hexrep(obj.source_hash, delimit=False),
            "destination_hash": RNS.hexrep(obj.destination_hash, delimit=False),
            "content": base64.b64encode(obj.content).decode() if obj.content else None,
            "title": obj.title,
            "timestamp": obj.timestamp.isoformat() if obj.timestamp else None
        }

        if hasattr(obj, "fields") and obj.fields:
            msg_data["fields"] = {
                str(k): serialize_value(v) for k, v in obj.fields.items()
            }

        return msg_data
    if isinstance(obj, Attachment):
        return {
            "__type": "Attachment",
            "type": obj.type,
            "name": obj.name,
            "data": base64.b64encode(obj.data).decode(),
            "format": obj.format
        }
    if isinstance(obj, (list, tuple)):
        return [serialize_value(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize_value(v) for k, v in obj.items()}
    return obj


def deserialize_value(obj: Any) -> Any:
    """Deserialize from storage format."""
    if isinstance(obj, dict):
        if "__type" in obj:
            if obj["__type"] == "bytes":
                return base64.b64decode(obj["data"])
            if obj["__type"] == "datetime":
                return datetime.fromisoformat(obj["data"])
            if obj["__type"] == "LXMessage":
                msg_data = {
                    "source_hash": obj["source_hash"],
                    "destination_hash": obj["destination_hash"],
                    "content": base64.b64decode(obj["data"]) if obj["content"] else None,
                    "title": obj["title"],
                    "timestamp": datetime.fromisoformat(obj["timestamp"]) if obj["timestamp"] else None
                }
                if "fields" in obj:
                    msg_data["fields"] = deserialize_value(obj["fields"])
                return msg_data
            if obj["__type"] == "Attachment":
                return Attachment(
                    type=AttachmentType(obj["type"]),
                    name=obj["name"],
                    data=base64.b64decode(obj["data"]),
                    format=obj["format"]
                )
        return {k: deserialize_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deserialize_value(item) for item in obj]
    return obj


class StorageBackend(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def scan(self, prefix: str) -> list:
        pass


class JSONStorage(StorageBackend):
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.cache:
            return self.cache[key]

        file_path = self.directory / f"{key}.json"
        try:
            if file_path.exists():
                with open(file_path) as f:
                    data = json.load(f)
                    self.cache[key] = data
                    return data
        except Exception as e:
            self.logger.error("Error reading %s: %s", key, str(e))
        return default

    def set(self, key: str, value: Any) -> None:
        file_path = self.directory / f"{key}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(value, f, indent=2)
            self.cache[key] = value
        except Exception as e:
            self.logger.error("Error writing %s: %s", key, str(e))
            raise

    def delete(self, key: str) -> None:
        file_path = self.directory / f"{key}.json"
        try:
            if file_path.exists():
                file_path.unlink()
            self.cache.pop(key, None)
        except Exception as e:
            self.logger.error("Error deleting %s: %s", key, str(e))
            raise

    def exists(self, key: str) -> bool:
        return (self.directory / f"{key}.json").exists()

    def scan(self, prefix: str) -> list:
        """Scan for keys with given prefix"""
        results = []
        try:
            for file in self.directory.glob(f"{prefix}*.json"):
                key = file.stem
                if key.startswith(prefix):
                    results.append(key)
        except Exception as e:
            self.logger.error("Error scanning with prefix %s: %s", prefix, str(e))
        return results


class SQLiteStorage(StorageBackend):
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.cache: dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS key_value (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_key_prefix ON key_value(key)
                """)
        except Exception as e:
            self.logger.error("Error initializing database: %s", str(e))
            raise

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.cache:
            return self.cache[key]

        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT value FROM key_value WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    try:
                        value = json.loads(row[0])  # Deserialize JSON string
                        self.cache[key] = value
                        return value
                    except json.JSONDecodeError:
                        return row[0]  # Return raw value if not JSON
        except Exception as e:
            self.logger.error("Error reading %s: %s", key, str(e))
        return default

    def set(self, key: str, value: Any) -> None:
        try:
            # Convert value to JSON string
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO key_value (key, value, type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (key, serialized, type(value).__name__))
            self.cache[key] = value
        except Exception as e:
            self.logger.error("Error writing %s: %s", key, str(e))
            raise

    def delete(self, key: str) -> None:
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("DELETE FROM key_value WHERE key = ?", (key,))
            self.cache.pop(key, None)
        except Exception as e:
            self.logger.error("Error deleting %s: %s", key, str(e))
            raise

    def exists(self, key: str) -> bool:
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT 1 FROM key_value WHERE key = ?", (key,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error("Error checking existence of %s: %s", key, str(e))
            return False

    def scan(self, prefix: str) -> list:
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "SELECT key FROM key_value WHERE key LIKE ? ORDER BY key",
                    (f"{prefix}%",)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error("Error scanning with prefix %s: %s", prefix, str(e))
            return []


class Storage:
    def __init__(self, backend: StorageBackend):
        self.backend = backend

    def get(self, key: str, default: Any = None) -> Any:
        value = self.backend.get(key, default)
        return deserialize_value(value)

    def set(self, key: str, value: Any) -> None:
        serialized = serialize_value(value)
        self.backend.set(key, serialized)

    def delete(self, key: str) -> None:
        self.backend.delete(key)

    def exists(self, key: str) -> bool:
        return self.backend.exists(key)

    def scan(self, prefix: str) -> list:
        return self.backend.scan(prefix)

    def get_role_data(self, role_name: str) -> dict:
        """Helper method for permission system"""
        return self.get(f"roles:{role_name}", {})

    def set_role_data(self, role_name: str, data: dict):
        """Helper method for permission system"""
        self.set(f"roles:{role_name}", data)

    def get_user_roles(self, user_hash: str) -> list[str]:
        """Helper method for permission system"""
        return self.get(f"user_roles:{user_hash}", [])

    def set_user_roles(self, user_hash: str, roles: list[str]):
        """Helper method for permission system"""
        self.set(f"user_roles:{user_hash}", roles)
