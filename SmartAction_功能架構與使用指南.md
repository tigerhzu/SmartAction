# SmartAction 功能架構與使用指南

這份文件用產品使用角度整理 SmartAction 目前可以做什麼、每種功能 Type 適合用在哪裡，以及使用者在新增快捷功能時應該如何選擇。

SmartAction 不是單純的「開 App 工具」。它比較像一個可自訂的 IT 工作台：你可以把網站、程式、PowerShell 指令、客戶維運環境、環境檢查、常用文字與表單工具整理成快捷輪盤，用一個熱鍵快速叫出來。

---

## 1. SmartAction 是什麼

SmartAction 是一個給 IT 維護人員、工程師、客服支援人員與重度電腦使用者使用的快捷工具。

它可以透過：

- 全域熱鍵
- 快捷輪盤
- 自訂按鈕
- PowerShell / Command 指令
- 客戶工作區
- Firefox Container
- 匯入 / 匯出設定檔

把日常重複操作整理成「一鍵執行」。

核心價值：

- 減少重複點擊，不用每天到處找常用工具。
- 快速開啟常用 App、網站、資料夾、檔案。
- 快速執行 PowerShell / 系統維護指令。
- 把不同客戶的維運網站整理成 Client Workspace。
- 每個按鈕都可以自訂名稱、圖示、動作與分類。
- 可匯入 / 匯出設定，方便備份或分享給同事。
- 可打包成 exe 與 release package，降低部署門檻。

適合族群：

- MSP / IT 外包維護人員
- Helpdesk / 客服支援工程師
- 系統管理員
- 需要常常開啟多個管理平台的人
- 想把日常工作流程整理成快捷系統的人

---

## 2. 整體功能架構圖

```text
SmartAction
├─ 快捷輪盤
│  ├─ 常用 App / File
│  ├─ 常用網站 URL
│  ├─ 資料夾 / 多層子選單
│  ├─ PowerShell 指令
│  ├─ PowerShell Library 腳本
│  ├─ Environment Check
│  ├─ Client Workspace
│  ├─ Paste / Form 快速貼上
│  └─ PS Form IT 維護表單
│
├─ 功能 Type 系統
│  ├─ Folder
│  ├─ URL
│  ├─ App / File
│  ├─ Command
│  ├─ PowerShell
│  ├─ PowerShell Library
│  ├─ Environment Check
│  ├─ Client Workspace
│  ├─ Paste
│  ├─ Form
│  └─ PS Form
│
├─ IT 工具箱
│  ├─ Network 腳本
│  ├─ System 腳本
│  ├─ User Management 腳本
│  ├─ Domain / AD 腳本
│  ├─ Repair Tools 腳本
│  └─ 自訂 PowerShell 腳本
│
├─ 設定系統
│  ├─ Actions 設定
│  ├─ Theme 設定
│  ├─ Hotkey Picker
│  ├─ Icon / Emoji Picker
│  ├─ Profile Import
│  └─ Profile Export
│
├─ Help / 文件
│  ├─ Quick Start
│  ├─ Full Documentation
│  ├─ GitHub Repository
│  ├─ Report Issue
│  └─ About SmartAction
│
├─ Firefox Client Workspace
│  ├─ 客戶清單
│  ├─ 客戶 URL 清單
│  ├─ Firefox Profile
│  ├─ Firefox Container Name
│  ├─ SmartAction Container Helper
│  └─ Native Messaging Host
│
└─ 發佈版本
   ├─ 開發版：python -m app.main
   ├─ PyInstaller exe：dist/UniversalActionsRing/
   └─ 同事安裝包：dist/SmartAction-Release/
```

---

## 3. Type 功能總覽

以下是目前專案中實際存在、可作為輪盤 action 的主要 Type。

