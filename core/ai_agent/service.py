"""Orchestrate provider output and local validation; contains no executor."""
from __future__ import annotations

from dataclasses import dataclass

from core.ai_agent.catalog import ActionCatalog
from core.ai_agent.models import ExecutionPlan
from core.ai_agent.provider import AIProvider, ProviderError
from core.ai_agent.validator import ActionWhitelistValidator


@dataclass(frozen=True)
class PlanProposal:
    plan: ExecutionPlan
    validation_notices: tuple[str, ...] = ()


class AIAgentService:
    def __init__(self, provider: AIProvider, catalog: ActionCatalog) -> None:
        self._provider = provider
        self._catalog = catalog
        self._validator = ActionWhitelistValidator(catalog)

    @property
    def catalog(self) -> ActionCatalog:
        return self._catalog

    def propose(self, user_request: str) -> PlanProposal:
        untrusted_plan = self._provider.generate_plan(user_request, self._catalog.entries)
        if not isinstance(untrusted_plan, ExecutionPlan):
            raise ProviderError("Provider did not return an ExecutionPlan.")
        result = self._validator.validate(untrusted_plan)
        return PlanProposal(result.plan, result.notices)
