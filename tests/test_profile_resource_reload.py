from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.actions_config import ActionsConfig
from core.client_workspace import ClientWorkspaceStore, WORKSPACE_VERSION
from core.client_workspace_service import ClientWorkspaceService
from core.config_manager import ConfigManager
from core.powershell_library import PowerShellLibrary
from core.powershell_service import PowerShellLibraryService
from core.smartaction_core import SmartActionCore


class ProfileResourceReloadTests(unittest.TestCase):
    def test_core_reloads_cached_repositories_in_place_after_external_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            library_path = root / "powershell.json"
            workspace_path = root / "workspaces.json"
            library = PowerShellLibrary(library_path)
            library.add(
                {"id": "stale", "name": "Stale", "script_content": "Write-Output stale"}
            )
            store = ClientWorkspaceStore(workspace_path)
            store.add_client({"id": "stale", "name": "Stale", "urls": []})
            powershell = PowerShellLibraryService(library)
            workspaces = ClientWorkspaceService(store)
            core = SmartActionCore(
                actions_config=ActionsConfig(root / "actions.json"),
                legacy_config=ConfigManager(root / "settings.json"),
                powershell=powershell,
                client_workspaces=workspaces,
            )

            library_path.write_text(
                json.dumps(
                    {
                        "version": "1.1",
                        "scripts": [
                            {
                                "id": "imported",
                                "name": "Imported",
                                "script_content": "Write-Output imported",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            workspace_path.write_text(
                json.dumps(
                    {
                        "version": WORKSPACE_VERSION,
                        "folders": [],
                        "clients": [
                            {"id": "imported", "name": "Imported", "urls": []}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = core.reload_profile_resources()

            self.assertTrue(result.success)
            self.assertIs(core.powershell.library, library)
            self.assertIs(core.client_workspaces.store, store)
            self.assertIsNotNone(library.get("imported"))
            self.assertIsNone(library.get("stale"))
            self.assertIsNotNone(store.get("imported"))
            self.assertIsNone(store.get("stale"))

            # A later edit must build on imported state, not resurrect the stale cache.
            powershell.create_script(
                {"id": "later", "name": "Later", "script_content": "Write-Output later"}
            )
            workspaces.create_client({"id": "later", "name": "Later", "urls": []})
            persisted_library = json.loads(library_path.read_text(encoding="utf-8"))
            persisted_workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
            self.assertIn("imported", {item["id"] for item in persisted_library["scripts"]})
            self.assertNotIn("stale", {item["id"] for item in persisted_library["scripts"]})
            self.assertEqual(
                {"imported", "later"},
                {item["id"] for item in persisted_workspace["clients"]},
            )


if __name__ == "__main__":
    unittest.main()