| Type 名稱 | 功能用途 | 適合情境 | 使用者需要填什麼 | 範例 |
| --- | --- | --- | --- | --- |
| Folder | 建立輪盤資料夾 / 子選單 | 把同類功能分組 | 名稱、Icon、子項目 | AI、PowerShell、客戶工具 |
| URL | 使用預設瀏覽器開啟網站 | 常用後台、雲端平台、監控平台 | 網址 | Microsoft Admin、Azure Portal、GitHub |
| App / File | 開啟本機程式、檔案或資料夾 | 常用軟體、文件、工具資料夾 | 本機路徑 | Task Manager、AnyDesk、工具資料夾 |
| Command | 執行 shell / cmd 指令 | 背景命令、快速啟動、批次操作 | Command 字串 | `explorer C:\Tools`、`ping 8.8.8.8` |
| PowerShell | 執行 PowerShell 指令 | IT 維護、系統查詢、開管理工具 | PowerShell 指令 | `Get-Process`、`Start-Process taskmgr` |
| PowerShell Library | 執行 Library 裡已儲存的腳本 | 常用 IT 腳本、可參數化腳本、危險腳本確認 | 選擇 Script | Ping Target、Create Local User、Join Domain |
| Environment Check | 一鍵檢查電腦環境 | 接手客戶電腦、遠端支援前快速盤點 | 通常不用填 | Windows 版本、IP、DNS、防火牆狀態 |
| Client Workspace | 開啟客戶工作區管理視窗 | MSP / 多客戶維運 | 通常不用 target，進視窗選客戶 | 一鍵開啟客戶所有維運網站 |
| Paste | 把固定文字貼到目前視窗 | 常用回覆、常用片語、命令片段 | 要貼上的文字 | 工單回覆模板、常用 email 片段 |
| Form | 跳出簡單輸入框，輸入後貼上 | 需要每次輸入一個值的貼上流程 | 表單 title / label / default | 輸入客戶代號後貼到系統 |
| PS Form | 開啟多欄位 PowerShell 表單 | IT 維護表單化操作 | Form ID | `add_local_user`、`join_domain` |

目前狀態：

- 已完成：Folder、URL、App / File、Command、PowerShell、PowerShell Library、Environment Check、Client Workspace、Paste、Form、PS Form。
- 需注意：Client Workspace 的 Firefox Container 功能需要安裝 SmartAction Container Helper extension 與 Native Messaging Host。
- 需確認：Command / PowerShell 類型可以執行高影響操作，分享設定前要確認內容安全。

---

## 4. 每個 Type 的詳細說明

### Type：Folder

Folder 用來建立輪盤上的分類或子選單。它不直接執行動作，而是把多個 action 收在同一個資料夾裡。

常見用途：

- 把 AI 工具放在一起。
- 把客戶網站放在一起。
- 把 PowerShell 維護工具放在一起。
- 把系統工具、瀏覽器、文件分組。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示在輪盤上的分類名稱 |
| Icon / Emoji | 顯示在輪盤 bubble 上的圖示 |
| 子項目 | Folder 裡面的 actions |
| Enabled | 是否顯示 |

適合情境：

- 功能變多時保持輪盤乾淨。
- 想依照工作流程分類，例如「客戶維運」、「系統工具」、「常用網站」。

注意事項：

- Folder 本身不執行 target。
- 如果 action 有 `sub_actions`，系統會把它視為資料夾類項目。

---

### Type：URL

URL Type 用來開啟網站，會使用系統預設瀏覽器。

常見用途：

- 管理後台
- SaaS 工具
- 雲端平台
- 監控平台
- 文件網站
- 客戶系統

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示在輪盤上的名稱 |
| URL / Target | 要開啟的網址 |
| Icon / Emoji | 例如地球、雲、文件、品牌 icon |
| Enabled | 是否顯示 |

範例：

- `https://admin.microsoft.com`
- `https://portal.azure.com`
- `https://github.com/tigerhzu/SmartAction`
- `https://www.youtube.com/`

適合情境：

- 每天都會打開固定網站。
- 支援人員需要快速進入多個後台。
- 想把常用 URL 從瀏覽器書籤移到工作流程裡。

注意事項：

- URL 建議填完整 `https://` 或 `http://`。
- 如果要依客戶一次開多個網站，建議使用 Client Workspace。

---

### Type：App / File

App / File Type 用來開啟本機程式、檔案或資料夾。Windows 上會使用系統 shell，也就是類似你在檔案總管雙擊該檔案。

常見用途：

- 開啟常用 exe。
- 開啟文件、PDF、Excel。
- 開啟工具資料夾。
- 開啟 Windows 系統工具。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Path / Target | exe、檔案或資料夾路徑 |
| Icon / Emoji | 顯示圖示 |
| Enabled | 是否顯示 |

