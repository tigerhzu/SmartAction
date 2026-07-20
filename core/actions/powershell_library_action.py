from __future__ import annotations

from PySide6.QtCore import Qt

from core.actions.base import BaseAction
from core.actions.registry import register_action

_library_window = None


@register_action
class PowerShellLibraryAction(BaseAction):
    """Open the PowerShell Library window from the Ring."""

    action_type = "powershell_library"

    def execute(self, payload: str, context: dict) -> None:
        opener = context.get("open_powershell_library")
        if callable(opener):
            opener()
            return

        from ui.powershell_library_window import PowerShellLibraryWindow
        from ui.window_utils import show_window_on_screen

        global _library_window
        if _library_window is None:
            parent = context.get("parent_widget")
            _library_window = PowerShellLibraryWindow(parent)
            _library_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            _library_window.destroyed.connect(lambda *_args: _clear_window_ref())
        show_window_on_screen(_library_window, context.get("target_screen"))


def _clear_window_ref() -> None:
    global _library_window
    _library_window = None
