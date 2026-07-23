"""Shared motion preference for ring and settings previews."""
from __future__ import annotations

import ctypes
import os
import sys

from PySide6.QtCore import QSettings

_ORGANIZATION = "Universal Actions Ring"
_APPLICATION = "Universal Actions Ring"
_KEY = "appearance/reduced_motion"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _system_reduced_motion() -> bool:
    if sys.platform != "win32":
        return False
    animations_enabled = ctypes.c_int(1)
    try:
        result = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
            0x1042,
            0,
            ctypes.byref(animations_enabled),
            0,
        )
    except (AttributeError, OSError):
        return False
    return bool(result) and not bool(animations_enabled.value)


def reduced_motion_enabled() -> bool:
    """Return the explicit preference, environment override, or Windows value."""
    environment = os.environ.get("SMARTACTION_REDUCED_MOTION", "").strip().lower()
    if environment in _TRUE_VALUES:
        return True
    stored = QSettings(_ORGANIZATION, _APPLICATION).value(_KEY)
    if stored is not None:
        if isinstance(stored, bool):
            return stored
        return str(stored).strip().lower() in _TRUE_VALUES
    return _system_reduced_motion()


def set_reduced_motion_enabled(enabled: bool) -> None:
    QSettings(_ORGANIZATION, _APPLICATION).setValue(_KEY, bool(enabled))
