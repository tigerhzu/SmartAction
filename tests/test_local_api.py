from __future__ import annotations

import http.client
import json
import tempfile
import unittest
from base64 import b64encode
from pathlib import Path
from threading import Event
from unittest.mock import patch

from core.actions_config import ActionsConfig
from core.client_workspace import ClientWorkspaceStore
from core.client_workspace_service import ClientWorkspaceService
from core.config_manager import ConfigManager
from core.local_api import AUTH_HEADER, LocalApiServer
from core.powershell_library import PowerShellLibrary
from core.powershell_service import PowerShellLibraryService
from core.smartaction_core import SmartActionCore


class LocalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        root = Path(self._temp_dir.name)
        self.core = SmartActionCore(
            actions_config=ActionsConfig(root / "actions.json"),
            legacy_config=ConfigManager(root / "settings.json"),
            powershell=PowerShellLibraryService(PowerShellLibrary(root / "powershell.json")),
            client_workspaces=ClientWorkspaceService(ClientWorkspaceStore(root / "workspaces.json")),
        )
        self.settings_changed = Event()
        self.profile_imported = Event()
        self.server = LocalApiServer(
            self.core,
            token="phase3-test-token",
            on_settings_changed=self.settings_changed.set,
            on_profile_imported=self.profile_imported.set,
        )
        self.endpoint = self.server.start()

    def tearDown(self) -> None:
        self.server.stop()
        self._temp_dir.cleanup()

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        *,
        authenticated: bool = True,
    ) -> tuple[int, dict]:
        status, _headers, raw = self._raw_request(
            method,
            path,
            body,
            authenticated=authenticated,
        )
        return status, json.loads(raw)

    def _raw_request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        *,
        authenticated: bool = True,
    ) -> tuple[int, dict[str, str], str]:
        headers: dict[str, str] = {}
        encoded: str | None = None
        if authenticated:
            headers[AUTH_HEADER] = self.server.token
        if body is not None:
            encoded = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection = http.client.HTTPConnection(self.endpoint.host, self.endpoint.port, timeout=3)
        try:
            connection.request(method, path, body=encoded, headers=headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read().decode("utf-8")
        finally:
            connection.close()

    def test_loopback_api_requires_token_and_never_returns_it(self) -> None:
        status, payload = self._request("GET", "/api/v1/status", authenticated=False)
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"]["code"], "authentication_required")

        status, payload = self._request("GET", "/api/v1/status")
        self.assertEqual(status, 200)
        self.assertEqual(payload["core"]["app"], "SmartAction")
        self.assertEqual(payload["api"]["endpoint"], self.endpoint.url)
        self.assertNotIn(self.server.token, json.dumps(payload))

    def test_control_center_shell_is_same_origin_and_token_bootstraps_in_fragment(self) -> None:
        status, headers, html = self._raw_request("GET", "/", authenticated=False)
        self.assertEqual(status, 200)
        self.assertIn("SmartAction", html)
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(
            self.server.control_center_url,
            f"{self.endpoint.url}/#token={self.server.token}",
        )

        status, headers, css = self._raw_request("GET", "/control-center.css", authenticated=False)
        self.assertEqual(status, 200)
        self.assertIn("text/css", headers["Content-Type"])
        self.assertIn("--accent", css)

        status, headers, javascript = self._raw_request("GET", "/control-center.js", authenticated=False)
        self.assertEqual(status, 200)
        self.assertIn("javascript", headers["Content-Type"])
        self.assertIn("/api/v1/status", javascript)

    def test_settings_patch_is_core_backed(self) -> None:
        status, payload = self._request(
            "PATCH",
            "/api/v1/settings",
            {"changes": {"hotkey": "ctrl+shift+f24", "ui_background_opacity": 999}},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["changedKeys"], ["hotkey", "ui_background_opacity"])
        self.assertEqual(payload["settings"]["ui_background_opacity"], 100)
        self.assertTrue(self.settings_changed.wait(0.2))
        self.assertEqual(self.core.actions_config.get_hotkey(), "ctrl+shift+f24")

    def test_custom_background_is_served_to_the_authenticated_control_center(self) -> None:
        image = b"\x89PNG\r\n\x1a\ncontrol-center-background"
        self.core.actions_config.install_ui_background_bytes("background.png", image)

        connection = http.client.HTTPConnection(
            self.endpoint.host, self.endpoint.port, timeout=3
        )
        try:
            connection.request(
                "GET",
                "/api/v1/settings/background",
                headers={AUTH_HEADER: self.server.token},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn("image/png", response.getheader("Content-Type") or "")
            self.assertEqual(response.read(), image)
        finally:
            connection.close()

    def test_actions_and_privileged_services_use_explicit_core_routes(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/v1/actions",
            {"action": {"id": "portal", "label": "Portal", "type": "url", "target": "https://example.com"}},
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["actionId"], "portal")

        status, payload = self._request("GET", "/api/v1/actions")
        self.assertEqual(status, 200)
        self.assertIn("portal", {item["id"] for item in payload["actions"]})

        status, payload = self._request(
            "POST",
            "/api/v1/powershell/execute",
            {
                "operation": "create",
                "payload": {
                    "script": {
                        "id": "api-script",
                        "name": "API Script",
                        "script_content": "Write-Output api",
                    }
                },
                "requestId": "api-create",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["requestId"], "api-create")

        status, payload = self._request(
            "POST",
            "/api/v1/powershell/execute",
            {
                "operation": "update",
                "payload": {
                    "script_id": "api-script",
                    "script": {
                        "name": "Updated API Script",
                        "script_content": "Write-Output updated",
                        "category": "Custom",
                        "risk_level": "safe",
                        "need_admin": False,
                        "parameters": [],
                    },
                },
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["value"]["name"], "Updated API Script")

        status, payload = self._request(
            "POST", "/api/v1/powershell/execute", {"operation": "list", "payload": {}}
        )
        self.assertEqual(status, 200)
        self.assertIn("api-script", {script["id"] for script in payload["value"]})

        status, payload = self._request(
            "POST",
            "/api/v1/powershell/execute",
            {"operation": "delete", "payload": {"script_id": "api-script"}},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])

        status, payload = self._request(
            "POST",
            "/api/v1/client-workspace/execute",
            {"operation": "create_folder", "payload": {"name": "API Clients"}},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["value"]["name"], "API Clients")

    def test_server_refuses_non_loopback_host(self) -> None:
        with self.assertRaises(ValueError):
            LocalApiServer(self.core, host="0.0.0.0")

    def test_settings_background_and_runtime_preferences_stay_core_backed(self) -> None:
        # A minimal valid PNG signature is enough for the deliberately lightweight
        # upload validation; image decoding remains the native renderer's concern.
        image = b"\x89PNG\r\n\x1a\nphase4"
        status, payload = self._request(
            "POST",
            "/api/v1/settings/background",
            {"filename": "ring.png", "contentBase64": b64encode(image).decode("ascii")},
        )
        self.assertEqual(status, 200)
        relative = payload["ui_background"]
        self.assertTrue(relative.startswith("ui-backgrounds/background-"))
        self.assertTrue((self.core.actions_config.path.parent / relative).is_file())

        class Preferences:
            current = {"autostart": False, "reduced_motion": False}

            def snapshot(self):
                return dict(self.current)

            def update(self, changes):
                self.current.update(changes)
                return self.snapshot()

        self.core.runtime_preferences = Preferences()
        status, payload = self._request(
            "PATCH",
            "/api/v1/runtime-preferences",
            {"changes": {"autostart": True, "reduced_motion": True}},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["preferences"], {"autostart": True, "reduced_motion": True})

    def test_profile_export_reads_the_core_owned_repositories(self) -> None:
        self.core.powershell.create_script(
            {"id": "profile-script", "name": "Profile Script", "script_content": "Write-Output profile"}
        )
        self.core.client_workspaces.create_folder("Profile Clients")

        status, payload = self._request("GET", "/api/v1/profiles/export")
        self.assertEqual(status, 200)
        self.assertEqual(payload["profile"]["app"], "SmartAction")
        self.assertIn("profile-script", {script["id"] for script in payload["profile"]["powershell_library"]})
        self.assertIn("Profile Clients", {folder["name"] for folder in payload["profile"]["client_workspace_folders"]})

    def test_profile_import_uses_existing_importer_and_notifies_application(self) -> None:
        status, exported = self._request("GET", "/api/v1/profiles/export")
        self.assertEqual(status, 200)
        profile = exported["profile"]
        profile["actions_config"]["hotkey"] = "ctrl+shift+f24"
        with patch("core.profile_manager.BACKUPS_DIR", Path(self._temp_dir.name) / "backups"):
            status, payload = self._request("POST", "/api/v1/profiles/import", {"profile": profile})
        self.assertEqual(status, 200)
        self.assertTrue(payload["imported"])
        self.assertTrue(self.profile_imported.wait(0.2))
        self.assertEqual(self.core.actions_config.get_hotkey(), "ctrl+shift+f24")


if __name__ == "__main__":
    unittest.main()
