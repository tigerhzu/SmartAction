from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.window_utils import fit_window_to_screen
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_WASH,
    FOG,
    SIGNAL_RED,
    STEEL,
    VOID,
)


MODIFIERS = ["Ctrl", "Alt", "Shift", "Win"]
MAIN_KEYS = (
    [chr(code) for code in range(ord("A"), ord("Z") + 1)]
    + [str(n) for n in range(10)]
    + [f"F{n}" for n in range(1, 13)]
    + ["Space", "Enter", "Esc", "Tab", "Backspace"]
)

DANGEROUS_HOTKEYS = {
    "ctrl+c",
    "ctrl+v",
    "ctrl+x",
    "ctrl+s",
    "ctrl+w",
    "ctrl+t",
    "alt+tab",
    "win+l",
    "win+d",
    "win+r",
    "ctrl+alt+del",
}

# Hook for future SmartAction internal shortcuts. Keep empty unless another
# in-app feature gets its own configurable global hotkey.
SMARTACTION_RESERVED: set[str] = set()


def normalize_hotkey(combo: str) -> str:
    aliases = {
        "control": "ctrl",
        "ctrl": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "win": "win",
        "windows": "win",
        "cmd": "win",
        "space": "space",
        "return": "enter",
        "enter": "enter",
        "escape": "esc",
        "esc": "esc",
        "tab": "tab",
        "backspace": "backspace",
        "del": "del",
        "delete": "del",
    }
    raw_parts = combo.replace(" ", "").split("+")
    parts = [p.strip().casefold() for p in raw_parts if p.strip()]
    normalized = [aliases.get(part, part) for part in parts]
    order = {"ctrl": 0, "alt": 1, "shift": 2, "win": 3}
    mods = sorted([p for p in normalized if p in order], key=lambda p: order[p])
    keys = [p for p in normalized if p not in order]
    return "+".join(mods + keys[:1])


def display_hotkey(combo: str) -> str:
    labels = {
        "ctrl": "Ctrl",
        "alt": "Alt",
        "shift": "Shift",
        "win": "Win",
        "space": "Space",
        "enter": "Enter",
        "esc": "Esc",
        "tab": "Tab",
        "backspace": "Backspace",
        "del": "Del",
    }
    parts = normalize_hotkey(combo).split("+") if combo else []
    display_parts = []
    for part in parts:
        if not part:
            continue
        if part.startswith("f") and part[1:].isdigit():
            display_parts.append(part.upper())
        else:
            display_parts.append(labels.get(part, part.upper() if len(part) == 1 else part))
    return " + ".join(display_parts)


def build_hotkey(modifiers: set[str], key: str) -> str:
    order = ["Ctrl", "Alt", "Shift", "Win"]
    parts = [mod for mod in order if mod in modifiers]
    if key:
        parts.append(key)
    return "+".join(part.lower() for part in parts)


_S_DIALOG = f"""
    QDialog {{ background: {VOID}; color: {BONE}; }}
    QLabel {{ color: {BONE}; }}
    QScrollArea {{
        background: transparent;
        border: 1px solid {ASH};
        border-radius: 3px;
    }}
    QScrollArea QWidget {{ background: {CHARCOAL}; }}
    QPushButton {{
        color: {BONE};
        background: {CHARCOAL};
        border: 1px solid {ASH};
        border-radius: 3px;
        min-height: 36px;
        padding: 0 12px;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background: {STEEL};
        color: {EMBER};
        border-color: {EMBER};
    }}
    QPushButton:pressed {{
        background: {VOID};
        color: {EMBER};
        border-color: {EMBER};
    }}
    QPushButton[selected="true"] {{
        background: {EMBER_WASH};
        color: {EMBER};
        border: 2px solid {EMBER};
        font-weight: 700;
    }}
    QPushButton:disabled {{
        background: {STEEL};
        color: {FOG};
        border-color: {ASH};
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
"""

_S_PRIMARY = f"""
    QPushButton {{
        background: {EMBER};
        color: {VOID};
        border: none;
        border-radius: 3px;
        min-height: 36px;
        padding: 0 18px;
        font-size: 14px;
        font-weight: 700;
    }}
    QPushButton:hover {{ background: {EMBER_HOVER}; color: {VOID}; }}
    QPushButton:pressed {{ background: {EMBER}; color: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; }}
"""

