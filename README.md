# SmartAction

SmartAction is a Windows tray + hotkey productivity launcher for common IT and desktop workflows. It opens a dark radial Ring UI for actions such as URLs, apps, commands, PowerShell tools, environment checks, client workspaces, paste snippets, and PowerShell forms.

## Download

Download SmartAction from the **GitHub Releases** page:

```text
Releases -> SmartAction v1.0.0 -> SmartAction-Release-v1.0.zip
```

Do **not** use GitHub `Code > Download ZIP` for installation. That download is the source code, not the packaged release app.

## Quick Start

1. Download `SmartAction-Release-v1.0.zip` from GitHub Releases.
2. Extract the zip to a writable folder, for example:

   ```text
   C:\Tools\SmartAction
   ```

3. Run:

   ```bat
   install.bat
   ```

4. Choose whether to create autostart and whether to run Firefox helper setup.
5. Start SmartAction with the Desktop shortcut, Start Menu shortcut, `start.bat`, or `SmartAction.exe`.

SmartAction runs in the Windows system tray. Right-click the tray icon to open Settings, PowerShell Library, Client Workspace, reload config, restart the hotkey, or exit.

Default hotkey:

```text
Ctrl + Alt + Space
```

## Configure Hotkey

1. Right-click the SmartAction tray icon.
2. Open **Settings**.
3. Use the Hotkey section to pick a new global hotkey.
4. Click **Save**.

If the hotkey does not respond, use the tray menu item **Restart Hotkey**.

## Add Ring Actions

1. Right-click the tray icon and open **Settings**.
2. Click **Add action**.
3. Choose an action type:
   - URL
   - App / File
   - Command
   - PowerShell
   - PowerShell Library
   - Environment Check
   - Client Workspace
   - Paste
   - Form
   - PS Form
4. Fill in the label, icon, target, and sub-actions as needed.
5. Click **Save**.

## PowerShell Library

The Ring `PowerShell Library` action opens the PowerShell Library window. In v1.0.0 it does not directly bind one specific library script to a Ring slot.

Inside PowerShell Library, users can review scripts, fill parameters, confirm dangerous scripts, and run them manually.

Some scripts can require administrator rights. Run SmartAction as administrator when executing scripts that change system settings.

## Firefox Setup

Firefox Container support requires two pieces:

1. Firefox extension: `firefox/firefox-helper.xpi`
2. Native Messaging Host: `firefox/native_host/smartaction_firefox_host.exe`

To register the Native Messaging Host for the current Windows user:

```bat
firefox\setup_firefox.bat
```

This writes to:

```text
HKCU\Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper
```

Admin rights are not normally required because registration uses `HKCU`, but company endpoint policy may still block it.

Important Firefox note: normal Firefox release builds usually require signed extensions. If Firefox refuses the bundled `firefox-helper.xpi`, use a signed XPI or your organization's normal extension deployment method.

## Uninstall

Run:

```bat
uninstall.bat
```

The uninstaller removes shortcuts and autostart. It asks before removing Firefox helper registration and asks again before deleting local package data.

To remove only Firefox helper registration:

```bat
firefox\uninstall_firefox.bat
```

## Troubleshooting

- **App does not open**: check whether SmartAction is already running in the system tray.
- **Hotkey does not work**: use tray menu -> Restart Hotkey, or choose a different hotkey in Settings.
- **Tray icon is missing**: check hidden tray icons and Windows notification settings.
- **Firefox helper check fails**: run `firefox\setup_firefox.bat`, install the XPI, restart Firefox, then use Client Workspace -> Check Helper.
- **Container not found**: create a Firefox Container with exactly the same name used in Client Workspace.
- **PowerShell action fails**: run SmartAction as administrator if the script changes system settings.

## Developer Setup

Use this only if you want to run or modify the source code.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## Build Release Package

From the project root:

```bat
build_release.bat
```

This creates:

```text
dist\SmartAction-Release-v1.0\
```

Zip this release folder and upload the zip to GitHub Releases. Do not commit the release zip or the `dist/` folder to `main`.

## Status

v1.0.0 is packaged for Windows as a tray-first desktop tool.
