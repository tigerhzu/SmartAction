from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.environment_check import CheckResult, format_environment_check
from ui.window_utils import fit_window_to_screen, handle_fullscreen_shortcut
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_PRESSED,
    FOG,
    STEEL,
    VOID,
)


_BTN_PRIMARY = f"""
    QPushButton {{
        background: {EMBER}; color: {VOID}; border: none;
        border-radius: 3px; padding: 0 16px;
        min-height: 36px; font-size: 14px; font-weight: 600;
    }}
    QPushButton:hover {{ background: {EMBER_HOVER}; }}
    QPushButton:pressed {{ background: {EMBER_PRESSED}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; }}
"""

_BTN_SECONDARY = f"""
    QPushButton {{
        background: transparent; color: {BONE};
        border: 1px solid {ASH}; border-radius: 3px;
        padding: 0 16px; min-height: 36px; font-size: 14px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""


class EnvironmentCheckResultDialog(QDialog):
    def __init__(self, result: CheckResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result = result
        self._text = format_environment_check(result)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Environment Check")
        fit_window_to_screen(self, (760, 620), (620, 460), width_ratio=0.86, height_ratio=0.84)
        self.setStyleSheet(
            f"QDialog {{ background: {VOID}; color: {BONE}; }}"
            f"QLabel {{ color: {BONE}; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(12)

        title = QLabel("SmartAction Environment Check")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {BONE};")
        root.addWidget(title)

        subtitle = QLabel(f"Time: {self._result.get('time', 'Unknown')}")
        subtitle.setStyleSheet(f"font-size: 12px; color: {FOG};")
        root.addWidget(subtitle)

        self._output = QPlainTextEdit(self._text)
        self._output.setReadOnly(True)
        self._output.setStyleSheet(f"""
            QPlainTextEdit {{
                color: {BONE};
                background: {CHARCOAL};
                border: 1px solid {ASH};
                border-radius: 3px;
                padding: 10px;
                font-family: Consolas, "Cascadia Mono", monospace;
                font-size: 13px;
                selection-background-color: {EMBER};
                selection-color: {VOID};
            }}
            QPlainTextEdit:focus {{
                border-color: {EMBER};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {ASH};
                border-radius: 5px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {EMBER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        root.addWidget(self._output, stretch=1)

        row = QHBoxLayout()
        row.addStretch()

        copy = QPushButton("Copy Result")
        copy.setStyleSheet(_BTN_PRIMARY)
        copy.clicked.connect(self._copy_result)
        row.addWidget(copy)

        close = QPushButton("Close")
        close.setStyleSheet(_BTN_SECONDARY)
        close.clicked.connect(self.accept)
        row.addWidget(close)

        root.addLayout(row)

    def _copy_result(self) -> None:
        QApplication.clipboard().setText(self._text)

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)
