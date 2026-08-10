"""Dispatch menu items to registered action handlers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import core.actions  # noqa: F401 - importing registers all action types

from core.actions.registry import get_action, registered_types
from core.execution_contracts import ExecutionError
from core.menu_model import MenuItem


ACTION_DISPATCHED = "dispatched"
ACTION_UNSUPPORTED = "unsupported"
ACTION_HANDLER_ERROR = "handler_error"


@dataclass(frozen=True)
class ActionDispatchResult:
    """Transport-neutral outcome of handing an action to its handler.

    ``dispatched`` only means that the handler returned without raising. It does
    not claim that an application, subprocess, URL, or other asynchronous OS work
    subsequently completed.
    """

    status: str
    item_id: str
    action_type: str
    handler: str = ""
    error: ExecutionError | None = None

    @property
    def success(self) -> bool:
        return self.status == ACTION_DISPATCHED

    @property
    def dispatched(self) -> bool:
        return self.status == ACTION_DISPATCHED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "success": self.success,
            "dispatched": self.dispatched,
            "itemId": self.item_id,
            "actionType": self.action_type,
            "handler": self.handler or None,
            "error": self.error.to_dict() if self.error else None,
        }


class ActionRunner:
    """Stateless dispatcher. Safe to call from the Qt main thread."""

    def run(self, item: MenuItem, context: dict | None = None) -> ActionDispatchResult:
        """Hand *item* to its action handler and describe the dispatch outcome.

        Existing callers may continue to ignore the return value. ``context`` holds
        optional runtime values such as a parent widget or target screen.
        """
        action_cls = get_action(item.action_type)
        if action_cls is None:
            registered = registered_types()
            print(
                f"[ActionRunner] No handler for type {item.action_type!r}. "
                f"Registered: {registered}"
            )
            return ActionDispatchResult(
                status=ACTION_UNSUPPORTED,
                item_id=item.id,
                action_type=item.action_type,
                error=ExecutionError(
                    code="unsupported_action_type",
                    message=f'No action handler is registered for type "{item.action_type}".',
                    details={"registered_types": registered},
                ),
            )

        try:
            action_cls().execute(item.action_payload, context or {})
        except Exception as exc:
            print(f"[ActionRunner] {item.action_type!r} raised: {exc}")
            return ActionDispatchResult(
                status=ACTION_HANDLER_ERROR,
                item_id=item.id,
                action_type=item.action_type,
                handler=action_cls.__name__,
                error=ExecutionError(
                    code="handler_exception",
                    message=str(exc) or "The action handler raised an exception.",
                    details={"exception_type": type(exc).__name__},
                ),
            )

        return ActionDispatchResult(
            status=ACTION_DISPATCHED,
            item_id=item.id,
            action_type=item.action_type,
            handler=action_cls.__name__,
        )


__all__ = [
    "ACTION_DISPATCHED",
    "ACTION_HANDLER_ERROR",
    "ACTION_UNSUPPORTED",
    "ActionDispatchResult",
    "ActionRunner",
]
