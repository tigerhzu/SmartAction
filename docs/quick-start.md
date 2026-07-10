# SmartAction Quick Start / 快速教學

## 1. 設定 Global Hotkey

打開 Settings，在上方 `Global hotkey` 欄位輸入快捷鍵，例如：

```text
Alt+Space
```

按下 `Save` 後，快捷鍵會套用到背景執行中的 SmartAction。

## 2. 新增 Action

在 Settings 左側按 `+ Add Action`，右側會出現 Action 設定表單。

常用欄位：

- Label：輪盤上顯示的名稱。
- Short Label：短文字標籤。
- Icon：emoji 或簡短符號。
- Type：Action 類型。
- Target：URL、檔案路徑、資料夾路徑、指令或其他目標。

## 3. 選擇 Action Type

可依照用途選擇：

- URL：開啟網站。
- App / File：開啟程式或檔案。
- Folder：開啟資料夾。
- Command：執行一般命令。
- PowerShell：執行 PowerShell 指令。
- PowerShell Library：執行 Library 裡管理的 PowerShell 腳本。
- Environment Check：一鍵檢查 Windows、網路、DNS、Firewall 等資訊。
- Client Workspace：開啟指定客戶的維運工作區。

## 4. 儲存 Settings

修改完成後按右下角 `Save`。如果按 `Cancel`，本次修改不會寫入設定。

## 5. 使用輪盤

SmartAction 在背景執行時，按下 Global Hotkey 叫出輪盤。

點擊輪盤上的 Action 後會執行對應動作。Folder 類型可以包含子 Action。

## 6. 使用 Client Workspace

在 Settings 新增一個 Action，Type 選擇 `Client Workspace`，儲存後即可掛到輪盤。

打開 Client Workspace 管理視窗後，可以建立客戶、加入維運網址，按 `Launch Workspace` 用 Firefox 一次打開所有網址。

若設定 `containerName`，SmartAction 會嘗試透過 Container Helper Extension 使用指定 Firefox Container 開啟。

更多細節請看：

```text
docs/client-workspace.md
docs/firefox-container-helper.md
```

## 7. 匯入 / 匯出 Profile

Settings 裡的 `Profile` 區塊提供：

- Export Profile：匯出目前 actions、hotkey、theme、PowerShell Library、Client Workspace 等設定。
- Import Profile：匯入別人的 SmartAction profile，匯入前會先備份目前設定。

匯入後建議重新載入設定或重新啟動 SmartAction。

