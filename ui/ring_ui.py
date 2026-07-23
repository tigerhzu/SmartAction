"""
Radial Action Ring overlay — themed floating-slot design.

Visual features
---------------
- Gradient-filled slot circles with inner rim highlight (glassmorphism feel)
- Independent floating action bubbles over a constellation star map
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
    QFontMetricsF,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from core.constellation import (
    CONSTELLATIONS,
    DEFAULT_CONSTELLATION,
    DEFAULT_CONSTELLATION_COLOR,
    normalise_constellation_color,
)
from core.debug_log import debug_log
from core.theme import DEFAULT_THEME, THEMES
from ui.style_tokens import (
    ASH,
    BONE,
    EMBER_HOVER,
    FOG,
    HEADLINE_FONT_FAMILY,
    NEON_CYAN,
    RING_LABEL_BG,
    RING_LABEL_EDGE,
    STEEL,
)
from ui.motion_preferences import reduced_motion_enabled
from ui.theme_painter import theme_frame_count
from ui.theme_renderer import (
    ThemeInteraction,
    theme_renderer,
)

if TYPE_CHECKING:
    from core.menu_model import MenuItem

# ── Geometry ──────────────────────────────────────────────────────────────────

ITEM_RADIUS   = 28      # slot circle radius (px)
ITEM_ORBIT    = 112     # distance from window centre → slot centre
NUM_SLOTS     = 8
MAX_DIRECT_SLOTS = 10  # keep modest overflow visible without crowding the ring
CENTER_RADIUS = 18      # centre close / back button radius

_LABEL_H      = 30      # label card height
_LABEL_R      = 6       # label card corner radius
_LABEL_PADX   = 12      # horizontal text padding inside card
_LABEL_MAX_W  = 154     # max card width before truncation
_LABEL_GAP    = 12      # gap between slot edge and near card edge
_HIT_PADDING  = 12      # forgiving click target padding for labels / buttons
_DRAG_THRESHOLD = 10.0  # avoids treating normal click jitter as ring rotation

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


def _cut_corner_path(rect: QRectF, cut: float) -> QPainterPath:
    """Return a precise chamfered plaque path used by action labels."""
    path = QPainterPath()
    path.moveTo(rect.left() + cut, rect.top())
    path.lineTo(rect.right() - cut, rect.top())
    path.lineTo(rect.right(), rect.top() + cut)
    path.lineTo(rect.right(), rect.bottom() - cut)
    path.lineTo(rect.right() - cut, rect.bottom())
    path.lineTo(rect.left() + cut, rect.bottom())
    path.lineTo(rect.left(), rect.bottom() - cut)
    path.lineTo(rect.left(), rect.top() + cut)
    path.closeSubpath()
    return path


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
        self._constellation_id = DEFAULT_CONSTELLATION
        self._constellation_color = DEFAULT_CONSTELLATION_COLOR
        self._ring_container_rect = QRectF(0, 0, WINDOW_SIZE, WINDOW_SIZE)
        self._outside_click_enabled: bool = False
        self._is_dismissing: bool = False
        self._pressed_inside_ring: bool = False
        self._ignore_next_click: bool = False
        self._active_action: int | None = None
        self._rotation_angle: float = 0.0
        self._drag_slot: int = -1
        self._drag_start_pos = QPointF()
        self._drag_last_angle: float = 0.0
        self._ring_drag_active: bool = False
        self._pressed_slot: int = -1
        self._click_slot: int = -1
        self._click_progress: float = 0.0
        self._pending_activation: MenuItem | None = None
        self._pointer_ring_pos = QPointF(WINDOW_SIZE / 2, WINDOW_SIZE / 2)
        self._slot_hover_progress = [0.0] * MAX_DIRECT_SLOTS
        self._reduced_motion = reduced_motion_enabled()

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
            | Qt.WindowType.Popup
            | Qt.WindowType.NoDropShadowWindowHint
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
        self._theme_renderer = theme_renderer(theme_id)
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
        self._c_empty    = c(*t["empty"])
        self._c_card_bg  = c(*t["card_bg"])
        self._c_card_txt = c(*t["card_text"])
        self._c_card_sh  = c(*t["card_shadow"])

    def _apply_constellation(
        self,
        constellation_id: str,
        constellation_color: str = DEFAULT_CONSTELLATION_COLOR,
    ) -> None:
        self._constellation_id = (
            constellation_id
            if constellation_id in CONSTELLATIONS
            else DEFAULT_CONSTELLATION
        )
        self._constellation_color = normalise_constellation_color(
            constellation_color
        )

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

        self._anim_click = QVariantAnimation(self)
        self._anim_click.setDuration(150)
        self._anim_click.setStartValue(0.0)
        self._anim_click.setEndValue(1.0)
        self._anim_click.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_click.valueChanged.connect(self._apply_click_progress)
        self._anim_click.finished.connect(self._finish_click_feedback)

    def _build_theme_timer(self) -> None:
        self._theme_timer = QTimer(self)
        self._theme_timer.setInterval(16)
        self._theme_timer.timeout.connect(self._advance_theme_frame)

    def _advance_theme_frame(self) -> None:
        count = theme_frame_count(getattr(self, "_theme_id", DEFAULT_THEME))
        if count <= 1:
            self._theme_timer.stop()
            return
        for index, amount in enumerate(self._slot_hover_progress):
            target = 1.0 if index == self._hovered_slot else 0.0
            rate = 0.24 if target > amount else 0.065
            if abs(target - amount) <= rate:
                self._slot_hover_progress[index] = target
            else:
                direction = 1.0 if target > amount else -1.0
                self._slot_hover_progress[index] = amount + direction * rate
        self._theme_frame = (self._theme_frame + 1) % count
        if self.isVisible():
            self._update_ring()

    def _start_theme_timer(self) -> None:
        count = theme_frame_count(getattr(self, "_theme_id", DEFAULT_THEME))
        debug_log(
            f"ring theme timer: theme_id={getattr(self, '_theme_id', DEFAULT_THEME)!r} "
            f"frame_count={count} visible={self.isVisible()}"
        )
        if count > 1 and self.isVisible() and not self._reduced_motion:
            self._theme_timer.start()

    def _stop_theme_timer(self) -> None:
        self._theme_timer.stop()

    def _apply_scale(self, value: object) -> None:
        self._scale = float(value)  # type: ignore[arg-type]
        self._update_ring()

    def _apply_click_progress(self, value: object) -> None:
        self._click_progress = float(value)  # type: ignore[arg-type]
        self._update_ring()

    def _stop_click_feedback(self) -> None:
        self._anim_click.stop()
        self._pressed_slot = -1
        self._click_slot = -1
        self._click_progress = 0.0
        self._pending_activation = None

    def _begin_click_feedback(self, slot: int, item: MenuItem) -> None:
        self._pressed_slot = -1
        if self._reduced_motion:
            self._drill_into(item)
            return
        self._click_slot = slot
        self._click_progress = 0.0
        self._pending_activation = item
        self._anim_click.stop()
        self._anim_click.setStartValue(0.0)
        self._anim_click.setEndValue(1.0)
        self._anim_click.start()
        self._update_ring()

    def _finish_click_feedback(self) -> None:
        item = self._pending_activation
        self._click_slot = -1
        self._click_progress = 0.0
        self._pending_activation = None
        if item is not None:
            self._drill_into(item)

    # ── Public API ────────────────────────────────────────────────────────────

    def show_at_cursor(
        self,
        items: list[MenuItem],
        theme_id: str = DEFAULT_THEME,
        constellation_id: str = DEFAULT_CONSTELLATION,
        constellation_color: str = DEFAULT_CONSTELLATION_COLOR,
    ) -> None:
        debug_log("show_ring called")
        debug_log(f"ring show requested: items={len(items)} theme_id={theme_id!r}")
        self._reduced_motion = reduced_motion_enabled()
        self._reset_show_state()
        self._apply_theme(theme_id)
        self._apply_constellation(constellation_id, constellation_color)
        self._nav_stack = [items]
        self._reset_hover()
        self._position_at_cursor()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        if self._reduced_motion:
            self.setWindowOpacity(1.0)
            self._scale = 1.0
        else:
            self.setWindowOpacity(0.0)
            self._scale = 0.80
            self._anim_opacity.setStartValue(0.0)
            self._anim_opacity.setEndValue(1.0)
            self._anim_scale.setStartValue(0.80)
            self._anim_scale.setEndValue(1.0)

        self._log_overlay_state("show_ring before show")
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self._log_overlay_state("show_ring after show")
        self._start_theme_timer()
        if not self._reduced_motion:
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
        self._cancel_ring_drag()
        self._reset_hover()
        self._anim_open.stop()
        self._anim_nav.stop()
        self._stop_click_feedback()
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
        self._rotation_angle = 0.0
        self._slot_hover_progress = [0.0] * MAX_DIRECT_SLOTS
        self._stop_click_feedback()
        self._cancel_ring_drag()
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
        if self._reduced_motion:
            self._scale = 1.0
        else:
            self._anim_nav.setStartValue(0.88)
            self._anim_nav.setEndValue(1.0)
            self._anim_nav.start()
        self._update_ring()

    def _reset_hover(self) -> None:
        self._hovered_slot = -1
        self._center_hovered = False

    def _interaction_state(
        self,
        cx: float,
        cy: float,
        *,
        hovered: bool = False,
        hover_progress: float | None = None,
        pressed: bool = False,
        click_progress: float = 0.0,
    ) -> ThemeInteraction:
        radius = max(1.0, float(ITEM_RADIUS))
        return ThemeInteraction(
            frame_index=self._theme_frame,
            hovered=hovered,
            hover_progress=(
                float(hovered)
                if self._reduced_motion or hover_progress is None
                else max(0.0, min(1.0, hover_progress))
            ),
            pressed=pressed,
            click_progress=click_progress,
            pointer_offset_x=(self._pointer_ring_pos.x() - cx) / radius,
            pointer_offset_y=(self._pointer_ring_pos.y() - cy) / radius,
            reduced_motion=self._reduced_motion,
        )

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

        avail = screen.availableGeometry()

        available_span = max(180, min(avail.width() - 20, avail.height() - 20))
        ring_size = max(MIN_WINDOW_SIZE, min(WINDOW_SIZE, available_span))
        ring_size = min(ring_size, max(180, avail.width()), max(180, avail.height()))
        min_x = avail.left()
        min_y = avail.top()
        max_x = max(min_x, avail.right() - ring_size + 1)
        max_y = max(min_y, avail.bottom() - ring_size + 1)
        window_x = max(min_x, min(pos.x() - ring_size // 2, max_x))
        window_y = max(min_y, min(pos.y() - ring_size // 2, max_y))
        self.setGeometry(window_x, window_y, ring_size, ring_size)
        self._ring_container_rect = QRectF(0, 0, ring_size, ring_size)
        debug_log(f"ring_container geometry = {self._ring_container_rect}")

    def _slot_centre(self, index: int) -> tuple[float, float]:
        angle = (
            2 * math.pi * index / self._slot_count()
            - math.pi / 2
            + self._rotation_angle
        )
        c = WINDOW_SIZE / 2
        return (
            c + ITEM_ORBIT * math.cos(angle),
            c + ITEM_ORBIT * math.sin(angle),
        )

    def _slot_count(self) -> int:
        return max(NUM_SLOTS, min(len(self._current_items), MAX_DIRECT_SLOTS))

    def _hit_centre(self, pos: QPointF) -> bool:
        c = WINDOW_SIZE / 2
        return math.hypot(pos.x() - c, pos.y() - c) <= CENTER_RADIUS + _HIT_PADDING

    def _hit_slot(self, pos: QPointF) -> int:
        items = self._current_items
        for i in range(self._slot_count()):
            sx, sy = self._slot_centre(i)
            if math.hypot(pos.x() - sx, pos.y() - sy) <= ITEM_RADIUS + _HIT_PADDING:
                return i
            if i < len(items) and self._label_card_rect(
                WINDOW_SIZE / 2,
                sx,
                sy,
                items[i].label,
            ).adjusted(-4, -4, 4, 4).contains(pos):
                return i
        return -1

    def _label_card_rect(
        self,
        c: float,
        sx: float,
        sy: float,
        label: str,
    ) -> QRectF:
        dx, dy = sx - c, sy - c
        dist = math.hypot(dx, dy) or 1.0
        nx, ny = dx / dist, dy / dist
        half_h = _LABEL_H / 2
        card_cx = sx + nx * (ITEM_RADIUS + _LABEL_GAP + half_h)
        card_cy = sy + ny * (ITEM_RADIUS + _LABEL_GAP + half_h)
        text_w = min(QFontMetricsF(self._font_label).horizontalAdvance(label), _LABEL_MAX_W)
        card_w = text_w + _LABEL_PADX * 2 + 6
        return QRectF(
            card_cx - card_w / 2,
            card_cy - half_h,
            card_w,
            _LABEL_H,
        )

    def _overlay_to_ring_pos(self, pos: QPointF) -> QPointF:
        container_scale = self._ring_container_rect.width() / WINDOW_SIZE if self._ring_container_rect.width() else 1.0
        return QPointF(
            (pos.x() - self._ring_container_rect.left()) / container_scale,
            (pos.y() - self._ring_container_rect.top()) / container_scale,
        )

    @staticmethod
    def _angle_from_centre(pos: QPointF) -> float:
        c = WINDOW_SIZE / 2
        return math.atan2(pos.y() - c, pos.x() - c)

    @staticmethod
    def _angle_delta(current: float, previous: float) -> float:
        """Return the shortest signed angular delta across the -pi/pi seam."""
        return (current - previous + math.pi) % (2 * math.pi) - math.pi

    def _cancel_ring_drag(self) -> None:
        self._drag_slot = -1
        self._ring_drag_active = False
        self.unsetCursor()

    def _update_ring(self) -> None:
        """Repaint only the ring area instead of the full-screen overlay."""
        self.update(self._ring_container_rect.toAlignedRect())

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
                # Defer activation until release so the same gesture can rotate
                # the whole ring without accidentally launching this action.
                self._drag_slot = idx
                self._drag_start_pos = QPointF(pos)
                self._drag_last_angle = self._angle_from_centre(pos)
                self._ring_drag_active = False
                self._pressed_slot = idx
                self._pointer_ring_pos = QPointF(pos)
                self._update_ring()
                debug_log(f"ring slot press pending: slot={idx}")
                event.accept()
                return

            debug_log("click inside ring_container: no action target")
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        if self._drag_slot != -1 and event.buttons() & Qt.MouseButton.LeftButton:
            ring_pos = self._overlay_to_ring_pos(pos)
            self._pointer_ring_pos = QPointF(ring_pos)
            moved = math.hypot(
                ring_pos.x() - self._drag_start_pos.x(),
                ring_pos.y() - self._drag_start_pos.y(),
            )
            if not self._ring_drag_active and moved >= _DRAG_THRESHOLD:
                self._ring_drag_active = True
                self._pressed_slot = -1
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                debug_log(f"ring rotation started: slot={self._drag_slot}")

            if self._ring_drag_active:
                c = WINDOW_SIZE / 2
                if math.hypot(ring_pos.x() - c, ring_pos.y() - c) > CENTER_RADIUS:
                    current_angle = self._angle_from_centre(ring_pos)
                    self._rotation_angle += self._angle_delta(
                        current_angle,
                        self._drag_last_angle,
                    )
                    self._drag_last_angle = current_angle
                    self._hovered_slot = self._drag_slot
                    self._center_hovered = False
                    self._update_ring()
                event.accept()
                return

        if not self._ring_container_rect.contains(pos):
            if self._hovered_slot != -1 or self._center_hovered:
                self._reset_hover()
                self._update_ring()
            self.unsetCursor()
            super().mouseMoveEvent(event)
            return
        pos      = self._overlay_to_ring_pos(pos)
        self._pointer_ring_pos = QPointF(pos)
        on_ctr   = self._hit_centre(pos)
        new_slot = -1 if on_ctr else self._hit_slot(pos)
        if new_slot != self._hovered_slot or on_ctr != self._center_hovered:
            self._hovered_slot   = new_slot
            self._center_hovered = on_ctr
            self._update_ring()
        if on_ctr or 0 <= new_slot < len(self._current_items):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_slot != -1:
            pressed_slot = self._drag_slot
            was_dragging = self._ring_drag_active
            self._pressed_slot = -1
            self._cancel_ring_drag()

            if was_dragging:
                debug_log(
                    f"ring rotation finished: radians={self._rotation_angle:.3f}"
                )
                self._update_ring()
            elif self._ring_container_rect.contains(event.position()):
                ring_pos = self._overlay_to_ring_pos(event.position())
                released_slot = self._hit_slot(ring_pos)
                if released_slot == pressed_slot and pressed_slot < len(self._current_items):
                    debug_log(f"ring slot clicked: slot={pressed_slot}")
                    self._begin_click_feedback(
                        pressed_slot,
                        self._current_items[pressed_slot],
                    )
                else:
                    self._update_ring()

            event.accept()
            return
        super().mouseReleaseEvent(event)

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
        self._cancel_ring_drag()
        self._stop_click_feedback()
        self._stop_theme_timer()
        debug_log(
            "hideEvent reset completed: "
            f"outside_click_enabled={self._outside_click_enabled} "
            f"is_dismissing={self._is_dismissing}"
        )
        super().hideEvent(event)

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(event.rect(), QColor(0, 0, 0, 1))

        p.save()
        p.translate(self._ring_container_rect.left(), self._ring_container_rect.top())
        container_scale = self._ring_container_rect.width() / WINDOW_SIZE if self._ring_container_rect.width() else 1.0
        p.scale(container_scale, container_scale)
        c = WINDOW_SIZE / 2
        p.translate(c, c)
        p.scale(self._scale, self._scale)
        p.translate(-c, -c)

        self._draw_launcher_grid(p, c)
        self._draw_slot_shadows(p)
        self._draw_slots(p, c)
        self._draw_centre_btn(p, c)

        p.restore()
        p.end()

    # ── Constellation background ──────────────────────────────────────────────

    def _draw_launcher_grid(self, p: QPainter, c: float) -> None:
        """Theme-tinted star field and selected zodiac constellation."""
        accent = QColor(self._c_glow)
        center_color = QColor(
            min(255, 16 + accent.red() // 8),
            min(255, 20 + accent.green() // 8),
            min(255, 38 + accent.blue() // 7),
            238,
        )
        halo = QRadialGradient(c, c, ITEM_ORBIT + 84)
        halo.setColorAt(0.0, center_color)
        halo.setColorAt(0.42, QColor(13, 18, 38, 232))
        halo.setColorAt(0.76, QColor(7, 12, 27, 210))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(c, c), ITEM_ORBIT + 86, ITEM_ORBIT + 86)

        scene_state = self._interaction_state(c, c)
        self._theme_renderer.draw_background(
            p,
            c,
            c,
            ITEM_ORBIT,
            scene_state,
        )
        self._draw_star_field(p, c, accent)
        self._draw_constellation(p, c, QColor(self._constellation_color))

        self._theme_renderer.draw_guides(
            p,
            c,
            c,
            ITEM_ORBIT,
            self._slot_count(),
            self._rotation_angle,
            scene_state,
        )

        self._theme_renderer.draw_orbit(
            p,
            c,
            c,
            ITEM_ORBIT + 51.0,
            scene_state,
        )
        p.setPen(Qt.PenStyle.NoPen)

    def _draw_star_field(self, p: QPainter, c: float, accent: QColor) -> None:
        """Draw a deterministic star field without loading another asset."""
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(42):
            angle = math.radians((index * 137.508 + 19.0) % 360.0)
            radius = 30.0 + float((index * 53) % 150)
            x = c + math.cos(angle) * radius
            y = c + math.sin(angle) * radius
            star_radius = 0.55 + (index % 4) * 0.22
            color = QColor(220, 232, 255, 44 + (index % 5) * 14)
            if index % 7 == 0:
                color = QColor(accent)
                color.setAlpha(105)
                star_radius += 0.45
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), star_radius, star_radius)

    def _draw_constellation(self, p: QPainter, c: float, accent: QColor) -> None:
        data = CONSTELLATIONS.get(
            self._constellation_id,
            CONSTELLATIONS[DEFAULT_CONSTELLATION],
        )
        left, top, width, height = c - 142.0, c - 121.0, 284.0, 242.0
        points = [
            QPointF(left + x * width, top + y * height)
            for x, y, _brightness in data["stars"]
        ]

        line_color = QColor(accent)
        line_color.setAlpha(92)
        line_pen = QPen(line_color, 1.15)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(line_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for start, end in data["links"]:
            p.drawLine(QLineF(points[start], points[end]))

        p.setPen(Qt.PenStyle.NoPen)
        for point, (_x, _y, brightness) in zip(points, data["stars"]):
            glow = QColor(accent)
            glow.setAlpha(int(38 + brightness * 34))
            p.setBrush(glow)
            p.drawEllipse(point, 3.0 + brightness * 1.6, 3.0 + brightness * 1.6)
            p.setBrush(QColor(238, 246, 255, int(150 + brightness * 95)))
            core_radius = 0.85 + brightness * 0.85
            p.drawEllipse(point, core_radius, core_radius)
        self._theme_renderer.draw_constellation_accents(
            p,
            points,
            data["links"],
            self._interaction_state(c, c),
        )

    # ── Slot decorations (theme textures) ────────────────────────────────────

    # ── Shadow pass ───────────────────────────────────────────────────────────

    def _draw_slot_shadows(self, p: QPainter) -> None:
        items = self._current_items
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(self._slot_count()):
            item = items[i] if i < len(items) else None
            if item is None:
                continue
            sx, sy = self._slot_centre(i)
            r = float(ITEM_RADIUS)
            self._theme_renderer.draw_shadow(
                p,
                sx,
                sy,
                r,
                QColor(self._c_shadow),
            )
        p.setBrush(Qt.BrushStyle.NoBrush)

    # ── Slot pass ─────────────────────────────────────────────────────────────

    def _draw_slots(self, p: QPainter, c: float) -> None:
        items = self._current_items
        for i in range(self._slot_count()):
            sx, sy = self._slot_centre(i)
            item   = items[i] if i < len(items) else None
            hov    = (i == self._hovered_slot)
            self._draw_one_slot(p, c, i, sx, sy, item, hov)

    def _draw_one_slot(
        self,
        p: QPainter,
        c: float,
        slot_index: int,
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

        state = self._interaction_state(
            sx,
            sy,
            hovered=hovered,
            hover_progress=self._slot_hover_progress[slot_index],
            pressed=self._pressed_slot == slot_index,
            click_progress=(
                self._click_progress
                if self._click_slot == slot_index
                else 0.0
            ),
        )
        inner_fill = QColor(
            fill.red(),
            fill.green(),
            fill.blue(),
            210 if hovered else 190,
        )
        content_offset = self._theme_renderer.content_offset(state)
        visual_sx = sx + content_offset.x()
        visual_sy = sy + content_offset.y()
        self._theme_renderer.draw_button(
            p,
            visual_sx,
            visual_sy,
            r + 0.6,
            inner_fill,
            state,
        )

        p.setPen(Qt.PenStyle.NoPen)

        # Icon / emoji (large font) or abbreviation (small bold font)
        abbrev = item.icon or item.short_label or _abbrev(item.label)
        content_font = (
            self._font_emoji if _is_emoji(abbrev) else self._font_abbrev
        )
        content_rect = QRectF(
            visual_sx - r + 1,
            visual_sy - r + 1,
            (r - 1) * 2,
            (r - 1) * 2,
        )
        self._theme_renderer.draw_content_echo(
            p,
            content_rect,
            abbrev,
            content_font,
            state,
        )
        p.setFont(content_font)
        p.setPen(_C_ABBREV)
        p.drawText(
            content_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            abbrev,
        )

        # Folder chevron › in lower-right quadrant
        if is_folder:
            cr_r = 12.0
            crx  = visual_sx + r * 0.52 - cr_r / 2
            cry  = visual_sy + r * 0.52 - cr_r / 2
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
        p.setFont(self._font_label)
        rect = self._label_card_rect(c, sx, sy, label)
        x0, y0 = rect.left(), rect.top()
        card_w = rect.width()

        shadow_rect = rect.translated(0.0, 3.0)
        shadow = _cut_corner_path(shadow_rect, 7.0)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(shadow, QColor(0, 0, 0, 168))

        card = _cut_corner_path(rect, 7.0)
        fill = QLinearGradient(x0, y0, x0, y0 + _LABEL_H)
        fill.setColorAt(0.0, QColor(25, 29, 38, 248))
        fill.setColorAt(0.48, QColor(RING_LABEL_BG))
        fill.setColorAt(1.0, QColor(4, 6, 10, 252))
        p.fillPath(card, QBrush(fill))

        accent = QColor(self._c_glow)
        edge = QColor(accent if hovered else QColor(RING_LABEL_EDGE))
        edge.setAlpha(225 if hovered else 150)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(edge, 1.15 if hovered else 0.85))
        p.drawPath(card)

        inner_rect = rect.adjusted(3.0, 3.0, -3.0, -3.0)
        inner_edge = QColor(accent)
        inner_edge.setAlpha(82 if hovered else 38)
        p.setPen(QPen(inner_edge, 0.65))
        p.drawPath(_cut_corner_path(inner_rect, 4.0))

        # Tiny engraved corner marks add detail without competing with text.
        marker = QColor(accent)
        marker.setAlpha(185 if hovered else 88)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(marker)
        marker_r = 1.15
        for mx in (x0 + 8.5, x0 + card_w - 8.5):
            diamond = QPainterPath()
            diamond.moveTo(mx, y0 + _LABEL_H / 2 - marker_r)
            diamond.lineTo(mx + marker_r, y0 + _LABEL_H / 2)
            diamond.lineTo(mx, y0 + _LABEL_H / 2 + marker_r)
            diamond.lineTo(mx - marker_r, y0 + _LABEL_H / 2)
            diamond.closeSubpath()
            p.fillPath(diamond, marker)

        text_color = QColor(BONE if hovered else FOG)
        text_color.setAlpha(255 if hovered else 236)
        p.setPen(text_color)
        p.drawText(
            rect.adjusted(_LABEL_PADX, 0.0, -_LABEL_PADX, 0.0),
            Qt.AlignmentFlag.AlignCenter,
            label,
        )

    # ── Centre button ─────────────────────────────────────────────────────────

    def _draw_centre_btn(self, p: QPainter, c: float) -> None:
        is_back = self._depth > 1
        hov     = self._center_hovered

        if hov:
            fill = self._c_center_b if is_back else self._c_center_x
        else:
            fill = self._c_center

        self._theme_renderer.draw_center(
            p,
            c,
            c,
            float(CENTER_RADIUS),
            QColor(fill),
            self._interaction_state(c, c, hovered=hov),
        )

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
