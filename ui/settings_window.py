"""
SettingsWindow — CRUD editor for config/actions.json.

Layout
------
  Left  (220 px fixed) : list of first-level actions
  Right (stretches)    : form fields for selected action + sub_actions table
  Bottom               : Cancel / Save
"""
from __future__ import annotations

import copy
import webbrowser
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, QLineF, QPointF, QRect, QRectF, QSettings, QSize, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.actions_config import ActionsConfig
from core import autostart as _autostart
from core.constellation import (
    CONSTELLATION_ORDER,
    DEFAULT_CONSTELLATION,
    DEFAULT_CONSTELLATION_COLOR,
    constellation_label,
)
from core.debug_log import debug_log
from core.help_links import (
    ABOUT_URL,
    DOCUMENTATION_URL,
    GITHUB_ISSUES_URL,
    GITHUB_REPO_URL,
)
from core.paths import DOCS_DIR
from core.powershell_library import PowerShellLibrary
from core.profile_manager import (
    ProfileError,
    default_export_filename,
    export_profile,
    import_profile,
)
from ui.theme_painter import (
    draw_energy_bubble,
    draw_theme_card_background,
    prune_theme_asset_cache,
    theme_frame_count,
)
from ui.window_utils import center_window, fit_window_to_screen, handle_fullscreen_shortcut
from ui.style_tokens import (
    ASH,
    BONE,
    BODY_FONT_FAMILY,
    BUTTON_MIN_HEIGHT,
    CHARCOAL,
    CORNER_CUT_PX,
    EMBER,
    EMBER_HOVER,
    EMBER_PRESSED,
    EMBER_WASH,
    FIELD_HEIGHT,
    FOG,
    HEADLINE_FONT_FAMILY,
    ROW_HEIGHT,
    SIGNAL_AMBER,
    SIGNAL_AMBER_WASH,
    SIGNAL_RED,
    SIGNAL_RED_HOVER,
    SIGNAL_RED_PRESSED,
    SIGNAL_RED_WASH,
    SIGNAL_GREEN,
    STEEL,
    VOID,
)

# ── Type definitions ──────────────────────────────────────────────────────────

_TYPES_ORDERED = ["folder", "settings", "url", "app", "command", "powershell", "powershell_library", "environment_check", "client_workspace", "paste", "form", "ps_form"]

_TYPE_LABELS: dict[str, str] = {
    "folder":     "Folder",
    "settings":   "Settings",
    "url":        "URL",
    "app":        "App / File",
    "command":    "Command",
    "powershell": "PowerShell",
    "powershell_library": "PowerShell Library",
    "environment_check": "Environment Check",
    "client_workspace": "Client Workspace",
    "paste":      "Paste",
    "form":       "Form",
    "ps_form":    "PS Form",
}

_LABEL_TO_TYPE: dict[str, str] = {v: k for k, v in _TYPE_LABELS.items()}

_COMBO_ALL  = [_TYPE_LABELS[t] for t in _TYPES_ORDERED]
_COMBO_LEAF = [_TYPE_LABELS[t] for t in _TYPES_ORDERED if t != "folder"]
_TARGETLESS_TYPES = {"settings", "powershell_library", "environment_check", "client_workspace"}

# ── Shared stylesheets ────────────────────────────────────────────────────────

_RADIUS = 6
_PANEL_RADIUS = 8
_SOFT_BORDER = "rgba(236, 232, 225, 0.10)"
_SOFT_LINE = "rgba(236, 232, 225, 0.08)"
_NEON_EDGE = "rgba(242, 118, 11, 0.42)"
_FIELD_BG = "#10141B"
_PANEL_BG = "#11151D"
_PANEL_BG_ALT = "#151A23"

_S_FIELD = f"""
    QLineEdit {{
        color: {BONE};
        border: 1px solid {_SOFT_BORDER};
        border-radius: {_RADIUS}px;
        padding: 0 10px;
        font-size: 14px;
        background: {_FIELD_BG};
        min-height: {FIELD_HEIGHT}px;
        max-height: {FIELD_HEIGHT}px;
        selection-background-color: {EMBER};
        selection-color: {VOID};
    }}
    QLineEdit:hover {{
        border-color: {ASH};
        background: {CHARCOAL};
    }}
    QLineEdit:focus {{
        border-color: {EMBER};
        background: {CHARCOAL};
    }}
    QLineEdit:disabled {{
        color: {FOG};
        background: {STEEL};
        border-color: {ASH};
    }}
    QLineEdit[placeholderText] {{ color: {FOG}; }}
"""

_S_COMBO = f"""
    QComboBox {{
        color: {BONE};
        border: 1px solid {_SOFT_BORDER};
        border-radius: {_RADIUS}px;
        padding: 0 10px;
        font-size: 14px;
        background: {_FIELD_BG};
        min-height: {FIELD_HEIGHT}px;
        max-height: {FIELD_HEIGHT}px;
    }}
    QComboBox:hover {{
        border-color: {ASH};
        background: {CHARCOAL};
    }}
    QComboBox:focus {{
        border-color: {EMBER};
        background: {CHARCOAL};
    }}
    QComboBox:disabled {{
        color: {FOG};
        background: {STEEL};
        border-color: {ASH};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox::down-arrow {{
        image: none;
        width: 0;
        height: 0;
    }}
    QComboBox QAbstractItemView {{
        color: {BONE};
        background-color: {_PANEL_BG};
        border: 1px solid {_NEON_EDGE};
        outline: none;
        selection-background-color: {EMBER_WASH};
        selection-color: {BONE};
        font-size: 14px;
    }}
"""

_S_BTN_PRIMARY = f"""
    QPushButton {{
        background: {EMBER};
        color: {VOID};
        border: 1px solid {EMBER};
        border-radius: {_RADIUS}px;
        padding: 0 20px;
        font-size: 14px; font-weight: 600;
        min-height: {BUTTON_MIN_HEIGHT}px; max-height: {BUTTON_MIN_HEIGHT}px;
    }}
    QPushButton:hover   {{ background: {EMBER_HOVER}; }}
    QPushButton:pressed {{ background: {EMBER_PRESSED}; }}
    QPushButton:disabled {{
        background: {STEEL};
        color: {FOG};
        border-color: {ASH};
    }}
"""

_S_BTN_SECONDARY = f"""
    QPushButton {{
        background: rgba(236, 232, 225, 0.03);
        color: {BONE};
        border: 1px solid {_SOFT_BORDER};
        border-radius: {_RADIUS}px;
        padding: 0 20px; font-size: 14px;
        min-height: {BUTTON_MIN_HEIGHT}px; max-height: {BUTTON_MIN_HEIGHT}px;
    }}
    QPushButton:hover   {{ background: {STEEL}; border-color: {EMBER}; color: {BONE}; }}
    QPushButton:pressed {{ background: {CHARCOAL}; border-color: {EMBER_PRESSED}; }}
    QPushButton:disabled {{
        background: {STEEL};
        color: {FOG};
        border-color: {ASH};
    }}
"""

_S_BTN_SMALL = f"""
    QPushButton {{
        background: rgba(242, 118, 11, 0.10);
        color: {EMBER};
        border: 1px solid rgba(242, 118, 11, 0.36);
        border-radius: {_RADIUS}px;
        padding: 0 10px; font-size: 12px;
        font-weight: 600;
        min-height: 28px; max-height: 28px;
    }}
    QPushButton:hover    {{ background: rgba(242, 118, 11, 0.18); border-color: {EMBER}; }}
    QPushButton:pressed  {{ background: rgba(242, 118, 11, 0.26); border-color: {EMBER_PRESSED}; }}
    QPushButton:disabled {{ color: {FOG}; border-color: {ASH}; background: {STEEL}; }}
"""

_S_BTN_DANGER = f"""
    QPushButton {{
        background: rgba(229, 72, 77, 0.08);
        color: {SIGNAL_RED};
        border: 1px solid rgba(229, 72, 77, 0.45);
        border-radius: {_RADIUS}px;
        padding: 0 10px; font-size: 12px;
        font-weight: 600;
        min-height: 28px; max-height: 28px;
    }}
    QPushButton:hover    {{ background: {SIGNAL_RED_WASH}; border-color: {SIGNAL_RED}; }}
    QPushButton:pressed  {{ background: rgba(229, 72, 77, 0.22); border-color: {SIGNAL_RED_PRESSED}; }}
    QPushButton:disabled {{ color: {FOG}; border-color: {ASH}; background: {STEEL}; }}
"""

