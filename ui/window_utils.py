from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QWidget


def _as_size(value: QSize | tuple[int, int]) -> QSize:
    if isinstance(value, QSize):
        return value
    return QSize(int(value[0]), int(value[1]))


def screen_for_widget(widget: QWidget):
    parent = widget.parentWidget()
    screen = widget.screen() or (parent.screen() if parent is not None else None)
    return screen or QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()


def fit_window_to_screen(
    widget: QWidget,
    preferred_size: QSize | tuple[int, int],
    minimum_size: QSize | tuple[int, int],
    *,
    width_ratio: float = 0.92,
    height_ratio: float = 0.88,
    allow_maximize: bool = True,
    center: bool = True,
) -> QSize:
    screen = screen_for_widget(widget)
    preferred = _as_size(preferred_size)
    minimum = _as_size(minimum_size)
    if screen is None:
        widget.setMinimumSize(minimum)
        widget.resize(preferred)
        return preferred

    geo = screen.availableGeometry()
    max_w = max(320, int(geo.width() * width_ratio))
    max_h = max(260, int(geo.height() * height_ratio))
    min_w = min(minimum.width(), max_w)
    min_h = min(minimum.height(), max_h)
    width = min(max(preferred.width(), min_w), max_w)
    height = min(max(preferred.height(), min_h), max_h)
    size = QSize(width, height)

    if allow_maximize:
        widget.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
    widget.setMinimumSize(min_w, min_h)
    widget.resize(size)
    if center:
        center_window(widget)
    return size


def center_window(widget: QWidget) -> None:
    screen = screen_for_widget(widget)
    if screen is None:
        return
    geo = screen.availableGeometry()
    frame = widget.frameGeometry()
    frame.moveCenter(geo.center())
    widget.move(frame.topLeft())


def handle_fullscreen_shortcut(widget: QWidget, event) -> bool:
    key = event.key()
    if key == Qt.Key.Key_F11:
        if widget.isFullScreen():
            widget.showNormal()
        else:
            widget.showFullScreen()
        event.accept()
        return True
    if key == Qt.Key.Key_Escape and widget.isFullScreen():
        widget.showNormal()
        event.accept()
        return True
    return False
