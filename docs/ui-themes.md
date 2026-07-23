# Global UI Themes / 全域介面主題

SmartAction 保留原本的深色介面，並提供可選擇圖片的可愛粉彩介面。

## 切換介面

1. 開啟 `Settings`。
2. 在 `Interface` 選擇：
   - `Classic — original dark UI`：原本的深色工業風介面。
   - `Cute — pastel + custom image`：粉彩、圓角按鈕與內建高畫質背景；也能換成自己的圖片。
   - `Woven Light — interactive particles`：明亮玻璃介面與會跟隨滑鼠產生視差、局部擾動的彩色光點編織背景。
3. 選擇後會立刻在 Settings 視窗套用預覽。
4. 按 `Save` 正式儲存並套用到 SmartAction 的主要視窗與對話框。

Ring 本身的能量環與星座仍由上方的 `Theme`、`Ring constellation` 設定控制。

Woven Light 使用 SmartAction 內建的 QPainter 繪圖，不需要 Pillow、Three.js、WebGL 或額外下載素材。圖片選擇與裁切功能只適用於 Cute 主題。

Cute 沒有設定自訂圖片時會自動使用 SmartAction 內建的櫻花天空背景。按下 `Clear` 會回到這張內建圖片，不會顯示空白背景。Windows 系統匣與應用程式 Logo 也會跟隨 Classic、Cute 或 Woven Light 自動切換。

## 使用自己的背景圖片

1. 選擇 `Cute`。
2. 按 `Choose Image`。
3. 選擇 PNG、JPG、BMP 或 WEBP 圖片。
4. 使用 `Image` 滑桿調整圖片顯示強度。
5. 畫面會即時顯示效果，確認後按 `Save`。

圖片在儲存時會複製到：

```text
config/ui-backgrounds/
```

因此原始圖片搬移或刪除後，SmartAction 仍能使用已套用的背景。

## 圖片建議

- 建議解析度至少 1920×1080。
- 盡量使用乾淨插圖，不要使用含有其他程式按鈕或表格的完整截圖。
- 主角可以放在畫面右側，避免被左側清單遮住。
- 背景太花時可降低 `Image` 百分比，維持文字可讀性。

## 套用範圍

全域介面會套用到 Settings、PowerShell Library、Client Workspace、Emoji Picker、Hotkey Picker、Help 與其他 SmartAction 對話框。切回 Classic 後，各視窗會恢復原有樣式。