_S_TABLE = f"""
    QTableWidget {{
        color: {BONE};
        background-color: {_PANEL_BG};
        alternate-background-color: {_PANEL_BG_ALT};
        border: 1px solid {_SOFT_BORDER};
        border-radius: {_PANEL_RADIUS}px;
        font-size: 13px; gridline-color: {_SOFT_LINE}; outline: none;
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        color: {BONE};
        border: none;
    }}
    QTableWidget::item:selected {{
        background: {EMBER_WASH};
        color: {BONE};
    }}
    QHeaderView::section {{
        color: {FOG};
        background-color: {CHARCOAL};
        font-size: 11px; font-weight: 600;
        border: none; border-bottom: 1px solid {ASH};
        padding: 7px 10px;
    }}
"""

_S_CHECKBOX = f"""
    QCheckBox {{
        color: {BONE};
        font-size: 13px;
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {_SOFT_BORDER};
        background: {_FIELD_BG};
    }}
    QCheckBox::indicator:hover {{
        border-color: {EMBER};
    }}
    QCheckBox::indicator:checked {{
        background: {EMBER};
        border-color: {EMBER};
    }}
    QCheckBox::indicator:disabled {{
        background: {STEEL};
        border-color: {ASH};
    }}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _divider_h() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {ASH}; border: none;")
    return f


def _divider_v() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFixedWidth(1)
    f.setStyleSheet(f"background: {ASH}; border: none;")
    return f


def _caption(text: str) -> QLabel:
    label = QLabel(text)
    label.setMinimumWidth(96)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    font = QFont(HEADLINE_FONT_FAMILY)
    font.setPixelSize(13)
    font.setBold(True)
    label.setFont(font)
    label.setStyleSheet(f"color: {FOG};")
    return label


_S_MESSAGE_BOX = f"""
    QMessageBox {{
        background: {VOID};
        color: {BONE};
    }}
    QMessageBox QLabel {{
        color: {BONE};
        background: transparent;
        font-size: 14px;
        selection-background-color: {EMBER};
        selection-color: {VOID};
    }}
    QMessageBox QPushButton {{
        background: {CHARCOAL};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        min-width: 82px;
        min-height: 32px;
        padding: 0 14px;
        font-size: 14px;
    }}
    QMessageBox QPushButton:hover {{
        background: {STEEL};
        border-color: {EMBER};
    }}
    QMessageBox QPushButton:pressed {{
        background: {VOID};
    }}
"""


def _show_settings_message(
    parent: QWidget,
    title: str,
    text: str,
    icon: QMessageBox.Icon = QMessageBox.Icon.Information,
) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setIcon(icon)
    box.setText(text)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.setStyleSheet(_S_MESSAGE_BOX)
    box.exec()


def _library_scripts() -> list[dict]:
    try:
        return PowerShellLibrary().scripts()
    except Exception as exc:
        debug_log(f"failed to load PowerShell Library scripts for settings: {exc}")
        return []


def _script_combo_label(script: dict) -> str:
    return f"{script.get('name', 'Unnamed')}  ({script.get('category', 'Custom')})"


def _find_library_script(script_id: str) -> dict | None:
    if not script_id:
        return None
    for script in _library_scripts():
        if script.get("id") == script_id:
            return script
    return None


def _populate_script_combo(combo: QComboBox, selected_id: str = "") -> None:
    combo.blockSignals(True)
    combo.clear()
    scripts = _library_scripts()
    if not scripts:
        combo.addItem("No PowerShell Library scripts available", "")
        combo.setEnabled(False)
        combo.blockSignals(False)
        return
    combo.setEnabled(True)
    for script in scripts:
        combo.addItem(_script_combo_label(script), script.get("id", ""))
    idx = combo.findData(selected_id)
    combo.setCurrentIndex(max(0, idx))
    combo.blockSignals(False)


def _current_script_id(combo: QComboBox) -> str:
    data = combo.currentData()
    return str(data or "")


def _display_target(action: dict) -> str:
    if action.get("type") == "powershell_library":
        return "Open PowerShell Library"
    if action.get("type") == "settings":
        return "Open Settings"
    return action.get("target", "")


class _ActionListWidget(QListWidget):
    drag_started = Signal()
    order_changed = Signal(list)
    drag_finished = Signal()

    _HANDLE_WIDTH = 34

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._handle_drag_active = False
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def ordered_ids(self) -> list[str]:
        return [
            str(self.item(row).data(Qt.ItemDataRole.UserRole) or "")
            for row in range(self.count())
        ]

    def _handle_rect(self, item: QListWidgetItem | None) -> QRect:
        if item is None:
            return QRect()
        rect = self.visualItemRect(item)
        return QRect(
            rect.right() - self._HANDLE_WIDTH + 1,
            rect.top(),
            self._HANDLE_WIDTH,
            rect.height(),
        )

    def _item_at_handle(self, pos) -> QListWidgetItem | None:
        item = self.itemAt(pos)
        if item and self._handle_rect(item).contains(pos):
            return item
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._item_at_handle(event.position().toPoint()):
            self._handle_drag_active = True
            self.setDragEnabled(True)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.drag_started.emit()
        else:
            self._handle_drag_active = False
            self.setDragEnabled(False)
            self.unsetCursor()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            if self._item_at_handle(event.position().toPoint()):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        if self._handle_drag_active:
            self.drag_finished.emit()
        self._handle_drag_active = False
        self.setDragEnabled(False)
        self.unsetCursor()

    def dropEvent(self, event) -> None:
        before = self.ordered_ids()
        try:
            super().dropEvent(event)
            after = self.ordered_ids()
            if before != after:
                self.order_changed.emit(after)
        finally:
            self.drag_finished.emit()
            self._handle_drag_active = False
            self.setDragEnabled(False)
            self.unsetCursor()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = painter.font()
        font.setPixelSize(16)
        font.setBold(True)
        painter.setFont(font)

        for row in range(self.count()):
            item = self.item(row)
            rect = self.visualItemRect(item)
            if not rect.isValid() or rect.bottom() < 0 or rect.top() > self.viewport().height():
                continue
            handle_rect = self._handle_rect(item)
            selected = item.isSelected()
            painter.setPen(QColor(EMBER if selected else FOG))
            painter.drawText(handle_rect, Qt.AlignmentFlag.AlignCenter, "::")


def _icon_row(field: QLineEdit) -> QWidget:
    """Wrap an icon QLineEdit with an icon picker button on the right."""
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(4)
    row.addWidget(field)

    btn = QPushButton("\U0001F42F")
    btn.setFixedSize(36, 32)
    btn.setToolTip("Choose Icon")
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {BONE};
            background: {_FIELD_BG};
            font-size: 18px;
            border: 1px solid {_SOFT_BORDER};
            border-radius: {_RADIUS}px;
            padding: 0;
            min-width: 36px;
            max-width: 36px;
            min-height: 34px;
            max-height: 34px;
        }}
        QPushButton:hover {{
            background: {CHARCOAL};
            border-color: {EMBER};
        }}
        QPushButton:pressed {{
            background: {EMBER_WASH};
            border-color: {EMBER};
        }}
        QPushButton:disabled {{
            background: {STEEL};
            color: {FOG};
            border-color: {ASH};
        }}
    """)

    def _open_picker():
        from ui.emoji_picker import EmojiPickerDialog
        dlg = EmojiPickerDialog(parent=btn.window())
        if dlg.exec():
            field.setText(dlg.selected_emoji)

    btn.clicked.connect(_open_picker)
    row.addWidget(btn)
    return w


# ── Theme preview card ────────────────────────────────────────────────────────

