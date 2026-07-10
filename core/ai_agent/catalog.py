"""Build the only action catalog an AI provider is allowed to reference."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.ai_agent.models import RiskLevel


ALLOWED_AI_TOOLS = frozenset(
    {
        "open_app",
        "open_url",
        "open_folder",
        "run_saved_powershell_action",
        "launch_workspace",
        "launch_firefox_container",
    }
)


@dataclass(frozen=True)
class CatalogEntry:
    action_type: str
    action_id: str
    label: str
    risk_level: RiskLevel
    description: str = ""
    required_parameters: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.action_type not in ALLOWED_AI_TOOLS:
            raise ValueError(f"Unsupported AI tool: {self.action_type!r}")
        if not self.action_id.strip():
            raise ValueError("Catalog action_id cannot be empty.")


class ActionCatalog:
    """Immutable view of saved SmartAction resources exposed to providers."""

    def __init__(self, entries: Iterable[CatalogEntry]) -> None:
        index: dict[tuple[str, str], CatalogEntry] = {}
        for entry in entries:
            key = (entry.action_type, entry.action_id)
            if key in index:
                raise ValueError(f"Duplicate catalog resource: {entry.action_type}/{entry.action_id}")
            index[key] = entry
        self._entries = tuple(index.values())
        self._index = index

    @property
    def entries(self) -> tuple[CatalogEntry, ...]:
        return self._entries

    def get(self, action_type: str, action_id: str) -> CatalogEntry | None:
        return self._index.get((action_type, action_id))

    @classmethod
    def from_sources(
        cls,
        actions_config,
        powershell_library,
        workspace_store,
    ) -> "ActionCatalog":
        entries: list[CatalogEntry] = []
        entries.extend(_ring_action_entries(actions_config.get_raw_actions()))
        entries.extend(_powershell_entries(powershell_library.scripts()))
        entries.extend(_workspace_entries(workspace_store.clients()))
        return cls(entries)


def _walk_enabled_actions(actions: Iterable[dict]) -> Iterable[dict]:
    for action in actions:
        if not isinstance(action, dict) or not action.get("enabled", True):
            continue
        yield action
        yield from _walk_enabled_actions(action.get("sub_actions", []))


def _ring_action_entries(actions: Iterable[dict]) -> Iterable[CatalogEntry]:
    for action in _walk_enabled_actions(actions):
        action_id = str(action.get("id", "")).strip()
        label = str(action.get("label", "")).strip() or action_id
        target = str(action.get("target", "")).strip()
        source_type = str(action.get("type", "")).strip()
        if not action_id or action.get("sub_actions"):
            continue
        if source_type == "url" and target:
            yield CatalogEntry("open_url", action_id, label, RiskLevel.LOW, target)
        elif source_type == "app" and target:
            tool = "open_folder" if Path(target).is_dir() else "open_app"
            yield CatalogEntry(tool, action_id, label, RiskLevel.LOW, target)


def _powershell_entries(scripts: Iterable[dict]) -> Iterable[CatalogEntry]:
    for script in scripts:
        script_id = str(script.get("id", "")).strip()
        if not script_id:
            continue
        risk = RiskLevel.HIGH if script.get("risk_level") == "dangerous" else RiskLevel.MEDIUM
        parameters = tuple(
            str(param.get("name", "")).strip()
            for param in script.get("parameters", [])
            if isinstance(param, dict) and str(param.get("name", "")).strip()
        )
        yield CatalogEntry(
            "run_saved_powershell_action",
            script_id,
            str(script.get("name", "")).strip() or script_id,
            risk,
            str(script.get("description", "")).strip(),
            parameters,
        )


def _workspace_entries(workspaces: Iterable[dict]) -> Iterable[CatalogEntry]:
    for workspace in workspaces:
        workspace_id = str(workspace.get("id", "")).strip()
        if not workspace_id:
            continue
        label = str(workspace.get("name", "")).strip() or workspace_id
        url_count = len(workspace.get("urls", []))
        yield CatalogEntry(
            "launch_workspace",
            workspace_id,
            label,
            RiskLevel.LOW,
            f"Saved workspace with {url_count} URL(s).",
        )
        container_name = str(workspace.get("containerName", "")).strip()
        if container_name:
            yield CatalogEntry(
                "launch_firefox_container",
                workspace_id,
                label,
                RiskLevel.LOW,
                f"Saved Firefox Container: {container_name}",
            )
