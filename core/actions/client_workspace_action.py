from __future__ import annotations

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class ClientWorkspaceAction(BaseAction):
    action_type = "client_workspace"

    def execute(self, payload: str, context: dict) -> None:
        opener = context.get("open_client_workspace")
        if callable(opener):
            opener()
            return

        from ui.client_workspace_window import ClientWorkspaceWindow
        from ui.window_utils import exec_dialog_on_screen

        parent = context.get("parent_widget")
        dialog = ClientWorkspaceWindow(parent)
        exec_dialog_on_screen(dialog, context.get("target_screen"))