範例：

- `C:\Windows\System32\Taskmgr.exe`
- `C:\Tools`
- `C:\Users\Public\Desktop\AnyDesk.exe`
- `C:\Docs\維護SOP.pdf`

適合情境：

- 想快速開常用桌面工具。
- 想把工具資料夾變成一鍵入口。
- 給同事分享內部工具 launcher。

注意事項：

- 匯出 profile 給別人時，本機路徑可能在對方電腦不存在。
- 如果是命令列工具且需要參數，Command 或 PowerShell 可能更適合。

---

### Type：Command

Command Type 用來執行 shell / cmd 指令。它適合簡單、背景式、不需要完整結果視窗的命令。

常見用途：

- 開啟系統工具。
- 執行簡單 command。
- 呼叫 batch file。
- 開啟資料夾或系統位置。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Command / Target | 要執行的 command 字串 |
| Icon / Emoji | 顯示圖示 |
| Enabled | 是否顯示 |

範例：

```bat
explorer C:\Tools
ping -n 4 8.8.8.8
notepad.exe
```

適合情境：

- 簡單命令。
- 不需要參數表單。
- 不需要把 stdout / stderr 顯示給使用者。

注意事項：

- Command 不會像 PowerShell Library 那樣顯示完整結果視窗。
- 如果需要權限、參數、風險確認、結果輸出，建議改用 PowerShell Library。

---

### Type：PowerShell

PowerShell Type 用來執行 Windows PowerShell 指令，適合 IT 維護人員把常用指令變成一鍵按鈕。

常見用途：

- 開啟工作管理員。
- 查詢 IP 設定。
- 開啟 Windows 管理工具。
- 重啟服務。
- 執行維護腳本。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示在輪盤上的名稱 |
| PowerShell 指令 | 實際要執行的 PowerShell command |
| Icon / Emoji | 顯示圖示 |
| Enabled | 是否顯示 |

範例：

```powershell
Start-Process taskmgr
Get-Process
ipconfig /all
Start-Process services.msc
```

適合情境：

- 客戶電腦維護。
- 重複性 IT 指令。
- 快速開啟系統工具。

注意事項：

- 目前一般 PowerShell Type 會開一個可互動的 PowerShell 視窗。
- 危險指令請確認後再加入。
- 若需要參數輸入、dangerous 確認、結果視窗，建議使用 PowerShell Library。

---

### Type：PowerShell Library

PowerShell Library Type 會執行 `data/powershell_library.json` 裡已儲存的腳本。輪盤 action 只儲存 `script_id`，不會把整段 script 複製到輪盤設定。

這代表你可以集中管理腳本，輪盤只是指向某個腳本。

常見用途：

- 常用 IT 工具箱。
- 需要參數的 PowerShell 腳本。
- 需要 dangerous 確認的系統修改腳本。
- 需要顯示 stdout / stderr / exit code 的維護指令。

PowerShell Library 目前分類：

- System
- Network
- User Management
- Domain / AD
- Repair Tools
- Custom

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| Script | 從 PowerShell Library 選擇腳本 |
| Display Name | 可自動帶入 script name，也可自行修改 |
| Icon / Emoji | 顯示圖示 |
| script_id | 儲存在設定檔中的穩定識別 |

Library script 本身可設定：

| Script 欄位 | 說明 |
| --- | --- |
| id | 腳本唯一識別，改名也不影響輪盤 |
| name | 腳本名稱 |
| description | 說明 |
| category | 分類 |
| script_content | PowerShell 內容 |
| need_admin | 是否建議系統管理員權限 |
| risk_level | `safe` 或 `dangerous` |
| parameters | 參數欄位，例如 text / password |

目前內建範例：

- IP Configuration
- Ping Google DNS
- Ping Target
- Current User
- Hostname
- Open Task Manager
- Open Services
- Create Local User
- Add Local User to Administrators
- Check Domain Status
- Join Domain
- Rename Computer
- Flush DNS
- Renew IP
- System File Checker
- DISM Restore Health

適合情境：

- 想做一套給 IT 團隊共用的腳本庫。
- 腳本需要參數，例如 `ping {{Target}}`。
- 腳本可能修改系統，需要執行前確認。

