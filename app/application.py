from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from pathlib import Path

from core.action_runner import ActionRunner
from core.actions_config import ActionsConfig
from core.config_manager import ConfigManager
from core.debug_log import debug_log
from core.fonts import load_bundled_fonts
from core.hotkey_manager import HotkeyManager
from core.menu_model import MenuItem
from core.paths import ASSETS_DIR, BUNDLE_DIR, CONFIG_DIR, DOCS_DIR
from ui.main_window import MainWindow
from ui.ring_ui import RingWindow
from ui.theme_painter import theme_asset_debug_summary
from ui.tray_icon import TrayIcon

_ACTION_DELAY_MS = 120
_APP_VERSION = "0.1.0"


class Application(QApplication):
    def __init__(self, argv: list[str]):
        super().__init__(argv)
        debug_log(f"application module path: {Path(__file__).resolve()}")
        self.setApplicationName("Universal Actions Ring")
        self.setApplicationVersion(_APP_VERSION)
        # Keep alive when all normal windows are hidden (tray-only mode)
        self.setQuitOnLastWindowClosed(False)

        load_bundled_fonts()

        self._actions = ActionsConfig()
        self._config  = ConfigManager()
        self._hotkey  = HotkeyManager(self._config)
        self._runner  = ActionRunner()
        self._ring    = RingWindow()
        ai_agent_enabled = _as_bool(self._config.get("ai_agent_enabled", False))
        self._tray    = TrayIcon(self, ai_agent_enabled=ai_agent_enabled)
        self._main_window: MainWindow | None = None
        self._settings_win = None
        self._ps_library_win = None
        self._client_workspace_win = None
        self._ai_agent_win = None
        self._startup_splash = None
        raw_count = len(self._actions.get_raw_actions())
        debug_log(f"app version: {_APP_VERSION}")
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

        # Tray
        self._tray.settings_requested.connect(self._open_settings)
        self._tray.ai_agent_requested.connect(self._open_ai_agent)
        self._tray.powershell_library_requested.connect(self._open_powershell_library)
        self._tray.client_workspace_requested.connect(self._open_client_workspace)
        self._tray.reload_requested.connect(self._reload_config)
        self._tray.restart_hotkey_requested.connect(self._restart_hotkey)
        self._tray.show()

        self._start_startup_sequence()

        return self.exec()

    def _start_startup_sequence(self) -> None:
        if self._show_startup_video():
            return
        QTimer.singleShot(0, self._enter_background_mode)

    def _show_startup_video(self) -> bool:
        if not _as_bool(self._config.get("startup_video_enabled", True)):
            debug_log("startup video disabled by config")
            return False

        from ui.startup_splash import StartupSplash, resolve_startup_media

        path_value = str(self._config.get("startup_video_path", "assets/startup/startup.mp4") or "")
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
            raw_count = len(self._actions.get_raw_actions())
            debug_log(
                f"opening ring via hotkey: loaded_actions_count={len(items)} "
                f"raw_actions_count={raw_count} selected_theme_id={theme!r}"
            )
            self._ring.show_at_cursor(items, theme)

    def _on_item_activated(self, item: MenuItem) -> None:
        context = {
            "parent_widget": None,
            "open_powershell_library": self._open_powershell_library,
        }
        QTimer.singleShot(_ACTION_DELAY_MS, lambda: self._runner.run(item, context))

    def _open_settings(self) -> None:
        from ui.settings_window import SettingsWindow
        if self._settings_win is not None:
            self._settings_win.raise_()
            self._settings_win.activateWindow()
            return
        raw_count = len(self._actions.get_raw_actions())
        enabled_count = len([a for a in self._actions.get_raw_actions() if a.get("enabled", True)])
        debug_log(
            f"opening settings: config_path={self._actions.path.resolve()} "
            f"raw_actions_count={raw_count} enabled_actions_count={enabled_count} "
            f"selected_theme_id={self._actions.get_theme()!r}"
        )
        self._settings_win = SettingsWindow(self._actions)
        self._settings_win.finished.connect(self._on_settings_closed)
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()

    def _on_settings_closed(self, result: int) -> None:
        self._settings_win = None
        from PySide6.QtWidgets import QDialog
        if result == QDialog.DialogCode.Accepted:
            new_combo = self._actions.get_hotkey()
            self._hotkey.stop()
            ok = self._hotkey.start(new_combo)
            if not ok:
                print(f"[Application] Failed to register new hotkey: {new_combo!r}")

    def _open_powershell_library(self) -> None:
        from ui.powershell_library_window import PowerShellLibraryWindow
        if self._ps_library_win is not None:
            self._ps_library_win.raise_()
            self._ps_library_win.activateWindow()
            return
        self._ps_library_win = PowerShellLibraryWindow()
        self._ps_library_win.finished.connect(lambda _result: setattr(self, "_ps_library_win", None))
        self._ps_library_win.show()
        self._ps_library_win.raise_()
        self._ps_library_win.activateWindow()

    def _open_ai_agent(self) -> None:
        if not _as_bool(self._config.get("ai_agent_enabled", False)):
            return
        if self._ai_agent_win is not None:
            self._ai_agent_win.raise_()
            self._ai_agent_win.activateWindow()
            return

        from core.ai_agent.catalog import ActionCatalog
        from core.ai_agent.mock_provider import MockAIProvider
        from core.ai_agent.service import AIAgentService
        from core.client_workspace import ClientWorkspaceStore
        from core.powershell_library import PowerShellLibrary
        from ui.ai_agent_window import AIAgentWindow

        try:
            catalog = ActionCatalog.from_sources(
                self._actions,
                PowerShellLibrary(),
                ClientWorkspaceStore(),
            )
        except Exception as exc:
            debug_log(f"AI Agent catalog initialization failed: {type(exc).__name__}")
            self._tray.showMessage(
                "SmartAction AI Agent",
                "Could not load the saved-action catalog. No plan was created or executed.",
                QSystemTrayIcon.MessageIcon.Warning,
                3000,
            )
            return
        service = AIAgentService(MockAIProvider(), catalog)
        self._ai_agent_win = AIAgentWindow(service)
        self._ai_agent_win.finished.connect(lambda _result: setattr(self, "_ai_agent_win", None))
        self._ai_agent_win.show()
        self._ai_agent_win.raise_()
        self._ai_agent_win.activateWindow()

    def _open_client_workspace(self) -> None:
        from ui.client_workspace_window import ClientWorkspaceWindow
        if self._client_workspace_win is not None:
            self._client_workspace_win.raise_()
            self._client_workspace_win.activateWindow()
            return
        self._client_workspace_win = ClientWorkspaceWindow()
        self._client_workspace_win.finished.connect(lambda _result: setattr(self, "_client_workspace_win", None))
        self._client_workspace_win.show()
        self._client_workspace_win.raise_()
        self._client_workspace_win.activateWindow()

    def _reload_config(self) -> None:
        if self._settings_win is not None:
            self._tray.showMessage(
                "Universal Actions Ring",
                "Close Settings before reloading config.",
                QSystemTrayIcon.MessageIcon.Warning,
                2000,
            )
            return
        self._actions.reload()
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
