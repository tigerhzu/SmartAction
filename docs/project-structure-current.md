# SmartAction Current Project Structure

Updated: 2026-07-09

This document describes the current local workspace at `C:\Users\naugh\smartaction`.
It is intended as a handoff note for future AI agents or teammates before doing more UI redesign work.

## 1. Current Folder Structure

Top-level folders currently observed:

| Path | Current role | Notes |
| --- | --- | --- |
| `app/` | Formal application entry and app lifecycle | Contains `main.py` and `application.py`. This is the source startup path. |
| `ui/` | PySide6 UI windows/dialogs/widgets | Contains settings, ring, tray, splash, helper dialogs, and an unused `main_window.py` launcher. |
| `core/` | Business logic, config, action execution, path resolution | Contains action registry/handlers, hotkey manager, config/profile/theme logic, PowerShell helpers. |
| `config/` | User-editable action configuration | Contains `actions.json`, the active ring/action tree config. |
| `data/` | Runtime data | Contains lock file, PowerShell library data, client workspaces, icon picker data. |
| `resources/` | Legacy writable resources/config and image test assets | Contains `config.json`, `styles/`, ring images, UI screenshots/check images. |
| `assets/` | Bundled read-only app assets | Startup video, fonts, emoji catalog, ring theme assets and animation frames. |
| `docs/` | Project docs | UI audit/redesign docs, help docs, Firefox/client workspace docs, and this file. |
| `.codex/` | Local Codex skills/config | Design/UI helper skills and related scripts/data. Not part of runtime app. |
| `.claude/` | Claude/local agent settings | Contains local settings. Not part of runtime app. |
| `extensions/` | Firefox extension source | `extensions/firefox-helper/` contains manifest/background script. |
| `native/` | Native messaging host source | `native/firefox_helper_host/` contains Python host, manifest templates, install helper. |
| `tools/` | Build/helper scripts | Emoji DB builder, Firefox extension builder, release package builder. |
| `build/` | Build work/output artifacts | Generated build intermediates. Do not treat as source for UI redesign. |
| `dist/` | Release artifacts | Generated packaged apps/extensions. Do not edit directly for source changes. |
| `backups/` | Profile backups | JSON profile backups. |

Important source files by area:

```text
app/
  main.py                  # `python -m app.main` entry module
  application.py           # QApplication subclass and tray/ring/settings orchestration

ui/
  ai_agent_window.py       # Feature-flagged AI plan preview; no execution
  tray_icon.py             # System tray icon and tray menu
  ring_ui.py               # RingWindow radial launcher UI
  settings_window.py       # Settings dialog, action editor, theme/hotkey/profile UI
  startup_splash.py        # Optional startup video/splash
  powershell_library_window.py
  client_workspace_window.py
  environment_check_window.py
  emoji_picker.py
  hotkey_picker.py
  help_modal.py
  theme_painter.py         # Ring/theme drawing helpers
  style_tokens.py          # Shared color/type/spacing tokens
  widgets.py               # Shared input/separator factories
  main_window.py           # Currently not shown by formal entry flow

core/
  ai_agent/                # Provider/schema/catalog/validator planning boundary
  action_runner.py         # Dispatches selected MenuItem to action handler
  actions_config.py        # Active `config/actions.json` config model
  config_manager.py        # Legacy `resources/config.json` config model
  hotkey_manager.py        # Global hotkey registration
  menu_model.py            # MenuItem data model
  paths.py                 # Dev/frozen path resolution
  theme.py                 # Theme catalog
  theme-related rendering is in ui/theme_painter.py
  profile_manager.py       # Export/import/backup profile logic
  client_workspace.py      # Client workspace data model/store
  powershell_library.py    # PowerShell library data model/store
  powershell_runner.py     # PowerShell execution
  actions/                 # Registered action handler classes
  scripts/                 # Bundled PowerShell scripts

config/
  actions.json             # Current formal action tree/hotkey/theme config

resources/
  config.json              # Legacy config, still used for startup video settings
  styles/                  # QSS placeholders

assets/
  startup/startup.mp4
  fonts/Oswald.ttf
  themes/<theme>/rim.png, rim_active.png, card_bg.png, frames/

extensions/firefox-helper/
  manifest.json
  background.js

native/firefox_helper_host/
  smartaction_firefox_host.py
  smartaction_firefox_host.cmd
  host_manifest.json
  host_manifest.json.template
  install_host_windows.py
```

## 2. Formal Startup Method

Current PowerShell startup command:

```powershell
Set-Location C:\Users\naugh\smartaction; python -m app.main
```

Formal startup flow:

1. `app/main.py`
   - Imports `Application` from `app.application`.
   - Acquires the single-instance lock via `core.single_instance.acquire_single_instance_lock()`.
   - Creates `Application(sys.argv)`.
   - Calls `app.run()`.

