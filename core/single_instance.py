from __future__ import annotations

from PySide6.QtCore import QLockFile

from core.debug_log import debug_log
from core.paths import DATA_DIR


def acquire_single_instance_lock() -> QLockFile | None:
    """Return a process-held lock, or None when SmartAction is already running."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = DATA_DIR / "smartaction.lock"
    lock = QLockFile(str(lock_path))
    lock.setStaleLockTime(30000)
    if lock.tryLock(100):
        debug_log(f"single instance lock acquired: {lock_path.resolve()}")
        return lock

    debug_log(f"single instance lock busy, exiting: {lock_path.resolve()}")
    return None
