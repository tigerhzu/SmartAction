# Firefox Container Helper

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
