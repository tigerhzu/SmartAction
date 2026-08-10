from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from pathlib import Path
import webbrowser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from core.app_info import APP_VERSION
from core.debug_log import debug_log
from core.fonts import configure_application_font, load_bundled_fonts
from core.hotkey_manager import HotkeyManager
from core.local_api import LocalApiServer
from core.menu_model import MenuItem
from core.paths import ASSETS_DIR, BUNDLE_DIR, CONFIG_DIR, DOCS_DIR
from core.smartaction_core import SmartActionCore
from ui.ring_ui import RingWindow
from ui.global_theme import GlobalUiThemeManager
from ui.theme_painter import theme_asset_debug_summary
from ui.tray_icon import TrayIcon
from ui.window_utils import screen_at_cursor

_ACTION_DELAY_MS = 120


class Application(QApplication):
    local_api_settings_changed = Signal()
    local_api_profile_imported = Signal()

    def __init__(self, argv: list[str]):
        super().__init__(argv)
        debug_log(f"application module path: {Path(__file__).resolve()}")
        self.setApplicationName("Universal Actions Ring")
        self.setApplicationVersion(APP_VERSION)
        # Keep alive when all normal windows are hidden (tray-only mode)
        self.setQuitOnLastWindowClosed(False)

        load_bundled_fonts()
        configure_application_font(self)

        self._core = SmartActionCore()
        self._actions = self._core.actions_config
        self._ui_theme = GlobalUiThemeManager(self, self._actions)
        self._config  = self._core.legacy_config
        self._hotkey  = HotkeyManager(self._config)
        self._runner  = self._core.action_runner
        self._local_api = LocalApiServer(
            self._core,
            on_settings_changed=self.local_api_settings_changed.emit,
            on_profile_imported=self.local_api_profile_imported.emit,
        )
        self.local_api_settings_changed.connect(self._apply_core_settings)
        self.local_api_profile_imported.connect(self._on_profile_imported)
        self._ring    = RingWindow()
        self._tray    = TrayIcon(self, self._actions.get_ui_theme())
        self._startup_splash = None
        raw_count = len(self._actions.get_raw_actions())
        debug_log(f"app version: {APP_VERSION}")
        debug_log(f"base resource path: {BUNDLE_DIR.resolve()} exists={BUNDLE_DIR.exists()}")
        debug_log(f"assets path: {ASSETS_DIR.resolve()} exists={ASSETS_DIR.exists()}")
        debug_log(f"docs/help.md path: {(DOCS_DIR / 'help.md').resolve()} exists={(DOCS_DIR / 'help.md').exists()}")
        debug_log(f"config dir path: {CONFIG_DIR.resolve()} exists={CONFIG_DIR.exists()}")
        debug_log(f"active actions config path: {self._actions.path.resolve()}")
        debug_log(f"active legacy config path: {self._config.path.resolve()}")
        debug_log(f"startup actions count: {raw_count} selected_theme_id={self._actions.get_theme()!r}")
        debug_log(f"startup selected theme asset: {theme_asset_debug_summary(self._actions.get_theme())}")

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> int:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("ERROR: System tray not available on this desktop.")
            return 1

        self.aboutToQuit.connect(self._on_quit)

        # Ring
        self._ring.item_activated.connect(self._on_item_activated)

        # Hotkey
        self._hotkey.triggered.connect(self._on_ring_triggered)
        ok = self._hotkey.start(self._actions.get_hotkey())
        if not ok:
            print("WARNING: Could not register hotkey — check config/actions.json")

        try:
            endpoint = self._local_api.start()
            debug_log(f"Local API started: {endpoint.url}")
        except OSError as exc:
            debug_log(f"Local API failed to start: {exc!r}")

        # Tray
        self._tray.control_center_requested.connect(self._open_control_center)
        self._tray.reload_requested.connect(self._reload_config)
        self._tray.restart_hotkey_requested.connect(self._restart_hotkey)
        self._tray.show()

        self._start_startup_sequence()

        return self.exec()

    def _start_startup_sequence(self) -> None:
        if self._show_startup_splash():
            return
        QTimer.singleShot(0, self._enter_background_mode)

    def _show_startup_splash(self) -> bool:
        if not _as_bool(self._config.get("startup_video_enabled", False)):
            debug_log("startup splash disabled by config")
            return False

        from ui.startup_splash import StartupSplash, resolve_startup_media

        path_value = str(self._config.get("startup_video_path", "assets/startup/startup.png") or "")
        media_path = resolve_startup_media(path_value)
        debug_log(f"startup splash media path: {media_path} exists={bool(media_path and media_path.exists())}")
        if media_path is None:
            return False

        duration = _bounded_duration(self._config.get("startup_video_duration", 5))
        splash = StartupSplash(media_path, duration)
        splash.splash_finished.connect(self._on_startup_splash_finished)
        if not splash.start():
            debug_log("startup splash skipped because media could not be started")
            return False
        self._startup_splash = splash
        return True

    def _on_startup_splash_finished(self) -> None:
        self._startup_splash = None
        self._enter_background_mode()

    def _enter_background_mode(self) -> None:
        debug_log("startup sequence complete; SmartAction is running in background/tray mode")

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_ring_triggered(self) -> None:
        if self._ring.isVisible():
            self._ring.close_ring()
        else:
            items = self._actions.load_actions()
            theme = self._actions.get_theme()
            constellation = self._actions.get_constellation()
            constellation_color = self._actions.get_constellation_color()
            raw_count = len(self._actions.get_raw_actions())
            debug_log(
                f"opening ring via hotkey: loaded_actions_count={len(items)} "
                f"raw_actions_count={raw_count} selected_theme_id={theme!r}"
            )
            self._ring.show_at_cursor(
                items,
                theme,
                constellation,
                constellation_color,
            )

    def _on_item_activated(self, item: MenuItem) -> None:
        target_screen = screen_at_cursor()
        context = {
            "parent_widget": None,
            "target_screen": target_screen,
            "open_settings": lambda: self._open_control_center("ring"),
            "open_powershell_library": lambda: self._open_control_center("powershell"),
            "open_client_workspace": lambda: self._open_control_center("workspace"),
        }
        QTimer.singleShot(_ACTION_DELAY_MS, lambda: self._runner.run(item, context))

    def _open_settings(self) -> None:
        self._open_control_center("ring")

    def _on_profile_imported(self) -> None:
        result = self._core.reload_profile_resources()
        if not result.success:
            message = result.error.message if result.error else "Imported resources could not be reloaded."
            debug_log(f"profile resource reload failed: {result.to_dict()!r}")
            self._tray.showMessage(
                "Universal Actions Ring",
                message,
                QSystemTrayIcon.MessageIcon.Critical,
                5000,
            )
            return

        self._apply_core_settings()
        debug_log(f"profile resources reloaded: {result.to_dict()!r}")

    def _apply_core_settings(self) -> None:
        """Apply persisted Core settings to the live Qt-owned integrations."""
        self._ui_theme.reload()
        self._tray.set_ui_theme(self._actions.get_ui_theme())
        new_combo = self._actions.get_hotkey()
        self._hotkey.stop()
        ok = self._hotkey.start(new_combo)
        if not ok:
            print(f"[Application] Failed to register new hotkey: {new_combo!r}")

    def _open_powershell_library(self) -> None:
        self._open_control_center("powershell")

    def _open_control_center(self, view: str = "dashboard") -> None:
        url = self._local_api.control_center_url
        if url is None:
            try:
                self._local_api.start()
                url = self._local_api.control_center_url
            except OSError as exc:
                debug_log(f"Local API could not be restarted for Control Center: {exc!r}")
        if not url:
            self._tray.showMessage(
                "Universal Actions Ring",
                "Web Control Center could not be started.",
                QSystemTrayIcon.MessageIcon.Critical,
                4000,
            )
            return
        parsed = urlsplit(url)
        fragment = dict(parse_qsl(parsed.fragment, keep_blank_values=True))
        fragment["view"] = view
        url = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",
                urlencode({"view": fragment.pop("view"), **fragment}),
            )
        )
        if not webbrowser.open(url):
            self._tray.showMessage(
                "Universal Actions Ring",
                "Could not open the Web Control Center in your browser.",
                QSystemTrayIcon.MessageIcon.Warning,
                4000,
            )

    def _open_client_workspace(self) -> None:
        self._open_control_center("workspace")

    def _reload_config(self) -> None:
        self._actions.reload()
        self._ui_theme.reload()
        self._tray.set_ui_theme(self._actions.get_ui_theme())
        combo = self._actions.get_hotkey()
        self._hotkey.stop()
        ok = self._hotkey.start(combo)
        msg = (
            f"Config reloaded  |  Hotkey: {combo}"
            if ok else
            "Config reloaded (hotkey registration failed)."
        )
        self._tray.showMessage(
            "Universal Actions Ring", msg,
            QSystemTrayIcon.MessageIcon.Information, 2000,
        )

    def _restart_hotkey(self) -> None:
        combo = self._actions.get_hotkey()
        self._hotkey.stop()
        ok = self._hotkey.start(combo)
        msg = f"Hotkey restarted: {combo}" if ok else "Hotkey restart failed."
        self._tray.showMessage(
            "Universal Actions Ring", msg,
            QSystemTrayIcon.MessageIcon.Information, 2000,
        )

    def _on_quit(self) -> None:
        self._local_api.stop()
        self._hotkey.stop()
        lock = getattr(self, "_single_instance_lock", None)
        if lock is not None:
            lock.unlock()


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _bounded_duration(value) -> int:
    try:
        return max(1, min(int(value), 5))
    except (TypeError, ValueError):
        return 5
