"""Small JSON repository with crash-safe, atomic document replacement."""
from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


class JsonStoreError(RuntimeError):
    """Raised when a JSON document cannot be read or committed."""

    def __init__(self, message: str, *, path: Path, operation: str) -> None:
        super().__init__(message)
        self.path = Path(path)
        self.operation = operation


class AtomicJsonStore:
    """Read and atomically replace one JSON document.

    The temporary file is created beside the destination so ``os.replace`` is
    guaranteed to stay on the same filesystem.  Callers only ever observe the
    previous complete document or the next complete document.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read(self, fallback: Any = None) -> Any:
        if not self.path.exists():
            return deepcopy(fallback)
        try:
            with self.path.open(encoding="utf-8") as stream:
                return json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            raise JsonStoreError(
                f"Unable to read JSON document {self.path}: {exc}",
                path=self.path,
                operation="read",
            ) from exc

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            descriptor, raw_temp_path = tempfile.mkstemp(
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
            )
            temp_path = Path(raw_temp_path)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(data, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, self.path)
            temp_path = None
        except (OSError, TypeError, ValueError) as exc:
            raise JsonStoreError(
                f"Unable to write JSON document {self.path}: {exc}",
                path=self.path,
                operation="write",
            ) from exc
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass


def read_json(path: Path, fallback: Any = None) -> Any:
    """Compatibility-friendly functional wrapper around :class:`AtomicJsonStore`."""
    return AtomicJsonStore(path).read(fallback)


def write_json_atomic(path: Path, data: Any) -> None:
    """Atomically serialize *data* to *path*."""
    AtomicJsonStore(path).write(data)
