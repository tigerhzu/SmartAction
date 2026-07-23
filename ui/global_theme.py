from __future__ import annotations

import weakref
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableView,
    QTextEdit,
    QWidget,
)

from core.actions_config import (
    ActionsConfig,
    UI_THEME_CLASSIC,
    UI_THEME_CUTE,
    UI_THEME_WOVEN,
)
from core.paths import ASSETS_DIR
from ui.woven_light_background import WovenLightBackground


_BASE_STYLE_PROPERTY = "_smartactionBaseStyle"
_APPLIED_STYLE_PROPERTY = "_smartactionAppliedStyle"
_BACKGROUND_OBJECT_NAME = "smartactionGlobalUiBackground"
_WOVEN_OBJECT_NAME = "smartactionWovenLightBackground"
_CUTE_MARKER = "/* smartaction-cute-ui */"
_WOVEN_MARKER = "/* smartaction-woven-light-ui */"
_THEME_MARKERS = (_CUTE_MARKER, _WOVEN_MARKER)
_CUTE_PANEL = "rgba(255, 247, 250, 225)"
_CUTE_DEEP_PANEL = "rgba(246, 226, 236, 148)"
_CUTE_DEEP_BORDER = "rgba(211, 124, 155, 178)"
_CUTE_DEFAULT_BACKGROUND = ASSETS_DIR / "ui" / "cute-default-background.png"


@dataclass(frozen=True)
class UiAppearance:
    theme: str = UI_THEME_CLASSIC
    background_path: Path | None = None
    background_opacity: int = 82
    background_zoom: int = 100
    background_focus_x: float = 0.5
    background_focus_y: float = 0.5


_CUTE_ROOT_QSS = f"""
{_CUTE_MARKER}
QWidget {{
    color: #574852;
    font-family: "Segoe UI Variable Text";
}}
QDialog, QMainWindow {{ background: transparent; }}
QLabel {{ color: #574852; background: transparent; }}
QPushButton {{
    color: #6B4554;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFDFE, stop:0.48 #FFEAF1, stop:1 #FFD5E2);
    border: 2px solid #F2AFC3;
    border-radius: 13px;
    padding: 0 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    color: #8D3D5B;
    background: #FFF5F9;
    border-color: #E983A4;
}}
QPushButton:pressed {{ background: #F8BDD0; border-color: #D96C91; }}
QPushButton:disabled {{ color: #B9A7AE; background: #F2E9ED; border-color: #DCCDD3; }}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    color: #493D45;
    background: #FFF9FB;
    border: 1px solid #E7B8C8;
    border-radius: 11px;
    selection-background-color: #F4A9C1;
    selection-color: #4C3540;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{
    color: #493D45; background: #FFF9FB; border: 2px solid #E882A4;
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover,
QTextEdit:hover, QPlainTextEdit:hover {{ color: #493D45; background: #FFF9FB; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
QTextEdit:disabled, QPlainTextEdit:disabled {{
    color: #A8959E; background: #F5EDF0; border-color: #DCCDD3;
}}
QComboBox QAbstractItemView {{
    color: #493D45;
    background: #FFF8FB;
    border: 1px solid #E7B8C8;
    selection-background-color: #FFD7E4;
    selection-color: #6B4554;
}}
QListWidget, QTreeWidget, QTableWidget, QTableView {{
    color: #493D45;
    background: rgba(255, 255, 255, 205);
    alternate-background-color: rgba(255, 242, 247, 215);
    border: 1px solid #E7B8C8;
    border-radius: 12px;
    gridline-color: #F0CCD8;
    selection-background-color: #FFD3E1;
    selection-color: #6B4554;
}}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected, QTableView::item:selected {{
    color: #713D52;
    background: #FFD3E1;
}}
QListWidget::item, QTreeWidget::item,
QTableWidget::item, QTableView::item {{ color: #493D45; }}
QHeaderView::section {{
    color: #795565;
    background: rgba(255, 238, 244, 230);
    border: none;
    border-bottom: 1px solid #E7B8C8;
    padding: 6px;
}}
QCheckBox {{ color: #654E59; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid #E6A7BC;
    border-radius: 7px;
    background: #FFF9FB;
}}
QCheckBox::indicator:checked {{ background: #F39AB8; border-color: #D96C91; }}
QSlider::groove:horizontal {{ height: 7px; background: #F2CFDA; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: #ED91AF; border-radius: 3px; }}
QSlider::handle:horizontal {{
    width: 18px; margin: -6px 0;
    background: #FFF9FB; border: 2px solid #DC7898; border-radius: 9px;
}}
QMenu {{ color: #574852; background: #FFF7FA; border: 1px solid #E7B8C8; border-radius: 10px; }}
QMenu::item:selected {{ color: #713D52; background: #FFD9E5; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #E7A9BD; border-radius: 5px; min-height: 28px; }}
QToolTip {{ color: #574852; background: #FFF8FB; border: 1px solid #E7B8C8; padding: 5px; }}
"""

