"""Composition facade for SmartAction's transport-neutral core services."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.action_runner import ActionRunner
from core.actions_config import ActionsConfig
from core.app_info import APP_NAME, APP_VERSION
from core.client_workspace_service import ClientWorkspaceService
from core.config_service import ConfigService
from core.config_manager import ConfigManager
from core.execution_contracts import ExecutionRequest, ExecutionResult
from core.powershell_service import PowerShellLibraryService
from core.runtime_preferences import RuntimePreferencesService


@dataclass(frozen=True)
class CoreStatus:
    app: str
    version: str
    hotkey: str
    action_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "version": self.version,
            "hotkey": self.hotkey,
            "actionCount": self.action_count,
        }


class SmartActionCore:
    """Own long-lived Core services without depending on any Native Window."""

    def __init__(
        self,
        *,
        actions_config: ActionsConfig | None = None,
        legacy_config: ConfigManager | None = None,
        action_runner: ActionRunner | None = None,
        powershell: PowerShellLibraryService | None = None,
        client_workspaces: ClientWorkspaceService | None = None,
        runtime_preferences: RuntimePreferencesService | None = None,
    ) -> None:
        self.actions_config = actions_config or ActionsConfig()
        self.legacy_config = legacy_config or ConfigManager()
        self.config = ConfigService(self.actions_config)
        self.actions = self.actions_config.action_service
        self.action_runner = action_runner or ActionRunner()
        self._powershell = powershell
        self._client_workspaces = client_workspaces
        self.runtime_preferences = runtime_preferences or RuntimePreferencesService()

    @property
    def powershell(self) -> PowerShellLibraryService:
        if self._powershell is None:
            self._powershell = PowerShellLibraryService()
        return self._powershell

    @property
    def client_workspaces(self) -> ClientWorkspaceService:
        if self._client_workspaces is None:
            self._client_workspaces = ClientWorkspaceService()
        return self._client_workspaces

    def status(self) -> CoreStatus:
        return CoreStatus(
            app=APP_NAME,
            version=APP_VERSION,
            hotkey=self.actions_config.get_hotkey(),
            action_count=len(self.actions.list_actions()),
        )

    def reload_profile_resources(self) -> ExecutionResult[dict[str, str]]:
        """Refresh instantiated repositories after profile files are replaced.

        Repositories are reloaded in place so existing service and window references
        cannot later write their pre-import snapshots over the imported profile.
        Services that have never been instantiated need no action; their first access
        will load the newly imported files.
        """
        states: dict[str, str] = {
            "powershell": "not_loaded",
            "client_workspace": "not_loaded",
        }
        failures: dict[str, Any] = {}

        if self._powershell is not None:
            result = self._powershell.reload()
            states["powershell"] = "reloaded" if result.success else "reload_failed"
            if not result.success:
                failures["powershell"] = result.to_dict()

        if self._client_workspaces is not None:
            result = self._client_workspaces.reload()
            states["client_workspace"] = "reloaded" if result.success else "reload_failed"
            if not result.success:
                failures["client_workspace"] = result.to_dict()

        if failures:
            return ExecutionResult.failed(
                "reload_profile_resources",
                "resource_reload_failed",
                "One or more profile-backed resources could not be reloaded.",
                details={"states": states, "failures": failures},
                value=states,
            )
        return ExecutionResult.completed("reload_profile_resources", states)

    def execute(
        self,
        capability: str,
        request: ExecutionRequest,
    ) -> ExecutionResult[Any]:
        """Dispatch a transport-neutral request to a privileged Core service."""
        capability_id = str(capability).strip().casefold()
        if capability_id == "powershell":
            service = self.powershell
        elif capability_id == "client_workspace":
            service = self.client_workspaces
        else:
            return ExecutionResult.failed(
                request.operation,
                "unsupported_capability",
                f'Unsupported Core capability: "{capability}".',
                request_id=request.request_id,
            )
        return service.execute(request)


__all__ = ["CoreStatus", "SmartActionCore"]
