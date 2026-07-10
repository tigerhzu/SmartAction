"""
ActionRunner — dispatches a MenuItem to the correct action class.

How it works
------------
1. `import core.actions` triggers every @register_action decorator, populating
   the global registry in core.actions.registry.
2. ActionRunner.run() does a single dict lookup — no if-else, no isinstance.
3. Adding a new action type requires only a new file in core/actions/;
   nothing else changes.
"""
from __future__ import annotations

import core.actions  # noqa: F401 — side-effect: registers all action types

from core.actions.registry import get_action, registered_types
from core.menu_model import MenuItem


class ActionRunner:
    """Stateless dispatcher.  Safe to call from the Qt main thread."""

    def run(self, item: MenuItem, context: dict | None = None) -> None:
        """
        Execute the action for *item*.

        Parameters
        ----------
        item    : the menu item whose action_type / action_payload to run
        context : optional runtime values (e.g. {"parent_widget": QWidget})
        """
        action_cls = get_action(item.action_type)
        if action_cls is None:
            print(
                f"[ActionRunner] No handler for type {item.action_type!r}. "
                f"Registered: {registered_types()}"
            )
            return
        try:
            action_cls().execute(item.action_payload, context or {})
        except Exception as exc:
            print(f"[ActionRunner] {item.action_type!r} raised: {exc}")
