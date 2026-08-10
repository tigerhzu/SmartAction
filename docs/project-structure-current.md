# SmartAction 現行專案結構

SmartAction 是 Windows 的 tray-first 應用程式。原生 PySide6 層保留 Action Ring、系統匣、全域快捷鍵與視覺效果；大型管理功能已改由同機的 Web Control Center 呈現，並透過有驗證的 Local API 呼叫 Core service。

## 執行流程

1. `app/main.py` 取得單一執行個體 lock。
2. `app/application.py` 建立 `SmartActionCore`、Action Ring、系統匣、快捷鍵管理器與 `LocalApiServer`。
3. `LocalApiServer` 僅監聽 `127.0.0.1`，每次啟動建立 token，並提供 `web_control_center/` 靜態檔案。
4. 快捷鍵顯示 Ring；Ring 使用 `ActionRunner` 與 Action Registry 分派執行。
5. Control Center 經由 Local API 讀寫設定、Action、PowerShell Library 與 Client Workspace；具權限的操作由 Core service 執行。

## 主要目錄

| 路徑 | 職責 |
| --- | --- |
| `app/` | 入口、Qt application lifecycle、原生整合。 |
| `core/` | Action contract／service、設定、Profile、原子儲存、PowerShell、Client Workspace、Local API。 |
| `core/actions/` | 已註冊的 Action handler。 |
| `ui/` | Ring、系統匣、主題、背景與必要的原生對話框。 |
| `web_control_center/` | Control Center 的靜態 HTML、CSS、JavaScript 與品牌素材。 |
| `config/`、`data/`、`resources/` | 可寫入的 runtime 設定與資料。 |
| `extensions/`、`native/` | Firefox extension 與 Native Messaging Helper。 |
| `assets/` | 打包進發行版的唯讀主題與 UI 素材。 |
| `tools/` | 建置、release package、Firefox extension 與資料工具。 |
| `tests/` | UI 回歸、Core service、Local API、Profile reload 與 Web cutover 測試。 |

`build/`、`dist/`、`.venv/`、`__pycache__/`、log、lock、backup、local profile 與 IDE 檔案均屬本機或產物，不應提交。

## Core 邊界

- `SmartActionCore` 組合長生命週期服務，不依賴原生視窗。
- `ActionConfigService` 與 `ConfigService` 提供已驗證且 detached 的資料快照。
- `PowerShellLibraryService` 與 `ClientWorkspaceService` 使用 `ExecutionRequest`／`ExecutionResult`，將失敗以結構化結果回傳。
- `LocalApiServer` 是 HTTP adapter，不包含 Windows 商業邏輯或直接 subprocess／檔案操作。
- `AtomicJsonStore` 以同目錄暫存檔、`fsync`、`os.replace` 寫入，避免中斷時留下半份 JSON。

## Build 與資料路徑

原始碼模式下，可寫入資料位於專案根目錄。PyInstaller 發行版則將 assets、web shell、文件與內建腳本置於唯讀 bundle，將 `config/`、`data/`、`resources/`、`backups/` 放在可執行檔同層。`tools/build_release_package.py` 會重建乾淨的 runtime 資料並檢查 cache、log 與已知本機路徑是否外洩。
