from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.ai_agent.catalog import ALLOWED_AI_TOOLS, ActionCatalog, CatalogEntry
from core.ai_agent.mock_provider import MockAIProvider
from core.ai_agent.models import ExecutionPlan, PlanModelError, PlanStep, RiskLevel
from core.ai_agent.provider import AIProvider, ProviderError
from core.ai_agent.service import AIAgentService
from core.ai_agent.validator import ActionWhitelistValidator, PlanValidationError
from ui.ai_agent_window import AIAgentWindow
from ui.tray_icon import TrayIcon


class ExecutionPlanModelTests(unittest.TestCase):
    def test_schema_round_trip(self) -> None:
        raw = {
            "schema_version": "1.0",
            "summary": "Open Porsche workspace",
            "steps": [
                {
                    "action_type": "launch_workspace",
                    "action_id": "porsche-workspace",
                    "parameters": {},
                    "risk_level": "low",
                }
            ],
            "requires_confirmation": True,
        }
        self.assertEqual(ExecutionPlan.from_dict(raw).to_dict(), raw)

    def test_rejects_unexpected_provider_fields(self) -> None:
        raw = {
            "schema_version": "1.0",
            "summary": "Unsafe",
            "steps": [],
            "requires_confirmation": True,
            "powershell": "Remove-Item *",
        }
        with self.assertRaises(PlanModelError):
            ExecutionPlan.from_dict(raw)

    def test_direct_constructor_rejects_untyped_risk(self) -> None:
        with self.assertRaises(PlanModelError):
            PlanStep("launch_workspace", "workspace", {}, "low")  # type: ignore[arg-type]


class ActionWhitelistValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = ActionCatalog(
            [
                CatalogEntry(
                    "launch_workspace",
                    "porsche-workspace",
                    "Porsche",
                    RiskLevel.LOW,
                ),
                CatalogEntry(
                    "run_saved_powershell_action",
                    "vpn-check",
                    "VPN Check",
                    RiskLevel.MEDIUM,
                ),
                CatalogEntry(
                    "run_saved_powershell_action",
                    "restart-computer",
                    "Restart Computer",
                    RiskLevel.HIGH,
                ),
            ]
        )
        self.validator = ActionWhitelistValidator(self.catalog)

    def _plan(self, step: PlanStep, confirmation: bool = True) -> ExecutionPlan:
        return ExecutionPlan("1.0", "Test plan", (step,), confirmation)

    def test_allowlist_is_exactly_phase_one_tools(self) -> None:
        self.assertEqual(
            ALLOWED_AI_TOOLS,
            {
                "open_app",
                "open_url",
                "open_folder",
                "run_saved_powershell_action",
                "launch_workspace",
                "launch_firefox_container",
            },
        )

    def test_normalizes_provider_risk_from_catalog(self) -> None:
        result = self.validator.validate(
            self._plan(
                PlanStep(
                    "run_saved_powershell_action",
                    "restart-computer",
                    {},
                    RiskLevel.LOW,
                )
            )
        )
        self.assertEqual(result.plan.steps[0].risk_level, RiskLevel.HIGH)
        self.assertTrue(result.notices)

    def test_rejects_unknown_saved_action_id(self) -> None:
        with self.assertRaises(PlanValidationError):
            self.validator.validate(
                self._plan(PlanStep("launch_workspace", "invented", {}, RiskLevel.LOW))
            )

    def test_rejects_arbitrary_parameters(self) -> None:
        with self.assertRaises(PlanValidationError):
            self.validator.validate(
                self._plan(
                    PlanStep(
                        "run_saved_powershell_action",
                        "vpn-check",
                        {"command": "arbitrary"},
                        RiskLevel.MEDIUM,
                    )
                )
            )

    def test_rejects_plan_without_confirmation(self) -> None:
        with self.assertRaises(PlanValidationError):
            self.validator.validate(
                self._plan(
                    PlanStep("launch_workspace", "porsche-workspace", {}, RiskLevel.LOW),
                    confirmation=False,
                )
            )


