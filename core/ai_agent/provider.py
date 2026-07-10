"""Provider abstraction; concrete providers may plan but never execute."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

from core.ai_agent.models import ExecutionPlan

if TYPE_CHECKING:
    from core.ai_agent.catalog import CatalogEntry


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a usable plan."""


class AIProvider(ABC):
    """Convert natural language into an execution plan.

    Providers receive only the already-filtered catalog. They have no executor,
    shell, PowerShell, subprocess, or filesystem mutation interface.
    """

    @abstractmethod
    def generate_plan(
        self,
        user_request: str,
        available_actions: Sequence["CatalogEntry"],
    ) -> ExecutionPlan:
        """Return a structured plan without executing any action."""