2. `app/application.py`
   - Defines `class Application(QApplication)`.
   - `QApplication` is created inside `Application.__init__()` by `super().__init__(argv)`.
   - Loads bundled fonts.
   - Creates config/runtime managers:
     - `ActionsConfig()` for `config/actions.json`
     - `ConfigManager()` for `resources/config.json`
     - `HotkeyManager(...)`
     - `ActionRunner()`
   - Creates the always-present but initially hidden `RingWindow()`.
   - Creates the system tray icon `TrayIcon(self)`.
   - Sets `_main_window: MainWindow | None = None`, but does not instantiate `MainWindow`.

3. `Application.run()`
   - Requires system tray availability.
   - Connects ring activation, hotkey, and tray menu signals.
   - Starts the configured global hotkey from `config/actions.json`.
   - Calls `self._tray.show()`.
   - Starts optional startup splash sequence.
   - Enters Qt event loop with `self.exec()`.

Object creation locations:

| Object | Where created | When shown |
| --- | --- | --- |
| `QApplication` / `Application` | `app/main.py` creates `Application(sys.argv)`; actual `QApplication` init is `Application.__init__()` in `app/application.py` | Event loop starts in `Application.run()` |
| `TrayIcon` | `app/application.py`, `self._tray = TrayIcon(self)` | Immediately shown in `Application.run()` via `self._tray.show()` |
| `RingWindow` | `app/application.py`, `self._ring = RingWindow()` | Shown only when hotkey triggers `_on_ring_triggered()` |
| `SettingsWindow` | `app/application.py`, inside `_open_settings()` | Shown when tray menu `Open Settings` or tray double-click emits `settings_requested` |
| `StartupSplash` | `app/application.py`, inside `_show_startup_video()` | Shown at startup only if enabled and media resolves |
| `PowerShellLibraryWindow` | `app/application.py`, inside `_open_powershell_library()` | Shown from tray menu |
| `ClientWorkspaceWindow` | `app/application.py`, inside `_open_client_workspace()` | Shown from tray menu |

## 3. UI Files Used By Formal Flow

Directly used by `app.main` / `Application` formal flow:

| File | Usage |
| --- | --- |
| `ui/tray_icon.py` | Defines `TrayIcon`, tray menu, tray double-click behavior. |
| `ui/ring_ui.py` | Defines `RingWindow`, the radial launcher. This is the actual ring file. There is no current `ui/ring_window.py`. |
| `ui/settings_window.py` | Defines `SettingsWindow`, the visible Settings dialog titled `Settings — Universal Actions Ring`. |
| `ui/startup_splash.py` | Optional startup video/splash, controlled by `resources/config.json`. |
| `ui/powershell_library_window.py` | Opened from tray menu and action handlers. |
| `ui/client_workspace_window.py` | Opened from tray menu and action handlers. |
| `ui/theme_painter.py` | Used by `Application` for startup theme debug summary, by `ring_ui.py`, and by `settings_window.py`. |
| `ui/style_tokens.py` | Shared design tokens imported by multiple formal UI files. |

Used indirectly through Settings or action handlers:

| File | Usage |
| --- | --- |
| `ui/emoji_picker.py` | Opened from Settings when choosing action icons. |
| `ui/hotkey_picker.py` | Opened from Settings to edit the global hotkey. |
| `ui/help_modal.py` | Opened from Settings or Client Workspace help flows. |
| `ui/environment_check_window.py` | Opened by `core/actions/environment_check_action.py`. |
| `ui/forms/*` | Loaded by `core/actions/ps_form_action.py` for form-based PowerShell actions. |
| `ui/widgets.py` | Shared small widget factories for forms. |

Naming note:

- The requested `ui/ring_window.py` does not currently exist.
- The actual formal ring window file is `ui/ring_ui.py`.

## 4. UI Files Possibly Not Used By Formal Flow

| File | Current status |
| --- | --- |
| `ui/main_window.py` | Imported by `app/application.py`, but not instantiated or shown by `app.main`. `_main_window` is set to `None` and no code path calls `MainWindow(...)` or `.show()` in the formal startup path. Marked: **currently not used by the formal entry point**. |

Details for `ui/main_window.py`:

- `app/application.py` has `from ui.main_window import MainWindow`.
- `Application.__init__()` sets `self._main_window: MainWindow | None = None`.
- No formal flow currently creates `self._main_window = MainWindow(...)`.
- No formal flow currently calls `self._main_window.show()`.
- Therefore any landing-page-style redesign inside `ui/main_window.py` will not appear when running:

```powershell
Set-Location C:\Users\naugh\smartaction; python -m app.main
```

## 5. Main Responsibility Map

