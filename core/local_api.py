"""Authenticated loopback HTTP adapter for :class:`SmartActionCore`.

This module deliberately contains no business or privileged Windows logic.  It
only translates local HTTP requests into existing Core service calls, so a
future Web Control Center never needs direct filesystem or subprocess access.
"""
from __future__ import annotations

import json
import mimetypes
import secrets
from base64 import b64decode
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock, Thread
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlparse

from core.action_service import ActionConflictError, ActionNotFoundError
from core.execution_contracts import ExecutionRequest
from core.profile_manager import (
    ProfileError,
    build_profile,
    default_export_filename,
    import_profile,
)
from core.paths import WEB_CONTROL_CENTER_DIR
from core.smartaction_core import SmartActionCore


API_PREFIX = "/api/v1"
AUTH_HEADER = "X-SmartAction-Token"
MAX_REQUEST_BYTES = 512 * 1024
MAX_UPLOAD_REQUEST_BYTES = 16 * 1024 * 1024
SETTINGS_KEYS = frozenset(
    {
        "hotkey",
        "theme",
        "constellation",
        "constellation_color",
        "ui_theme",
        "ui_background",
        "ui_background_opacity",
        "ui_background_zoom",
        "ui_background_focus_x",
        "ui_background_focus_y",
    }
)


