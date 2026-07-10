from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from core.actions.base import BaseAction
from core.actions.registry import register_action
from core.environment_check import run_environment_check


@register_action
class EnvironmentCheckAction(BaseAction):
    action_type = "environment_check"

    def execute(self, payload: str, context: dict) -> None:
        parent = context.get("parent_widget")
        try:
            result = run_environment_check()
        except Exception as exc:
            QMessageBox.warning(
                parent,
                "Environment Check",
                f"Environment Check failed: {str(exc)[:160]}",
            )
            return

        from ui.environment_check_window import EnvironmentCheckResultDialog

        EnvironmentCheckResultDialog(result, parent).exec()