_CUTE_BUTTON_QSS = f"""
{_CUTE_MARKER}
QPushButton {{
    color: #6B4554;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFDFE, stop:0.48 #FFEAF1, stop:1 #FFD5E2);
    border: 2px solid #F2AFC3;
    border-radius: 13px;
    padding: 0 14px;
    font-weight: 600;
}}
QPushButton:hover {{ color: #8D3D5B; background: #FFF5F9; border-color: #E983A4; }}
QPushButton:pressed {{ background: #F8BDD0; border-color: #D96C91; }}
QPushButton:disabled {{ color: #B9A7AE; background: #F2E9ED; border-color: #DCCDD3; }}
"""

_CUTE_FIELD_QSS = f"""
{_CUTE_MARKER}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    color: #493D45;
    background: #FFF9FB;
    border: 1px solid #E7B8C8;
    border-radius: 11px;
    selection-background-color: #F4A9C1;
    selection-color: #4C3540;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{
    color: #493D45; background: #FFF9FB; border: 2px solid #E882A4;
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover,
QTextEdit:hover, QPlainTextEdit:hover {{ color: #493D45; background: #FFF9FB; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
QTextEdit:disabled, QPlainTextEdit:disabled {{
    color: #A8959E; background: #F5EDF0; border-color: #DCCDD3;
}}
QLineEdit[placeholderText] {{ color: #493D45; }}
QComboBox QAbstractItemView {{
    color: #493D45; background: #FFF8FB; border: 1px solid #E7B8C8;
    selection-background-color: #FFD7E4; selection-color: #6B4554;
}}
"""

_CUTE_ITEM_VIEW_QSS = f"""
{_CUTE_MARKER}
QListWidget, QTreeWidget, QTableWidget, QTableView, QAbstractItemView {{
    color: #493D45;
    background: rgba(255, 255, 255, 205);
    alternate-background-color: rgba(255, 242, 247, 215);
    border: 1px solid #E7B8C8;
    border-radius: 12px;
    gridline-color: #F0CCD8;
    selection-background-color: #FFD3E1;
    selection-color: #6B4554;
}}
QListWidget::item, QTreeWidget::item,
QTableWidget::item, QTableView::item {{ color: #493D45; }}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected, QTableView::item:selected {{
    color: #713D52; background: #FFD3E1;
}}
QListWidget::item:focus, QTreeWidget::item:focus,
QTableWidget::item:focus, QTableView::item:focus {{ border: 1px solid #E882A4; }}
QHeaderView::section {{
    color: #795565; background: #FFEEF4; border: none;
    border-bottom: 1px solid #E7B8C8; padding: 6px;
}}
QTableCornerButton::section {{ background: #FFEEF4; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #E7A9BD; border-radius: 5px; min-height: 28px; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 3px; }}
QScrollBar::handle:horizontal {{ background: #E7A9BD; border-radius: 5px; min-width: 28px; }}
"""

_CUTE_LABEL_QSS = f"""
{_CUTE_MARKER}
QLabel {{ color: #574852; background: transparent; border-color: #E7B8C8; }}
"""

_CUTE_CHECKBOX_QSS = f"""
{_CUTE_MARKER}
QCheckBox {{ color: #654E59; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 2px solid #E6A7BC;
    border-radius: 7px; background: #FFF9FB;
}}
QCheckBox::indicator:checked {{ background: #F39AB8; border-color: #D96C91; }}
"""

