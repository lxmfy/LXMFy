"""
Storage module for LXMFy bot framework.

This module provides abstract and concrete storage implementations for persistent data storage.
It includes a base StorageBackend interface and a JSON file-based implementation.
The Storage class serves as a facade for the underlying storage backend.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import json
from pathlib import Path
import logging


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
        self.cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.cache:
            return self.cache[key]

        file_path = self.directory / f"{key}.json"
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
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


class Storage:
    def __init__(self, backend: StorageBackend):
        self.backend = backend

    def get(self, key: str, default: Any = None) -> Any:
        return self.backend.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.backend.set(key, value)

    def delete(self, key: str) -> None:
        self.backend.delete(key)

    def exists(self, key: str) -> bool:
        return self.backend.exists(key)

    def scan(self, prefix: str) -> list:
        return self.backend.scan(prefix)

    def get_role_data(self, role_name: str) -> Dict:
        """Helper method for permission system"""
        return self.get(f"roles:{role_name}", {})

    def set_role_data(self, role_name: str, data: Dict):
        """Helper method for permission system"""
        self.set(f"roles:{role_name}", data)

    def get_user_roles(self, user_hash: str) -> List[str]:
        """Helper method for permission system"""
        return self.get(f"user_roles:{user_hash}", [])

    def set_user_roles(self, user_hash: str, roles: List[str]):
        """Helper method for permission system"""
        self.set(f"user_roles:{user_hash}", roles)
