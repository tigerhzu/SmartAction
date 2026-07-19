# SmartAction 架構與功能說明

## 0. 目前架構狀態（2026-07-10）

- 正式啟動指令：`Set-Location C:\Users\naugh\smartaction; python -m app.main`。
- 正式流程是 `app.main` 建立 `Application`，再由 `app/application.py` 建立 QApplication、TrayIcon、RingWindow、SettingsWindow、startup splash 與支援視窗。
- 目前主要 UI 是 tray + hotkey launcher：System Tray 負責常駐入口，Universal Actions Ring 負責快捷執行，Settings 負責設定編輯。
- UI redesign 已執行到 Phase 5。Phase 4 已完成 tray icon / tray menu / About dialog / startup splash 的 dark neon productivity polish 與 splash adaptive sizing；Phase 5 已完成 release-readiness 自動 QA。
- 舊的 landing page 已移除；正式 UI 只保留系統匣、輪盤、設定與功能對話框。
- PowerShell Library action type 目前只負責從 Ring 開啟 PowerShell Library 視窗，尚未支援綁定單一 library script 並直接從 Ring 執行。
- Phase 5 自動 QA 通過範圍包含：Python source compile、正式入口 smoke test、主要 UI offscreen 建構、PowerShell Library action callback、action registry 與主要 JSON 設定讀取。正式 release 前仍需人工實機測試 tray、hotkey、startup splash、F11/Esc、1080p / 2K / DPI scaling 與高風險 action type。

本文件整理 SmartAction 目前的專案架構、功能模組、使用方式、打包流程與維護方式。它同時給開發維護者與需要了解產品能力的同事 / 客戶閱讀。

SmartAction 是一個 Windows 桌面工具，用 Python + PySide6 製作。核心概念是用全域快捷鍵叫出 Universal Actions Ring，讓使用者快速執行常用的 App、URL、Folder、PowerShell、IT 維護工具、Client Workspace 等動作。

---

## 1. 專案資料夾架構

### 根目錄

```text
smartaction/
├─ app/
├─ core/
├─ ui/
├─ assets/
├─ config/
├─ data/
├─ docs/
├─ extensions/
├─ native/
├─ resources/
├─ tools/
├─ dist/
├─ build/
├─ backups/
├─ build.bat
├─ build_extension.bat
├─ build_release.bat
├─ smartaction.spec
├─ requirements.txt
└─ README.md
```

### `app/`

應用程式入口與主生命週期。

- `app/main.py`：正式入口。開發時使用 `python -m app.main` 執行。這裡會做 debug log、single instance lock，然後建立 `Application`。
- `app/application.py`：主 QApplication。負責建立 hotkey、tray icon、ring window、settings window、PowerShell Library、Client Workspace、startup splash，並把各模組串起來。

### `core/`

核心邏輯層，不直接負責畫面。

- `core/paths.py`：所有路徑集中管理。開發版使用專案根目錄；PyInstaller 打包後，可寫資料放在 exe 旁邊，唯讀資源從 `_internal` / `sys._MEIPASS` 讀取。
- `core/actions_config.py`：主要輪盤設定，讀寫 `config/actions.json`。包含 hotkey、theme、actions tree。
- `core/config_manager.py`：舊版 / 補充設定，讀寫 `resources/config.json`。目前仍用於輕量啟動畫面等設定。
- `core/hotkey_manager.py`：全域快捷鍵註冊，使用 `keyboard` library。
- `core/action_runner.py`：Action dispatcher。點擊輪盤項目後，依照 action type 找到對應 action class 執行。
- `core/actions/`：各種 action type 的實作，例如 URL、App、PowerShell、PowerShell Library、Environment Check、Client Workspace。
- `core/powershell_library.py`：PowerShell Library 資料管理，讀寫 `data/powershell_library.json`。
- `core/powershell_runner.py`：PowerShell 執行與結果收集。
- `core/environment_check.py`：一鍵環境檢查，例如 Windows 版本、使用者、網路、DNS、防火牆等。
- `core/client_workspace.py`：Client Workspace 資料、Firefox profile、Firefox Container Helper、Native Host 狀態與啟動邏輯。
- `core/profile_manager.py`：Profile Import / Export。負責匯出設定、匯入設定、備份目前設定、敏感欄位遮蔽。
- `core/autostart.py`：Start with Windows 相關邏輯。
- `core/single_instance.py`：避免同時啟動多個 SmartAction。
- `core/debug_log.py`：debug log 輸出。
- `core/help_links.py`：Help Center 外部連結集中管理。