_WOVEN_ROOT_QSS = f"""
{_WOVEN_MARKER}
QWidget {{
    color: #1C2430;
    font-family: "Segoe UI Variable Text";
}}
QDialog, QMainWindow {{ background: transparent; }}
QLabel {{ color: #27313E; background: transparent; }}
QPushButton {{
    color: #202833;
    background: rgba(255, 255, 255, 226);
    border: 1px solid rgba(139, 153, 173, 150);
    border-radius: 12px;
    padding: 0 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    color: #111720;
    background: rgba(255, 255, 255, 248);
    border-color: #70809A;
}}
QPushButton:pressed {{ background: #E9EDF3; border-color: #56657C; }}
QPushButton:disabled {{
    color: #687587; background: rgba(235, 239, 245, 218);
    border-color: rgba(174, 184, 198, 120);
}}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    color: #17202B;
    background: rgba(255, 255, 255, 224);
    border: 1px solid rgba(140, 154, 174, 145);
    border-radius: 10px;
    selection-background-color: #BDEAF0;
    selection-color: #17202B;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{
    color: #111720;
    background: rgba(255, 255, 255, 246);
    border: 2px solid #7186A4;
}}
QComboBox QAbstractItemView {{
    color: #1C2430;
    background: #F9FBFD;
    border: 1px solid #CAD2DE;
    selection-background-color: #DDECF4;
    selection-color: #17202B;
}}
QComboBox QAbstractItemView::item {{
    color: #1C2430;
    background: #F9FBFD;
}}
QComboBox QAbstractItemView::item:selected {{
    color: #111720;
    background: #DDECF4;
}}
QListWidget, QTreeWidget, QTableWidget, QTableView {{
    color: #1C2430;
    background: rgba(255, 255, 255, 210);
    alternate-background-color: rgba(243, 247, 251, 220);
    border: 1px solid rgba(163, 175, 192, 130);
    border-radius: 12px;
    gridline-color: rgba(177, 187, 201, 100);
    selection-background-color: #D9EAF1;
    selection-color: #17202B;
}}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected, QTableView::item:selected {{
    color: #17202B;
    background: rgba(214, 235, 242, 235);
}}
QHeaderView::section {{
    color: #425064;
    background: rgba(239, 243, 248, 232);
    border: none;
    border-bottom: 1px solid #D1D8E2;
    padding: 6px;
}}
QCheckBox {{ color: #354153; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1px solid #9DAABA;
    border-radius: 6px;
    background: rgba(255, 255, 255, 230);
}}
QCheckBox::indicator:checked {{ background: #53647C; border-color: #53647C; }}
QSlider::groove:horizontal {{ height: 6px; background: #DCE3EB; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: #8191A8; border-radius: 3px; }}
QSlider::handle:horizontal {{
    width: 18px; margin: -6px 0;
    background: #FFFFFF; border: 2px solid #66778F; border-radius: 9px;
}}
QMenu {{
    color: #1C2430; background: #FAFBFD;
    border: 1px solid #CAD2DE; border-radius: 10px;
}}
QMenu::item {{
    color: #1C2430;
    background: transparent;
}}
QMenu::item:selected {{ color: #17202B; background: #DFEAF2; }}
QMenu::item:disabled {{ color: #6A7687; }}
QMenu::separator {{ height: 1px; background: #AAB5C4; margin: 6px 4px; }}
QGroupBox {{ color: #27313E; }}
QRadioButton {{ color: #27313E; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #B8C3D1; border-radius: 5px; min-height: 28px; }}
QToolTip {{ color: #1C2430; background: #FFFFFF; border: 1px solid #CAD2DE; padding: 5px; }}
"""

_WOVEN_BUTTON_QSS = f"""
{_WOVEN_MARKER}
QPushButton {{
    color: #202833; background: rgba(255, 255, 255, 226);
    border: 1px solid rgba(139, 153, 173, 150);
    border-radius: 12px; padding: 0 14px; font-weight: 600;
}}
QPushButton:hover {{
    color: #111720; background: rgba(255, 255, 255, 248);
    border-color: #70809A;
}}
QPushButton:pressed {{ background: #E9EDF3; border-color: #56657C; }}
QPushButton:disabled {{
    color: #687587; background: rgba(235, 239, 245, 218);
    border-color: rgba(174, 184, 198, 120);
}}
"""

