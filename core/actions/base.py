"""
BaseAction — abstract contract every action type must implement.

An action receives:
  payload : str   — the raw string stored in config.json (action_payload)
  context : dict  — runtime values the caller injects
                    {
                      "parent_widget": QWidget | None,  # for dialogs
                    }
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAction(ABC):
    # Every concrete class must declare its type identifier at class level.
    action_type: str

    @abstractmethod
    def execute(self, payload: str, context: dict) -> None:
        """Run the action.  Must not block the Qt main thread for > ~50 ms."""
