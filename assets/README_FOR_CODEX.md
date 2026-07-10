
# SmartAction Theme Ring Assets

This package contains static and animated theme ring assets for Universal Actions Ring / SmartAction.

## Folder layout

```
assets/themes/purple/rim.png
assets/themes/purple/rim_active.png
assets/themes/purple/card_bg.png
assets/themes/purple/frames/frame_000.png ... frame_023.png

assets/themes/tiger/...
assets/themes/ice/...
assets/themes/lava/...
assets/themes/cosmic/...
```

## Recommended usage

Use `rim.png` as the static ring rim.
Use `frames/frame_000.png` through `frame_023.png` for animated rim playback.
Use `card_bg.png` as the theme picker card background or preview texture.

All assets are exported as 512x512 RGBA PNGs for rim / frames and 256x360 RGBA PNGs for card previews.

## Codex prompt

Please add support for external theme assets in the Universal Actions Ring app.

Requirements:
1. Load theme assets from `assets/themes/<theme_id>/`.
2. Supported files:
   - `rim.png` static ring rim
   - `rim_active.png` optional active ring rim
   - `card_bg.png` optional theme picker card background
   - `frames/frame_000.png` ... frame_NNN.png` optional animation frames
3. If `frames/` exists, play frames with QTimer at about 24fps or 30fps.
4. Cache all QPixmap frames on load. Do not read files every frame.
5. Only animate while Ring window or Settings window is visible.
6. If assets are missing, fallback to the existing QPainter theme drawing.
7. Draw order for action bubble:
   - outer glow fallback / shadow
   - animated frame or static rim image
   - inner glass circle
   - icon / emoji / short label on top
8. Draw order for theme picker card:
   - card background or dark glass fallback
   - ring preview image or animated frame
   - theme name text
   - selected glow border + check mark
9. Do not change hotkey, action launch logic, config structure, or emoji picker.
10. After implementation, run Python compile check and tell me how to start the source version for testing.
