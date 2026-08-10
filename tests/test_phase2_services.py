"""Focused regression tests for the Phase 2 service/persistence boundaries.

These tests deliberately exercise the small, UI-free surfaces that Phase 2
introduces.  They keep the Qt windows out of the test path and use temporary
stores so a test cannot modify a developer's real SmartAction data.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.action_contracts import (
    ActionValidationError,
    action_type_labels,
    action_type_metadata,
    normalise_actions,
)
from core.action_service import ActionConfigService
from core.actions_config import ActionsConfig
from core.client_workspace import ClientWorkspaceStore
from core.client_workspace_service import ClientWorkspaceService
from core.config_manager import ConfigManager
from core.config_service import ConfigService
from core.execution_contracts import ExecutionRequest
from core.powershell_library import PowerShellLibrary
from core.powershell_service import PowerShellService
from core import profile_manager


class ActionsConfigBoundaryTests(unittest.TestCase):
    def test_raw_action_snapshot_is_detached_from_internal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ActionsConfig(Path(temp_dir) / "actions.json")
            original = config.get_raw_actions()
            self.assertTrue(original)
            original[0]["label"] = "mutated outside config"
            original[0].setdefault("sub_actions", []).append(
                {"id": "outside", "label": "Outside", "type": "url"}
            )

            snapshot = config.get_raw_actions()
            self.assertNotEqual(snapshot[0]["label"], "mutated outside config")
            self.assertNotIn(
                "outside",
                {child.get("id") for child in snapshot[0].get("sub_actions", [])},
            )

            # A read-only snapshot must not change the persisted document either.
            reloaded = ActionsConfig(Path(temp_dir) / "actions.json")
            self.assertNotEqual(reloaded.get_raw_actions()[0]["label"], "mutated outside config")

            # Action settings use the same atomic persistence boundary; the
            # destination should always be parseable and no staging file is
            # left behind after a successful mutation.
            config.set_hotkey("ctrl+shift+f24")
            persisted = json.loads((Path(temp_dir) / "actions.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["hotkey"], "ctrl+shift+f24")
            self.assertFalse(list(Path(temp_dir).glob("*.tmp")))
            self.assertFalse(list(Path(temp_dir).glob(".*.tmp")))


class ConfigServiceBoundaryTests(unittest.TestCase):
    def test_update_is_normalized_atomic_and_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "actions.json"
            config = ActionsConfig(path)
            service = ConfigService(config)

            result = service.update(
                {
                    "hotkey": "  ctrl+shift+f24  ",
                    "ui_background_opacity": 999,
                    "ui_background_zoom": 1,
                    "ui_background_focus_x": -1,
                    "ui_background_focus_y": 2,
                    "ui_theme": "not-a-theme",
                }
            )
            self.assertEqual(result.after["hotkey"], "ctrl+shift+f24")
            self.assertEqual(result.after["ui_background_opacity"], 100)
            self.assertEqual(result.after["ui_background_zoom"], 100)
            self.assertEqual(result.after["ui_background_focus_x"], 0.0)
            self.assertEqual(result.after["ui_background_focus_y"], 1.0)
            self.assertEqual(result.after["ui_theme"], "classic")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), config.snapshot())

            # Both snapshots in the result are detached from repository state.
            result.before["hotkey"] = "mutated-before"
            result.after["actions"][0]["label"] = "mutated-after"
            self.assertEqual(service.snapshot()["hotkey"], "ctrl+shift+f24")
            self.assertNotEqual(service.snapshot()["actions"][0]["label"], "mutated-after")

            disk_before = path.read_text(encoding="utf-8")
            memory_before = service.snapshot()
            with self.assertRaises(ValueError):
                service.update({"unknown_setting": "must fail", "ui_theme": "cute"})
            self.assertEqual(path.read_text(encoding="utf-8"), disk_before)
            self.assertEqual(service.snapshot(), memory_before)


class ActionContractAndServiceTests(unittest.TestCase):
    def test_action_metadata_and_normalisation_are_stable(self) -> None:
        labels = action_type_labels()
        self.assertEqual(labels["url"], "URL")
        self.assertTrue(action_type_metadata("folder").allows_children)  # type: ignore[union-attr]

        raw = [
            {
                "id": "folder",
                "label": "Folder",
                "type": "url",
                "target": "ignored for children",
                "sub_actions": [
                    {"id": "child", "label": "Child", "type": "url", "target": "https://example.com"}
                ],
            }
        ]
        clean = normalise_actions(raw)
        self.assertEqual(clean[0]["type"], "folder")
        self.assertEqual(clean[0]["target"], "")
        self.assertEqual(clean[0]["sub_actions"][0]["target"], "https://example.com")
        self.assertEqual(raw[0]["type"], "url")
        with self.assertRaises(ActionValidationError) as raised:
            normalise_actions(
                [
                    {"id": "same", "label": "One", "type": "url", "target": "https://one"},
                    {"id": "same", "label": "Two", "type": "url", "target": "https://two"},
                ]
            )
        self.assertEqual(raised.exception.code, "duplicate_action_id")

    def test_action_service_crud_returns_detached_structured_mutations(self) -> None:
        class Repository:
            def __init__(self) -> None:
                self.actions = []

            def action_snapshot(self):
                from copy import deepcopy

                return deepcopy(self.actions)

            def replace_action_snapshot(self, actions):
                from copy import deepcopy

                self.actions = deepcopy(actions)

        repository = Repository()
        service = ActionConfigService(repository)
        created = service.create(
            {"id": "portal", "label": "Portal", "type": "url", "target": "https://example.com"}
        )
        self.assertEqual(created.operation, "create")
        self.assertEqual(created.action_id, "portal")
        created.actions[0]["label"] = "changed result"
        self.assertEqual(service.list_actions()[0]["label"], "Portal")

        updated = service.update("portal", {"label": "Updated"})
        self.assertEqual(updated.operation, "update")
        self.assertEqual(service.list_actions()[0]["label"], "Updated")
        deleted = service.delete("portal")
        self.assertEqual(deleted.operation, "delete")
        self.assertEqual(service.list_actions(), [])


class AtomicPersistenceTests(unittest.TestCase):
    def test_workspace_writes_are_valid_and_leave_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = ClientWorkspaceStore(root / "workspaces.json")
            folder = store.add_folder("Operations")
            client = store.add_client(
                {
                    "id": "acme",
                    "name": "Acme",
                    "folderId": folder["id"],
                    "urls": [{"name": "Portal", "url": "https://example.com"}],
                }
            )
            persisted = json.loads((root / "workspaces.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["folders"][0]["id"], folder["id"])
            self.assertEqual(persisted["clients"][0]["folderId"], folder["id"])
            self.assertEqual(persisted["clients"][0]["id"], client["id"])
            self.assertFalse(list(root.glob("*.tmp")))
            self.assertFalse(list(root.glob(".*.tmp")))

    def test_client_workspace_service_exposes_structured_crud_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ClientWorkspaceStore(Path(temp_dir) / "workspaces.json")
            service = ClientWorkspaceService(store)

            folder_result = service.create_folder("Engineering", request_id="req-folder")
            self.assertTrue(folder_result.success)
            self.assertEqual(folder_result.operation, "create_folder")
            self.assertEqual(folder_result.request_id, "req-folder")
            folder_id = folder_result.value["id"]  # type: ignore[index]

            client_result = service.create_client(
                {
                    "id": "acme",
                    "name": "Acme",
                    "folderId": folder_id,
                    "urls": [{"name": "Portal", "url": "https://example.com"}],
                },
                request_id="req-client",
            )
            self.assertTrue(client_result.success)
            self.assertEqual(client_result.value["folderId"], folder_id)  # type: ignore[index]

            listed = service.execute(ExecutionRequest("list_clients", {}, request_id="req-list"))
            self.assertTrue(listed.success)
            self.assertEqual(listed.request_id, "req-list")
            self.assertEqual(listed.value[0]["id"], "acme")  # type: ignore[index]

            updated = service.update_client("acme", {"name": "Acme Updated", "folderId": folder_id, "urls": []})
            self.assertTrue(updated.success)
            self.assertEqual(updated.value["name"], "Acme Updated")  # type: ignore[index]

            missing = service.delete_client("unknown")
            self.assertFalse(missing.success)
            self.assertEqual(missing.error.code, "not_found")  # type: ignore[union-attr]

            imported = service.execute(
                ExecutionRequest(
                    "import_data",
                    {
                        "data": {
                            "version": "1.1",
                            "folders": [{"id": "sales", "name": "Sales"}],
                            "clients": [
                                {
                                    "id": "globex",
                                    "name": "Globex",
                                    "folderId": "sales",
                                    "urls": [{"name": "CRM", "url": "https://example.com/crm"}],
                                }
                            ],
                        }
                    },
                    request_id="req-import-data",
                )
            )
            self.assertTrue(imported.success)
            self.assertEqual(imported.value["client_count"], 1)  # type: ignore[index]
            self.assertTrue(Path(imported.value["backup_path"]).is_file())  # type: ignore[index]
            self.assertEqual(service.list_clients().value[0]["id"], "globex")  # type: ignore[index]

    def test_power_shell_service_crud_and_dispatch_use_execution_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            library = PowerShellLibrary(Path(temp_dir) / "library.json")
            service = PowerShellService(library)
            request = ExecutionRequest(
                "create",
                {
                    "script": {
                        "id": "phase2-test",
                        "name": "Phase 2 Test",
                        "script_content": "Write-Output ok",
                    }
                },
                request_id="req-create",
            )
            created = service.execute(request)
            self.assertTrue(created.success)
            self.assertEqual(created.operation, "create")
            self.assertEqual(created.request_id, "req-create")
            self.assertEqual(created.value["id"], "phase2-test")  # type: ignore[index]

            listed = service.list_scripts()
            self.assertTrue(listed.success)
            self.assertIn("phase2-test", {item["id"] for item in listed.value or []})

            missing = service.get_script("does-not-exist")
            self.assertFalse(missing.success)
            self.assertEqual(missing.error.code, "not_found")  # type: ignore[union-attr]

            unsupported = service.execute(ExecutionRequest("unknown", {}, request_id="req-unknown"))
            self.assertFalse(unsupported.success)
            self.assertEqual(unsupported.error.code, "unsupported_operation")  # type: ignore[union-attr]


class ProfileWorkspaceRoundTripTests(unittest.TestCase):
    def test_profile_round_trip_preserves_folders_and_folder_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_actions_path = root / "source-actions.json"
            source_workspace_path = root / "source-workspaces.json"
            source_library_path = root / "source-library.json"
            source_settings_path = root / "source-settings.json"
            export_path = root / "profile.json"

            source_config = ActionsConfig(source_actions_path)
            source_store = ClientWorkspaceStore(source_workspace_path)
            folder = source_store.add_folder("Engineering")
            source_store.add_client(
                {
                    "id": "client-acme",
                    "name": "Acme",
                    "folderId": folder["id"],
                    "urls": [{"name": "Portal", "url": "https://example.com"}],
                }
            )

            # ProfileManager's legacy constructors use application-wide paths;
            # point each dependency at this test's isolated stores.
            def config_factory(path: Path | None = None) -> ConfigManager:
                return ConfigManager(source_settings_path)

            def library_factory(path: Path | None = None) -> PowerShellLibrary:
                return PowerShellLibrary(source_library_path)

            def workspace_factory(path: Path | None = None) -> ClientWorkspaceStore:
                return ClientWorkspaceStore(source_workspace_path)

            with patch.object(profile_manager, "ConfigManager", config_factory), patch.object(
                profile_manager, "PowerShellLibrary", library_factory
            ), patch.object(profile_manager, "ClientWorkspaceStore", workspace_factory), patch.object(
                profile_manager, "WORKSPACE_PATH", source_workspace_path
            ), patch.object(profile_manager, "LIBRARY_PATH", source_library_path), patch.object(
                profile_manager, "BACKUPS_DIR", root / "backups"
            ):
                profile_manager.export_profile(export_path, source_config)

                exported = json.loads(export_path.read_text(encoding="utf-8"))
                self.assertEqual(exported["client_workspace_folders"][0]["id"], folder["id"])
                self.assertEqual(exported["client_workspaces"][0]["folderId"], folder["id"])

                # Import into a fresh action/workspace path while keeping the
                # same profile payload and verifying the folder reference survives.
                destination_actions_path = root / "destination-actions.json"
                destination_workspace_path = root / "destination-workspaces.json"
                destination_library_path = root / "destination-library.json"
                destination_settings_path = root / "destination-settings.json"
                destination_config = ActionsConfig(destination_actions_path)

                def dest_config_factory(path: Path | None = None) -> ConfigManager:
                    return ConfigManager(destination_settings_path)

                def dest_library_factory(path: Path | None = None) -> PowerShellLibrary:
                    return PowerShellLibrary(destination_library_path)

                def dest_workspace_factory(path: Path | None = None) -> ClientWorkspaceStore:
                    return ClientWorkspaceStore(destination_workspace_path)

                with patch.object(profile_manager, "ConfigManager", dest_config_factory), patch.object(
                    profile_manager, "PowerShellLibrary", dest_library_factory
                ), patch.object(profile_manager, "ClientWorkspaceStore", dest_workspace_factory), patch.object(
                    profile_manager, "WORKSPACE_PATH", destination_workspace_path
                ), patch.object(profile_manager, "LIBRARY_PATH", destination_library_path):
                    profile_manager.import_profile(export_path, destination_config)

                restored = ClientWorkspaceStore(destination_workspace_path)
                self.assertEqual(restored.folders(), [{"id": folder["id"], "name": "Engineering"}])
                self.assertEqual(restored.clients()[0]["folderId"], folder["id"])

                # Profiles written before folder support omitted the folder
                # field.  They should still import as an unassigned client
                # rather than being rejected.
                legacy_profile = dict(exported)
                legacy_profile.pop("client_workspace_folders", None)
                legacy_path = root / "legacy-profile.json"
                legacy_path.write_text(json.dumps(legacy_profile), encoding="utf-8")
                with patch.object(profile_manager, "ConfigManager", dest_config_factory), patch.object(
                    profile_manager, "PowerShellLibrary", dest_library_factory
                ), patch.object(profile_manager, "ClientWorkspaceStore", dest_workspace_factory), patch.object(
                    profile_manager, "WORKSPACE_PATH", destination_workspace_path
                ), patch.object(profile_manager, "LIBRARY_PATH", destination_library_path):
                    profile_manager.import_profile(legacy_path, destination_config)
                legacy_restored = ClientWorkspaceStore(destination_workspace_path)
                self.assertEqual(legacy_restored.folders(), [])
                self.assertEqual(legacy_restored.clients()[0]["folderId"], "")


if __name__ == "__main__":
    unittest.main()