### `core/actions/`

Action 類型集中在這裡。每個 action class 透過 decorator 註冊到 registry。

- `registry.py`：action type registry。
- `base.py`：Action base class。
- `url_action.py`：開 URL。
- `app_action.py`：開啟本機 App。
- `command_action.py`：執行 command。
- `powershell_action.py`：執行一般 PowerShell action。
- `powershell_library_action.py`：目前從 Ring 開啟 PowerShell Library 視窗；尚未直接綁定並執行單一 `script_id`。
- `environment_check_action.py`：執行 Environment Check 並開結果視窗。
- `client_workspace_action.py`：從輪盤啟動 Client Workspace。
- `paste_action.py`：貼上文字。
- `form_action.py`：表單類 action。
- `ps_form_action.py`：PowerShell 表單類 action，例如 Join Domain、Add Local User。
- `submenu_action.py`：資料夾 / 子選單。

新增 action type 時，通常要新增一個 `core/actions/*_action.py`，再到 `core/actions/__init__.py` import，並在設定畫面中加入 type 選項。

### `ui/`

PySide6 GUI 介面。

- `ui/ring_ui.py`：Universal Actions Ring 輪盤視窗、Action bubble、點擊外部關閉、ESC 關閉、theme 動畫顯示。
- `ui/settings_window.py`：Settings 主視窗。管理 actions、theme、hotkey、Profile Import / Export、Help Center 等。
- `ui/tray_icon.py`：系統匣 icon 與右鍵選單。Phase 4 後已套用 dark neon tray menu 與 dark themed About dialog。
- `ui/startup_splash.py`：啟動影片 splash screen。Phase 4 後會依螢幕可用區域 clamp 尺寸並置中。
- `ui/theme_painter.py`：theme asset loader / painter，處理 Purple、Tiger、Ice、Lava、Cosmic 等主題素材與 fallback。
- `ui/emoji_picker.py`：Icon Picker / Emoji Picker。
- `ui/hotkey_picker.py`：Hotkey Picker，用點選方式選 Ctrl / Alt / Shift / Win 與主鍵。
- `ui/help_modal.py`：Help / Quick Start / Markdown 顯示。
- `ui/powershell_library_window.py`：PowerShell Library 管理視窗。
- `ui/client_workspace_window.py`：Client Workspace 管理視窗、Setup Status、Install Helper、Check Helper、Repair Setup、Open Add-ons。
- `ui/environment_check_window.py`：Environment Check 結果視窗。
- `ui/widgets.py`：共用 widget / style helper。

### `ui/forms/`

PowerShell 表單式工具。

- `add_local_user_form.py`：新增本機使用者表單。
- `join_domain_form.py`：加入網域表單。
- `form_registry.py`：表單 registry。

### `assets/`

視覺與媒體資源。

- `assets/themes/`：輪盤主題素材。
  - `purple/`
  - `tiger/`
  - `ice/`
  - `lava/`
  - `cosmic/`
  - 每個主題包含最佳化動畫幀、`card_bg.png`，並可選擇提供 `rim.png` 靜態 fallback。
- `assets/startup/`：可選擇放置 PNG、JPG 或 GIF 啟動畫面；預設停用。
- `assets/wiki/`：Help / Wiki 圖片可放置處。

### `config/`

主要使用者設定。

- `config/actions.json`：目前最重要的設定檔。包含：
  - `hotkey`
  - `theme`
  - root actions
  - sub actions
  - action type
  - action id
  - icon / label / target / script_id / client_id 等

開發版讀寫專案內的 `config/actions.json`。打包版讀寫 exe 旁邊的 `config/actions.json`。

### `data/`

功能資料庫與使用者資料。

