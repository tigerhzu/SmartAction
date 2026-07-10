# Action Types / 動作類型
<img width="963" height="808" alt="image" src="https://github.com/user-attachments/assets/5478b78d-7d1d-4165-b09d-5bc653495597" />


SmartAction 透過 Action Type 決定每個輪盤按鈕要執行什麼動作。

---

## URL Action

用來開啟指定網址。

適合：

- 常用網站
- 管理後台
- 文件連結
- Web 工具

範例：

```text
https://admin.microsoft.com
https://portal.azure.com
https://github.com
```

---

## App Action

用來開啟本機應用程式。

適合：

- 工作管理員
- PowerShell
- CMD
- Windows Terminal
- 自訂工具
- exe 程式

範例：

```text
C:\Windows\System32\Taskmgr.exe
C:\Windows\System32\cmd.exe
```

---

## PowerShell Action

用來執行 PowerShell 指令或腳本。

適合：

- 一鍵查詢系統資訊
- 一鍵開啟工具
- 一鍵執行維護指令
- IT 現場快速處理

範例：

```powershell
Start-Process taskmgr
```

注意：

請不要執行不熟悉或不可信任的 PowerShell 指令。

---

## Client Workspace Action

Action Type：

```text
client_workspace
```

用來開啟 Client Workspace 視窗。

Client Workspace 可以管理不同客戶的維運網址，並一鍵開啟該客戶所有網站。

適合：

- IT 維運
- MSP 客戶管理
- 多客戶入口網站
- Firefox Container 分流登入

---

## Environment Check Action

用來快速檢查目前電腦環境。

可能包含：

- Windows 版本
- 目前登入使用者
- 電腦名稱
- 是否為系統管理員權限
- IP 資訊
- DNS 資訊
- 網路連線狀態

適合 IT 現場維護前快速確認環境。

---

## 注意事項

不同 Action Type 可能需要不同欄位。

如果 Action 執行失敗，請先檢查：

- 路徑是否正確
- URL 是否正確
- PowerShell 指令是否可手動執行
- 權限是否足夠
- 是否需要系統管理員權限
