"""SmartAction AI planning foundation.

This package is deliberately execution-free in phase 1. Providers can only
produce plans, and every plan must pass the local action catalog validator.
"""

from core.ai_agent.catalog import ALLOWED_AI_TOOLS, ActionCatalog, CatalogEntry
from core.ai_agent.models import ExecutionPlan, PlanStep, RiskLevel
from core.ai_agent.provider import AIProvider, ProviderError
from core.ai_agent.service import AIAgentService, PlanProposal
from core.ai_agent.validator import ActionWhitelistValidator, PlanValidationError

__all__ = [
    "ALLOWED_AI_TOOLS",
    "AIProvider",
    "AIAgentService",
    "ActionCatalog",
    "ActionWhitelistValidator",
    "CatalogEntry",
    "ExecutionPlan",
    "PlanProposal",
    "PlanStep",
    "PlanValidationError",
    "ProviderError",
    "RiskLevel",
]
