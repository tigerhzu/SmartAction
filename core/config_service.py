"""Transport-neutral settings service over the existing actions document."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class ConfigRepository(Protocol):
    def snapshot(self) -> dict[str, Any]: ...

    def update_settings(self, changes: Mapping[str, Any]) -> None: ...


@dataclass(frozen=True)
class ConfigMutationResult:
    changed_keys: tuple[str, ...]
    before: dict[str, Any]
    after: dict[str, Any]


class ConfigService:
    """Validated, detached settings snapshots for Native and future Web adapters."""

    def __init__(self, repository: ConfigRepository) -> None:
        self._repository = repository

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._repository.snapshot())

    def update(self, changes: Mapping[str, Any]) -> ConfigMutationResult:
        requested = deepcopy(dict(changes))
        before = self.snapshot()
        self._repository.update_settings(requested)
        after = self.snapshot()
        changed = tuple(
            key for key in requested if before.get(key) != after.get(key)
        )
        return ConfigMutationResult(changed, before, after)


__all__ = ["ConfigMutationResult", "ConfigRepository", "ConfigService"]
