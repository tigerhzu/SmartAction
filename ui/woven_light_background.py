"""Lightweight interactive particle tapestry for the Woven Light UI theme."""
from __future__ import annotations

from dataclasses import dataclass
import math

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QCursor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class _ParticleSeed:
    band: int
    point: int
    u: float
    v: float
    phase: float


@dataclass(frozen=True)
class _ProjectedParticle:
    x: float
    y: float
    depth: float
    proximity: float
    color_index: int


_PALETTE = (
    QColor("#0BB8CF"),
    QColor("#4E73F0"),
    QColor("#9C4ED8"),
    QColor("#E9568B"),
    QColor("#F09C24"),
)


class WovenLightBackground(QWidget):
    """Animated, cursor-reactive backdrop drawn entirely with QPainter.

    The particle count is intentionally bounded so the visual remains smooth
    on office laptops without requiring OpenGL, Three.js, or extra packages.
    """

    BANDS = 15
    POINTS_PER_BAND = 32
    FRAME_INTERVAL_MS = 40

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._phase = 0.0
        self._tilt_x = 0.0
        self._tilt_y = 0.0
        self._target_tilt_x = 0.0
        self._target_tilt_y = 0.0
        self._pointer = QPointF(-10_000.0, -10_000.0)
        self._pointer_inside = False
        self._seeds = self._build_seeds()
        self._projected: list[_ProjectedParticle] = []

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.CoarseTimer)
        self._timer.setInterval(self.FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._advance_frame)

    @property
    def particle_count(self) -> int:
        return len(self._seeds)

    @property
    def phase(self) -> float:
        return self._phase

    def set_test_pointer(self, point: QPointF | None) -> None:
        """Set a deterministic pointer for visual regression tests."""
        if point is None:
            self._pointer_inside = False
            self._pointer = QPointF(-10_000.0, -10_000.0)
            self._target_tilt_x = 0.0
            self._target_tilt_y = 0.0
            return
        self._pointer = QPointF(point)
        self._pointer_inside = True
        if self.width() > 0 and self.height() > 0:
            self._target_tilt_y = (
                point.x() / self.width() - 0.5
            ) * 0.58
            self._target_tilt_x = (
                point.y() / self.height() - 0.5
            ) * -0.38

    def showEvent(self, event: QEvent) -> None:
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start()

    def hideEvent(self, event: QEvent) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def _build_seeds(self) -> tuple[_ParticleSeed, ...]:
        seeds: list[_ParticleSeed] = []
        for band in range(self.BANDS):
            v = band / (self.BANDS - 1) * 2.0 - 1.0
            for point in range(self.POINTS_PER_BAND):
                u = point / self.POINTS_PER_BAND * math.tau
                seeds.append(
                    _ParticleSeed(
                        band=band,
                        point=point,
                        u=u,
                        v=v,
                        phase=band * 0.29 + point * 0.071,
                    )
                )
        return tuple(seeds)

    def _advance_frame(self) -> None:
        if not self.isVisible():
            return
        local = self.mapFromGlobal(QCursor.pos())
        if self.rect().contains(local):
            self.set_test_pointer(QPointF(local))
        else:
            self.set_test_pointer(None)

        self._tilt_x += (self._target_tilt_x - self._tilt_x) * 0.085
        self._tilt_y += (self._target_tilt_y - self._tilt_y) * 0.085
        self._phase = (self._phase + 0.0125) % math.tau
        self.update()

    def _project_particles(self) -> list[_ProjectedParticle]:
        width = max(1.0, float(self.width()))
        height = max(1.0, float(self.height()))
        center_x = width * 0.68
        center_y = height * 0.49
        scale = min(width * 0.36, height * 0.48)

        cos_y = math.cos(self._tilt_y + self._phase * 0.10)
        sin_y = math.sin(self._tilt_y + self._phase * 0.10)
        cos_x = math.cos(self._tilt_x - 0.08)
        sin_x = math.sin(self._tilt_x - 0.08)
        projected: list[_ProjectedParticle] = []

        for seed in self._seeds:
            wave = (
                math.sin(seed.u * 3.0 + seed.v * 2.6 + self._phase)
                * 0.13
            )
            radius = 0.72 + wave + math.cos(seed.u * 2.0 - seed.v * 3.4) * 0.055
            x = math.cos(seed.u) * radius + seed.v * 0.12
            y = math.sin(seed.u) * radius * 0.76 + seed.v * 0.30
            z = (
                math.sin(seed.u * 2.0 + seed.v * 4.2 + self._phase * 0.72)
                * 0.34
                + math.cos(seed.u * 4.0 - seed.v * 2.0) * 0.08
            )

            rotated_x = x * cos_y + z * sin_y
            rotated_z = -x * sin_y + z * cos_y
            rotated_y = y * cos_x - rotated_z * sin_x
            depth = y * sin_x + rotated_z * cos_x
            perspective = 1.0 + depth * 0.17

            screen_x = center_x + rotated_x * scale * perspective
            screen_y = center_y + rotated_y * scale * perspective
            proximity = 0.0
            if self._pointer_inside:
                dx = screen_x - self._pointer.x()
                dy = screen_y - self._pointer.y()
                distance = math.hypot(dx, dy)
                influence_radius = max(105.0, min(width, height) * 0.19)
                if distance < influence_radius:
                    proximity = 1.0 - distance / influence_radius
                    force = proximity * proximity * 22.0
                    if distance > 0.01:
                        screen_x += dx / distance * force
                        screen_y += dy / distance * force

            projected.append(
                _ProjectedParticle(
                    x=screen_x,
                    y=screen_y,
                    depth=depth,
                    proximity=proximity,
                    color_index=(seed.band + seed.point // 7) % len(_PALETTE),
                )
            )
        return projected

    def paintEvent(self, event: QEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        base = QLinearGradient(0.0, 0.0, self.width(), self.height())
        base.setColorAt(0.0, QColor("#FBFCFE"))
        base.setColorAt(0.45, QColor("#F7F9FC"))
        base.setColorAt(1.0, QColor("#EEF3FA"))
        painter.fillRect(self.rect(), base)

        for x, y, radius, color in (
            (0.18, 0.18, 280.0, QColor(178, 224, 239, 32)),
            (0.83, 0.20, 330.0, QColor(197, 178, 241, 34)),
            (0.72, 0.86, 360.0, QColor(242, 179, 201, 28)),
        ):
            glow = QRadialGradient(
                self.width() * x,
                self.height() * y,
                min(radius, max(self.width(), self.height()) * 0.42),
            )
            glow.setColorAt(0.0, color)
            glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillRect(self.rect(), glow)

        self._projected = self._project_particles()
        if not self._projected:
            painter.end()
            return

        pixel_scale = max(
            1.0,
            min(1.7, min(self.width(), self.height()) / 700.0),
        )
        thread = QPen(
            QColor(82, 104, 139, 82),
            0.94 * pixel_scale,
        )
        thread.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(thread)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for band in range(self.BANDS):
            path = QPainterPath()
            start = band * self.POINTS_PER_BAND
            first = self._projected[start]
            path.moveTo(first.x, first.y)
            for point in range(1, self.POINTS_PER_BAND):
                item = self._projected[start + point]
                path.lineTo(item.x, item.y)
            path.closeSubpath()
            painter.drawPath(path)

        for point in range(0, self.POINTS_PER_BAND, 2):
            path = QPainterPath()
            first = self._projected[point]
            path.moveTo(first.x, first.y)
            for band in range(1, self.BANDS):
                item = self._projected[band * self.POINTS_PER_BAND + point]
                path.lineTo(item.x, item.y)
            painter.drawPath(path)

        ordered = sorted(self._projected, key=lambda item: item.depth)
        painter.setPen(Qt.PenStyle.NoPen)
        for index, item in enumerate(ordered):
            color = QColor(_PALETTE[item.color_index])
            depth_normalized = max(0.0, min(1.0, (item.depth + 0.65) / 1.3))
            color.setAlpha(
                int(
                    188
                    + depth_normalized * 54
                    + item.proximity * 13
                )
            )
            radius = pixel_scale * (
                1.18
                + depth_normalized * 0.92
                + item.proximity * 2.15
            )
            if item.proximity > 0.48 and index % 5 == 0:
                halo = QColor(color)
                halo.setAlpha(62)
                painter.setBrush(halo)
                painter.drawEllipse(
                    QPointF(item.x, item.y),
                    radius * 3.1,
                    radius * 3.1,
                )
            painter.setBrush(color)
            painter.drawEllipse(QPointF(item.x, item.y), radius, radius)

        if self._pointer_inside:
            pointer_glow = QRadialGradient(
                self._pointer,
                max(90.0, min(self.width(), self.height()) * 0.14),
            )
            pointer_glow.setColorAt(0.0, QColor(255, 255, 255, 46))
            pointer_glow.setColorAt(0.65, QColor(157, 213, 236, 12))
            pointer_glow.setColorAt(1.0, QColor(157, 213, 236, 0))
            painter.fillRect(QRectF(self.rect()), pointer_glow)

        painter.end()
