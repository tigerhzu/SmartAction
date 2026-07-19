"""
Shared theme painting helpers for ring previews and action bubbles.

The visual language is an energy rim around a clean glass center. Textures stay
inside the rim so labels and emoji remain readable.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PySide6.QtCore import QLineF, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
    QImageReader,
)

from core.debug_log import debug_log
from core.paths import ASSETS_DIR

_ASSET_ROOT = ASSETS_DIR / "themes"
_ASSET_CACHE: dict[str, "ThemeAssets"] = {}
_FRAME_COUNT_CACHE: dict[str, int] = {}
_DRAW_LOGGED: set[tuple[str, str]] = set()
_MAX_RIM_PIXELS = 160


@dataclass
class ThemeAssets:
    base_path: Path
    frames_path: Path
    rim: QPixmap | None
    card_bg: QPixmap | None
    frames: list[QPixmap]
    frames_fully_loaded: bool

    @property
    def has_rim(self) -> bool:
        return self.rim is not None or bool(self.frames)

    def ring_pixmap(self, frame_index: int = 0) -> QPixmap | None:
        if self.frames:
            return self.frames[frame_index % len(self.frames)]
        return self.rim


def _load_pixmap(path: Path, max_pixels: int | None = None) -> QPixmap | None:
    if not path.exists():
        return None
    reader = QImageReader(str(path))
    if max_pixels:
        size = reader.size()
        if size.isValid() and (size.width() > max_pixels or size.height() > max_pixels):
            reader.setScaledSize(
                size.scaled(
                    QSize(max_pixels, max_pixels),
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            )
    image = reader.read()
    if image.isNull():
        return None
    pix = QPixmap.fromImage(image)
    return None if pix.isNull() else pix


def preload_theme_assets(theme_id: str, load_all_frames: bool = True) -> ThemeAssets:
    """Load and cache theme pixmaps, optionally using only the first frame."""
    cached = _ASSET_CACHE.get(theme_id)
    if cached is not None:
        if load_all_frames and not cached.frames_fully_loaded:
            cached.frames = _load_theme_frames(cached.frames_path, True)
            cached.frames_fully_loaded = True
        return cached

    base = _ASSET_ROOT / theme_id
    frames_dir = base / "frames"
    frames = _load_theme_frames(frames_dir, load_all_frames)

    assets = ThemeAssets(
        base_path=base,
        frames_path=frames_dir,
        rim=_load_pixmap(base / "rim.png", _MAX_RIM_PIXELS),
        card_bg=_load_pixmap(base / "card_bg.png"),
        frames=frames,
        frames_fully_loaded=load_all_frames,
    )
    _ASSET_CACHE[theme_id] = assets
    debug_log(
        f"theme assets: theme_id={theme_id!r} "
        f"asset_path={base.resolve()} asset_exists={base.exists()} "
        f"frames_path={frames_dir.resolve()} frames_exists={frames_dir.exists()} "
        f"frames_count={len(frames)} rim_exists={(base / 'rim.png').exists()} "
        f"card_bg_exists={(base / 'card_bg.png').exists()}"
    )
    return assets


def _load_theme_frames(frames_dir: Path, load_all: bool) -> list[QPixmap]:
    if not frames_dir.exists():
        return []
    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if not load_all:
        frame_paths = frame_paths[:1]
    frames: list[QPixmap] = []
    for frame_path in frame_paths:
        pix = _load_pixmap(frame_path, _MAX_RIM_PIXELS)
        if pix is not None:
            frames.append(pix)
    return frames


def theme_frame_count(theme_id: str) -> int:
    cached = _FRAME_COUNT_CACHE.get(theme_id)
    if cached is None:
        frames_dir = _ASSET_ROOT / theme_id / "frames"
        cached = sum(1 for _ in frames_dir.glob("frame_*.png")) if frames_dir.exists() else 0
        _FRAME_COUNT_CACHE[theme_id] = cached
    return cached


def theme_asset_debug_summary(theme_id: str) -> str:
    base_path = _ASSET_ROOT / theme_id
    frames_path = base_path / "frames"
    frame_count = theme_frame_count(theme_id)
    rim_path = base_path / "rim.png"
    mode = "animated asset" if frame_count else "static png fallback" if rim_path.exists() else "painter fallback"
    selected_path = frames_path if frame_count else rim_path
    return (
        f"theme_id={theme_id!r} selected_theme_asset_path={selected_path.resolve()} "
        f"asset_exists={selected_path.exists()} frames_count={frame_count} "
        f"using={mode}"
    )


def prune_theme_asset_cache(keep_theme_ids: set[str]) -> None:
    """Release decoded pixmaps for themes that are no longer on screen."""
    for theme_id in tuple(_ASSET_CACHE):
        if theme_id not in keep_theme_ids:
            del _ASSET_CACHE[theme_id]


def _draw_pixmap_cover(p: QPainter, pix: QPixmap, rect: QRectF) -> None:
    """Draw pixmap cropped to cover rect while preserving aspect ratio."""
    if pix.isNull() or rect.width() <= 0 or rect.height() <= 0:
        return
    pix_w = float(pix.width())
    pix_h = float(pix.height())
    target_ar = rect.width() / rect.height()
    pix_ar = pix_w / pix_h
    if pix_ar > target_ar:
        src_h = pix_h
        src_w = pix_h * target_ar
        src_x = (pix_w - src_w) / 2.0
        src_y = 0.0
    else:
        src_w = pix_w
        src_h = pix_w / target_ar
        src_x = 0.0
        src_y = (pix_h - src_h) / 2.0
    p.drawPixmap(
        rect.toRect(),
        pix,
        QRectF(src_x, src_y, src_w, src_h).toRect(),
    )


def draw_theme_card_background(p: QPainter, rect: QRectF, theme_id: str) -> bool:
    """Draw card_bg.png if available. Returns True when an asset was used."""
    pix = preload_theme_assets(theme_id, load_all_frames=False).card_bg
    if pix is None:
        return False
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    _draw_pixmap_cover(p, pix, rect)
    return True


def _annulus(cx: float, cy: float, outer_r: float, inner_r: float) -> QPainterPath:
    path = QPainterPath()
    path.setFillRule(Qt.FillRule.OddEvenFill)
    path.addEllipse(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
    path.addEllipse(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
    return path


def _theme_colors(theme_id: str) -> tuple[QColor, QColor, QColor, QColor]:
    """Rim-gradient colors for the painter-fallback bubble render.

    Sourced from core.theme.THEMES so there is a single place to edit a
    theme's palette — this used to be an independent hardcoded copy that
    could silently drift out of sync with core/theme.py.
    """
    from core.theme import DEFAULT_THEME, THEMES
    t = THEMES.get(theme_id, THEMES[DEFAULT_THEME])
    return (
        QColor(*t["bubble_main"]),
        QColor(*t["bubble_dark"]),
        QColor(*t["bubble_highlight"]),
        QColor(*t["bubble_glow"]),
    )


def draw_energy_bubble(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    theme_id: str,
    *,
    selected: bool = False,
    hovered: bool = False,
    rim_width: float | None = None,
    inner_fill: QColor | None = None,
    frame_index: int = 0,
    animate: bool = True,
) -> None:
    """Draw an outer glow, textured rim, and clean inner glass center."""
    rim_w = rim_width if rim_width is not None else max(7.0, outer_r * 0.28)
    inner_r = max(outer_r - rim_w, 4.0)
    main, dark, highlight, glow = _theme_colors(theme_id)
    glow_alpha = min(122, glow.alpha() + (28 if hovered or selected else 0))

    p.setPen(Qt.PenStyle.NoPen)
    for grow, alpha_mul in ((8.0, 0.16), (4.0, 0.30), (1.8, 0.52)):
        g = QRadialGradient(cx, cy, outer_r + grow)
        g.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
        g.setColorAt(0.62, QColor(glow.red(), glow.green(), glow.blue(), int(glow_alpha * alpha_mul)))
        g.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), outer_r + grow, outer_r + grow)

    assets = preload_theme_assets(theme_id, load_all_frames=animate)
    pix = assets.ring_pixmap(frame_index)
    if pix is not None:
        mode = (
            "animated asset"
            if assets.frames_fully_loaded and len(assets.frames) > 1
            else "static preview frame"
            if assets.frames
            else "static png fallback"
        )
        key = (theme_id, mode)
        if key not in _DRAW_LOGGED:
            selected_path = assets.frames_path if assets.frames else assets.base_path / "rim.png"
            debug_log(
                f"theme renderer: theme_id={theme_id!r} "
                f"selected_theme_asset_path={selected_path.resolve()} "
                f"asset_exists={selected_path.exists()} using={mode}"
            )
            _DRAW_LOGGED.add(key)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        draw_r = outer_r + 3.8
        target = QRectF(cx - draw_r, cy - draw_r, draw_r * 2, draw_r * 2)
        p.drawPixmap(target.toRect(), pix)
        _draw_inner_glass(p, cx, cy, outer_r, inner_r, highlight, hovered, selected, inner_fill)
        return

    key = (theme_id, "painter fallback")
    if key not in _DRAW_LOGGED:
        debug_log(
            f"theme renderer: theme_id={theme_id!r} "
            f"selected_theme_asset_path={assets.base_path.resolve()} "
            f"asset_exists={assets.base_path.exists()} using=painter fallback"
        )
        _DRAW_LOGGED.add(key)

    ring = _annulus(cx, cy, outer_r, inner_r)
    cg = QConicalGradient(QPointF(cx, cy), -65)
    cg.setColorAt(0.00, highlight)
    cg.setColorAt(0.16, main.lighter(125))
    cg.setColorAt(0.34, dark)
    cg.setColorAt(0.54, main)
    cg.setColorAt(0.72, dark.darker(130))
    cg.setColorAt(0.88, main.lighter(145))
    cg.setColorAt(1.00, highlight)
    p.fillPath(ring, QBrush(cg))

    p.save()
    p.setClipPath(ring)
    _draw_rim_texture(p, cx, cy, outer_r, inner_r, theme_id)
    p.restore()

    _draw_inner_glass(p, cx, cy, outer_r, inner_r, highlight, hovered, selected, inner_fill)


def _draw_inner_glass(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    inner_r: float,
    highlight: QColor,
    hovered: bool,
    selected: bool,
    inner_fill: QColor | None,
) -> None:
    glass = QPainterPath()
    glass.addEllipse(cx - inner_r + 0.7, cy - inner_r + 0.7, (inner_r - 0.7) * 2, (inner_r - 0.7) * 2)
    base = inner_fill or QColor(20, 24, 42, 196)
    fill = QLinearGradient(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r)
    fill.setColorAt(0.0, base.lighter(142))
    fill.setColorAt(0.58, base)
    fill.setColorAt(1.0, base.darker(132))
    p.fillPath(glass, QBrush(fill))

    sheen = QRadialGradient(cx - inner_r * 0.42, cy - inner_r * 0.52, inner_r * 0.86)
    sheen.setColorAt(0.0, QColor(255, 255, 255, 48))
    sheen.setColorAt(0.55, QColor(255, 255, 255, 10))
    sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillPath(glass, QBrush(sheen))

    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 74 if hovered else 46), 1.0))
    p.drawEllipse(QPointF(cx, cy), inner_r - 0.4, inner_r - 0.4)
    p.setPen(QPen(highlight, 1.4 if hovered or selected else 1.0))
    p.drawEllipse(QPointF(cx, cy), outer_r - 0.7, outer_r - 0.7)
    arc_rect = QRectF(cx - outer_r + 3.0, cy - outer_r + 3.0, (outer_r - 3.0) * 2, (outer_r - 3.0) * 2)
    p.setPen(QPen(QColor(255, 255, 255, 96 if hovered or selected else 62), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawArc(arc_rect, 34 * 16, 104 * 16)
    p.setPen(QPen(QColor(0, 0, 0, 75), 0.8))
    p.drawEllipse(QPointF(cx, cy), inner_r + 0.5, inner_r + 0.5)
    p.setPen(Qt.PenStyle.NoPen)


def _draw_rim_texture(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    inner_r: float,
    theme_id: str,
) -> None:
    width = outer_r - inner_r
    if theme_id == "tiger":
        p.setPen(QPen(QColor(18, 9, 4, 190), max(2.2, width * 0.52), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(12):
            a = math.radians(i * 30 - 12)
            mid_r = (outer_r + inner_r) * 0.5
            x = cx + math.cos(a) * mid_r
            y = cy + math.sin(a) * mid_r
            dx = math.cos(a + math.pi / 2) * width * 0.52
            dy = math.sin(a + math.pi / 2) * width * 0.52
            p.drawLine(QLineF(x - dx, y - dy, x + dx, y + dy))
        p.setPen(QPen(QColor(255, 184, 72, 135), 1.1))
        p.drawArc(QRectF(cx - outer_r + 3, cy - outer_r + 3, (outer_r - 3) * 2, (outer_r - 3) * 2), 24 * 16, 92 * 16)

    elif theme_id == "ice":
        p.setPen(QPen(QColor(235, 255, 255, 155), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for a_deg in (-70, -24, 18, 58, 112, 158, 205, 252):
            a = math.radians(a_deg)
            x1 = cx + math.cos(a) * (inner_r + 1)
            y1 = cy + math.sin(a) * (inner_r + 1)
            x2 = cx + math.cos(a + 0.10) * (outer_r - 2)
            y2 = cy + math.sin(a + 0.10) * (outer_r - 2)
            p.drawLine(QLineF(x1, y1, x2, y2))
        p.setPen(QPen(QColor(126, 231, 255, 135), max(1.5, width * 0.24)))
        p.drawArc(QRectF(cx - outer_r + 2, cy - outer_r + 2, (outer_r - 2) * 2, (outer_r - 2) * 2), 195 * 16, 96 * 16)

    elif theme_id == "lava":
        p.setPen(QPen(QColor(255, 218, 78, 185), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for a_deg in (-36, 18, 78, 132, 210, 286):
            a = math.radians(a_deg)
            p.drawLine(QLineF(
                cx + math.cos(a) * (inner_r + 1),
                cy + math.sin(a) * (inner_r + 1),
                cx + math.cos(a + 0.18) * (outer_r - 2),
                cy + math.sin(a + 0.18) * (outer_r - 2),
            ))
        p.setPen(QPen(QColor(65, 5, 9, 130), max(2.0, width * 0.34)))
        p.drawArc(QRectF(cx - outer_r + 2, cy - outer_r + 2, (outer_r - 2) * 2, (outer_r - 2) * 2), 310 * 16, 88 * 16)

    elif theme_id == "cosmic":
        nebula = QRadialGradient(cx - outer_r * 0.38, cy + outer_r * 0.08, outer_r * 1.2)
        nebula.setColorAt(0.0, QColor(203, 98, 255, 95))
        nebula.setColorAt(0.52, QColor(86, 68, 255, 36))
        nebula.setColorAt(1.0, QColor(86, 68, 255, 0))
        p.fillRect(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2), QBrush(nebula))
        stars = [(-0.46, -0.44, 1.3, 220), (-0.12, -0.60, 1.0, 170), (0.42, -0.30, 1.6, 205),
                 (0.56, 0.15, 1.1, 155), (-0.35, 0.38, 1.5, 210), (0.08, 0.58, 1.0, 180)]
        p.setPen(Qt.PenStyle.NoPen)
        for dx, dy, sr, alpha in stars:
            p.setBrush(QColor(255, 255, 255, alpha))
            p.drawEllipse(QPointF(cx + dx * outer_r, cy + dy * outer_r), sr, sr)

    else:
        p.setPen(QPen(QColor(255, 255, 255, 70), max(1.5, width * 0.22), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for a_deg in (24, 92, 166, 232, 302):
            rect_r = outer_r - width * 0.25
            p.drawArc(QRectF(cx - rect_r, cy - rect_r, rect_r * 2, rect_r * 2), a_deg * 16, 24 * 16)
