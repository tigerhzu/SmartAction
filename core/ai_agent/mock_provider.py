"""Deterministic offline provider used by the phase-1 UI and tests."""
from __future__ import annotations

import re
from typing import Sequence

from core.ai_agent.catalog import CatalogEntry
from core.ai_agent.models import SCHEMA_VERSION, ExecutionPlan, PlanStep
from core.ai_agent.provider import AIProvider, ProviderError


class MockAIProvider(AIProvider):
    """Select one matching saved action without network or model access."""

    def generate_plan(
        self,
        user_request: str,
        available_actions: Sequence[CatalogEntry],
    ) -> ExecutionPlan:
        request = user_request.strip()
        if not request:
            raise ProviderError("Please enter a request.")

        desired_tools = _desired_tools(request)
        candidates = [entry for entry in available_actions if entry.action_type in desired_tools]
        if not candidates:
            candidates = list(available_actions)
        entry = _best_match(request, candidates)
        if entry is None:
            raise ProviderError(
                "Mock provider could not match the request to a saved allowlisted action."
            )

        return ExecutionPlan(
            schema_version=SCHEMA_VERSION,
            summary=request,
            steps=(
                PlanStep(
                    action_type=entry.action_type,
                    action_id=entry.action_id,
                    parameters={},
                    risk_level=entry.risk_level,
                ),
            ),
            requires_confirmation=True,
        )


def _desired_tools(request: str) -> tuple[str, ...]:
    folded = request.casefold()
    if any(token in folded for token in ("container", "容器")):
        return ("launch_firefox_container",)
    if any(token in folded for token in ("workspace", "工作環境", "工作區")):
        return ("launch_workspace",)
    if any(token in folded for token in ("powershell", "腳本", "script", "檢查", "check")):
        return ("run_saved_powershell_action",)
    if any(token in folded for token in ("folder", "資料夾", "目錄")):
        return ("open_folder",)
    if any(token in folded for token in ("url", "website", "site", "網站", "網頁")):
        return ("open_url",)
    if any(token in folded for token in ("app", "application", "程式", "應用")):
        return ("open_app",)
    return ()


def _best_match(request: str, entries: Sequence[CatalogEntry]) -> CatalogEntry | None:
    if not entries:
        return None
    folded = request.casefold()
    request_tokens = set(re.findall(r"[\w-]+", folded))
    scored: list[tuple[int, CatalogEntry]] = []
    for entry in entries:
        label = entry.label.casefold()
        action_id = entry.action_id.casefold()
        score = 0
        if label and label in folded:
            score += 100
        if action_id and action_id in folded:
            score += 90
        score += 10 * len(request_tokens & set(re.findall(r"[\w-]+", f"{label} {action_id}")))
        scored.append((score, entry))
    score, best = max(scored, key=lambda item: item[0])
    return best if score > 0 or len(entries) == 1 else None
