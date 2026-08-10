# SmartAction v1.4.0 Release Notes

## 重點更新

- 新增 Web Control Center：由預設瀏覽器提供設定、Action、設定檔、PowerShell 腳本庫與 Client Workspace 的管理介面。
- 導入 `SmartActionCore` 與 UI-free services，將設定、PowerShell、Client Workspace 與資料存取從原生管理視窗分離。
- 新增 authenticated loopback Local API：固定綁定 `127.0.0.1`、每次啟動產生 token、限制請求大小並使用同源 CSP。
- 新增 Action schema validation、結構化執行結果與原子 JSON 寫入。
- 移除已被 Web Control Center 取代的舊原生 Settings、PowerShell Library 與 Client Workspace 管理視窗。

## 給使用者

- 請下載 `SmartAction-v1.4.0-portable.zip`，完整解壓到可寫入的資料夾後執行 `install.bat` 或 `SmartAction.exe`。
- 不要只複製 `SmartAction.exe`；Firefox Helper、設定與 runtime 檔案必須保留在同一個資料夾結構。
- 第一次使用請從系統匣開啟「控制中心」，在瀏覽器管理 Ring 與工作流程。

## 已驗證

- `python -m unittest discover -s tests -p "test_*.py"`：58 項測試通過。
- portable release 包含 Control Center 的 HTML、CSS、JavaScript 與 logo，並在打包流程檢查已知本機路徑、cache、log 與 lock 檔未外洩。
