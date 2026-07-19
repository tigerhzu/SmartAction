"""Windows-specific integrations."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

_MODIFIERS = {
    "alt": MOD_ALT,
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
    "cmd": MOD_WIN,
}

_KEYS = {
    "space": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "backspace": 0x08,
    "del": 0x2E,
    "delete": 0x2E,
}


def parse_hotkey(combo: str) -> tuple[int, int]:
    """Translate a SmartAction hotkey string to Win32 modifiers and VK code."""
    parts = [part.strip().casefold() for part in combo.split("+") if part.strip()]
    modifiers = MOD_NOREPEAT
    keys: list[str] = []
    for part in parts:
        modifier = _MODIFIERS.get(part)
        if modifier is not None:
            modifiers |= modifier
        else:
            keys.append(part)

    if len(keys) != 1:
        raise ValueError("A hotkey must contain exactly one non-modifier key.")

    key = keys[0]
    if len(key) == 1 and ("a" <= key <= "z" or "0" <= key <= "9"):
        virtual_key = ord(key.upper())
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        virtual_key = 0x70 + int(key[1:]) - 1
    else:
        virtual_key = _KEYS.get(key, 0)

    if not virtual_key:
        raise ValueError(f"Unsupported Windows hotkey key: {key!r}")
    return modifiers, virtual_key


class WindowsHotkeyBackend(QAbstractNativeEventFilter):
    """Global hotkeys backed by the Windows message queue.

    ``RegisterHotKey`` is owned by Windows rather than a Python keyboard-hook
    thread, so registration remains stable while SmartAction sits in the tray
    for long periods or the desktop is locked and resumed.
    """

    _HOTKEY_ID = 0x5341  # "SA"; unique within SmartAction's GUI thread.

    def __init__(self) -> None:
        super().__init__()
        self._callback: Callable[[], None] | None = None
        self._registered = False
        self._filter_installed = False
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.RegisterHotKey.argtypes = (
            wintypes.HWND,
            ctypes.c_int,
            wintypes.UINT,
            wintypes.UINT,
        )
        self._user32.RegisterHotKey.restype = wintypes.BOOL
        self._user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
        self._user32.UnregisterHotKey.restype = wintypes.BOOL

    def register(self, combo: str, callback: Callable[[], None]) -> bool:
        if self._registered:
            self.unregister(combo)
        try:
            modifiers, virtual_key = parse_hotkey(combo)
        except ValueError as exc:
            print(f"[HotkeyManager] Cannot register {combo!r}: {exc}")
            return False

        app = QCoreApplication.instance()
        if app is None:
            print("[HotkeyManager] Cannot register hotkey before Qt starts.")
            return False

        self._callback = callback
        if not self._filter_installed:
            app.installNativeEventFilter(self)
            self._filter_installed = True

        ctypes.set_last_error(0)
        ok = bool(
            self._user32.RegisterHotKey(
                None,
                self._HOTKEY_ID,
                modifiers,
                virtual_key,
            )
        )
        if not ok:
            error = ctypes.get_last_error()
            print(
                f"[HotkeyManager] WinAPI RegisterHotKey failed for {combo!r} "
                f"(Windows error {error})."
            )
            self._callback = None
            self._remove_filter()
            return False

        self._registered = True
        return True

    def unregister(self, _combo: str) -> None:
        if self._registered:
            self._user32.UnregisterHotKey(None, self._HOTKEY_ID)
        self._registered = False
        self._callback = None
        self._remove_filter()

    def _remove_filter(self) -> None:
        app = QCoreApplication.instance()
        if self._filter_installed and app is not None:
            app.removeNativeEventFilter(self)
        self._filter_installed = False

    def nativeEventFilter(self, event_type, message):  # noqa: N802 - Qt API
        if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and int(msg.wParam) == self._HOTKEY_ID:
                callback = self._callback
                if callback is not None:
                    callback()
                return True, 0
        return False, 0