_S_SECONDARY = f"""
    QPushButton {{
        background: transparent;
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        min-height: 36px;
        padding: 0 14px;
        font-size: 14px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""


class HotkeyPickerDialog(QDialog):
    def __init__(
        self,
        current_hotkey: str = "",
        reserved_hotkeys: set[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.selected_hotkey = normalize_hotkey(current_hotkey)
        self._reserved = {
            normalize_hotkey(v)
            for v in ((reserved_hotkeys or set()) | SMARTACTION_RESERVED)
            if v
        }
        self._modifiers: set[str] = set()
        self._main_key = ""
        self._modifier_buttons: dict[str, QPushButton] = {}
        self._key_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self._load_current(self.selected_hotkey)
        self._refresh()

    def _build_ui(self) -> None:
        self.setWindowTitle("Set Hotkey")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        fit_window_to_screen(self, (740, 600), (620, 500), width_ratio=0.82, height_ratio=0.84)
        self.setStyleSheet(_S_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)

        title = QLabel("Hotkey Picker")
        title.setStyleSheet(f"font-size: 21px; font-weight: 800; color: {BONE};")
        root.addWidget(title)

        subtitle = QLabel("Click modifier keys and one main key. No keyboard capture is used.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {FOG};")
        root.addWidget(subtitle)

        root.addWidget(self._caption("Modifiers"))
        mod_row = QHBoxLayout()
        mod_row.setSpacing(8)
        for mod in MODIFIERS:
            btn = QPushButton(mod)
            btn.clicked.connect(lambda _checked=False, value=mod: self._toggle_modifier(value))
            self._modifier_buttons[mod] = btn
            mod_row.addWidget(btn)
        mod_row.addStretch()
        root.addLayout(mod_row)

        root.addWidget(self._caption("Main key"))
        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        grid_host = QWidget()
        key_grid = QGridLayout(grid_host)
        key_grid.setContentsMargins(12, 12, 12, 12)
        key_grid.setHorizontalSpacing(7)
        key_grid.setVerticalSpacing(7)
        for idx, key in enumerate(MAIN_KEYS):
            btn = QPushButton(key)
            btn.setMinimumWidth(54)
            btn.clicked.connect(lambda _checked=False, value=key: self._select_key(value))
            self._key_buttons[key] = btn
            key_grid.addWidget(btn, idx // 10, idx % 10)
        scroller.setWidget(grid_host)
        root.addWidget(scroller, 1)

        self._preview = QLabel("")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {EMBER}; "
            f"background: {EMBER_WASH}; border: 1px solid {EMBER}; "
            f"border-radius: 3px; padding: 12px;"
        )
        root.addWidget(self._preview)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setStyleSheet(f"font-size: 12px; color: {SIGNAL_RED}; min-height: 20px;")
        root.addWidget(self._status)

        footer = QHBoxLayout()
        footer.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(_S_SECONDARY)
        clear_btn.clicked.connect(self._clear)
        footer.addWidget(clear_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_S_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet(_S_PRIMARY)
        self._apply_btn.clicked.connect(self._apply)
        footer.addWidget(self._apply_btn)

        root.addLayout(footer)

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {FOG};")
        return label

    def _load_current(self, combo: str) -> None:
        parts = normalize_hotkey(combo).split("+") if combo else []
        for part in parts:
            label = display_hotkey(part)
            if label in MODIFIERS:
                self._modifiers.add(label)
            elif part:
                self._main_key = display_hotkey(part)

    def _toggle_modifier(self, modifier: str) -> None:
        if modifier in self._modifiers:
            self._modifiers.remove(modifier)
        else:
            self._modifiers.add(modifier)
        self._refresh()

    def _select_key(self, key: str) -> None:
        self._main_key = key
        self._refresh()

    def _clear(self) -> None:
        self._modifiers.clear()
        self._main_key = ""
        self._refresh()

    def _combo(self) -> str:
        return build_hotkey(self._modifiers, self._main_key)

    def _validation_error(self) -> str:
        combo = normalize_hotkey(self._combo())
        if not self._modifiers:
            return "Please choose at least one modifier key."
        if not self._main_key:
            return "Please choose one main key."
        if combo in DANGEROUS_HOTKEYS:
            return "This is a common system shortcut and is not recommended."
        if combo in self._reserved:
            return "This hotkey is already used by another SmartAction feature."
        return ""

    def _refresh(self) -> None:
        for mod, btn in self._modifier_buttons.items():
            btn.setProperty("selected", "true" if mod in self._modifiers else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        for key, btn in self._key_buttons.items():
            btn.setProperty("selected", "true" if key == self._main_key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        combo = self._combo()
        self._preview.setText(display_hotkey(combo) if combo else "No hotkey selected")
        error = self._validation_error()
        self._status.setText(error)
        self._apply_btn.setEnabled(not error)

    def _apply(self) -> None:
        error = self._validation_error()
        if error:
            self._status.setText(error)
            return
        self.selected_hotkey = normalize_hotkey(self._combo())
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._apply_btn.isEnabled():
                self._apply()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