- `data/powershell_library.json`：PowerShell Library 腳本。
- `data/client_workspaces.json`：Client Workspace 客戶與 URL。
- `data/icons/emoji_database.json`：Icon Picker 使用的本機 emoji / icon database。
- `data/icons/icon_picker_state.json`：Icon Picker recent / favorites 狀態。
- `data/smartaction.lock`：single instance lock 相關 runtime 檔案。

### `docs/`

內建說明文件與維護文件。

- `docs/help.md`：App 內建 Help markdown。
- `docs/quick-start.md`：Quick Start。
- `docs/help-center.md`：Help Center 說明。
- `docs/client-workspace.md`：Client Workspace 文件。
- `docs/firefox-container-helper.md`：Firefox Container Helper 使用說明。
- `docs/firefox-helper-signing.md`：XPI 送 AMO unlisted signing 的說明。

### `extensions/`

瀏覽器 extension。

- `extensions/firefox-helper/manifest.json`：SmartAction Container Helper WebExtension manifest。
- `extensions/firefox-helper/background.js`：接收 Native Messaging 指令、查找 Firefox Container、用 `cookieStoreId` 開分頁。
- `extensions/firefox-helper/README.md`：extension 開發 / 安裝說明。

目前 extension 顯示名稱是 `SmartAction Container Helper`，add-on id 是：

```text
smartaction-container-helper@naughtytiger06.local
```

### `native/`

Native Messaging Host。

- `native/firefox_helper_host/smartaction_firefox_host.py`：Native Messaging Host 主程式。
- `native/firefox_helper_host/host_manifest.json.template`：Native Host manifest template。
- `native/firefox_helper_host/install_host_windows.py`：Windows Native Host 安裝工具。
- `native/firefox_helper_host/README.md`：Native Host 說明。

正式 release 會另外建立 `native_host/smartaction_firefox_host.exe`，給同事不用裝 Python 也能安裝。

### `resources/`

舊版資源與設定。

- `resources/config.json`：舊版 / 補充設定，包含輕量啟動畫面設定等。

### `tools/`

開發與打包工具。

- `tools/build_firefox_extension.py`：打包 `extensions/firefox-helper` 成 `dist/firefox-helper.xpi`。
- `tools/build_release_package.py`：建立給同事使用的 `dist/SmartAction-Release/`。
- `tools/build_emoji_database.py`：產生 / 更新 `data/icons/emoji_database.json`。

### `dist/`

打包輸出，不是原始碼。

- `dist/UniversalActionsRing/UniversalActionsRing.exe`：PyInstaller 打包後的主要 exe。
- `dist/firefox-helper.xpi`：Firefox helper extension XPI。
- `dist/SmartAction-Release/`：給同事使用的 release package。
  - `SmartAction.exe`
  - `setup.bat`
  - `firefox-helper.xpi`
  - `install_native_host.bat`
  - `install_native_host.ps1`
  - `native_host/smartaction_firefox_host.exe`
  - `README_安裝說明.txt`
  - `clients.json`

### `build/`

PyInstaller 中間產物。可以刪除，會由 build scripts 重新產生。

### `backups/`

匯入 Profile 或 Client Workspace JSON 前的備份資料。

---

## 2. 程式整體架構

### 啟動入口

開發版入口：

```bat
python -m app.main
```

流程：

1. `app/main.py` 記錄 app entry path、cwd、是否 frozen。
2. `core/single_instance.py` 取得 single instance lock，避免開第二個 SmartAction。
3. 建立 `Application`。
4. `Application.run()`：
   - 檢查 system tray。
   - 建立 / 註冊 global hotkey。
   - 建立 tray icon。
   - 視設定顯示輕量 startup splash，或直接進入背景。
   - App 留在背景等待 hotkey。

### GUI 組成

SmartAction 不是傳統一直顯示主視窗的工具，而是 tray + hotkey 型桌面工具。

主要 GUI：

