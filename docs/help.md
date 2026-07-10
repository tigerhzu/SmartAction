# Universal Actions Ring 使用說明

## 這個 App 的用途

Universal Actions Ring 是一個快速啟動工具。按下全域快捷鍵後，畫面會出現一個圓形快捷輪盤，你可以用它快速開啟網站、執行工具、貼上文字、啟動 PowerShell 腳本，或進入下一層資料夾選單。

## 如何新增 Action

1. 開啟 Settings。
2. 在左側 Actions 區塊按下 `+ Add`。
3. 輸入顯示名稱、短標籤或 emoji。
4. 選擇 Type。
5. 依照 Type 填入 Target。
6. 按下 Save。

## 各種 Type 的用途說明

### Folder

Folder 用來建立子選單。它本身不執行動作，點擊後會進入下一層 action ring。

### URL

URL 用來開啟網站或網頁連結。

```text
https://www.google.com
```

### App / File

App / File 用來開啟本機程式或檔案。Target 可以填入 exe、文件或其他可由系統開啟的檔案路徑。

```text
C:\Windows\System32\notepad.exe
```

### Command

Command 用來執行一般 shell 指令，適合啟動工具、執行批次命令或開啟特定工作流程。

```bat
ipconfig /all
```

### PowerShell

PowerShell 用來執行 PowerShell 指令或腳本，適合系統管理、查詢、維護動作。

```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

### Paste

Paste 用來把指定文字放到剪貼簿並貼上，適合常用片語、回覆模板、命令片段。

### Form

Form 用來開啟簡單輸入表單。適合需要先輸入資訊再產生結果的流程。

### PS Form

PS Form 用來搭配已註冊的 PowerShell 表單流程。Target 通常會是特定 form id。

## 如何設定 Global hotkey

在 Settings 上方的 Global hotkey 欄位輸入快捷鍵組合，按下 Save 後生效。

```text
ctrl+space
ctrl+alt+r
```

如果快捷鍵註冊失敗，請確認該組合沒有被其他程式占用。

## 使用範例

- 建立一個 Folder 叫做 `Admin`，裡面放常用 PowerShell 腳本。
- 建立一個 URL action 快速打開公司內部系統。
- 建立一個 Paste action 貼上常用客服回覆。
- 建立一個 App / File action 開啟常用工具或文件。

## 圖片語法

教學截圖可以放在 `assets/wiki/`，然後在本文使用相對路徑：

```markdown
![圖片說明](../assets/wiki/example.png)
```

## 注意事項

- 執行 Command 或 PowerShell 前，請確認指令內容安全。
- 修改 Settings 後要按 Save 才會保存。
- 如果某個 action 沒有出現在 ring 中，請確認它是否已啟用。
- Folder 可以包含多個 sub-action，用來整理常用工作流程。