_WOVEN_FIELD_QSS = f"""
{_WOVEN_MARKER}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    color: #17202B; background: rgba(255, 255, 255, 224);
    border: 1px solid rgba(140, 154, 174, 145); border-radius: 10px;
    selection-background-color: #BDEAF0; selection-color: #17202B;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{
    color: #111720; background: rgba(255, 255, 255, 246);
    border: 2px solid #7186A4;
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
QTextEdit:disabled, QPlainTextEdit:disabled {{
    color: #697587; background: rgba(235, 239, 245, 218);
    border-color: rgba(174, 184, 198, 120);
}}
QComboBox QAbstractItemView {{
    color: #1C2430; background: #F9FBFD; border: 1px solid #CAD2DE;
    selection-background-color: #DDECF4; selection-color: #17202B;
}}
QComboBox QAbstractItemView::item {{
    color: #1C2430; background: #F9FBFD;
}}
QComboBox QAbstractItemView::item:selected {{
    color: #111720; background: #DDECF4;
}}
"""

_WOVEN_ITEM_VIEW_QSS = f"""
{_WOVEN_MARKER}
QListWidget, QTreeWidget, QTableWidget, QTableView, QAbstractItemView {{
    color: #1C2430; background: rgba(255, 255, 255, 210);
    alternate-background-color: rgba(243, 247, 251, 220);
    border: 1px solid rgba(163, 175, 192, 130); border-radius: 12px;
    gridline-color: rgba(177, 187, 201, 100);
    selection-background-color: #D9EAF1; selection-color: #17202B;
}}
QListWidget::item, QTreeWidget::item,
QTableWidget::item, QTableView::item {{ color: #27313E; }}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected, QTableView::item:selected {{
    color: #17202B; background: rgba(214, 235, 242, 235);
}}
QHeaderView::section {{
    color: #425064; background: rgba(239, 243, 248, 232);
    border: none; border-bottom: 1px solid #D1D8E2; padding: 6px;
}}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #B8C3D1; border-radius: 5px; min-height: 28px; }}
"""

_WOVEN_LABEL_QSS = f"""
{_WOVEN_MARKER}
QLabel {{ color: #27313E; background: transparent; border-color: #CDD5E0; }}
"""

_WOVEN_CHECKBOX_QSS = f"""
{_WOVEN_MARKER}
QCheckBox {{ color: #354153; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 1px solid #9DAABA;
    border-radius: 6px; background: rgba(255, 255, 255, 230);
}}
QCheckBox::indicator:checked {{ background: #53647C; border-color: #53647C; }}
"""


def appearance_from_config(config: ActionsConfig) -> UiAppearance:
    theme = config.get_ui_theme()
    custom_path = config.resolve_ui_background()
    path = (
        custom_path
        if custom_path is not None and custom_path.is_file()
        else default_cute_background_path()
        if theme == UI_THEME_CUTE
        else None
    )
    focus_x, focus_y = config.get_ui_background_focus()
    return UiAppearance(
        theme=theme,
        background_path=path,
        background_opacity=config.get_ui_background_opacity(),
        background_zoom=config.get_ui_background_zoom(),
        background_focus_x=focus_x,
        background_focus_y=focus_y,
    )


def default_cute_background_path() -> Path | None:
    """Return the bundled Cute artwork without creating writable config."""
    return (
        _CUTE_DEFAULT_BACKGROUND
        if _CUTE_DEFAULT_BACKGROUND.is_file()
        else None
    )


def apply_ui_appearance(root: QWidget, appearance: UiAppearance) -> None:
    if _excluded(root):
        return
    widgets = [root, *root.findChildren(QWidget)]
    if appearance.theme in {UI_THEME_CUTE, UI_THEME_WOVEN}:
        for widget in widgets:
            if widget.objectName() in {
                _BACKGROUND_OBJECT_NAME,
                _WOVEN_OBJECT_NAME,
            }:
                continue
            _apply_theme_style(
                widget,
                appearance.theme,
                is_root=widget is root,
            )
        if _supports_background(root):
            if appearance.theme == UI_THEME_CUTE:
                _hide_woven_background(root)
                _update_background(root, appearance)
            else:
                _hide_image_background(root)
                _update_woven_background(root)
        else:
            _hide_visual_backgrounds(root)
    else:
        for widget in widgets:
            if widget.objectName() in {
                _BACKGROUND_OBJECT_NAME,
                _WOVEN_OBJECT_NAME,
            }:
                widget.hide()
                continue
            _restore_base_style(widget)


