# Client Workspace / 客戶工作區
<img width="1300" height="790" alt="image" src="https://github.com/user-attachments/assets/22a3b9e2-aa64-4f21-9334-3636738c57be" />

Client Workspace 是 SmartAction 的客戶維運工作區功能。

它可以讓你針對不同客戶建立不同的維運網址清單，並一鍵開啟所有網站。

---

## 適合情境

例如你有不同客戶：

- A 客戶
- B 客戶
- C 客戶

每個客戶都可能有自己的：

- Microsoft 365 Admin Center
- Azure Portal
- Firewall 管理頁
- NAS 管理頁
- UniFi Controller
- HaloPSA 工單系統
- Remote Desktop Gateway

使用 Client Workspace 後，你可以點選客戶，然後一次打開所有相關網址。

---

## 客戶欄位說明

每個客戶包含：

- `id`
- `name`
- `containerName`
- `firefoxProfile`
- `urls`

---

## containerName

`containerName` 是 Firefox Container 的名稱。

如果 `containerName` 是空白：

```text
SmartAction 會使用一般 Firefox 分頁開啟網址。
