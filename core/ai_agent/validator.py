"""Local allowlist validation for untrusted provider output."""
from __future__ import annotations

from dataclasses import dataclass

from core.ai_agent.catalog import ALLOWED_AI_TOOLS, ActionCatalog
from core.ai_agent.models import SCHEMA_VERSION, ExecutionPlan, PlanStep


class PlanValidationError(ValueError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(issues))


@dataclass(frozen=True)
class ValidationResult:
    plan: ExecutionPlan
    notices: tuple[str, ...] = ()


class ActionWhitelistValidator:
    """Resolve every plan step against saved, enabled SmartAction resources."""

    MAX_STEPS = 20

    def __init__(self, catalog: ActionCatalog) -> None:
        self._catalog = catalog

    def validate(self, plan: ExecutionPlan) -> ValidationResult:
        issues: list[str] = []
        notices: list[str] = []
        normalized_steps: list[PlanStep] = []

        if plan.schema_version != SCHEMA_VERSION:
            issues.append(
                f"Unsupported schema_version {plan.schema_version!r}; expected {SCHEMA_VERSION!r}."
            )
        if not plan.requires_confirmation:
            issues.append("requires_confirmation must be true.")
        if not plan.steps:
            issues.append("Execution plan must contain at least one step.")
        if len(plan.steps) > self.MAX_STEPS:
            issues.append(f"Execution plan exceeds the {self.MAX_STEPS}-step limit.")

        for index, step in enumerate(plan.steps, start=1):
            prefix = f"Step {index}"
            if step.action_type not in ALLOWED_AI_TOOLS:
                issues.append(f"{prefix}: action type {step.action_type!r} is not allowlisted.")
                continue
            entry = self._catalog.get(step.action_type, step.action_id)
            if entry is None:
                issues.append(
                    f"{prefix}: action {step.action_type}/{step.action_id} is not a saved allowlisted resource."
                )
                continue
            if step.parameters:
                issues.append(f"{prefix}: phase 1 does not accept AI-supplied parameters.")
                continue
            if entry.required_parameters:
                names = ", ".join(entry.required_parameters)
                issues.append(
                    f"{prefix}: saved action requires parameters ({names}); phase 1 cannot plan it."
                )
                continue
            if step.risk_level is not entry.risk_level:
                notices.append(
                    f"{prefix}: risk normalized from {step.risk_level.value} to {entry.risk_level.value}."
                )
            normalized_steps.append(
                PlanStep(
                    action_type=entry.action_type,
                    action_id=entry.action_id,
                    parameters={},
                    risk_level=entry.risk_level,
                )
            )

        if issues:
            raise PlanValidationError(issues)

        return ValidationResult(
            plan=ExecutionPlan(
                schema_version=SCHEMA_VERSION,
                summary=plan.summary,
                steps=tuple(normalized_steps),
                requires_confirmation=True,
            ),
            notices=tuple(notices),
        )
