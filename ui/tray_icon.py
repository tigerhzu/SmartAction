from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtCore import Qt, Signal

from core.actions_config import (
    UI_THEME_CLASSIC,
    UI_THEME_CUTE,
    UI_THEME_IDS,
    UI_THEME_WOVEN,
)
from ui.style_tokens import ASH, BONE, CHARCOAL, EMBER, EMBER_HOVER, FOG, NEON_CYAN, STEEL, VOID


_MENU_STYLE = f"""
    QMenu {{
        background: {VOID};
        color: {BONE};
        border: 1px solid {ASH};
        padding: 6px;
        font-size: 13px;
    }}
    QMenu::item {{
        background: transparent;
        padding: 7px 30px 7px 12px;
        border-radius: 3px;
    }}
    QMenu::item:selected {{
        background: {STEEL};
        color: {EMBER_HOVER};
    }}
    QMenu::item:disabled {{
        color: {FOG};
    }}
    QMenu::separator {{
        height: 1px;
        background: {ASH};
        margin: 6px 8px;
    }}
"""

_ABOUT_STYLE = f"""
    QMessageBox {{
        background: {VOID};
        color: {BONE};
        font-size: 13px;
    }}
    QMessageBox QLabel {{
        color: {BONE};
    }}
    QMessageBox QPushButton {{
        background: {EMBER};
        color: {VOID};
        border: 1px solid {EMBER};
        border-radius: 3px;
        min-width: 86px;
        min-height: 30px;
        padding: 0 14px;
        font-weight: 700;
    }}
    QMessageBox QPushButton:hover {{
        background: {EMBER_HOVER};
        border-color: {EMBER_HOVER};
    }}
    QMessageBox QPushButton:pressed {{
        background: {CHARCOAL};
        color: {BONE};
        border-color: {EMBER};
    }}
"""


def _make_icon(ui_theme: str = UI_THEME_CLASSIC) -> QIcon:
    """Draw a crisp tray logo matching the active global interface."""
    theme = (
        str(ui_theme).strip().lower()
        if str(ui_theme).strip().lower() in UI_THEME_IDS
        else UI_THEME_CLASSIC
    )
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(2.0, 2.0)

    if theme == UI_THEME_CUTE:
        _draw_cute_icon(painter)
    elif theme == UI_THEME_WOVEN:
        _draw_woven_icon(painter)
    else:
        _draw_classic_icon(painter)
    painter.end()
    return QIcon(pixmap)


def _draw_classic_icon(painter: QPainter) -> None:
    glow = QRadialGradient(16, 16, 15)
    glow.setColorAt(0.0, QColor(EMBER_HOVER))
    glow.setColorAt(0.58, QColor(EMBER))
    glow.setColorAt(1.0, QColor(EMBER).darker(170))
    painter.setBrush(QBrush(glow))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)

    painter.setBrush(QColor(CHARCOAL))
    painter.setPen(QPen(QColor(ASH), 1))
    painter.drawEllipse(6, 6, 20, 20)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(NEON_CYAN), 1))
    painter.drawArc(8, 8, 16, 16, 30 * 16, 115 * 16)
    painter.setBrush(QColor(EMBER_HOVER))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(14, 14, 4, 4)


