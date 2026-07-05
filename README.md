# SmartAction

SmartAction is a lightweight universal actions ring for IT maintenance, workspace launching, shortcuts, and automation.

SmartAction 是一個輕量級的萬用快捷輪盤工具，適合 IT 維運、客戶工作區啟動、PowerShell 腳本、網址捷徑與日常自動化操作。

---

## Features / 功能

- Universal Actions Ring / 萬用快捷輪盤
- Global Hotkey / 全域快捷鍵
- Custom Actions / 自訂動作
- PowerShell / App / URL actions
- Client Workspace / 客戶工作區
- Firefox Container Helper
- Profile Import / Export
- Theme Selection
- Start with Windows

---

## Documentation / 文件

- [Client Workspace / 客戶工作區](docs/client-workspace.md)
- [Firefox Container Helper](docs/firefox-container-helper.md)
- [Action Types / 動作類型](docs/action-types.md)
- [Profile Import / Export / 設定檔匯入匯出](docs/profile-import-export.md)
- [Troubleshooting / 常見問題](docs/troubleshooting.md)
- [Build and Release / 打包與發布](docs/build-and-release.md)

---

## Client Workspace

Client Workspace 用來管理不同客戶的維運網址。

你可以為每個客戶設定：

- 客戶名稱
- Firefox Container
- Firefox Profile
- 維運網址清單

按下 Launch Workspace 後，SmartAction 會自動開啟 Firefox，並打開該客戶所有維運網站。

---

## Firefox Container Helper

如果你需要讓不同客戶的登入狀態互相隔離，可以搭配 Firefox Container Helper 使用。

用途：

- 客戶 A 使用 Container A
- 客戶 B 使用 Container B
- 避免 Microsoft 365、Azure、Firewall、NAS 等管理後台登入狀態混在一起

---

## Safety Notice / 安全提醒

請不要把以下資訊公開上傳到 GitHub：

- 密碼
- API Key
- VPN 資訊
- 客戶機敏資料
- 完整內網架構
- 重要客戶管理後台網址

分享 Profile JSON 前，請先檢查是否包含客戶名稱、內網 IP、管理後台網址或其他敏感資訊。

---

## About SmartAction

Brand: Tiger

SmartAction is designed for IT maintenance workflows where engineers need fast access to customer portals, admin tools, scripts, and workspace shortcuts.
