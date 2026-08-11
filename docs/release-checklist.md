# SmartAction Portable Release Checklist

## Build output

Run `build_release.bat` from the project root. It prefers `.venv\Scripts\python.exe` and only falls back to `python` on `PATH`.

Successful output:

```text
dist/
  SmartAction/
    SmartAction.exe
    _internal/
    config/
    resources/
    data/
    firefox/
    install.bat
    start.bat
    uninstall.bat
    README.md
  SmartAction-v1.4.1-portable.zip
```

Share the ZIP, or the complete `dist\SmartAction\` folder. Never share `SmartAction.exe` by itself. Extract it to a writable folder such as `C:\Tools\SmartAction`; do not run it in-place from the ZIP or a protected system directory.

## Automated release gates

- `build_release.bat` runs a source compile check, validates required release sources before deleting prior output, produces the onedir bundle, creates the Firefox XPI/native host, and validates the resulting portable folder.
- Required bundled checks include the Web Control Center HTML/CSS/JS/logo, Ring theme frames, cute background, emoji database, and PowerShell scripts.
- The final release folder is scrubbed of Python source/cache files, logs, locks, build folders, and known developer-machine paths.
- Writable settings and user data are beside `SmartAction.exe` in `config/`, `resources/`, `data/`, and `backups/`; they are not stored under `_internal/`.

## Clean Windows smoke test

Use a Windows PC with no Python, pip, virtualenv, or source checkout.

1. Extract the portable ZIP to a writable location. Confirm `SmartAction.exe`, `_internal/`, and `firefox/` all exist.
2. Run `start.bat` (or `SmartAction.exe`). Confirm a SmartAction tray icon appears and the process remains running.
3. From the tray, open Web Control Center. Confirm the browser opens a `127.0.0.1` URL and Dashboard, Ring, PowerShell Library, Client Workspace, and Settings load without missing styles/images.
4. Change a safe setting such as the UI theme or hotkey, save it, and verify the tray/Ring updates immediately.
5. Press the configured hotkey (default `Ctrl+Alt+Space`). Confirm the Ring opens, renders themes/icons, and an innocuous action such as Task Manager or a URL executes.
6. In PowerShell Library, create and run a safe `Write-Output` script. Do not use privileged scripts for the first smoke test.
7. In Client Workspace, create a test folder/client, save it, then restart SmartAction and confirm it remains present.
8. Exit SmartAction from the tray. Refresh the former Control Center URL: it should no longer connect, confirming the Local API stopped.
9. Restart SmartAction and confirm saved settings, actions, PowerShell Library entries, and Client Workspace data persist.
10. If Firefox/containers are needed, run `firefox\setup_firefox.bat`, install the supplied (normally signed) XPI, then use Client Workspace to check/repair the helper and test a container launch.

## Firefox-specific setup

Firefox features are optional for the core tray, Ring, hotkey, settings, actions, and PowerShell Library. They require both:

1. `firefox\setup_firefox.bat`, which installs/registers the native messaging host for the current Windows user.
2. Installation of `firefox\firefox-helper.xpi` in the intended Firefox profile. Standard Firefox release channels usually require a signed XPI.

The package uses the current-user registry (`HKCU`), so administrator rights are normally not needed. Organization policy or privileged PowerShell actions can still require elevation.
