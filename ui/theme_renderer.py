"""Modular visual-DNA renderers for the radial action ring.

The ring owns geometry and interaction. Theme components own every visual
decision: scene accents, orbit silhouette, button material, hover response,
click feedback, and motion behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)

from core.theme import DEFAULT_THEME, THEMES
from ui.style_tokens import CHARCOAL, EMBER, NEON_CYAN, STEEL, VOID
from ui.theme_painter import (
    draw_energy_bubble,
    draw_ocean_wave_orbit,
    draw_premium_rim,
    draw_theme_orbit,
)


@dataclass(frozen=True)
class ThemeVisualDNA:
    theme_id: str
    orbit_kind: str
    button_material: str
    particle_kind: str
    hover_kind: str
    click_kind: str
    hover_scale: float = 1.05
    press_scale: float = 0.95


@dataclass(frozen=True)
class ThemeInteraction:
    frame_index: int = 0
    hovered: bool = False
    hover_progress: float = 0.0
    pressed: bool = False
    click_progress: float = 0.0
    pointer_offset_x: float = 0.0
    pointer_offset_y: float = 0.0
    reduced_motion: bool = False

    @property
    def phase(self) -> float:
        if self.reduced_motion:
            return 0.18
        return (self.frame_index % 120) / 120.0


def _theme_color(theme_id: str, key: str) -> QColor:
    data = THEMES.get(theme_id, THEMES[DEFAULT_THEME])
    return QColor(*data[key])


def _radial_path(
    cx: float,
    cy: float,
    radius_at,
    *,
    samples: int = 180,
) -> QPainterPath:
    path = QPainterPath()
    for index in range(samples + 1):
        angle = math.tau * index / samples
        radius = radius_at(angle)
        point = QPointF(
            cx + math.cos(angle) * radius,
            cy + math.sin(angle) * radius,
        )
        if index == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)
    path.closeSubpath()
    return path


def _radial_band(outer: QPainterPath, inner: QPainterPath) -> QPainterPath:
    band = QPainterPath()
    band.setFillRule(Qt.FillRule.OddEvenFill)
    band.addPath(outer)
    band.addPath(inner)
    return band


def _diamond_path(width: float, height: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(0.0, -height)
    path.lineTo(width, 0.0)
    path.lineTo(0.0, height)
    path.lineTo(-width, 0.0)
    path.closeSubpath()
    return path


def _rotated_ellipse_point(
    cx: float,
    cy: float,
    radius_x: float,
    radius_y: float,
    rotation: float,
    angle: float,
) -> QPointF:
    local_x = math.cos(angle) * radius_x
    local_y = math.sin(angle) * radius_y
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    return QPointF(
        cx + local_x * cos_r - local_y * sin_r,
        cy + local_x * sin_r + local_y * cos_r,
    )


def _polar_segment(
    cx: float,
    cy: float,
    start_angle: float,
    span: float,
    radius_at,
    *,
    samples: int = 36,
) -> QPainterPath:
    path = QPainterPath()
    for index in range(samples + 1):
        angle = start_angle + span * index / samples
        radius = radius_at(angle)
        point = QPointF(
            cx + math.cos(angle) * radius,
            cy + math.sin(angle) * radius,
        )
        if index == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)
    return path


class ThemeRenderer:
    dna = ThemeVisualDNA(
        DEFAULT_THEME,
        "energy instrument",
        "glass energy",
        "energy motes",
        "soft expansion",
        "radial ripple",
    )

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.pressed:
            return self.dna.press_scale
        if state.click_progress > 0.0:
            return 1.0 - math.sin(state.click_progress * math.pi) * 0.045
        if state.hovered:
            return self.dna.hover_scale
        return 1.0

    def content_offset(self, state: ThemeInteraction) -> QPointF:
        del state
        return QPointF()

    def draw_content_echo(
        self,
        p: QPainter,
        rect: QRectF,
        text: str,
        font: QFont,
        state: ThemeInteraction,
    ) -> None:
        del p, rect, text, font, state

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        del p, cx, cy, orbit_r, state

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del state
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for radius, alpha, width in (
            (orbit_r - 38, 22, 0.8),
            (orbit_r, 44, 1.0),
            (orbit_r + 38, 18, 0.8),
        ):
            color = QColor(NEON_CYAN)
            color.setAlpha(alpha)
            p.setPen(QPen(color, width))
            p.drawEllipse(QPointF(cx, cy), radius, radius)

        tick_color = QColor(EMBER)
        tick_color.setAlpha(70)
        tick_pen = QPen(tick_color, 1.1)
        tick_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(tick_pen)
        for index in range(slot_count):
            angle = math.tau * index / slot_count - math.pi / 2 + rotation
            inner = orbit_r - 46
            outer = orbit_r - 34
            p.drawLine(
                QLineF(
                    cx + math.cos(angle) * inner,
                    cy + math.sin(angle) * inner,
                    cx + math.cos(angle) * outer,
                    cy + math.sin(angle) * outer,
                )
            )
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del p, points, links, state

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        draw_theme_orbit(
            p,
            cx,
            cy,
            outer_r,
            self.dna.theme_id,
            state.frame_index,
        )

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        shadow = QColor(color)
        shadow.setAlpha(min(150, max(70, shadow.alpha())))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(shadow)
        p.drawEllipse(QPointF(cx, cy + 6.0), radius + 5.0, radius + 5.0)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        draw_radius = radius * self.button_scale(state)
        draw_energy_bubble(
            p,
            cx,
            cy,
            draw_radius,
            self.dna.theme_id,
            selected=state.hovered,
            hovered=state.hovered,
            rim_width=9.0 if state.hovered else 8.0,
            inner_fill=fill,
            frame_index=state.frame_index,
            animate=not state.reduced_motion,
            ornaments=False,
        )
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 130))
        p.drawEllipse(QPointF(cx, cy + 3.0), radius + 5.0, radius + 5.0)
        draw_premium_rim(
            p,
            cx,
            cy,
            radius + 5.0,
            self.dna.theme_id,
            frame_index=state.frame_index,
            rim_width=6.5,
            opacity=0.92,
            energy_strength=1.28 if state.hovered else 0.92,
        )
        core = QRadialGradient(cx - 4.0, cy - 5.0, radius * 1.65)
        core.setColorAt(0.0, QColor(STEEL if state.hovered else CHARCOAL))
        core.setColorAt(0.62, fill)
        core.setColorAt(1.0, QColor(VOID))
        p.setBrush(QBrush(core))
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        pulse = QColor(EMBER if not state.hovered else NEON_CYAN)
        pulse.setAlpha(170 if state.hovered else 95)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(pulse, 1.5 if state.hovered else 1.0))
        p.drawEllipse(QPointF(cx, cy), radius + 3.0, radius + 3.0)
        p.restore()

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        color = _theme_color(self.dna.theme_id, "bubble_main")
        color.setAlpha(int(105 * (1.0 - progress)))
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(color, 1.4, Qt.PenStyle.SolidLine))
        ripple = radius * (1.0 + progress * 0.48)
        p.drawEllipse(QPointF(cx, cy), ripple, ripple)
        p.restore()


class TigerThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "tiger",
        "irregular amber energy fur",
        "dark amber striped jelly",
        "gold dust and claw fragments",
        "forward swell with claw sweep",
        "recoil and amber impact wave",
        hover_scale=1.085,
        press_scale=0.925,
    )

    @staticmethod
    def _fur_radius(radius: float, angle: float, phase: float) -> float:
        return radius + (
            math.sin(angle * 9.0 - phase * math.tau * 0.22) * 4.8
            + math.sin(angle * 21.0 + phase * math.tau * 0.13) * 2.2
            + math.sin(angle * 37.0 - phase * math.tau * 0.08) * 1.1
        )

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.click_progress > 0.0:
            progress = state.click_progress
            if progress < 0.36:
                return 1.0 - progress / 0.36 * 0.085
            return 0.915 + (progress - 0.36) / 0.64 * 0.085
        return super().button_scale(state)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(18):
            angle = math.radians((index * 137.5 + 17.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (7.0 + index % 3)
            radius = 38.0 + ((index * 47) % int(orbit_r + 35.0))
            x = cx + math.cos(angle + drift * 0.01) * radius
            y = cy + math.sin(angle + drift * 0.01) * radius
            size = 0.8 + (index % 3) * 0.45
            color = QColor(255, 166 + (index % 3) * 24, 56, 70 + index % 5 * 20)
            p.setBrush(color)
            if index % 4 == 0:
                p.save()
                p.translate(x, y)
                p.rotate(math.degrees(angle) + 35.0)
                p.drawRect(QRectF(-size * 2.4, -size * 0.45, size * 4.8, size * 0.9))
                p.restore()
            else:
                p.drawEllipse(QPointF(x, y), size, size)

        scratch = QColor(255, 143, 35, 38)
        p.setPen(QPen(scratch, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for offset in (-5.0, 0.0, 5.0):
            p.drawLine(QLineF(cx - 92.0, cy + 58.0 + offset, cx - 52.0, cy + 34.0 + offset))
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        phase = state.phase
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, start in enumerate((18.0, 151.0, 272.0)):
            radius = orbit_r - 32.0 + index * 10.0
            rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
            color = QColor(244, 126 + index * 18, 32, 56 + index * 18)
            p.setPen(
                QPen(
                    color,
                    1.15 + index * 0.18,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            animated_start = start + (0.0 if state.reduced_motion else phase * 24.0)
            p.drawArc(rect, int(animated_start * 16), int((42.0 + index * 9.0) * 16))
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del state
        p.save()
        color = QColor(255, 137, 32, 82)
        p.setPen(QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for link_index, (start, end) in enumerate(links):
            if link_index % 3 != 0:
                continue
            first, second = points[start], points[end]
            dx, dy = second.x() - first.x(), second.y() - first.y()
            length = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / length, dx / length
            for offset in (-2.3, 2.3):
                p.drawLine(
                    QLineF(
                        first.x() + nx * offset,
                        first.y() + ny * offset,
                        second.x() + nx * offset,
                        second.y() + ny * offset,
                    )
                )
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        outer = _radial_path(
            cx,
            cy,
            lambda angle: self._fur_radius(outer_r + 5.0, angle, phase),
            samples=216,
        )
        inner = _radial_path(
            cx,
            cy,
            lambda angle: self._fur_radius(outer_r - 18.0, angle, phase + 0.17),
            samples=216,
        )
        band = _radial_band(outer, inner)

        p.save()
        glow = QRadialGradient(cx, cy, outer_r + 18.0)
        glow.setColorAt(0.70, QColor(255, 120, 20, 0))
        glow.setColorAt(0.90, QColor(255, 126, 24, 58))
        glow.setColorAt(1.0, QColor(255, 157, 43, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), outer_r + 18.0, outer_r + 18.0)

        fur = QRadialGradient(cx, cy, outer_r + 12.0)
        fur.setColorAt(0.0, QColor(0, 0, 0, 0))
        fur.setColorAt(0.77, QColor(13, 8, 5, 248))
        fur.setColorAt(0.89, QColor(72, 31, 8, 246))
        fur.setColorAt(0.96, QColor(222, 103, 19, 242))
        fur.setColorAt(1.0, QColor(255, 186, 68, 198))
        p.setBrush(QBrush(fur))
        p.drawPath(band)

        p.save()
        p.setClipPath(band)
        for index in range(16):
            angle = index * math.tau / 16.0 + phase * math.tau * 0.035
            tangent = angle + math.pi / 2.0
            mid_r = outer_r - 5.0
            x = cx + math.cos(angle) * mid_r
            y = cy + math.sin(angle) * mid_r
            length = 24.0 + (index % 4) * 3.0
            stripe = QPainterPath()
            stripe.moveTo(
                x - math.cos(tangent) * length * 0.52,
                y - math.sin(tangent) * length * 0.52,
            )
            stripe.cubicTo(
                x - math.cos(tangent) * length * 0.12 - math.cos(angle) * 6.0,
                y - math.sin(tangent) * length * 0.12 - math.sin(angle) * 6.0,
                x + math.cos(tangent) * length * 0.16 + math.cos(angle) * 3.0,
                y + math.sin(tangent) * length * 0.16 + math.sin(angle) * 3.0,
                x + math.cos(tangent) * length * 0.50,
                y + math.sin(tangent) * length * 0.50,
            )
            p.setPen(
                QPen(
                    QColor(2, 3, 4, 205),
                    4.2 + index % 3,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(stripe)
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 190, 75, 112), 1.25))
        p.drawPath(outer)

        # Fine directional hairs break the silhouette into a flowing pelt.
        for index in range(52):
            angle = index * math.tau / 52.0
            root_r = self._fur_radius(outer_r + 1.0, angle, phase)
            hair_length = 3.0 + index % 5 * 1.15
            lean = math.sin(index * 1.91 + phase * math.tau) * 0.045
            start = QPointF(
                cx + math.cos(angle) * root_r,
                cy + math.sin(angle) * root_r,
            )
            end_angle = angle + lean
            end = QPointF(
                cx + math.cos(end_angle) * (root_r + hair_length),
                cy + math.sin(end_angle) * (root_r + hair_length),
            )
            hair_color = QColor(
                255,
                139 + index % 4 * 17,
                35,
                72 + index % 3 * 24,
            )
            p.setPen(
                QPen(
                    hair_color,
                    0.65 + index % 3 * 0.18,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawLine(QLineF(start, end))

        flash = 0.0
        if not state.reduced_motion:
            flash = max(0.0, (math.sin(phase * math.tau * 1.7) - 0.83) / 0.17)
        if flash > 0.0:
            p.setPen(
                QPen(
                    QColor(255, 220, 146, int(190 * flash)),
                    2.0,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            for offset in (-5.0, 0.0, 5.0):
                p.drawArc(
                    QRectF(
                        cx - outer_r - offset,
                        cy - outer_r - offset,
                        (outer_r + offset) * 2.0,
                        (outer_r + offset) * 2.0,
                    ),
                    28 * 16,
                    18 * 16,
                )
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.45, radius * 1.35)
        shadow.setColorAt(0.0, QColor(18, 6, 0, 118))
        shadow.setColorAt(1.0, QColor(18, 6, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.35, radius * 1.35)

    def _draw_tiger_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        phase = state.phase
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        base = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        base.setColorAt(0.0, QColor(255, 184, 72, 242))
        base.setColorAt(0.42, QColor(174, 77, 14, 236))
        base.setColorAt(1.0, QColor(42, 14, 5, 248))
        p.setBrush(QBrush(base))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        stripe_alpha = 178 if state.hovered else 142
        stripes = (
            (-1.0, -0.70, -0.16, -0.43),
            (-1.0, -0.12, -0.34, -0.04),
            (-1.0, 0.55, -0.14, 0.34),
            (1.0, -0.48, 0.24, -0.26),
            (1.0, 0.20, 0.31, 0.10),
            (1.0, 0.74, 0.18, 0.46),
        )
        p.setPen(Qt.PenStyle.NoPen)
        for index, (side, root_y, tip_x, tip_y) in enumerate(stripes):
            root_x = cx + side * radius * 1.04
            root_center_y = cy + root_y * radius
            tip = QPointF(cx + tip_x * radius, cy + tip_y * radius)
            stripe = QPainterPath()
            stripe.moveTo(root_x, root_center_y - radius * 0.13)
            stripe.cubicTo(
                cx + side * radius * 0.66,
                root_center_y - radius * 0.10,
                tip.x() + side * radius * 0.12,
                tip.y() - radius * 0.04,
                tip.x(),
                tip.y(),
            )
            stripe.cubicTo(
                tip.x() + side * radius * 0.12,
                tip.y() + radius * 0.04,
                cx + side * radius * 0.66,
                root_center_y + radius * 0.10,
                root_x,
                root_center_y + radius * 0.13,
            )
            stripe.closeSubpath()
            stripe_color = QColor(
                3,
                5,
                6,
                stripe_alpha + index % 2 * 16,
            )
            p.setBrush(stripe_color)
            p.drawPath(stripe)

        sheen = QRadialGradient(
            cx - radius * 0.40,
            cy - radius * 0.56,
            radius * 1.08,
        )
        sheen.setColorAt(0.0, QColor(255, 247, 211, 142))
        sheen.setColorAt(0.45, QColor(255, 197, 102, 35))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(sheen))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        if state.hovered and not state.reduced_motion:
            sweep = ((phase * 4.0) % 1.0) * radius * 2.8 - radius * 1.4
            p.setPen(
                QPen(
                    QColor(255, 235, 180, 155),
                    1.3,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            for offset in (-4.0, 0.0, 4.0):
                p.drawLine(
                    QLineF(
                        cx + sweep - radius * 0.28,
                        cy - radius + offset,
                        cx + sweep + radius * 0.34,
                        cy + radius + offset,
                    )
                )
        p.restore()

        inner = QColor(255, 209, 126, 82 if state.hovered else 50)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(inner, 1.0))
        p.drawEllipse(QPointF(cx, cy), radius - 1.2, radius - 1.2)
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_tiger_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_tiger_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        impact = radius * (1.0 + progress * 0.82)
        color = QColor(255, 137, 31, int(155 * (1.0 - progress)))
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(color, 2.2 - progress * 1.1))
        p.drawEllipse(QPointF(cx, cy), impact, impact)
        p.restore()


class PurpleThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "purple",
        "floating amethyst facets and rune nodes",
        "faceted amethyst mist jelly",
        "diamond crystals and magic dust",
        "pointer-reactive facets and rune halo",
        "converging then dispersing violet energy",
        hover_scale=1.035,
        press_scale=0.95,
    )

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        diamond = _diamond_path(1.0, 1.35)
        for index in range(20):
            angle = math.radians((index * 137.508 + 31.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (0.13 + index % 3 * 0.02)
            radius = 40.0 + (index * 43) % int(orbit_r + 38.0)
            x = cx + math.cos(angle + drift) * radius
            y = cy + math.sin(angle + drift) * radius
            size = 1.2 + index % 4 * 0.65
            p.save()
            p.translate(x, y)
            p.rotate(index * 29.0 + phase * 90.0)
            p.scale(size, size)
            p.setBrush(
                QColor(
                    192 + index % 2 * 35,
                    128 + index % 3 * 22,
                    255,
                    72 + index % 4 * 28,
                )
            )
            p.drawPath(diamond)
            p.restore()
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        phase = state.phase
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(12):
            angle = (
                index * math.tau / 12.0
                + (0.0 if state.reduced_motion else phase * math.tau * 0.045)
            )
            radius = orbit_r - 30.0 + (index % 2) * 9.0
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            p.save()
            p.translate(x, y)
            p.rotate(math.degrees(angle) + 45.0)
            p.setPen(QPen(QColor(209, 172, 255, 74), 0.9))
            p.drawPath(_diamond_path(3.0, 4.8))
            if index % 3 == 0:
                p.drawLine(QLineF(-6.0, 0.0, 6.0, 0.0))
            p.restore()
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links, state
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(216, 177, 255, 110), 0.85))
        rune = _diamond_path(2.7, 3.8)
        for index, point in enumerate(points):
            if index % 2:
                continue
            p.save()
            p.translate(point)
            p.rotate(index * 23.0)
            p.drawPath(rune)
            p.restore()
        p.restore()

    @staticmethod
    def _draw_crystal(
        p: QPainter,
        x: float,
        y: float,
        width: float,
        height: float,
        rotation: float,
        alpha: int,
    ) -> None:
        p.save()
        p.translate(x, y)
        p.rotate(rotation)
        crystal = _diamond_path(width, height)
        fill = QLinearGradient(-width, -height, width, height)
        fill.setColorAt(0.0, QColor(244, 222, 255, alpha))
        fill.setColorAt(0.38, QColor(157, 87, 226, alpha))
        fill.setColorAt(1.0, QColor(54, 20, 104, alpha))
        p.setPen(QPen(QColor(232, 205, 255, min(235, alpha + 40)), 0.85))
        p.setBrush(QBrush(fill))
        p.drawPath(crystal)
        p.setPen(QPen(QColor(255, 245, 255, min(190, alpha)), 0.65))
        p.drawLine(QLineF(0.0, -height, 0.0, height))
        p.drawLine(QLineF(-width, 0.0, 0.0, height))
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        mist = QRadialGradient(cx, cy, outer_r + 22.0)
        mist.setColorAt(0.70, QColor(117, 45, 176, 0))
        mist.setColorAt(0.90, QColor(132, 63, 206, 42))
        mist.setColorAt(1.0, QColor(78, 33, 132, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(mist))
        p.drawEllipse(QPointF(cx, cy), outer_r + 22.0, outer_r + 22.0)

        for index in range(18):
            angle = (
                index * math.tau / 18.0
                + (0.0 if state.reduced_motion else phase * math.tau * 0.055)
            )
            radius = outer_r + math.sin(index * 1.73) * 5.5
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            width = 5.2 + index % 3 * 1.25
            height = 11.0 + index % 4 * 1.8
            self._draw_crystal(
                p,
                x,
                y,
                width,
                height,
                math.degrees(angle) + 90.0 + math.sin(index) * 18.0,
                178 + index % 3 * 18,
            )

        for index in range(9):
            angle = (
                index * math.tau / 9.0
                - (0.0 if state.reduced_motion else phase * math.tau * 0.025)
            )
            radius = outer_r - 21.0
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            p.save()
            p.translate(x, y)
            p.rotate(math.degrees(angle) + 45.0)
            p.setPen(QPen(QColor(205, 165, 255, 112), 0.85))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(_diamond_path(3.8, 5.6))
            p.restore()
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.38, radius * 1.38)
        shadow.setColorAt(0.0, QColor(42, 10, 82, 108))
        shadow.setColorAt(1.0, QColor(42, 10, 82, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.38, radius * 1.38)

    def _draw_amethyst_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        phase = state.phase
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        base = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        base.setColorAt(0.0, QColor(224, 190, 255, 226))
        base.setColorAt(0.36, QColor(142, 75, 207, 222))
        base.setColorAt(0.72, QColor(79, 34, 137, 235))
        base.setColorAt(1.0, QColor(30, 15, 66, 246))
        p.setBrush(QBrush(base))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        for index in range(3):
            angle = phase * math.tau * (0.12 + index * 0.03) + index * 2.1
            mx = cx + math.cos(angle) * radius * 0.32
            my = cy + math.sin(angle) * radius * 0.28
            fog = QRadialGradient(mx, my, radius * 0.72)
            fog.setColorAt(
                0.0,
                QColor(
                    196 + index * 18,
                    105 + index * 25,
                    255,
                    54,
                ),
            )
            fog.setColorAt(1.0, QColor(118, 57, 190, 0))
            p.setBrush(QBrush(fog))
            p.drawEllipse(QPointF(mx, my), radius * 0.75, radius * 0.62)

        pointer_x = max(-1.0, min(1.0, state.pointer_offset_x))
        pointer_y = max(-1.0, min(1.0, state.pointer_offset_y))
        highlight = QRadialGradient(
            cx - radius * 0.36 + pointer_x * radius * 0.24,
            cy - radius * 0.42 + pointer_y * radius * 0.20,
            radius,
        )
        highlight.setColorAt(0.0, QColor(255, 247, 255, 168 if state.hovered else 104))
        highlight.setColorAt(0.45, QColor(229, 193, 255, 30))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(highlight))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        facet_pen = QPen(QColor(239, 218, 255, 88 if state.hovered else 54), 0.85)
        p.setPen(facet_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QLineF(cx - radius, cy - radius * 0.12, cx, cy + radius))
        p.drawLine(QLineF(cx - radius * 0.45, cy - radius, cx + radius, cy + radius * 0.10))
        p.drawLine(QLineF(cx, cy + radius, cx + radius * 0.58, cy - radius))
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(236, 211, 255, 104 if state.hovered else 62), 0.9))
        p.drawEllipse(QPointF(cx, cy), radius - 0.9, radius - 0.9)

        if state.hovered:
            rune_radius = radius + 5.6
            rune = _diamond_path(1.2, 2.0)
            for index in range(8):
                angle = (
                    index * math.tau / 8.0
                    + (0.0 if state.reduced_motion else phase * math.tau * 0.35)
                )
                p.save()
                p.translate(
                    cx + math.cos(angle) * rune_radius,
                    cy + math.sin(angle) * rune_radius,
                )
                p.rotate(math.degrees(angle))
                p.setPen(QPen(QColor(229, 198, 255, 142), 0.7))
                p.drawPath(rune)
                p.restore()
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_amethyst_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_amethyst_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        converging = progress < 0.46
        local = progress / 0.46 if converging else (progress - 0.46) / 0.54
        particle_radius = (
            radius * (1.52 - local * 0.86)
            if converging
            else radius * (0.66 + local * 1.08)
        )
        alpha = int(190 * (1.0 - progress * 0.72))
        for index in range(8):
            angle = index * math.tau / 8.0 + progress * 0.45
            p.setBrush(QColor(219, 174, 255, alpha))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * particle_radius,
                    cy + math.sin(angle) * particle_radius,
                ),
                1.7,
                1.7,
            )
        if not converging:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(178, 105, 245, int(130 * (1.0 - local))), 1.3))
            p.drawEllipse(QPointF(cx, cy), particle_radius, particle_radius)
        p.restore()


class IceThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "ice",
        "jagged frost shelf with transparent fractures",
        "matte frozen glass jelly",
        "ice dust, sparse snow, and cold mist",
        "progressive frost crystallization",
        "temporary branching ice fracture",
        hover_scale=1.045,
        press_scale=0.945,
    )

    @staticmethod
    def _ice_radius(radius: float, angle: float, phase: float) -> float:
        facets = abs(math.sin(angle * 17.0 + 0.45)) * 4.8
        shimmer = math.sin(angle * 7.0 - phase * math.tau * 0.08) * 2.1
        return radius + facets + shimmer

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.click_progress > 0.0:
            return 1.0 - math.sin(state.click_progress * math.pi) * 0.055
        return super().button_scale(state)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(15):
            angle = math.radians((index * 137.508 + 11.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (0.08 + index % 3 * 0.018)
            radius = 42.0 + (index * 47) % int(orbit_r + 33.0)
            x = cx + math.cos(angle + drift) * radius
            y = cy + math.sin(angle + drift) * radius
            size = 0.65 + index % 4 * 0.38
            color = QColor(210, 248, 255, 72 + index % 4 * 23)
            p.setBrush(color)
            if index % 5 == 0:
                p.save()
                p.translate(x, y)
                p.rotate(index * 31.0)
                p.drawPath(_diamond_path(size * 0.75, size * 2.4))
                p.restore()
            else:
                p.drawEllipse(QPointF(x, y), size, size)

        # Sparse cold-air streams; low alpha keeps labels and constellation crisp.
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(3):
            y = cy - 74.0 + index * 69.0
            offset = 0.0 if state.reduced_motion else math.sin(phase * math.tau + index) * 8.0
            mist = QPainterPath()
            mist.moveTo(cx - 122.0 + offset, y)
            mist.cubicTo(
                cx - 52.0,
                y - 13.0,
                cx + 36.0,
                y + 12.0,
                cx + 118.0 + offset,
                y - 3.0,
            )
            p.setPen(
                QPen(
                    QColor(181, 236, 248, 24 + index * 7),
                    4.2 - index * 0.7,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(mist)
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, start in enumerate((14.0, 119.0, 241.0)):
            radius = orbit_r - 31.0 + index * 10.0
            rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
            color = QColor(166, 228, 244, 42 + index * 16)
            p.setPen(QPen(color, 0.8 + index * 0.18))
            phase_shift = 0.0 if state.reduced_motion else state.phase * 10.0
            p.drawArc(
                rect,
                int((start + phase_shift) * 16),
                int((31.0 + index * 8.0) * 16),
            )
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links, state
        p.save()
        p.setPen(
            QPen(
                QColor(210, 249, 255, 98),
                0.72,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        for index, point in enumerate(points):
            if index % 3:
                continue
            for angle in (0.0, math.pi / 3.0, math.pi * 2.0 / 3.0):
                dx = math.cos(angle) * 4.2
                dy = math.sin(angle) * 4.2
                p.drawLine(
                    QLineF(
                        point.x() - dx,
                        point.y() - dy,
                        point.x() + dx,
                        point.y() + dy,
                    )
                )
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        outer = _radial_path(
            cx,
            cy,
            lambda angle: self._ice_radius(outer_r + 1.0, angle, phase),
            samples=216,
        )
        inner = _radial_path(
            cx,
            cy,
            lambda angle: outer_r
            - 20.0
            + math.sin(angle * 13.0 + 0.8) * 2.2,
            samples=216,
        )
        band = _radial_band(outer, inner)

        p.save()
        halo = QRadialGradient(cx, cy, outer_r + 22.0)
        halo.setColorAt(0.72, QColor(102, 215, 245, 0))
        halo.setColorAt(0.91, QColor(122, 229, 255, 48))
        halo.setColorAt(1.0, QColor(221, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(cx, cy), outer_r + 22.0, outer_r + 22.0)

        ice = QRadialGradient(cx, cy, outer_r + 14.0)
        ice.setColorAt(0.0, QColor(0, 0, 0, 0))
        ice.setColorAt(0.76, QColor(10, 48, 76, 224))
        ice.setColorAt(0.87, QColor(37, 121, 164, 225))
        ice.setColorAt(0.96, QColor(166, 232, 244, 216))
        ice.setColorAt(1.0, QColor(244, 255, 255, 232))
        p.setBrush(QBrush(ice))
        p.drawPath(band)

        p.save()
        p.setClipPath(band)
        for index in range(15):
            angle = index * math.tau / 15.0 + 0.08
            inner_r = outer_r - 18.0
            outer_edge = self._ice_radius(outer_r + 2.0, angle, phase)
            start = QPointF(
                cx + math.cos(angle) * inner_r,
                cy + math.sin(angle) * inner_r,
            )
            middle_angle = angle + math.sin(index * 2.3) * 0.035
            middle_r = (inner_r + outer_edge) * 0.52
            middle = QPointF(
                cx + math.cos(middle_angle) * middle_r,
                cy + math.sin(middle_angle) * middle_r,
            )
            end_angle = angle - math.sin(index * 1.7) * 0.028
            end = QPointF(
                cx + math.cos(end_angle) * outer_edge,
                cy + math.sin(end_angle) * outer_edge,
            )
            crack = QPainterPath(start)
            crack.lineTo(middle)
            crack.lineTo(end)
            p.setPen(
                QPen(
                    QColor(7, 61, 98, 126),
                    2.2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(crack)
            p.setPen(
                QPen(
                    QColor(225, 253, 255, 116 + index % 3 * 20),
                    0.75,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(crack)
            branch_angle = middle_angle + (0.10 if index % 2 else -0.10)
            branch = QPointF(
                middle.x() + math.cos(branch_angle) * 8.0,
                middle.y() + math.sin(branch_angle) * 8.0,
            )
            p.drawLine(QLineF(middle, branch))
        p.restore()

        # Faceted shards sit outside the shelf and keep its silhouette icy.
        for index in range(18):
            angle = index * math.tau / 18.0 + 0.04
            base_r = self._ice_radius(outer_r - 1.0, angle, phase)
            tip_r = base_r + 5.0 + index % 4 * 2.1
            angular_width = 0.020 + index % 3 * 0.004
            shard = QPainterPath()
            shard.moveTo(
                cx + math.cos(angle - angular_width) * base_r,
                cy + math.sin(angle - angular_width) * base_r,
            )
            shard.lineTo(
                cx + math.cos(angle) * tip_r,
                cy + math.sin(angle) * tip_r,
            )
            shard.lineTo(
                cx + math.cos(angle + angular_width) * base_r,
                cy + math.sin(angle + angular_width) * base_r,
            )
            shard.closeSubpath()
            shard_fill = QLinearGradient(
                cx + math.cos(angle) * base_r,
                cy + math.sin(angle) * base_r,
                cx + math.cos(angle) * tip_r,
                cy + math.sin(angle) * tip_r,
            )
            shard_fill.setColorAt(0.0, QColor(84, 174, 207, 126))
            shard_fill.setColorAt(1.0, QColor(239, 255, 255, 210))
            p.setPen(QPen(QColor(226, 252, 255, 132), 0.65))
            p.setBrush(QBrush(shard_fill))
            p.drawPath(shard)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(239, 255, 255, 178), 1.25))
        p.drawPath(outer)

        for index in range(5):
            angle = index * math.tau / 5.0 + phase * math.tau * 0.04
            radius = self._ice_radius(outer_r + 3.0, angle, phase)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            pulse = 0.45 + math.sin(phase * math.tau * 1.4 + index) * 0.35
            alpha = int(85 + max(0.0, pulse) * 145)
            p.setPen(QPen(QColor(245, 255, 255, alpha), 1.0))
            p.drawLine(QLineF(x - 4.0, y, x + 4.0, y))
            p.drawLine(QLineF(x, y - 4.0, x, y + 4.0))
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.42, radius * 1.36)
        shadow.setColorAt(0.0, QColor(2, 39, 73, 92))
        shadow.setColorAt(1.0, QColor(2, 39, 73, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.36, radius * 1.36)

    @staticmethod
    def _draw_frost_branch(
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        angle: float,
        length_scale: float,
    ) -> None:
        end_r = radius * length_scale
        end = QPointF(
            cx + math.cos(angle) * end_r,
            cy + math.sin(angle) * end_r,
        )
        middle = QPointF(
            cx + math.cos(angle + 0.03) * end_r * 0.52,
            cy + math.sin(angle + 0.03) * end_r * 0.52,
        )
        path = QPainterPath(QPointF(cx, cy))
        path.lineTo(middle)
        path.lineTo(end)
        p.drawPath(path)
        tangent = angle + math.pi / 2.0
        branch_length = radius * 0.17
        for sign in (-1.0, 1.0):
            branch = QPointF(
                middle.x()
                + math.cos(tangent) * branch_length * sign
                + math.cos(angle) * branch_length * 0.45,
                middle.y()
                + math.sin(tangent) * branch_length * sign
                + math.sin(angle) * branch_length * 0.45,
            )
            p.drawLine(QLineF(middle, branch))

    def _draw_frozen_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        frozen = QLinearGradient(cx, cy - radius, cx, cy + radius)
        frozen.setColorAt(0.0, QColor(244, 255, 255, 236))
        frozen.setColorAt(0.28, QColor(183, 231, 242, 226))
        frozen.setColorAt(0.58, QColor(54, 133, 179, 226))
        frozen.setColorAt(1.0, QColor(5, 45, 83, 244))
        p.setBrush(QBrush(frozen))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        frost = QRadialGradient(
            cx - radius * 0.32,
            cy - radius * 0.55,
            radius * 1.05,
        )
        frost.setColorAt(0.0, QColor(255, 255, 255, 178))
        frost.setColorAt(0.48, QColor(224, 252, 255, 50))
        frost.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(frost))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        ambient_alpha = 28 + int(state.hover_progress * 94)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(237, 255, 255, ambient_alpha),
                0.72 + state.hover_progress * 0.35,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        for index in range(4):
            angle = index * math.tau / 4.0 + 0.42
            start_x = cx + math.cos(angle) * radius * 0.34
            start_y = cy + math.sin(angle) * radius * 0.34
            self._draw_frost_branch(
                p,
                start_x,
                start_y,
                radius * 0.58,
                angle,
                0.74,
            )
        p.restore()

        frost_amount = max(state.hover_progress, 0.18 if state.hovered else 0.0)
        if frost_amount > 0.0:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(
                QPen(
                    QColor(245, 255, 255, int(55 + 170 * frost_amount)),
                    0.8 + frost_amount * 0.65,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            for index in range(14):
                angle = index * math.tau / 14.0
                inner_r = radius * (0.88 - frost_amount * 0.05)
                outer_r = radius * (0.95 + frost_amount * (0.09 + index % 3 * 0.02))
                p.drawLine(
                    QLineF(
                        cx + math.cos(angle) * inner_r,
                        cy + math.sin(angle) * inner_r,
                        cx + math.cos(angle) * outer_r,
                        cy + math.sin(angle) * outer_r,
                    )
                )
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_frozen_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_frozen_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        alpha = int(225 * (1.0 - progress))
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(225, 253, 255, alpha),
                1.05,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        for index in range(7):
            angle = index * math.tau / 7.0 + 0.16
            self._draw_frost_branch(
                p,
                cx,
                cy,
                radius,
                angle,
                0.35 + progress * 0.58,
            )
        p.restore()


class LavaThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "lava",
        "fractured obsidian with flowing magma seams",
        "dark translucent molten jelly",
        "embers, sparks, and rising heat",
        "accelerated magma and sparks",
        "recoil with a molten burst wave",
        hover_scale=1.06,
        press_scale=0.92,
    )

    @staticmethod
    def _rock_radius(radius: float, angle: float, phase: float) -> float:
        del phase
        return radius + (
            math.sin(angle * 9.0 + 0.7) * 2.5
            + math.sin(angle * 19.0 - 0.2) * 2.0
            + abs(math.sin(angle * 13.0 + 1.1)) * 3.4
        )

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.click_progress > 0.0:
            progress = state.click_progress
            if progress < 0.30:
                return 1.0 - progress / 0.30 * 0.10
            return 0.90 + (progress - 0.30) / 0.70 * 0.10
        return super().button_scale(state)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        span = orbit_r * 2.75
        for index in range(18):
            x = cx - orbit_r * 1.12 + ((index * 53) % int(orbit_r * 2.24))
            base_y = cy + orbit_r * 1.08 - (index % 5) * 18.0
            rise = 0.0 if state.reduced_motion else phase * span * (0.34 + index % 3 * 0.07)
            y = cy + orbit_r - ((base_y - cy + rise + orbit_r) % span)
            size = 0.8 + index % 4 * 0.45
            color = QColor(
                255,
                76 + index % 4 * 28,
                18,
                80 + index % 5 * 24,
            )
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), size * 1.25, size)

        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(3):
            heat = QPainterPath()
            x = cx - 75.0 + index * 74.0
            heat.moveTo(x, cy + 105.0)
            heat.cubicTo(
                x - 13.0,
                cy + 58.0,
                x + 15.0,
                cy + 17.0,
                x - 3.0,
                cy - 32.0,
            )
            p.setPen(
                QPen(
                    QColor(255, 111, 41, 18 + index * 6),
                    3.8 - index * 0.6,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(heat)
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, start in enumerate((22.0, 142.0, 265.0)):
            radius = orbit_r - 33.0 + index * 10.0
            rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
            color = QColor(176, 49 + index * 15, 17, 45 + index * 16)
            p.setPen(
                QPen(
                    color,
                    1.0 + index * 0.25,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            drift = 0.0 if state.reduced_motion else state.phase * 15.0
            p.drawArc(rect, int((start + drift) * 16), int((38 + index * 7) * 16))
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links, state
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index, point in enumerate(points):
            if index % 2:
                continue
            glow = QRadialGradient(point, 6.0)
            glow.setColorAt(0.0, QColor(255, 178, 66, 150))
            glow.setColorAt(1.0, QColor(255, 76, 20, 0))
            p.setBrush(QBrush(glow))
            p.drawEllipse(point, 6.0, 6.0)
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        outer = _radial_path(
            cx,
            cy,
            lambda angle: self._rock_radius(outer_r + 3.0, angle, phase),
            samples=208,
        )
        inner = _radial_path(
            cx,
            cy,
            lambda angle: outer_r
            - 21.0
            + math.sin(angle * 11.0 + 1.3) * 2.4,
            samples=208,
        )
        band = _radial_band(outer, inner)

        p.save()
        glow = QRadialGradient(cx, cy, outer_r + 20.0)
        glow.setColorAt(0.72, QColor(255, 55, 8, 0))
        glow.setColorAt(0.91, QColor(255, 67, 9, 66))
        glow.setColorAt(1.0, QColor(255, 111, 20, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), outer_r + 20.0, outer_r + 20.0)

        rock = QRadialGradient(cx, cy, outer_r + 13.0)
        rock.setColorAt(0.0, QColor(0, 0, 0, 0))
        rock.setColorAt(0.75, QColor(7, 6, 7, 250))
        rock.setColorAt(0.88, QColor(25, 18, 18, 250))
        rock.setColorAt(0.96, QColor(50, 23, 18, 248))
        rock.setColorAt(1.0, QColor(12, 8, 9, 250))
        p.setBrush(QBrush(rock))
        p.drawPath(band)

        p.save()
        p.setClipPath(band)
        flow = phase * math.tau * 0.13
        for index in range(14):
            angle = index * math.tau / 14.0 + flow
            inner_r = outer_r - 20.0
            outer_edge = self._rock_radius(outer_r + 5.0, angle, phase)
            start = QPointF(
                cx + math.cos(angle - 0.025) * inner_r,
                cy + math.sin(angle - 0.025) * inner_r,
            )
            mid_angle = angle + math.sin(index * 2.1) * 0.045
            middle_r = (inner_r + outer_edge) * 0.51
            middle = QPointF(
                cx + math.cos(mid_angle) * middle_r,
                cy + math.sin(mid_angle) * middle_r,
            )
            end = QPointF(
                cx + math.cos(angle + 0.018) * outer_edge,
                cy + math.sin(angle + 0.018) * outer_edge,
            )
            seam = QPainterPath(start)
            seam.lineTo(middle)
            seam.lineTo(end)
            pulse = 0.72 + math.sin(phase * math.tau * 1.2 + index) * 0.24
            p.setPen(
                QPen(
                    QColor(129, 24, 6, int(150 * pulse)),
                    4.8,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(seam)
            p.setPen(
                QPen(
                    QColor(255, 94 + index % 3 * 28, 18, int(220 * pulse)),
                    1.45,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(seam)
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(116, 43, 22, 135), 1.0))
        p.drawPath(outer)
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.45, radius * 1.40)
        shadow.setColorAt(0.0, QColor(34, 4, 0, 122))
        shadow.setColorAt(1.0, QColor(34, 4, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.40, radius * 1.40)

    def _draw_lava_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        lava = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        lava.setColorAt(0.0, QColor(128, 39, 29, 226))
        lava.setColorAt(0.42, QColor(74, 14, 16, 238))
        lava.setColorAt(1.0, QColor(20, 5, 8, 250))
        p.setBrush(QBrush(lava))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        speed = 0.42 if state.hovered else 0.17
        flow = state.phase * math.tau * speed
        for index in range(4):
            y_offset = (-0.66 + index * 0.44) * radius
            vein = QPainterPath()
            for step in range(15):
                x = cx - radius + radius * 2.0 * step / 14.0
                y = (
                    cy
                    + y_offset
                    + math.sin(step * 0.72 + flow + index * 1.4)
                    * radius
                    * 0.12
                )
                if step == 0:
                    vein.moveTo(x, y)
                else:
                    vein.lineTo(x, y)
            brightness = 1.0 if state.hovered else 0.72
            p.setPen(
                QPen(
                    QColor(135, 25, 7, int(120 * brightness)),
                    4.2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(vein)
            p.setPen(
                QPen(
                    QColor(255, 79 + index * 17, 17, int(205 * brightness)),
                    1.15,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(vein)

        heat = QRadialGradient(
            cx - radius * 0.32,
            cy - radius * 0.45,
            radius * 1.10,
        )
        heat.setColorAt(0.0, QColor(255, 170, 82, 104 if state.hovered else 62))
        heat.setColorAt(0.55, QColor(255, 75, 20, 20))
        heat.setColorAt(1.0, QColor(255, 44, 10, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(heat))
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        p.restore()

        if state.hovered:
            p.setPen(Qt.PenStyle.NoPen)
            for index in range(5):
                angle = index * math.tau / 5.0 + state.phase * math.tau * 0.9
                spark_r = radius * (1.05 + index % 2 * 0.13)
                p.setBrush(QColor(255, 129, 35, 155 - index * 14))
                p.drawEllipse(
                    QPointF(
                        cx + math.cos(angle) * spark_r,
                        cy + math.sin(angle) * spark_r,
                    ),
                    1.15,
                    0.85,
                )
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_lava_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_lava_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        wave_r = radius * (1.0 + progress * 0.90)
        p.setPen(
            QPen(
                QColor(255, 79, 14, int(190 * (1.0 - progress))),
                2.6 - progress * 1.3,
            )
        )
        p.drawEllipse(QPointF(cx, cy), wave_r, wave_r)
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(7):
            angle = index * math.tau / 7.0 + 0.3
            shard_r = radius * (0.70 + progress * 1.45)
            p.setBrush(QColor(255, 127, 35, int(175 * (1.0 - progress))))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * shard_r,
                    cy + math.sin(angle) * shard_r,
                ),
                1.7,
                1.0,
            )
        p.restore()


class CosmicThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "cosmic",
        "multi-speed planetary orbit system",
        "deep-space nebula jelly",
        "star dust, meteors, and faint nebula",
        "accelerated inner stars and gravity lens",
        "gravitational compression and star-dust release",
        hover_scale=1.045,
        press_scale=0.94,
    )

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.click_progress > 0.0:
            return 1.0 - math.sin(state.click_progress * math.pi) * 0.12
        return super().button_scale(state)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        nebula = QRadialGradient(
            cx - orbit_r * 0.35,
            cy + orbit_r * 0.12,
            orbit_r * 1.45,
        )
        nebula.setColorAt(0.0, QColor(117, 70, 218, 42))
        nebula.setColorAt(0.46, QColor(32, 88, 180, 22))
        nebula.setColorAt(1.0, QColor(16, 24, 74, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(nebula))
        p.drawEllipse(QPointF(cx, cy), orbit_r + 60.0, orbit_r + 60.0)

        for index in range(30):
            angle = math.radians((index * 137.508 + 7.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (0.04 + index % 4 * 0.008)
            radius = 36.0 + (index * 61) % int(orbit_r + 48.0)
            x = cx + math.cos(angle + drift) * radius
            y = cy + math.sin(angle + drift) * radius
            size = 0.55 + index % 5 * 0.24
            color = QColor(
                194 + index % 3 * 20,
                213 + index % 2 * 24,
                255,
                62 + index % 6 * 23,
            )
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), size, size)

        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(2):
            angle = -0.62 + index * 2.55
            radius = orbit_r * (0.66 + index * 0.25)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            trail = QPainterPath(QPointF(x, y))
            trail.lineTo(
                x - math.cos(angle) * 24.0,
                y - math.sin(angle) * 24.0,
            )
            p.setPen(
                QPen(
                    QColor(185, 220, 255, 54),
                    1.2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(trail)
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del p, cx, cy, orbit_r, slot_count, rotation, state

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links, state
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, point in enumerate(points):
            color = QColor(154, 184, 255, 72 + index % 3 * 22)
            p.setPen(QPen(color, 0.75))
            p.drawEllipse(point, 3.2 + index % 2, 3.2 + index % 2)
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        orbit_specs = (
            (0.84, 0.56, -22.0, 0.11, QColor(117, 145, 255, 90)),
            (0.95, 0.69, 18.0, -0.075, QColor(170, 113, 255, 104)),
            (1.04, 0.82, -8.0, 0.052, QColor(106, 209, 255, 82)),
            (1.12, 0.94, 31.0, -0.035, QColor(230, 196, 255, 68)),
        )
        p.save()
        for index, (rx_scale, ry_scale, rotation_deg, speed, color) in enumerate(
            orbit_specs
        ):
            rotation = math.radians(rotation_deg)
            rx = outer_r * rx_scale
            ry = outer_r * ry_scale
            p.save()
            p.translate(cx, cy)
            p.rotate(rotation_deg)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(
                QPen(
                    color,
                    0.9 + index * 0.14,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawEllipse(QRectF(-rx, -ry, rx * 2.0, ry * 2.0))
            p.restore()

            travel = index * 1.62 + phase * math.tau * speed * 8.0
            planet = _rotated_ellipse_point(
                cx,
                cy,
                rx,
                ry,
                rotation,
                travel,
            )
            planet_radius = 2.4 + index * 0.95
            planet_fill = QRadialGradient(
                planet.x() - planet_radius * 0.35,
                planet.y() - planet_radius * 0.35,
                planet_radius * 1.4,
            )
            planet_fill.setColorAt(0.0, QColor(249, 246, 255, 238))
            planet_fill.setColorAt(0.38, color.lighter(155))
            planet_fill.setColorAt(1.0, color.darker(170))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(planet_fill))
            p.drawEllipse(planet, planet_radius, planet_radius)

        for index in range(9):
            angle = index * math.tau / 9.0 + phase * math.tau * 0.025
            radius = outer_r * (0.96 + index % 2 * 0.08)
            p.setBrush(QColor(211, 224, 255, 112 + index % 3 * 30))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius,
                ),
                1.0 + index % 2 * 0.45,
                1.0 + index % 2 * 0.45,
            )
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.35, radius * 1.44)
        shadow.setColorAt(0.0, QColor(8, 10, 54, 116))
        shadow.setColorAt(1.0, QColor(8, 10, 54, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.44, radius * 1.44)

    def _draw_cosmic_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        space = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        space.setColorAt(0.0, QColor(65, 89, 184, 226))
        space.setColorAt(0.42, QColor(27, 42, 116, 238))
        space.setColorAt(1.0, QColor(7, 12, 47, 250))
        p.setBrush(QBrush(space))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        nebula = QRadialGradient(
            cx - radius * 0.28,
            cy + radius * 0.12,
            radius * 1.10,
        )
        nebula.setColorAt(0.0, QColor(186, 94, 237, 88))
        nebula.setColorAt(0.46, QColor(64, 126, 227, 36))
        nebula.setColorAt(1.0, QColor(27, 41, 116, 0))
        p.setBrush(QBrush(nebula))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        speed = 0.88 if state.hovered else 0.18
        for index in range(11):
            angle = (
                index * math.tau / 11.0
                + state.phase * math.tau * speed
                + index * 0.21
            )
            star_r = radius * (0.18 + (index * 37 % 66) / 100.0)
            x = cx + math.cos(angle) * star_r
            y = cy + math.sin(angle) * star_r
            size = 0.55 + index % 3 * 0.35
            p.setBrush(QColor(230, 239, 255, 125 + index % 4 * 28))
            p.drawEllipse(QPointF(x, y), size, size)

        atmosphere = QRadialGradient(
            cx - radius * 0.40,
            cy - radius * 0.48,
            radius * 1.12,
        )
        atmosphere.setColorAt(0.0, QColor(239, 247, 255, 126))
        atmosphere.setColorAt(0.42, QColor(135, 178, 255, 34))
        atmosphere.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(atmosphere))
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        p.restore()

        if state.hovered:
            lens = QRadialGradient(cx, cy, radius * 1.34)
            lens.setColorAt(0.62, QColor(126, 169, 255, 0))
            lens.setColorAt(0.79, QColor(158, 192, 255, 72))
            lens.setColorAt(0.88, QColor(208, 220, 255, 18))
            lens.setColorAt(1.0, QColor(126, 169, 255, 0))
            p.setBrush(QBrush(lens))
            p.drawEllipse(QPointF(cx, cy), radius * 1.34, radius * 1.34)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(178, 205, 255, 90 if state.hovered else 52), 0.9))
        p.drawArc(
            QRectF(
                cx - radius + 1.0,
                cy - radius + 1.0,
                (radius - 1.0) * 2.0,
                (radius - 1.0) * 2.0,
            ),
            28 * 16,
            118 * 16,
        )
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_cosmic_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_cosmic_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        release = max(0.0, (progress - 0.35) / 0.65)
        dust_r = radius * (0.35 + release * 1.65)
        alpha = int(185 * (1.0 - release))
        for index in range(12):
            angle = index * math.tau / 12.0 + progress * 0.65
            p.setBrush(QColor(201, 217, 255, alpha))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * dust_r,
                    cy + math.sin(angle) * dust_r,
                ),
                1.25 + index % 2 * 0.45,
                1.25 + index % 2 * 0.45,
            )
        if release > 0.0:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(149, 183, 255, int(110 * (1.0 - release))), 1.1))
            p.drawEllipse(QPointF(cx, cy), dust_r, dust_r)
        p.restore()


class HalloweenThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "halloween",
        "broken spectral mist and soul tails",
        "deep violet soul jelly",
        "soul fire, occult marks, and distant wraiths",
        "spectral breathing and afterimage",
        "mist dissolution and reassembly",
        hover_scale=1.045,
        press_scale=0.94,
    )

    @staticmethod
    def _wraith_path(scale: float = 1.0) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(0.0, -13.0 * scale)
        path.cubicTo(
            8.5 * scale,
            -12.0 * scale,
            10.0 * scale,
            -4.0 * scale,
            7.0 * scale,
            2.0 * scale,
        )
        path.cubicTo(
            5.0 * scale,
            6.0 * scale,
            10.0 * scale,
            9.0 * scale,
            12.0 * scale,
            13.0 * scale,
        )
        path.cubicTo(
            6.0 * scale,
            10.0 * scale,
            3.0 * scale,
            17.0 * scale,
            -1.0 * scale,
            10.0 * scale,
        )
        path.cubicTo(
            -5.0 * scale,
            16.0 * scale,
            -7.0 * scale,
            9.0 * scale,
            -11.0 * scale,
            12.0 * scale,
        )
        path.cubicTo(
            -8.0 * scale,
            6.0 * scale,
            -5.5 * scale,
            4.0 * scale,
            -7.0 * scale,
            0.0,
        )
        path.cubicTo(
            -10.0 * scale,
            -6.0 * scale,
            -7.0 * scale,
            -12.0 * scale,
            0.0,
            -13.0 * scale,
        )
        path.closeSubpath()
        return path

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.click_progress > 0.0:
            return 1.0 - math.sin(state.click_progress * math.pi) * 0.08
        if state.hovered and not state.reduced_motion:
            return 1.04 + math.sin(state.phase * math.tau * 0.72) * 0.028
        return super().button_scale(state)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(11):
            angle = math.radians((index * 137.508 + 23.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (0.05 + index % 3 * 0.012)
            radius = 50.0 + (index * 59) % int(orbit_r + 32.0)
            x = cx + math.cos(angle + drift) * radius
            y = cy + math.sin(angle + drift) * radius
            flame_r = 2.0 + index % 3 * 0.65
            soul = QRadialGradient(x, y, flame_r * 3.2)
            soul.setColorAt(0.0, QColor(158, 255, 221, 150))
            soul.setColorAt(0.45, QColor(58, 205, 177, 74))
            soul.setColorAt(1.0, QColor(64, 68, 158, 0))
            p.setBrush(QBrush(soul))
            p.drawEllipse(QPointF(x, y), flame_r * 3.2, flame_r * 3.2)

        # Remote hooded silhouettes, kept faint and faceless.
        for index, angle in enumerate((0.55, 2.78, 4.58)):
            radius = orbit_r * (0.77 + index * 0.06)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            p.save()
            p.translate(x, y)
            p.rotate(math.degrees(angle) + 88.0)
            p.setBrush(QColor(33, 19, 65, 44 + index * 10))
            p.drawPath(self._wraith_path(0.62 + index * 0.08))
            p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(154, 111, 212, 52), 0.8))
        for index in range(5):
            angle = index * math.tau / 5.0 + 0.3
            radius = orbit_r * 0.58
            point = QPointF(
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            )
            p.save()
            p.translate(point)
            p.rotate(index * 36.0)
            p.drawPath(_diamond_path(2.8, 4.8))
            p.drawLine(QLineF(-4.5, 0.0, 4.5, 0.0))
            p.restore()
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, start in enumerate((0.25, 2.25, 4.48)):
            path = _polar_segment(
                cx,
                cy,
                start + state.phase * 0.10,
                0.60 + index * 0.08,
                lambda angle, index=index: orbit_r
                - 33.0
                + index * 8.0
                + math.sin(angle * 5.0 + index) * 2.0,
                samples=28,
            )
            p.setPen(
                QPen(
                    QColor(113, 79, 170, 40 + index * 16),
                    0.9 + index * 0.16,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(path)
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links
        p.save()
        pulse = 0.65 + math.sin(state.phase * math.tau) * 0.20
        p.setPen(Qt.PenStyle.NoPen)
        for index, point in enumerate(points):
            if index % 2:
                continue
            glow = QRadialGradient(point, 5.0)
            glow.setColorAt(0.0, QColor(116, 244, 214, int(125 * pulse)))
            glow.setColorAt(1.0, QColor(62, 185, 171, 0))
            p.setBrush(QBrush(glow))
            p.drawEllipse(point, 5.0, 5.0)
        p.restore()

    def _draw_wraith(
        self,
        p: QPainter,
        x: float,
        y: float,
        scale: float,
        rotation: float,
        alpha: int,
    ) -> None:
        p.save()
        p.translate(x, y)
        p.rotate(rotation)
        fill = QLinearGradient(0.0, -14.0 * scale, 0.0, 15.0 * scale)
        fill.setColorAt(0.0, QColor(192, 180, 241, alpha))
        fill.setColorAt(0.42, QColor(94, 75, 171, int(alpha * 0.82)))
        fill.setColorAt(1.0, QColor(53, 209, 183, 0))
        p.setPen(QPen(QColor(179, 240, 226, int(alpha * 0.48)), 0.7))
        p.setBrush(QBrush(fill))
        p.drawPath(self._wraith_path(scale))
        face = QRadialGradient(
            QPointF(0.0, -4.1 * scale),
            5.2 * scale,
        )
        face.setColorAt(0.0, QColor(4, 7, 20, int(alpha * 0.92)))
        face.setColorAt(0.62, QColor(15, 13, 43, int(alpha * 0.68)))
        face.setColorAt(1.0, QColor(44, 33, 84, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(face))
        p.drawEllipse(
            QPointF(0.0, -4.0 * scale),
            4.0 * scale,
            5.3 * scale,
        )
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        # Broken, breathing mist streams deliberately leave large gaps.
        for index in range(7):
            start = index * math.tau / 7.0 + phase * (0.08 + index % 2 * 0.03)
            span = 0.48 + index % 3 * 0.11
            radius_base = outer_r + (index % 3 - 1) * 6.0
            path = _polar_segment(
                cx,
                cy,
                start,
                span,
                lambda angle, index=index: radius_base
                + math.sin(angle * 9.0 + phase * math.tau + index) * 6.5
                + math.sin(angle * 21.0 + index) * 2.0,
                samples=34,
            )
            fade = 0.58 + math.sin(phase * math.tau * 0.72 + index) * 0.28
            aura = QColor(92, 58, 163, int(54 * fade))
            p.setPen(
                QPen(
                    aura,
                    13.0 + index % 2 * 4.0,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(path)
            core = QColor(
                115 + index % 2 * 35,
                112 + index % 3 * 18,
                211,
                int(112 * fade),
            )
            p.setPen(
                QPen(
                    core,
                    3.8 + index % 2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(path)

        for index in range(4):
            local_phase = phase * (0.105 + index * 0.018)
            angle = local_phase * math.tau + index * math.tau / 4.0
            radius = outer_r * (0.96 + index % 2 * 0.08)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            self._draw_wraith(
                p,
                x,
                y,
                0.82 + index % 2 * 0.12,
                math.degrees(angle) + 90.0,
                170 + index % 2 * 28,
            )
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + 4.0, radius * 1.46)
        shadow.setColorAt(0.0, QColor(36, 11, 70, 112))
        shadow.setColorAt(1.0, QColor(36, 11, 70, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.46, radius * 1.46)

    def _draw_soul_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        dissolve = (
            math.sin(state.click_progress * math.pi)
            if state.click_progress > 0.0
            else 0.0
        )
        body_alpha = int(244 * (1.0 - dissolve * 0.62))
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        soul = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        soul.setColorAt(0.0, QColor(123, 96, 188, body_alpha))
        soul.setColorAt(0.48, QColor(48, 27, 96, body_alpha))
        soul.setColorAt(1.0, QColor(12, 16, 43, body_alpha))
        p.setBrush(QBrush(soul))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        for index in range(3):
            angle = state.phase * math.tau * (0.08 + index * 0.025) + index * 2.2
            mx = cx + math.cos(angle) * radius * 0.28
            my = cy + math.sin(angle) * radius * 0.30
            mist = QRadialGradient(mx, my, radius * 0.72)
            mist.setColorAt(0.0, QColor(68, 232, 198, 66 + index * 8))
            mist.setColorAt(0.55, QColor(93, 89, 184, 28))
            mist.setColorAt(1.0, QColor(53, 35, 111, 0))
            p.setBrush(QBrush(mist))
            p.drawEllipse(QPointF(mx, my), radius * 0.74, radius * 0.62)
        p.restore()

        # Soft trailing edge; no hard ring.
        tail_alpha = 62 + int(state.hover_progress * 72)
        tail = QPainterPath()
        tail.moveTo(cx - radius * 0.52, cy + radius * 0.72)
        tail.cubicTo(
            cx - radius * 0.16,
            cy + radius * 1.12,
            cx + radius * 0.12,
            cy + radius * 0.80,
            cx + radius * 0.48,
            cy + radius * 1.02,
        )
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(65, 211, 187, tail_alpha),
                2.2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawPath(tail)

        if state.hovered:
            after_alpha = int(48 + state.hover_progress * 46)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(87, 67, 151, after_alpha))
            p.drawEllipse(
                QPointF(cx - 4.0, cy + 2.0),
                radius * 1.08,
                radius * 0.96,
            )
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_soul_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_soul_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        spread = radius * (0.35 + math.sin(progress * math.pi) * 1.25)
        alpha = int(160 * (1.0 - progress * 0.72))
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(12):
            angle = index * math.tau / 12.0 + progress * 0.55
            p.setBrush(
                QColor(
                    90 + index % 2 * 40,
                    148 + index % 3 * 24,
                    190,
                    alpha,
                )
            )
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * spread,
                    cy + math.sin(angle) * spread,
                ),
                1.7 + index % 2,
                1.1 + index % 3 * 0.35,
            )
        p.restore()


class KawaiiThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "kawaii",
        "elastic syrup and marshmallow waves",
        "pink-cream gummy jelly",
        "bubbles, miniature hearts, and soft glints",
        "pudding wobble with heart bubbles",
        "gummy compression and rebound",
        hover_scale=1.03,
        press_scale=0.91,
    )

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        colors = (
            QColor(255, 187, 214, 94),
            QColor(190, 226, 255, 82),
            QColor(207, 244, 222, 78),
            QColor(255, 224, 167, 86),
        )
        p.save()
        for index in range(14):
            angle = math.radians((index * 137.508 + 17.0) % 360.0)
            drift = 0.0 if state.reduced_motion else phase * (0.045 + index % 3 * 0.01)
            radius = 42.0 + (index * 51) % int(orbit_r + 38.0)
            x = cx + math.cos(angle + drift) * radius
            y = cy + math.sin(angle + drift) * radius
            size = 1.8 + index % 4 * 0.72
            color = colors[index % len(colors)]
            p.setBrush(QColor(color.red(), color.green(), color.blue(), 24))
            p.setPen(QPen(color, 0.75))
            p.drawEllipse(QPointF(x, y), size, size)
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(4):
            angle = index * math.tau / 4.0 + 0.6
            radius = orbit_r * (0.58 + index % 2 * 0.13)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            p.save()
            p.translate(x, y)
            p.rotate(index * 27.0)
            p.setBrush(QColor(255, 188, 218, 72))
            p.drawPath(self._heart_path(3.5))
            p.restore()
        p.restore()

    @staticmethod
    def _heart_path(size: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(0.0, size)
        path.cubicTo(-size * 0.30, size * 0.62, -size, 0.12, -size, -size * 0.45)
        path.cubicTo(-size, -size, -size * 0.20, -size * 1.10, 0.0, -size * 0.58)
        path.cubicTo(size * 0.20, -size * 1.10, size, -size, size, -size * 0.45)
        path.cubicTo(size, 0.12, size * 0.30, size * 0.62, 0.0, size)
        path.closeSubpath()
        return path

    @staticmethod
    def _syrup_radius(radius: float, angle: float, phase: float) -> float:
        return radius + (
            math.sin(angle * 5.0 - phase * math.tau * 0.22) * 4.2
            + math.sin(angle * 9.0 + phase * math.tau * 0.12) * 2.3
        )

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(8):
            angle = index * math.tau / 8.0 + state.phase * 0.08
            radius = orbit_r - 33.0 + index % 2 * 10.0
            point = QPointF(
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            )
            p.setPen(QPen(QColor(255, 211, 229, 54), 0.8))
            p.drawEllipse(point, 2.0 + index % 2, 2.0 + index % 2)
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        breath = 0.0 if state.reduced_motion else math.sin(phase * math.tau * 0.62) * 2.0
        outer = _radial_path(
            cx,
            cy,
            lambda angle: self._syrup_radius(outer_r + breath, angle, phase),
            samples=196,
        )
        inner = _radial_path(
            cx,
            cy,
            lambda angle: outer_r
            - 22.0
            + math.sin(angle * 4.0 + phase * math.tau * 0.13) * 3.4,
            samples=196,
        )
        band = _radial_band(outer, inner)
        p.save()
        glow = QRadialGradient(cx, cy, outer_r + 24.0)
        glow.setColorAt(0.73, QColor(255, 184, 217, 0))
        glow.setColorAt(0.91, QColor(255, 183, 214, 48))
        glow.setColorAt(1.0, QColor(255, 224, 238, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), outer_r + 24.0, outer_r + 24.0)

        syrup = QConicalGradient(QPointF(cx, cy), phase * -22.0)
        syrup.setColorAt(0.00, QColor(255, 186, 216, 218))
        syrup.setColorAt(0.22, QColor(255, 239, 224, 226))
        syrup.setColorAt(0.43, QColor(190, 232, 220, 212))
        syrup.setColorAt(0.66, QColor(198, 196, 245, 214))
        syrup.setColorAt(0.84, QColor(255, 213, 172, 218))
        syrup.setColorAt(1.00, QColor(255, 186, 216, 218))
        p.setBrush(QBrush(syrup))
        p.drawPath(band)

        shine = _radial_path(
            cx,
            cy,
            lambda angle: self._syrup_radius(outer_r - 1.2, angle, phase),
            samples=196,
        )
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(255, 255, 255, 156),
                1.25,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        p.drawPath(shine)
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + radius * 0.45, radius * 1.36)
        shadow.setColorAt(0.0, QColor(120, 55, 87, 62))
        shadow.setColorAt(1.0, QColor(120, 55, 87, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.36, radius * 1.36)

    def _gummy_scales(self, state: ThemeInteraction) -> tuple[float, float]:
        if state.click_progress > 0.0:
            pulse = math.sin(state.click_progress * math.pi)
            return 1.0 + pulse * 0.12, 1.0 - pulse * 0.17
        if state.hovered and not state.reduced_motion:
            wobble = math.sin(state.phase * math.tau * 1.9)
            return 1.0 + wobble * 0.035, 1.0 - wobble * 0.025
        return (1.0, 1.0)

    def _draw_gummy(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        scale_x, scale_y = self._gummy_scales(state)
        p.save()
        p.translate(cx, cy)
        p.scale(scale_x, scale_y)
        p.translate(-cx, -cy)
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        p.setPen(Qt.PenStyle.NoPen)
        gummy = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        gummy.setColorAt(0.0, QColor(255, 250, 242, 242))
        gummy.setColorAt(0.38, QColor(255, 183, 215, 232))
        gummy.setColorAt(0.72, QColor(231, 138, 186, 234))
        gummy.setColorAt(1.0, QColor(151, 78, 129, 238))
        p.setBrush(QBrush(gummy))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        puff = QRadialGradient(
            cx - radius * 0.38,
            cy - radius * 0.48,
            radius,
        )
        puff.setColorAt(0.0, QColor(255, 255, 255, 174))
        puff.setColorAt(0.50, QColor(255, 246, 249, 48))
        puff.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(puff))
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        p.setBrush(QColor(255, 244, 247, 22))
        p.drawPath(self._heart_path(radius * 0.34).translated(cx, cy + 2.0))
        star = _diamond_path(radius * 0.12, radius * 0.17)
        p.drawPath(star.translated(cx + radius * 0.42, cy - radius * 0.28))
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 108), 0.9))
        p.drawArc(
            QRectF(
                cx - radius + 1.0,
                cy - radius + 1.0,
                (radius - 1.0) * 2.0,
                (radius - 1.0) * 2.0,
            ),
            42 * 16,
            92 * 16,
        )
        p.restore()

        if state.hovered:
            p.save()
            p.setPen(QPen(QColor(255, 226, 239, 155), 0.7))
            for index in range(2):
                angle = -0.75 + index * 1.35 + state.phase * 0.25
                bubble_r = radius * (1.15 + index * 0.22)
                x = cx + math.cos(angle) * bubble_r
                y = cy + math.sin(angle) * bubble_r
                p.setBrush(QColor(255, 189, 218, 105))
                p.drawPath(self._heart_path(2.4 + index * 0.7).translated(x, y))
            p.restore()

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_gummy(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_gummy(p, cx, cy, radius, state)


class SakuraThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "sakura",
        "broken water ripples and flowering branches",
        "petal-water crystal jelly",
        "naturally drifting petals, bokeh, and surface ripples",
        "button ripple with orbiting petal",
        "central blossom and petal release",
        hover_scale=1.03,
        press_scale=0.94,
    )

    @staticmethod
    def _petal_path(size: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(0.0, -size)
        path.cubicTo(
            size * 0.72,
            -size * 0.66,
            size * 0.66,
            size * 0.40,
            0.0,
            size,
        )
        path.cubicTo(
            -size * 0.66,
            size * 0.40,
            -size * 0.72,
            -size * 0.66,
            0.0,
            -size,
        )
        path.closeSubpath()
        return path

    def _draw_petal(
        self,
        p: QPainter,
        x: float,
        y: float,
        size: float,
        rotation: float,
        alpha: int,
        *,
        pale: bool = False,
    ) -> None:
        p.save()
        p.translate(x, y)
        p.rotate(rotation)
        petal = self._petal_path(size)
        fill = QLinearGradient(0.0, -size, 0.0, size)
        if pale:
            fill.setColorAt(0.0, QColor(255, 251, 249, alpha))
            fill.setColorAt(0.52, QColor(255, 212, 225, int(alpha * 0.92)))
            fill.setColorAt(1.0, QColor(226, 121, 157, int(alpha * 0.78)))
        else:
            fill.setColorAt(0.0, QColor(255, 224, 232, alpha))
            fill.setColorAt(0.55, QColor(245, 157, 184, int(alpha * 0.92)))
            fill.setColorAt(1.0, QColor(181, 79, 119, int(alpha * 0.78)))
        p.setBrush(QBrush(fill))
        p.setPen(QPen(QColor(255, 240, 244, int(alpha * 0.62)), 0.55))
        p.drawPath(petal)
        p.restore()

    def _draw_blossom(
        self,
        p: QPainter,
        x: float,
        y: float,
        size: float,
        rotation: float,
        alpha: int,
    ) -> None:
        p.save()
        p.translate(x, y)
        p.rotate(rotation)
        for index in range(5):
            p.save()
            p.rotate(index * 72.0)
            p.translate(0.0, -size * 0.56)
            petal = self._petal_path(size * 0.62)
            flower_fill = QLinearGradient(
                0.0,
                -size * 0.62,
                0.0,
                size * 0.62,
            )
            flower_fill.setColorAt(0.0, QColor(255, 250, 247, alpha))
            flower_fill.setColorAt(
                1.0,
                QColor(236, 135, 171, int(alpha * 0.82)),
            )
            p.setBrush(QBrush(flower_fill))
            p.setPen(QPen(QColor(255, 235, 238, int(alpha * 0.64)), 0.45))
            p.drawPath(petal)
            p.restore()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(247, 205, 113, int(alpha * 0.88)))
        p.drawEllipse(QPointF(), size * 0.19, size * 0.19)
        p.restore()

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()

        # Wide, faint surface rings anchor the petals in a water scene.
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(3):
            ripple_cx = cx + (index - 1) * orbit_r * 0.42
            ripple_cy = cy + orbit_r * (0.16 + index * 0.10)
            ripple_w = orbit_r * (0.38 + index * 0.11)
            p.setPen(
                QPen(
                    QColor(255, 187, 207, 26 + index * 8),
                    0.8 + index * 0.18,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawArc(
                QRectF(
                    ripple_cx - ripple_w,
                    ripple_cy - ripple_w * 0.30,
                    ripple_w * 2.0,
                    ripple_w * 0.60,
                ),
                (18 + index * 71) * 16,
                (112 - index * 14) * 16,
            )

        # Petals fall diagonally with individual drift, rather than emitting
        # from one fixed point or moving in an identical radial pattern.
        for index in range(13):
            seed = (index * 0.61803398875 + 0.17) % 1.0
            travel = (
                seed
                if state.reduced_motion
                else (
                    seed
                    + phase * (0.16 + (index % 4) * 0.026)
                )
                % 1.0
            )
            base_x = cx - orbit_r * 0.86 + (
                (index * 67) % int(orbit_r * 1.64)
            )
            x = (
                base_x
                + travel * orbit_r * (0.18 + index % 3 * 0.045)
                + math.sin(travel * math.tau * 1.7 + index) * 8.0
            )
            y = cy - orbit_r * 0.98 + travel * orbit_r * 1.96
            size = 2.2 + index % 4 * 0.58
            rotation = index * 47.0 + travel * (92.0 + index % 3 * 28.0)
            self._draw_petal(
                p,
                x,
                y,
                size,
                rotation,
                84 + index % 3 * 34,
                pale=index % 3 == 0,
            )

        p.setPen(Qt.PenStyle.NoPen)
        for index in range(7):
            angle = index * 2.17 + 0.4
            distance = orbit_r * (0.24 + index % 4 * 0.16)
            glow_x = cx + math.cos(angle) * distance
            glow_y = cy + math.sin(angle * 0.81) * distance * 0.72
            glow_r = 3.0 + index % 3 * 1.6
            bokeh = QRadialGradient(glow_x, glow_y, glow_r * 2.2)
            bokeh.setColorAt(0.0, QColor(255, 225, 221, 58 + index % 2 * 22))
            bokeh.setColorAt(1.0, QColor(255, 188, 204, 0))
            p.setBrush(QBrush(bokeh))
            p.drawEllipse(
                QPointF(glow_x, glow_y),
                glow_r * 2.2,
                glow_r * 2.2,
            )
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(4):
            radius_x = orbit_r * (0.48 + index * 0.08)
            radius_y = radius_x * (0.42 + index * 0.025)
            rect = QRectF(
                cx - radius_x,
                cy - radius_y + orbit_r * 0.13,
                radius_x * 2.0,
                radius_y * 2.0,
            )
            p.setPen(
                QPen(
                    QColor(249, 181, 203, 27 + index * 8),
                    0.7 + index * 0.12,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawArc(rect, (15 + index * 62) * 16, (76 + index * 8) * 16)
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        shimmer = 0.72 + math.sin(state.phase * math.tau) * 0.16
        for index, point in enumerate(points):
            if index % 3:
                continue
            p.setBrush(QColor(255, 211, 219, int(82 * shimmer)))
            p.drawEllipse(point, 2.6, 1.2)
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Broken water paths overlap at different radii; no complete neon rim.
        for index in range(6):
            start = 0.12 + index * math.tau / 6.0 + phase * (0.035 + index % 2 * 0.012)
            span = 0.54 + index % 3 * 0.09
            path = _polar_segment(
                cx,
                cy,
                start,
                span,
                lambda angle, index=index: outer_r
                + (index % 3 - 1) * 5.5
                + math.sin(angle * 7.0 + index + phase * math.tau * 0.14) * 3.2,
                samples=34,
            )
            p.setPen(
                QPen(
                    QColor(255, 172, 199, 32 + index % 2 * 16),
                    8.0 + index % 2 * 2.5,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(path)
            p.setPen(
                QPen(
                    QColor(255, 227, 233, 105 + index % 2 * 28),
                    1.15,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawPath(path)

        # Three flowering branch sections break the circular silhouette.
        for branch_index, (start, span) in enumerate(
            ((0.28, 0.92), (2.35, 0.82), (4.37, 1.02))
        ):
            branch = _polar_segment(
                cx,
                cy,
                start,
                span,
                lambda angle, branch_index=branch_index: outer_r
                - 2.0
                + math.sin(angle * 4.0 + branch_index) * 4.5,
                samples=46,
            )
            p.setPen(
                QPen(
                    QColor(91, 43, 65, 210),
                    3.4,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            p.drawPath(branch)
            p.setPen(QPen(QColor(226, 147, 170, 128), 0.9))
            p.drawPath(branch)

            for twig_index in range(1, 5):
                angle = start + span * twig_index / 5.0
                radius = (
                    outer_r
                    - 2.0
                    + math.sin(angle * 4.0 + branch_index) * 4.5
                )
                base = QPointF(
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius,
                )
                direction = angle + (-0.30 if twig_index % 2 else 0.28)
                twig_length = 8.0 + twig_index % 2 * 4.0
                tip = QPointF(
                    base.x() + math.cos(direction) * twig_length,
                    base.y() + math.sin(direction) * twig_length,
                )
                p.setPen(
                    QPen(
                        QColor(109, 52, 75, 190),
                        1.35,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                    )
                )
                p.drawLine(QLineF(base, tip))
                if (twig_index + branch_index) % 2 == 0:
                    self._draw_blossom(
                        p,
                        tip.x(),
                        tip.y(),
                        3.3,
                        branch_index * 17.0 + twig_index * 23.0,
                        178,
                    )

        for index in range(9):
            speed = 0.055 + index % 4 * 0.014
            angle = (
                index * math.tau / 9.0
                + phase * math.tau * speed
                + math.sin(phase * math.tau * 0.16 + index) * 0.035
            )
            radius = outer_r + math.sin(index * 1.8 + phase * math.tau * 0.12) * 9.0
            self._draw_petal(
                p,
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
                3.0 + index % 3 * 0.75,
                math.degrees(angle) + 34.0 + index * 19.0,
                128 + index % 3 * 26,
                pale=index % 4 == 0,
            )
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + 4.0, radius * 1.42)
        shadow.setColorAt(0.0, QColor(92, 32, 63, 84))
        shadow.setColorAt(1.0, QColor(92, 32, 63, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 4.0), radius * 1.42, radius * 1.42)

    def _draw_petal_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        bounds = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        circle = QPainterPath()
        circle.addEllipse(bounds)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        crystal = QLinearGradient(cx, cy - radius, cx, cy + radius)
        crystal.setColorAt(0.0, QColor(255, 236, 241, 232))
        crystal.setColorAt(0.22, QColor(244, 181, 201, 230))
        crystal.setColorAt(0.58, QColor(190, 94, 135, 240))
        crystal.setColorAt(1.0, QColor(78, 31, 68, 250))
        p.setBrush(QBrush(crystal))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        water_light = QRadialGradient(
            cx - radius * 0.38,
            cy - radius * 0.48,
            radius * 1.08,
        )
        water_light.setColorAt(0.0, QColor(255, 255, 252, 168))
        water_light.setColorAt(0.52, QColor(255, 232, 238, 42))
        water_light.setColorAt(1.0, QColor(255, 232, 238, 0))
        p.setBrush(QBrush(water_light))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        p.setBrush(QColor(255, 231, 237, 22))
        p.setPen(QPen(QColor(255, 239, 241, 32), 0.5))
        for index, offset in enumerate(((-0.34, 0.13), (0.30, -0.04))):
            p.save()
            p.translate(
                cx + radius * offset[0],
                cy + radius * offset[1],
            )
            p.rotate(28.0 + index * 96.0)
            p.drawPath(self._petal_path(radius * (0.30 + index * 0.05)))
            p.restore()

        # A soft water-surface streak makes the material read as a droplet.
        surface = QPainterPath()
        surface.moveTo(cx - radius * 0.70, cy - radius * 0.36)
        for index in range(10):
            x = cx - radius * 0.72 + radius * 1.44 * index / 9.0
            y = (
                cy
                - radius * 0.36
                + math.sin(index * 1.18 + state.phase * math.tau * 0.35)
                * radius
                * 0.035
            )
            surface.lineTo(x, y)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(255, 252, 248, 116),
                1.55,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawPath(surface)
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 248, 246, 104), 0.85))
        p.drawArc(bounds.adjusted(1.0, 1.0, -1.0, -1.0), 28 * 16, 122 * 16)

        hover = state.hover_progress
        if hover > 0.0:
            ripple_phase = 0.32 if state.reduced_motion else (state.phase * 2.0) % 1.0
            ripple_r = radius * (1.02 + ripple_phase * 0.36)
            p.setPen(
                QPen(
                    QColor(
                        255,
                        207,
                        219,
                        int(126 * hover * (1.0 - ripple_phase)),
                    ),
                    1.15,
                )
            )
            p.drawEllipse(QPointF(cx, cy), ripple_r, ripple_r * 0.90)
            petal_angle = (
                -0.82
                if state.reduced_motion
                else state.phase * math.tau * 0.72
            )
            petal_r = radius * 1.22
            self._draw_petal(
                p,
                cx + math.cos(petal_angle) * petal_r,
                cy + math.sin(petal_angle) * petal_r,
                3.1,
                math.degrees(petal_angle) + 34.0,
                int(205 * hover),
                pale=True,
            )
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_petal_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_petal_jelly(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        bloom = min(1.0, progress / 0.38)
        release = max(0.0, (progress - 0.30) / 0.70)
        alpha = int(210 * (1.0 - progress * 0.76))
        self._draw_blossom(
            p,
            cx,
            cy,
            radius * (0.13 + bloom * 0.20),
            progress * 38.0,
            alpha,
        )
        if release <= 0.0:
            return
        for index in range(7):
            angle = index * math.tau / 7.0 + progress * 0.34
            distance = radius * (0.24 + release * 1.22)
            self._draw_petal(
                p,
                cx + math.cos(angle) * distance,
                cy + math.sin(angle) * distance,
                2.1 + index % 3 * 0.42,
                math.degrees(angle) + index * 24.0,
                int(alpha * (1.0 - release * 0.28)),
                pale=index % 2 == 0,
            )


class CyberThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "cyber",
        "segmented HUD with data ticks and scan sectors",
        "dark transparent scan-grid jelly",
        "digital noise, cursor nodes, and code fragments",
        "horizontal scan with single RGB echo",
        "confirmation flash and segmented pulse",
        hover_scale=1.035,
        press_scale=0.94,
    )

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(24):
            x = cx - orbit_r + (index * 71 % int(orbit_r * 2.0))
            y = cy - orbit_r + (index * 43 % int(orbit_r * 2.0))
            alpha = 42 + index % 5 * 18
            p.setBrush(
                QColor(76, 229, 242, alpha)
                if index % 3
                else QColor(226, 74, 242, alpha)
            )
            size = 0.7 + index % 3 * 0.35
            p.drawRect(QRectF(x, y, size * 1.6, size))

        scan_y = cy - orbit_r + (
            0.42 * orbit_r
            if state.reduced_motion
            else phase * orbit_r * 2.0
        )
        scan = QLinearGradient(cx - orbit_r, scan_y, cx + orbit_r, scan_y)
        scan.setColorAt(0.0, QColor(50, 224, 240, 0))
        scan.setColorAt(0.42, QColor(67, 229, 242, 48))
        scan.setColorAt(0.58, QColor(222, 80, 245, 42))
        scan.setColorAt(1.0, QColor(50, 224, 240, 0))
        p.setBrush(QBrush(scan))
        p.drawRect(QRectF(cx - orbit_r, scan_y - 0.6, orbit_r * 2.0, 1.2))

        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(7):
            angle = index * math.tau / 7.0 + 0.2
            radius = orbit_r * (0.52 + index % 3 * 0.12)
            point = QPointF(
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            )
            p.setPen(QPen(QColor(83, 226, 238, 65), 0.7))
            p.drawRect(QRectF(point.x() - 2.5, point.y() - 2.5, 5.0, 5.0))
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del slot_count, rotation
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(20):
            angle = index * math.tau / 20.0
            inner = orbit_r - 39.0
            outer = inner + (8.0 if index % 5 == 0 else 4.0)
            color = (
                QColor(222, 72, 245, 86)
                if index % 5 == 0
                else QColor(75, 226, 239, 64)
            )
            p.setPen(QPen(color, 0.85))
            p.drawLine(
                QLineF(
                    cx + math.cos(angle) * inner,
                    cy + math.sin(angle) * inner,
                    cx + math.cos(angle) * outer,
                    cy + math.sin(angle) * outer,
                )
            )
        p.restore()

    def draw_constellation_accents(
        self,
        p: QPainter,
        points: list[QPointF],
        links: list[tuple[int, int]],
        state: ThemeInteraction,
    ) -> None:
        del links, state
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        for index, point in enumerate(points):
            color = (
                QColor(72, 225, 239, 118)
                if index % 2
                else QColor(220, 69, 240, 104)
            )
            p.setPen(QPen(color, 0.75))
            p.drawRect(QRectF(point.x() - 2.7, point.y() - 2.7, 5.4, 5.4))
        p.restore()

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        segment_count = 24
        scanning = int(phase * segment_count) % segment_count
        glitch = (
            not state.reduced_motion
            and math.sin(phase * math.tau * 2.3) > 0.93
        )
        for index in range(segment_count):
            radius = outer_r + (index % 3 - 1) * 5.0
            rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
            start = index * 360.0 / segment_count + 2.0
            span = 9.2 if index % 4 else 6.0
            active = min(
                (index - scanning) % segment_count,
                (scanning - index) % segment_count,
            ) <= 1
            color = (
                QColor(87, 239, 246, 228)
                if active
                else QColor(74, 201, 221, 112)
                if index % 2
                else QColor(219, 67, 241, 126)
            )
            width = 2.5 if active else 1.25 + index % 3 * 0.25
            offset = 3.0 if glitch and index in {4, 5, 16} else 0.0
            p.setPen(
                QPen(
                    color,
                    width,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.SquareCap,
                )
            )
            p.drawArc(
                rect.translated(offset, 0.0),
                int(start * 16),
                int(span * 16),
            )

        for index in range(12):
            angle = index * math.tau / 12.0 + 0.13
            radius = outer_r + (7.0 if index % 3 == 0 else -7.0)
            point = QPointF(
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            )
            p.save()
            p.translate(point)
            p.rotate(math.degrees(angle))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(
                QColor(78, 229, 239, 156)
                if index % 2
                else QColor(224, 72, 244, 145)
            )
            p.drawRect(QRectF(-3.0, -1.1, 6.0, 2.2))
            p.restore()
        p.restore()

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        shadow = QRadialGradient(cx, cy + 3.0, radius * 1.38)
        shadow.setColorAt(0.0, QColor(1, 24, 38, 112))
        shadow.setColorAt(1.0, QColor(1, 24, 38, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 3.0), radius * 1.38, radius * 1.38)

    def _draw_cyber_jelly(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        circle = QPainterPath()
        circle.addEllipse(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        tech = QLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        tech.setColorAt(0.0, QColor(20, 85, 103, 222))
        tech.setColorAt(0.46, QColor(7, 39, 59, 240))
        tech.setColorAt(1.0, QColor(3, 15, 29, 250))
        p.setBrush(QBrush(tech))
        p.drawPath(circle)

        p.save()
        p.setClipPath(circle)
        for index in range(7):
            y = cy - radius + 5.0 + index * radius * 0.28
            alpha = 72 if state.hovered and index == int(state.phase * 14) % 7 else 27
            p.setPen(QPen(QColor(76, 230, 239, alpha), 0.75))
            p.drawLine(QLineF(cx - radius, y, cx + radius, y))
        for index in range(8):
            x = cx - radius * 0.72 + (index * 17 % int(radius * 1.42))
            y = cy - radius * 0.62 + (index * 29 % int(radius * 1.24))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(
                QColor(222, 74, 243, 82)
                if index % 3 == 0
                else QColor(72, 225, 237, 68)
            )
            p.drawRect(QRectF(x, y, 1.8 + index % 2, 1.3))

        if state.hovered:
            scan_y = cy - radius + ((state.phase * 3.6) % 1.0) * radius * 2.0
            scan = QLinearGradient(cx - radius, scan_y, cx + radius, scan_y)
            scan.setColorAt(0.0, QColor(72, 229, 239, 0))
            scan.setColorAt(0.42, QColor(88, 241, 245, 185))
            scan.setColorAt(0.58, QColor(229, 91, 247, 145))
            scan.setColorAt(1.0, QColor(72, 229, 239, 0))
            p.setBrush(QBrush(scan))
            p.drawRect(QRectF(cx - radius, scan_y - 1.0, radius * 2.0, 2.0))
        p.restore()

        # Four short brackets define the control without a heavy border.
        bracket = radius * 0.26
        inset = radius * 0.66
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(92, 237, 242, 145 if state.hovered else 92),
                1.15,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.SquareCap,
            )
        )
        for sx, sy in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
            x = cx + sx * inset
            y = cy + sy * inset
            p.drawLine(QLineF(x, y, x - sx * bracket, y))
            p.drawLine(QLineF(x, y, x, y - sy * bracket))
        p.restore()
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_cyber_jelly(p, cx, cy, radius, state)

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_cyber_jelly(p, cx, cy, radius, state)

    def draw_content_echo(
        self,
        p: QPainter,
        rect: QRectF,
        text: str,
        font: QFont,
        state: ThemeInteraction,
    ) -> None:
        if not state.hovered or state.reduced_motion:
            return
        glitch = max(0.0, math.sin(state.phase * math.tau * 3.2))
        if glitch < 0.72:
            return
        alpha = int((glitch - 0.72) / 0.28 * 125)
        p.save()
        p.setFont(font)
        p.setPen(QColor(255, 65, 116, alpha))
        p.drawText(
            rect.translated(-1.4, 0.0),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        p.setPen(QColor(41, 238, 255, alpha))
        p.drawText(
            rect.translated(1.4, 0.0),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        p.restore()

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        flash = max(0.0, 1.0 - progress * 1.9)
        pulse_r = radius * (1.0 + progress * 0.65)
        p.save()
        p.setBrush(QColor(114, 247, 246, int(72 * flash)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(84, 239, 244, int(185 * (1.0 - progress))),
                1.5,
                Qt.PenStyle.DashLine,
            )
        )
        p.drawEllipse(QPointF(cx, cy), pulse_r, pulse_r)
        p.restore()


class OceanThemeRenderer(ThemeRenderer):
    dna = ThemeVisualDNA(
        "ocean",
        "parallax deep-sea swell",
        "refractive water gel",
        "caustics, bubbles, and shark silhouettes",
        "buoyant lift and ripple",
        "water-drop rebound",
        hover_scale=1.035,
        press_scale=0.92,
    )

    def button_scale(self, state: ThemeInteraction) -> float:
        if state.pressed:
            return self.dna.press_scale
        if state.click_progress > 0.0 and not state.reduced_motion:
            return 1.0 - math.sin(state.click_progress * math.pi) * 0.085
        return 1.0 + state.hover_progress * 0.035

    def content_offset(self, state: ThemeInteraction) -> QPointF:
        progress = 1.0 if state.hovered and state.reduced_motion else state.hover_progress
        return QPointF(0.0, -2.4 * progress)

    def draw_background(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        state: ThemeInteraction,
    ) -> None:
        phase = state.phase
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Broad, broken caustics suggest moving light without blurring the UI.
        for index in range(5):
            angle = index * math.tau / 5.0 + phase * 0.38
            radius = orbit_r * (0.34 + (index % 3) * 0.13)
            center = QPointF(
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            )
            p.setPen(
                QPen(
                    QColor(91, 233, 226, 14 + (index % 2) * 7),
                    1.1 + (index % 2) * 0.45,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            p.drawArc(
                QRectF(
                    center.x() - orbit_r * 0.18,
                    center.y() - orbit_r * 0.07,
                    orbit_r * 0.36,
                    orbit_r * 0.14,
                ),
                int((22 + index * 57) * 16),
                int((54 + (index % 2) * 22) * 16),
            )

        # A small fixed budget of rising bubbles and suspended matter.
        for index in range(13):
            seed = (index * 0.61803398875) % 1.0
            bubble_phase = (
                seed if state.reduced_motion else (seed + phase * (0.18 + index % 3 * 0.035)) % 1.0
            )
            x = cx + math.sin(index * 4.17) * orbit_r * (0.18 + (index % 5) * 0.105)
            y = cy + orbit_r * 0.84 - bubble_phase * orbit_r * 1.62
            size = 0.75 + (index % 4) * 0.48
            alpha = 42 + (index % 3) * 18
            p.setPen(QPen(QColor(143, 246, 238, alpha), 0.75))
            p.setBrush(QColor(76, 188, 205, alpha // 5))
            p.drawEllipse(QPointF(x, y), size, size)

        p.setPen(Qt.PenStyle.NoPen)
        for index in range(9):
            angle = index * 2.41 + phase * 0.24
            distance = orbit_r * (0.18 + (index % 5) * 0.145)
            p.setBrush(QColor(102, 203, 202, 38 + (index % 2) * 16))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * distance,
                    cy + math.sin(angle * 0.83) * distance * 0.74,
                ),
                0.7,
                0.7,
            )
        p.restore()

    def draw_guides(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        orbit_r: float,
        slot_count: int,
        rotation: float,
        state: ThemeInteraction,
    ) -> None:
        del p, cx, cy, orbit_r, slot_count, rotation, state

    def draw_orbit(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        outer_r: float,
        state: ThemeInteraction,
    ) -> None:
        draw_ocean_wave_orbit(p, cx, cy, outer_r, state.frame_index)

    def draw_shadow(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        del color
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 26, 50, 72))
        p.drawEllipse(QPointF(cx, cy + 4.5), radius + 2.8, radius + 2.2)

    def _draw_water_gel(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        radius *= self.button_scale(state)
        bounds = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        phase = state.phase

        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        water = QLinearGradient(cx, cy - radius, cx, cy + radius)
        water.setColorAt(0.0, QColor(75, 211, 215, 225))
        water.setColorAt(0.20, QColor(24, 151, 176, 228))
        water.setColorAt(0.58, QColor(7, 85, 126, 241))
        water.setColorAt(1.0, QColor(2, 31, 69, 250))
        p.setBrush(QBrush(water))
        p.drawEllipse(bounds)

        # Refracted surface light remains clipped inside the water gel.
        p.save()
        clip = QPainterPath()
        clip.addEllipse(bounds.adjusted(1.0, 1.0, -1.0, -1.0))
        p.setClipPath(clip)
        surface = QPainterPath()
        surface.moveTo(cx - radius * 0.94, cy - radius * 0.44)
        for step in range(13):
            x = cx - radius + radius * 2.0 * step / 12.0
            y = (
                cy
                - radius * 0.47
                + math.sin(step * 1.21 + phase * math.tau) * radius * 0.055
            )
            surface.lineTo(x, y)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(205, 255, 252, 118),
                2.1,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawPath(surface)
        p.setBrush(QColor(196, 255, 250, 34))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(
            QRectF(
                cx - radius * 0.62,
                cy - radius * 0.78,
                radius * 1.24,
                radius * 0.46,
            )
        )

        for index in range(4):
            bubble_phase = (
                (index * 0.27 + 0.14)
                if state.reduced_motion
                else (index * 0.27 + phase * (0.30 + index * 0.025)) % 1.0
            )
            bx = cx + math.sin(index * 2.73) * radius * 0.48
            by = cy + radius * 0.63 - bubble_phase * radius * 1.16
            bubble_r = max(0.7, radius * (0.025 + (index % 2) * 0.017))
            p.setBrush(QColor(184, 255, 250, 25))
            p.setPen(QPen(QColor(195, 255, 253, 82), 0.65))
            p.drawEllipse(QPointF(bx, by), bubble_r, bubble_r)
        p.restore()

        # Only a fine atmospheric glint defines the edge—no hard blue rim.
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                QColor(205, 255, 253, 116),
                1.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawArc(bounds.adjusted(1.0, 1.0, -1.0, -1.0), 24 * 16, 132 * 16)

        hover = state.hover_progress
        if hover > 0.0:
            ripple_progress = 0.34 if state.reduced_motion else (phase * 2.25) % 1.0
            ripple_radius = radius * (1.04 + ripple_progress * 0.34)
            p.setPen(
                QPen(
                    QColor(122, 238, 235, int(112 * hover * (1.0 - ripple_progress))),
                    1.25,
                )
            )
            p.drawEllipse(QPointF(cx, cy), ripple_radius, ripple_radius * 0.90)
            p.setPen(QPen(QColor(178, 255, 250, int(118 * hover)), 0.75))
            p.setBrush(QColor(112, 230, 226, int(34 * hover)))
            for index in range(3):
                bubble_x = cx + (index - 1) * radius * 0.34
                bubble_y = cy + radius * (0.82 - index * 0.12)
                bubble_r = 1.0 + index * 0.45
                p.drawEllipse(QPointF(bubble_x, bubble_y), bubble_r, bubble_r)
        p.restore()

    def draw_button(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        del fill
        self._draw_water_gel(p, cx, cy, radius, state)
        self.draw_click_feedback(p, cx, cy, radius, state)

    def draw_click_feedback(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        state: ThemeInteraction,
    ) -> None:
        progress = state.click_progress
        if progress <= 0.0 or state.reduced_motion:
            return
        ring_r = radius * (0.82 + progress * 1.05)
        alpha = int(175 * (1.0 - progress))
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(158, 249, 242, alpha), 1.6))
        p.drawEllipse(QPointF(cx, cy), ring_r, ring_r * 0.88)
        p.setPen(Qt.PenStyle.NoPen)
        for index in range(5):
            angle = -0.95 + index * 0.48
            distance = radius * (0.76 + progress * (0.48 + index % 2 * 0.12))
            droplet_r = max(0.45, (1.8 - progress * 1.2) * (0.8 + index % 2 * 0.25))
            p.setBrush(QColor(151, 247, 240, int(alpha * 0.72)))
            p.drawEllipse(
                QPointF(
                    cx + math.cos(angle) * distance,
                    cy + math.sin(angle) * distance,
                ),
                droplet_r,
                droplet_r,
            )
        p.restore()

    def draw_center(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        radius: float,
        fill: QColor,
        state: ThemeInteraction,
    ) -> None:
        self.draw_button(p, cx, cy, radius, fill, state)


_DEFAULT_RENDERERS: dict[str, ThemeRenderer] = {
    theme_id: ThemeRenderer()
    for theme_id in THEMES
}
for _theme_id, _renderer in tuple(_DEFAULT_RENDERERS.items()):
    _renderer.dna = ThemeVisualDNA(
        _theme_id,
        _renderer.dna.orbit_kind,
        _renderer.dna.button_material,
        _renderer.dna.particle_kind,
        _renderer.dna.hover_kind,
        _renderer.dna.click_kind,
        _renderer.dna.hover_scale,
        _renderer.dna.press_scale,
    )

THEME_RENDERERS: dict[str, ThemeRenderer] = {
    **_DEFAULT_RENDERERS,
    "tiger": TigerThemeRenderer(),
    "purple": PurpleThemeRenderer(),
    "ice": IceThemeRenderer(),
    "lava": LavaThemeRenderer(),
    "cosmic": CosmicThemeRenderer(),
    "halloween": HalloweenThemeRenderer(),
    "kawaii": KawaiiThemeRenderer(),
    "sakura": SakuraThemeRenderer(),
    "cyber": CyberThemeRenderer(),
    "ocean": OceanThemeRenderer(),
}


def theme_renderer(theme_id: str) -> ThemeRenderer:
    return THEME_RENDERERS.get(theme_id, THEME_RENDERERS[DEFAULT_THEME])
