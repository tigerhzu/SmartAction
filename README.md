# SmartAction

SmartAction 是一個 Windows tray + hotkey productivity launcher。它用全域快捷鍵叫出深色 radial Ring UI，讓 IT / support / power user 快速開啟網站、工具、PowerShell、環境檢查、客戶工作區與常用表單。

SmartAction is a Windows desktop launcher for repeatable IT and productivity workflows.

<a id="navigation"></a>
## 目錄 / Navigation

- [專案介紹 / Project Overview](#project-overview)
- [Download](#download)
- [主要功能 / Key Features](#key-features)
- [Quick Start](#quick-start)
- [Action Types](#action-types)
- [PowerShell Library](#powershell-library)
- [Firefox Setup](#firefox-setup)
- [專案架構 / Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Developer Setup](#developer-setup)
- [Release Notes](#release-notes)

<a id="project-overview"></a>
## 專案介紹 / Project Overview

SmartAction 是 tray-first 的 Windows 桌面工具，不是傳統一直顯示主視窗的 app。啟動後它會常駐在 system tray，使用者可以透過 tray menu 或全域 hotkey 開啟功能。

核心使用情境：

- 把常用網站、程式、資料夾、命令整理成 Ring action。
- 快速執行 PowerShell / IT support 工具。
- 管理客戶維運網站與 Firefox Container workflow。
- 一鍵查看 Windows 環境資訊。
- 匯入 / 匯出設定，方便備份或交接。

<a id="download"></a>
## Download

Download SmartAction from the **GitHub Releases** page:

```text
Releases -> SmartAction v1.0.0 -> SmartAction-Release-v1.0.zip
```

Do **not** use GitHub `Code > Download ZIP` for installation. That download is the source code, not the packaged release app.

Release zip should be uploaded to GitHub Releases, not committed into `main`.

<a id="key-features"></a>
## 主要功能 / Key Features

- System tray app with right-click menu.
- Global hotkey to open the Universal Actions Ring.
- Dark neon productivity UI for Settings, Ring, support dialogs, tray, and startup splash.
- Editable Ring actions and sub-actions.
- Settings dashboard for hotkey, theme, actions, import/export, and help.
- PowerShell Library for reusable scripts with parameters and dangerous-action confirmation.
- Environment Check for quick machine diagnostics.
- Client Workspace for grouped customer/support URLs.
- Firefox Container Helper integration for container-aware workspace launches.
- Release package with `install.bat`, `start.bat`, `uninstall.bat`, and Firefox helper scripts.

<a id="quick-start"></a>
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

To change it:

1. Right-click the SmartAction tray icon.
2. Open **Settings**.
3. Use the Hotkey section to pick a new global hotkey.
4. Click **Save**.

<a id="action-types"></a>
## Action Types

Ring actions can be configured from Settings.

| Type | 用途 | Example |
| --- | --- | --- |
| URL | 開啟網站 | Admin portal, docs, dashboard |
| App / File | 開啟本機 app、檔案或資料夾 | Task Manager, tools folder |
| Command | 執行 shell / cmd 指令 | `explorer C:\Tools` |
| PowerShell | 執行 PowerShell 指令 | `Get-Process` |
| PowerShell Library | 開啟 PowerShell Library 視窗 | reusable IT scripts |
| Environment Check | 顯示環境檢查結果 | Windows, network, DNS |
| Client Workspace | 開啟客戶工作區管理視窗 | grouped customer URLs |
| Paste | 貼上固定文字 | ticket reply snippet |
| Form | 單欄位輸入後貼上 | templated text |
| PS Form | PowerShell 表單工具 | Add Local User, Join Domain |

新增 action：

1. Open **Settings** from the tray.
2. Click **Add action**.
3. Choose an action type.
4. Fill in label, icon, target, and sub-actions as needed.
5. Click **Save**.

<a id="powershell-library"></a>
## PowerShell Library

The Ring `PowerShell Library` action opens the PowerShell Library window. In v1.0.0 it does not directly bind one specific library script to a Ring slot.

Inside PowerShell Library, users can:

- review reusable scripts,
- fill script parameters,
- confirm dangerous scripts,
- run scripts manually,
- view stdout / stderr / exit code.

Some scripts can require administrator rights. Run SmartAction as administrator when executing scripts that change system settings.

<a id="firefox-setup"></a>
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

To remove only Firefox helper registration:

```bat
firefox\uninstall_firefox.bat
```

<a id="project-structure"></a>
## 專案架構 / Project Structure

| Path | Responsibility |
| --- | --- |
| [app/](./app) | 正式啟動入口與 QApplication lifecycle。`python -m app.main` runs from here. |
| [core/](./core) | Action dispatch, config, hotkey, profile, PowerShell, Client Workspace, and business logic. |
| [ui/](./ui) | PySide6 UI: Ring, Settings, tray, dialogs, pickers, forms, shared styling tokens. |
| [config/](./config) | Active Ring/action configuration such as `actions.json`. |
| [extensions/](./extensions) | Firefox Container Helper WebExtension source. |
| [native/](./native) | Firefox Native Messaging Host source and templates. |
| [platforms/](./platforms) | OS-specific platform adapters. |
| [resources/](./resources) | Legacy/runtime resources and startup settings. |
| [tools/](./tools) | Build, release package, emoji database, and Firefox extension helper scripts. |
| [docs/](./docs) | Help, quick start, Firefox helper docs, release notes, and project documentation. |

Formal entry points:

- Source/dev entry: `python -m app.main`
- PyInstaller entry file: `app/main.py`
- Release executable: `SmartAction.exe`
- Release helper: `start.bat`

<a id="troubleshooting"></a>
## Troubleshooting

- **App does not open**: check whether SmartAction is already running in the system tray.
- **Hotkey does not work**: use tray menu -> Restart Hotkey, or choose a different hotkey in Settings.
- **Tray icon is missing**: check hidden tray icons and Windows notification settings.
- **Firefox helper check fails**: run `firefox\setup_firefox.bat`, install the XPI, restart Firefox, then use Client Workspace -> Check Helper.
- **Container not found**: create a Firefox Container with exactly the same name used in Client Workspace.
- **PowerShell action fails**: run SmartAction as administrator if the script changes system settings.

Uninstall:

```bat
uninstall.bat
```

The uninstaller removes shortcuts and autostart. It asks before removing Firefox helper registration and asks again before deleting local package data.

<a id="developer-setup"></a>
## Developer Setup

Use this only if you want to run or modify the source code.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Build release package:

```bat
build_release.bat
```

This creates:

```text
dist\SmartAction-Release-v1.0\
```

Zip this release folder and upload the zip to GitHub Releases. Do not commit the release zip or the `dist/` folder to `main`.

<a id="release-notes"></a>
## Release Notes

- Latest release notes: [docs/release-notes-v1.0.0.md](./docs/release-notes-v1.0.0.md)
- Release checklist: [docs/release-checklist.md](./docs/release-checklist.md)

v1.0.0 is packaged for Windows as a tray-first desktop tool.