注意事項：

- `risk_level = dangerous` 的腳本執行前一定會跳確認。
- password 參數會遮蔽，不會在確認視窗或結果視窗顯示明文。
- 分享 profile 前請確認腳本不含密碼、token、客戶機密。

---

### Type：Environment Check

Environment Check 是一鍵環境檢查工具。它會收集目前電腦的基本系統與網路狀態，並顯示可複製的結果。

檢查項目：

- Windows 版本
- 目前登入使用者
- 是否以系統管理員權限執行
- 電腦名稱
- 是否加入網域
- IP address
- Gateway
- DNS servers
- 是否能 ping gateway
- 是否能解析 DNS
- PowerShell Execution Policy
- 防火牆狀態

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Icon / Emoji | 顯示圖示 |
| Target | 不需要 |

適合情境：

- 接手客戶電腦前快速盤點。
- 遠端支援時先確認基本狀態。
- 把結果貼到工單或交給同事。

注意事項：

- Environment Check 是查詢資訊，不會修改系統。
- 若某項檢查失敗，會顯示 Unknown / Failed，不會讓整個 App 閃退。

---

### Type：Client Workspace (搭配 FireFox Cpntainer 使用)

Client Workspace 用來管理不同客戶的維運工作區。你可以為每個客戶設定多個維運網站，啟動時一次開啟。

每個客戶包含：

- id
- name
- containerName
- firefoxProfile
- urls

每個 URL 包含：

- name
- url

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 輪盤上的入口名稱，例如「客戶維運」 |
| Icon / Emoji | 顯示圖示 |
| Target | 通常不需要 |

Client Workspace 視窗內可設定：

| 設定項目 | 說明 |
| --- | --- |
| 客戶名稱 | 客戶顯示名稱 |
| Container Name | Firefox Container 名稱 |
| Firefox Profile | 使用哪個 Firefox profile |
| URL 清單 | 該客戶需要開啟的維運網站 |

特色：

- 可依客戶分類。
- 可設定多個管理網站。
- 可匯入 / 匯出 JSON。
- 可搭配 Firefox Multi-Account Containers。
- 可透過 SmartAction Container Helper 在指定 Container 開頁面。

適合情境：

- MSP 每天切換不同客戶。
- 客服工程師需要同時打開客戶 M365、Azure、監控、Firewall、NAS 後台。
- 想避免不同客戶登入狀態混在一起。

注意事項：

- 若 `containerName` 空白，會用一般 Firefox 分頁開啟。
- 若設定 `containerName`，需要安裝 SmartAction Container Helper 與 Native Messaging Host。
- 找不到 Container 時，不會自動開在一般分頁，避免登入錯客戶環境。

---

### Type：Paste

Paste Type 用來把固定文字寫入剪貼簿，然後模擬 Ctrl + V 貼到目前視窗。

常見用途：

- 工單回覆模板。
- 常用客服語句。
- 常用 command 片段。
- email 片段。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Text / Target | 要貼上的固定文字 |
| Icon / Emoji | 顯示圖示 |

範例：

```text
您好，已收到您的問題，我們正在協助確認。
```

適合情境：

- 常常重複打同一段文字。
- 需要快速貼到 Teams、Email、工單系統。

注意事項：

- Paste 會改變目前剪貼簿內容。
- 不建議放密碼或 token。

---

### Type：Form

Form Type 會跳出一個簡單輸入框，使用者輸入內容後，SmartAction 會把結果貼到目前視窗。

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Form JSON / Target | 可用 JSON 設定 title、label、default |
| Icon / Emoji | 顯示圖示 |

Target 可用 JSON：

```json
{
  "title": "Customer Code",
  "label": "Enter customer code:",
  "default": ""
}
```

適合情境：

- 每次都要輸入不同值，但貼上格式固定。
- 快速輸入客戶代號、工單號、主機名稱。

注意事項：

- Form 是單欄位輸入。
- 如果需要多欄位並執行 PowerShell，請用 PS Form 或 PowerShell Library parameters。

---

### Type：PS Form

PS Form 是多欄位 PowerShell 表單工具。它會開啟一個客製表單，填完後執行對應 PowerShell script。

