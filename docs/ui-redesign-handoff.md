# SmartAction UI 改版交接文件

Date: 2026-07-09
狀態：**視覺套色階段（redesign plan §11 step 1–6, 9）已完成並驗證；Ring 動效/光暈調參（step 7–8）尚未開始**
前置文件：`docs/ui-audit.md`（原始掃描）、`docs/ui-redesign-plan.md`（設計方案，已加註完成狀態）

這份文件是給接手後續工作的人（包含未來的我）看的：現在專案的 UI 實際處於什麼狀態、改了什麼、為什麼這樣改、還剩什麼、以及每一步是怎麼驗證的。

---

## 1. 現況總覽

SmartAction 目前已經是一個統一的深色 UI：黑曜岩背景（`void`/`charcoal`/`steel`）+ 琥珀色 Tiger 品牌強調色（`ember`），取代了原本「白底表單 + 淺紫點綴」的預設 Qt 觀感。**13 個 UI 檔案**全部從 hardcoded hex 換成共用 token，`core/theme.py` 的 Tiger 主題升格為預設，字型內嵌了 Oswald（尚未套用到任何畫面，只有基礎設施）。

**Ring 本體（`ui/ring_ui.py`/`ui/theme_painter.py`）的光暈與動畫參數完全沒有調整** —— 這是刻意的，因為那是全專案風險最高、最需要小心測試的區塊（見 §5）。

## 2. 這次改了什麼（依時間順序，兩個 Phase）

### Phase 0 — 前置整理（不涉及視覺）

| 項目 | 內容 |
|---|---|
| 移除 legacy 程式碼 | 刪除 `ui/settings_ui.py`、`ui/pages/*`（`about_page.py`/`general_page.py`/`hotkey_page.py`/`menus_page.py`/`__init__.py`）、`ui/menu_editor.py`（2 行空 stub）。確認過 repo 全域沒有任何 import，`smartaction.spec`/build .bat 也沒有引用。 |
| 修正過時文件 | `README.md`、`SmartAction_架構與功能說明.md` 裡提到上述已刪檔案的段落，改指向真正在用的 `ui/settings_window.py`。 |
| 清理資料層死碼 | `core/config_manager.py` 移除從未被讀取的 `"ring"` 預設 block 與 `"menu_items"`/`load_menu_tree()`（唯一讀寫者是已刪除的 `menus_page.py`）。**`ConfigManager` 類別本身沒有刪**，因為 `startup_video_*` 三個 key 與 `core/profile_manager.py` 的備份/還原還在用它。 |
| 內嵌 Oswald 字型 | 新增 `assets/fonts/Oswald.ttf`（Google Fonts 官方可變字重版本）+ `assets/fonts/OFL.txt`（授權全文），會被 `smartaction.spec` 既有的 `collect_tree(assets)` 自動打包，**沒有改 spec 檔**。新增 `core/fonts.py`（`FONTS_DIR`、`DISPLAY_FONT_FAMILY = "Oswald"`、`load_bundled_fonts()`），從 `app/application.py` 的 `Application.__init__` 呼叫一次。**目前只驗證了字型能正確載入（`debug_log` 確認 `families=['Oswald', ...]`），還沒有任何畫面實際套用 Oswald 字型**——這是下一步視覺工作可以做的事。 |

### Phase 1 — 視覺套色（redesign plan §11 的 step 1–6, 9）

新增 `ui/style_tokens.py` 作為唯一的顏色/字級/間距來源（純資料，內容見 §3）。以下檔案的所有 QSS 字串顏色都已從 hardcoded hex 換成這份 token：

