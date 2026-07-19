# SmartAction current project structure

SmartAction is a Windows tray application. Its normal visible surfaces are the
radial ring, Settings, PowerShell Library, Client Workspace, and helper dialogs.

## Runtime flow

1. `app/main.py` acquires the single-instance lock.
2. `app/application.py` creates the tray, lightweight ring shell, action runner,
   and native Windows hotkey manager.
3. The app stays in tray/background mode. Startup media is disabled by default.
4. The first hotkey press loads only the selected theme and opens the ring.
5. Settings and other large dialogs are imported and constructed only on demand.

## Primary directories

| Path | Role |
| --- | --- |
| `app/` | Entry point and application lifecycle |
| `core/` | Config, action dispatch, native hotkey orchestration, profiles, PowerShell and client-workspace logic |
| `ui/` | Live PySide6 windows, dialogs, widgets, theme painting and ring UI |
| `platforms/windows.py` | Windows `RegisterHotKey` backend |
| `config/actions.json` | Active hotkey, theme and radial action tree |
| `data/` | PowerShell library, client workspaces and Emoji picker data |
| `resources/config.json` | Small legacy/startup setting store |
| `assets/themes/` | Optimized theme animation frames and card backgrounds |
| `assets/startup/` | Optional lightweight PNG/JPG/GIF startup media; disabled by default |
| `docs/` | User and developer documentation |
| `extensions/` | Firefox helper extension source |
| `native/` | Firefox native-messaging helper source |
| `tools/` | Build, release and database utilities |
| `tests/` | Regression tests |

`build/`, `dist/`, `.venv/`, caches, logs and lock files are generated locally
and ignored by Git.

## Performance behavior

- Creating the hidden ring does not decode theme frames.
- Theme frames are loaded at a maximum of 160×160 pixels.
- The active theme caches all animation frames; inactive Settings cards cache
  only their first frame.
- Closing Settings releases decoded assets for themes that are no longer active.
- Ring animation uses about 10 FPS and repaints only the ring rectangle, not the
  full screen. The ring itself is a compact `Qt.Popup`, so outside-click
  dismissal does not require a screen-sized backing buffer.
- Settings animates only the selected theme preview at about 12 FPS.
- Emoji cells are created in batches and skin-tone duplicates are excluded.
- The ring's twelve constellation backgrounds are drawn with QPainter, so they
  add no bitmap assets or startup I/O. Their star/line color is user-selectable,
  while action bubbles remain independent and are not connected by extra lines.
- A `settings` action type opens the main Settings window directly from any
  root or nested ring slot.
- The lightweight startup image is opt-in, so low-end machines enter tray mode immediately.

## Build

The runtime uses `PySide6-Essentials`; unused Multimedia, QML and Quick modules
are neither installed nor bundled.

Source:

```powershell
python -m app.main
```

Windows bundle:

```bat
build.bat
```

Release package:

```bat
build_release.bat
```