目前已註冊 Form：

- `add_local_user`
- `join_domain`

可設定項目：

| 設定項目 | 說明 |
| --- | --- |
| 名稱 | 顯示名稱 |
| Form ID / Target | 例如 `add_local_user` 或 `join_domain` |
| Icon / Emoji | 顯示圖示 |

適合情境：

- 建立本機使用者。
- 加入網域。
- 把 IT 維護操作做成表單，降低輸入錯誤。

注意事項：

- 這類操作通常可能需要系統管理員權限。
- 涉及帳號、密碼、網域資訊時，請注意資料保護。
- 如果是通用腳本，未來也可以考慮改成 PowerShell Library + parameters。

---

## 5. 使用者該怎麼選 Type

| 我想做的事 | 建議 Type |
| --- | --- |
| 開啟一個網站 | URL |
| 開啟本機程式 | App / File |
| 開啟本機檔案 | App / File |
| 開啟資料夾 | App / File 或 Command |
| 執行簡單 cmd 指令 | Command |
| 執行 PowerShell 指令 | PowerShell |
| 執行有參數、有結果、有風險確認的 PowerShell 腳本 | PowerShell Library |
| 把多個功能收在同一組 | Folder |
| 一鍵檢查電腦環境 | Environment Check |
| 幫客戶一次開多個維運網站 | Client Workspace |
| 用 Firefox Container 分隔客戶登入狀態 | Client Workspace |
| 建立本機帳號 | PS Form 或 PowerShell Library |
| 加入網域 | PS Form 或 PowerShell Library |
| 查 Domain / AD 狀態 | PowerShell Library |
| 快速貼上固定文字 | Paste |
| 先輸入一個值，再貼上 | Form |
| 想做一套可分享給同事的 IT 腳本庫 | PowerShell Library |
| 不確定怎麼分類，只是要分組 | Folder |

簡單判斷：

- 是網站：選 URL。
- 是本機檔案 / 程式：選 App / File。
- 是單行命令：選 Command 或 PowerShell。
- 是可重複使用的 IT 腳本：選 PowerShell Library。
- 是客戶多網站工作流程：選 Client Workspace。
- 是系統資訊盤點：選 Environment Check。
- 是文字輸入輔助：選 Paste 或 Form。

---

## 6. 目前 SmartAction 已完成的功能

### 快捷輪盤

使用者可以透過熱鍵叫出快捷輪盤，快速點選常用功能。

特色：

- 支援多個快捷項目。
- 支援多層資料夾。
- 可自訂名稱、Icon / Emoji、動作。
- 可放 App、URL、PowerShell、Client Workspace、Environment Check。
- 支援 Theme 動畫。
- 支援點擊外部空白處關閉。

目前狀態：已完成。

### Settings 設定中心

Settings 是管理 SmartAction 的主要入口。

特色：

- 新增 / 編輯 / 刪除 actions。
- 選擇 action type。
- 設定 hotkey。
- 選擇 theme。
- Profile Import / Export。
- Help Center。
- Start with Windows。

目前狀態：已完成。

### Theme / 能量環視覺

輪盤支援多種主題與動畫素材。

目前主題：

- Purple
- Tiger Fur
- Ice / Frozen
- Fire / Lava
- Space / Cosmic

特色：

- Action bubble 有 themed rim。
- 支援 frame animation。
- 若素材缺失會 fallback，不會 crash。

目前狀態：已完成。

### Icon Picker / Emoji Picker

使用者可以用更完整的 Icon Picker 為 action 選圖示。

特色：

- 搜尋 icon。
- 多分類。
- Recent。
- Favorites。
- Preview。
- Clear。
- 雙擊套用。
- 本機 emoji database。

目前狀態：已完成。

### Hotkey Picker

使用者可以用小型鍵盤介面設定 hotkey，不需要實際按鍵偵測。

特色：

- Ctrl / Alt / Shift / Win 可多選。
- 主鍵只能選一個。
- 即時顯示組合鍵。
- 危險快捷鍵檢查。
- 套用前驗證。

目前狀態：已完成。

### PowerShell Library

PowerShell Library 是 SmartAction 的 IT 工具箱。

特色：

