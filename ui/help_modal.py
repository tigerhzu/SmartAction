"""
Modal help/wiki dialog for Settings.

The visible content is loaded from docs/help.md so the wiki text can be
edited without changing this UI component.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.paths import DOCS_DIR
from ui.window_utils import fit_window_to_screen, handle_fullscreen_shortcut
from ui.style_tokens import ASH, BONE, CHARCOAL, EMBER, EMBER_HOVER, EMBER_PRESSED, FOG, STEEL, VOID


def _help_content_path(markdown_path: Path | None = None) -> Path:
    return markdown_path or DOCS_DIR / "help.md"


def load_help_markdown(markdown_path: Path | None = None) -> str:
    path = _help_content_path(markdown_path)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# SmartAction Help\n\nHelp content is missing: `{path.name}`"


class HelpModal(QDialog):
    """Scrollable modal wiki dialog."""

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Universal Actions Ring Wiki",
        markdown_path: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._markdown_path = markdown_path
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._title)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        fit_window_to_screen(self, (760, 680), (620, 460), width_ratio=0.86, height_ratio=0.86)
        self.setStyleSheet(f"""
            QDialog {{
                background: {VOID};
                color: {BONE};
            }}
            QTextBrowser {{
                background: {CHARCOAL};
                color: {BONE};
                border: 1px solid {ASH};
                border-radius: 3px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.45;
                selection-background-color: {EMBER};
                selection-color: {VOID};
            }}
            QTextBrowser:focus {{
                border-color: {EMBER};
            }}
            QPushButton {{
                background: {EMBER};
                color: {VOID};
                border: none;
                border-radius: 3px;
                min-width: 88px;
                min-height: 36px;
                padding: 0 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {EMBER_HOVER};
            }}
            QPushButton:pressed {{
                background: {EMBER_PRESSED};
            }}
            QPushButton:disabled {{
                background: {STEEL};
                color: {FOG};
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

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 16)
        root.setSpacing(12)

        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(False)
        help_path = _help_content_path(self._markdown_path)
        viewer.document().setBaseUrl(QUrl.fromLocalFile(str(help_path.parent.resolve()) + "/"))
        viewer.setMarkdown(load_help_markdown(self._markdown_path))
        root.addWidget(viewer, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        root.addLayout(buttons)

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)
