from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


def _log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "app_debug.log"
    return Path(__file__).resolve().parent.parent / "app_debug.log"


def debug_log(message: str) -> None:
    line = f"[DEBUG] {message}"
    print(line)
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
    except OSError:
        pass