- System Tray：右鍵選單進 Settings、PowerShell Library、Client Workspace、Reload Config、Restart Hotkey、Exit。Phase 4 後使用 dark neon context menu 與 SmartAction About dialog。
- Universal Actions Ring：按全域 hotkey 時顯示的輪盤。
- Settings Window：編輯 actions、theme、hotkey、profile、help。
- PowerShell Library Window：管理常用 PowerShell 腳本。
- Client Workspace Window：管理客戶網站、Firefox Profile、Container Helper 狀態。
- Environment Check Window：顯示一鍵環境檢查結果。
- Help Modal / Help Center：App 內建說明與 GitHub 連結。
- Icon Picker：選 Action icon / emoji。
- Hotkey Picker：用點選 UI 設定 hotkey。

### 設定檔儲存

SmartAction 目前有幾個不同用途的設定檔：

| 檔案 | 用途 |
| --- | --- |
| `config/actions.json` | 輪盤 actions、hotkey、theme，是目前最主要設定 |
| `resources/config.json` | 舊版 / 補充設定，例如 startup splash |
| `data/powershell_library.json` | PowerShell Library 腳本 |
| `data/client_workspaces.json` | Client Workspace 客戶資料與 URL |
| `data/icons/emoji_database.json` | Icon Picker 本機 icon database |
| `data/icons/icon_picker_state.json` | Icon Picker recent / favorites |
| `backups/*.json` | 匯入前備份 |

開發版路徑：

- `config/`
- `resources/`
- `data/`
- `backups/`

打包版路徑：

- 可寫設定放在 exe 旁邊，例如 `dist/UniversalActionsRing/config/actions.json`。
- bundled assets / docs 放在 `_internal/` 裡，由 `core/paths.py` 透過 `sys._MEIPASS` 讀取。

### 熱鍵 / 輪盤 / 快捷功能如何運作

1. `Application` 讀取 `ActionsConfig.get_hotkey()`。
2. `HotkeyManager` 用 `keyboard.add_hotkey()` 註冊全域快捷鍵。
3. 使用者按 hotkey 後，`Application._on_ring_triggered()` 被呼叫。
4. 如果輪盤已經顯示，就關閉；如果沒顯示，就讀取 `config/actions.json` 並呼叫 `RingWindow.show_at_cursor(items, theme)`。
5. 使用者點擊輪盤 action。
6. `RingWindow` emit `item_activated`。
7. `Application` 呼叫 `ActionRunner.run(item, context)`。
8. `ActionRunner` 依照 `item.action_type` 到 registry 找 action class。
9. 對應 action 執行，例如開 URL、執行 PowerShell、啟動 Client Workspace。

Action registry 的好處是：新增 action type 時不需要在 ActionRunner 裡寫一堆 if / else。

### 資源放置規則

- Theme 動畫 / rim / card background：`assets/themes/<theme_id>/`
- Startup splash：`assets/startup/` 下的 PNG、JPG 或 GIF（預設停用）
- Startup GIF fallback：`assets/startup/startup.gif`
- Icon Picker database：`data/icons/emoji_database.json`
- Help markdown：`docs/help.md`、`docs/quick-start.md`
- Help 圖片：`docs/images/` 或 `assets/wiki/`
- PowerShell helper scripts：`core/scripts/`
- Firefox extension：`extensions/firefox-helper/`
- Native messaging host：`native/firefox_helper_host/`

### Release 版本和開發版本差異

開發版：

- 用 `python -m app.main` 執行。
- 直接讀寫專案資料夾裡的 `config/`、`data/`、`resources/`。
- 適合開發、測試、修改 UI。

PyInstaller 打包版：

- 用 `build.bat` 產生。
- 輸出在 `dist/UniversalActionsRing/UniversalActionsRing.exe`。
- exe 旁會有可寫的 `config/`、`data/`、`resources/`。
- `_internal/` 裡放 PySide6 runtime、assets、docs、scripts 等 bundled resources。

同事 Release Package：

- 用 `build_release.bat` 產生。
- 輸出在 `dist/SmartAction-Release/`。
- 目標是讓同事拿整個資料夾後，執行 `setup.bat` 完成必要安裝。
- 包含 `SmartAction.exe`、`firefox-helper.xpi`、Native Host installer、README、範例 clients JSON。