- 管理常用 PowerShell 腳本。
- 支援分類。
- 支援 safe / dangerous。
- 支援參數。
- 支援 password 欄位遮蔽。
- 支援執行結果視窗。
- 可以把單一 script 掛到輪盤。

目前狀態：已完成。

### Local User / Domain / AD 維護

目前透過 PS Form 與 PowerShell Library 提供相關能力。

包含：

- 建立本機使用者。
- 加入 Administrators。
- 停用本機使用者。
- 查看本機使用者。
- 查看本機 Administrators。
- 查看 Domain status。
- Join Domain。
- Rename Computer。

目前狀態：已完成基礎版本，dangerous 操作會要求確認或建議管理員權限。

### Environment Check

一鍵檢查目前電腦環境，並可 Copy Result。

特色：

- 系統資訊。
- 使用者權限。
- 網路資訊。
- DNS / Gateway 測試。
- PowerShell Execution Policy。
- 防火牆狀態。

目前狀態：已完成。

### Client Workspace

可針對不同客戶建立維運工作區，一鍵開啟該客戶需要的網站或系統。

特色：

- 客戶清單。
- URL 清單。
- 匯入 / 匯出 JSON。
- Firefox Profile。
- Firefox Container Name。
- SmartAction Container Helper 狀態檢查。
- Native Host repair。

目前狀態：V1 一般 Firefox 開啟已完成；V2 Firefox Container Helper 整合已完成基礎流程，但使用者端需安裝 signed XPI 與 Native Host。

### Startup Video Splash

啟動 SmartAction 時可以播放啟動影片。

特色：

- 支援 mp4。
- 支援 gif fallback。
- 最多播放 5 秒。
- Skip 後進入背景，不退出 App。
- 影片不存在時自動跳過。

目前狀態：已完成。

### Profile Import / Export

使用者可以匯出目前設定，分享或備份。

特色：

- 匯出 actions、hotkey、theme、PowerShell Library、Client Workspace、UI 設定。
- 匯入前自動備份。
- 敏感欄位遮蔽。
- 匯入錯誤時不破壞原設定。

目前狀態：已完成 Replace 模式；Merge 模式為預留 / 待擴充。

### Help Center / Wiki

Settings 右上角有 Help Center。

特色：

- Quick Start 內建視窗。
- Full Documentation 開 GitHub README。
- Open GitHub Repository。
- Report Issue。
- About SmartAction。
- 本機 markdown docs。

目前狀態：已完成。

### Release Package / 一鍵安裝

SmartAction 可以打包成給同事使用的 release package。

包含：

- SmartAction.exe
- setup.bat
- firefox-helper.xpi
- Native Host installer
- README_安裝說明.txt
- clients.json 範例

目前狀態：已完成。

---

## 7. 這個工具的強大之處

SmartAction 強的地方，不只是「可以開 App」。

它真正的價值是：把 IT 維護流程工具化。

一般快捷工具通常只能做：

- 開程式
- 開網站
- 開資料夾

SmartAction 可以進一步做到：

- 每個按鈕都是不同 Type。
- 同一個輪盤可以混合 URL、App、PowerShell、Client Workspace、Environment Check。
- PowerShell 腳本可以集中管理、分類、加參數、加 dangerous 確認。
- 客戶維運網站可以用 Client Workspace 管理，搭配 Firefox Container 隔離登入狀態。
- 設定可以匯出，讓團隊共用同一套工具。
- 可以打包成 exe 與 release package，降低部署門檻。
- 未來可以繼續擴充更多 Type，例如更多 AD 工具、遠端工具、API 自動化、票務系統整合。

換句話說，SmartAction 可以讓每個 IT 人員建立自己的工作控制台。

---

## 8. 建議使用情境

### 場景 1：IT 到客戶現場維護

可能使用：

- Environment Check：先確認電腦狀態。
- PowerShell Library：查 IP、Flush DNS、Renew IP、開 Services。
- PS Form：建立本機使用者、Join Domain。
- App / File：開啟工具資料夾或遠端工具。
- URL：開客戶後台。

建議輪盤分類：

- 系統檢查
- 網路工具
- 帳號工具
- 客戶後台
- 修復工具

### 場景 2：客服工程師每天處理不同客戶

可能使用：

