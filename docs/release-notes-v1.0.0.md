# SmartAction v1.0.0 Release Notes

Release asset:

```text
SmartAction-Release-v1.0.zip
```

Download the release zip from GitHub Releases. Do not use `Code > Download ZIP`; that downloads the source code, not the packaged app.

## New Features

- Windows tray-first SmartAction desktop launcher.
- Global hotkey opens the Universal Actions Ring.
- Dark neon productivity UI across Settings, Ring, support dialogs, tray menu, and startup splash.
- Configurable Ring actions:
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
- Settings window for editing actions, themes, hotkey, profile import/export, and app options.
- PowerShell Library window for reviewing and running reusable scripts.
- Environment Check window for quick machine diagnostics.
- Client Workspace for opening grouped maintenance URLs.
- Firefox Container Helper package for container-aware Client Workspace launches.
- Adaptive sizing for main dialogs and Ring UI across common desktop resolutions.
- `install.bat`, `uninstall.bat`, and `start.bat` helper scripts for colleague installs.

## Installation

1. Download `SmartAction-Release-v1.0.zip` from this GitHub Release.
2. Extract the zip to a writable folder, for example:

   ```text
   C:\Tools\SmartAction
   ```

3. Run:

   ```bat
   install.bat
   ```

4. Choose whether to enable Windows autostart.
5. Choose whether to run Firefox helper setup.
6. Launch SmartAction from the Desktop shortcut, Start Menu shortcut, `start.bat`, or `SmartAction.exe`.

Default hotkey:

```text
Ctrl + Alt + Space
```

## Firefox Notes

Firefox Container support requires:

- `firefox/firefox-helper.xpi`
- `firefox/native_host/smartaction_firefox_host.exe`
- Native Messaging Host registration through `firefox/setup_firefox.bat`

The native host registration uses:

```text
HKCU\Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper
```

Admin rights are not normally required because registration is per-user under HKCU. However, company endpoint policy or registry restrictions may still require IT/admin help.

Regular Firefox release builds usually require signed extensions. If Firefox refuses the included XPI, deploy a signed XPI through your normal organization process.

## Known Limitations

- PowerShell Library Ring action opens the PowerShell Library window only. It does not yet bind and directly run one specific library script from the Ring.
- Firefox Container support requires both the extension and native host registration.
- The included XPI may require signing before it can be installed in standard Firefox release builds.
- Some PowerShell actions require administrator rights.
- High-impact actions such as domain join, local user changes, shutdown/restart, or system repair scripts should be reviewed before sharing with non-admin users.
- Real machine QA is still recommended for tray visibility, global hotkey registration, Firefox helper setup, and endpoint security policy behavior.

## Uninstall

Run:

```bat
uninstall.bat
```

The uninstaller removes shortcuts and autostart. It asks before removing Firefox helper registration and asks again before deleting local package data.

To remove only the Firefox helper registration:

```bat
firefox\uninstall_firefox.bat
```