---

## 3. 目前已有功能簡述

### 快捷輪盤

Universal Actions Ring 是 SmartAction 的核心。使用者按下 Global Hotkey 後，游標附近會顯示圓形快捷輪盤。輪盤支援多層資料夾、Action bubble、icon / emoji、short label、theme 動畫與點擊外部關閉。

### 自訂功能按鈕

使用者可以在 Settings 裡新增 / 編輯 / 刪除 actions。支援 root action 與 sub action。每個 action 有固定 id，不依賴顯示名稱，因此改名後仍可維持排序與關聯。

目前常見 Action Type：

- App
- URL
- Folder
- File
- Command
- PowerShell
- PowerShell Library
- Environment Check
- Client Workspace
- Paste
- Form
- PS Form

### PowerShell 指令執行

一般 PowerShell Action 可直接在輪盤上執行 PowerShell 指令。PowerShell 執行結果會整理 stdout、stderr、exit code 與執行時間，不只丟 Python traceback。

### PowerShell Library

PowerShell Library 是一個 IT 工具箱，可以集中管理常用 PowerShell 腳本。

每個 script 包含：

- id
- name
- description
- category
- script_content
- need_admin
- risk_level
- parameters

支援 safe / dangerous 風險等級。Dangerous script 執行前會跳確認視窗。Password parameter 會遮蔽，不會在確認或結果視窗顯示明文。

PowerShell Library 目前也可以作為 Ring action type，但點擊後是開啟 PowerShell Library 視窗。輪盤設定目前不需要 `script_id`，尚未支援從 Ring 直接綁定並執行單一 Library script。

### Local User / AD / Domain IT 維護功能

目前有表單式 PowerShell 工具架構，例如：

- Add Local User
- Join Domain

相關 script 放在 `core/scripts/`，表單 UI 放在 `ui/forms/`。

PowerShell Library 內也已包含 System、Network、User Management、Domain / AD、Repair Tools、Custom 等分類，可擴充更多 IT 維護腳本。

### Wiki / 使用說明 / Help Center

Settings 右上角有 Help Center。內容包含：

- Quick Start / 快速教學：App 內建說明視窗。
- Full Documentation：開啟 GitHub README。
- Open GitHub Repository：開 GitHub repo。
- Report Issue：開 GitHub Issues。
- About SmartAction：開 README about 區塊。

本機 help markdown 放在 `docs/`。

### Emoji / Icon Picker

Icon Picker 是產品化的 icon 選擇器，支援：

- 搜尋 icon name / keywords / category
- 多分類
- Recent
- Favorites
- Preview
- Clear
- Select / Apply
- 雙擊套用
- 鍵盤操作

資料來源是本機 `data/icons/emoji_database.json`，狀態存於 `data/icons/icon_picker_state.json`。

### Hotkey Picker

Hotkey Picker 使用小型鍵盤 UI，不靠實際鍵盤監聽偵測輸入。使用者可以點選 Ctrl / Alt / Shift / Win 與主鍵，並有危險快捷鍵檢查，避免使用常見系統快捷鍵。

### 啟動畫面影片

Startup Splash 支援 PNG、JPG 或 GIF，且預設停用。啟用時最多顯示 5 秒；結束或按 Skip 後進入背景 / system tray。若圖片不存在或載入失敗，會直接跳過，不影響啟動。Splash 會依目前螢幕的 availableGeometry() 自動限制大小並置中。

### 匯出 / 匯入設定檔

Profile Import / Export 可將目前設定匯出為版本化 JSON。內容包含：

- app settings
- hotkey
- actions
- theme / UI 設定
- PowerShell Library
- Client Workspaces

匯入前會自動備份目前設定到 `backups/`。敏感欄位如 password、token、api key、secret 會遮蔽。

### 客戶工作區 / Firefox Container 開啟維運網站

Client Workspace 用來管理客戶與其維運網址。

每個 client 包含：

- id
- name
- containerName
- firefoxProfile
- urls

啟動工作區時：

- 如果沒有設定 containerName，使用一般 Firefox 分頁開啟 URL。
- 如果有設定 containerName，會透過 SmartAction Container Helper extension + Native Messaging Host 找到對應 Firefox Container，並在該 container 內開啟 URL。

