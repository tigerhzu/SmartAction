"""Windows registry autostart management (HKCU Run key)."""
from __future__ import annotations

import sys
from pathlib import Path

_REG_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "UniversalActionsRing"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    # Dev mode: use pythonw.exe (no console) with the entry-point script
    python = Path(sys.executable)
    pythonw = python.with_name("pythonw.exe")
    interpreter = str(pythonw if pythonw.exists() else python)
    main_py = Path(__file__).resolve().parent.parent / "app" / "main.py"
    return f'"{interpreter}" "{main_py}"'


def is_enabled() -> bool:
    """Return True if the autostart registry value exists."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY) as key:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def set_enabled(enabled: bool) -> bool:
    """Write or remove the autostart registry value. Returns True on success."""
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY,
            access=winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError as exc:
        print(f"[Autostart] Failed: {exc}")
        return False
