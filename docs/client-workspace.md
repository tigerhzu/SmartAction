# Client Workspace / 客戶工作區

Client Workspace 用來管理不同客戶的維運網址。你可以為每個客戶建立一組 URL，從輪盤或 Client Workspace 視窗一次開啟。

## 資料欄位

每個客戶包含：

- id
- name
- containerName
- firefoxProfile
- urls

每個 URL 包含：

- name
- url

範例：

```json
{
  "version": "1.0",
  "clients": [
    {
      "id": "abc-company",
      "name": "ABC 客戶",
      "containerName": "ABC-Maintenance",
      "firefoxProfile": "SmartAction-ClientWorkspace",
      "urls": [
        {
          "name": "Microsoft 365 Admin",
          "url": "https://admin.microsoft.com"
        }
      ]
    }
  ]
}
```

## 一般 Firefox 分頁

如果 `containerName` 是空白，SmartAction 會使用一般 Firefox 分頁開啟客戶所有 URL。

## Firefox Container

如果 `containerName` 有值，SmartAction 會使用 Container Helper Extension，嘗試在指定 Container 中開啟 URL。

Container 名稱必須和 Firefox 裡建立的 Container 完全一致。

## 輪盤 Action Type

在 Settings 新增 Action 時，Type 選擇：

```text
Client Workspace
```

儲存後，輪盤點擊該 Action 會進入或啟動 Client Workspace 流程。

## 匯入 / 匯出

Client Workspace 支援 JSON 匯入與匯出。匯入前會備份目前的設定檔：

```text
data/client_workspaces.json
```

備份檔案格式：

```text
client_workspaces.backup.YYYYMMDD-HHMMSS.json
```

## 常見問題

### 沒有 URL

如果客戶沒有任何 URL，SmartAction 會提示並停止啟動。

### URL 格式不完整

建議 URL 使用：

```text
https://example.com
```

如果缺少 `http://` 或 `https://`，SmartAction 會提示你確認格式。

### 找不到 Firefox

請確認 Firefox 已安裝，或 `firefox.exe` 已加入 PATH。

### Container 無法開啟

請確認 Container Helper Extension、Native Messaging Host 與 Firefox Container 都已設定完成。

更多細節請看：

```text
docs/firefox-container-helper.md
```