class GlobalUiThemeManager(QObject):
    def __init__(self, app: QApplication, config: ActionsConfig) -> None:
        super().__init__(app)
        self._app = app
        self._config = config
        self._appearance = appearance_from_config(config)
        self._pending_background_updates: set[int] = set()
        app.installEventFilter(self)

    @property
    def appearance(self) -> UiAppearance:
        return self._appearance

    def reload(self) -> None:
        self._appearance = appearance_from_config(self._config)
        for widget in self._app.topLevelWidgets():
            apply_ui_appearance(widget, self._appearance)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(watched, QWidget) or _excluded(watched):
            return super().eventFilter(watched, event)
        if event.type() == QEvent.Type.Show and watched.isWindow():
            widget_ref = weakref.ref(watched)
            QTimer.singleShot(0, lambda: self._apply_later(widget_ref))
        elif (
            event.type() == QEvent.Type.Resize
            and watched.isWindow()
            and self._appearance.theme in {UI_THEME_CUTE, UI_THEME_WOVEN}
        ):
            self._schedule_background_update(watched)
        return super().eventFilter(watched, event)

    def _apply_later(self, widget_ref) -> None:
        widget = widget_ref()
        if widget is not None:
            apply_ui_appearance(widget, self._appearance)

    def _schedule_background_update(self, widget: QWidget) -> None:
        key = id(widget)
        if key in self._pending_background_updates:
            return
        self._pending_background_updates.add(key)
        widget_ref = weakref.ref(widget)
        QTimer.singleShot(
            40,
            lambda: self._update_background_later(key, widget_ref),
        )

    def _update_background_later(self, key: int, widget_ref) -> None:
        self._pending_background_updates.discard(key)
        widget = widget_ref()
        if widget is None:
            return
        if self._appearance.theme == UI_THEME_CUTE:
            _update_background(widget, self._appearance)
        elif self._appearance.theme == UI_THEME_WOVEN:
            _update_woven_background(widget)


def _excluded(widget: QWidget) -> bool:
    if widget.property("smartactionExcludeGlobalTheme"):
        return True
    root = widget.window()
    return root.__class__.__name__ in {"RingWindow", "StartupSplash"}


def _supports_background(root: QWidget) -> bool:
    """Return whether a full-page custom image is safe for this window.

    Combo lists, menus and tooltips are transient top-level widgets in Qt.
    Giving them a child image label covers their text and can look like a
    detached image floating above the Windows system tray.
    """
    if not isinstance(root, QDialog):
        return False
    return root.windowType() not in {
        Qt.WindowType.Popup,
        Qt.WindowType.ToolTip,
        Qt.WindowType.SplashScreen,
    }


def _hide_image_background(root: QWidget) -> None:
    label = root.findChild(
        QLabel,
        _BACKGROUND_OBJECT_NAME,
        Qt.FindChildOption.FindDirectChildrenOnly,
    )
    if label is not None:
        label.hide()


def _hide_woven_background(root: QWidget) -> None:
    backdrop = root.findChild(
        WovenLightBackground,
        _WOVEN_OBJECT_NAME,
        Qt.FindChildOption.FindDirectChildrenOnly,
    )
    if backdrop is not None:
        backdrop.hide()


def _hide_visual_backgrounds(root: QWidget) -> None:
    _hide_image_background(root)
    _hide_woven_background(root)


def _hide_background(root: QWidget) -> None:
    """Compatibility wrapper retained for older callers."""
    _hide_visual_backgrounds(root)


def _apply_theme_style(
    widget: QWidget,
    theme: str,
    *,
    is_root: bool,
) -> None:
    current = widget.styleSheet()
    base = widget.property(_BASE_STYLE_PROPERTY)
    applied = widget.property(_APPLIED_STYLE_PROPERTY)
    has_theme_marker = any(marker in current for marker in _THEME_MARKERS)
    if base is None or (current != applied and not has_theme_marker):
        base = current
        widget.setProperty(_BASE_STYLE_PROPERTY, base)

    overlay = _overlay_for_widget(
        widget,
        theme=theme,
        is_root=is_root,
        base_style=str(base or ""),
    )
    if not overlay:
        return
    combined = f"{base or ''}\n{overlay}"
    if current != combined:
        widget.setStyleSheet(combined)
    widget.setProperty(_APPLIED_STYLE_PROPERTY, combined)


def _restore_base_style(widget: QWidget) -> None:
    base = widget.property(_BASE_STYLE_PROPERTY)
    applied = widget.property(_APPLIED_STYLE_PROPERTY)
    current = widget.styleSheet()
    has_theme_marker = any(marker in current for marker in _THEME_MARKERS)
    if base is not None and (current == applied or has_theme_marker):
        widget.setStyleSheet(str(base))
    widget.setProperty(_APPLIED_STYLE_PROPERTY, None)


