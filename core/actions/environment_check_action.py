from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from core.actions.base import BaseAction
from core.actions.registry import register_action
from core.environment_check import run_environment_check
from ui.window_utils import exec_dialog_on_screen


@register_action
class EnvironmentCheckAction(BaseAction):
    action_type = "environment_check"

    def execute(self, payload: str, context: dict) -> None:
        parent = context.get("parent_widget")
        try:
            result = run_environment_check()
        except Exception as exc:
            warning = QMessageBox(
                QMessageBox.Icon.Warning,
                "Environment Check",
                f"Environment Check failed: {str(exc)[:160]}",
                QMessageBox.StandardButton.Ok,
                parent,
            )
            exec_dialog_on_screen(warning, context.get("target_screen"))
            return

        from ui.environment_check_window import EnvironmentCheckResultDialog

        dialog = EnvironmentCheckResultDialog(result, parent)
        exec_dialog_on_screen(dialog, context.get("target_screen"))
