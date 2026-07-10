"""
PasteAction — write text to the clipboard then simulate Ctrl+V.

payload : the exact text to paste into the previously active window.

Timing note
-----------
The ring window is already hidden before this action executes (Application
closes it before dispatching, and adds a 120 ms delay).  A further 80 ms
timer here gives the OS time to return focus to the original window before
the synthetic Ctrl+V is sent.
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.actions._clipboard import send_paste
from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class PasteAction(BaseAction):
    action_type = "paste"

    def execute(self, payload: str, context: dict) -> None:
        if not payload:
            print("[PasteAction] Empty payload — nothing to paste.")
            return
        QApplication.clipboard().setText(payload)
        QTimer.singleShot(80, send_paste)
