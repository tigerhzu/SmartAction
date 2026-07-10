# Troubleshooting / 常見問題

這裡整理 SmartAction 常見問題與排查方式。

---

## 快捷鍵沒有反應

可能原因：

- 尚未按 Save
- 快捷鍵被其他程式占用
- SmartAction 沒有在背景執行
- 快捷鍵格式不支援
- 程式發生錯誤

建議處理：

1. 開啟 Settings
2. 確認 Global Hotkey
3. 按 Save
4. 關閉 Settings
5. 再測試快捷鍵

如果仍然無效，請換一組快捷鍵測試。

---

## exe 是舊版

如果你修改了程式碼，但打開 exe 後還是舊畫面，通常是因為沒有重新打包。

請重新執行：

```powershell
.\build.bat
```

如果怕舊檔案殘留，可以先刪除：

```powershell
rmdir /s /q build
rmdir /s /q dist
.\build.bat
```

打包完成後，請確認你開的是 `dist` 裡的新 exe。

---

## 打包後功能不見

可能原因：

- 新增的檔案沒有被 smartaction.spec 包進去
- build.bat 沒有更新
- 你開到舊 exe
- data / docs / extensions / native 資料夾沒有被包含

建議檢查：

- `smartaction.spec`
- `build.bat`
- `dist` 資料夾內容
- 是否有重新打包

---

## Firefox 找不到

可能原因：

- 電腦沒有安裝 Firefox
- Firefox 安裝路徑不是預設位置
- SmartAction 找不到 firefox.exe

建議處理：

1. 先手動打開 Firefox
2. 確認 Firefox 可以正常啟動
3. 檢查 SmartAction 是否支援手動指定 Firefox 路徑

---

## Client Workspace 沒有開啟網址

可能原因：

- 該客戶沒有設定 URL
- URL 欄位是空的
- URL 格式錯誤
- Firefox 找不到
- containerName 設定錯誤
- Firefox Helper Extension 沒有回應

建議處理：

1. 確認客戶有 URL
2. 確認 URL 有 `http://` 或 `https://`
3. 若 containerName 空白，測試一般 Firefox 分頁是否能開啟
4. 若 containerName 有值，檢查 Firefox Helper Extension

---

## Container not found

錯誤範例：

```text
Container not found: Demo-Container
```

原因：

SmartAction 裡設定的 `containerName` 找不到對應 Firefox Container。

請檢查：

- Firefox 是否有建立該 Container
- 名稱是否完全一致
- 大小寫是否一致
- 是否有多餘空格

---

## No permission for cookieStoreId

錯誤範例：

```text
No permission for cookieStoreId: firefox-container-6
```

原因：

Firefox Helper Extension 缺少 `cookies` 權限。

請檢查：

```text
extensions/firefox-helper/manifest.json
```

permissions 應包含：

```json
[
  "tabs",
  "cookies",
  "contextualIdentities",
  "nativeMessaging"
]
```

修改後請到 Firefox：

```text
about:debugging#/runtime/this-firefox
```

重新 Reload Extension。

---

## Firefox Helper Extension 沒有回應

可能原因：

- Extension 沒有安裝
- Extension 沒有 Reload
- Native Messaging Host 沒有安裝
- Firefox 沒有啟動
- Helper 溝通檔案異常

建議檢查：

```text
%APPDATA%/SmartAction/firefox_helper/
```

常見檔案：

```text
pending_launch.json
last_result.json
helper.log
```

可以查看 `helper.log` 了解錯誤原因。

---

## Import JSON 失敗

可能原因：

- JSON 格式錯誤
- 檔案內容不完整
- 匯入了不支援的設定格式
- 檔案不是 SmartAction Profile

建議處理：

1. 用文字編輯器打開 JSON
2. 確認 JSON 沒有被截斷
3. 確認括號、逗號格式正確
4. 確認是 SmartAction 匯出的 Profile

---

## 文字顏色看不清楚

可能原因：

- 深色 / 淺色主題樣式衝突
- QMessageBox 或彈窗繼承錯誤樣式
- 按鈕文字顏色沒有設定

建議處理：

- 切換 Theme 測試
- 重新啟動 SmartAction
- 回報問題時附上截圖

---

## PowerShell Action 沒有執行

可能原因：

- 指令錯誤
- 權限不足
- Execution Policy 限制
- 需要系統管理員權限
- PowerShell 路徑錯誤

建議先手動在 PowerShell 執行同一段指令，確認指令本身可用。

---

## Start with Windows 沒有效果

可能原因：

- 沒有按 Save
- 開機啟動註冊失敗
- 防毒或系統政策阻擋
- exe 位置被移動

建議處理：

1. 勾選 Start with Windows
2. 按 Save
3. 重新開啟 SmartAction 確認設定仍存在
4. 測試重新登入 Windows

---

## 回報問題時請提供

如果要回報 Bug，請盡量提供：

- SmartAction 版本
- 是否使用 exe
- Windows 版本
- 錯誤截圖
- 重現步驟
- 是否使用 Firefox Helper
- 是否使用 Client Workspace
- 錯誤訊息
- helper.log 內容
