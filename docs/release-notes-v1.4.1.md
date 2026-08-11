# SmartAction v1.4.1 Release Notes

## 重點更新

- 修正 Web Control Center 的 PowerShell 執行對話框：改由表單送出，避免按下 Enter 或重複點擊時產生重複執行請求。
- 執行期間會停用送出按鈕並顯示「Core 執行中…」，完成或失敗後會恢復操作。
- PowerShell 執行結果會顯示在腳本清單之前並自動捲動至結果，方便確認 stdout、stderr 或錯誤訊息。
- Local API 對 Control Center 的靜態檔案加入 `Cache-Control: no-store`，避免已開啟的瀏覽器使用舊版 JavaScript/CSS。

## 給使用者

- 下載 `SmartAction-v1.4.1-portable.zip`，完整解壓到可寫入的資料夾後執行 `install.bat`、`start.bat` 或 `SmartAction.exe`。
- 請保留完整資料夾結構；不要只複製 `SmartAction.exe`。
- Firefox Container 功能仍需要執行 `firefox\\setup_firefox.bat`，並在 Firefox 安裝已簽署的 helper XPI。

## 已驗證

- 全部既有單元／整合測試通過。
- Ruff lint 與 Python compile check 通過。
- PyInstaller onedir portable build、Firefox XPI/native host 與 release ZIP 結構驗證通過。
