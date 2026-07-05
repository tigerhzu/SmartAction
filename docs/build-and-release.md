# Build and Release / 打包與發布

這篇說明如何測試 SmartAction、打包 exe，以及分享給其他人使用。

---

## 開發模式執行

在專案根目錄執行：

```powershell
python -m app.main
```

這種方式適合開發與測試。

優點：

- 修改程式後可以快速測試
- 容易看到錯誤訊息
- 不需要每次都重新打包

---

## 打包 exe

在專案根目錄執行：

```powershell
.\build.bat
```

打包完成後，通常會產生：

```text
build/
dist/
```

真正要給使用者執行的檔案通常在：

```text
dist/
```

---

## 修改後為什麼要重新打包

如果你修改了 Python 程式碼、UI、docs、extensions 或 native helper，舊的 exe 不會自動更新。

所以每次功能修改完成後，都需要重新執行：

```powershell
.\build.bat
```

否則你打開的 exe 可能還是舊版。

---

## 清除舊打包檔案

如果懷疑打包結果還是舊版，可以先刪掉 build 和 dist：

```powershell
rmdir /s /q build
rmdir /s /q dist
.\build.bat
```

---

## dist 是什麼

`dist` 是打包後的輸出資料夾。

裡面通常會包含：

- SmartAction exe
- 需要一起帶走的資料夾
- docs
- extensions
- native
- data 或預設設定檔

實際內容依目前打包設定為準。

---

## build 是什麼

`build` 是打包過程產生的中間資料夾。

一般不需要分享給使用者。

如果打包出錯，可以刪掉 `build` 後重新打包。

---

## smartaction.spec 是什麼

`smartaction.spec` 是 PyInstaller 的打包設定檔。

如果新增了資料夾或檔案，例如：

```text
docs/
extensions/
native/
data/
```

需要確認 `smartaction.spec` 有把它們包含進去。

否則 exe 打包後可能找不到文件、Extension 或 Native Host。

---

## 分享給朋友時要給哪些檔案

如果是 one-folder 打包，通常要把整個 `dist` 裡的 SmartAction 資料夾一起給對方。

不要只給單一 exe，除非你的打包方式本來就是 one-file 且所有資料都已包含。

建議分享方式：

```text
dist/SmartAction/
```

整個資料夾壓縮成 zip 後提供。

---

## 分享前注意事項

分享前請檢查：

- 是否包含個人設定
- 是否包含客戶資料
- 是否包含內網 IP
- 是否包含管理後台網址
- 是否包含 API Key 或密碼
- data 裡是否有真實客戶資料

如果要給別人測試，建議使用 Demo 資料。

---

## 建議打包流程

1. 用開發模式測試：

```powershell
python -m app.main
```

2. 確認功能正常

3. 清除舊打包：

```powershell
rmdir /s /q build
rmdir /s /q dist
```

4. 重新打包：

```powershell
.\build.bat
```

5. 打開 dist 裡的新 exe 測試

6. 確認以下功能：

```text
Settings 可開啟
Theme 可切換
Global Hotkey 可用
Action 可執行
Client Workspace 可開啟
Help Center 可用
Export / Import Profile 可用
Start with Windows 不報錯
```

---

## GitHub Release

如果要正式發布，可以使用 GitHub Release。

建議流程：

1. 打包 SmartAction
2. 壓縮 dist 裡的輸出資料夾
3. 到 GitHub Repository
4. 點右側 Releases
5. 點 Create a new release
6. 建立版本號，例如：

```text
v0.1.0
```

7. 上傳 zip 檔
8. 寫上更新內容
9. Publish release

---

## 版本號建議

可以使用：

```text
v0.1.0
v0.2.0
v1.0.0
```

建議規則：

- 修 Bug：小版本增加，例如 v0.1.1
- 新增功能：中版本增加，例如 v0.2.0
- 穩定正式版：v1.0.0

---

## 常見問題

### 打包後功能不見

請檢查：

- smartaction.spec 是否包含新檔案
- build.bat 是否正確
- 是否開到舊 exe
- dist 是否重新產生

### exe 開不起來

請先用開發模式測試：

```powershell
python -m app.main
```

如果開發模式也失敗，代表不是打包問題，而是程式本身有錯。

### 修改 README 或 docs 要重新打包嗎

如果 Help Center 是跳 GitHub 網頁，不需要重新打包。

如果 docs 是包在 exe 或本機資料夾裡，就需要重新打包。
