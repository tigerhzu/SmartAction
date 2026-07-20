from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QScreen
from PySide6.QtWidgets import QDialog, QWidget


def _as_size(value: QSize | tuple[int, int]) -> QSize:
    if isinstance(value, QSize):
        return value
    return QSize(int(value[0]), int(value[1]))


def screen_at_cursor() -> QScreen | None:
    return QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()


def screen_for_widget(
    widget: QWidget,
    preferred_screen: QScreen | None = None,
) -> QScreen | None:
    if preferred_screen is not None:
        return preferred_screen
    parent = widget.parentWidget()
    if parent is not None and parent.screen() is not None:
        return parent.screen()

    # An unshown top-level QWidget reports the primary screen even when it was
    # created from a Ring action on another monitor. Prefer the cursor screen
    # before widget.screen() so first-show placement follows the active monitor.
    return screen_at_cursor() or widget.screen() or QGuiApplication.primaryScreen()


def fit_window_to_screen(
    widget: QWidget,
    preferred_size: QSize | tuple[int, int],
    minimum_size: QSize | tuple[int, int],
    *,
    width_ratio: float = 0.92,
    height_ratio: float = 0.88,
    allow_maximize: bool = True,
    center: bool = True,
    screen: QScreen | None = None,
) -> QSize:
    screen = screen_for_widget(widget, screen)
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
        center_window(widget, screen)
    return size


def center_window(
    widget: QWidget,
    screen: QScreen | None = None,
) -> None:
    screen = screen_for_widget(widget, screen)
    if screen is None:
        return
    geo = screen.availableGeometry()
    width = min(widget.width(), geo.width())
    height = min(widget.height(), geo.height())
    if width != widget.width() or height != widget.height():
        widget.resize(width, height)
    widget.move(
        geo.left() + max(0, (geo.width() - widget.width()) // 2),
        geo.top() + max(0, (geo.height() - widget.height()) // 2),
    )


def show_window_on_screen(
    widget: QWidget,
    screen: QScreen | None = None,
) -> None:
    """Show or restore a top-level window on the requested monitor."""
    target = screen_for_widget(widget, screen)
    center_window(widget, target)
    if widget.isMinimized():
        widget.showNormal()
    else:
        widget.show()
    # Reapply after show because Windows may restore an old native geometry.
    center_window(widget, target)
    widget.raise_()
    widget.activateWindow()


def exec_dialog_on_screen(
    dialog: QDialog,
    screen: QScreen | None = None,
) -> int:
    """Run a modal dialog centred on the requested monitor."""
    target = screen_for_widget(dialog, screen)
    center_window(dialog, target)
    return dialog.exec()


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