def _confirm_delete(parent: QWidget, title: str, message: str) -> bool:
    """Show a delete confirmation with local button styling only."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setText(message)
    box.setStyleSheet(f"""
        QMessageBox {{
            background: {VOID};
            color: {BONE};
        }}
        QMessageBox QLabel {{
            color: {BONE};
            font-size: 14px;
        }}
        QMessageBox QPushButton {{
            min-width: 82px;
            min-height: 32px;
            padding: 0 14px;
            border-radius: 3px;
            font-size: 14px;
            font-weight: 600;
        }}
        QMessageBox QPushButton#deleteConfirmButton {{
            background: {SIGNAL_RED};
            color: {VOID};
            border: 1px solid {SIGNAL_RED_PRESSED};
        }}
        QMessageBox QPushButton#deleteConfirmButton:hover {{
            background: {SIGNAL_RED_HOVER};
        }}
        QMessageBox QPushButton#cancelConfirmButton {{
            background: {CHARCOAL};
            color: {BONE};
            border: 1px solid {ASH};
        }}
        QMessageBox QPushButton#cancelConfirmButton:hover {{
            background: {STEEL};
        }}
    """)

    delete_btn = box.addButton("Delete", QMessageBox.ButtonRole.DestructiveRole)
    cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    delete_btn.setObjectName("deleteConfirmButton")
    cancel_btn.setObjectName("cancelConfirmButton")
    delete_btn.setStyleSheet(f"""
        QPushButton {{
            background: {SIGNAL_RED};
            color: {VOID};
            border: 1px solid {SIGNAL_RED_PRESSED};
            border-radius: 3px;
            min-width: 82px;
            min-height: 32px;
            padding: 0 14px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {SIGNAL_RED_HOVER}; }}
    """)
    cancel_btn.setStyleSheet(f"""
        QPushButton {{
            background: {CHARCOAL};
            color: {BONE};
            border: 1px solid {ASH};
            border-radius: 3px;
            min-width: 82px;
            min-height: 32px;
            padding: 0 14px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {STEEL}; }}
    """)
    box.setDefaultButton(cancel_btn)
    box.exec()
    return box.clickedButton() is delete_btn


class _ThemeCard(QPushButton):
    """Custom-painted glass theme card used in the Settings theme row."""

    _W = 104
    _H = 124

    def __init__(self, theme_id: str, theme_data: dict,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tid   = theme_id
        self._tdata = theme_data
        self._sel   = False
        self._frame_index = 0
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(theme_data["name"])
        self.setFlat(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def set_selected(self, sel: bool) -> None:
        if self._sel != sel:
            self._sel = sel
            self.update()

    def set_frame_index(self, frame_index: int) -> None:
        if self._frame_index != frame_index:
            self._frame_index = frame_index
            self.update()

    def _cut_corner_path(self, rect: QRectF, cut: float) -> QPainterPath:
        """Rounded rect except the top-right corner, which is chamfered — the
        app's recurring "cut steel" shape instead of a uniformly rounded card."""
        path = QPainterPath()
        r = 10.0
        path.moveTo(rect.left() + r, rect.top())
        path.lineTo(rect.right() - cut, rect.top())
        path.lineTo(rect.right(), rect.top() + cut)
        path.lineTo(rect.right(), rect.bottom() - r)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - r, rect.bottom())
        path.lineTo(rect.left() + r, rect.bottom())
        path.quadTo(rect.left(), rect.bottom(), rect.left(), rect.bottom() - r)
        path.lineTo(rect.left(), rect.top() + r)
        path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
        path.closeSubpath()
        return path

    def paintEvent(self, _event) -> None:
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        outer = QRectF(2, 3, self._W - 4, self._H - 6)
        card = self._cut_corner_path(outer, CORNER_CUT_PX * 1.5)

        p.setPen(Qt.PenStyle.NoPen)
        p.save()
        p.setClipPath(card)
        used_bg = draw_theme_card_background(p, outer, self._tid)
        p.restore()
        if not used_bg:
            bg = QLinearGradient(outer.left(), outer.top(), outer.right(), outer.bottom())
            bg.setColorAt(0.0, QColor(36, 38, 64, 232))
            bg.setColorAt(0.52, QColor(17, 20, 38, 235))
            bg.setColorAt(1.0, QColor(10, 12, 28, 238))
            p.fillPath(card, QBrush(bg))

            wash = QLinearGradient(outer.left(), outer.top(), outer.left(), outer.bottom())
            wash.setColorAt(0.0, QColor(*self._tdata["glow"]))
            wash.setColorAt(0.58, QColor(0, 0, 0, 0))
            wash.setColorAt(1.0, QColor(0, 0, 0, 35))
            p.fillPath(card, QBrush(wash))

        border = QColor(142, 129, 190, 78)
        if self._sel:
            border = QColor(EMBER)
            p.setPen(QPen(QColor(242, 118, 11, 92), 5.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(self._cut_corner_path(outer.adjusted(2, 2, -2, -2), CORNER_CUT_PX * 1.5 - 2))
        p.setPen(QPen(border, 1.5 if self._sel else 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(self._cut_corner_path(outer.adjusted(0.5, 0.5, -0.5, -0.5), CORNER_CUT_PX * 1.5))

        cx = self._W / 2.0
        cy = 45.0
        draw_energy_bubble(
            p,
            cx,
            cy,
            31.0,
            self._tid,
            selected=self._sel,
            hovered=self.underMouse(),
            rim_width=10.0,
            inner_fill=QColor(20, 22, 42, 218),
            frame_index=self._frame_index,
            animate=self._sel,
        )

        if self._sel:
            chk_cx, chk_cy, chk_r = self._W - 19.0, 20.0, 12.0
            p.setPen(QPen(QColor(242, 118, 11, 120), 4.0))
            p.setBrush(QColor(255, 247, 237, 255))
            p.drawEllipse(QPointF(chk_cx, chk_cy), chk_r, chk_r)
            p.setPen(QPen(QColor(EMBER), 2.4, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawLine(QLineF(chk_cx - 4.2, chk_cy - 0.3, chk_cx - 1.0, chk_cy + 3.2))
            p.drawLine(QLineF(chk_cx - 1.0, chk_cy + 3.2, chk_cx + 5.0, chk_cy - 4.8))

        band = QRectF(3.5, 86, self._W - 7, 34)
        band_path = QPainterPath()
        band_path.addRoundedRect(band, 9, 9)
        band_grad = QLinearGradient(band.left(), band.top(), band.left(), band.bottom())
        band_grad.setColorAt(0.0, QColor(255, 255, 255, 18 if self._sel else 9))
        band_grad.setColorAt(1.0, QColor(*self._tdata["glow"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(band_path, QBrush(band_grad))

        font = QFont()
        font.setPixelSize(12)
        font.setBold(self._sel)
        p.setFont(font)
        p.setPen(QColor(245, 242, 255) if self._sel else QColor(218, 222, 240))
        p.drawText(
            QRectF(9, 88, self._W - 18, 31),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
            self._tdata["name"],
        )
        p.end()


# ── Sub-action dialog ─────────────────────────────────────────────────────────

class _SubActionDialog(QDialog):
    """Create or edit a single sub_action dict."""

    def __init__(self, data: dict | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = data or {}
        self._build_ui()

    def _build_ui(self) -> None:
        is_edit = bool(self._data)
        self.setWindowTitle("Edit Sub Action" if is_edit else "Add Sub Action")
        self.setMinimumWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background: {VOID};
                color: {BONE};
                font-family: {BODY_FONT_FAMILY};
            }}
            QLabel  {{ color: {BONE}; background: transparent; }}
            QLineEdit, QComboBox {{
                color: {BONE}; background-color: {_FIELD_BG};
                selection-background-color: {EMBER}; selection-color: {VOID};
            }}
            QComboBox QAbstractItemView {{
                color: {BONE}; background-color: {_PANEL_BG};
                selection-background-color: {EMBER_WASH}; selection-color: {BONE};
            }}
            {_S_CHECKBOX}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(12)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        def _field(placeholder: str, value: str = "") -> QLineEdit:
            f = QLineEdit(value)
            f.setPlaceholderText(placeholder)
            f.setStyleSheet(_S_FIELD)
            return f

        self._edit_label  = _field("Display name",          self._data.get("label", ""))
        self._edit_short  = _field("1–3 chars (optional)",  self._data.get("short_label", ""))
        self._edit_icon   = _field("emoji or symbol",       self._data.get("icon", ""))

        self._combo_type = QComboBox()
        self._combo_type.addItems(_COMBO_LEAF)
        self._combo_type.setStyleSheet(_S_COMBO)
        cur_label = _TYPE_LABELS.get(self._data.get("type", "url"), "URL")
        idx = self._combo_type.findText(cur_label)
        if idx >= 0:
            self._combo_type.setCurrentIndex(idx)

        self._edit_target = _field(
            "URL, command, or form id",
            self._data.get("target", ""),
        )

        self._combo_script = QComboBox()
        self._combo_script.setStyleSheet(_S_COMBO)
        _populate_script_combo(
            self._combo_script,
            self._data.get("script_id") or self._data.get("target", ""),
        )
        self._combo_script.currentIndexChanged.connect(self._on_script_changed)

        self._warning_script = QLabel(
            "This script is marked as dangerous and will require confirmation before running."
        )
        self._warning_script.setWordWrap(True)
        self._warning_script.setStyleSheet(
            f"font-size: 12px; color: {SIGNAL_AMBER}; background: {SIGNAL_AMBER_WASH}; "
            f"border: 1px solid rgba(217, 147, 42, 0.48); border-radius: {_RADIUS}px; padding: 9px;"
        )

        self._check_enabled = QCheckBox("Enabled")
        self._check_enabled.setChecked(self._data.get("enabled", True))
        self._check_enabled.setStyleSheet(_S_CHECKBOX)

        self._lbl_target = _caption("TARGET")
        self._lbl_script = _caption("SCRIPT")
        form.addRow(_caption("LABEL"),       self._edit_label)
        form.addRow(_caption("SHORT LABEL"), self._edit_short)
        form.addRow(_caption("ICON"),        _icon_row(self._edit_icon))
        form.addRow(_caption("TYPE"),        self._combo_type)
        form.addRow(self._lbl_target,        self._edit_target)
        form.addRow(self._lbl_script,        self._combo_script)
        form.addRow("",                      self._warning_script)
        form.addRow("",                      self._check_enabled)
        root.addLayout(form)
        self._combo_type.currentTextChanged.connect(self._on_type_changed)
        self._sync_type_fields()

        root.addSpacing(6)
        root.addWidget(_divider_h())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(_S_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet(_S_BTN_PRIMARY)
        btn_ok.clicked.connect(self._on_ok)
        btn_ok.setDefault(True)
        btn_row.addWidget(btn_ok)

        root.addLayout(btn_row)

    def _on_ok(self) -> None:
        if not self._edit_label.text().strip():
            self._edit_label.setPlaceholderText("Label is required!")
            self._edit_label.setFocus()
            return
        self.accept()

    def result_data(self) -> dict:
        type_label = self._combo_type.currentText()
        type_key = _LABEL_TO_TYPE.get(type_label, type_label)
        needs_target = type_key not in _TARGETLESS_TYPES
        result = {
            "id":          self._data.get("id") or f"act_{uuid.uuid4().hex[:8]}",
            "label":       self._edit_label.text().strip(),
            "short_label": self._edit_short.text().strip(),
            "icon":        self._edit_icon.text().strip(),
            "type":        type_key,
            "target":      self._edit_target.text().strip() if needs_target else "",
            "enabled":     self._check_enabled.isChecked(),
        }
        if type_key == "powershell_library":
            result.pop("script_id", None)
        return result

    def _current_type(self) -> str:
        type_label = self._combo_type.currentText()
        return _LABEL_TO_TYPE.get(type_label, type_label)

    def _on_type_changed(self, *_args) -> None:
        self._sync_type_fields()
        if self._current_type() == "powershell_library" and not self._edit_label.text().strip():
            self._edit_label.setText("PowerShell Library")
        if self._current_type() == "settings" and not self._edit_label.text().strip():
            self._edit_label.setText("Settings")
            if not self._edit_short.text().strip():
                self._edit_short.setText("SET")

    def _on_script_changed(self, *_args) -> None:
        self._sync_type_fields()
        self._apply_selected_script_name()

    def _apply_selected_script_name(self) -> None:
        if self._edit_label.text().strip():
            return
        script = _find_library_script(_current_script_id(self._combo_script))
        if script:
            self._edit_label.setText(script.get("name", ""))
            if not self._edit_icon.text().strip():
                self._edit_icon.setText("terminal")

    def _sync_type_fields(self) -> None:
        type_key = self._current_type()
        is_library = False
        needs_target = type_key not in _TARGETLESS_TYPES
        self._lbl_target.setVisible(needs_target)
        self._edit_target.setVisible(needs_target)
        self._lbl_script.setVisible(is_library)
        self._combo_script.setVisible(is_library)
        script = _find_library_script(_current_script_id(self._combo_script)) if is_library else None
        self._warning_script.setVisible(bool(script and script.get("risk_level") == "dangerous"))


# ── Main window ───────────────────────────────────────────────────────────────

class SettingsWindow(QDialog):
    """
    Full CRUD editor for config/actions.json.

    Works on a deep-copy of the raw actions list until the user clicks Save,
    at which point changes are committed to disk via ActionsConfig.
    """

    def __init__(self, config: ActionsConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config     = config
        self._draft         = copy.deepcopy(config.get_raw_actions())
        self._ensure_action_ids(self._draft)
        self._sel_action    = -1   # currently selected first-level action index
        self._updating      = False  # guard against re-entrant signal handling
        self._reordering    = False
        self._pre_reorder_draft: list[dict] | None = None
        self._pending_theme = config.get_theme()
        self._pending_constellation = config.get_constellation()
        self._pending_constellation_color = config.get_constellation_color()
        self._theme_frame   = 0
        self._theme_timer   = QTimer(self)
        self._theme_timer.setInterval(84)
        self._theme_timer.timeout.connect(self._advance_theme_frame)
        debug_log(
            f"SettingsWindow init: config_path={self._config.path.resolve()} "
            f"raw_actions_count={len(self._draft)} selected_theme_id={self._pending_theme!r}"
        )

        self._build_ui()
        self._refresh_action_list()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle("Settings — Universal Actions Ring")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        fit_window_to_screen(self, (1180, 760), (860, 560))
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #070A0E,
                    stop:0.58 {VOID},
                    stop:1 #11100B);
                color: {BONE};
                font-family: {BODY_FONT_FAMILY};
            }}
            QLabel  {{ color: {BONE}; background: transparent; }}
            QLineEdit, QComboBox, QSpinBox {{
                color: {BONE};
                background-color: {_FIELD_BG};
                selection-background-color: {EMBER};
                selection-color: {VOID};
            }}
            QComboBox QAbstractItemView {{
                color: {BONE};
                background-color: {_PANEL_BG};
                selection-background-color: {EMBER_WASH};
                selection-color: {BONE};
            }}
            QTableWidget, QTableView {{
                color: {BONE};
                background-color: {_PANEL_BG};
                gridline-color: {_SOFT_LINE};
            }}
            QTableWidget::item, QTableView::item {{ color: {BONE}; }}
            QHeaderView::section {{
                color: {FOG};
                background-color: {CHARCOAL};
            }}
            {_S_CHECKBOX}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(_divider_h())
        root.addWidget(self._make_hotkey_row())
        root.addWidget(_divider_h())
        root.addWidget(self._make_theme_row())
        root.addWidget(_divider_h())
        root.addWidget(self._make_profile_row())
        root.addWidget(_divider_h())

        # ── content (left + right) ──
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        content_row.addWidget(self._make_left_panel())
        content_row.addWidget(_divider_v())
        content_row.addWidget(self._make_right_panel(), stretch=1)

        content_widget = QWidget()
        content_widget.setLayout(content_row)
        root.addWidget(content_widget, stretch=1)

        root.addWidget(_divider_h())
        root.addWidget(self._make_bottom_bar())
        self._restore_window_size()
        self._center_on_screen()

    def _settings_store(self) -> QSettings:
        return QSettings("Universal Actions Ring", "Universal Actions Ring")

    def _restore_window_size(self) -> None:
        saved = self._settings_store().value("settings_window/size")
        if isinstance(saved, QSize) and saved.isValid():
            fit_window_to_screen(self, saved.expandedTo(QSize(860, 560)), (860, 560))

    def _save_window_size(self) -> None:
        if self.isFullScreen() or self.isMaximized():
            return
        self._settings_store().setValue("settings_window/size", self.size())

    def _center_on_screen(self) -> None:
        center_window(self)

    def _make_header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"""
            QWidget {{
                background: rgba(11, 13, 16, 0.94);
                border-bottom: 1px solid {_SOFT_LINE};
            }}
        """)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 16, 24, 12)
        layout.setSpacing(4)

        title = QLabel("Settings")
        title.setStyleSheet(
            f"font-family: {HEADLINE_FONT_FAMILY}; font-size: 24px; "
            f"font-weight: 700; color: {BONE}; letter-spacing: 0px;"
        )
        layout.addWidget(title)

        sub = QLabel("Edit ring actions. Changes take effect after you click Save.")
        sub.setStyleSheet(f"color: {FOG}; font-size: 12px;")
        layout.addWidget(sub)
        return w

    def _make_hotkey_row(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(54)
        w.setStyleSheet(f"""
            QWidget {{
                background: {_PANEL_BG};
                border-top: 1px solid {_SOFT_LINE};
                border-bottom: 1px solid {_SOFT_LINE};
            }}
        """)
        row = QHBoxLayout(w)
        row.setContentsMargins(24, 0, 24, 0)
        row.setSpacing(12)

        lbl = QLabel("Global hotkey:")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {FOG};")
        row.addWidget(lbl)

        self._hotkey_edit = QLineEdit(self._config.get_hotkey())
        self._hotkey_edit.setFixedWidth(200)
        self._hotkey_edit.setPlaceholderText("e.g. ctrl+space")
        self._hotkey_edit.setStyleSheet(_S_FIELD)
        row.addWidget(self._hotkey_edit)

        btn_set_hotkey = QPushButton("Set Hotkey")
        btn_set_hotkey.setToolTip("Open Hotkey Picker")
        btn_set_hotkey.setStyleSheet(_S_BTN_SMALL)
        btn_set_hotkey.clicked.connect(self._open_hotkey_picker)
        row.addWidget(btn_set_hotkey)

        hint = QLabel("(takes effect immediately after Save)")
        hint.setStyleSheet(f"font-size: 11px; color: {FOG};")
        row.addWidget(hint)

        row.addStretch()

        btn_help = QPushButton("? Help Center")
        btn_help.setToolTip("Open SmartAction Help Center")
        btn_help.setStyleSheet(f"""
            QPushButton {{
                background: rgba(236, 232, 225, 0.03);
                color: {FOG};
                border: 1px solid {_SOFT_BORDER};
                border-radius: {_RADIUS}px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 600;
                min-height: 30px; max-height: 30px;
            }}
            QPushButton:hover {{
                background: {EMBER_WASH};
                color: {EMBER};
                border-color: {EMBER};
            }}
            QPushButton:pressed {{
                background: {STEEL};
            }}
            QPushButton::menu-indicator {{
                width: 10px;
                padding-right: 4px;
            }}
        """)
        btn_help.setMenu(self._make_help_menu(btn_help))
        row.addWidget(btn_help)

        self._check_autostart = QCheckBox("Start with Windows")
        self._check_autostart.setChecked(_autostart.is_enabled())
        self._check_autostart.setStyleSheet(_S_CHECKBOX + f"QCheckBox {{ font-size: 12px; color: {FOG}; }}")
        row.addWidget(self._check_autostart)

        return w

    def _make_theme_row(self) -> QWidget:
        from core.theme import THEME_ORDER, THEMES
        w = QWidget()
        w.setFixedHeight(154)
        w.setStyleSheet(f"""
            QWidget {{
                background: {_PANEL_BG_ALT};
                border-top: 1px solid {_SOFT_LINE};
                border-bottom: 1px solid {_SOFT_LINE};
            }}
        """)
        row = QHBoxLayout(w)
        row.setContentsMargins(24, 14, 24, 14)
        row.setSpacing(12)

        lbl = QLabel("Theme:")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {FOG};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row.addWidget(lbl)

        self._theme_btns: dict[str, _ThemeCard] = {}
        for tid in THEME_ORDER:
            card = _ThemeCard(tid, THEMES[tid])
            card.clicked.connect(lambda checked=False, theme_id=tid: self._select_theme(theme_id))
            self._theme_btns[tid] = card
            row.addWidget(card)

        row.addStretch()

        constellation_panel = QWidget()
        constellation_panel.setFixedWidth(160)
        constellation_layout = QVBoxLayout(constellation_panel)
        constellation_layout.setContentsMargins(0, 5, 0, 5)
        constellation_layout.setSpacing(7)

        constellation_title = QLabel("Ring constellation:")
        constellation_title.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {FOG};"
        )
        constellation_layout.addWidget(constellation_title)

        self._constellation_combo = QComboBox()
        self._constellation_combo.setStyleSheet(_S_COMBO)
        for constellation_id in CONSTELLATION_ORDER:
            self._constellation_combo.addItem(
                constellation_label(constellation_id),
                constellation_id,
            )
        constellation_index = self._constellation_combo.findData(
            self._pending_constellation
        )
        if constellation_index < 0:
            constellation_index = self._constellation_combo.findData(
                DEFAULT_CONSTELLATION
            )
        self._constellation_combo.setCurrentIndex(max(0, constellation_index))
        self._constellation_combo.currentIndexChanged.connect(
            self._on_constellation_changed
        )
        constellation_layout.addWidget(self._constellation_combo)

        color_row = QHBoxLayout()
        color_row.setContentsMargins(0, 0, 0, 0)
        color_row.setSpacing(7)
        color_label = QLabel("Line:")
        color_label.setStyleSheet(f"font-size: 11px; color: {FOG};")
        color_row.addWidget(color_label)
        self._constellation_color_btn = QPushButton()
        self._constellation_color_btn.setFixedHeight(27)
        self._constellation_color_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self._constellation_color_btn.setToolTip(
            "Choose the constellation star and line color"
        )
        self._constellation_color_btn.clicked.connect(
            self._pick_constellation_color
        )
        color_row.addWidget(self._constellation_color_btn, stretch=1)
        constellation_layout.addLayout(color_row)
        constellation_layout.addStretch()
        row.addWidget(constellation_panel)

        self._update_theme_btns()
        self._update_constellation_color_button()
        return w

    def _make_profile_row(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(58)
        w.setStyleSheet(f"""
            QWidget {{
                background: {_PANEL_BG};
                border-top: 1px solid {_SOFT_LINE};
                border-bottom: 1px solid {_SOFT_LINE};
            }}
        """)
        row = QHBoxLayout(w)
        row.setContentsMargins(24, 0, 24, 0)
        row.setSpacing(12)

        title = QLabel("Profile:")
        title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {FOG};")
        row.addWidget(title)

        hint = QLabel("Export or import SmartAction settings as JSON.")
        hint.setStyleSheet(f"font-size: 11px; color: {FOG};")
        row.addWidget(hint)
        row.addStretch()

        btn_export = QPushButton("Export Profile")
        btn_export.setToolTip("Export actions, theme, hotkey, startup settings, and PowerShell Library scripts.")
        btn_export.setStyleSheet(_S_BTN_SMALL)
        btn_export.clicked.connect(self._on_export_profile)
        row.addWidget(btn_export)

        btn_import = QPushButton("Import Profile")
        btn_import.setToolTip("Import a SmartAction profile. Current settings are backed up first. Replace mode is used.")
        btn_import.setStyleSheet(_S_BTN_SMALL)
        btn_import.clicked.connect(self._on_import_profile)
        row.addWidget(btn_import)

        return w

    def _make_help_menu(self, parent: QWidget) -> QMenu:
        menu = QMenu(parent)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {CHARCOAL};
                color: {BONE};
                border: 1px solid {ASH};
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }}
            QMenu::item {{
                color: {BONE};
                background: transparent;
                padding: 7px 26px 7px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                color: {EMBER};
                background: {EMBER_WASH};
            }}
            QMenu::separator {{
                height: 1px;
                background: {ASH};
                margin: 6px 4px;
            }}
        """)

        quick_start = QAction("Quick Start / 快速教學", menu)
        quick_start.triggered.connect(self._open_quick_start)
        menu.addAction(quick_start)

        full_docs = QAction("Full Documentation / 完整文件", menu)
        full_docs.triggered.connect(lambda: self._open_external_url(DOCUMENTATION_URL, "Full Documentation"))
        menu.addAction(full_docs)

        repo = QAction("Open GitHub Repository", menu)
        repo.triggered.connect(lambda: self._open_external_url(GITHUB_REPO_URL, "GitHub Repository"))
        menu.addAction(repo)

        issue = QAction("Report Issue", menu)
        issue.triggered.connect(lambda: self._open_external_url(GITHUB_ISSUES_URL, "GitHub Issues"))
        menu.addAction(issue)

        menu.addSeparator()

        about = QAction("About SmartAction", menu)
        about.triggered.connect(lambda: self._open_external_url(ABOUT_URL, "About SmartAction"))
        menu.addAction(about)

        return menu

    def _open_quick_start(self) -> None:
        from ui.help_modal import HelpModal
        dlg = HelpModal(
            self,
            title="SmartAction Quick Start",
            markdown_path=DOCS_DIR / "quick-start.md",
        )
        dlg.exec()

    def _open_external_url(self, url: str, label: str) -> None:
        message = f"Help Center opening {label}: {url}"
        print(message)
        debug_log(message)
        try:
            opened = webbrowser.open(url)
        except Exception as exc:
            _show_settings_message(
                self,
                label,
                f"Failed to open browser:\n{exc}\n\nURL:\n{url}",
                QMessageBox.Icon.Warning,
            )
            return
        if not opened:
            _show_settings_message(
                self,
                label,
                f"Could not open the browser automatically.\n\nURL:\n{url}",
                QMessageBox.Icon.Warning,
            )

    def _open_hotkey_picker(self) -> None:
        from ui.hotkey_picker import HotkeyPickerDialog, normalize_hotkey

        current = self._hotkey_edit.text().strip() or self._config.get_hotkey()
        reserved_hotkeys = self._smartaction_reserved_hotkeys()
        reserved_hotkeys.discard(normalize_hotkey(current))

        dlg = HotkeyPickerDialog(
            current_hotkey=current,
            reserved_hotkeys=reserved_hotkeys,
            parent=self,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        self._hotkey_edit.setText(dlg.selected_hotkey)
        self._config.set_hotkey(dlg.selected_hotkey)

    def _smartaction_reserved_hotkeys(self) -> set[str]:
        # Central hook for duplicate checks as more SmartAction-level hotkeys are added.
        # Current config only has one global hotkey, but this also supports future
        # optional "hotkeys" / "shortcuts" maps without changing the picker.
        from ui.hotkey_picker import normalize_hotkey

        reserved: set[str] = set()
        raw = getattr(self._config, "_data", {})
        for section_name in ("hotkeys", "shortcuts"):
            section = raw.get(section_name, {}) if isinstance(raw, dict) else {}
            if isinstance(section, dict):
                for value in section.values():
                    if isinstance(value, str) and value.strip():
                        reserved.add(normalize_hotkey(value))
        return reserved

    def _on_export_profile(self) -> None:
        self._commit_current()
        filename = default_export_filename()
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Export SmartAction Profile",
            filename,
            "JSON Files (*.json)",
        )
        if not path:
            return
        try:
            export_profile(
                Path(path),
                self._config,
                actions_override=copy.deepcopy(self._draft),
                hotkey_override=self._hotkey_edit.text().strip() or self._config.get_hotkey(),
                theme_override=self._pending_theme,
                constellation_override=self._pending_constellation,
                constellation_color_override=self._pending_constellation_color,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Export Profile", f"Profile export failed:\n{exc}")
            return
        QMessageBox.information(self, "Export Profile", "Profile exported successfully.")

    def _on_import_profile(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Import SmartAction Profile",
            "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        reply = QMessageBox.question(
            self,
            "Import Profile",
            "即將匯入 SmartAction Profile。\n"
            "目前設定會先自動備份。\n\n"
            "Import mode: Replace\n"
            "Merge mode is planned for a later version.\n\n"
            "請確認是否繼續。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = import_profile(Path(path), self._config, mode="replace")
        except ProfileError as exc:
            QMessageBox.warning(self, "Import Profile", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "Import Profile", f"Profile import failed:\n{exc}")
            return

        self._config.reload()
        self._draft = copy.deepcopy(self._config.get_raw_actions())
        self._pending_theme = self._config.get_theme()
        self._pending_constellation = self._config.get_constellation()
        self._pending_constellation_color = self._config.get_constellation_color()
        self._hotkey_edit.setText(self._config.get_hotkey())
        self._sel_action = -1
        self._refresh_action_list()
        self._update_theme_btns()
        constellation_index = self._constellation_combo.findData(
            self._pending_constellation
        )
        self._constellation_combo.setCurrentIndex(max(0, constellation_index))
        self._update_constellation_color_button()
        self._right_stack.setCurrentIndex(0)

        message = (
            "Profile imported successfully.\n"
            f"Backup created:\n{result.backup_path}\n\n"
            "Please close Settings with Save, use tray Reload Config, or restart SmartAction."
        )
        if result.local_path_warning:
            message += (
                "\n\nSome imported actions contain local file paths. "
                "They may not work on this computer until the paths are updated."
            )
        QMessageBox.information(self, "Import Profile", message)

    def _select_theme(self, theme_id: str) -> None:
        self._pending_theme = theme_id
        self._update_theme_btns()

    def _on_constellation_changed(self, index: int) -> None:
        constellation_id = self._constellation_combo.itemData(index)
        self._pending_constellation = str(
            constellation_id or DEFAULT_CONSTELLATION
        )

    def _pick_constellation_color(self) -> None:
        selected = QColorDialog.getColor(
            QColor(self._pending_constellation_color),
            self,
            "Constellation line color",
        )
        if not selected.isValid():
            return
        self._pending_constellation_color = selected.name(
            QColor.NameFormat.HexRgb
        ).upper()
        self._update_constellation_color_button()

    def _update_constellation_color_button(self) -> None:
        button = getattr(self, "_constellation_color_btn", None)
        if button is None:
            return
        color = QColor(
            self._pending_constellation_color
            or DEFAULT_CONSTELLATION_COLOR
        )
        text_color = "#101216" if color.lightness() >= 145 else "#F5F2EB"
        color_name = color.name(QColor.NameFormat.HexRgb).upper()
        button.setText(color_name)
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color_name};
                color: {text_color};
                border: 1px solid rgba(255, 255, 255, 0.34);
                border-radius: 5px;
                padding: 0 5px;
                font-size: 10px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                border: 2px solid {BONE};
            }}
        """)

    def _update_theme_btns(self) -> None:
        for tid, card in self._theme_btns.items():
            card.set_selected(tid == self._pending_theme)

    def _advance_theme_frame(self) -> None:
        frame_count = max(1, theme_frame_count(self._pending_theme))
        self._theme_frame = (self._theme_frame + 1) % frame_count
        card = getattr(self, "_theme_btns", {}).get(self._pending_theme)
        if card is not None:
            card.set_frame_index(self._theme_frame)

    def _start_theme_timer(self) -> None:
        selected_theme = self._pending_theme
        has_animation = theme_frame_count(selected_theme) > 1
        debug_log(
            f"settings theme timer: selected_theme={selected_theme!r} "
            f"has_animated_assets={has_animation} "
            f"visible={self.isVisible()}"
        )
        if has_animation and self.isVisible():
            self._theme_timer.start()

    def _stop_theme_timer(self) -> None:
        self._theme_timer.stop()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._start_theme_timer()

    def hideEvent(self, event) -> None:
        self._save_window_size()
        self._stop_theme_timer()
        prune_theme_asset_cache({self._pending_theme, self._config.get_theme()})
        super().hideEvent(event)

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _make_left_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(252)
        w.setStyleSheet(f"""
            QWidget {{
                background: rgba(17, 21, 29, 0.98);
                border-right: 1px solid {_SOFT_LINE};
            }}
        """)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # section header
        hdr = QWidget()
        hdr.setFixedHeight(40)
        hdr.setStyleSheet(f"""
            QWidget {{
                background: {CHARCOAL};
                border-bottom: 1px solid {_SOFT_LINE};
            }}
        """)
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(16, 0, 12, 0)
        lbl = QLabel("Actions")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {BONE};")
        hdr_row.addWidget(lbl)
        hdr_row.addStretch()
        self._order_status = QLabel("")
        self._order_status.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {SIGNAL_GREEN};")
        hdr_row.addWidget(self._order_status)
        layout.addWidget(hdr)

        # list
        self._action_list = _ActionListWidget()
        self._action_list.setFrameShape(QFrame.Shape.NoFrame)
        self._action_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
                padding: 8px 8px 8px 8px;
            }}
            QListWidget::item {{
                padding: 10px 42px 10px 12px;
                color: {BONE};
                font-size: 14px;
                min-height: {ROW_HEIGHT}px;
                border: 1px solid transparent;
                border-radius: {_RADIUS}px;
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background: {EMBER_WASH};
                color: {BONE};
                font-weight: 600;
                border: 1px solid {_NEON_EDGE};
                border-left: 3px solid {EMBER};
            }}
            QListWidget::item:hover:!selected {{
                background: {STEEL};
                border-color: {_SOFT_BORDER};
            }}
        """)
        self._action_list.currentRowChanged.connect(self._on_action_selected)
        self._action_list.drag_started.connect(self._on_action_drag_started)
        self._action_list.order_changed.connect(self._on_action_reordered)
        self._action_list.drag_finished.connect(self._on_action_drag_finished)
        layout.addWidget(self._action_list, stretch=1)

        # toolbar
        tb = QWidget()
        tb.setFixedHeight(48)
        tb.setStyleSheet(f"background: {CHARCOAL}; border-top: 1px solid {_SOFT_LINE};")
        tb_row = QHBoxLayout(tb)
        tb_row.setContentsMargins(12, 0, 12, 0)
        tb_row.setSpacing(8)

        self._btn_add_action = QPushButton("+ Add")
        self._btn_add_action.setStyleSheet(_S_BTN_SMALL)
        self._btn_add_action.clicked.connect(self._on_add_action)
        tb_row.addWidget(self._btn_add_action)

        tb_row.addStretch()

        self._btn_del_action = QPushButton("Delete")
        self._btn_del_action.setStyleSheet(_S_BTN_DANGER)
        self._btn_del_action.setEnabled(False)
        self._btn_del_action.clicked.connect(self._on_delete_action)
        tb_row.addWidget(self._btn_del_action)

        layout.addWidget(tb)
        return w

    # ── Right panel (stacked) ─────────────────────────────────────────────────

    def _make_right_panel(self) -> QStackedWidget:
        self._right_stack = QStackedWidget()
        self._right_stack.addWidget(self._make_empty_hint())  # index 0
        self._right_stack.addWidget(self._make_editor())      # index 1
        return self._right_stack

    def _make_empty_hint(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        lbl = QLabel("Select an action to edit")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {FOG}; font-size: 14px;")
        layout.addStretch()
        layout.addWidget(lbl)
        layout.addStretch()
        return w

    def _make_editor(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("""
            QWidget {
                background: rgba(11, 13, 16, 0.72);
            }
        """)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(32, 24, 32, 20)
        outer.setSpacing(0)

        # title
        self._editor_title = QLabel("Edit Action")
        self._editor_title.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {BONE}; margin-bottom: 16px;"
        )
        outer.addWidget(self._editor_title)

        # form fields
        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(18)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        def _field(placeholder: str) -> QLineEdit:
            f = QLineEdit()
            f.setPlaceholderText(placeholder)
            f.setStyleSheet(_S_FIELD)
            f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return f

        self._edit_label  = _field("Display name")
        self._edit_short  = _field("1–3 chars (optional)")
        self._edit_icon   = _field("emoji or symbol")

        self._combo_type = QComboBox()
        self._combo_type.addItems(_COMBO_ALL)
        self._combo_type.setStyleSheet(_S_COMBO)
        self._combo_type.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._lbl_target  = _caption("TARGET")
        self._edit_target = _field("URL, command, or form id")

        self._lbl_script = _caption("SCRIPT")
        self._combo_script = QComboBox()
        self._combo_script.setStyleSheet(_S_COMBO)
        self._combo_script.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _populate_script_combo(self._combo_script)

        self._warning_script = QLabel(
            "This script is marked as dangerous and will require confirmation before running."
        )
        self._warning_script.setWordWrap(True)
        self._warning_script.setStyleSheet(
            f"font-size: 12px; color: {SIGNAL_AMBER}; background: {SIGNAL_AMBER_WASH}; "
            f"border: 1px solid rgba(217, 147, 42, 0.48); border-radius: {_RADIUS}px; padding: 9px;"
        )

        self._check_enabled = QCheckBox("Enabled")
        self._check_enabled.setStyleSheet(_S_CHECKBOX)

        form.addRow(_caption("LABEL"),       self._edit_label)
        form.addRow(_caption("SHORT LABEL"), self._edit_short)
        form.addRow(_caption("ICON"),        _icon_row(self._edit_icon))
        form.addRow(_caption("TYPE"),        self._combo_type)
        form.addRow(self._lbl_target,        self._edit_target)
        form.addRow(self._lbl_script,        self._combo_script)
        form.addRow("",                      self._warning_script)
        form.addRow("",                      self._check_enabled)

        outer.addLayout(form)
        outer.addSpacing(22)
        outer.addWidget(_divider_h())
        outer.addSpacing(16)

        # sub-actions section
        sub_title = QLabel("Sub Actions")
        sub_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {BONE};")
        outer.addWidget(sub_title)
        outer.addSpacing(10)

        self._sub_table = QTableWidget()
        self._sub_table.setColumnCount(4)
        self._sub_table.setHorizontalHeaderLabels(["Label", "Type", "Target", "On"])
        self._sub_table.setFixedHeight(176)
        self._sub_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._sub_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._sub_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._sub_table.setAlternatingRowColors(True)
        self._sub_table.verticalHeader().setVisible(False)
        self._sub_table.setStyleSheet(_S_TABLE)

        hdr = self._sub_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(1, 80)
        hdr.resizeSection(3, 36)

        self._sub_table.itemSelectionChanged.connect(self._on_sub_selected)
        self._sub_table.doubleClicked.connect(self._on_edit_sub)
        outer.addWidget(self._sub_table)
        outer.addSpacing(10)

        # sub-action buttons
        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)

        self._btn_add_sub = QPushButton("+ Add")
        self._btn_add_sub.setStyleSheet(_S_BTN_SMALL)
        self._btn_add_sub.clicked.connect(self._on_add_sub)

        self._btn_edit_sub = QPushButton("Edit")
        self._btn_edit_sub.setStyleSheet(_S_BTN_SMALL)
        self._btn_edit_sub.setEnabled(False)
        self._btn_edit_sub.clicked.connect(self._on_edit_sub)

        self._btn_del_sub = QPushButton("Delete")
        self._btn_del_sub.setStyleSheet(_S_BTN_DANGER)
        self._btn_del_sub.setEnabled(False)
        self._btn_del_sub.clicked.connect(self._on_delete_sub)

        sub_row.addWidget(self._btn_add_sub)
        sub_row.addWidget(self._btn_edit_sub)
        sub_row.addStretch()
        sub_row.addWidget(self._btn_del_sub)
        outer.addLayout(sub_row)

        outer.addStretch()

        # wire field signals AFTER all widgets are created
        self._edit_label.textChanged.connect(self._on_field_changed)
        self._edit_short.textChanged.connect(self._on_field_changed)
        self._edit_icon.textChanged.connect(self._on_field_changed)
        self._combo_type.currentTextChanged.connect(self._on_type_changed)
        self._edit_target.textChanged.connect(self._on_field_changed)
        self._combo_script.currentIndexChanged.connect(self._on_script_changed)
        self._check_enabled.stateChanged.connect(self._on_field_changed)

        return w

    def _make_bottom_bar(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(64)
        w.setStyleSheet(f"""
            QWidget {{
                background: rgba(11, 13, 16, 0.96);
                border-top: 1px solid {_SOFT_LINE};
            }}
        """)
        row = QHBoxLayout(w)
        row.setContentsMargins(24, 0, 24, 0)
        row.setSpacing(12)
        row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(_S_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_cancel)

        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(_S_BTN_PRIMARY)
        btn_save.clicked.connect(self._on_save)
        btn_save.setDefault(True)
        row.addWidget(btn_save)

        return w

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _ensure_action_ids(self, actions: list[dict]) -> bool:
        changed = False
        for action in actions:
            if not action.get("id"):
                action["id"] = f"act_{uuid.uuid4().hex[:8]}"
                changed = True
            sub_actions = action.get("sub_actions", [])
            if isinstance(sub_actions, list):
                changed = self._ensure_action_ids(sub_actions) or changed
        return changed

    def _refresh_action_list(self) -> None:
        """Rebuild the left list from self._draft (preserves selection)."""
        self._ensure_action_ids(self._draft)
        self._action_list.blockSignals(True)
        self._action_list.clear()
        for action in self._draft:
            enabled = action.get("enabled", True)
            status  = "ON " if enabled else "OFF"
            item    = QListWidgetItem(f"{status}  {action.get('label', 'Unnamed')}")
            item.setData(Qt.ItemDataRole.UserRole, action.get("id", ""))
            item.setToolTip("Drag the handle to reorder. Click the row to edit.")
            if not enabled:
                item.setForeground(QColor(FOG))
            self._action_list.addItem(item)
        self._action_list.blockSignals(False)

        # restore selection within bounds
        if 0 <= self._sel_action < self._action_list.count():
            self._action_list.blockSignals(True)
            self._action_list.setCurrentRow(self._sel_action)
            self._action_list.blockSignals(False)

    def _show_order_status(self, text: str, error: bool = False) -> None:
        self._order_status.setText(text)
        self._order_status.setStyleSheet(
            "font-size: 11px; font-weight: 600; "
            f"color: {SIGNAL_RED if error else SIGNAL_GREEN};"
        )
        QTimer.singleShot(1800, lambda: self._order_status.setText(""))

    def _load_action_into_editor(self, action: dict) -> None:
        """Populate form fields from an action dict without triggering commits."""
        self._updating = True
        self._editor_title.setText(f"Edit: {action.get('label', 'Unnamed')}")

        self._edit_label.setText(action.get("label", ""))
        self._edit_short.setText(action.get("short_label", ""))
        self._edit_icon.setText(action.get("icon", ""))

        type_label = _TYPE_LABELS.get(action.get("type", "folder"), "Folder")
        idx = self._combo_type.findText(type_label)
        self._combo_type.setCurrentIndex(max(0, idx))

        _populate_script_combo(
            self._combo_script,
            action.get("script_id") or action.get("target", ""),
        )
        self._edit_target.setText(action.get("target", ""))
        self._check_enabled.setChecked(action.get("enabled", True))

        self._sync_action_type_fields(action.get("type", "folder"))

        self._refresh_sub_table(action.get("sub_actions", []))
        self._updating = False

    def _refresh_sub_table(self, subs: list[dict]) -> None:
        """Rebuild the sub-actions table from a list of dicts."""
        self._sub_table.setRowCount(0)
        for sub in subs:
            row = self._sub_table.rowCount()
            self._sub_table.insertRow(row)
            self._sub_table.setItem(row, 0, QTableWidgetItem(sub.get("label", "")))

            type_val   = sub.get("type", "")
            type_label = _TYPE_LABELS.get(type_val, type_val)
            self._sub_table.setItem(row, 1, QTableWidgetItem(type_label))
            self._sub_table.setItem(row, 2, QTableWidgetItem(_display_target(sub)))

            on_item = QTableWidgetItem("On" if sub.get("enabled", True) else "Off")
            on_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sub_table.setItem(row, 3, on_item)

        # Reset sub-action button states
        self._btn_edit_sub.setEnabled(False)
        self._btn_del_sub.setEnabled(False)

    def _commit_current(self) -> None:
        """Write current editor fields back to self._draft[_sel_action]."""
        if self._sel_action < 0 or self._updating:
            return
        action = self._draft[self._sel_action]
        action["label"]       = self._edit_label.text().strip() or "Unnamed"
        action["short_label"] = self._edit_short.text().strip()
        action["icon"]        = self._edit_icon.text().strip()
        type_label            = self._combo_type.currentText()
        type_key              = _LABEL_TO_TYPE.get(type_label, type_label)
        action["type"]        = type_key
        if type_key == "powershell_library":
            action.pop("script_id", None)
            action["target"] = ""
        elif type_key in _TARGETLESS_TYPES:
            action.pop("script_id", None)
            action["target"] = ""
        else:
            action.pop("script_id", None)
            action["target"] = self._edit_target.text().strip()
        action["enabled"]     = self._check_enabled.isChecked()

    def _current_subs(self) -> list[dict]:
        if self._sel_action < 0:
            return []
        return self._draft[self._sel_action].setdefault("sub_actions", [])

    # ── Slots: action list ────────────────────────────────────────────────────

    def _on_action_selected(self, idx: int) -> None:
        if self._reordering:
            return
        self._commit_current()      # save fields → self._draft[old sel_action]
        self._sel_action = idx      # update BEFORE refresh so list highlights new item
        self._refresh_action_list() # rebuild dots/labels, restore visual selection

        if not (0 <= idx < len(self._draft)):
            self._right_stack.setCurrentIndex(0)
            self._btn_del_action.setEnabled(False)
            return

        self._right_stack.setCurrentIndex(1)
        self._btn_del_action.setEnabled(True)
        self._load_action_into_editor(self._draft[idx])

    def _on_action_drag_started(self) -> None:
        if self._reordering:
            return
        self._commit_current()
        self._pre_reorder_draft = copy.deepcopy(self._draft)
        self._reordering = True

    def _on_action_reordered(self, ordered_ids: list[str]) -> None:
        if not ordered_ids:
            self._on_action_drag_finished()
            return

        selected_id = ""
        current = self._action_list.currentItem()
        if current is not None:
            selected_id = str(current.data(Qt.ItemDataRole.UserRole) or "")

        try:
            by_id = {str(action.get("id", "")): action for action in self._draft}
            if len(by_id) != len(self._draft) or any(action_id not in by_id for action_id in ordered_ids):
                raise ValueError("Action order contains missing or duplicate ids.")

            self._draft = [by_id[action_id] for action_id in ordered_ids]
            self._config.save_raw_actions(self._draft)

            if selected_id:
                self._sel_action = next(
                    (idx for idx, action in enumerate(self._draft) if action.get("id") == selected_id),
                    -1,
                )
            self._reordering = False
            self._pre_reorder_draft = None
            self._refresh_action_list()
            if 0 <= self._sel_action < len(self._draft):
                self._right_stack.setCurrentIndex(1)
                self._load_action_into_editor(self._draft[self._sel_action])
            self._show_order_status("Order saved")
        except Exception as exc:
            if self._pre_reorder_draft is not None:
                self._draft = self._pre_reorder_draft
            self._reordering = False
            self._pre_reorder_draft = None
            self._refresh_action_list()
            self._show_order_status("Order restored", error=True)
            _show_settings_message(
                self,
                "Reorder Actions",
                f"Could not save the new order. The previous order was restored.\n\n{exc}",
                QMessageBox.Icon.Warning,
            )

    def _on_action_drag_finished(self) -> None:
        self._reordering = False
        self._pre_reorder_draft = None

    # ── Slots: form fields ────────────────────────────────────────────────────

    def _on_field_changed(self, *_) -> None:
        if self._updating:
            return
        self._commit_current()
        # Live-update the list item label/dot
        if 0 <= self._sel_action < self._action_list.count():
            action  = self._draft[self._sel_action]
            enabled = action.get("enabled", True)
            status  = "ON " if enabled else "OFF"
            item    = self._action_list.item(self._sel_action)
            if item:
                item.setText(f"{status}  {action.get('label', 'Unnamed')}")
                item.setForeground(QColor(BONE if enabled else FOG))

    def _on_type_changed(self, type_label: str) -> None:
        if self._updating:
            return
        type_key = _LABEL_TO_TYPE.get(type_label, type_label)
        self._sync_action_type_fields(type_key)
        if type_key == "powershell_library":
            if not self._edit_label.text().strip() or self._edit_label.text().strip() == "New Action":
                self._edit_label.setText("PowerShell Library")
        if type_key == "settings":
            if not self._edit_label.text().strip() or self._edit_label.text().strip() == "New Action":
                self._edit_label.setText("Settings")
            if not self._edit_short.text().strip():
                self._edit_short.setText("SET")
        self._on_field_changed()

    def _on_script_changed(self, *_args) -> None:
        if self._updating:
            return
        self._sync_action_type_fields(_LABEL_TO_TYPE.get(self._combo_type.currentText(), self._combo_type.currentText()))
        self._apply_selected_library_script_name()
        self._on_field_changed()

    def _apply_selected_library_script_name(self) -> None:
        if self._edit_label.text().strip() and self._edit_label.text().strip() != "New Action":
            return
        script = _find_library_script(_current_script_id(self._combo_script))
        if script:
            self._edit_label.setText(script.get("name", ""))
            if not self._edit_icon.text().strip():
                self._edit_icon.setText("terminal")

    def _sync_action_type_fields(self, type_key: str) -> None:
        is_folder = type_key == "folder"
        is_library = False
        needs_target = not is_folder and not is_library and type_key not in _TARGETLESS_TYPES
        self._lbl_target.setVisible(needs_target)
        self._edit_target.setVisible(needs_target)
        self._lbl_script.setVisible(is_library)
        self._combo_script.setVisible(is_library)
        script = _find_library_script(_current_script_id(self._combo_script)) if is_library else None
        self._warning_script.setVisible(bool(script and script.get("risk_level") == "dangerous"))

    # ── Slots: sub-actions ────────────────────────────────────────────────────

    def _on_sub_selected(self) -> None:
        row = self._sub_table.currentRow()
        has = row >= 0
        self._btn_edit_sub.setEnabled(has)
        self._btn_del_sub.setEnabled(has)

    def _on_add_sub(self) -> None:
        dlg = _SubActionDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._current_subs().append(dlg.result_data())
        subs = self._current_subs()
        self._refresh_sub_table(subs)
        self._sub_table.setCurrentCell(len(subs) - 1, 0)

    def _on_edit_sub(self, *_) -> None:
        row  = self._sub_table.currentRow()
        subs = self._current_subs()
        if not (0 <= row < len(subs)):
            return
        dlg = _SubActionDialog(data=subs[row], parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        subs[row] = dlg.result_data()
        self._refresh_sub_table(subs)
        self._sub_table.setCurrentCell(row, 0)

    def _on_delete_sub(self) -> None:
        row  = self._sub_table.currentRow()
        subs = self._current_subs()
        if not (0 <= row < len(subs)):
            return
        label = subs[row].get("label", "this sub-action")
        if not _confirm_delete(self, "Delete Sub Action", f'Delete "{label}"?'):
            return
        del subs[row]
        self._refresh_sub_table(subs)

    # ── Slots: action CRUD ────────────────────────────────────────────────────

    def _on_add_action(self) -> None:
        self._commit_current()
        new_action: dict = {
            "id":          f"act_{uuid.uuid4().hex[:8]}",
            "label":       "New Action",
            "short_label": "",
            "icon":        "",
            "type":        "folder",
            "target":      "",
            "enabled":     True,
            "sub_actions": [],
        }
        self._draft.append(new_action)
        self._sel_action = len(self._draft) - 1
        self._refresh_action_list()   # selects new row via blocked setCurrentRow
        self._right_stack.setCurrentIndex(1)
        self._btn_del_action.setEnabled(True)
        self._load_action_into_editor(new_action)
        self._edit_label.setFocus()
        self._edit_label.selectAll()

    def _on_delete_action(self) -> None:
        idx = self._sel_action
        if idx < 0:
            return
        label = self._draft[idx].get("label", "this action")
        if not _confirm_delete(
            self,
            "Delete Action",
            f'Delete "{label}" and all its sub-actions?',
        ):
            return
        del self._draft[idx]
        self._sel_action = min(idx, len(self._draft) - 1)
        self._refresh_action_list()   # selects adjusted row via blocked setCurrentRow
        if self._sel_action >= 0:
            self._right_stack.setCurrentIndex(1)
            self._load_action_into_editor(self._draft[self._sel_action])
        else:
            self._right_stack.setCurrentIndex(0)
            self._btn_del_action.setEnabled(False)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        self._commit_current()

        # Hotkey
        hotkey = self._hotkey_edit.text().strip()
        if hotkey:
            self._config.set_hotkey(hotkey)

        # Autostart
        _autostart.set_enabled(self._check_autostart.isChecked())

        # Theme
        self._config.set_theme(self._pending_theme)
        self._config.set_constellation(self._pending_constellation)
        self._config.set_constellation_color(
            self._pending_constellation_color
        )

        # Actions
        self._config.save_raw_actions(self._draft)
        self.accept()
