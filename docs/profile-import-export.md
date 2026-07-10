# Profile Import / Export / 設定檔匯入匯出

SmartAction 支援 Profile 匯入與匯出，用來備份設定或分享設定檔給其他人。

---

## Export Profile 是什麼

Export Profile 可以把目前 SmartAction 的設定匯出成 JSON 檔案。

適合用在：

- 備份自己的 SmartAction 設定
- 換電腦時搬移設定
- 分享常用 Action 給朋友或同事
- 建立不同工作情境的設定檔

---

## Import Profile 是什麼

Import Profile 可以匯入別人提供的 JSON 設定檔，或還原自己之前備份的設定。

匯入後，SmartAction 會讀取 JSON 裡面的設定並套用。

---

## 可能包含的內容

Profile 可能包含：

- Global Hotkey
- Theme
- Actions
- URL Actions
- App Actions
- PowerShell Actions
- Client Workspace 設定
- Client Workspace URL 清單

實際內容依目前版本支援的功能為準。

---

## Client Workspace 設定

Client Workspace 可能包含以下欄位：

```json
{
  "id": "demo-client",
  "name": "Demo 客戶",
  "containerName": "Demo-Container",
  "firefoxProfile": "default-release",
  "urls": [
    {
      "name": "Microsoft 365 Admin",
      "url": "https://admin.microsoft.com"
    },
    {
      "name": "Azure Portal",
      "url": "https://portal.azure.com"
    }
  ]
}
```

---

## 匯出設定檔

1. 開啟 SmartAction Settings
2. 點選 `Export Profile`
3. 選擇儲存位置
4. 儲存 JSON 檔案

建議檔名：

```text
smartaction-profile.json
```

或依用途命名：

```text
smartaction-it-maintenance-profile.json
```

---

## 匯入設定檔

1. 開啟 SmartAction Settings
2. 點選 `Import Profile`
3. 選擇 JSON 設定檔
4. 確認匯入
5. 檢查 Actions 是否正常出現
6. 按 Save 儲存

---

## 安全提醒

分享 Profile JSON 前，請務必檢查內容。

不要公開分享包含以下資訊的設定檔：

- 密碼
- API Key
- Token
- VPN 資訊
- 客戶名稱
- 客戶內網 IP
- 客戶管理後台網址
- 防火牆管理網址
- NAS 管理網址
- 遠端桌面入口
- 其他機敏維運資訊

---

## 建議做法

如果要分享給別人，建議先做一份乾淨範例：

```text
Demo 客戶
Test Container
https://example.com
```

避免直接分享真實客戶資料。

---

## 匯入失敗怎麼辦

如果匯入失敗，請檢查：

- JSON 格式是否正確
- 檔案是否被截斷
- 是否選錯檔案
- 是否有不支援的欄位
- SmartAction 版本是否太舊

如果仍然失敗，可以先用文字編輯器打開 JSON 檔案，確認內容是否完整。
