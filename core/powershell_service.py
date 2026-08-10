from __future__ import annotations

from collections.abc import Callable, Mapping
from threading import RLock
from typing import Any

from core.execution_contracts import ExecutionRequest, ExecutionResult
from core.powershell_library import PowerShellLibrary
from core.powershell_runner import PowerShellRunResult, is_user_admin, run_powershell_script


PowerShellRunner = Callable[
    [str, dict[str, str], list[dict[str, Any]]],
    PowerShellRunResult,
]


class PowerShellLibraryService:
    """UI-free boundary for library persistence and high-risk script execution.

    Methods are synchronous by design, but each call is self-contained and returns a
    transport-neutral result, so an application can safely submit it to a worker or
    job queue without importing UI code.
    """

    def __init__(
        self,
        library: PowerShellLibrary | None = None,
        *,
        runner: PowerShellRunner = run_powershell_script,
        admin_check: Callable[[], bool] = is_user_admin,
    ) -> None:
        self.library = library or PowerShellLibrary()
        self._runner = runner
        self._admin_check = admin_check
        self._lock = RLock()

    def execute(self, request: ExecutionRequest) -> ExecutionResult[Any]:
        """Dispatch a queue-friendly request without exposing implementation methods."""
        payload = dict(request.payload)
        operations: dict[str, Callable[[], ExecutionResult[Any]]] = {
            "reload": lambda: self.reload(request_id=request.request_id),
            "list": lambda: self.list_scripts(payload.get("category"), request_id=request.request_id),
            "get": lambda: self.get_script(payload.get("script_id", ""), request_id=request.request_id),
            "create": lambda: self.create_script(payload.get("script"), request_id=request.request_id),
            "update": lambda: self.update_script(
                payload.get("script_id", ""), payload.get("script"), request_id=request.request_id
            ),
            "delete": lambda: self.delete_script(payload.get("script_id", ""), request_id=request.request_id),
            "run": lambda: self.run_script(
                payload.get("script_id", ""),
                payload.get("values"),
                confirmed=payload.get("confirmed") is True,
                enforce_admin=payload.get("enforce_admin") is True,
                request_id=request.request_id,
            ),
        }
        operation = operations.get(request.operation)
        if operation is None:
            return ExecutionResult.failed(
                request.operation,
                "unsupported_operation",
                f'Unsupported PowerShell Library operation: "{request.operation}".',
                request_id=request.request_id,
            )
        return operation()

    def reload(self, *, request_id: str = "") -> ExecutionResult[dict[str, int]]:
        """Refresh the cached library object without invalidating existing UI references."""
        try:
            with self._lock:
                self.library.reload()
                script_count = len(self.library.scripts())
        except OSError as exc:
            return self._persistence_failure("reload", exc, request_id)
        return ExecutionResult.completed(
            "reload", {"script_count": script_count}, request_id=request_id
        )

    def list_scripts(
        self, category: Any = None, *, request_id: str = ""
    ) -> ExecutionResult[list[dict[str, Any]]]:
        with self._lock:
            scripts = self.library.scripts(str(category) if category is not None else None)
        return ExecutionResult.completed("list", scripts, request_id=request_id)

    def get_script(self, script_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, Any]]:
        identifier = str(script_id or "").strip()
        if not identifier:
            return self._validation("get", "Script id is required.", request_id)
        with self._lock:
            script = self.library.get(identifier)
        if script is None:
            return self._not_found("get", identifier, request_id)
        return ExecutionResult.completed("get", script, request_id=request_id)

    def create_script(
        self, script: Any, *, request_id: str = ""
    ) -> ExecutionResult[dict[str, Any]]:
        invalid = self._validate_script_payload("create", script, request_id)
        if invalid:
            return invalid
        try:
            with self._lock:
                requested_id = str(script.get("id", "")).strip()
                if requested_id and self.library.get(requested_id) is not None:
                    return ExecutionResult.failed(
                        "create",
                        "conflict",
                        "A PowerShell Library script with this id already exists.",
                        request_id=request_id,
                        details={"script_id": requested_id},
                    )
                created = self.library.add(dict(script))
        except OSError as exc:
            return self._persistence_failure("create", exc, request_id)
        return ExecutionResult.completed("create", created, request_id=request_id)

    def update_script(
        self, script_id: Any, script: Any, *, request_id: str = ""
    ) -> ExecutionResult[dict[str, Any]]:
        identifier = str(script_id or "").strip()
        if not identifier:
            return self._validation("update", "Script id is required.", request_id)
        invalid = self._validate_script_payload("update", script, request_id)
        if invalid:
            return invalid
        try:
            with self._lock:
                if self.library.get(identifier) is None:
                    return self._not_found("update", identifier, request_id)
                updated = self.library.update(identifier, dict(script))
        except OSError as exc:
            return self._persistence_failure("update", exc, request_id)
        return ExecutionResult.completed("update", updated, request_id=request_id)

    def delete_script(self, script_id: Any, *, request_id: str = "") -> ExecutionResult[dict[str, str]]:
        identifier = str(script_id or "").strip()
        if not identifier:
            return self._validation("delete", "Script id is required.", request_id)
        try:
            with self._lock:
                if self.library.get(identifier) is None:
                    return self._not_found("delete", identifier, request_id)
                self.library.delete(identifier)
        except OSError as exc:
            return self._persistence_failure("delete", exc, request_id)
        return ExecutionResult.completed("delete", {"script_id": identifier}, request_id=request_id)

    def run_script(
        self,
        script_id: Any,
        values: Any = None,
        *,
        confirmed: bool = False,
        enforce_admin: bool = False,
        request_id: str = "",
    ) -> ExecutionResult[PowerShellRunResult]:
        operation = "run"
        identifier = str(script_id or "").strip()
        if not identifier:
            return self._validation(operation, "Script id is required.", request_id)
        if values is None:
            values = {}
        if not isinstance(values, Mapping):
            return self._validation(operation, "Parameter values must be an object.", request_id)

        with self._lock:
            script = self.library.get(identifier)
        if script is None:
            return self._not_found(operation, identifier, request_id)
        if script.get("risk_level") == "dangerous" and not confirmed:
            return ExecutionResult.failed(
                operation,
                "confirmation_required",
                "This dangerous script requires explicit confirmation.",
                request_id=request_id,
                details={"script_id": identifier, "risk_level": "dangerous"},
            )
        if enforce_admin and script.get("need_admin") and not self._admin_check():
            return ExecutionResult.failed(
                operation,
                "administrator_required",
                "This script requires administrator privileges.",
                request_id=request_id,
                details={"script_id": identifier},
            )

        clean_values = {
            str(name): "" if value is None else str(value)
            for name, value in values.items()
        }
        missing = [
            str(parameter.get("name", ""))
            for parameter in script.get("parameters", [])
            if parameter.get("required") and not clean_values.get(str(parameter.get("name", ""))).strip()
        ]
        if missing:
            return ExecutionResult.failed(
                operation,
                "missing_parameters",
                "Required script parameters are missing.",
                request_id=request_id,
                details={"parameters": missing, "script_id": identifier},
            )

        try:
            result = self._runner(script["script_content"], clean_values, script.get("parameters", []))
        except Exception as exc:
            return ExecutionResult.failed(
                operation,
                "execution_error",
                "The PowerShell runner could not execute the script.",
                request_id=request_id,
                retryable=True,
                details={"exception_type": type(exc).__name__, "script_id": identifier},
            )
        if not result.success:
            return ExecutionResult.failed(
                operation,
                "script_failed",
                result.friendly_error or "The PowerShell script returned an error.",
                request_id=request_id,
                details={
                    "script_id": identifier,
                    "exit_code": result.exit_code,
                    "duration_seconds": result.duration_seconds,
                },
                value=result,
            )
        return ExecutionResult.completed(operation, result, request_id=request_id)

    @staticmethod
    def _validate_script_payload(
        operation: str, script: Any, request_id: str
    ) -> ExecutionResult[Any] | None:
        if not isinstance(script, Mapping):
            return PowerShellLibraryService._validation(operation, "Script must be an object.", request_id)
        if not str(script.get("name", "")).strip():
            return PowerShellLibraryService._validation(operation, "Script name is required.", request_id)
        if not str(script.get("script_content", "")).strip():
            return PowerShellLibraryService._validation(operation, "Script content is required.", request_id)
        return None

    @staticmethod
    def _validation(operation: str, message: str, request_id: str) -> ExecutionResult[Any]:
        return ExecutionResult.failed(operation, "validation_error", message, request_id=request_id)

    @staticmethod
    def _not_found(operation: str, script_id: str, request_id: str) -> ExecutionResult[Any]:
        return ExecutionResult.failed(
            operation,
            "not_found",
            "PowerShell Library script was not found.",
            request_id=request_id,
            details={"script_id": script_id},
        )

    @staticmethod
    def _persistence_failure(operation: str, exc: OSError, request_id: str) -> ExecutionResult[Any]:
        return ExecutionResult.failed(
            operation,
            "persistence_error",
            "The PowerShell Library could not be saved.",
            request_id=request_id,
            retryable=True,
            details={"exception_type": type(exc).__name__},
        )


# Short alias for callers that prefer a capability-oriented service name.
PowerShellService = PowerShellLibraryService
