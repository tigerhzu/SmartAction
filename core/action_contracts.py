"""Core contracts, metadata, and validation for configured actions."""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ActionTypeMetadata:
    """Stable presentation and schema metadata for one action type."""

    id: str
    label: str
    requires_target: bool = True
    allows_children: bool = False


ACTION_TYPES: tuple[ActionTypeMetadata, ...] = (
    ActionTypeMetadata("folder", "Folder", requires_target=False, allows_children=True),
    ActionTypeMetadata("settings", "Settings", requires_target=False),
    ActionTypeMetadata("url", "URL"),
    ActionTypeMetadata("app", "App / File"),
    ActionTypeMetadata("command", "Command"),
    ActionTypeMetadata("powershell", "PowerShell"),
    ActionTypeMetadata("powershell_library", "PowerShell Library", requires_target=False),
    ActionTypeMetadata("environment_check", "Environment Check", requires_target=False),
    ActionTypeMetadata("client_workspace", "Client Workspace", requires_target=False),
    ActionTypeMetadata("paste", "Paste"),
    ActionTypeMetadata("form", "Form"),
    ActionTypeMetadata("ps_form", "PS Form"),
)

_ACTION_TYPES_BY_ID = {item.id: item for item in ACTION_TYPES}
ACTION_TYPE_ORDER: tuple[str, ...] = tuple(item.id for item in ACTION_TYPES)
ACTION_TYPE_LABELS: Mapping[str, str] = MappingProxyType(
    {item.id: item.label for item in ACTION_TYPES}
)
TARGETLESS_ACTION_TYPES: frozenset[str] = frozenset(
    item.id for item in ACTION_TYPES if not item.requires_target
)


def action_type_metadata(action_type: str) -> ActionTypeMetadata | None:
    return _ACTION_TYPES_BY_ID.get(str(action_type))


def action_type_labels() -> dict[str, str]:
    """Return a detached id-to-label snapshot for UI/API adapters."""
    return dict(ACTION_TYPE_LABELS)


def ordered_action_types(*, include_folders: bool = True) -> tuple[str, ...]:
    return tuple(
        item.id for item in ACTION_TYPES if include_folders or not item.allows_children
    )


def targetless_action_types() -> frozenset[str]:
    return TARGETLESS_ACTION_TYPES


@dataclass(frozen=True)
class ActionValidationIssue:
    code: str
    path: str
    message: str


class ActionValidationError(ValueError):
    """Structured action schema error suitable for native or HTTP adapters."""

    def __init__(self, issue: ActionValidationIssue) -> None:
        super().__init__(issue.message)
        self.issue = issue
        self.code = issue.code
        self.path = issue.path


def _fail(code: str, path: str, message: str) -> None:
    raise ActionValidationError(ActionValidationIssue(code, path, message))


def _normalise_enabled(value: Any, path: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        folded = value.strip().casefold()
        if folded in {"true", "yes", "on", "1"}:
            return True
        if folded in {"false", "no", "off", "0"}:
            return False
    _fail("invalid_enabled", path, f"{path} must be a boolean.")


def normalise_actions(actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate and return a detached canonical action tree.

    Unknown non-empty action types remain valid for extension compatibility;
    known types use the metadata above for target/children normalization.
    IDs are required to be unique across the full tree.
    """
    if not isinstance(actions, (list, tuple)):
        _fail("invalid_actions", "actions", "Actions must be a list.")

    seen_ids: set[str] = set()

    def normalise_one(raw: Mapping[str, Any], path: str) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            _fail("invalid_action", path, f"{path} must be an object.")

        action = copy.deepcopy(dict(raw))
        action_id = str(action.get("id", "") or "").strip()
        if not action_id:
            action_id = f"act_{uuid.uuid4().hex[:8]}"
        if action_id in seen_ids:
            _fail(
                "duplicate_action_id",
                f"{path}.id",
                f'{path}.id duplicates action id "{action_id}".',
            )
        seen_ids.add(action_id)

        label = str(action.get("label", "") or "").strip()
        if not label:
            _fail("label_required", f"{path}.label", f"{path}.label is required.")

        raw_children = action.get("sub_actions", [])
        if raw_children is None:
            raw_children = []
        if not isinstance(raw_children, (list, tuple)):
            _fail(
                "invalid_sub_actions",
                f"{path}.sub_actions",
                f"{path}.sub_actions must be a list.",
            )

        action_type = str(action.get("type", "") or "").strip()
        if not action_type:
            action_type = "folder" if raw_children else "command"
        metadata = action_type_metadata(action_type)
        if raw_children and metadata is not None and not metadata.allows_children:
            # Existing configurations have historically treated any action with
            # children as a folder. Canonicalize that documented behavior.
            action_type = "folder"
            metadata = action_type_metadata(action_type)

        target = str(action.get("target", "") or "")
        if metadata is not None and not metadata.requires_target:
            target = ""

        action["id"] = action_id
        action["label"] = label
        action["short_label"] = str(action.get("short_label", "") or "").strip()
        action["icon"] = str(action.get("icon", "") or "").strip()
        action["type"] = action_type
        action["target"] = target
        action["enabled"] = _normalise_enabled(
            action.get("enabled", True), f"{path}.enabled"
        )
        action["sub_actions"] = [
            normalise_one(child, f"{path}.sub_actions[{index}]")
            for index, child in enumerate(raw_children)
        ]
        if action_type == "powershell_library":
            action.pop("script_id", None)
        return action

    return [
        normalise_one(action, f"actions[{index}]")
        for index, action in enumerate(actions)
    ]
