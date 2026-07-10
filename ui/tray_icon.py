from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtCore import Qt, Signal

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


def _make_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    settings_requested       = Signal()
    ai_agent_requested       = Signal()
    powershell_library_requested = Signal()
    client_workspace_requested = Signal()
    reload_requested         = Signal()
    restart_hotkey_requested = Signal()

    def __init__(self, app: QApplication, ai_agent_enabled: bool = False):
        super().__init__()
        self._app = app
        self._ai_agent_enabled = ai_agent_enabled
        self.setIcon(_make_icon())
        self.setToolTip("Universal Actions Ring")
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet(_MENU_STYLE)

        menu.addAction("Open Settings",  self.settings_requested.emit)
        if self._ai_agent_enabled:
            menu.addAction("AI Agent (Preview)", self.ai_agent_requested.emit)
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
        box.setIconPixmap(_make_icon().pixmap(48, 48))
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