def _draw_cute_icon(painter: QPainter) -> None:
    shadow = QRadialGradient(16, 18, 15)
    shadow.setColorAt(0.0, QColor(178, 76, 121, 88))
    shadow.setColorAt(1.0, QColor(178, 76, 121, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(shadow))
    painter.drawEllipse(1, 3, 30, 29)

    jelly = QLinearGradient(6, 4, 26, 29)
    jelly.setColorAt(0.0, QColor(255, 250, 246))
    jelly.setColorAt(0.25, QColor(255, 185, 214))
    jelly.setColorAt(0.68, QColor(237, 104, 167))
    jelly.setColorAt(1.0, QColor(164, 61, 130))
    painter.setBrush(QBrush(jelly))
    painter.setPen(QPen(QColor(255, 239, 246, 214), 0.9))
    painter.drawEllipse(3, 3, 26, 26)

    highlight = QPainterPath()
    highlight.moveTo(8.2, 10.3)
    highlight.cubicTo(11.0, 5.7, 17.7, 4.7, 22.0, 7.1)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(
        QPen(
            QColor(255, 255, 255, 205),
            1.6,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
    )
    painter.drawPath(highlight)

    heart = QPainterPath()
    heart.moveTo(16.0, 23.5)
    heart.cubicTo(13.6, 20.5, 8.8, 17.0, 8.8, 12.9)
    heart.cubicTo(8.8, 8.8, 13.7, 8.0, 16.0, 11.1)
    heart.cubicTo(18.3, 8.0, 23.2, 8.8, 23.2, 12.9)
    heart.cubicTo(23.2, 17.0, 18.4, 20.5, 16.0, 23.5)
    heart.closeSubpath()
    painter.setPen(QPen(QColor(255, 255, 255, 230), 0.65))
    painter.setBrush(QColor(255, 248, 250, 242))
    painter.drawPath(heart)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(153, 224, 246, 238))
    painter.drawEllipse(24.2, 21.7, 3.8, 3.8)
    painter.setBrush(QColor(255, 255, 255, 238))
    painter.drawEllipse(25.0, 22.2, 1.1, 1.1)


def _draw_woven_icon(painter: QPainter) -> None:
    glow = QRadialGradient(16, 16, 15)
    glow.setColorAt(0.0, QColor(236, 253, 255))
    glow.setColorAt(0.48, QColor(118, 216, 226))
    glow.setColorAt(1.0, QColor(32, 72, 104))
    painter.setPen(QPen(QColor(221, 251, 255, 204), 0.8))
    painter.setBrush(QBrush(glow))
    painter.drawEllipse(3, 3, 26, 26)

    colors = (
        QColor(255, 255, 255, 232),
        QColor(56, 126, 165, 238),
        QColor(217, 249, 251, 232),
    )
    for index, y in enumerate((11.0, 16.0, 21.0)):
        strand = QPainterPath()
        strand.moveTo(7.0, y)
        strand.cubicTo(
            11.0,
            y - 5.2,
            21.0,
            y + 5.2,
            25.0,
            y,
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(
                colors[index],
                1.65,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawPath(strand)

    painter.setPen(Qt.PenStyle.NoPen)
    for x, y, color in (
        (8.0, 11.0, QColor(255, 255, 255)),
        (16.0, 16.0, QColor(32, 103, 144)),
        (24.0, 21.0, QColor(235, 255, 255)),
    ):
        painter.setBrush(color)
        painter.drawEllipse(x - 1.15, y - 1.15, 2.3, 2.3)


class TrayIcon(QSystemTrayIcon):
    settings_requested       = Signal()
    powershell_library_requested = Signal()
    client_workspace_requested = Signal()
    reload_requested         = Signal()
    restart_hotkey_requested = Signal()

    def __init__(
        self,
        app: QApplication,
        ui_theme: str = UI_THEME_CLASSIC,
    ):
        super().__init__()
        self._app = app
        self._ui_theme = UI_THEME_CLASSIC
        self.set_ui_theme(ui_theme)
        self.setToolTip("Universal Actions Ring")
        self._build_menu()
        self.activated.connect(self._on_activated)

    def set_ui_theme(self, ui_theme: str) -> None:
        theme = (
            str(ui_theme).strip().lower()
            if str(ui_theme).strip().lower() in UI_THEME_IDS
            else UI_THEME_CLASSIC
        )
        self._ui_theme = theme
        icon = _make_icon(theme)
        self.setIcon(icon)
        self._app.setWindowIcon(icon)

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet(_MENU_STYLE)

        menu.addAction("Open Settings",  self.settings_requested.emit)
        menu.addAction("PowerShell Library", self.powershell_library_requested.emit)
        menu.addAction("Client Workspace", self.client_workspace_requested.emit)
        menu.addSeparator()
        menu.addAction("Reload Config",  self.reload_requested.emit)
        menu.addAction("Restart Hotkey", self.restart_hotkey_requested.emit)
        menu.addSeparator()
        menu.addAction("About SmartAction", self._show_about)
        menu.addSeparator()
        menu.addAction("Exit",           self._app.quit)

        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def _show_about(self) -> None:
        box = QMessageBox()
        box.setWindowTitle("About SmartAction")
        box.setIconPixmap(self.icon().pixmap(48, 48))
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(
            "<b>SmartAction</b> v0.1.0<br><br>"
            "A tray-first productivity launcher for Windows.<br>"
            "Trigger: global hotkey, tray menu, or configured Ring actions.<br><br>"
            "<span style='color:#9AA0AA'>Built with Python + PySide6.</span>"
        )
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(_ABOUT_STYLE)
        box.exec()
