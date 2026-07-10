"""
Action registry.

Each action module decorates its class with @register_action.
ActionRunner looks up by action_type string — no if-else chains anywhere.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.actions.base import BaseAction

_REGISTRY: dict[str, type[BaseAction]] = {}


def register_action(cls: type[BaseAction]) -> type[BaseAction]:
    """Class decorator — adds the class to the global action registry."""
    _REGISTRY[cls.action_type] = cls
    return cls


def get_action(action_type: str) -> type[BaseAction] | None:
    """Return the registered action class for *action_type*, or None."""
    return _REGISTRY.get(action_type)


def registered_types() -> list[str]:
    return list(_REGISTRY.keys())
