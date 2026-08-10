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
