from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path


_DEBUG_ENABLED = os.environ.get("SMARTACTION_DEBUG", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_MAX_LOG_BYTES = 1_000_000


def _log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "app_debug.log"
    return Path(__file__).resolve().parent.parent / "app_debug.log"


def debug_log(message: str) -> None:
    if not _DEBUG_ENABLED:
        return

    line = f"[DEBUG] {message}"
    print(line)
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if path.exists() and path.stat().st_size >= _MAX_LOG_BYTES else "a"
        with open(path, mode, encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
    except OSError:
        pass
