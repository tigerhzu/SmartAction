# SmartAction Release Checklist

Updated: 2026-07-10

Release package path:

```text
C:\Users\naugh\smartaction\dist\SmartAction-Release-v1.0
```

## 1. Formal Entry Points

- Source/dev entry: `python -m app.main`
- PyInstaller entry file: `app/main.py`
- Release executable: `SmartAction.exe`
- Release start helper: `start.bat`

`smartaction.spec` uses `app/main.py` as the PyInstaller entry and bundles only public end-user docs into `_internal/docs`.

## 2. Build Commands

Full release build:

```bat
build_release.bat
```

The release build runs:

```bat
python -m compileall -q app core ui platforms native\firefox_helper_host tools
build.bat
python tools\build_release_package.py
```

## 3. Release Package Contents

Top-level release files/folders:

```text
SmartAction-Release-v1.0/
  SmartAction.exe
  _internal/
  assets/
  config/
  data/
  firefox/
  resources/
  install.bat
  uninstall.bat
  start.bat
  README.md
```

Key runtime files:

```text
config/actions.json
resources/config.json
data/powershell_library.json
data/client_workspaces.json
data/icons/emoji_database.json
firefox/firefox-helper.xpi
firefox/native_host/smartaction_firefox_host.exe
firefox/setup_firefox.bat
firefox/uninstall_firefox.bat
```

## 4. Files For Colleagues

Give colleagues the whole `SmartAction-Release-v1.0/` folder.

Colleague-facing files:

- `install.bat` - creates Desktop and Start Menu shortcuts, optionally enables autostart, optionally runs Firefox setup.
- `start.bat` - launches SmartAction.
- `uninstall.bat` - removes shortcuts/autostart and optionally removes Firefox helper registration and local package data.
- `README.md` - installation, usage, Firefox helper, and troubleshooting guide.
- `firefox/setup_firefox.bat` - registers the Firefox Native Messaging Host for the current Windows user.
- `firefox/uninstall_firefox.bat` - removes Firefox helper registration.

## 5. Files That Must Not Leak Into Release

The release package must not include:

- `build/`
- old `dist/` artifacts inside the package
- `backups/`
- `__pycache__/`
- `.venv/`
- `data/smartaction.lock`
- `app_debug.log`
- test logs
- local native host manifests containing `C:\Users\...`
- personal Firefox profile names such as `default-release`
- customer names, customer URLs, passwords, tokens, API keys, or private credentials

Current release validation result:

- No `data/smartaction.lock` in final package.
- No `app_debug.log` in final package.
- No `__pycache__` / `.pyc` / `.pyo` / `.log` in final package.
- No `C:\Users\naugh`, `C:/Users/naugh`, or `default-release` text in release JSON/MD/TXT/BAT/template files.
- `data/client_workspaces.json` is reset to an empty `clients` list.
- `config/actions.json` is reset to a clean starter Ring config.

## 6. Firefox Helper Notes

Firefox helper package:

```text
firefox/
  firefox-helper.xpi
  EXTENSION_README.md
  setup_firefox.bat
  uninstall_firefox.bat
  native_host/
    smartaction_firefox_host.exe
    host_manifest.json.template
```

`setup_firefox.bat` registers:

```text
HKCU\Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper
```

Admin rights:

- Not normally required.
- Registration uses `HKCU`, so it is per-user.
- Admin may still be required by company endpoint policy, locked-down registry policy, or later PowerShell actions.

Manual Firefox extension step:

- Regular Firefox release builds usually require signed extensions.
- If Firefox refuses `firefox-helper.xpi`, submit/sign it or deploy a signed XPI through the organization's normal extension management process.
- Native host registration alone is not enough; the Firefox extension must also be installed.

## 7. Verification Completed

Completed automatically:

- Source compile check passed.
- PyInstaller app build passed.
- Firefox extension XPI build passed.
- Native host exe build passed.
- Clean release package staging passed.
- Release validation passed.
- Release `SmartAction.exe` launch smoke test passed: process stayed running after startup and was stopped after the test.
- `install.bat`, `uninstall.bat`, `start.bat`, `firefox/setup_firefox.bat`, and `firefox/uninstall_firefox.bat` smoke tests passed with `SMARTACTION_TEST_MODE=1`.

## 8. Known Release Limitations

- PowerShell Library Ring action opens the PowerShell Library window only; it does not directly bind and run one specific Library script from the Ring.
- The included `firefox-helper.xpi` may need signing for normal Firefox release installations.
- Real colleague-machine QA is still required for Windows shortcut creation, autostart, tray visibility, global hotkey registration, Firefox extension installation, and native messaging helper checks.
- High-impact PowerShell actions should be reviewed before sharing with non-admin or non-IT users.