@dataclass(frozen=True)
class LocalApiEndpoint:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class LocalApiServer:
    """Run the authenticated Local API on an IPv4 loopback-only socket."""

    def __init__(
        self,
        core: SmartActionCore,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        token: str | None = None,
        on_settings_changed: Callable[[], None] | None = None,
        on_profile_imported: Callable[[], None] | None = None,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Local API may only bind to 127.0.0.1.")
        if not 0 <= int(port) <= 65535:
            raise ValueError("Local API port must be between 0 and 65535.")
        self._core = core
        self._host = host
        self._port = int(port)
        self._token = token or secrets.token_urlsafe(32)
        self._on_settings_changed = on_settings_changed
        self._on_profile_imported = on_profile_imported
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None
        self._lock = RLock()
        self._request_lock = RLock()

    @property
    def token(self) -> str:
        """Per-process credential. Do not log or expose it in status responses."""
        return self._token

    @property
    def endpoint(self) -> LocalApiEndpoint | None:
        with self._lock:
            if self._server is None:
                return None
            return LocalApiEndpoint(self._host, int(self._server.server_port))

    @property
    def control_center_url(self) -> str | None:
        """Authenticated browser URL; token stays in the fragment, never HTTP."""
        endpoint = self.endpoint
        if endpoint is None:
            return None
        return f"{endpoint.url}/#token={quote(self._token, safe='')}"

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._server is not None

    def start(self) -> LocalApiEndpoint:
        with self._lock:
            if self._server is not None:
                return self.endpoint  # type: ignore[return-value]
            handler = self._handler_type()
            server = ThreadingHTTPServer((self._host, self._port), handler)
            server.daemon_threads = True
            thread = Thread(
                target=server.serve_forever,
                name="SmartActionLocalApi",
                daemon=True,
            )
            self._server = server
            self._thread = thread
            thread.start()
            return LocalApiEndpoint(self._host, int(server.server_port))

    def stop(self) -> None:
        with self._lock:
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None
        if server is None:
            return
        server.shutdown()
        server.server_close()
        if thread is not None:
            thread.join(timeout=2)

    def _handler_type(self) -> type[BaseHTTPRequestHandler]:
        adapter = self

        class LocalApiHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802
                adapter._handle(self, "GET")

            def do_POST(self) -> None:  # noqa: N802
                adapter._handle(self, "POST")

            def do_PATCH(self) -> None:  # noqa: N802
                adapter._handle(self, "PATCH")

            def do_DELETE(self) -> None:  # noqa: N802
                adapter._handle(self, "DELETE")

            def do_OPTIONS(self) -> None:  # noqa: N802
                adapter._respond_error(
                    self,
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    "method_not_allowed",
                    "CORS preflight is not supported by the Local API.",
                )

            def log_message(self, _format: str, *_args: object) -> None:
                # Access logs are intentionally suppressed: a future Control Center
                # may include sensitive local identifiers in request paths.
                return

        return LocalApiHandler

    def _handle(self, handler: BaseHTTPRequestHandler, method: str) -> None:
        parsed = urlparse(handler.path)
        if method == "GET" and not parsed.query and self._serve_control_center(handler, parsed.path):
            return
        if parsed.query or parsed.fragment:
            self._respond_error(
                handler,
                HTTPStatus.BAD_REQUEST,
                "invalid_request_target",
                "Query strings and fragments are not supported.",
            )
            return
        if not self._authorised(handler):
            self._respond_error(
                handler,
                HTTPStatus.UNAUTHORIZED,
                "authentication_required",
                "A valid SmartAction Local API token is required.",
                headers={"WWW-Authenticate": "SmartActionToken"},
            )
            return

        try:
            # Service storage was designed for synchronous desktop use. Serialize
            # HTTP adapters so two browser requests cannot interleave a read/
            # validate/write cycle around the same Core repository.
            with self._request_lock:
                self._route(handler, method, parsed.path)
        except ActionNotFoundError as exc:
            self._respond_error(handler, HTTPStatus.NOT_FOUND, exc.code, str(exc))
        except ActionConflictError as exc:
            self._respond_error(handler, HTTPStatus.CONFLICT, exc.code, str(exc))
        except ProfileError as exc:
            self._respond_error(handler, HTTPStatus.BAD_REQUEST, "invalid_profile", str(exc))
        except (TypeError, ValueError) as exc:
            self._respond_error(handler, HTTPStatus.BAD_REQUEST, "validation_error", str(exc))
        except Exception:
            # Keep implementation and host details out of localhost HTTP responses.
            self._respond_error(
                handler,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "internal_error",
                "The SmartAction Local API could not complete the request.",
            )

    @staticmethod
    def _control_center_files() -> dict[str, Path]:
        return {
            "/": WEB_CONTROL_CENTER_DIR / "index.html",
            "/index.html": WEB_CONTROL_CENTER_DIR / "index.html",
            "/control-center.css": WEB_CONTROL_CENTER_DIR / "control-center.css",
            "/control-center.js": WEB_CONTROL_CENTER_DIR / "control-center.js",
            "/smartaction-logo.png": WEB_CONTROL_CENTER_DIR / "smartaction-logo.png",
        }

    def _serve_control_center(self, handler: BaseHTTPRequestHandler, path: str) -> bool:
        file_path = self._control_center_files().get(path)
        if file_path is None:
            return False
        try:
            body = file_path.read_bytes()
        except OSError:
            self._respond_error(
                handler,
                HTTPStatus.SERVICE_UNAVAILABLE,
                "control_center_unavailable",
                "The Web Control Center files are unavailable.",
            )
            return True
        content_type, _encoding = mimetypes.guess_type(file_path.name)
        self._respond_bytes(
            handler,
            HTTPStatus.OK,
            body,
            content_type or "application/octet-stream",
            headers={
                "Content-Security-Policy": (
                    "default-src 'self'; base-uri 'none'; form-action 'self'; "
                    "frame-ancestors 'none'; img-src 'self' data: blob:; "
                    "style-src 'self'; script-src 'self'; connect-src 'self'"
                ),
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
            },
        )
        return True

    def _route(self, handler: BaseHTTPRequestHandler, method: str, path: str) -> None:
        if method == "GET" and path == f"{API_PREFIX}/status":
            endpoint = self.endpoint
            self._respond_json(
                handler,
                HTTPStatus.OK,
                {
                    "core": self._core.status().to_dict(),
                    "api": {
                        "version": 1,
                        "endpoint": endpoint.url if endpoint else None,
                    },
                },
            )
            return

        if path == f"{API_PREFIX}/settings":
            if method == "GET":
                self._respond_json(handler, HTTPStatus.OK, {"settings": self._settings_snapshot()})
                return
            if method == "PATCH":
                body = self._read_body(handler)
                changes = body.get("changes")
                if not isinstance(changes, Mapping):
                    raise ValueError('"changes" must be an object.')
                result = self._core.config.update(changes)
                if self._on_settings_changed is not None and result.changed_keys:
                    self._on_settings_changed()
                self._respond_json(
                    handler,
                    HTTPStatus.OK,
                    {
                        "changedKeys": list(result.changed_keys),
                        "settings": self._filter_settings(result.after),
                    },
                )
                return

        if path == f"{API_PREFIX}/runtime-preferences":
            if method == "GET":
                self._respond_json(
                    handler, HTTPStatus.OK,
                    {"preferences": self._core.runtime_preferences.snapshot()},
                )
                return
            if method == "PATCH":
                body = self._read_body(handler)
                changes = body.get("changes")
                if not isinstance(changes, Mapping):
                    raise ValueError('"changes" must be an object.')
                self._respond_json(
                    handler, HTTPStatus.OK,
                    {"preferences": self._core.runtime_preferences.update(dict(changes))},
                )
                return

        if path == f"{API_PREFIX}/settings/background" and method == "POST":
            body = self._read_body(handler, max_bytes=MAX_UPLOAD_REQUEST_BYTES)
            filename = self._optional_text(body.get("filename"))
            content = self._base64_content(body.get("contentBase64"))
            if not filename:
                raise ValueError('"filename" is required.')
            relative_path = self._core.actions_config.install_ui_background_bytes(
                filename, content
            )
            if self._on_settings_changed is not None:
                self._on_settings_changed()
            self._respond_json(
                handler,
                HTTPStatus.OK,
                {"ui_background": relative_path},
            )
            return

        if path == f"{API_PREFIX}/settings/background" and method == "GET":
            background = self._core.actions_config.resolve_ui_background()
            if background is None or not background.is_file():
                self._respond_error(
                    handler,
                    HTTPStatus.NOT_FOUND,
                    "background_not_configured",
                    "No custom Control Center background is available.",
                )
                return
            try:
                background.resolve().relative_to(
                    self._core.actions_config.path.parent.resolve()
                )
            except ValueError:
                self._respond_error(
                    handler,
                    HTTPStatus.BAD_REQUEST,
                    "invalid_background_path",
                    "The configured background must be stored by SmartAction.",
                )
                return
            content_type, _encoding = mimetypes.guess_type(background.name)
            self._respond_bytes(
                handler,
                HTTPStatus.OK,
                background.read_bytes(),
                content_type or "application/octet-stream",
                headers={"X-Content-Type-Options": "nosniff"},
            )
            return

        if path == f"{API_PREFIX}/settings/background" and method == "DELETE":
            result = self._core.config.update({"ui_background": ""})
            if self._on_settings_changed is not None and result.changed_keys:
                self._on_settings_changed()
            self._respond_json(
                handler,
                HTTPStatus.OK,
                {"settings": self._filter_settings(result.after)},
            )
            return

        if path == f"{API_PREFIX}/profiles/export" and method == "GET":
            self._respond_json(
                handler,
                HTTPStatus.OK,
                {
                    "filename": default_export_filename(),
                    "profile": build_profile(
                        self._core.actions_config,
                        settings_path=self._core.legacy_config.path,
                        powershell_library=self._core.powershell.library,
                        workspace_store=self._core.client_workspaces.store,
                    ),
                },
            )
            return

        if path == f"{API_PREFIX}/profiles/import" and method == "POST":
            body = self._read_body(handler, max_bytes=MAX_UPLOAD_REQUEST_BYTES)
            profile = body.get("profile")
            if not isinstance(profile, Mapping):
                raise ValueError('"profile" must be an object.')
            self._import_profile_document(dict(profile))
            self._respond_json(handler, HTTPStatus.OK, {"imported": True})
            return

        if path == f"{API_PREFIX}/actions" and method == "GET":
            self._respond_json(handler, HTTPStatus.OK, {"actions": self._core.actions.list_actions()})
            return
        if path == f"{API_PREFIX}/actions" and method == "POST":
            body = self._read_body(handler)
            action = body.get("action")
            if not isinstance(action, Mapping):
                raise ValueError('"action" must be an object.')
            result = self._core.actions.create(
                action,
                parent_id=self._optional_text(body.get("parentId")),
                index=body.get("index"),
            )
            self._respond_json(handler, HTTPStatus.CREATED, self._action_result(result))
            return
        if path == f"{API_PREFIX}/actions/reorder" and method == "POST":
            body = self._read_body(handler)
            ordered_ids = body.get("orderedIds")
            if not isinstance(ordered_ids, list):
                raise ValueError('"orderedIds" must be an array.')
            result = self._core.actions.reorder(
                ordered_ids,
                parent_id=self._optional_text(body.get("parentId")),
            )
            self._respond_json(handler, HTTPStatus.OK, self._action_result(result))
            return

        action_id = self._path_id(path, f"{API_PREFIX}/actions/")
        if action_id is not None:
            if method == "PATCH":
                body = self._read_body(handler)
                changes = body.get("changes")
                if not isinstance(changes, Mapping):
                    raise ValueError('"changes" must be an object.')
                result = self._core.actions.update(action_id, changes)
                self._respond_json(handler, HTTPStatus.OK, self._action_result(result))
                return
            if method == "DELETE":
                result = self._core.actions.delete(action_id)
                self._respond_json(handler, HTTPStatus.OK, self._action_result(result))
                return

        capability = {
            f"{API_PREFIX}/powershell/execute": "powershell",
            f"{API_PREFIX}/client-workspace/execute": "client_workspace",
        }.get(path)
        if capability is not None and method == "POST":
            body = self._read_body(handler)
            operation = body.get("operation")
            payload = body.get("payload", {})
            request_id = body.get("requestId", "")
            request = ExecutionRequest(str(operation or ""), payload, request_id=str(request_id or ""))
            result = self._core.execute(capability, request)
            self._respond_json(
                handler,
                HTTPStatus.OK if result.success else HTTPStatus.UNPROCESSABLE_ENTITY,
                result.to_dict(),
            )
            return

        self._respond_error(
            handler,
            HTTPStatus.NOT_FOUND,
            "route_not_found",
            "The requested Local API route was not found.",
        )

    def _authorised(self, handler: BaseHTTPRequestHandler) -> bool:
        provided = handler.headers.get(AUTH_HEADER, "")
        return bool(provided) and secrets.compare_digest(provided, self._token)

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _path_id(path: str, prefix: str) -> str | None:
        if not path.startswith(prefix):
            return None
        identifier = path.removeprefix(prefix)
        if not identifier or "/" in identifier:
            return None
        return identifier

    def _settings_snapshot(self) -> dict[str, Any]:
        return self._filter_settings(self._core.config.snapshot())

    @staticmethod
    def _filter_settings(snapshot: Mapping[str, Any]) -> dict[str, Any]:
        return {key: snapshot.get(key) for key in sorted(SETTINGS_KEYS) if key in snapshot}

    @staticmethod
    def _action_result(result: Any) -> dict[str, Any]:
        return {
            "operation": result.operation,
            "actionId": result.action_id,
            "changed": result.changed,
            "actions": list(result.actions),
        }

    def _read_body(
        self,
        handler: BaseHTTPRequestHandler,
        *,
        max_bytes: int = MAX_REQUEST_BYTES,
    ) -> dict[str, Any]:
        content_type = handler.headers.get("Content-Type", "")
        if content_type.split(";", 1)[0].strip().casefold() != "application/json":
            raise ValueError("Content-Type must be application/json.")
        raw_length = handler.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError as exc:
            raise ValueError("Content-Length is required.") from exc
        if length < 0 or length > max_bytes:
            raise ValueError(f"Request body must be no larger than {max_bytes} bytes.")
        raw = handler.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must contain valid UTF-8 JSON.") from exc
        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object.")
        return value

    @staticmethod
    def _base64_content(value: Any) -> bytes:
        if not isinstance(value, str) or not value:
            raise ValueError('"contentBase64" is required.')
        try:
            return b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError('"contentBase64" must be valid base64.') from exc

    def _import_profile_document(self, profile: dict[str, Any]) -> None:
        """Use the existing file-based importer without exposing a disk path to Web."""
        from tempfile import NamedTemporaryFile

        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as file:
                json.dump(profile, file, ensure_ascii=False, separators=(",", ":"))
                temporary_path = Path(file.name)
            import_profile(
                temporary_path,
                self._core.actions_config,
                settings_path=self._core.legacy_config.path,
                powershell_library=self._core.powershell.library,
                workspace_store=self._core.client_workspaces.store,
            )
            if self._on_profile_imported is not None:
                self._on_profile_imported()
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def _respond_json(
        handler: BaseHTTPRequestHandler,
        status: HTTPStatus,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        LocalApiServer._respond_bytes(
            handler,
            status,
            body,
            "application/json; charset=utf-8",
            headers=headers,
        )

    @staticmethod
    def _respond_bytes(
        handler: BaseHTTPRequestHandler,
        status: HTTPStatus,
        body: bytes,
        content_type: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        handler.send_response(status.value)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(body)

    def _respond_error(
        self,
        handler: BaseHTTPRequestHandler,
        status: HTTPStatus,
        code: str,
        message: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self._respond_json(
            handler,
            status,
            {"error": {"code": code, "message": message}},
            headers=headers,
        )


__all__ = [
    "API_PREFIX",
    "AUTH_HEADER",
    "LocalApiEndpoint",
    "LocalApiServer",
    "MAX_REQUEST_BYTES",
    "MAX_UPLOAD_REQUEST_BYTES",
    "SETTINGS_KEYS",
]
