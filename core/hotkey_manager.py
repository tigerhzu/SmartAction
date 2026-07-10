"""
Global hotkey manager.

Supported now  : keyboard combos (F13, Ctrl+Alt+Space, Ctrl+Shift+Q, …)
Reserved (stub): Mouse Button 4 / 5  — token names: mouse4, mouse5
"""

from __future__ import annotations

import keyboard
from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot

from core.config_manager import ConfigManager

# Tokens that identify mouse-button combos
_MOUSE_TOKENS: frozenset[str] = frozenset(
    {"mouse4", "mouse5", "mb4", "mb5", "xbutton1", "xbutton2"}
)


def _is_mouse_combo(combo: str) -> bool:
    return bool(set(combo.lower().split("+")) & _MOUSE_TOKENS)


# ── Backends ──────────────────────────────────────────────────────────────────


class _KeyboardBackend:
    """Global keyboard hotkeys via the `keyboard` library."""

    def register(self, combo: str, callback) -> bool:
        try:
            keyboard.add_hotkey(combo, callback, suppress=False)
            return True
        except Exception as exc:
            print(f"[HotkeyManager] Cannot register '{combo}': {exc}")
            return False

    def unregister(self, combo: str) -> None:
        try:
            keyboard.remove_hotkey(combo)
        except (KeyError, ValueError):
            pass


class _MouseBackend:
    """
    Stub for Mouse Button 4 / 5.

    Implement by hooking pynput.mouse.Listener when ready.
    Token names: mouse4, mouse5  (use these in config.json)
    """

    def register(self, combo: str, callback) -> bool:
        print(f"[HotkeyManager] Mouse hotkey '{combo}' is not yet implemented.")
        return False

    def unregister(self, combo: str) -> None:
        pass


# ── Manager ───────────────────────────────────────────────────────────────────


class HotkeyManager(QObject):
    """
    Loads the active hotkey from ConfigManager, registers it globally,
    and emits `triggered` (in the Qt main thread) whenever it fires.

    Supported combo strings (case-insensitive):
        "f13"
        "ctrl+alt+space"
        "ctrl+shift+q"

    Reserved for future mouse-backend support:
        "mouse4"
        "mouse5"

    Usage:
        mgr = HotkeyManager(config)
        mgr.triggered.connect(my_slot)
        mgr.start()            # register from config
        mgr.reload("f13")      # live swap — no restart needed
        mgr.stop()             # unregister
    """

    triggered = Signal()

    def __init__(self, config: ConfigManager, parent: QObject | None = None):
        super().__init__(parent)
        self._config = config
        self._current_combo: str | None = None
        self._kb = _KeyboardBackend()
        self._mouse = _MouseBackend()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, combo: str | None = None) -> bool:
        """Register the hotkey.

        Parameters
        ----------
        combo : str | None
            Override the combo string.  When *None* the value stored in
            ConfigManager is used (legacy behaviour).
        """
        if combo is None:
            combo = self._config.get("hotkey", "ctrl+alt+space")
        return self._register(combo)

    def stop(self) -> None:
        """Unregister the active hotkey."""
        self._unregister_current()

    def reload(self, new_combo: str) -> bool:
        """
        Swap to a new hotkey combo at runtime.

        Unregisters the current combo, registers the new one,
        and persists it to config.json — no app restart needed.
        Returns True on success.
        """
        self._unregister_current()
        ok = self._register(new_combo)
        if ok:
            self._config.set("hotkey", new_combo)
        return ok

    @property
    def current_combo(self) -> str | None:
        """Currently active hotkey combo, or None if not registered."""
        return self._current_combo

    # ── Internals ─────────────────────────────────────────────────────────────

    def _backend_for(self, combo: str) -> _KeyboardBackend | _MouseBackend:
        return self._mouse if _is_mouse_combo(combo) else self._kb

    def _register(self, combo: str) -> bool:
        ok = self._backend_for(combo).register(combo, self._fire)
        if ok:
            self._current_combo = combo
            print(f"[HotkeyManager] Registered: {combo}")
        return ok

    def _unregister_current(self) -> None:
        if self._current_combo:
            self._backend_for(self._current_combo).unregister(self._current_combo)
            print(f"[HotkeyManager] Unregistered: {self._current_combo}")
            self._current_combo = None

    def _fire(self) -> None:
        """
        Called from the keyboard hook thread.
        Marshal to the Qt main thread via a queued invoke.
        """
        QMetaObject.invokeMethod(
            self,
            "_on_hotkey_fired",
            Qt.ConnectionType.QueuedConnection,
        )

    @Slot()
    def _on_hotkey_fired(self) -> None:
        self.triggered.emit()
