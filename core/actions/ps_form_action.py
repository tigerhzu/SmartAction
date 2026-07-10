from __future__ import annotations

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class PsFormAction(BaseAction):
    """Opens a custom multi-field form dialog, then runs the matching PS script.

    Payload: the form_id string registered by @register_form (e.g. "join_domain").

    The late import of `ui.forms` avoids a core→ui circular dependency at module
    load time while still triggering all @register_form decorators before lookup.
    """

    action_type = "ps_form"

    def execute(self, payload: str, context: dict) -> None:
        import ui.forms  # noqa: F401 — triggers @register_form decorators
        from ui.forms.form_registry import get_form, registered_forms

        form_cls = get_form(payload)
        if form_cls is None:
            print(
                f"[PsFormAction] No form registered for {payload!r}. "
                f"Registered: {registered_forms()}"
            )
            return

        parent = context.get("parent_widget")
        dialog = form_cls(parent=parent)
        dialog.exec()
