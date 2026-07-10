"""
UrlAction — open a URL in the default browser.

payload : a fully-qualified URL, e.g. "https://claude.ai"
"""
import webbrowser

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class UrlAction(BaseAction):
    action_type = "url"

    def execute(self, payload: str, context: dict) -> None:
        if not payload:
            print("[UrlAction] Empty payload — nothing to open.")
            return
        webbrowser.open(payload)