class CatalogBuilderTests(unittest.TestCase):
    def test_catalog_contains_only_saved_supported_resources(self) -> None:
        class Actions:
            def __init__(self, folder: str) -> None:
                self.folder = folder

            def get_raw_actions(self):
                return [
                    {"id": "site", "label": "Portal", "type": "url", "target": "https://example.com"},
                    {"id": "folder", "label": "Files", "type": "app", "target": self.folder},
                    {"id": "raw-ps", "label": "Raw", "type": "powershell", "target": "whoami"},
                ]

        class Library:
            def scripts(self):
                return [
                    {
                        "id": "vpn-check",
                        "name": "VPN Check",
                        "risk_level": "safe",
                        "parameters": [],
                    }
                ]

        class Workspaces:
            def clients(self):
                return [
                    {
                        "id": "porsche-workspace",
                        "name": "Porsche",
                        "containerName": "Porsche",
                        "urls": [],
                    }
                ]

        with tempfile.TemporaryDirectory() as temp_dir:
            catalog = ActionCatalog.from_sources(Actions(temp_dir), Library(), Workspaces())

        keys = {(entry.action_type, entry.action_id) for entry in catalog.entries}
        self.assertIn(("open_url", "site"), keys)
        self.assertIn(("open_folder", "folder"), keys)
        self.assertIn(("run_saved_powershell_action", "vpn-check"), keys)
        self.assertIn(("launch_workspace", "porsche-workspace"), keys)
        self.assertIn(("launch_firefox_container", "porsche-workspace"), keys)
        self.assertNotIn(("powershell", "raw-ps"), keys)


class MockProviderTests(unittest.TestCase):
    def test_matches_named_workspace(self) -> None:
        catalog = ActionCatalog(
            [CatalogEntry("launch_workspace", "porsche-workspace", "Porsche", RiskLevel.LOW)]
        )
        proposal = AIAgentService(MockAIProvider(), catalog).propose(
            "幫我開啟 Porsche 工作環境"
        )
        self.assertEqual(proposal.plan.steps[0].action_id, "porsche-workspace")
        self.assertTrue(proposal.plan.requires_confirmation)

    def test_service_rejects_non_model_provider_output(self) -> None:
        class BadProvider(AIProvider):
            def generate_plan(self, user_request, available_actions):
                return {"summary": "not a model"}  # type: ignore[return-value]

        catalog = ActionCatalog(
            [CatalogEntry("launch_workspace", "workspace", "Workspace", RiskLevel.LOW)]
        )
        with self.assertRaises(ProviderError):
            AIAgentService(BadProvider(), catalog).propose("Open workspace")


class AIAgentWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_low_risk_plan_can_be_approved_as_preview(self) -> None:
        catalog = ActionCatalog(
            [CatalogEntry("launch_workspace", "porsche-workspace", "Porsche", RiskLevel.LOW)]
        )
        window = AIAgentWindow(AIAgentService(MockAIProvider(), catalog))
        window._request.setPlainText("幫我開啟 Porsche 工作環境")
        window._generate_plan()
        self.assertTrue(window.confirm_enabled)
        window.close()

    def test_high_risk_plan_cannot_be_approved(self) -> None:
        catalog = ActionCatalog(
            [
                CatalogEntry(
                    "run_saved_powershell_action",
                    "restart-computer",
                    "Restart Computer",
                    RiskLevel.HIGH,
                )
            ]
        )
        window = AIAgentWindow(AIAgentService(MockAIProvider(), catalog))
        window._request.setPlainText("Run PowerShell Restart Computer")
        window._generate_plan()
        self.assertFalse(window.confirm_enabled)
        window.close()

    def test_tray_hides_ai_entry_when_feature_is_off(self) -> None:
        hidden = TrayIcon(self.app, ai_agent_enabled=False)
        shown = TrayIcon(self.app, ai_agent_enabled=True)
        hidden_labels = [action.text() for action in hidden.contextMenu().actions()]
        shown_labels = [action.text() for action in shown.contextMenu().actions()]
        self.assertNotIn("AI Agent (Preview)", hidden_labels)
        self.assertIn("AI Agent (Preview)", shown_labels)


if __name__ == "__main__":
    unittest.main()
