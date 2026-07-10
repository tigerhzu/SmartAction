"""
FormAction — show a simple single-field input dialog, then paste the value.

payload : JSON string describing the form, or plain text used as the dialog title.

JSON format (all fields optional):
  {
    "title":   "Dialog title",
    "label":   "Field label:",
    "default": ""
  }

After the user confirms, the entered text is placed on the clipboard and
Ctrl+V is sent to the previously active window (same mechanism as PasteAction).

For multi-field forms backed by a PowerShell script, use action_type "ps_form".
"""
from __future__ import annotations

import json

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QInputDialog, QWidget

from core.actions._clipboard import send_paste
from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class FormAction(BaseAction):
    action_type = "form"

    def execute(self, payload: str, context: dict) -> None:
        form_def = _parse_payload(payload)
        title    = form_def.get("title",   "Input")
        label    = form_def.get("label",   "Enter value:")
        default  = form_def.get("default", "")
        parent: QWidget | None = context.get("parent_widget")

        text, ok = QInputDialog.getText(parent, title, label, text=default)
        if ok and text:
            QApplication.clipboard().setText(text)
            QTimer.singleShot(80, send_paste)


def _parse_payload(payload: str) -> dict:
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"title": payload}
