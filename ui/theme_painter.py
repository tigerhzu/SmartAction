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
_PREMIUM_RIM_PATH = _ASSET_ROOT / "shared" / "premium_rim.png"
_PREMIUM_RIM_PIXMAP: QPixmap | None = None
_PREMIUM_RIM_LOADED = False
_MAX_PREMIUM_RIM_PIXELS = 768
_PREMIUM_RIM_SCALED: dict[int, QPixmap] = {}


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


def _premium_rim_pixmap() -> QPixmap | None:
    global _PREMIUM_RIM_LOADED, _PREMIUM_RIM_PIXMAP
    if not _PREMIUM_RIM_LOADED:
        _PREMIUM_RIM_PIXMAP = _load_pixmap(
            _PREMIUM_RIM_PATH,
            _MAX_PREMIUM_RIM_PIXELS,
        )
        _PREMIUM_RIM_LOADED = True
        debug_log(
            f"premium rim asset: path={_PREMIUM_RIM_PATH.resolve()} "
            f"exists={_PREMIUM_RIM_PATH.exists()} "
            f"loaded={_PREMIUM_RIM_PIXMAP is not None}"
        )
    return _PREMIUM_RIM_PIXMAP


def _scaled_premium_rim_pixmap(target_pixels: int) -> QPixmap | None:
    """Return a cached size tier to avoid resampling the master every frame."""
    master = _premium_rim_pixmap()
    if master is None:
        return None
    bucket = max(48, min(_MAX_PREMIUM_RIM_PIXELS, int(math.ceil(target_pixels / 32)) * 32))
    cached = _PREMIUM_RIM_SCALED.get(bucket)
    if cached is None:
        cached = master.scaled(
            QSize(bucket, bucket),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        _PREMIUM_RIM_SCALED[bucket] = cached
    return cached


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
        asset_frames = (
            sum(1 for _ in frames_dir.glob("frame_*.png"))
            if frames_dir.exists()
            else 0
        )
        from core.theme import THEMES

        procedural_frames = int(
            THEMES.get(theme_id, {}).get("procedural_frames", 0)
        )
        cached = max(asset_frames, procedural_frames)
        _FRAME_COUNT_CACHE[theme_id] = cached
    return cached


def theme_asset_debug_summary(theme_id: str) -> str:
    base_path = _ASSET_ROOT / theme_id
    frames_path = base_path / "frames"
    frame_count = theme_frame_count(theme_id)
    rim_path = base_path / "rim.png"
    from core.theme import THEMES

    procedural = bool(THEMES.get(theme_id, {}).get("procedural_frames"))
    mode = (
        "animated asset"
        if frames_path.exists() and any(frames_path.glob("frame_*.png"))
        else "static png fallback"
        if rim_path.exists()
        else "procedural animation"
        if procedural
        else "painter fallback"
    )
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
    """Legacy hook retained for compatibility with the Settings card."""
    # The old card bitmaps were built around the retired toy-like rim art.
    # Settings now uses its restrained procedural metal surface for every
    # theme so the premium rim remains the visual focus.
    return False


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


def draw_premium_rim(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    theme_id: str,
    *,
    frame_index: int = 0,
    rim_width: float | None = None,
    opacity: float = 1.0,
    energy_strength: float = 1.0,
) -> bool:
    """Composite the shared obsidian-metal material with live theme energy."""
    main, dark, highlight, glow = _theme_colors(theme_id)
    rim_w = rim_width if rim_width is not None else outer_r * 0.30
    inner_r = max(3.0, outer_r - rim_w)
    phase = (frame_index % 120) / 120.0

    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    for grow, alpha in (
        (outer_r * 0.16, int(24 * energy_strength)),
        (outer_r * 0.08, int(46 * energy_strength)),
        (outer_r * 0.025, int(72 * energy_strength)),
    ):
        bloom = QRadialGradient(cx, cy, outer_r + grow)
        bloom.setColorAt(0.56, QColor(glow.red(), glow.green(), glow.blue(), 0))
        bloom.setColorAt(0.83, QColor(glow.red(), glow.green(), glow.blue(), alpha))
        bloom.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
        p.setBrush(QBrush(bloom))
        p.drawEllipse(QPointF(cx, cy), outer_r + grow, outer_r + grow)

    # The source art has generous padding. A 1.15 target expansion aligns its
    # actual metal silhouette with outer_r while retaining antialiased edges.
    draw_r = outer_r * 1.15
    try:
        device_ratio = max(1.0, float(p.device().devicePixelRatioF()))
    except (AttributeError, TypeError):
        device_ratio = 1.0
    pixmap = _scaled_premium_rim_pixmap(
        int(math.ceil(draw_r * 2.0 * device_ratio * 1.35))
    )
    if pixmap is None:
        p.restore()
        return False
    target = QRectF(cx - draw_r, cy - draw_r, draw_r * 2.0, draw_r * 2.0)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    p.setOpacity(max(0.0, min(1.0, opacity)))
    p.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
    p.setOpacity(1.0)

    energy_ring = _annulus(cx, cy, outer_r * 0.985, inner_r)
    energy = QConicalGradient(QPointF(cx, cy), phase * -360.0)
    energy.setColorAt(0.00, QColor(highlight.red(), highlight.green(), highlight.blue(), 190))
    energy.setColorAt(0.12, QColor(main.red(), main.green(), main.blue(), 35))
    energy.setColorAt(0.32, QColor(dark.red(), dark.green(), dark.blue(), 18))
    energy.setColorAt(0.50, QColor(main.red(), main.green(), main.blue(), 150))
    energy.setColorAt(0.68, QColor(dark.red(), dark.green(), dark.blue(), 16))
    energy.setColorAt(0.86, QColor(main.red(), main.green(), main.blue(), 92))
    energy.setColorAt(1.00, QColor(highlight.red(), highlight.green(), highlight.blue(), 190))
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
    p.setOpacity(max(0.0, min(1.0, 0.58 * energy_strength * opacity)))
    p.fillPath(energy_ring, QBrush(energy))
    p.setOpacity(1.0)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

    arc_rect = QRectF(
        cx - outer_r * 0.94,
        cy - outer_r * 0.94,
        outer_r * 1.88,
        outer_r * 1.88,
    )
    for offset, span, color, width in (
        (0, 54, highlight, 1.15),
        (137, 36, main, 1.55),
        (246, 72, highlight, 0.75),
    ):
        arc_color = QColor(color)
        arc_color.setAlpha(int(min(235, 155 * energy_strength * opacity)))
        p.setPen(
            QPen(
                arc_color,
                max(0.7, width * outer_r / 30.0),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        start = int((phase * 360.0 + offset) * 16)
        p.drawArc(arc_rect, start, span * 16)

    p.setPen(Qt.PenStyle.NoPen)
    for index in range(6):
        angle = phase * math.tau + index * math.tau / 6.0
        radius = outer_r * (0.93 + (index % 2) * 0.045)
        node = max(0.8, outer_r * 0.028)
        color = QColor(highlight if index % 2 == 0 else main)
        color.setAlpha(int(min(235, 190 * energy_strength * opacity)))
        p.setBrush(color)
        p.drawEllipse(
            QPointF(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius),
            node,
            node,
        )
    p.restore()
    return True


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
    ornaments: bool = True,
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

    if draw_premium_rim(
        p,
        cx,
        cy,
        outer_r,
        theme_id,
        frame_index=frame_index,
        rim_width=rim_w,
        opacity=1.0,
        energy_strength=1.2 if hovered or selected else 0.88,
    ):
        ring = _annulus(cx, cy, outer_r * 0.97, inner_r)
        p.save()
        p.setClipPath(ring)
        _draw_rim_texture(p, cx, cy, outer_r, inner_r, theme_id)
        p.restore()
        _draw_inner_glass(
            p,
            cx,
            cy,
            outer_r,
            inner_r,
            highlight,
            hovered,
            selected,
            inner_fill,
        )
        if ornaments:
            _draw_theme_effect(p, cx, cy, outer_r, theme_id, frame_index)
        return

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
    if ornaments:
        _draw_theme_effect(p, cx, cy, outer_r, theme_id, frame_index)


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

    elif theme_id == "halloween":
        p.setPen(QPen(QColor(255, 183, 77, 185), max(1.2, width * 0.20),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        rune_r = (outer_r + inner_r) * 0.5
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            tangent = a + math.pi / 2
            x = cx + math.cos(a) * rune_r
            y = cy + math.sin(a) * rune_r
            half = width * 0.23
            p.drawLine(QLineF(
                x - math.cos(tangent) * half,
                y - math.sin(tangent) * half,
                x + math.cos(tangent) * half,
                y + math.sin(tangent) * half,
            ))

    elif theme_id == "kawaii":
        p.setPen(Qt.PenStyle.NoPen)
        for angle, color in zip(
            range(0, 360, 45),
            (QColor(255, 246, 251, 210), QColor(255, 177, 213, 190)) * 4,
        ):
            a = math.radians(angle)
            dot_r = (outer_r + inner_r) * 0.5
            p.setBrush(color)
            p.drawEllipse(
                QPointF(cx + math.cos(a) * dot_r, cy + math.sin(a) * dot_r),
                max(1.0, width * 0.12),
                max(1.0, width * 0.12),
            )

    elif theme_id == "sakura":
        p.setPen(QPen(QColor(255, 234, 238, 180), max(1.0, width * 0.16),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        arc = QRectF(cx - outer_r + 2, cy - outer_r + 2,
                     (outer_r - 2) * 2, (outer_r - 2) * 2)
        for angle in (8, 80, 152, 224, 296):
            p.drawArc(arc, angle * 16, 30 * 16)

    elif theme_id == "cyber":
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc = QRectF(cx - outer_r + 2, cy - outer_r + 2,
                     (outer_r - 2) * 2, (outer_r - 2) * 2)
        for angle, color in (
            (4, QColor(103, 232, 249, 220)),
            (94, QColor(217, 70, 239, 210)),
            (184, QColor(103, 232, 249, 220)),
            (274, QColor(217, 70, 239, 210)),
        ):
            p.setPen(QPen(color, max(1.5, width * 0.25),
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            p.drawArc(arc, angle * 16, 48 * 16)

    elif theme_id == "ocean":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(186, 251, 242, 150), max(1.0, width * 0.15),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for inset, start in ((2.0, 188), (4.5, 18)):
            arc_r = outer_r - inset
            p.drawArc(
                QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2),
                start * 16,
                116 * 16,
            )

    else:
        p.setPen(QPen(QColor(255, 255, 255, 70), max(1.5, width * 0.22), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for a_deg in (24, 92, 166, 232, 302):
            rect_r = outer_r - width * 0.25
            p.drawArc(QRectF(cx - rect_r, cy - rect_r, rect_r * 2, rect_r * 2), a_deg * 16, 24 * 16)


def _draw_theme_effect(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    theme_id: str,
    frame_index: int,
    *,
    scene: bool = False,
) -> None:
    """Paint theme-specific animated ornaments over the shared material."""
    phase = (frame_index % 120) / 120.0
    if theme_id in {"tiger", "purple", "ice", "lava", "cosmic"}:
        _draw_orbiting_motes(p, cx, cy, outer_r, phase, theme_id, scene=scene)
    elif theme_id == "halloween":
        _draw_orbiting_ghosts(p, cx, cy, outer_r, phase, scene=scene)
    elif theme_id == "kawaii":
        _draw_orbiting_hearts(p, cx, cy, outer_r, phase, scene=scene)
    elif theme_id == "sakura":
        _draw_orbiting_petals(p, cx, cy, outer_r, phase, scene=scene)
    elif theme_id == "cyber":
        _draw_cyber_nodes(p, cx, cy, outer_r, phase, scene=scene)
    elif theme_id == "ocean":
        _draw_orbiting_sharks(p, cx, cy, outer_r, phase, scene=scene)


def draw_theme_orbit(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    theme_id: str,
    frame_index: int,
) -> None:
    """Draw the premium scene-scale ring behind all action bubbles."""
    if theme_id == "ocean":
        draw_ocean_wave_orbit(p, cx, cy, outer_r, frame_index)
        return

    draw_premium_rim(
        p,
        cx,
        cy,
        outer_r,
        theme_id,
        frame_index=frame_index,
        rim_width=outer_r * 0.28,
        opacity=0.34,
        energy_strength=0.62,
    )
    main, _dark, highlight, _glow = _theme_colors(theme_id)
    phase = (frame_index % 120) / 120.0
    p.save()
    p.setBrush(Qt.BrushStyle.NoBrush)
    for radius_scale, alpha, width, speed in (
        (0.80, 42, 0.75, -1.0),
        (0.91, 88, 1.05, 1.0),
        (1.02, 58, 0.85, -0.6),
    ):
        radius = outer_r * radius_scale
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        color = QColor(main if speed > 0 else highlight)
        color.setAlpha(alpha)
        p.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        start = int((phase * speed * 360.0 + radius_scale * 113.0) * 16)
        p.drawArc(rect, start, 92 * 16)
        p.drawArc(rect, start + 180 * 16, 38 * 16)
    p.restore()
    _draw_theme_effect(
        p,
        cx,
        cy,
        outer_r,
        theme_id,
        frame_index,
        scene=True,
    )


def _ocean_wave_radius(
    radius: float,
    angle: float,
    phase: float,
    amplitude: float,
    *,
    detail: float = 1.0,
) -> float:
    """Return a layered, seamless wave profile around a circular orbit."""
    return radius + amplitude * (
        math.sin(angle * 11.0 - phase * math.tau * 0.32)
        + math.sin(angle * 23.0 + phase * math.tau * 0.18 + 0.72)
        * 0.24
        * detail
        + math.sin(angle * 5.0 + phase * math.tau * 0.11 + 1.4)
        * 0.18
    )


def _ocean_wave_path(
    cx: float,
    cy: float,
    radius: float,
    phase: float,
    amplitude: float,
    *,
    detail: float = 1.0,
    samples: int = 180,
) -> QPainterPath:
    path = QPainterPath()
    for index in range(samples + 1):
        angle = math.tau * index / samples
        wave_r = _ocean_wave_radius(
            radius,
            angle,
            phase,
            amplitude,
            detail=detail,
        )
        point = QPointF(
            cx + math.cos(angle) * wave_r,
            cy + math.sin(angle) * wave_r,
        )
        if index == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)
    path.closeSubpath()
    return path


def _ocean_wave_band(
    cx: float,
    cy: float,
    outer_radius: float,
    inner_radius: float,
    phase: float,
) -> QPainterPath:
    outer = _ocean_wave_path(
        cx,
        cy,
        outer_radius,
        phase,
        7.2,
        samples=192,
    )
    inner = _ocean_wave_path(
        cx,
        cy,
        inner_radius,
        phase + 0.16,
        3.4,
        detail=0.55,
        samples=192,
    )
    band = QPainterPath()
    band.setFillRule(Qt.FillRule.OddEvenFill)
    band.addPath(outer)
    band.addPath(inner)
    return band


def _draw_ocean_foam(
    p: QPainter,
    cx: float,
    cy: float,
    radius: float,
    phase: float,
) -> None:
    """Paint broken foam caps so the orbit reads as water, not a neon ring."""
    crest_offset = phase * math.tau * 0.32
    p.setBrush(Qt.BrushStyle.NoBrush)
    for crest in range(11):
        center_angle = (math.pi / 2 + crest_offset + math.tau * crest) / 11.0
        foam = QPainterPath()
        for step in range(13):
            angle = center_angle + (step / 12.0 - 0.5) * 0.20
            wave_r = _ocean_wave_radius(radius, angle, phase, 7.2)
            wave_r += math.sin(step / 12.0 * math.pi) * 1.6
            point = QPointF(
                cx + math.cos(angle) * wave_r,
                cy + math.sin(angle) * wave_r,
            )
            if step == 0:
                foam.moveTo(point)
            else:
                foam.lineTo(point)
        alpha = 186 if crest % 3 == 0 else 142
        p.setPen(
            QPen(
                QColor(218, 255, 252, alpha),
                2.1 if crest % 3 == 0 else 1.45,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        p.drawPath(foam)

        if crest % 2 == 0:
            droplet_angle = center_angle + 0.035
            droplet_r = (
                _ocean_wave_radius(radius, droplet_angle, phase, 7.2) + 5.0
            )
            droplet = QPointF(
                cx + math.cos(droplet_angle) * droplet_r,
                cy + math.sin(droplet_angle) * droplet_r,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(194, 255, 251, 125))
            p.drawEllipse(droplet, 1.25, 1.25)
            p.setBrush(Qt.BrushStyle.NoBrush)


def draw_ocean_wave_orbit(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    frame_index: int,
) -> None:
    """Render two translucent swells with deep-sea sharks riding the crest."""
    phase = (frame_index % 120) / 120.0
    wave_outer = outer_r + 1.5
    wave_inner = outer_r - 22.0
    band = _ocean_wave_band(cx, cy, wave_outer, wave_inner, phase)
    back_phase = (phase * 0.57 + 0.21) % 1.0
    back_outer = outer_r - 5.0
    back_inner = outer_r - 27.0
    back_band = _ocean_wave_band(
        cx,
        cy,
        back_outer,
        back_inner,
        back_phase,
    )

    p.save()
    p.setPen(Qt.PenStyle.NoPen)

    # The rear swell moves more slowly, creating inexpensive parallax depth.
    rear_water = QRadialGradient(cx, cy, back_outer + 12.0)
    rear_water.setColorAt(0.0, QColor(0, 15, 35, 0))
    rear_water.setColorAt(0.75, QColor(1, 35, 69, 118))
    rear_water.setColorAt(0.90, QColor(5, 90, 120, 146))
    rear_water.setColorAt(1.0, QColor(46, 166, 172, 126))
    p.setBrush(QBrush(rear_water))
    p.drawPath(back_band)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(
        QPen(
            QColor(56, 186, 188, 62),
            1.25,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    p.drawPath(
        _ocean_wave_path(
            cx,
            cy,
            back_outer - 2.0,
            back_phase,
            5.3,
            detail=0.72,
            samples=160,
        )
    )

    glow_path = _ocean_wave_path(
        cx,
        cy,
        wave_outer - 1.0,
        phase,
        7.6,
        samples=192,
    )
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(
        QPen(
            QColor(31, 215, 214, 24),
            18.0,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    p.drawPath(glow_path)

    water = QRadialGradient(cx, cy, wave_outer + 12.0)
    water.setColorAt(0.0, QColor(1, 22, 43, 0))
    water.setColorAt(0.78, QColor(3, 43, 78, 188))
    water.setColorAt(0.88, QColor(5, 102, 137, 207))
    water.setColorAt(0.95, QColor(18, 169, 179, 194))
    water.setColorAt(1.0, QColor(146, 246, 235, 174))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(water))
    p.drawPath(band)

    # Sub-surface currents give the water depth without recreating a rigid rim.
    for inset, alpha, width, speed_offset in (
        (7.0, 104, 1.15, 0.06),
        (13.5, 68, 0.85, 0.18),
    ):
        current = _ocean_wave_path(
            cx,
            cy,
            wave_outer - inset,
            phase + speed_offset,
            2.4,
            detail=0.45,
            samples=160,
        )
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(93, 230, 225, alpha),
                width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        p.drawPath(current)

    # Sharks sit directly on the swell; the final foam pass overlaps them.
    _draw_orbiting_sharks(
        p,
        cx,
        cy,
        wave_outer,
        phase,
        scene=True,
        wave_riding=True,
    )
    _draw_ocean_foam(p, cx, cy, wave_outer, phase)
    p.restore()


def draw_jelly_button(
    p: QPainter,
    cx: float,
    cy: float,
    radius: float,
    base: QColor,
    *,
    hovered: bool = False,
) -> None:
    """Draw a simple polished jelly button in the supplied accent color."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)

    shadow = QRadialGradient(cx, cy + radius * 0.34, radius * 1.32)
    shadow.setColorAt(0.0, QColor(0, 18, 35, 105 if hovered else 82))
    shadow.setColorAt(0.72, QColor(0, 18, 35, 42 if hovered else 28))
    shadow.setColorAt(1.0, QColor(0, 18, 35, 0))
    p.setBrush(QBrush(shadow))
    p.drawEllipse(
        QPointF(cx, cy + radius * 0.20),
        radius * 1.34,
        radius * 1.34,
    )

    aura = QColor(base).lighter(150)
    aura.setAlpha(66 if hovered else 36)
    p.setBrush(aura)
    p.drawEllipse(QPointF(cx, cy), radius + 2.8, radius + 2.8)

    button_path = QPainterPath()
    button_path.addEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
    body = QLinearGradient(
        cx - radius * 0.65,
        cy - radius,
        cx + radius * 0.55,
        cy + radius,
    )
    top = QColor(base).lighter(150 if hovered else 138)
    middle = QColor(base).lighter(112 if hovered else 102)
    bottom = QColor(base).darker(145)
    top.setAlpha(238)
    middle.setAlpha(230)
    bottom.setAlpha(244)
    body.setColorAt(0.0, top)
    body.setColorAt(0.48, middle)
    body.setColorAt(1.0, bottom)
    p.setBrush(QBrush(body))
    p.drawPath(button_path)

    p.save()
    p.setClipPath(button_path)
    gloss = QRadialGradient(
        cx - radius * 0.38,
        cy - radius * 0.52,
        radius * 1.10,
    )
    gloss.setColorAt(0.0, QColor(255, 255, 255, 154))
    gloss.setColorAt(0.32, QColor(232, 255, 253, 68))
    gloss.setColorAt(0.72, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(gloss))
    p.drawEllipse(QPointF(cx, cy), radius, radius)

    lower_glow = QLinearGradient(cx, cy, cx, cy + radius)
    lower_glow.setColorAt(0.0, QColor(13, 67, 91, 0))
    lower_glow.setColorAt(1.0, QColor(2, 33, 58, 118))
    p.setBrush(QBrush(lower_glow))
    p.drawEllipse(QPointF(cx, cy + radius * 0.18), radius, radius)
    p.restore()

    p.setBrush(Qt.BrushStyle.NoBrush)
    edge = QColor(base).lighter(205)
    edge.setAlpha(224 if hovered else 174)
    p.setPen(QPen(edge, 1.45 if hovered else 1.05))
    p.drawEllipse(QPointF(cx, cy), radius - 0.55, radius - 0.55)
    p.setPen(
        QPen(
            QColor(255, 255, 255, 142 if hovered else 104),
            1.3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
    )
    shine_rect = QRectF(
        cx - radius * 0.70,
        cy - radius * 0.70,
        radius * 1.40,
        radius * 1.40,
    )
    p.drawArc(shine_rect, 44 * 16, 88 * 16)
    p.restore()


def _draw_orbiting_motes(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    theme_id: str,
    *,
    scene: bool,
) -> None:
    palettes = {
        "tiger": (QColor(255, 158, 48), QColor(255, 225, 156)),
        "purple": (QColor(174, 104, 255), QColor(232, 211, 255)),
        "ice": (QColor(108, 225, 255), QColor(239, 255, 255)),
        "lava": (QColor(255, 79, 24), QColor(255, 224, 87)),
        "cosmic": (QColor(117, 96, 255), QColor(255, 193, 255)),
    }
    primary, secondary = palettes[theme_id]
    count = 16 if scene else 5
    size = max(1.2, outer_r * (0.022 if scene else 0.052))
    for index in range(count):
        local_phase = phase * (0.62 + (index % 3) * 0.055)
        radius = outer_r * (0.92 + (index % 4) * 0.035)
        x, y, angle = _orbit_point(
            cx,
            cy,
            radius,
            local_phase,
            index * math.tau / count,
        )
        color = QColor(primary if index % 3 else secondary)
        color.setAlpha(130 + (index % 4) * 25)
        tangent = math.radians(angle)
        trail = size * (3.8 if scene else 2.2)
        trail_color = QColor(color)
        trail_color.setAlpha(color.alpha() // 3)
        p.setPen(QPen(trail_color, max(0.55, size * 0.42),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QLineF(
            x - math.cos(tangent) * trail,
            y - math.sin(tangent) * trail,
            x,
            y,
        ))
        p.save()
        p.translate(x, y)
        p.rotate(angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        if theme_id == "ice":
            shard = QPainterPath()
            shard.moveTo(0, -size * 1.8)
            shard.lineTo(size * 0.65, 0)
            shard.lineTo(0, size * 1.8)
            shard.lineTo(-size * 0.65, 0)
            shard.closeSubpath()
            p.drawPath(shard)
        elif theme_id == "tiger":
            p.drawRoundedRect(QRectF(-size * 1.8, -size * 0.38,
                                     size * 3.6, size * 0.76), size * 0.3, size * 0.3)
        elif theme_id == "cosmic":
            p.drawEllipse(QPointF(), size, size)
            p.setPen(QPen(secondary, max(0.45, size * 0.32)))
            p.drawLine(QLineF(-size * 2.1, 0, size * 2.1, 0))
            p.drawLine(QLineF(0, -size * 2.1, 0, size * 2.1))
        else:
            p.drawEllipse(QPointF(), size * 1.15, size * 0.72)
        p.restore()


def _orbit_point(
    cx: float,
    cy: float,
    radius: float,
    phase: float,
    offset: float,
) -> tuple[float, float, float]:
    angle = phase * math.tau + offset
    return (
        cx + math.cos(angle) * radius,
        cy + math.sin(angle) * radius,
        math.degrees(angle) + 90.0,
    )


def _draw_orbiting_ghosts(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    *,
    scene: bool,
) -> None:
    count = 7 if scene else 3
    size = max(5.8, outer_r * (0.085 if scene else 0.23))
    for index in range(count):
        x, y, angle = _orbit_point(
            cx,
            cy,
            outer_r * (0.97 + (index % 2) * 0.045),
            phase * (0.72 if scene else 1.0),
            index * math.tau / count,
        )
        y += math.sin(phase * math.tau * 3 + index) * 1.1
        p.save()
        p.translate(x, y)
        p.rotate(angle * 0.08)
        p.scale(size, size)
        ghost = QPainterPath()
        ghost.moveTo(-0.62, 0.48)
        ghost.lineTo(-0.62, -0.04)
        ghost.cubicTo(-0.62, -0.72, -0.30, -1.00, 0.0, -1.00)
        ghost.cubicTo(0.32, -1.00, 0.62, -0.70, 0.62, -0.04)
        ghost.lineTo(0.62, 0.48)
        ghost.cubicTo(0.42, 0.24, 0.22, 0.70, 0.0, 0.44)
        ghost.cubicTo(-0.22, 0.70, -0.42, 0.24, -0.62, 0.48)
        ghost.closeSubpath()
        aura = QPainterPath(ghost)
        p.save()
        p.scale(1.18, 1.18)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(139, 74, 255, 48))
        p.drawPath(aura)
        p.restore()
        ghost_fill = QLinearGradient(0.0, -1.0, 0.0, 0.7)
        ghost_fill.setColorAt(0.0, QColor(247, 241, 255, 238))
        ghost_fill.setColorAt(0.48, QColor(180, 143, 242, 224))
        ghost_fill.setColorAt(1.0, QColor(89, 50, 150, 132))
        p.setPen(QPen(QColor(205, 174, 255, 205), 0.08))
        p.setBrush(QBrush(ghost_fill))
        p.drawPath(ghost)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(52, 22, 72, 225))
        p.drawEllipse(QPointF(-0.22, -0.32), 0.09, 0.14)
        p.drawEllipse(QPointF(0.22, -0.32), 0.09, 0.14)
        p.restore()


def _heart_path() -> QPainterPath:
    heart = QPainterPath()
    heart.moveTo(0.0, 0.72)
    heart.cubicTo(-0.18, 0.50, -0.72, 0.14, -0.72, -0.25)
    heart.cubicTo(-0.72, -0.74, -0.15, -0.82, 0.0, -0.46)
    heart.cubicTo(0.15, -0.82, 0.72, -0.74, 0.72, -0.25)
    heart.cubicTo(0.72, 0.14, 0.18, 0.50, 0.0, 0.72)
    heart.closeSubpath()
    return heart


def _draw_orbiting_hearts(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    *,
    scene: bool,
) -> None:
    heart = _heart_path()
    colors = (
        QColor(255, 240, 247, 238),
        QColor(255, 119, 178, 235),
        QColor(255, 211, 89, 230),
    )
    count = 9 if scene else 3
    for index in range(count):
        color = colors[index % len(colors)]
        x, y, angle = _orbit_point(
            cx, cy, outer_r * (0.98 + (index % 2) * 0.05),
            phase * 0.72, index * math.tau / count,
        )
        size = max(3.4, outer_r * (0.052 if scene else 0.18))
        pulse = 1.0 + math.sin(phase * math.tau * 2 + index) * 0.10
        p.save()
        p.translate(x, y)
        p.rotate(angle)
        p.scale(size * pulse, size * pulse)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color.red(), color.green(), color.blue(), 42))
        p.save()
        p.scale(1.35, 1.35)
        p.drawPath(heart)
        p.restore()
        heart_fill = QLinearGradient(-0.52, -0.65, 0.48, 0.70)
        heart_fill.setColorAt(0.0, color.lighter(138))
        heart_fill.setColorAt(0.45, color)
        heart_fill.setColorAt(1.0, color.darker(142))
        p.setPen(QPen(QColor(255, 238, 248, 190), 0.075))
        p.setBrush(QBrush(heart_fill))
        p.drawPath(heart)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 150))
        p.drawEllipse(QPointF(-0.29, -0.35), 0.105, 0.07)
        p.restore()


def _petal_path() -> QPainterPath:
    petal = QPainterPath()
    petal.moveTo(0.0, -0.90)
    petal.cubicTo(0.68, -0.50, 0.58, 0.38, 0.0, 0.82)
    petal.cubicTo(-0.58, 0.38, -0.68, -0.50, 0.0, -0.90)
    petal.closeSubpath()
    return petal


def _draw_orbiting_petals(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    *,
    scene: bool,
) -> None:
    petal = _petal_path()
    count = 13 if scene else 5
    for index in range(count):
        local_phase = phase * (0.46 + index * 0.035)
        x, y, angle = _orbit_point(
            cx, cy, outer_r * (0.96 + (index % 2) * 0.13),
            local_phase, index * math.tau / count,
        )
        size = max(3.4, outer_r * (0.045 if scene else 0.16))
        p.save()
        p.translate(x, y)
        p.rotate(angle + phase * 240 + index * 37)
        p.scale(size * 0.72, size)
        p.setPen(QPen(QColor(176, 62, 91, 130), 0.10))
        petal_fill = QLinearGradient(-0.6, -0.8, 0.45, 0.75)
        petal_fill.setColorAt(0.0, QColor(255, 250, 252, 245))
        petal_fill.setColorAt(
            0.48,
            QColor(255, 218 + (index % 2) * 17, 229, 225),
        )
        petal_fill.setColorAt(1.0, QColor(184, 70, 103, 185))
        p.setBrush(QBrush(petal_fill))
        p.drawPath(petal)
        p.setPen(QPen(QColor(255, 255, 255, 130), 0.06))
        p.drawLine(QLineF(0.0, -0.60, 0.0, 0.50))
        p.restore()


def _draw_cyber_nodes(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    *,
    scene: bool,
) -> None:
    arc_r = outer_r * 1.03
    arc = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
    rotation = int(phase * 360)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for index, color in enumerate((QColor(90, 240, 255, 225), QColor(235, 77, 255, 220))):
        p.setPen(QPen(color, max(1.2, outer_r * 0.055),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
        p.drawArc(arc, (rotation + index * 180) * 16, 58 * 16)
    count = 10 if scene else 4
    for index in range(count):
        x, y, angle = _orbit_point(
            cx, cy, outer_r * 1.03, phase, index * math.tau / count
        )
        node = max(2.0, outer_r * (0.025 if scene else 0.085))
        p.save()
        p.translate(x, y)
        p.rotate(angle)
        p.setPen(QPen(QColor(4, 30, 40, 220), 0.7))
        p.setBrush(QColor(116, 247, 255, 235) if index % 2 == 0 else QColor(236, 72, 255, 235))
        p.drawRect(QRectF(-node, -node, node * 2, node * 2))
        p.restore()


def _shark_paths() -> tuple[QPainterPath, QPainterPath, QPainterPath]:
    body = QPainterPath()
    body.moveTo(1.00, 0.0)
    body.cubicTo(0.58, -0.42, -0.12, -0.43, -0.62, -0.13)
    body.lineTo(-1.00, -0.52)
    body.lineTo(-0.82, 0.0)
    body.lineTo(-1.00, 0.52)
    body.lineTo(-0.62, 0.13)
    body.cubicTo(-0.12, 0.43, 0.58, 0.42, 1.00, 0.0)
    body.closeSubpath()

    dorsal = QPainterPath()
    dorsal.moveTo(-0.25, -0.30)
    dorsal.lineTo(0.02, -0.88)
    dorsal.lineTo(0.30, -0.28)
    dorsal.closeSubpath()

    fin = QPainterPath()
    fin.moveTo(0.02, 0.22)
    fin.lineTo(0.36, 0.72)
    fin.lineTo(0.48, 0.17)
    fin.closeSubpath()
    return body, dorsal, fin


def _draw_orbiting_sharks(
    p: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    phase: float,
    *,
    scene: bool,
    wave_riding: bool = False,
) -> None:
    body, dorsal, fin = _shark_paths()
    colors = (
        (QColor(27, 105, 130, 232), QColor(2, 37, 67, 244)),
        (QColor(34, 91, 128, 224), QColor(4, 32, 73, 240)),
        (QColor(18, 121, 133, 218), QColor(1, 45, 66, 240)),
    )
    count = 3 if scene and wave_riding else 4 if scene else 2
    for index in range(count):
        body_color, fin_color = colors[index % len(colors)]
        local_phase = phase * (0.54 + index * 0.07)
        radius_scale = (
            0.992 + index * 0.025
            if scene and wave_riding
            else 1.00 + index * 0.07
        )
        x, y, angle = _orbit_point(
            cx,
            cy,
            outer_r * radius_scale,
            local_phase,
            index * math.tau / count,
        )
        if scene:
            size = max(
                13.0,
                outer_r
                * (
                    0.125 - (index % 2) * 0.012
                    if wave_riding
                    else 0.115 - (index % 2) * 0.014
                ),
            )
        else:
            size = max(7.2, outer_r * (0.30 if index == 0 else 0.24))
        p.save()
        p.translate(x, y)
        p.rotate(angle)
        p.scale(size, size)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(52, 207, 209, 28 if wave_riding else 42))
        p.save()
        p.scale(1.20, 1.25)
        p.drawPath(body)
        p.restore()
        shark_fill = QLinearGradient(-0.75, -0.45, 0.72, 0.38)
        shark_fill.setColorAt(0.0, fin_color.darker(122))
        shark_fill.setColorAt(0.45, body_color)
        shark_fill.setColorAt(1.0, body_color.lighter(132))
        p.setPen(
            QPen(
                QColor(132, 231, 229, 118 if wave_riding else 205),
                0.065 if wave_riding else 0.075,
            )
        )
        p.setBrush(QBrush(shark_fill))
        p.drawPath(body)
        p.setBrush(fin_color)
        p.drawPath(dorsal)
        p.drawPath(fin)
        p.setPen(Qt.PenStyle.NoPen)
        if not wave_riding:
            p.setBrush(QColor(245, 255, 252, 245))
            p.drawEllipse(QPointF(0.57, -0.12), 0.075, 0.075)
            p.setBrush(QColor(3, 30, 45, 245))
            p.drawEllipse(QPointF(0.59, -0.12), 0.035, 0.035)
        p.restore()

        # A tiny wake makes the direction of travel readable without adding
        # bitmap animation frames or much paint cost.
        wake_angle = math.radians(angle)
        tail_x = x - math.cos(wake_angle) * size * 1.15
        tail_y = y - math.sin(wake_angle) * size * 1.15
        p.setBrush(QColor(190, 252, 245, 30))
        for bubble_index, bubble_size in enumerate((1.8, 1.2)):
            bx = tail_x - math.cos(wake_angle) * bubble_index * size * 0.45
            by = tail_y - math.sin(wake_angle) * bubble_index * size * 0.45
            p.setPen(QPen(QColor(191, 255, 248, 190), 0.75))
            p.drawEllipse(QPointF(bx, by), bubble_size, bubble_size)