| Responsibility | Primary files |
| --- | --- |
| Source entry point | `app/main.py` |
| Application lifecycle / Qt event loop orchestration | `app/application.py` |
| Tray app | `ui/tray_icon.py`, orchestrated by `app/application.py` |
| Ring window / radial launcher | `ui/ring_ui.py` |
| Settings window / action editor | `ui/settings_window.py` |
| Startup video/splash | `ui/startup_splash.py`, controlled by `resources/config.json` |
| Action execution dispatch | `core/action_runner.py` |
| AI plan generation and validation (feature off by default) | `core/ai_agent/` |
| AI plan preview and approval-only UI | `ui/ai_agent_window.py` |
| Action handler registry | `core/actions/registry.py`, loaded through `core/actions/__init__.py` |
| Individual action behavior | `core/actions/*.py` |
| Active action config | `core/actions_config.py`, data in `config/actions.json` |
| Legacy app config | `core/config_manager.py`, data in `resources/config.json` |
| Profile export/import/backup | `core/profile_manager.py`, backups in `backups/` |
| Theme catalog | `core/theme.py` |
| Theme/ring asset drawing | `ui/theme_painter.py`, assets under `assets/themes/` |
| Shared design tokens | `ui/style_tokens.py` |
| Paths for dev/frozen builds | `core/paths.py` |
| Global hotkey | `core/hotkey_manager.py` |
| PowerShell library data/UI | `core/powershell_library.py`, `ui/powershell_library_window.py`, data in `data/powershell_library.json` |
| PowerShell execution | `core/powershell_runner.py`, scripts under `core/scripts/` |
| Client workspace data/UI | `core/client_workspace.py`, `ui/client_workspace_window.py`, data in `data/client_workspaces.json` |
| Firefox extension | `extensions/firefox-helper/manifest.json`, `extensions/firefox-helper/background.js` |
| Native messaging host | `native/firefox_helper_host/` |
| Build/release helpers | `tools/*.py`, `build*.bat`, `smartaction.spec` |
| Build outputs | `build/`, `dist/` |

### AI Agent Phase-1 Boundary

The optional AI Agent foundation is isolated under `core/ai_agent/` and is
disabled by default through `resources/config.json`. It uses an offline Mock
Provider and can reference only saved allowlisted Action, PowerShell Library,
and Client Workspace IDs. `ui/ai_agent_window.py` previews a validated plan and
can emit an approval signal, but no Phase-1 code connects that signal to
`ActionRunner`, PowerShell, subprocess, or Client Workspace launch functions.

See `docs/ai-agent-plan.md` for the security model, schema, rollout phases, and
rollback procedure.

## 6. Current Workspace Change Status

The repository is a Git working tree with `origin` pointing to
`https://github.com/tigerhzu/SmartAction.git`. The v1.0 baseline inspected for
the AI Agent work was clean `main` at commit `bbed860`, matching
`origin/main`. AI foundation development is isolated on
`feature/ai-agent-foundation`; no source changes are made directly on `main`.

Generated `build/` and `dist/` output remains ignored and must not be edited as
source. The real visible app after startup is primarily tray/background, then
Ring and dialogs on demand.

## 7. Next-Step Recommendations For SmartAction UI Redesign

If the goal is to redesign the UI that users actually see through the formal entry point, focus on these files first:

### Phase 1: Formal Visible Surfaces

Recommended files:

- `ui/settings_window.py`
- `ui/ring_ui.py`
- `ui/tray_icon.py`
- `ui/startup_splash.py`
- `ui/style_tokens.py`
- `ui/theme_painter.py`

Scope:

- Refresh Settings visual system and layout.
- Improve RingWindow visuals, animation, labels, theme consistency.
- Improve tray menu/about behavior if needed.
- Keep shared tokens in `ui/style_tokens.py` so redesign stays consistent.
- Use `ui/theme_painter.py` and `assets/themes/` for ring visuals rather than building unrelated surfaces.

Avoid for Phase 1:

- Do not continue investing in `ui/main_window.py` unless the product decision is to add a real main dashboard window to `Application`.
- Do not edit `dist/` or `build/`.

### Phase 2: Supporting Dialogs And Feature Windows

Recommended files:

- `ui/powershell_library_window.py`
- `ui/client_workspace_window.py`
- `ui/environment_check_window.py`
- `ui/emoji_picker.py`
- `ui/hotkey_picker.py`
- `ui/help_modal.py`
- `ui/forms/*`
- `ui/widgets.py`

Scope:

- Bring secondary windows into the same visual system after Settings/Ring are settled.
- Standardize buttons, fields, separators, modal sizing, and error/success states.
- Make PowerShell and Client Workspace workflows easier to scan.

### Phase 3: Product Architecture Decisions

Potential decisions:

- Decide whether SmartAction should remain tray-first or gain a real main dashboard window.
- If a dashboard is desired, explicitly wire `ui/main_window.py` into `app/application.py`, add tray menu action such as `Open Dashboard`, and define when it opens.
- Consolidate legacy `resources/config.json` and active `config/actions.json` where appropriate.
- Add tests or smoke checks for formal UI windows instead of only unused launcher surfaces.

Files not to continue changing unless architecture changes:

- `ui/main_window.py` for visual redesign work, because it is currently not used by `app.main`.
- `build/` and `dist/`, because they are generated outputs.
- `.codex/` and `.claude/`, unless changing agent/tooling configuration.