| 檔案 | 備註 |
|---|---|
| `ui/tray_icon.py` | 系統匣圖示改成 ember 色 |
| `core/theme.py` | 每個 ring 主題新增 `bubble_*` 四個 key（數值原封不動搬自 `theme_painter.py`，零視覺差異）；`DEFAULT_THEME` 改成 `"tiger"`；`THEME_ORDER` 把 tiger 移到第一位 |
| `ui/theme_painter.py` | `_theme_colors()` 改成從 `core.theme.THEMES` 讀 `bubble_*`，不再是獨立維護的第二份色票 |
| `core/actions_config.py` | `get_theme()` 的 fallback 從 `"purple"` 改成 `"tiger"`（新安裝真正吃到的預設值） |
| `ui/ring_ui.py` | 5 處硬編碼 `"purple"` fallback 改用 `DEFAULT_THEME`；**除此之外沒有動 ring 的任何繪圖/動畫/命中測試邏輯** |
| `core/profile_manager.py` | Profile 匯入時的 theme fallback 同步改用 `DEFAULT_THEME` |
| `ui/settings_window.py` | 全部 QSS 常數 + `_ThemeCard.paintEvent`（見 §4 的切角說明）+ 視窗尺寸 |
| `ui/client_workspace_window.py` | 全部 QSS 常數 + 新增 `_BTN_SMALL` + 視窗尺寸放大（見 §4） |
| `ui/powershell_library_window.py` | 全部 QSS 常數（原本的深色 console 區塊統一併入同一套 token，不再是孤島） |
| `ui/emoji_picker.py` | 全部 QSS 常數（搜尋/分類/收藏/鍵盤導覽邏輯完全沒動） |
| `ui/hotkey_picker.py` | 全部 QSS 常數 + 視窗尺寸放大（見 §4） |
| `ui/help_modal.py` | 對話框/按鈕換色（Markdown 內容渲染不受影響，已截圖驗證中文內容清楚可讀） |
| `ui/environment_check_window.py` | 按鈕/console 輸出面板換色 |
| `ui/widgets.py` | `make_input_field`/`make_h_separator` 共用工廠函式換色；順便修掉 audit 提到的「另一支藍色 `#2563EB`」與分隔線灰階不一致問題 |
| `ui/forms/base_form.py` | 藍色按鈕改 ember；**補上原本完全沒有的 QDialog 深色背景**（原本這個對話框只有欄位/按鈕有樣式，對話框本身吃系統預設淺色背景） |
| `ui/forms/add_local_user_form.py` | checkbox 補上明確文字色 |
| `ui/forms/join_domain_form.py` | **沒有改動**——它唯一的自訂樣式是加入網域後的重開機確認 `QMessageBox`，屬於安全敏感流程，刻意不碰 |
| `ui/main_window.py` | dev launcher 按鈕/文字換色 |
| `ui/startup_splash.py` | 原本就是深色（`#090A12`/`#05070D`），這次對齊到共用 token，不再獨立維護 |

## 3. `ui/style_tokens.py` 內容速查

```python
VOID, CHARCOAL, STEEL, ASH            # 背景層次（由深到淺）
BONE, FOG                              # 文字（主要/次要）
EMBER, EMBER_HOVER, EMBER_PRESSED, EMBER_WASH   # 品牌強調色
SIGNAL_RED / _HOVER / _PRESSED / _WASH          # 危險
SIGNAL_GREEN / _WASH                            # 成功
SIGNAL_AMBER / _WASH                            # 警告
SPACE_4 ... SPACE_40                            # 間距刻度
CORNER_CUT_PX                                   # 簽名切角尺寸常數
BODY_FONT_FAMILY / HEADLINE_FONT_FAMILY / MONO_FONT_FAMILY
SIZE_DISPLAY ... SIZE_MONO                      # 字級尺度
BUTTON_MIN_HEIGHT, FIELD_HEIGHT, ROW_HEIGHT
```

`HEADLINE_FONT_FAMILY` 指向 `core.fonts.DISPLAY_FONT_FAMILY`（`"Oswald"`）——**目前沒有任何畫面實際使用這個常數**，字級/間距的其他 token 也還沒有全部套用到每個畫面的每個字級（多數畫面沿用各自原本合理的字級，只換了顏色跟少數幾個明顯太小的地方）。

## 4. 已知的取捨與偏離原計畫之處

**「單一切角」簽名造型只有 `_ThemeCard`（Settings 主題卡）做到了真正的 45° 切角。** Qt Style Sheet（QSS）本身不支援任意角度切角，只支援 `border-radius`（圓角）。一般 `QPushButton`/`QLineEdit`/`QTableWidget` 這次全部用很小的圓角（3px，接近直角但非純方形）代替，沒有做成切角。要讓所有按鈕都有真正的切角，需要另外做一個自繪按鈕元件（新 widget class，逐一替換所有 `QPushButton()` 呼叫），這是比「機械式換色」大很多的工程，這次沒有做。`_ThemeCard` 因為本來就是 `paintEvent` 自繪，改成切角是低風險的既有程式碼調整，所以做了。

**兩個視窗因為字級從 13px 升到 14px、按鈕從 32px 升到 36px 而變得擁擠，實測後放大了預設尺寸**（原計畫 `docs/ui-redesign-plan.md` §10 曾預估這兩個「不變」，但截圖驗證後發現裁切問題才調整）：

| 視窗 | 原計畫 | 實際採用 | 原因 |
|---|---|---|---|
| Client Workspace | 不變（1080×720） | `resize(1300, 760)`，並把底部 7 個次要按鈕（Install Helper/Check Helper/Repair Setup/Open Add-ons/Export/Import/Close）改用新增的 `_BTN_SMALL`（12px/28px，比照 `settings_window.py` 既有的工具列按鈕分級） | 8 個按鈕的工具列在原寬度下文字被截斷（截圖驗證「ch Works」「Helper Ex」等裁切） |
| Hotkey Picker | 不變（660×590） | `resize(740, 600)`，`setMinimumSize(680, 560)` | 10 欄按鍵網格在原寬度下最後一欄（Space/Enter）被裁切、出現水平捲軸 |

