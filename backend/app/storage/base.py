# StorageBackend interface — save/read/delete file bytes, swappable for Azure Blob later.

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def save(self, storage_path: str, content: bytes) -> None:
        """Write bytes at storage_path, creating any parent directories/containers as needed."""

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        """Read back the bytes previously saved at storage_path."""

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        """Remove the file at storage_path. No-op if it doesn't exist."""
