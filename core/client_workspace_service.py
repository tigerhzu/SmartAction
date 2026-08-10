from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from threading import RLock
from typing import Any

from core.client_workspace import (
    ClientWorkspaceError,
    ClientWorkspaceStore,
    FirefoxProfile,
    LaunchResult,
    check_firefox_helper,
    ensure_smartaction_firefox_profile,
    get_setup_status,
    install_firefox_helper_extension,
    launch_client_workspace,
    list_firefox_profiles,
    open_firefox_addons,
    repair_native_host_setup,
)
from core.execution_contracts import ExecutionRequest, ExecutionResult


class ClientWorkspaceService:
    """UI-free boundary around workspace storage, launch, helper, and setup actions."""

    def __init__(
        self,
        store: ClientWorkspaceStore | None = None,
        *,
        launcher: Callable[[dict[str, Any]], LaunchResult] = launch_client_workspace,
        helper_checker: Callable[[dict[str, Any], bool], dict[str, Any]] = check_firefox_helper,
        helper_installer: Callable[[dict[str, Any]], Path] = install_firefox_helper_extension,
        addons_opener: Callable[[dict[str, Any]], None] = open_firefox_addons,
        setup_repairer: Callable[[], Path] = repair_native_host_setup,
        setup_reader: Callable[[dict[str, Any], bool | None], dict[str, Any]] = get_setup_status,
        profile_creator: Callable[[], FirefoxProfile] = ensure_smartaction_firefox_profile,
        profile_lister: Callable[[], list[FirefoxProfile]] = list_firefox_profiles,
    ) -> None:
        self.store = store or ClientWorkspaceStore()
        self._launcher = launcher
        self._helper_checker = helper_checker
        self._helper_installer = helper_installer
        self._addons_opener = addons_opener
        self._setup_repairer = setup_repairer
        self._setup_reader = setup_reader
        self._profile_creator = profile_creator
        self._profile_lister = profile_lister
        self._lock = RLock()

    def execute(self, request: ExecutionRequest) -> ExecutionResult[Any]:
        """Dispatch a transport-neutral request suitable for a background worker."""
        payload = dict(request.payload)
        request_id = request.request_id
        operations: dict[str, Callable[[], ExecutionResult[Any]]] = {
            "reload": lambda: self.reload(request_id=request_id),
            "list_clients": lambda: self.list_clients(request_id=request_id),
            "list_folders": lambda: self.list_folders(request_id=request_id),
            "get_client": lambda: self.get_client(payload.get("client_id", ""), request_id=request_id),
            "create_client": lambda: self.create_client(payload.get("client"), request_id=request_id),
            "update_client": lambda: self.update_client(
                payload.get("client_id", ""), payload.get("client"), request_id=request_id
            ),
            "delete_client": lambda: self.delete_client(payload.get("client_id", ""), request_id=request_id),
            "create_folder": lambda: self.create_folder(payload.get("name", ""), request_id=request_id),
            "rename_folder": lambda: self.rename_folder(
                payload.get("folder_id", ""), payload.get("name", ""), request_id=request_id
            ),
            "delete_folder": lambda: self.delete_folder(payload.get("folder_id", ""), request_id=request_id),
            "set_layout": lambda: self.set_client_layout(payload.get("layout"), request_id=request_id),
            "import_data": lambda: self.import_data(payload.get("data"), request_id=request_id),
            "export": lambda: self.export_json(payload.get("path"), request_id=request_id),
            "import": lambda: self.import_json(payload.get("path"), request_id=request_id),
            "backup": lambda: self.backup(request_id=request_id),
            "launch": lambda: self.launch(payload.get("client_id", ""), request_id=request_id),
            "check_helper": lambda: self.check_helper(
                payload.get("client_id", ""),
                start_firefox=payload.get("start_firefox", True) is True,
                request_id=request_id,
            ),
            "install_helper": lambda: self.install_helper(payload.get("client_id", ""), request_id=request_id),
            "open_addons": lambda: self.open_addons(payload.get("client_id", ""), request_id=request_id),
            "repair_setup": lambda: self.repair_setup(request_id=request_id),
            "setup_status": lambda: self.setup_status(
                payload.get("client_id", ""), payload.get("helper_connected"), request_id=request_id
            ),
            "list_profiles": lambda: self.list_profiles(request_id=request_id),
            "create_profile": lambda: self.create_profile(request_id=request_id),
        }
        operation = operations.get(request.operation)
        if operation is None:
            return ExecutionResult.failed(
                request.operation,
                "unsupported_operation",
                f'Unsupported Client Workspace operation: "{request.operation}".',
                request_id=request_id,
            )
        return operation()

    def reload(self, *, request_id: str = "") -> ExecutionResult[dict[str, int]]:
        """Refresh the cached store object without invalidating existing UI references."""
        result = self._store_call("reload", request_id, self.store.reload)
        if not result.success:
            return result
        return ExecutionResult.completed(
            "reload",
            {
                "client_count": len(self.store.clients()),
                "folder_count": len(self.store.folders()),
            },
            request_id=result.request_id,
        )

    def list_clients(self, *, request_id: str = "") -> ExecutionResult[list[dict[str, Any]]]:
        with self._lock:
            value = self.store.clients()
        return ExecutionResult.completed("list_clients", value, request_id=request_id)

    def list_folders(self, *, request_id: str = "") -> ExecutionResult[list[dict[str, str]]]:
        with self._lock:
            value = self.store.folders()
        return ExecutionResult.completed("list_folders", value, request_id=request_id)

    def get_client(self, client_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, Any]]:
        identifier, error = self._identifier("get_client", "Client", client_id, request_id)
        if error:
            return error
        with self._lock:
            client = self.store.get(identifier)
        if client is None:
            return self._not_found("get_client", "Client", identifier, request_id)
        return ExecutionResult.completed("get_client", client, request_id=request_id)

    def create_client(self, client: Any, *, request_id: str = "") -> ExecutionResult[dict[str, Any]]:
        if not isinstance(client, Mapping):
            return self._validation("create_client", "Client must be an object.", request_id)
        return self._store_call("create_client", request_id, lambda: self.store.add_client(dict(client)))

    def update_client(
        self, client_id: Any, client: Any, *, request_id: str = ""
    ) -> ExecutionResult[dict[str, Any]]:
        identifier, error = self._identifier("update_client", "Client", client_id, request_id)
        if error:
            return error
        if not isinstance(client, Mapping):
            return self._validation("update_client", "Client must be an object.", request_id)
        with self._lock:
            if self.store.get(identifier) is None:
                return self._not_found("update_client", "Client", identifier, request_id)
        return self._store_call(
            "update_client", request_id, lambda: self.store.update_client(identifier, dict(client))
        )

    def delete_client(self, client_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, str]]:
        identifier, error = self._identifier("delete_client", "Client", client_id, request_id)
        if error:
            return error
        with self._lock:
            if self.store.get(identifier) is None:
                return self._not_found("delete_client", "Client", identifier, request_id)
        result = self._store_call("delete_client", request_id, lambda: self.store.delete_client(identifier))
        if result.success:
            return ExecutionResult.completed(
                "delete_client", {"client_id": identifier}, request_id=result.request_id
            )
        return result

    def create_folder(self, name: Any, *, request_id: str = "") -> ExecutionResult[dict[str, str]]:
        return self._store_call("create_folder", request_id, lambda: self.store.add_folder(str(name or "")))

    def rename_folder(
        self, folder_id: Any, name: Any, *, request_id: str = ""
    ) -> ExecutionResult[dict[str, str]]:
        identifier, error = self._identifier("rename_folder", "Folder", folder_id, request_id)
        if error:
            return error
        return self._store_call(
            "rename_folder", request_id, lambda: self.store.rename_folder(identifier, str(name or ""))
        )

    def delete_folder(self, folder_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, str]]:
        identifier, error = self._identifier("delete_folder", "Folder", folder_id, request_id)
        if error:
            return error
        result = self._store_call("delete_folder", request_id, lambda: self.store.delete_folder(identifier))
        if result.success:
            return ExecutionResult.completed(
                "delete_folder", {"folder_id": identifier}, request_id=result.request_id
            )
        return result

    def set_client_layout(self, layout: Any, *, request_id: str = "") -> ExecutionResult[dict[str, int]]:
        if not isinstance(layout, Sequence) or isinstance(layout, (str, bytes)):
            return self._validation("set_layout", "Client layout must be an array.", request_id)
        clean_layout: list[tuple[str, str]] = []
        for item in layout:
            if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) != 2:
                return self._validation(
                    "set_layout", "Each client layout item must contain client and folder ids.", request_id
                )
            clean_layout.append((str(item[0]), str(item[1])))
        result = self._store_call("set_layout", request_id, lambda: self.store.set_client_layout(clean_layout))
        if result.success:
            return ExecutionResult.completed(
                "set_layout", {"client_count": len(clean_layout)}, request_id=result.request_id
            )
        return result

    def import_data(self, data: Any, *, request_id: str = "") -> ExecutionResult[dict[str, Any]]:
        """Atomically replace workspace data supplied by an authenticated transport."""
        if not isinstance(data, Mapping):
            return self._validation("import_data", "Workspace data must be an object.", request_id)

        def replace() -> dict[str, Any]:
            backup = self.store.backup()
            self.store.save_data(dict(data))
            return {
                "backup_path": str(backup),
                "client_count": len(self.store.clients()),
                "folder_count": len(self.store.folders()),
            }

        return self._store_call("import_data", request_id, replace)

    def export_json(self, path: Any, *, request_id: str = "") -> ExecutionResult[Path]:
        destination, error = self._path("export", path, request_id)
        if error:
            return error
        result = self._store_call("export", request_id, lambda: self.store.export_json(destination))
        if result.success:
            return ExecutionResult.completed("export", destination, request_id=result.request_id)
        return result

    def import_json(self, path: Any, *, request_id: str = "") -> ExecutionResult[Path]:
        source, error = self._path("import", path, request_id)
        if error:
            return error
        if not source.is_file():
            return ExecutionResult.failed(
                "import", "not_found", "Workspace import file was not found.",
                request_id=request_id, details={"path": str(source)}
            )
        return self._store_call("import", request_id, lambda: self.store.import_json(source))

    def backup(self, *, request_id: str = "") -> ExecutionResult[Path]:
        return self._store_call("backup", request_id, self.store.backup)

    def launch(self, client_id: Any, *, request_id: str = "") -> ExecutionResult[LaunchResult]:
        client_result = self.get_client(client_id, request_id=request_id)
        if not client_result.success:
            return self._relabel(client_result, "launch")
        return self._external_call("launch", request_id, lambda: self._launcher(client_result.value))

    def check_helper(
        self, client_id: Any, *, start_firefox: bool = True, request_id: str = ""
    ) -> ExecutionResult[dict[str, Any]]:
        client_result = self.get_client(client_id, request_id=request_id)
        if not client_result.success:
            return self._relabel(client_result, "check_helper")
        return self._external_call(
            "check_helper", request_id,
            lambda: self._helper_checker(client_result.value, start_firefox),
        )

    def install_helper(self, client_id: Any, *, request_id: str = "") -> ExecutionResult[Path]:
        client_result = self.get_client(client_id, request_id=request_id)
        if not client_result.success:
            return self._relabel(client_result, "install_helper")
        return self._external_call(
            "install_helper", request_id, lambda: self._helper_installer(client_result.value)
        )

    def open_addons(self, client_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, str]]:
        client_result = self.get_client(client_id, request_id=request_id)
        if not client_result.success:
            return self._relabel(client_result, "open_addons")
        result = self._external_call(
            "open_addons", request_id, lambda: self._addons_opener(client_result.value)
        )
        if result.success:
            return ExecutionResult.completed(
                "open_addons", {"client_id": str(client_id)}, request_id=result.request_id
            )
        return result

    def repair_setup(self, *, request_id: str = "") -> ExecutionResult[Path]:
        return self._external_call("repair_setup", request_id, self._setup_repairer)

    def setup_status(
        self, client_id: Any, helper_connected: Any = None, *, request_id: str = ""
    ) -> ExecutionResult[dict[str, Any]]:
        client_result = self.get_client(client_id, request_id=request_id)
        if not client_result.success:
            return self._relabel(client_result, "setup_status")
        connected = helper_connected if isinstance(helper_connected, bool) else None
        return self._external_call(
            "setup_status", request_id,
            lambda: self._setup_reader(client_result.value, connected),
        )

    def list_profiles(self, *, request_id: str = "") -> ExecutionResult[list[dict[str, Any]]]:
        result = self._external_call("list_profiles", request_id, self._profile_lister)
        if not result.success:
            return result
        return ExecutionResult.completed(
            "list_profiles", [profile.to_dict() for profile in result.value], request_id=result.request_id
        )

    def create_profile(self, *, request_id: str = "") -> ExecutionResult[dict[str, Any]]:
        result = self._external_call("create_profile", request_id, self._profile_creator)
        if not result.success:
            return result
        return ExecutionResult.completed("create_profile", result.value.to_dict(), request_id=result.request_id)

    def _store_call(
        self, operation: str, request_id: str, callback: Callable[[], Any]
    ) -> ExecutionResult[Any]:
        try:
            with self._lock:
                value = callback()
            return ExecutionResult.completed(operation, value, request_id=request_id)
        except ClientWorkspaceError as exc:
            message = str(exc)
            folded = message.casefold()
            code = "conflict" if "already exists" in folded else "not_found" if "not found" in folded else "validation_error"
            return ExecutionResult.failed(operation, code, message, request_id=request_id)
        except (OSError, json.JSONDecodeError) as exc:
            return ExecutionResult.failed(
                operation,
                "persistence_error",
                "Client Workspace data could not be read or saved.",
                request_id=request_id,
                retryable=True,
                details={"exception_type": type(exc).__name__},
            )

    @staticmethod
    def _external_call(
        operation: str, request_id: str, callback: Callable[[], Any]
    ) -> ExecutionResult[Any]:
        try:
            return ExecutionResult.completed(operation, callback(), request_id=request_id)
        except ClientWorkspaceError as exc:
            return ExecutionResult.failed(
                operation, "workspace_error", str(exc), request_id=request_id, retryable=True
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ExecutionResult.failed(
                operation,
                "execution_error",
                "The Client Workspace operation could not be completed.",
                request_id=request_id,
                retryable=True,
                details={"exception_type": type(exc).__name__},
            )
        except Exception as exc:
            return ExecutionResult.failed(
                operation,
                "internal_error",
                "The Client Workspace operation failed unexpectedly.",
                request_id=request_id,
                details={"exception_type": type(exc).__name__},
            )

    @staticmethod
    def _identifier(
        operation: str, label: str, value: Any, request_id: str
    ) -> tuple[str, ExecutionResult[Any] | None]:
        identifier = str(value or "").strip()
        if not identifier:
            return "", ClientWorkspaceService._validation(
                operation, f"{label} id is required.", request_id
            )
        return identifier, None

    @staticmethod
    def _path(
        operation: str, value: Any, request_id: str
    ) -> tuple[Path, ExecutionResult[Any] | None]:
        if value is None or not str(value).strip():
            return Path(), ClientWorkspaceService._validation(
                operation, "File path is required.", request_id
            )
        return Path(value), None

    @staticmethod
    def _validation(operation: str, message: str, request_id: str) -> ExecutionResult[Any]:
        return ExecutionResult.failed(operation, "validation_error", message, request_id=request_id)

    @staticmethod
    def _not_found(
        operation: str, label: str, identifier: str, request_id: str
    ) -> ExecutionResult[Any]:
        return ExecutionResult.failed(
            operation,
            "not_found",
            f"{label} was not found.",
            request_id=request_id,
            details={f"{label.casefold()}_id": identifier},
        )

    @staticmethod
    def _relabel(result: ExecutionResult[Any], operation: str) -> ExecutionResult[Any]:
        return ExecutionResult(
            result.success, operation, result.request_id, value=result.value, error=result.error
        )