Settings（`1180×760`）照原計畫執行；Client Workspace 的最小尺寸維持 `980×660`；PowerShell Library / Emoji Picker / Environment Check / Help Modal / Main window / Ring 都維持原尺寸不變（實測沒有裁切問題）。

## 5. 還沒做的部分（redesign plan §11 step 7–8）

這兩步刻意留到最後，因為牽涉 `ui/ring_ui.py`/`ui/theme_painter.py` 全專案風險最高的區塊（`paintEvent` 座標變換、命中測試、動畫 timer 生命週期）：

1. **Ring 的 glow/gradient 參數微調**（`theme_painter.py` 的 `draw_energy_bubble` 內的放射狀漸層半徑/不透明度）——目標是把柔和光暈換成更清晰的「金屬邊緣反光」，純調參數不重寫繪圖邏輯，但**需要在多個螢幕/多個主題下實測**才能確認沒有引入視覺瑕疵。
2. **Ring 開場動畫調整**（`OutBack` overshoot 幅度降低、slot 進場加 8–12ms stagger、中心按鈕加一次性 ember 脈衝）——風險最高，因為 audit 已指出動畫過程中「視覺位置跟命中測試位置本來就有些微不同步」的既有問題，任何改動都必須實測拖曳/點擊時序與多螢幕情境，不能只看畫面。

這兩步的詳細做法已經寫在 `docs/ui-redesign-plan.md` §8，之後要繼續時直接照那份規格做即可，不需要重新設計。

## 6. 怎麼驗證這次的改動（重現我用過的驗證方式）

沒有寫自動化測試，每一個檔案改完都是這樣驗證的，之後要接手可以照同樣模式：

1. **靜態檢查**：`python -m py_compile <改動的檔案>`，以及 `Grep` 該檔案確認沒有殘留 `#[0-9A-Fa-f]{6}` hex（`ui/style_tokens.py` 本身跟 `ui/tray_icon.py` 的白色內點例外，那是故意的）。
2. **獨立截圖驗證**：寫一個一次性小腳本（`QApplication` + 直接 `new` 目標對話框 + `QTimer.singleShot` 延遲呼叫 `widget.grab().save(...)`），實際帶入真實資料（例如真的 `ActionsConfig()`/`PowerShellLibrary()`）建構畫面，讀圖確認顏色/裁切/對齊沒問題。這次每個窗口都至少截圖驗證過一次。
3. **全 App 煙霧測試**：`python -m app.main` 背景啟動，等 6 秒讓 startup splash 跑完進入 tray 模式，檢查 `app_debug.log` 有沒有新增的 `error`/`exception`/`traceback`，確認後手動 `taskkill` 關閉。
4. 所有一次性驗證腳本跟截圖用完都刪除了，repo 裡不會留下測試殘骸。

## 7. 檔案異動總清單

**新增：**
- `ui/style_tokens.py`
- `core/fonts.py`
- `assets/fonts/Oswald.ttf`、`assets/fonts/OFL.txt`
- `docs/ui-redesign-handoff.md`（這份文件）

**刪除：**
- `ui/settings_ui.py`、`ui/pages/`（整個目錄）、`ui/menu_editor.py`

**修改：**
- `README.md`、`SmartAction_架構與功能說明.md`（文件修正）
- `core/config_manager.py`、`core/actions_config.py`、`core/theme.py`、`core/profile_manager.py`、`app/application.py`
- `ui/tray_icon.py`、`ui/theme_painter.py`、`ui/ring_ui.py`（僅 `DEFAULT_THEME` 替換，非視覺/動畫改動）
- `ui/settings_window.py`、`ui/client_workspace_window.py`、`ui/powershell_library_window.py`、`ui/emoji_picker.py`、`ui/hotkey_picker.py`、`ui/help_modal.py`、`ui/environment_check_window.py`、`ui/widgets.py`、`ui/forms/base_form.py`、`ui/forms/add_local_user_form.py`、`ui/main_window.py`、`ui/startup_splash.py`

**刻意沒動：**
- `ui/forms/join_domain_form.py`（安全敏感的重開機確認流程）
- `ui/ring_ui.py` 的繪圖/動畫邏輯本體、`ui/theme_painter.py` 的 gradient/blur 參數（留給下一階段）
- `core/theme.py` 裡 purple/ice/lava/cosmic 四個既有主題的實際色票數值（沒有改配色，只加了新 key、調了預設/排序）
