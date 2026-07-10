"""Strict, dependency-free data model for AI-generated execution plans."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"


class PlanModelError(ValueError):
    """Raised when provider output does not conform to the plan schema."""


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def parse(cls, value: object, field_name: str = "risk_level") -> "RiskLevel":
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            allowed = ", ".join(level.value for level in cls)
            raise PlanModelError(f"{field_name} must be one of: {allowed}.") from exc


@dataclass(frozen=True)
class PlanStep:
    action_type: str
    action_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW

    def __post_init__(self) -> None:
        if not isinstance(self.action_type, str) or not self.action_type.strip():
            raise PlanModelError("action_type is required.")
        if not isinstance(self.action_id, str) or not self.action_id.strip():
            raise PlanModelError("action_id is required.")
        if not isinstance(self.parameters, dict):
            raise PlanModelError("parameters must be an object.")
        if not isinstance(self.risk_level, RiskLevel):
            raise PlanModelError("risk_level must be a RiskLevel.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlanStep":
        if not isinstance(data, Mapping):
            raise PlanModelError("Each plan step must be an object.")
        expected = {"action_type", "action_id", "parameters", "risk_level"}
        unexpected = sorted(set(data) - expected)
        if unexpected:
            raise PlanModelError(f"Unexpected plan step fields: {', '.join(unexpected)}.")

        action_type = str(data.get("action_type", "")).strip()
        action_id = str(data.get("action_id", "")).strip()
        parameters = data.get("parameters", {})
        if not action_type:
            raise PlanModelError("action_type is required.")
        if not action_id:
            raise PlanModelError("action_id is required.")
        if not isinstance(parameters, Mapping):
            raise PlanModelError("parameters must be an object.")

        return cls(
            action_type=action_type,
            action_id=action_id,
            parameters=dict(parameters),
            risk_level=RiskLevel.parse(data.get("risk_level", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "action_id": self.action_id,
            "parameters": dict(self.parameters),
            "risk_level": self.risk_level.value,
        }


@dataclass(frozen=True)
class ExecutionPlan:
    schema_version: str
    summary: str
    steps: tuple[PlanStep, ...]
    requires_confirmation: bool

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise PlanModelError("schema_version is required.")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise PlanModelError("summary is required.")
        if not isinstance(self.steps, tuple) or not all(
            isinstance(step, PlanStep) for step in self.steps
        ):
            raise PlanModelError("steps must be a tuple of PlanStep values.")
        if not isinstance(self.requires_confirmation, bool):
            raise PlanModelError("requires_confirmation must be a boolean.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionPlan":
        if not isinstance(data, Mapping):
            raise PlanModelError("Execution plan must be an object.")
        expected = {"schema_version", "summary", "steps", "requires_confirmation"}
        unexpected = sorted(set(data) - expected)
        if unexpected:
            raise PlanModelError(f"Unexpected execution plan fields: {', '.join(unexpected)}.")

        schema_version = str(data.get("schema_version", "")).strip()
        summary = str(data.get("summary", "")).strip()
        raw_steps = data.get("steps")
        requires_confirmation = data.get("requires_confirmation")
        if not schema_version:
            raise PlanModelError("schema_version is required.")
        if not summary:
            raise PlanModelError("summary is required.")
        if not isinstance(raw_steps, list):
            raise PlanModelError("steps must be an array.")
        if not isinstance(requires_confirmation, bool):
            raise PlanModelError("requires_confirmation must be a boolean.")

        return cls(
            schema_version=schema_version,
            summary=summary,
            steps=tuple(PlanStep.from_dict(step) for step in raw_steps),
            requires_confirmation=requires_confirmation,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "summary": self.summary,
            "steps": [step.to_dict() for step in self.steps],
            "requires_confirmation": self.requires_confirmation,
        }

    @property
    def has_high_risk_step(self) -> bool:
        return any(step.risk_level is RiskLevel.HIGH for step in self.steps)