def _overlay_for_widget(
    widget: QWidget,
    *,
    theme: str,
    is_root: bool,
    base_style: str,
) -> str:
    woven = theme == UI_THEME_WOVEN
    root_qss = _WOVEN_ROOT_QSS if woven else _CUTE_ROOT_QSS
    checkbox_qss = _WOVEN_CHECKBOX_QSS if woven else _CUTE_CHECKBOX_QSS
    button_qss = _WOVEN_BUTTON_QSS if woven else _CUTE_BUTTON_QSS
    field_qss = _WOVEN_FIELD_QSS if woven else _CUTE_FIELD_QSS
    item_view_qss = _WOVEN_ITEM_VIEW_QSS if woven else _CUTE_ITEM_VIEW_QSS
    label_qss = _WOVEN_LABEL_QSS if woven else _CUTE_LABEL_QSS
    marker = _WOVEN_MARKER if woven else _CUTE_MARKER
    text_color = "#27313E" if woven else "#574852"
    border_color = "#CDD5E0" if woven else "#E7B8C8"

    if is_root or isinstance(widget, (QDialog, QMenu)):
        return root_qss
    if isinstance(widget, QCheckBox):
        return checkbox_qss
    if isinstance(widget, (QPushButton, QAbstractButton)):
        return button_qss
    if isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit)):
        return field_qss
    if isinstance(widget, (QTableView, QAbstractItemView)):
        return item_view_qss
    if isinstance(widget, QLabel):
        if base_style and "{" not in base_style:
            return (
                f"\n{marker}\n"
                f"color: {text_color}; background: transparent; "
                f"border-color: {border_color};"
            )
        return label_qss
    if isinstance(widget, QSlider):
        return root_qss
    if isinstance(widget, QFrame) and widget.styleSheet():
        if "{" not in base_style:
            return f"\n{marker}\nbackground: {border_color}; border: none;"
        return _direct_panel_overlay(widget, theme)
    if type(widget) is QWidget and widget.styleSheet():
        if "{" not in base_style:
            if woven:
                return (
                    f"\n{marker}\n"
                    "color: #1C2430; background: rgba(255, 255, 255, 126); "
                    "border-color: rgba(164, 176, 193, 135);"
                )
            if _uses_deep_cute_surface(widget):
                return (
                    f"\n{marker}\n"
                    f"color: #574852; background: {_CUTE_DEEP_PANEL}; "
                    f"border-color: {_CUTE_DEEP_BORDER};"
                )
            return (
                f"\n{marker}\n"
                f"color: #574852; background: {_CUTE_PANEL}; "
                "border-color: rgba(225, 153, 178, 150);"
            )
        return _direct_panel_overlay(widget, theme)
    return ""


def _uses_deep_cute_surface(widget: QWidget) -> bool:
    root = widget.window()
    return bool(root.property("smartactionCuteDeepSurface"))


def _direct_panel_overlay(widget: QWidget, theme: str) -> str:
    name = widget.objectName()
    if not name:
        prefix = (
            "smartactionWovenPanel"
            if theme == UI_THEME_WOVEN
            else "smartactionCutePanel"
        )
        name = f"{prefix}{id(widget)}"
        widget.setObjectName(name)
    if theme == UI_THEME_WOVEN:
        return f"""
{_WOVEN_MARKER}
QWidget#{name} {{
    color: #1C2430;
    background: rgba(255, 255, 255, 126);
    border-color: rgba(164, 176, 193, 135);
}}
QWidget {{
    background: transparent;
}}
QWidget#{name} {{
    background: rgba(255, 255, 255, 126);
}}
"""
    panel = (
        _CUTE_DEEP_PANEL
        if _uses_deep_cute_surface(widget)
        else _CUTE_PANEL
    )
    border = (
        _CUTE_DEEP_BORDER
        if _uses_deep_cute_surface(widget)
        else "rgba(225, 153, 178, 150)"
    )
    return f"""
{_CUTE_MARKER}
QWidget#{name} {{
    color: #574852;
    background: {panel};
    border-color: {border};
}}
QWidget {{
    background: transparent;
}}
QWidget#{name} {{
    background: {panel};
}}
"""


