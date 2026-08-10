"""Application service for validated action-tree CRUD operations."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from core.action_contracts import ActionValidationError, normalise_actions


class ActionRepository(Protocol):
    """Persistence boundary implemented by :class:`ActionsConfig`."""

    def action_snapshot(self) -> list[dict[str, Any]]: ...

    def replace_action_snapshot(self, actions: list[dict[str, Any]]) -> None: ...


@dataclass(frozen=True)
class ActionMutationResult:
    operation: str
    action_id: str | None
    changed: bool
    actions: tuple[dict[str, Any], ...]


class ActionNotFoundError(LookupError):
    def __init__(self, action_id: str) -> None:
        super().__init__(f'Action "{action_id}" was not found.')
        self.code = "action_not_found"
        self.action_id = action_id


class ActionConflictError(ValueError):
    def __init__(self, message: str, *, code: str = "action_conflict") -> None:
        super().__init__(message)
        self.code = code


class ActionConfigService:
    """Validated mutations independent of Qt or a future transport layer."""

    def __init__(self, repository: ActionRepository) -> None:
        self._repository = repository

    def list_actions(self) -> list[dict[str, Any]]:
        return deepcopy(self._repository.action_snapshot())

    def replace_all(self, actions: Sequence[Mapping[str, Any]]) -> ActionMutationResult:
        clean = normalise_actions(actions)
        changed = clean != self.list_actions()
        if changed:
            self._repository.replace_action_snapshot(clean)
        return self._result("replace", None, changed, clean)

    def create(
        self,
        action: Mapping[str, Any],
        *,
        parent_id: str | None = None,
        index: int | None = None,
    ) -> ActionMutationResult:
        actions = self.list_actions()
        destination = self._children(actions, parent_id)
        clean_action = normalise_actions([action])[0]
        if self._find(actions, clean_action["id"]) is not None:
            raise ActionConflictError(
                f'Action id "{clean_action["id"]}" already exists.',
                code="duplicate_action_id",
            )
        insertion_index = len(destination) if index is None else max(0, min(int(index), len(destination)))
        destination.insert(insertion_index, clean_action)
        clean = normalise_actions(actions)
        self._repository.replace_action_snapshot(clean)
        return self._result("create", clean_action["id"], True, clean)

    def update(
        self,
        action_id: str,
        changes: Mapping[str, Any],
    ) -> ActionMutationResult:
        actions = self.list_actions()
        current = self._find(actions, action_id)
        if current is None:
            raise ActionNotFoundError(action_id)
        replacement = {**current, **deepcopy(dict(changes)), "id": action_id}
        clean_replacement = normalise_actions([replacement])[0]
        if clean_replacement == current:
            return self._result("update", action_id, False, actions)
        current.clear()
        current.update(clean_replacement)
        clean = normalise_actions(actions)
        self._repository.replace_action_snapshot(clean)
        return self._result("update", action_id, True, clean)

    def delete(self, action_id: str) -> ActionMutationResult:
        actions = self.list_actions()
        removed = self._remove(actions, action_id)
        if not removed:
            raise ActionNotFoundError(action_id)
        clean = normalise_actions(actions)
        self._repository.replace_action_snapshot(clean)
        return self._result("delete", action_id, True, clean)

    def reorder(
        self,
        ordered_ids: Sequence[str],
        *,
        parent_id: str | None = None,
    ) -> ActionMutationResult:
        actions = self.list_actions()
        destination = self._children(actions, parent_id)
        ids = [str(action_id) for action_id in ordered_ids]
        current_ids = [str(action.get("id", "")) for action in destination]
        if len(ids) != len(set(ids)) or set(ids) != set(current_ids):
            raise ActionConflictError(
                "Action order must contain every sibling action exactly once.",
                code="invalid_action_order",
            )
        if ids == current_ids:
            return self._result("reorder", parent_id, False, actions)
        by_id = {str(action["id"]): action for action in destination}
        destination[:] = [by_id[action_id] for action_id in ids]
        clean = normalise_actions(actions)
        self._repository.replace_action_snapshot(clean)
        return self._result("reorder", parent_id, True, clean)

    @staticmethod
    def _result(
        operation: str,
        action_id: str | None,
        changed: bool,
        actions: list[dict[str, Any]],
    ) -> ActionMutationResult:
        return ActionMutationResult(operation, action_id, changed, tuple(deepcopy(actions)))

    @classmethod
    def _find(cls, actions: list[dict[str, Any]], action_id: str) -> dict[str, Any] | None:
        for action in actions:
            if str(action.get("id", "")) == str(action_id):
                return action
            found = cls._find(action.get("sub_actions", []), action_id)
            if found is not None:
                return found
        return None

    @classmethod
    def _remove(cls, actions: list[dict[str, Any]], action_id: str) -> bool:
        for index, action in enumerate(actions):
            if str(action.get("id", "")) == str(action_id):
                del actions[index]
                return True
            if cls._remove(action.get("sub_actions", []), action_id):
                return True
        return False

    @classmethod
    def _children(
        cls,
        actions: list[dict[str, Any]],
        parent_id: str | None,
    ) -> list[dict[str, Any]]:
        if parent_id is None:
            return actions
        parent = cls._find(actions, parent_id)
        if parent is None:
            raise ActionNotFoundError(parent_id)
        if parent.get("type") != "folder":
            raise ActionConflictError(
                f'Action "{parent_id}" does not accept child actions.',
                code="parent_not_folder",
            )
        return parent.setdefault("sub_actions", [])


__all__ = [
    "ActionConfigService",
    "ActionConflictError",
    "ActionMutationResult",
    "ActionNotFoundError",
    "ActionRepository",
    "ActionValidationError",
]
