# Local filesystem implementation of StorageBackend, for dev before Azure Blob is wired in.

from pathlib import Path

from app.storage.base import StorageBackend

# backend/storage_data — already present as an empty dir in the scaffold.
STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage_data"


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path = STORAGE_ROOT):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _full_path(self, storage_path: str) -> Path:
        return self.root / storage_path

    def save(self, storage_path: str, content: bytes) -> None:
        full_path = self._full_path(storage_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)

    def read(self, storage_path: str) -> bytes:
        return self._full_path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        self._full_path(storage_path).unlink(missing_ok=True)
