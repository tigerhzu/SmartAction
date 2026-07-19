# SmartAction theme assets

Each directory under `assets/themes/` contains:

- `frames/frame_000.png` through `frame_023.png`: animated ring frames.
- `card_bg.png`: Settings theme-card background.

The bundled ring frames are optimized to 160×160 RGBA PNGs. The ring draws
them at roughly 64–74 logical pixels, so this retains high-DPI headroom while
keeping decoded memory and package size low. Do not restore the old 512×512
exports unless the runtime display size is also increased.

`ui/theme_painter.py` caches decoded frames. It loads all frames only for the
active animated theme; inactive Settings previews load frame 0 only. A custom
theme may still provide an optional `rim.png` static fallback. If no usable
image exists, the QPainter fallback is used.
