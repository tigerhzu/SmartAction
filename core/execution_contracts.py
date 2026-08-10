from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Generic, Mapping, TypeVar
from uuid import uuid4


T = TypeVar("T")


@dataclass(frozen=True)
class ExecutionRequest:
    """A transport-neutral unit of work that can be handed to a job queue."""

    operation: str
    payload: Mapping[str, Any]
    request_id: str = ""

    def __post_init__(self) -> None:
        operation = str(self.operation or "").strip()
        if not operation:
            raise ValueError("Execution operation is required.")
        if not isinstance(self.payload, Mapping):
            raise TypeError("Execution payload must be a mapping.")
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "payload", deepcopy(dict(self.payload)))
        if not self.request_id:
            object.__setattr__(self, "request_id", uuid4().hex)


@dataclass(frozen=True)
class ExecutionError:
    code: str
    message: str
    retryable: bool = False
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            result["details"] = _serialise(self.details)
        return result


@dataclass(frozen=True)
class ExecutionResult(Generic[T]):
    """Structured service result; failures do not need exception-based control flow."""

    success: bool
    operation: str
    request_id: str
    value: T | None = None
    error: ExecutionError | None = None

    @classmethod
    def completed(
        cls,
        operation: str,
        value: T | None = None,
        *,
        request_id: str = "",
    ) -> "ExecutionResult[T]":
        return cls(True, operation, request_id or uuid4().hex, value=value)

    @classmethod
    def failed(
        cls,
        operation: str,
        code: str,
        message: str,
        *,
        request_id: str = "",
        retryable: bool = False,
        details: Mapping[str, Any] | None = None,
        value: T | None = None,
    ) -> "ExecutionResult[T]":
        return cls(
            False,
            operation,
            request_id or uuid4().hex,
            value=value,
            error=ExecutionError(code, message, retryable, details),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "operation": self.operation,
            "requestId": self.request_id,
            "value": _serialise(self.value),
            "error": self.error.to_dict() if self.error else None,
        }


def _serialise(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _serialise(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _serialise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialise(item) for item in value]
    return value