Client Workspace 視窗也提供 Setup Status：

- Firefox 是否已安裝
- Firefox Multi-Account Containers 是否已安裝
- SmartAction Container Helper 是否已安裝
- Native Host 是否已註冊
- Helper 是否 connected

並提供：

- Install Helper Extension
- Check Helper
- Repair Setup
- Open Add-ons

### 環境檢查

Environment Check 是可掛到輪盤的 action type。點擊後會檢查：

- Windows 版本
- 目前登入使用者
- 是否系統管理員
- 電腦名稱
- 是否加入網域
- IP address
- Gateway
- DNS servers
- 是否能 ping gateway
- 是否能解析 DNS
- PowerShell Execution Policy
- 防火牆狀態

結果視窗支援 Copy Result，方便貼到工單或傳給同事。

### Theme 視覺

目前支援：

- Purple
- Tiger Fur
- Ice / Frozen
- Fire / Lava
- Space / Cosmic

Theme asset 支援 frame animation。若素材不存在，會 fallback 到 QPainter 繪製，不讓 App crash。

### Single Instance

SmartAction 會限制單一實例。若背景已經有 SmartAction，再次啟動不會開第二個背景程序。

### Start with Windows

Settings 內有 Start with Windows 相關設定，透過 `core/autostart.py` 處理 Windows 開機啟動。

---

## 4. 使用方式

### 使用者怎麼啟動

開發版：

```bat
python -m app.main
```

打包版：

```bat
dist\UniversalActionsRing\UniversalActionsRing.exe
```

同事 Release 版：

```bat
dist\SmartAction-Release\setup.bat
dist\SmartAction-Release\SmartAction.exe
```

第一次給同事使用時，建議先執行 `setup.bat`，它會安裝 Native Messaging Host、複製 XPI，並提示下一步安裝 SmartAction Container Helper。

### 怎麼叫出輪盤

1. 啟動 SmartAction。
2. App 會留在 system tray。
3. 按 `config/actions.json` 內設定的 global hotkey。
4. Universal Actions Ring 出現。
5. 點擊 action 執行功能。
6. 點輪盤外部空白處、中央 X 或 ESC 可取消。

### 怎麼新增功能

1. 右鍵 system tray icon。
2. 選 `Open Settings`。
3. 在 Action / Menu 編輯區新增 action。
4. 選擇 Action Type。
5. 填入 Display Name、Icon、Target 或對應欄位。
6. 儲存 Settings。
7. 再次按 hotkey 開輪盤，即可看到新 action。

### 怎麼修改設定

大部分日常設定都應從 Settings 修改。

若需要手動修改：

- 輪盤 actions / hotkey / theme：改 `config/actions.json`
- 啟動影片設定：改 `resources/config.json`
- PowerShell Library：改 `data/powershell_library.json`
- Client Workspace：改 `data/client_workspaces.json`
- Help 文件：改 `docs/*.md`

手動改 JSON 前建議先備份。

### 怎麼打包成 exe

在專案根目錄執行：

```bat
build.bat
```

它會：

1. 安裝 dependencies。
2. 清除舊的 `build/`、`dist/`、`__pycache__/`。
3. 清 PyInstaller cache。
4. 用 `smartaction.spec` 打包 `app/main.py`。
5. 複製可寫 config / data 到 exe 旁。
6. 打包 Container Helper XPI。
7. 驗證必要資源是否存在。

輸出：

```text
dist/UniversalActionsRing/UniversalActionsRing.exe
dist/firefox-helper.xpi
```

### 怎麼打包 Firefox Helper Extension

```bat
build_extension.bat
```

輸出：

```text
dist/firefox-helper.xpi
%LOCALAPPDATA%\SmartAction\firefox-helper.xpi
```

正式給同事長期使用時，XPI 應使用 AMO unlisted signing 後的版本。

### 怎麼建立給同事的 Release

先執行：

```bat
build.bat
```

再執行：

```bat
build_release.bat
```

輸出：