def _update_background(root: QWidget, appearance: UiAppearance) -> None:
    if (
        _excluded(root)
        or not _supports_background(root)
        or root.width() < 2
        or root.height() < 2
    ):
        _hide_background(root)
        return
    label = root.findChild(
        QLabel,
        _BACKGROUND_OBJECT_NAME,
        Qt.FindChildOption.FindDirectChildrenOnly,
    )
    if label is None:
        label = QLabel(root)
        label.setObjectName(_BACKGROUND_OBJECT_NAME)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setStyleSheet("background: transparent; border: none;")
    label.setGeometry(root.rect())
    label.setPixmap(
        _render_background(
            root.width(),
            root.height(),
            appearance,
            max(1.0, root.devicePixelRatioF()),
        )
    )
    label.show()
    label.lower()


def _update_woven_background(root: QWidget) -> None:
    if (
        _excluded(root)
        or not _supports_background(root)
        or root.width() < 2
        or root.height() < 2
    ):
        _hide_visual_backgrounds(root)
        return
    backdrop = root.findChild(
        WovenLightBackground,
        _WOVEN_OBJECT_NAME,
        Qt.FindChildOption.FindDirectChildrenOnly,
    )
    if backdrop is None:
        backdrop = WovenLightBackground(root)
        backdrop.setObjectName(_WOVEN_OBJECT_NAME)
    backdrop.setGeometry(root.rect())
    backdrop.show()
    backdrop.lower()


def background_source_rect(
    source_width: float,
    source_height: float,
    target_width: float,
    target_height: float,
    zoom_percent: int,
    focus_x: float,
    focus_y: float,
) -> QRectF:
    """Return the source crop used to cover a target without empty edges."""
    if min(source_width, source_height, target_width, target_height) <= 0:
        return QRectF()
    base_scale = max(target_width / source_width, target_height / source_height)
    zoom = max(1.0, min(4.0, zoom_percent / 100.0))
    visible_width = min(source_width, target_width / (base_scale * zoom))
    visible_height = min(source_height, target_height / (base_scale * zoom))
    available_x = max(0.0, source_width - visible_width)
    available_y = max(0.0, source_height - visible_height)
    left = available_x * max(0.0, min(1.0, focus_x))
    top = available_y * max(0.0, min(1.0, focus_y))
    return QRectF(left, top, visible_width, visible_height)


def _render_background(
    width: int,
    height: int,
    appearance: UiAppearance,
    device_pixel_ratio: float = 1.0,
) -> QPixmap:
    dpr = max(1.0, float(device_pixel_ratio))
    canvas = QPixmap(
        max(1, math.ceil(width * dpr)),
        max(1, math.ceil(height * dpr)),
    )
    canvas.setDevicePixelRatio(dpr)
    canvas.fill(QColor("#FFF5F9"))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    source = _load_background_pixmap(appearance.background_path)
    if not source.isNull():
        source_rect = background_source_rect(
            source.width(),
            source.height(),
            width,
            height,
            appearance.background_zoom,
            appearance.background_focus_x,
            appearance.background_focus_y,
        )
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setOpacity(max(0.15, min(1.0, appearance.background_opacity / 100.0)))
        painter.drawPixmap(QRectF(0, 0, width, height), source, source_rect)
        painter.setOpacity(1.0)
        painter.fillRect(QRectF(0, 0, width, height), QColor(255, 247, 251, 28))
    else:
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0.0, QColor("#FFF9FB"))
        gradient.setColorAt(0.48, QColor("#FFE5EE"))
        gradient.setColorAt(1.0, QColor("#E8F5FF"))
        painter.fillRect(QRectF(0, 0, width, height), gradient)
        painter.setOpacity(0.24)
        for x, y, radius, color in (
            (0.08, 0.16, 110, "#F7A8C2"),
            (0.86, 0.18, 150, "#A9DDF5"),
            (0.72, 0.82, 190, "#F5B5D0"),
            (0.18, 0.88, 130, "#C3E5F6"),
        ):
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(width * x - radius),
                int(height * y - radius),
                radius * 2,
                radius * 2,
            )
        painter.setOpacity(1.0)

    painter.end()
    return canvas


def _load_background_pixmap(path: Path | None) -> QPixmap:
    if path is None:
        return QPixmap()
    try:
        modified_ns = path.stat().st_mtime_ns
    except OSError:
        return QPixmap()
    return _cached_background_pixmap(str(path), modified_ns)


@lru_cache(maxsize=4)
def _cached_background_pixmap(path: str, _modified_ns: int) -> QPixmap:
    return QPixmap(path)
