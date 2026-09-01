import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    key: str
    sha256: str
    size: int


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes) -> StoredObject: ...
    def get(self, key: str) -> bytes: ...


class LocalObjectStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if self.root not in candidate.parents:
            raise ValueError("Invalid storage key")
        return candidate

    def put(self, key: str, content: bytes) -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(key=key, sha256=hashlib.sha256(content).hexdigest(), size=len(content))

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()