```text
dist/SmartAction-Release/
```

分享給同事時，建議給整個資料夾，不要只給單一 exe。因為 release 需要包含 XPI、Native Host installer、assets、config、data、docs 與 PyInstaller runtime。

---

## 5. 維護方式

### 修改輪盤視覺 / Click Outside / Theme

主要檔案：

- `ui/ring_ui.py`
- `ui/theme_painter.py`
- `assets/themes/`

Theme frame、rim、card background 請放在：

```text
assets/themes/<theme_id>/
```

修改後執行：

```bat
python -m compileall app core ui native tools
python -m app.main
```

### 修改 Settings UI

主要檔案：

- `ui/settings_window.py`
- `ui/hotkey_picker.py`
- `ui/emoji_picker.py`

如果新增 Action Type，Settings 也要加入對應欄位與儲存邏輯。

### 新增 Action Type

通常需要改：

1. 新增 `core/actions/<type>_action.py`
2. 在 `core/actions/__init__.py` import 新 action module
3. 在 `core/actions_config.py` 的 `_normalise_type()` 加入 type mapping
4. 在 Settings action type 下拉選單加入顯示名稱
5. 若有特殊欄位，在 `ui/settings_window.py` 補 UI
6. 若要顯示結果視窗，新增或修改 `ui/*_window.py`

### 修改 PowerShell Library

主要檔案：

- `core/powershell_library.py`
- `core/powershell_runner.py`
- `ui/powershell_library_window.py`
- `core/actions/powershell_library_action.py`
- `data/powershell_library.json`

預設腳本在 `core/powershell_library.py` 的 `DEFAULT_SCRIPTS`。使用者實際資料在 `data/powershell_library.json`。

### 修改 Client Workspace / Firefox Container

主要檔案：

- `core/client_workspace.py`
- `ui/client_workspace_window.py`
- `core/actions/client_workspace_action.py`
- `extensions/firefox-helper/background.js`
- `extensions/firefox-helper/manifest.json`
- `native/firefox_helper_host/smartaction_firefox_host.py`
- `native/firefox_helper_host/host_manifest.json.template`
- `docs/firefox-container-helper.md`
- `docs/firefox-helper-signing.md`

注意：

- Extension add-on id 與 Native Host `allowed_extensions` 必須一致。
- 目前 id 是 `smartaction-container-helper@naughtytiger06.local`。
- 不要使用 temporary profile 或 `-no-remote` 來啟動 Firefox，避免 helper 安裝在另一個 profile 卻被錯誤 instance 使用。

### 修改 Help Center

主要檔案：

- `ui/help_modal.py`
- `core/help_links.py`
- `docs/help.md`
- `docs/quick-start.md`
- `docs/help-center.md`
- `docs/client-workspace.md`
- `docs/firefox-container-helper.md`

外部 GitHub 連結集中在 `core/help_links.py`。

### 修改 Icon Picker / Emoji Database

主要檔案：

- `ui/emoji_picker.py`
- `data/icons/emoji_database.json`
- `data/icons/icon_picker_state.json`
- `tools/build_emoji_database.py`

如果更新 emoji database，建議用 tools 產生，不要手工大量編輯 JSON。

### 修改啟動影片

主要檔案：

- `ui/startup_splash.py`
- `resources/config.json`
- `assets/startup/`（可選 PNG、JPG 或 GIF）
- `assets/startup/startup.gif`

設定鍵：

```json
{
  "startup_video_enabled": false,
  "startup_video_duration": 5,
  "startup_video_path": "assets/startup/startup.png"
}
```

### 修改 Profile Import / Export

主要檔案：

- `core/profile_manager.py`
- `ui/settings_window.py`
- `backups/`

匯入前一定要保留備份機制，避免壞 JSON 或不相容版本破壞現有設定。

### 修改打包流程

主要檔案：

- `build.bat`
- `smartaction.spec`
- `build_extension.bat`
- `tools/build_firefox_extension.py`
- `build_release.bat`
- `tools/build_release_package.py`

如果新增 assets、docs、data icons 或 core scripts，要確認：

