from __future__ import annotations

import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

from core.actions.settings_action import SettingsAction
from core.actions_config import ActionsConfig
from core.client_workspace import (
    WORKSPACE_VERSION,
    ClientWorkspaceStore,
    validate_workspace_data,
)
from core.constellation import (
    CONSTELLATIONS,
    CONSTELLATION_ORDER,
    DEFAULT_CONSTELLATION,
    DEFAULT_CONSTELLATION_COLOR,
    normalise_constellation_color,
)
from core.menu_model import MenuItem
from platforms.windows import (
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    parse_hotkey,
)
from tools.build_emoji_database import parse_emoji_test
from ui.emoji_picker import CATALOG
from ui.ring_ui import RingWindow, WINDOW_SIZE
from ui.theme_painter import preload_theme_assets, prune_theme_asset_cache
from ui.window_utils import center_window, screen_for_widget


class HotkeyRegressionTests(unittest.TestCase):
    def test_windows_hotkey_parser_supports_picker_keys(self) -> None:
        modifiers, virtual_key = parse_hotkey("ctrl+shift+f24")
        self.assertEqual(modifiers, MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT)
        self.assertEqual(virtual_key, 0x87)
        self.assertEqual(parse_hotkey("F13")[1], 0x7C)

    def test_windows_hotkey_parser_rejects_invalid_combos(self) -> None:
        for combo in ("ctrl+alt", "ctrl+a+b", "ctrl+pageup"):
            with self.subTest(combo=combo), self.assertRaises(ValueError):
                parse_hotkey(combo)


class EmojiRegressionTests(unittest.TestCase):
    def test_builder_and_runtime_catalog_drop_skin_tone_variants(self) -> None:
        wave = "\U0001F44B"
        light = "\U0001F3FB"
        dark = "\U0001F3FF"
        sample = f"""
# group: People & Body
# subgroup: hand-fingers-open
1F44B       ; fully-qualified # {wave} E0.6 waving hand
1F44B 1F3FB ; fully-qualified # {wave}{light} E1.0 waving hand: light skin tone
1F44B 1F3FF ; fully-qualified # {wave}{dark} E1.0 waving hand: dark skin tone
"""
        parsed = parse_emoji_test(sample)
        self.assertEqual([item["icon"] for item in parsed], [wave])
        self.assertFalse(
            any(
                0x1F3FB <= ord(char) <= 0x1F3FF
                for item in CATALOG
                for char in item.icon
            )
        )


class ConstellationAndSettingsActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_all_zodiac_constellations_have_valid_geometry(self) -> None:
        self.assertEqual(len(CONSTELLATION_ORDER), 12)
        for constellation_id in CONSTELLATION_ORDER:
            data = CONSTELLATIONS[constellation_id]
            self.assertGreaterEqual(len(data["stars"]), 5)
            for x, y, brightness in data["stars"]:
                self.assertGreaterEqual(x, 0.0)
                self.assertLessEqual(x, 1.0)
                self.assertGreaterEqual(y, 0.0)
                self.assertLessEqual(y, 1.0)
                self.assertGreater(brightness, 0.0)
            for start, end in data["links"]:
                self.assertLess(start, len(data["stars"]))
                self.assertLess(end, len(data["stars"]))

    def test_new_config_includes_constellation_and_settings_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ActionsConfig(Path(temp_dir) / "actions.json")
            self.assertEqual(config.get_constellation(), DEFAULT_CONSTELLATION)
            self.assertEqual(
                config.get_constellation_color(),
                DEFAULT_CONSTELLATION_COLOR,
            )
            self.assertIn(
                "settings",
                [item.action_type for item in config.load_actions()],
            )
            config.set_constellation("sagittarius")
            self.assertEqual(config.get_constellation(), "sagittarius")
            config.set_constellation_color("#22ccff")
            self.assertEqual(config.get_constellation_color(), "#22CCFF")
            self.assertEqual(
                normalise_constellation_color("invalid"),
                DEFAULT_CONSTELLATION_COLOR,
            )

    def test_settings_action_uses_application_callback(self) -> None:
        opened: list[bool] = []
        SettingsAction().execute("", {"open_settings": lambda: opened.append(True)})
        self.assertEqual(opened, [True])

    def test_legacy_config_migration_preserves_actions_and_adds_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "actions.json"
            legacy = {
                "version": "1.0",
                "hotkey": "F24",
                "theme": "tiger",
                "actions": [
                    {
                        "id": f"custom-{index}",
                        "label": f"Custom {index}",
                        "type": "url",
                        "target": "https://example.com",
                        "enabled": True,
                    }
                    for index in range(8)
                ],
            }
            path.write_text(json.dumps(legacy), encoding="utf-8")

            first_load = ActionsConfig(path)
            action_types = [
                action.get("type") for action in first_load.get_raw_actions()
            ]
            self.assertEqual(action_types[2], "settings")
            self.assertEqual(len(action_types), 9)
            self.assertIn(
                "settings",
                [item.action_type for item in first_load.load_actions()[:8]],
            )
            self.assertEqual(first_load.get_hotkey(), "F24")
            self.assertEqual(first_load.get_constellation(), DEFAULT_CONSTELLATION)

            second_load = ActionsConfig(path)
            self.assertEqual(
                [
                    action.get("type")
                    for action in second_load.get_raw_actions()
                ].count("settings"),
                1,
            )

    def test_settings_selector_saves_constellation(self) -> None:
        from ui.settings_window import SettingsWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            config = ActionsConfig(Path(temp_dir) / "actions.json")
            window = SettingsWindow(config)
            index = window._constellation_combo.findData("sagittarius")
            self.assertGreaterEqual(index, 0)
            self.assertGreaterEqual(window._combo_type.findText("Settings"), 0)
            window._constellation_combo.setCurrentIndex(index)
            window._pending_constellation_color = "#22CCFF"
            with patch("ui.settings_window._autostart.set_enabled"):
                window._on_save()
            self.assertEqual(config.get_constellation(), "sagittarius")
            self.assertEqual(config.get_constellation_color(), "#22CCFF")
            window.close()


class ClientWorkspaceOrganisationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _client(name: str, folder_id: str = "") -> dict:
        return {
            "name": name,
            "folderId": folder_id,
            "containerName": "",
            "firefoxProfile": "",
            "urls": [],
        }

    def test_v1_workspace_migrates_clients_to_unassigned(self) -> None:
        clean = validate_workspace_data(
            {
                "version": "1.0",
                "clients": [self._client("Legacy Client")],
            }
        )

        self.assertEqual(clean["version"], WORKSPACE_VERSION)
        self.assertEqual(clean["folders"], [])
        self.assertEqual(clean["clients"][0]["folderId"], "")

    def test_folders_and_drag_layout_are_persisted(self) -> None:
        from ui.client_workspace_window import ClientWorkspaceWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            store = ClientWorkspaceStore(Path(temp_dir) / "client-workspaces.json")
            first_folder = store.add_folder("Engineer A")
            second_folder = store.add_folder("Engineer B")
            first_client = store.add_client(self._client("Client One", first_folder["id"]))
            second_client = store.add_client(self._client("Client Two", second_folder["id"]))
            window = ClientWorkspaceWindow(store=store)

            first_item = window._client_tree.topLevelItem(1)
            second_item = window._client_tree.topLevelItem(2)
            moved_client = first_item.takeChild(0)
            second_item.insertChild(0, moved_client)
            reordered_client = second_item.takeChild(1)
            second_item.insertChild(0, reordered_client)
            window._save_client_tree_layout()

            clients = store.clients()
            self.assertEqual(
                [client["id"] for client in clients],
                [second_client["id"], first_client["id"]],
            )
            self.assertEqual(
                [client["folderId"] for client in clients],
                [second_folder["id"], second_folder["id"]],
            )

            store.delete_folder(second_folder["id"])
            self.assertTrue(all(not client["folderId"] for client in store.clients()))
            window.close()


class _FakeScreen:
    def __init__(self, geometry: QRect):
        self._geometry = geometry

    def availableGeometry(self) -> QRect:
        return self._geometry


class MultiMonitorWindowRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_unshown_top_level_window_uses_cursor_screen(self) -> None:
        window = QWidget()
        secondary = _FakeScreen(QRect(-1920, 40, 1600, 900))
        with patch("ui.window_utils.screen_at_cursor", return_value=secondary):
            self.assertIs(screen_for_widget(window), secondary)
        window.close()

    def test_window_centres_in_negative_coordinate_monitor_geometry(self) -> None:
        window = QWidget()
        window.resize(800, 600)
        secondary = _FakeScreen(QRect(-1920, 40, 1600, 900))

        center_window(window, secondary)

        self.assertEqual(window.pos(), QPoint(-1520, 190))
        window.close()


class RingRotationRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _mouse_event(kind, x: float, y: float, button, buttons) -> QMouseEvent:
        pos = QPointF(x, y)
        return QMouseEvent(
            kind,
            pos,
            pos,
            pos,
            button,
            buttons,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_drag_rotates_without_launching_then_click_still_launches(self) -> None:
        ring = RingWindow()
        self.assertFalse(hasattr(ring, "_draw_ring_lines"))
        ring.resize(WINDOW_SIZE, WINDOW_SIZE)
        ring._ring_container_rect = QRectF(0, 0, WINDOW_SIZE, WINDOW_SIZE)
        ring._nav_stack = [[MenuItem(id="one", label="One", action_type="command")]]
        ring._outside_click_enabled = True
        activated: list[str] = []
        ring.item_activated.connect(lambda item: activated.append(item.id))

        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonPress,
                230,
                118,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
            ),
        )
        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseMove,
                342,
                230,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
            ),
        )
        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonRelease,
                342,
                230,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            ),
        )

        self.assertAlmostEqual(ring._rotation_angle, math.pi / 2, places=2)
        self.assertEqual(activated, [])

        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonPress,
                342,
                230,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
            ),
        )
        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonRelease,
                342,
                230,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            ),
        )

        self.assertEqual(activated, ["one"])
        ring.close()

    def test_action_label_card_is_clickable(self) -> None:
        ring = RingWindow()
        ring.resize(WINDOW_SIZE, WINDOW_SIZE)
        ring._ring_container_rect = QRectF(0, 0, WINDOW_SIZE, WINDOW_SIZE)
        item = MenuItem(id="settings", label="Settings", action_type="settings")
        ring._nav_stack = [[item]]
        ring._outside_click_enabled = True
        activated: list[str] = []
        ring.item_activated.connect(lambda selected: activated.append(selected.id))

        sx, sy = ring._slot_centre(0)
        label_pos = ring._label_card_rect(
            WINDOW_SIZE / 2,
            sx,
            sy,
            item.label,
        ).center()
        self.assertEqual(ring._hit_slot(label_pos), 0)

        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonPress,
                label_pos.x(),
                label_pos.y(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
            ),
        )
        self.app.sendEvent(
            ring,
            self._mouse_event(
                QEvent.Type.MouseButtonRelease,
                label_pos.x(),
                label_pos.y(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
            ),
        )

        self.assertEqual(activated, ["settings"])
        ring.close()

    def test_nine_root_actions_are_all_directly_reachable(self) -> None:
        ring = RingWindow()
        ring._nav_stack = [[
            MenuItem(id=str(index), label=f"Item {index}", action_type="command")
            for index in range(9)
        ]]

        self.assertEqual(ring._slot_count(), 9)
        for index in range(9):
            with self.subTest(index=index):
                self.assertEqual(
                    ring._hit_slot(QPointF(*ring._slot_centre(index))),
                    index,
                )
        ring.close()


class PerformanceRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        prune_theme_asset_cache(set())

    def test_inactive_theme_loads_only_static_preview_frame(self) -> None:
        assets = preload_theme_assets("purple", load_all_frames=False)
        self.assertEqual(len(assets.frames), 1)
        self.assertFalse(assets.frames_fully_loaded)

        assets = preload_theme_assets("purple", load_all_frames=True)
        self.assertEqual(len(assets.frames), 24)
        self.assertTrue(assets.frames_fully_loaded)
        self.assertTrue(all(frame.width() <= 160 for frame in assets.frames))

    def test_ring_constructor_does_not_decode_theme_assets(self) -> None:
        prune_theme_asset_cache(set())
        ring = RingWindow()
        self.assertTrue(ring.windowFlags() & Qt.WindowType.Popup)
        self.assertTrue(ring.windowFlags() & Qt.WindowType.NoDropShadowWindowHint)
        assets = preload_theme_assets("tiger", load_all_frames=False)
        self.assertFalse(assets.frames_fully_loaded)
        ring.close()


if __name__ == "__main__":
    unittest.main()
