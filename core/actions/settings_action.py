"""Open the main Settings window from a radial-ring action."""
from __future__ import annotations

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class SettingsAction(BaseAction):
    action_type = "settings"

    def execute(self, payload: str, context: dict) -> None:
        opener = context.get("open_settings")
        if callable(opener):
            opener()