1. `smartaction.spec` 是否有 bundled 到 `_internal/`。
2. `build.bat` 是否有複製可寫資料到 exe 旁。
3. `tools/build_release_package.py` 是否有放進 `dist/SmartAction-Release/`。

### 修改完怎麼驗證

基本語法檢查：

```bat
python -m compileall app core ui native tools
```

開發版測試：

```bat
python -m app.main
```

正式打包：

```bat
build.bat
```

建立同事 release：

```bat
build_release.bat
```

### 哪些資料夾不要直接改

以下通常是自動產生或打包輸出，不建議手動修改：

- `build/`
- `dist/UniversalActionsRing/`
- `dist/SmartAction-Release/`
- `dist/firefox-helper/`
- `__pycache__/`
- `*.pyc`

如果需要修改功能，應改原始碼與原始資源，再重新打包。

### 哪些檔案是自動產生的

- `build/`：PyInstaller build cache。
- `dist/UniversalActionsRing/`：`build.bat` 產生。
- `dist/firefox-helper.xpi`：`build_extension.bat` 或 `build.bat` 產生。
- `dist/SmartAction-Release/`：`build_release.bat` 產生。
- `data/smartaction.lock`：single instance runtime lock。
- `backups/backup_profile_*.json`：Profile import 前自動備份。
- `client_workspaces.backup.*.json`：Client Workspace import 前備份。
- `app_debug.log`：debug log。

---

## 6. 建議開發工作流

一般功能修改：

```bat
python -m compileall app core ui native tools
python -m app.main
```

確認功能 OK 後：

```bat
build.bat
```

要交給同事：

```bat
build_release.bat
```

交付資料夾：

```text
dist/SmartAction-Release/
```

同事端第一次安裝：

```bat
setup.bat
SmartAction.exe
```

---

## 7. 快速對照表

| 想改的東西 | 優先看這些檔案 |
| --- | --- |
| App 入口 / 啟動流程 | `app/main.py`, `app/application.py` |
| 路徑問題 / exe 路徑 | `core/paths.py` |
| 輪盤 UI | `ui/ring_ui.py` |
| Theme 動畫 | `ui/theme_painter.py`, `assets/themes/` |
| Settings | `ui/settings_window.py` |
| Hotkey | `core/hotkey_manager.py`, `ui/hotkey_picker.py`, `config/actions.json` |
| Action 執行 | `core/action_runner.py`, `core/actions/` |
| 新增 Action Type | `core/actions/`, `core/actions_config.py`, `ui/settings_window.py` |
| PowerShell Library | `core/powershell_library.py`, `ui/powershell_library_window.py` |
| Environment Check | `core/environment_check.py`, `ui/environment_check_window.py` |
| Client Workspace | `core/client_workspace.py`, `ui/client_workspace_window.py` |
| Firefox Extension | `extensions/firefox-helper/` |
| Native Messaging Host | `native/firefox_helper_host/` |
| Help Center | `ui/help_modal.py`, `core/help_links.py`, `docs/` |
| Icon Picker | `ui/emoji_picker.py`, `data/icons/` |
| Startup Video | `ui/startup_splash.py`, `assets/startup/`, `resources/config.json` |
| Profile Import / Export | `core/profile_manager.py` |
| PyInstaller 打包 | `smartaction.spec`, `build.bat` |
| Release Package | `tools/build_release_package.py`, `build_release.bat` |

---

## 8. 目前專案定位

SmartAction 可以介紹成：

> SmartAction 是一個給 IT 維護與日常工作自動化使用的輕量級 Universal Actions Ring。它把常用網站、系統工具、PowerShell 腳本、環境檢查、客戶維運工作區與 Firefox Container 管理整合在同一個快捷輪盤中，讓使用者用一個全域快捷鍵快速完成工作。

對一般使用者來說，它是快捷輪盤。

對 IT 維護者來說，它是 PowerShell 工具箱、環境檢查器、客戶工作區啟動器。

對開發維護者來說，它是一個 PySide6 desktop app，核心分成 GUI、config、action registry、resource path、release packaging 幾層，後續擴充 Action Type 或 IT 工具時，不需要重寫整個 App。
