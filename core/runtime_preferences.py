"""Small Core boundary for machine-local runtime preferences."""
from __future__ import annotations

import ctypes
import os
import sys
from typing import Any

from PySide6.QtCore import QSettings

from core import autostart


_ORGANIZATION = "Universal Actions Ring"
_APPLICATION = "Universal Actions Ring"
_REDUCED_MOTION_KEY = "appearance/reduced_motion"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _system_reduced_motion() -> bool:
    if sys.platform != "win32":
        return False
    animations_enabled = ctypes.c_int(1)
    try:
        result = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
            0x1042, 0, ctypes.byref(animations_enabled), 0
        )
    except (AttributeError, OSError):
        return False
    return bool(result) and not bool(animations_enabled.value)


class RuntimePreferencesService:
    """Own settings that are intentionally outside the actions JSON document."""

    def snapshot(self) -> dict[str, bool]:
        return {
            "autostart": autostart.is_enabled(),
            "reduced_motion": self.reduced_motion_enabled(),
        }

    def update(self, changes: dict[str, Any]) -> dict[str, bool]:
        allowed = {"autostart", "reduced_motion"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported runtime preference: {sorted(unknown)[0]}")
        if "autostart" in changes:
            if not autostart.set_enabled(bool(changes["autostart"])):
                raise ValueError("Windows could not update SmartAction autostart.")
        if "reduced_motion" in changes:
            self.set_reduced_motion_enabled(bool(changes["reduced_motion"]))
        return self.snapshot()

    @staticmethod
    def reduced_motion_enabled() -> bool:
        environment = os.environ.get("SMARTACTION_REDUCED_MOTION", "").strip().lower()
        if environment in _TRUE_VALUES:
            return True
        stored = QSettings(_ORGANIZATION, _APPLICATION).value(_REDUCED_MOTION_KEY)
        if stored is not None:
            if isinstance(stored, bool):
                return stored
            return str(stored).strip().lower() in _TRUE_VALUES
        return _system_reduced_motion()

    @staticmethod
    def set_reduced_motion_enabled(enabled: bool) -> None:
        QSettings(_ORGANIZATION, _APPLICATION).setValue(_REDUCED_MOTION_KEY, bool(enabled))


__all__ = ["RuntimePreferencesService"]
