# Client Workspace / 客戶工作區

Client Workspace 用來管理不同客戶的維運網址。每個客戶可以保存 Firefox Profile、Container 名稱與多個網址，並從輪盤一次開啟完整工作區。

## 資料夾與排序

- 按 `New Folder` 建立分類，例如依工程師、區域或專案分類。
- 客戶可以直接拖曳到其他資料夾。
- 同一資料夾內可上下拖曳調整客戶順序，變更會立即寫入 JSON。
- 新增或編輯客戶時，也可以從 `Folder` 欄位指定分類。
- 刪除資料夾不會刪除客戶；其中的客戶會移到 `Unassigned`。

舊版 1.0 資料會自動相容，原有客戶會先顯示在 `Unassigned`。

## 資料格式

Client Workspace 1.1 使用 `folders` 保存分類順序，客戶以 `folderId` 指向所屬資料夾：

```json
{
  "version": "1.1",
  "folders": [
    {
      "id": "engineer-a",
      "name": "工程師 A"
    }
  ],
  "clients": [
    {
      "id": "abc-company",
      "name": "ABC 客戶",
      "folderId": "engineer-a",
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

## Firefox 與 Container

未設定 `containerName` 時，SmartAction 會使用指定的 Firefox Profile 開啟客戶網址。設定 Container 後，則透過 Container Helper Extension 在指定的 Firefox Container 內開啟。

詳細設定請參考 `docs/firefox-container-helper.md`。

## 匯入、匯出與備份

Client Workspace 支援 JSON 匯入與匯出，主要資料位於：

```text
data/client_workspaces.json
```

匯入會先建立備份：

```text
client_workspaces.backup.YYYYMMDD-HHMMSS.json
```

匯入 1.0 或 1.1 格式皆可；匯出一律使用 1.1 格式。

## 常見問題

- 客戶沒有網址：`Launch Workspace` 會保持停用。
- 網址無法開啟：確認網址以 `http://` 或 `https://` 開頭。
- Firefox 找不到：確認 Firefox 已安裝，或 `firefox.exe` 已加入 PATH。
- Container 無法使用：在 Client Workspace 執行 `Check Helper` 或 `Repair Setup`。
