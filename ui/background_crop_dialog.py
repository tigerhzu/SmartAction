from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.global_theme import background_source_rect
from ui.window_utils import center_window, screen_for_widget


class BackgroundCropCanvas(QWidget):
    """Interactive cover-crop preview that keeps the original file intact."""

    transform_changed = Signal(int, float, float)

    def __init__(
        self,
        image_path: Path,
        target_size: QSize,
        zoom: int,
        focus_x: float,
        focus_y: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(image_path))
        self._target_ratio = max(0.2, target_size.width() / max(1, target_size.height()))
        self._zoom = max(100, min(400, int(zoom)))
        self._focus_x = max(0.0, min(1.0, float(focus_x)))
        self._focus_y = max(0.0, min(1.0, float(focus_y)))
        self._drag_origin: QPointF | None = None
        self._drag_focus = (self._focus_x, self._focus_y)
        self.setMinimumSize(560, 350)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMouseTracking(True)

    @property
    def image_size(self) -> QSize:
        return self._pixmap.size()

    def transform(self) -> tuple[int, float, float]:
        return self._zoom, self._focus_x, self._focus_y

    def set_zoom(self, zoom: int) -> None:
        zoom = max(100, min(400, int(zoom)))
        if zoom == self._zoom:
            return
        self._zoom = zoom
        self.update()
        self.transform_changed.emit(self._zoom, self._focus_x, self._focus_y)

    def reset_transform(self) -> None:
        self._zoom = 100
        self._focus_x = 0.5
        self._focus_y = 0.5
        self.update()
        self.transform_changed.emit(self._zoom, self._focus_x, self._focus_y)

    def _frame_rect(self) -> QRectF:
        margin = 18.0
        available = QRectF(self.rect()).adjusted(margin, margin, -margin, -margin)
        if available.width() / max(1.0, available.height()) > self._target_ratio:
            frame_height = available.height()
            frame_width = frame_height * self._target_ratio
        else:
            frame_width = available.width()
            frame_height = frame_width / self._target_ratio
        return QRectF(
            available.center().x() - frame_width / 2.0,
            available.center().y() - frame_height / 2.0,
            frame_width,
            frame_height,
        )

    def _source_rect(self) -> QRectF:
        frame = self._frame_rect()
        return background_source_rect(
            self._pixmap.width(),
            self._pixmap.height(),
            frame.width(),
            frame.height(),
            self._zoom,
            self._focus_x,
            self._focus_y,
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#15181D"))
        frame = self._frame_rect()

        if not self._pixmap.isNull():
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(frame, self._pixmap, self._source_rect())

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 84), 1.0))
        for fraction in (1.0 / 3.0, 2.0 / 3.0):
            x = frame.left() + frame.width() * fraction
            y = frame.top() + frame.height() * fraction
            painter.drawLine(QPointF(x, frame.top()), QPointF(x, frame.bottom()))
            painter.drawLine(QPointF(frame.left(), y), QPointF(frame.right(), y))

        painter.setPen(QPen(QColor("#F59AB8"), 2.0))
        painter.drawRoundedRect(frame, 8.0, 8.0)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._frame_rect().contains(event.position())
        ):
            self._drag_origin = event.position()
            self._drag_focus = (self._focus_x, self._focus_y)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is None:
            super().mouseMoveEvent(event)
            return
        frame = self._frame_rect()
        source = self._source_rect()
        delta = event.position() - self._drag_origin
        available_x = max(0.0, self._pixmap.width() - source.width())
        available_y = max(0.0, self._pixmap.height() - source.height())
        focus_x = self._drag_focus[0]
        focus_y = self._drag_focus[1]
        if available_x > 0.01:
            focus_x -= delta.x() * source.width() / frame.width() / available_x
        if available_y > 0.01:
            focus_y -= delta.y() * source.height() / frame.height() / available_y
        self._focus_x = max(0.0, min(1.0, focus_x))
        self._focus_y = max(0.0, min(1.0, focus_y))
        self.update()
        self.transform_changed.emit(self._zoom, self._focus_x, self._focus_y)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            self._drag_origin = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        steps = event.angleDelta().y() // 120
        if steps:
            self.set_zoom(self._zoom + steps * 10)
            event.accept()
            return
        super().wheelEvent(event)


class BackgroundCropDialog(QDialog):
    def __init__(
        self,
        image_path: Path,
        target_size: QSize,
        *,
        zoom: int = 100,
        focus_x: float = 0.5,
        focus_y: float = 0.5,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("smartactionExcludeGlobalTheme", True)
        self.setWindowTitle("Crop & Position Background")
        self.setMinimumSize(680, 540)
        self.resize(840, 620)
        self.setStyleSheet("""
            QDialog { background: #11151C; color: #EEF2F7; }
            QLabel { color: #DCE3EC; }
            QPushButton {
                min-height: 32px; padding: 0 14px; border-radius: 8px;
                color: #F6EAF0; background: #252B35; border: 1px solid #3B4452;
            }
            QPushButton:hover { background: #303846; border-color: #F59AB8; }
            QSlider::groove:horizontal { height: 6px; background: #343C48; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #F08CAC; border-radius: 3px; }
            QSlider::handle:horizontal {
                width: 18px; margin: -6px 0; border-radius: 9px;
                background: #FFF6F9; border: 2px solid #E8789C;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Drag the photo to position it inside the frame")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title)

        hint = QLabel(
            "Use the slider or mouse wheel to zoom. The original image is kept unchanged."
        )
        hint.setStyleSheet("font-size: 12px; color: #AAB5C3;")
        layout.addWidget(hint)

        self._canvas = BackgroundCropCanvas(
            image_path,
            target_size,
            zoom,
            focus_x,
            focus_y,
        )
        layout.addWidget(self._canvas, stretch=1)

        source_size = self._canvas.image_size
        detail = QLabel(
            f"Source {source_size.width()} × {source_size.height()}  ·  "
            f"Frame {target_size.width()} × {target_size.height()}  ·  High-DPI output"
        )
        detail.setStyleSheet("font-size: 11px; color: #8F9AA8;")
        layout.addWidget(detail)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(QLabel("Zoom"))
        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(100, 400)
        self._zoom_slider.setValue(max(100, min(400, zoom)))
        self._zoom_slider.valueChanged.connect(self._canvas.set_zoom)
        controls.addWidget(self._zoom_slider, stretch=1)
        self._zoom_label = QLabel(f"{self._zoom_slider.value()}%")
        self._zoom_label.setFixedWidth(48)
        controls.addWidget(self._zoom_label)
        reset = QPushButton("Reset")
        reset.clicked.connect(self._canvas.reset_transform)
        controls.addWidget(reset)
        layout.addLayout(controls)

        self._canvas.transform_changed.connect(self._on_transform_changed)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Crop")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        center_window(self, screen_for_widget(parent) if parent is not None else None)

    def _on_transform_changed(self, zoom: int, _focus_x: float, _focus_y: float) -> None:
        if self._zoom_slider.value() != zoom:
            self._zoom_slider.setValue(zoom)
        self._zoom_label.setText(f"{zoom}%")

    def crop_values(self) -> tuple[int, float, float]:
        return self._canvas.transform()
