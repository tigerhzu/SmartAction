"""
Radial Action Ring overlay — themed floating-slot design.

Visual features
---------------
- Gradient-filled slot circles with inner rim highlight (glassmorphism feel)
- Thin connecting lines between adjacent occupied slots
- Enlarged emoji inside slots (24 px pixel size); short text labels at 13 px
- Five swappable themes via core.theme
- Floating white label cards outside each occupied slot
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEasingCurve,
    QLineF,
    QParallelAnimationGroup,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from core.debug_log import debug_log
from core.theme import DEFAULT_THEME, THEMES
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    FOG,
    HEADLINE_FONT_FAMILY,
    NEON_CYAN,
    RING_LABEL_BG,
    RING_LABEL_EDGE,
    STEEL,
    VOID,
)
from ui.theme_painter import draw_energy_bubble, preload_theme_assets, theme_frame_count

if TYPE_CHECKING:
    from core.menu_model import MenuItem

# ── Geometry ──────────────────────────────────────────────────────────────────

ITEM_RADIUS   = 28      # slot circle radius (px)
ITEM_ORBIT    = 112     # distance from window centre → slot centre
NUM_SLOTS     = 8
CENTER_RADIUS = 18      # centre close / back button radius

_LABEL_H      = 30      # label card height
_LABEL_R      = 6       # label card corner radius
_LABEL_PADX   = 12      # horizontal text padding inside card
_LABEL_MAX_W  = 154     # max card width before truncation
_LABEL_GAP    = 12      # gap between slot edge and near card edge
_HIT_PADDING  = 12      # forgiving click target padding for labels / buttons

WINDOW_SIZE   = 460
MIN_WINDOW_SIZE = 300

# ── Fixed colours (not theme-dependent) ──────────────────────────────────────

_C_ABBREV    = QColor(BONE)                  # text / emoji inside slot
_C_CHEVRON   = QColor(EMBER_HOVER)           # folder chevron
_C_CTR_ICO   = QColor(BONE)                  # centre-button icon (normal)
_C_CTR_ICO_H = QColor(NEON_CYAN)             # centre-button icon (hovered)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_emoji(text: str) -> bool:
    """Return True when the first character is non-ASCII (likely an emoji)."""
    return bool(text) and ord(text[0]) > 127


def _abbrev(label: str) -> str:
    """Return a 1-2 char abbreviation for an unlabelled slot."""
    label = label.strip()
    if not label:
        return "?"
    if len(label) <= 3 and label.isupper():
        return label
    words = label.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    uppers = [ch for ch in label if ch.isupper()]
    if len(uppers) >= 2:
        return "".join(uppers[:2])
    return label[:2].upper()


# ── Ring window ───────────────────────────────────────────────────────────────

class RingWindow(QWidget):
    """
    Frameless translucent radial menu — themed floating-slot design.

    _nav_stack[-1] is the current item list.
    Clicking a folder pushes its children; centre button pops (or closes).

    Signals
    -------
    item_activated(MenuItem) — emitted when a leaf item is clicked.
    """

    item_activated = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nav_stack: list[list[MenuItem]] = []
        self._scale: float = 0.85
        self._hovered_slot: int = -1
        self._center_hovered: bool = False
        self._theme_frame: int = 0
        self._ring_container_rect = QRectF(0, 0, WINDOW_SIZE, WINDOW_SIZE)
        self._outside_click_enabled: bool = False
        self._is_dismissing: bool = False
        self._pressed_inside_ring: bool = False
        self._ignore_next_click: bool = False
        self._active_action: int | None = None

        self._setup_window()
        self._build_fonts()
        self._build_animations()
        self._build_theme_timer()
        self._apply_theme(DEFAULT_THEME)   # default; overridden in show_at_cursor

    # ── Window config ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def _build_fonts(self) -> None:
        self._font_abbrev = QFont(HEADLINE_FONT_FAMILY)
        self._font_abbrev.setPixelSize(14)
        self._font_abbrev.setBold(True)

        # Enlarged emoji font — 24 px fits comfortably inside a 56 px slot
        self._font_emoji = QFont()
        self._font_emoji.setPixelSize(24)

        self._font_label = QFont()
        self._font_label.setPixelSize(12)
        self._font_label.setWeight(QFont.Weight.DemiBold)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, theme_id: str) -> None:
        self._theme_id = theme_id
        preload_theme_assets(theme_id)
        self._theme_frame = 0
        t = THEMES.get(theme_id, THEMES[DEFAULT_THEME])

        def c(*rgba: int) -> QColor:
            return QColor(*rgba)

        self._c_slot     = c(*t["slot"])
        self._c_slot_h   = c(*t["slot_h"])
        self._c_folder   = c(*t["folder"])
        self._c_folder_h = c(*t["folder_h"])
        self._c_glow     = c(*t["glow"])
        self._c_shadow   = c(*t["shadow"])
        self._c_center   = c(*t["center"])
        self._c_center_x = c(*t["center_x"])
        self._c_center_b = c(*t["center_b"])
        self._c_rim      = c(*t["rim"])
        self._c_line     = c(*t["line"])
        self._c_empty    = c(*t["empty"])
        self._c_card_bg  = c(*t["card_bg"])
        self._c_card_txt = c(*t["card_text"])
        self._c_card_sh  = c(*t["card_shadow"])

    # ── Animations ────────────────────────────────────────────────────────────

    def _build_animations(self) -> None:
        self._anim_open = QParallelAnimationGroup(self)

        self._anim_opacity = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim_opacity.setDuration(180)
        self._anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_open.addAnimation(self._anim_opacity)

        self._anim_scale = QVariantAnimation(self)
        self._anim_scale.setDuration(200)
        self._anim_scale.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim_scale.valueChanged.connect(self._apply_scale)
        self._anim_open.addAnimation(self._anim_scale)

        self._anim_nav = QVariantAnimation(self)
        self._anim_nav.setDuration(120)
        self._anim_nav.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim_nav.valueChanged.connect(self._apply_scale)

    def _build_theme_timer(self) -> None:
        self._theme_timer = QTimer(self)
        self._theme_timer.setInterval(42)
        self._theme_timer.timeout.connect(self._advance_theme_frame)

    def _advance_theme_frame(self) -> None:
        count = theme_frame_count(getattr(self, "_theme_id", DEFAULT_THEME))
        if count <= 1:
            self._theme_timer.stop()
            return
        self._theme_frame = (self._theme_frame + 1) % count
        if self.isVisible():
            self.update()

    def _start_theme_timer(self) -> None:
        count = theme_frame_count(getattr(self, "_theme_id", DEFAULT_THEME))
        debug_log(
            f"ring theme timer: theme_id={getattr(self, '_theme_id', DEFAULT_THEME)!r} "
            f"frame_count={count} visible={self.isVisible()}"
        )
        if count > 1 and self.isVisible():
            self._theme_timer.start()

    def _stop_theme_timer(self) -> None:
        self._theme_timer.stop()

    def _apply_scale(self, value: object) -> None:
        self._scale = float(value)  # type: ignore[arg-type]
        self.update()

    # ── Public API ────────────────────────────────────────────────────────────

    def show_at_cursor(self, items: list[MenuItem], theme_id: str = DEFAULT_THEME) -> None:
        debug_log("show_ring called")
        debug_log(f"ring show requested: items={len(items)} theme_id={theme_id!r}")
        self._reset_show_state()
        self._apply_theme(theme_id)
        self._nav_stack = [items]
        self._reset_hover()
        self._position_at_cursor()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.setWindowOpacity(0.0)
        self._scale = 0.80
        self._anim_opacity.setStartValue(0.0)
        self._anim_opacity.setEndValue(1.0)
        self._anim_scale.setStartValue(0.80)
        self._anim_scale.setEndValue(1.0)

        self._log_overlay_state("show_ring before showFullScreen")
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self._log_overlay_state("show_ring after showFullScreen")
        self._start_theme_timer()
        self._anim_open.start()
        debug_log("outside_click_enabled scheduled")
        QTimer.singleShot(150, self._enable_outside_click)

    def close_ring(self, reason: str = "programmatic") -> None:
        self.dismiss_ring(reason)

    def dismiss_ring(self, reason: str) -> None:
        debug_log(
            f"dismiss_ring reason={reason} visible={self.isVisible()} "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"is_dismissing={self._is_dismissing}"
        )
        if self._is_dismissing:
            debug_log("dismiss_ring ignored: already dismissing")
            return
        self._is_dismissing = True
        self._outside_click_enabled = False
        self._pressed_inside_ring = False
        self._ignore_next_click = False
        self._active_action = None
        self._reset_hover()
        self._anim_open.stop()
        self._anim_nav.stop()
        self._stop_theme_timer()
        self.hide()
        self._is_dismissing = False
        debug_log(
            "dismiss_ring reset completed: "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"is_dismissing={self._is_dismissing}"
        )
        debug_log("dismiss_ring completed")

    def _enable_outside_click(self) -> None:
        if self.isVisible():
            self._outside_click_enabled = True
            debug_log(
                "outside_click_enabled=True"
            )

    def _reset_show_state(self) -> None:
        self._is_dismissing = False
        self._outside_click_enabled = False
        self._pressed_inside_ring = False
        self._ignore_next_click = False
        self._active_action = None
        self._reset_hover()
        debug_log(
            "next show reset completed: "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"is_dismissing={self._is_dismissing}"
        )
        debug_log(f"outside_click_enabled={self._outside_click_enabled}")

    def _log_overlay_state(self, label: str) -> None:
        flags = self.windowFlags()
        flags_value = getattr(flags, "value", str(flags))
        transparent_for_input = getattr(Qt.WindowType, "WindowTransparentForInput", None)
        has_transparent_for_input = bool(flags & transparent_for_input) if transparent_for_input else False
        debug_log(
            f"{label}: window_flags={flags_value} "
            f"geometry={self.geometry()} "
            f"isVisible={self.isVisible()} "
            f"ring_container_rect={self._ring_container_rect} "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"WA_TransparentForMouseEvents="
            f"{self.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)} "
            f"WindowTransparentForInput={has_transparent_for_input} "
            f"mouseTracking={self.hasMouseTracking()}"
        )

    # ── Navigation ────────────────────────────────────────────────────────────

    def _drill_into(self, item: MenuItem) -> None:
        if item.is_folder:
            self._nav_stack.append(item.children)
            self._reset_hover()
            self._play_nav()
        else:
            self.dismiss_ring("action")
            self.item_activated.emit(item)

    def _go_back(self) -> None:
        if len(self._nav_stack) > 1:
            self._nav_stack.pop()
            self._reset_hover()
            self._play_nav()
        else:
            self.dismiss_ring("center_x")

    def _play_nav(self) -> None:
        self._anim_open.stop()
        self._anim_nav.setStartValue(0.88)
        self._anim_nav.setEndValue(1.0)
        self._anim_nav.start()
        self.update()

    def _reset_hover(self) -> None:
        self._hovered_slot = -1
        self._center_hovered = False

    @property
    def _current_items(self) -> list[MenuItem]:
        return self._nav_stack[-1] if self._nav_stack else []

    @property
    def _depth(self) -> int:
        return len(self._nav_stack)

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _position_at_cursor(self) -> None:
        pos = QCursor.pos()
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            self.setGeometry(pos.x() - WINDOW_SIZE // 2, pos.y() - WINDOW_SIZE // 2, WINDOW_SIZE, WINDOW_SIZE)
            self._ring_container_rect = QRectF(0, 0, WINDOW_SIZE, WINDOW_SIZE)
            debug_log(f"ring_container geometry = {self._ring_container_rect}")
            return

        g = screen.geometry()
        avail = screen.availableGeometry()
        self.setGeometry(g)

        available_span = max(180, min(avail.width() - 20, avail.height() - 20))
        ring_size = max(MIN_WINDOW_SIZE, min(WINDOW_SIZE, available_span))
        ring_size = min(ring_size, max(180, avail.width()), max(180, avail.height()))
        min_x = max(0, avail.x() - g.x())
        min_y = max(0, avail.y() - g.y())
        max_x = max(min_x, avail.x() - g.x() + max(0, avail.width() - ring_size))
        max_y = max(min_y, avail.y() - g.y() + max(0, avail.height() - ring_size))
        local_x = pos.x() - g.x() - ring_size // 2
        local_y = pos.y() - g.y() - ring_size // 2
        local_x = max(min_x, min(local_x, max_x))
        local_y = max(min_y, min(local_y, max_y))
        self._ring_container_rect = QRectF(local_x, local_y, ring_size, ring_size)
        debug_log(f"ring_container geometry = {self._ring_container_rect}")

    @staticmethod
    def _slot_centre(index: int) -> tuple[float, float]:
        angle = 2 * math.pi * index / NUM_SLOTS - math.pi / 2
        c = WINDOW_SIZE / 2
        return (
            c + ITEM_ORBIT * math.cos(angle),
            c + ITEM_ORBIT * math.sin(angle),
        )

    def _hit_centre(self, pos: QPointF) -> bool:
        c = WINDOW_SIZE / 2
        return math.hypot(pos.x() - c, pos.y() - c) <= CENTER_RADIUS + _HIT_PADDING

    def _hit_slot(self, pos: QPointF) -> int:
        for i in range(NUM_SLOTS):
            sx, sy = self._slot_centre(i)
            if math.hypot(pos.x() - sx, pos.y() - sy) <= ITEM_RADIUS + _HIT_PADDING:
                return i
        return -1

    def _overlay_to_ring_pos(self, pos: QPointF) -> QPointF:
        container_scale = self._ring_container_rect.width() / WINDOW_SIZE if self._ring_container_rect.width() else 1.0
        return QPointF(
            (pos.x() - self._ring_container_rect.left()) / container_scale,
            (pos.y() - self._ring_container_rect.top()) / container_scale,
        )

    # ── Events ────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            debug_log("dismissed by ESC")
            self.dismiss_ring("esc")
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        contains = self._ring_container_rect.contains(pos)
        debug_log(
            "overlay mousePressEvent ENTER "
            f"button={event.button()} "
            f"pos={pos} "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"ring_container_rect={self._ring_container_rect} "
            f"contains={contains}"
        )
        if event.button() == Qt.MouseButton.LeftButton:
            debug_log(f"overlay mousePressEvent pos={pos}")
            if not self._outside_click_enabled or self._is_dismissing:
                debug_log(
                    "overlay mousePressEvent ignored: "
                    f"outside_click_enabled={self._outside_click_enabled} "
                    f"is_dismissing={self._is_dismissing}"
                )
                event.accept()
                return

            if not self._ring_container_rect.contains(pos):
                debug_log("click outside ring_container")
                self.dismiss_ring("outside_click")
                event.accept()
                return

            debug_log("click inside ring_container")
            pos = self._overlay_to_ring_pos(pos)
            if self._hit_centre(pos):
                debug_log("click inside ring ignored: center button")
                self._go_back()
                event.accept()
                return

            idx = self._hit_slot(pos)
            if idx != -1 and idx < len(self._current_items):
                debug_log(f"click inside ring ignored: action slot={idx}")
                self._drill_into(self._current_items[idx])
                event.accept()
                return

            debug_log("click inside ring_container: no action target")
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        pos      = event.position()
        if not self._ring_container_rect.contains(pos):
            if self._hovered_slot != -1 or self._center_hovered:
                self._reset_hover()
                self.update()
            super().mouseMoveEvent(event)
            return
        pos      = self._overlay_to_ring_pos(pos)
        on_ctr   = self._hit_centre(pos)
        new_slot = -1 if on_ctr else self._hit_slot(pos)
        if new_slot != self._hovered_slot or on_ctr != self._center_hovered:
            self._hovered_slot   = new_slot
            self._center_hovered = on_ctr
            self.update()
        super().mouseMoveEvent(event)

    def showEvent(self, event) -> None:
        debug_log("ring show")
        debug_log("overlay shown")
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        debug_log("hideEvent called")
        debug_log("ring hide")
        self._outside_click_enabled = False
        self._pressed_inside_ring = False
        self._ignore_next_click = False
        self._active_action = None
        self._stop_theme_timer()
        debug_log(
            "hideEvent reset completed: "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"is_dismissing={self._is_dismissing}"
        )
        super().hideEvent(event)

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 1))

        p.save()
        p.translate(self._ring_container_rect.left(), self._ring_container_rect.top())
        container_scale = self._ring_container_rect.width() / WINDOW_SIZE if self._ring_container_rect.width() else 1.0
        p.scale(container_scale, container_scale)
        c = WINDOW_SIZE / 2
        p.translate(c, c)
        p.scale(self._scale, self._scale)
        p.translate(-c, -c)

        self._draw_launcher_grid(p, c)
        self._draw_ring_lines(p)
        self._draw_slot_shadows(p)
        self._draw_slots(p, c)
        self._draw_centre_btn(p, c)

        p.restore()
        p.end()

    # ── Connecting lines ──────────────────────────────────────────────────────

    def _draw_launcher_grid(self, p: QPainter, c: float) -> None:
        """Subtle dark-neon orbit guides behind the actionable slots."""
        halo = QRadialGradient(c, c, ITEM_ORBIT + 84)
        halo.setColorAt(0.0, QColor(VOID))
        halo.setColorAt(0.36, QColor(CHARCOAL))
        halo.setColorAt(0.72, QColor(VOID))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(c, c), ITEM_ORBIT + 86, ITEM_ORBIT + 86)

        p.setBrush(Qt.BrushStyle.NoBrush)
        for radius, alpha, width in (
            (ITEM_ORBIT - 38, 22, 0.8),
            (ITEM_ORBIT, 44, 1.0),
            (ITEM_ORBIT + 38, 18, 0.8),
        ):
            pen = QPen(QColor(NEON_CYAN))
            pen.setWidthF(width)
            pen.setColor(QColor(pen.color().red(), pen.color().green(), pen.color().blue(), alpha))
            p.setPen(pen)
            p.drawEllipse(QPointF(c, c), radius, radius)

        tick_pen = QPen(QColor(EMBER))
        tick_pen.setWidthF(1.1)
        tick_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        tick_color = QColor(EMBER)
        tick_color.setAlpha(70)
        tick_pen.setColor(tick_color)
        p.setPen(tick_pen)
        for i in range(NUM_SLOTS):
            angle = 2 * math.pi * i / NUM_SLOTS - math.pi / 2
            inner = ITEM_ORBIT - 46
            outer = ITEM_ORBIT - 34
            p.drawLine(
                QLineF(
                    c + math.cos(angle) * inner,
                    c + math.sin(angle) * inner,
                    c + math.cos(angle) * outer,
                    c + math.sin(angle) * outer,
                )
            )
        p.setPen(Qt.PenStyle.NoPen)

    def _draw_ring_lines(self, p: QPainter) -> None:
        """Thin lines between adjacent occupied slot centres (behind circles)."""
        items = self._current_items
        line_color = QColor(self._c_line)
        line_color.setAlpha(max(48, min(110, line_color.alpha())))
        pen = QPen(line_color, 1.1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(NUM_SLOTS):
            j = (i + 1) % NUM_SLOTS
            has_i = i < len(items)
            has_j = j < len(items)
            if not has_i and not has_j:
                continue
            sx_i, sy_i = self._slot_centre(i)
            sx_j, sy_j = self._slot_centre(j)
            p.drawLine(QLineF(sx_i, sy_i, sx_j, sy_j))
        p.setPen(Qt.PenStyle.NoPen)

    # ── Slot decorations (theme textures) ────────────────────────────────────

    # ── Shadow pass ───────────────────────────────────────────────────────────

    def _draw_slot_shadows(self, p: QPainter) -> None:
        items = self._current_items
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(NUM_SLOTS):
            item = items[i] if i < len(items) else None
            if item is None:
                continue
            sx, sy = self._slot_centre(i)
            r = float(ITEM_RADIUS)
            shadow = QColor(self._c_shadow)
            shadow.setAlpha(min(150, max(70, shadow.alpha())))
            p.setBrush(shadow)
            p.drawEllipse(QPointF(sx, sy + 6), r + 5, r + 5)
        p.setBrush(Qt.BrushStyle.NoBrush)

    # ── Slot pass ─────────────────────────────────────────────────────────────

    def _draw_slots(self, p: QPainter, c: float) -> None:
        items = self._current_items
        for i in range(NUM_SLOTS):
            sx, sy = self._slot_centre(i)
            item   = items[i] if i < len(items) else None
            hov    = (i == self._hovered_slot)
            self._draw_one_slot(p, c, sx, sy, item, hov)

    def _draw_one_slot(
        self,
        p: QPainter,
        c: float,
        sx: float,
        sy: float,
        item: MenuItem | None,
        hovered: bool,
    ) -> None:
        r = float(ITEM_RADIUS)

        if item is None:
            empty_color = QColor(ASH)
            empty_color.setAlpha(72)
            p.setPen(QPen(empty_color, 1.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(sx, sy), r, r)
            dot_color = QColor(STEEL)
            dot_color.setAlpha(120)
            p.setBrush(dot_color)
            p.drawEllipse(QPointF(sx, sy), 2.0, 2.0)
            p.setPen(Qt.PenStyle.NoPen)
            return

        is_folder = item.is_folder
        fill = (self._c_folder_h if hovered else self._c_folder) if is_folder \
               else (self._c_slot_h if hovered else self._c_slot)

        inner_fill = QColor(fill.red(), fill.green(), fill.blue(), 210 if hovered else 190)
        draw_energy_bubble(
            p,
            sx,
            sy,
            r + (1.8 if hovered else 0.6),
            getattr(self, "_theme_id", DEFAULT_THEME),
            selected=hovered,
            hovered=hovered,
            rim_width=9.0 if hovered else 8.0,
            inner_fill=inner_fill,
            frame_index=self._theme_frame,
        )

        p.setPen(Qt.PenStyle.NoPen)

        # Icon / emoji (large font) or abbreviation (small bold font)
        abbrev = item.icon or item.short_label or _abbrev(item.label)
        p.setFont(self._font_emoji if _is_emoji(abbrev) else self._font_abbrev)
        p.setPen(_C_ABBREV)
        p.drawText(
            QRectF(sx - r + 1, sy - r + 1, (r - 1) * 2, (r - 1) * 2),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            abbrev,
        )

        # Folder chevron › in lower-right quadrant
        if is_folder:
            cr_r = 12.0
            crx  = sx + r * 0.52 - cr_r / 2
            cry  = sy + r * 0.52 - cr_r / 2
            badge = QPainterPath()
            badge.addEllipse(crx, cry, cr_r, cr_r)
            p.fillPath(badge, QColor(RING_LABEL_BG))
            badge_edge = QColor(EMBER_HOVER)
            badge_edge.setAlpha(170)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(badge_edge, 1.0))
            p.drawEllipse(QRectF(crx, cry, cr_r, cr_r))
            chevron_font = QFont()
            chevron_font.setPixelSize(9)
            chevron_font.setBold(True)
            p.setFont(chevron_font)
            p.setPen(_C_CHEVRON)
            p.drawText(QRectF(crx, cry, cr_r, cr_r),
                       Qt.AlignmentFlag.AlignCenter, ">")

        self._draw_label_card(p, c, sx, sy, item.label, hovered)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Qt.BrushStyle.NoBrush)

    # ── Label card ────────────────────────────────────────────────────────────

    def _draw_label_card(
        self,
        p: QPainter,
        c: float,
        sx: float,
        sy: float,
        label: str,
        hovered: bool,
    ) -> None:
        dx, dy = sx - c, sy - c
        dist   = math.hypot(dx, dy) or 1.0
        nx, ny = dx / dist, dy / dist

        half_h  = _LABEL_H / 2
        card_cx = sx + nx * (ITEM_RADIUS + _LABEL_GAP + half_h)
        card_cy = sy + ny * (ITEM_RADIUS + _LABEL_GAP + half_h)

        p.setFont(self._font_label)
        fm     = p.fontMetrics()
        text_w = min(fm.horizontalAdvance(label), _LABEL_MAX_W)
        card_w = text_w + _LABEL_PADX * 2 + 6

        x0 = card_cx - card_w / 2
        y0 = card_cy - half_h

        shadow = QPainterPath()
        shadow.addRoundedRect(x0, y0 + 3, card_w, _LABEL_H, _LABEL_R, _LABEL_R)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(shadow, QColor(0, 0, 0, 130))

        card = QPainterPath()
        card.addRoundedRect(x0, y0, card_w, _LABEL_H, _LABEL_R, _LABEL_R)
        fill = QLinearGradient(x0, y0, x0 + card_w, y0 + _LABEL_H)
        fill.setColorAt(0.0, QColor(RING_LABEL_BG))
        fill.setColorAt(0.58, QColor(CHARCOAL))
        fill.setColorAt(1.0, QColor(VOID))
        p.fillPath(card, QBrush(fill))

        edge = QColor(EMBER_HOVER if hovered else RING_LABEL_EDGE)
        edge.setAlpha(210 if hovered else 150)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(edge, 1.1 if hovered else 0.9))
        p.drawPath(card)

        accent = QColor(EMBER if hovered else ASH)
        accent.setAlpha(225 if hovered else 120)
        p.setPen(QPen(accent, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QLineF(x0 + 5, y0 + 7, x0 + 5, y0 + _LABEL_H - 7))

        p.setPen(QColor(BONE if hovered else FOG))
        p.drawText(
            QRectF(x0 + _LABEL_PADX + 4, y0, text_w, _LABEL_H),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            label,
        )

    # ── Centre button ─────────────────────────────────────────────────────────

    def _draw_centre_btn(self, p: QPainter, c: float) -> None:
        is_back = self._depth > 1
        hov     = self._center_hovered

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 130))
        p.drawEllipse(QPointF(c, c + 3),
                      float(CENTER_RADIUS + 5), float(CENTER_RADIUS + 5))

        if hov:
            fill = self._c_center_b if is_back else self._c_center_x
        else:
            fill = self._c_center
        btn_path = QPainterPath()
        btn_path.addEllipse(c - CENTER_RADIUS, c - CENTER_RADIUS,
                            CENTER_RADIUS * 2, CENTER_RADIUS * 2)
        core = QRadialGradient(c - 4, c - 5, CENTER_RADIUS * 1.65)
        core.setColorAt(0.0, QColor(STEEL if hov else CHARCOAL))
        core.setColorAt(0.62, QColor(fill))
        core.setColorAt(1.0, QColor(VOID))
        p.fillPath(btn_path, QBrush(core))

        pulse = QColor(EMBER_HOVER if hov else EMBER)
        pulse.setAlpha(170 if hov else 95)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(pulse, 1.5 if hov else 1.0))
        p.drawEllipse(QPointF(c, c), CENTER_RADIUS + 3, CENTER_RADIUS + 3)

        glass = QColor(NEON_CYAN if hov else BONE)
        glass.setAlpha(95 if hov else 42)
        p.setPen(QPen(glass, 0.9))
        p.drawEllipse(QPointF(c, c), CENTER_RADIUS - 3, CENTER_RADIUS - 3)

        ir   = CENTER_RADIUS * 0.40
        pw   = 2.0
        cap  = Qt.PenCapStyle.RoundCap
        join = Qt.PenJoinStyle.RoundJoin
        ico  = _C_CTR_ICO_H if hov else _C_CTR_ICO

        if is_back:
            p.setPen(QPen(ico, pw, Qt.PenStyle.SolidLine, cap, join))
            ah = ir * 0.55
            p.drawLine(QLineF(c - ir, c,      c + ir,      c))
            p.drawLine(QLineF(c - ir, c,      c - ir + ah, c - ah))
            p.drawLine(QLineF(c - ir, c,      c - ir + ah, c + ah))
        else:
            p.setPen(QPen(ico, pw, Qt.PenStyle.SolidLine, cap, join))
            p.drawLine(QLineF(c - ir, c - ir, c + ir,  c + ir))
            p.drawLine(QLineF(c + ir, c - ir, c - ir,  c + ir))

        p.setPen(Qt.PenStyle.NoPen)
