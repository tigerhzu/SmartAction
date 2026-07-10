"""
SubMenuAction — navigation to a child ring level.

Ring items with children are handled by RingWindow._drill_into() before
item_activated is ever emitted, so execute() here is only reached when an
item declares action_type="submenu" but has no children in config
(e.g. a placeholder or future dynamic menu).
"""
from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class SubMenuAction(BaseAction):
    action_type = "submenu"

    def execute(self, payload: str, context: dict) -> None:
        # Navigation to children is handled upstream by the ring widget.
        # Nothing to do for a childless submenu stub.
        print(f"[SubMenuAction] submenu stub — no children defined (payload={payload!r})")
