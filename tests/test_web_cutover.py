from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from app.application import Application


class _ViewRecorder:
    def __init__(self) -> None:
        self.views: list[str] = []

    def _open_control_center(self, view: str) -> None:
        self.views.append(view)


class _Api:
    control_center_url = "http://127.0.0.1:8765/#token=test-token"


class _Tray:
    def showMessage(self, *args, **kwargs) -> None:  # noqa: N802 - Qt API shape
        raise AssertionError(f"Unexpected tray error: {args!r} {kwargs!r}")


class _ControlCenterLauncher:
    _local_api = _Api()
    _tray = _Tray()


class WebOnlyCutoverTests(unittest.TestCase):
    def test_management_entry_wrappers_target_the_matching_web_view(self) -> None:
        recorder = _ViewRecorder()

        Application._open_settings(recorder)
        Application._open_powershell_library(recorder)
        Application._open_client_workspace(recorder)

        self.assertEqual(recorder.views, ["ring", "powershell", "workspace"])

    def test_control_center_url_uses_only_the_fragment_for_view_and_token(self) -> None:
        launcher = _ControlCenterLauncher()
        with patch("app.application.webbrowser.open", return_value=True) as browser_open:
            Application._open_control_center(launcher, "profiles")

        browser_open.assert_called_once_with(
            "http://127.0.0.1:8765/#view=profiles&token=test-token"
        )

    def test_default_tray_entry_uses_fragment_dashboard_deep_link(self) -> None:
        launcher = _ControlCenterLauncher()
        with patch("app.application.webbrowser.open", return_value=True) as browser_open:
            Application._open_control_center(launcher)

        url = browser_open.call_args.args[0]
        self.assertEqual(url, "http://127.0.0.1:8765/#view=dashboard&token=test-token")
        self.assertNotIn("?view=", url)

    def test_control_center_reads_navigation_and_token_from_the_fragment(self) -> None:
        script = (Path(__file__).parents[1] / "web_control_center" / "control-center.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('new URLSearchParams(location.hash.slice(1))', script)
        self.assertIn('const requestedView = launchFragment.get("view")', script)
        self.assertNotIn('new URLSearchParams(location.search).get("view")', script)

    def test_dashboard_and_workspace_use_direct_web_navigation_contracts(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertIn('class="dashboard-module"', html)
        self.assertIn('data-go="workspace"', html)
        self.assertIn("workspace-drag-handle", script)
        self.assertIn("workspace-client-urls", script)
        self.assertIn("new URL(entry.url)", script)

    def test_dashboard_is_direct_and_powershell_has_a_manual_sop_contract(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertNotIn('class="hero-card"', html)
        self.assertIn('id="ps-sop"', html)
        self.assertIn("手動執行 SOP", html)
        self.assertIn("openPowerShellSop", script)
        self.assertIn("script.script_content", script)

    def test_powershell_run_dialog_submits_to_core_and_disables_duplicate_runs(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertIn('id="ps-run-form"', html)
        self.assertIn('id="ps-confirm-run" type="submit"', html)
        self.assertIn('$("#ps-run-form").addEventListener("submit", runPowerShellScript)', script)
        self.assertIn("if (!script || state.psRunning) return", script)
        self.assertIn('submit.textContent = "Core 執行中…"', script)

    def test_powershell_execution_result_appears_before_the_script_list(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertLess(html.index('id="ps-run-result"'), html.index('id="ps-script-list"'))
        power_shell_view = html.index('id="view-powershell"')
        actions_view = html.index('id="view-actions"')
        self.assertGreater(html.index('id="ps-run-result"'), power_shell_view)
        self.assertGreater(power_shell_view, actions_view)
        self.assertIn('result.scrollIntoView({ behavior: "smooth", block: "start" })', script)

    def test_ring_settings_localise_constellations_and_preview_web_backgrounds(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        script = (root / "control-center.js").read_text(encoding="utf-8")
        stylesheet = (root / "control-center.css").read_text(encoding="utf-8")

        self.assertIn('aries: "牡羊座"', script)
        self.assertIn('scorpio: "天蠍座"', script)
        self.assertIn("applyControlCenterBackground", script)
        self.assertIn('fetch("/api/v1/settings/background"', script)
        self.assertIn("has-custom-background", stylesheet)

    def test_action_editor_has_a_compact_base_emoji_catalog(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertIn('id="emoji-picker-dialog"', html)
        self.assertIn('id="open-emoji-picker"', html)
        self.assertIn('id="close-emoji-picker"', html)
        self.assertNotIn('id="emoji-picker-search"', html)
        self.assertNotIn('id="emoji-count"', html)
        self.assertNotIn('id="clear-emoji-picker"', html)
        self.assertIn("const emojiCatalog", script)
        self.assertIn("renderEmojiCatalog", script)
        self.assertIn("setActionIcon", script)
        for modifier in ("🏻", "🏼", "🏽", "🏾", "🏿"):
            self.assertNotIn(modifier, script)

    def test_action_list_has_inline_emoji_management_and_large_catalog(self) -> None:
        root = Path(__file__).parents[1] / "web_control_center"
        html = (root / "index.html").read_text(encoding="utf-8")
        script = (root / "control-center.js").read_text(encoding="utf-8")

        self.assertIn("action-emoji-control", script)
        self.assertIn("item.append(handle, icon, info, controls)", script)
        self.assertIn("openEmojiPicker(action)", script)
        self.assertIn('id="emoji-category-tabs"', html)
        self.assertIn('emojiRange(0x1F300, 0x1F3FA)', script)
        self.assertIn('emojiRange(0x1F500, 0x1F5FF)', script)
        self.assertIn('grid-template-columns: 18px 38px minmax(0, 1fr) max-content', (root / "control-center.css").read_text(encoding="utf-8"))
        self.assertIn("flex-wrap: nowrap", (root / "control-center.css").read_text(encoding="utf-8"))

    def test_legacy_management_windows_and_fallbacks_are_removed(self) -> None:
        root = Path(__file__).parents[1]
        legacy_modules = (
            "settings_window.py",
            "powershell_library_window.py",
            "client_workspace_window.py",
            "background_crop_dialog.py",
            "emoji_picker.py",
            "help_modal.py",
            "hotkey_picker.py",
        )

        self.assertTrue(all(not (root / "ui" / module).exists() for module in legacy_modules))
        application = (root / "app" / "application.py").read_text(encoding="utf-8")
        spec = (root / "smartaction.spec").read_text(encoding="utf-8")
        self.assertNotIn("_open_legacy_", application)
        self.assertNotIn("settings_window", application)
        self.assertNotIn("powershell_library_window", spec)
        self.assertNotIn("client_workspace_window", spec)
