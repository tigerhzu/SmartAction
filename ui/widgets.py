"""Shared Qt widget factories used across Settings pages and form dialogs."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLineEdit

from ui.style_tokens import ASH, BONE, CHARCOAL, EMBER, FOG, STEEL, VOID


CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {BONE};
        font-size: 14px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {ASH};
        border-radius: 3px;
        background: {CHARCOAL};
    }}
    QCheckBox::indicator:hover {{
        border-color: {EMBER};
        background: {STEEL};
    }}
    QCheckBox::indicator:checked {{
        border-color: {EMBER};
        background: {EMBER};
    }}
    QCheckBox:disabled {{
        color: {FOG};
    }}
"""


def _input_style(bg: str) -> str:
    return f"""
        QLineEdit {{
            color: {BONE};
            border: 1px solid {ASH};
            border-radius: 3px;
            padding: 0 8px;
            font-size: 14px;
            min-height: 34px;
            background: {bg};
            selection-background-color: {EMBER};
            selection-color: {VOID};
        }}
        QLineEdit:hover {{ border-color: {STEEL}; }}
        QLineEdit:focus {{ border-color: {EMBER}; }}
        QLineEdit:disabled {{ background: {STEEL}; color: {FOG}; }}
    """


def make_input_field(
    placeholder: str = "",
    *,
    password: bool = False,
    bg: str = CHARCOAL,
) -> QLineEdit:
    """Return a styled 34 px QLineEdit."""
    w = QLineEdit()
    w.setFixedHeight(34)
    w.setStyleSheet(_input_style(bg))
    if placeholder:
        w.setPlaceholderText(placeholder)
    if password:
        w.setEchoMode(QLineEdit.EchoMode.Password)
    return w


def make_h_separator(color: str = ASH) -> QFrame:
    """Return a 1 px horizontal rule."""
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {color}; border: none;")
    return f
