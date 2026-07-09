# Firefox Container Helper
<img width="723" height="306" alt="image" src="https://github.com/user-attachments/assets/c56adbd3-ea32-4b11-885c-dd364556a08d" />

Firefox Container Helper 是 SmartAction 的 Firefox 容器輔助功能。

它可以讓 Client Workspace 依照不同客戶，使用不同 Firefox Container 開啟維運網站，避免不同客戶的登入狀態混在一起。

---

## 功能用途

如果你同時維護多個客戶，常會遇到這種情況：

- A 客戶有 Microsoft 365 Admin
- B 客戶也有 Microsoft 365 Admin
- C 客戶也有 Azure Portal

這些網站網址可能都一樣，但登入帳號不同。

如果全部開在一般 Firefox 分頁，Cookie 和登入狀態容易混在一起。

Firefox Container Helper 可以讓：

```text
A 客戶 → A Container
B 客戶 → B Container
C 客戶 → C Container
```

這樣每個客戶的登入狀態會分開保存。

---

## 架構說明

Firefox Container Helper 由兩個部分組成：

```text
SmartAction App
→ Native Messaging Host
→ Firefox Helper Extension
→ Firefox Container
```

### Firefox Helper Extension

負責在 Firefox 裡建立指定 Container 分頁。

### Native Messaging Host

負責讓 SmartAction App 和 Firefox Extension 溝通。

---

## 安裝 Firefox Helper Extension

1. 打開 Firefox
2. 在網址列輸入：

```text
about:debugging#/runtime/this-firefox
```

3. 點選：

```text
Load Temporary Add-on
```

4. 選擇：

```text
extensions/firefox-helper/manifest.json
```

5. 確認 SmartAction Firefox Helper 已出現在 Extension 清單中

---

## 安裝 Native Messaging Host

在 SmartAction 專案資料夾中執行：

```powershell
python native/firefox_helper_host/install_host_windows.py
```

安裝後會建立或使用以下資料夾：

```text
%APPDATA%/SmartAction/firefox_helper/
```

常見檔案：

```text
pending_launch.json
last_result.json
helper.log
```

---

## 建立 Firefox Container

1. 打開 Firefox
2. 開啟 Firefox Multi-Account Containers
3. 建立一個新的 Container
4. 名稱要和 SmartAction 裡的 `containerName` 完全一致

例如 SmartAction 裡設定：

```text
Demo-Container
```

Firefox Container 也要叫：

```text
Demo-Container
```

---

## SmartAction 裡要怎麼設定

在 Client Workspace 裡：

```text
Container:
Demo-Container
```

如果 `containerName` 是空白：

```text
SmartAction 會使用一般 Firefox 分頁開啟網址。
```

如果 `containerName` 有值：

```text
SmartAction 會透過 Firefox Helper Extension，在指定 Container 裡開啟網址。
```

---

## 常見錯誤

### No permission for cookieStoreId

錯誤範例：

```text
No permission for cookieStoreId: firefox-container-6
```

原因：

Firefox Helper Extension 缺少 `cookies` 權限。

請確認：

```text
extensions/firefox-helper/manifest.json
```

裡面的 permissions 包含：

```json
[
  "tabs",
  "cookies",
  "contextualIdentities",
  "nativeMessaging"
]
```

修改後請到：

```text
about:debugging#/runtime/this-firefox
```

重新 Reload Extension。

---

### Container not found

錯誤範例：

```text
Container not found: Demo-Container
```

原因：

SmartAction 裡的 `containerName` 找不到對應的 Firefox Container。

請檢查：

- Firefox 是否有建立該 Container
- Container 名稱是否完全一致
- 大小寫是否一致
- 是否有多餘空格

---

### Firefox Helper Extension 沒有回應

可能原因：

- Extension 沒有安裝
- Extension 沒有 Reload
- Native Messaging Host 沒有安裝
- Firefox 沒有正確啟動

建議檢查：

```text
%APPDATA%/SmartAction/firefox_helper/helper.log
```

---

### Firefox 找不到

可能原因：

- 電腦沒有安裝 Firefox
- Firefox 沒有加入系統路徑
- SmartAction 找不到 firefox.exe

請先確認 Firefox 可以正常手動開啟。

---

## 注意事項

Firefox Temporary Add-on 在 Firefox 重開後可能會消失。

正式使用時，建議之後改成正式 Extension 安裝方式。

SmartAction 不會保存密碼。

登入狀態由 Firefox Container 自己保存。
