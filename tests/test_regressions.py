from __future__ import annotations

import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMenu,
    QPushButton,
    QWidget,
)

from core.actions.settings_action import SettingsAction
from core.actions_config import (
    ActionsConfig,
    UI_THEME_CLASSIC,
    UI_THEME_CUTE,
    UI_THEME_WOVEN,
)
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
from core.paths import ASSETS_DIR
from core.theme import THEME_ORDER, THEMES
from platforms.windows import (
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    parse_hotkey,
)
from tools.build_emoji_database import parse_emoji_test
from ui.emoji_picker import CATALOG
from ui.ring_ui import RingWindow, WINDOW_SIZE
from ui.theme_painter import (
    draw_energy_bubble,
    draw_jelly_button,
    draw_theme_orbit,
    preload_theme_assets,
    prune_theme_asset_cache,
    theme_frame_count,
)
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
            ui_index = window._ui_theme_combo.findData(UI_THEME_CUTE)
            woven_index = window._ui_theme_combo.findData(UI_THEME_WOVEN)
            self.assertGreaterEqual(index, 0)
            self.assertGreaterEqual(ui_index, 0)
            self.assertGreaterEqual(woven_index, 0)
            self.assertGreaterEqual(window._combo_type.findText("Settings"), 0)
            self.assertEqual(set(window._theme_btns), set(THEME_ORDER))
            window._constellation_combo.setCurrentIndex(index)
            window._select_theme("halloween")
            window._pending_constellation_color = "#22CCFF"
            window._ui_theme_combo.setCurrentIndex(ui_index)
            window._ui_opacity_slider.setValue(68)
            with patch("ui.settings_window._autostart.set_enabled"):
                window._on_save()
            self.assertEqual(config.get_constellation(), "sagittarius")
            self.assertEqual(config.get_theme(), "halloween")
            self.assertEqual(config.get_constellation_color(), "#22CCFF")
            self.assertEqual(config.get_ui_theme(), UI_THEME_CUTE)
            self.assertEqual(config.get_ui_background_opacity(), 68)
            window.close()


class GlobalUiThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_settings_interface_selector_previews_immediately_without_button(
        self,
    ) -> None:
        from ui.settings_window import SettingsWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            config = ActionsConfig(Path(temp_dir) / "actions.json")
            window = SettingsWindow(config)
            self.assertFalse(
                any(
                    button.text() == "Preview"
                    for button in window.findChildren(QPushButton)
                )
            )

            woven_index = window._ui_theme_combo.findData(UI_THEME_WOVEN)
            window._ui_theme_combo.setCurrentIndex(woven_index)
            self.assertEqual(window._pending_ui_theme, UI_THEME_WOVEN)
            self.assertIn(
                "smartaction-woven-light-ui",
                window.styleSheet(),
            )

            classic_index = window._ui_theme_combo.findData(UI_THEME_CLASSIC)
            window._ui_theme_combo.setCurrentIndex(classic_index)
            self.assertEqual(window._pending_ui_theme, UI_THEME_CLASSIC)
            self.assertNotIn(
                "smartaction-woven-light-ui",
                window.styleSheet(),
            )
            self.assertEqual(config.get_ui_theme(), UI_THEME_CLASSIC)
            window.close()

    def test_theme_card_labels_keep_contrast_on_light_backgrounds(self) -> None:
        from ui.settings_window import _ThemeCard

        card = _ThemeCard("sakura", THEMES["sakura"])
        image = QImage(
            card.size(),
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.fill(QColor(0, 0, 0, 0))
        card.render(image)

        label_backing = image.pixelColor(8, 84)
        label_text = image.pixelColor(card.width() // 2, 84)
        self.assertGreaterEqual(label_backing.alpha(), 210)
        self.assertLess(label_backing.lightness(), 45)
        self.assertGreaterEqual(label_text.lightness(), 220)
        card.close()

    def test_settings_cute_surface_is_deeper_than_utility_panels(self) -> None:
        from ui.global_theme import UiAppearance, apply_ui_appearance
        from ui.settings_window import SettingsWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            config = ActionsConfig(Path(temp_dir) / "actions.json")
            settings = SettingsWindow(config)
            apply_ui_appearance(
                settings,
                UiAppearance(theme=UI_THEME_CUTE),
            )
            settings_surface = settings._right_stack.widget(0)
            self.assertIn(
                "background: rgba(246, 226, 236, 148)",
                settings_surface.styleSheet(),
            )

            utility = QDialog()
            utility_surface = QWidget(utility)
            utility_surface.setStyleSheet("background: transparent;")
            apply_ui_appearance(
                utility,
                UiAppearance(theme=UI_THEME_CUTE),
            )
            self.assertIn(
                "background: rgba(255, 247, 250, 225)",
                utility_surface.styleSheet(),
            )
            self.assertNotIn(
                "rgba(246, 226, 236, 148)",
                utility_surface.styleSheet(),
            )
            settings.close()
            utility.close()

    def test_ui_theme_config_and_background_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = ActionsConfig(root / "actions.json")
            self.assertEqual(config.get_ui_theme(), UI_THEME_CLASSIC)

            source = root / "sample.png"
            image = QImage(8, 8, QImage.Format.Format_ARGB32)
            image.fill(0xFFFFD6E4)
            self.assertTrue(image.save(str(source)))

            stored = config.install_ui_background(source)
            config.set_ui_theme(UI_THEME_WOVEN)
            self.assertEqual(config.get_ui_theme(), UI_THEME_WOVEN)
            config.set_ui_theme(UI_THEME_CUTE)
            config.set_ui_background_opacity(64)
            config.set_ui_background_crop(175, 0.2, 0.8)

            self.assertFalse(Path(stored).is_absolute())
            self.assertTrue(config.resolve_ui_background().is_file())
            self.assertEqual(config.get_ui_theme(), UI_THEME_CUTE)
            self.assertEqual(config.get_ui_background_opacity(), 64)
            self.assertEqual(config.get_ui_background_zoom(), 175)
            self.assertEqual(config.get_ui_background_focus(), (0.2, 0.8))

    def test_cute_uses_bundled_background_until_custom_image_is_set(
        self,
    ) -> None:
        from ui.global_theme import (
            appearance_from_config,
            default_cute_background_path,
        )
        from ui.settings_window import SettingsWindow

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = ActionsConfig(root / "actions.json")
            config.set_ui_theme(UI_THEME_CUTE)
            config.set_ui_background("")

            bundled = default_cute_background_path()
            self.assertIsNotNone(bundled)
            self.assertTrue(bundled.is_file())
            self.assertEqual(
                bundled.name,
                "cute-default-background.png",
            )
            source = QImage(str(bundled))
            self.assertGreaterEqual(source.width(), 2000)
            self.assertGreaterEqual(source.height(), 680)

            appearance = appearance_from_config(config)
            self.assertEqual(appearance.background_path, bundled)
            self.assertEqual(config.get_ui_background(), "")

            window = SettingsWindow(config)
            self.assertEqual(window._pending_ui_background_path(), bundled)
            self.assertEqual(
                window._ui_background_edit.text(),
                "Built-in Cute background",
            )
            self.assertFalse(window._ui_background_clear.isEnabled())
            self.assertTrue(window._ui_background_crop.isEnabled())
            window.close()

            custom = root / "custom.png"
            custom_image = QImage(16, 16, QImage.Format.Format_ARGB32)
            custom_image.fill(QColor("#334455"))
            self.assertTrue(custom_image.save(str(custom)))
            config.install_ui_background(custom)
            self.assertEqual(
                appearance_from_config(config).background_path,
                config.resolve_ui_background(),
            )

    def test_tray_logo_matches_the_global_interface_theme(self) -> None:
        from ui.tray_icon import TrayIcon, _make_icon

        signatures = []
        for theme in (UI_THEME_CLASSIC, UI_THEME_CUTE, UI_THEME_WOVEN):
            image = _make_icon(theme).pixmap(64, 64).toImage()
            signatures.append(
                tuple(
                    image.pixelColor(x, y).rgba()
                    for y in range(4, 64, 7)
                    for x in range(4, 64, 7)
                )
            )
        self.assertEqual(len(set(signatures)), 3)

        tray = TrayIcon(self.app, UI_THEME_CLASSIC)
        classic_key = tray.icon().cacheKey()
        tray.set_ui_theme(UI_THEME_CUTE)
        self.assertEqual(tray._ui_theme, UI_THEME_CUTE)
        self.assertNotEqual(tray.icon().cacheKey(), classic_key)
        self.assertEqual(
            self.app.windowIcon().cacheKey(),
            tray.icon().cacheKey(),
        )
        tray.hide()

    def test_background_crop_and_high_dpi_rendering(self) -> None:
        from ui.global_theme import (
            UiAppearance,
            _render_background,
            background_source_rect,
        )

        crop = background_source_rect(2048, 1152, 1180, 760, 100, 0.5, 0.5)
        self.assertAlmostEqual(crop.width(), 1788.63, places=1)
        self.assertAlmostEqual(crop.height(), 1152.0, places=1)
        self.assertAlmostEqual(crop.left(), 129.68, places=1)
        self.assertAlmostEqual(crop.top(), 0.0, places=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "background.png"
            source = QImage(320, 180, QImage.Format.Format_ARGB32)
            source.fill(0xFF75D9F3)
            self.assertTrue(source.save(str(path)))
            rendered = _render_background(
                160,
                100,
                UiAppearance(
                    theme=UI_THEME_CUTE,
                    background_path=path,
                    background_zoom=140,
                    background_focus_x=0.25,
                    background_focus_y=0.75,
                ),
                device_pixel_ratio=2.0,
            )
            self.assertEqual(rendered.size(), QSize(320, 200))
            self.assertEqual(rendered.devicePixelRatio(), 2.0)

    def test_background_crop_canvas_drag_repositions_image(self) -> None:
        from ui.background_crop_dialog import BackgroundCropCanvas

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "wide-background.png"
            source = QImage(600, 300, QImage.Format.Format_ARGB32)
            source.fill(0xFFFFD6E4)
            self.assertTrue(source.save(str(path)))

            canvas = BackgroundCropCanvas(
                path,
                QSize(160, 100),
                zoom=150,
                focus_x=0.5,
                focus_y=0.5,
            )
            canvas.resize(640, 400)
            center = canvas.rect().center()
            press = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                QPointF(center),
                QPointF(center),
                QPointF(center),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            move_pos = QPointF(center.x() + 90, center.y() - 45)
            move = QMouseEvent(
                QEvent.Type.MouseMove,
                move_pos,
                move_pos,
                move_pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            self.app.sendEvent(canvas, press)
            self.app.sendEvent(canvas, move)

            zoom, focus_x, focus_y = canvas.transform()
            self.assertEqual(zoom, 150)
            self.assertLess(focus_x, 0.5)
            self.assertGreater(focus_y, 0.5)
            canvas.close()

    def test_cute_theme_overlay_restores_original_widget_styles(self) -> None:
        from ui.global_theme import UiAppearance, apply_ui_appearance

        dialog = QDialog()
        dialog.resize(500, 320)
        button = QPushButton("Save", dialog)
        original_style = "QPushButton { background: #123456; }"
        button.setStyleSheet(original_style)

        apply_ui_appearance(
            dialog,
            UiAppearance(theme=UI_THEME_CUTE, background_opacity=82),
        )

        self.assertIn("smartaction-cute-ui", button.styleSheet())
        background = dialog.findChild(QLabel, "smartactionGlobalUiBackground")
        self.assertIsNotNone(background)
        self.assertFalse(background.isHidden())

        apply_ui_appearance(dialog, UiAppearance(theme=UI_THEME_CLASSIC))
        self.assertEqual(button.styleSheet(), original_style)
        self.assertTrue(background.isHidden())
        dialog.close()

    def test_woven_light_theme_reacts_and_switches_without_style_leaks(self) -> None:
        from ui.global_theme import UiAppearance, apply_ui_appearance
        from ui.woven_light_background import WovenLightBackground

        dialog = QDialog()
        dialog.resize(640, 400)
        button = QPushButton("Save", dialog)
        label = QLabel("Dialog description", dialog)
        original_style = "QPushButton { background: #123456; }"
        button.setStyleSheet(original_style)
        label.setStyleSheet("color: #F5F2EB;")

        apply_ui_appearance(dialog, UiAppearance(theme=UI_THEME_CUTE))
        self.assertIn("smartaction-cute-ui", button.styleSheet())
        apply_ui_appearance(dialog, UiAppearance(theme=UI_THEME_WOVEN))

        self.assertIn("smartaction-woven-light-ui", button.styleSheet())
        self.assertNotIn("smartaction-cute-ui", button.styleSheet())
        self.assertIn("color: #27313E", label.styleSheet())
        backdrop = dialog.findChild(
            WovenLightBackground,
            "smartactionWovenLightBackground",
            Qt.FindChildOption.FindDirectChildrenOnly,
        )
        self.assertIsNotNone(backdrop)
        self.assertFalse(backdrop.isHidden())
        self.assertEqual(backdrop.particle_count, 480)

        before = backdrop._project_particles()
        backdrop.set_test_pointer(QPointF(640 * 0.68, 400 * 0.49))
        after = backdrop._project_particles()
        self.assertTrue(any(point.proximity > 0 for point in after))
        self.assertTrue(
            any(
                abs(first.x - second.x) > 0.1
                or abs(first.y - second.y) > 0.1
                for first, second in zip(before, after)
            )
        )

        rendered = QImage(
            backdrop.size(),
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        rendered.fill(QColor("white"))
        backdrop.render(rendered)
        saturated_samples = sum(
            1
            for y in range(0, rendered.height(), 4)
            for x in range(0, rendered.width(), 4)
            if rendered.pixelColor(x, y).saturation() >= 55
            and rendered.pixelColor(x, y).value() <= 245
        )
        self.assertGreater(saturated_samples, 120)

        menu = QMenu(dialog)
        menu.setStyleSheet(
            "QMenu::item { color: #F5F2EB; background: #11151D; }"
        )
        menu.addAction("Quick Start")
        apply_ui_appearance(menu, UiAppearance(theme=UI_THEME_WOVEN))
        self.assertIn("QMenu::item {\n    color: #1C2430;", menu.styleSheet())

        apply_ui_appearance(dialog, UiAppearance(theme=UI_THEME_CLASSIC))
        self.assertEqual(button.styleSheet(), original_style)
        self.assertTrue(backdrop.isHidden())
        dialog.close()

    def test_transient_menu_never_receives_background_image_layer(self) -> None:
        from ui.global_theme import UiAppearance, apply_ui_appearance

        menu = QMenu()
        menu.resize(240, 180)
        menu.addAction("Settings")
        apply_ui_appearance(
            menu,
            UiAppearance(theme=UI_THEME_CUTE, background_opacity=82),
        )

        background = menu.findChild(
            QLabel,
            "smartactionGlobalUiBackground",
            Qt.FindChildOption.FindDirectChildrenOnly,
        )
        self.assertIsNone(background)
        menu.close()


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
        ring._reduced_motion = True
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
        ring._reduced_motion = True
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

    def test_click_feedback_completes_before_action_activation(self) -> None:
        ring = RingWindow()
        ring._reduced_motion = False
        item = MenuItem(id="one", label="One", action_type="command")
        ring._nav_stack = [[item]]
        activated: list[str] = []
        ring.item_activated.connect(lambda selected: activated.append(selected.id))

        ring._begin_click_feedback(0, item)
        self.assertEqual(ring._click_slot, 0)
        self.assertEqual(activated, [])

        ring._anim_click.setCurrentTime(ring._anim_click.duration() // 2)
        self.assertGreater(ring._click_progress, 0.0)
        self.assertLess(ring._click_progress, 1.0)
        ring._anim_click.setCurrentTime(ring._anim_click.duration())
        self.app.processEvents()

        self.assertEqual(activated, ["one"])
        self.assertEqual(ring._click_slot, -1)
        ring.close()

    def test_hover_progress_freezes_quickly_and_melts_gradually(self) -> None:
        ring = RingWindow()
        ring._hovered_slot = 0
        ring._advance_theme_frame()
        frozen = ring._slot_hover_progress[0]
        self.assertGreater(frozen, 0.0)

        ring._hovered_slot = -1
        ring._advance_theme_frame()
        melting = ring._slot_hover_progress[0]
        self.assertGreater(melting, 0.0)
        self.assertLess(melting, frozen)
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

    def test_premium_rim_is_high_resolution_and_all_themes_animate(self) -> None:
        rim_path = ASSETS_DIR / "themes" / "shared" / "premium_rim.png"
        rim = QImage(str(rim_path))
        self.assertFalse(rim.isNull())
        self.assertGreaterEqual(rim.width(), 1000)
        self.assertGreaterEqual(rim.height(), 1000)
        self.assertTrue(rim.hasAlphaChannel())
        self.assertLess(rim.pixelColor(rim.width() // 2, rim.height() // 2).alpha(), 12)

        for theme_id in THEME_ORDER:
            with self.subTest(theme_id=theme_id):
                self.assertEqual(theme_frame_count(theme_id), 120)

    def test_procedural_ring_themes_animate_without_bitmap_frames(self) -> None:
        procedural = {"halloween", "kawaii", "sakura", "cyber", "ocean"}
        self.assertTrue(procedural.issubset(THEMES))
        self.assertTrue(procedural.issubset(THEME_ORDER))

        for theme_id in procedural:
            with self.subTest(theme_id=theme_id):
                assets = preload_theme_assets(theme_id, load_all_frames=True)
                self.assertEqual(assets.frames, [])
                self.assertEqual(theme_frame_count(theme_id), 120)

                image = QImage(84, 84, QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(QColor(0, 0, 0, 0))
                painter = QPainter(image)
                draw_energy_bubble(
                    painter,
                    42,
                    42,
                    30,
                    theme_id,
                    frame_index=31,
                )
                painter.end()
                self.assertFalse(image.isNull())
                self.assertNotEqual(image.pixelColor(42, 42).alpha(), 0)

    def test_ocean_uses_wave_orbit_and_jelly_button_without_metal_rim(
        self,
    ) -> None:
        image = QImage(460, 460, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))
        painter = QPainter(image)
        with patch("ui.theme_painter.draw_premium_rim") as premium_rim:
            draw_theme_orbit(painter, 230, 230, 163, "ocean", 31)
            premium_rim.assert_not_called()
        draw_jelly_button(
            painter,
            230,
            230,
            28,
            QColor(8, 118, 175),
        )
        painter.end()

        self.assertGreater(image.pixelColor(230, 230).alpha(), 0)
        self.assertGreater(image.pixelColor(393, 230).alpha(), 0)

    def test_custom_themes_have_independent_visual_dna_renderers(
        self,
    ) -> None:
        from ui.theme_renderer import (
            CyberThemeRenderer,
            CosmicThemeRenderer,
            HalloweenThemeRenderer,
            IceThemeRenderer,
            KawaiiThemeRenderer,
            LavaThemeRenderer,
            OceanThemeRenderer,
            PurpleThemeRenderer,
            SakuraThemeRenderer,
            ThemeInteraction,
            TigerThemeRenderer,
            theme_renderer,
        )

        renderers = {
            "tiger": (theme_renderer("tiger"), TigerThemeRenderer),
            "purple": (theme_renderer("purple"), PurpleThemeRenderer),
            "ice": (theme_renderer("ice"), IceThemeRenderer),
            "lava": (theme_renderer("lava"), LavaThemeRenderer),
            "cosmic": (theme_renderer("cosmic"), CosmicThemeRenderer),
            "halloween": (
                theme_renderer("halloween"),
                HalloweenThemeRenderer,
            ),
            "kawaii": (theme_renderer("kawaii"), KawaiiThemeRenderer),
            "sakura": (theme_renderer("sakura"), SakuraThemeRenderer),
            "cyber": (theme_renderer("cyber"), CyberThemeRenderer),
            "ocean": (theme_renderer("ocean"), OceanThemeRenderer),
        }
        for theme_id, (renderer, renderer_type) in renderers.items():
            with self.subTest(theme_id=theme_id):
                self.assertIsInstance(renderer, renderer_type)

        tiger = renderers["tiger"][0]
        purple = renderers["purple"][0]
        self.assertIsInstance(tiger, TigerThemeRenderer)
        self.assertIsInstance(purple, PurpleThemeRenderer)
        self.assertNotEqual(tiger.dna.orbit_kind, purple.dna.orbit_kind)
        self.assertNotEqual(
            tiger.dna.button_material,
            purple.dna.button_material,
        )
        self.assertNotEqual(tiger.dna.click_kind, purple.dna.click_kind)

        image = QImage(460, 460, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))
        painter = QPainter(image)
        state = ThemeInteraction(frame_index=37)
        with patch("ui.theme_renderer.draw_premium_rim") as premium_rim:
            for renderer, _renderer_type in renderers.values():
                renderer.draw_orbit(painter, 230, 230, 163, state)
            premium_rim.assert_not_called()
        painter.end()

        reduced_a = ThemeInteraction(
            frame_index=3,
            reduced_motion=True,
        )
        reduced_b = ThemeInteraction(
            frame_index=98,
            reduced_motion=True,
        )
        self.assertEqual(reduced_a.phase, reduced_b.phase)


if __name__ == "__main__":
    unittest.main()
