from __future__ import annotations

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class PowerShellLibraryAction(BaseAction):
    """Open the Web PowerShell Library from the Ring."""

    action_type = "powershell_library"

    def execute(self, payload: str, context: dict) -> None:
        opener = context.get("open_powershell_library")
        if callable(opener):
            opener()