- Client Workspace：依客戶開啟所有維運網站。
- URL：常用平台如 M365、Azure、監控、票務系統。
- Paste：常用回覆模板。
- Help Center：快速查看內部使用方式。
- Icon Picker：把不同客戶或工具設成容易辨識的 icon。

建議輪盤分類：

- 客戶工作區
- 工單系統
- 雲端管理
- 常用回覆
- 文件 / SOP

### 場景 3：一般使用者提升日常效率

可能使用：

- App / File：開常用軟體。
- URL：開常用網站。
- Folder：分類工作、娛樂、文件。
- Paste：常用文字片段。
- Form：快速輸入固定格式資料。

建議輪盤分類：

- 工作
- 網站
- 文件
- 常用文字
- 工具

### 場景 4：團隊共用 IT 工具包

可能使用：

- PowerShell Library：整理團隊共同腳本。
- Profile Export：匯出設定給同事。
- Release Package：打包 exe 與 setup.bat。
- Help Center：提供使用說明。

建議流程：

1. 由一位維護者建立標準 SmartAction 設定。
2. 加入常用 PowerShell Library。
3. 建立標準輪盤分類。
4. 匯出 profile。
5. 打包 release package。
6. 同事執行 setup.bat 後匯入 profile。

---

## 9. 給新使用者的快速建議

第一次使用 SmartAction，建議不要一次做太複雜。可以先建立這五類：

1. 常用網站

   例如 Microsoft Admin、Azure Portal、GitHub、監控平台。

2. 常用 App

   例如 Task Manager、AnyDesk、瀏覽器、工具資料夾。

3. 常用 PowerShell 工具

   先從 safe 腳本開始，例如 IP Configuration、Ping Target、Current User、Hostname。

4. 客戶工作區

   為常維護的客戶建立 Client Workspace，每個客戶放管理網站清單。

5. 匯出設定檔備份

   設定完成後使用 Export Profile 備份，之後換電腦或分享給同事會很方便。

建議順序：

```text
先建立 URL / App
→ 再整理 Folder 分類
→ 加入 PowerShell Library safe 腳本
→ 建立 Client Workspace
→ Export Profile 備份
```

---

## 10. 給開發者的補充

### Type 定義在哪裡

Action Type 主要在：

```text
core/actions/
```

目前註冊方式是每個 action class 使用 `@register_action`。`core/action_runner.py` 會透過 registry 找到對應 class。

### 新增 Type 應該修改哪些地方

通常需要修改：

1. 新增 `core/actions/<new_type>_action.py`
2. 在 `core/actions/__init__.py` import 新 module
3. 在 `core/actions_config.py` 的 `_normalise_type()` 加入 mapping
4. 在 `ui/settings_window.py` 的 type list 加入顯示名稱
5. 如果有特殊設定欄位，補 Settings UI
6. 如果需要結果視窗，新增 `ui/*_window.py`

### 設定檔格式在哪裡

主要設定：

```text
config/actions.json
```

資料型設定：

```text
data/powershell_library.json
data/client_workspaces.json
data/icons/emoji_database.json
data/icons/icon_picker_state.json
```

舊版 / 補充設定：

```text
resources/config.json
```

### UI 顯示邏輯在哪裡

主要 UI：

```text
ui/ring_ui.py
ui/settings_window.py
ui/powershell_library_window.py
ui/client_workspace_window.py
ui/environment_check_window.py
ui/emoji_picker.py
ui/hotkey_picker.py
ui/help_modal.py
ui/tray_icon.py
```

### 打包 / Release 相關檔案

```text
build.bat
build_extension.bat
build_release.bat
smartaction.spec
tools/build_firefox_extension.py
tools/build_release_package.py
```

常用命令：

```bat
python -m compileall app core ui native tools
python -m app.main
build.bat
build_release.bat
```

輸出位置：

```text
dist/UniversalActionsRing/
dist/firefox-helper.xpi
dist/SmartAction-Release/
```

---

## 11. 一句話總結

SmartAction 是一個可自訂、可擴充、可打包分享的 IT 快捷工作台。它把「開工具、開網站、執行指令、檢查環境、切換客戶工作區」整合到同一個快捷輪盤，讓日常維護流程變成更快、更穩、更容易交接的一鍵操作。
