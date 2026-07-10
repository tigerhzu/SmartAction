"""Product-style icon picker used by the Settings ICON field."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.paths import BUNDLE_DIR, DATA_DIR
from ui.window_utils import fit_window_to_screen
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_WASH,
    FOG,
    SIGNAL_AMBER,
    SIGNAL_AMBER_WASH,
    STEEL,
    VOID,
)


ICON_DATA_DIR = DATA_DIR / "icons"
DATABASE_PATH = ICON_DATA_DIR / "emoji_database.json"
BUNDLED_DATABASE_PATH = BUNDLE_DIR / "data" / "icons" / "emoji_database.json"
STATE_PATH = ICON_DATA_DIR / "icon_picker_state.json"
MAX_RECENT = 32


@dataclass(frozen=True)
class IconItem:
    icon: str
    name: str
    category: str
    keywords: tuple[str, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def search_text(self) -> str:
        return " ".join(
            (self.icon, self.name, self.category, *self.keywords, *self.aliases)
        ).casefold()


def _u(codepoint: str) -> str:
    return "".join(chr(int(part, 16)) for part in codepoint.split())


def _item(icon_hex: str, name: str, category: str, *keywords: str) -> IconItem:
    return IconItem(icon=_u(icon_hex), name=name, category=category, keywords=tuple(keywords))


FALLBACK_CATALOG: list[IconItem] = [
    _item("1F42F", "Tiger Face", "Animals & Nature", "tiger", "cat", "brand", "smartaction"),
    _item("1F405", "Tiger", "Animals & Nature", "tiger", "animal", "cat", "wild"),
    _item("1F916", "Robot", "AI", "ai", "bot", "assistant", "automation"),
    _item("1F9E0", "Brain", "AI", "ai", "smart", "model", "thinking"),
    _item("2728", "Sparkles", "AI", "magic", "clean", "auto", "enhance"),
    _item("1F4A1", "Idea", "AI", "tip", "light", "insight"),
    _item("1F310", "Globe", "Browser / Web", "web", "browser", "internet", "network"),
    _item("1F4C1", "Folder", "Files & Storage", "folder", "files", "directory"),
    _item("1F4C2", "Open Folder", "Files & Storage", "folder", "open", "files"),
    _item("1F5C2 FE0F", "Card Index Dividers", "Files & Storage", "folder", "index", "tabs"),
    _item("1F4E1", "Antenna", "Network", "network", "wifi", "signal"),
    _item("1F6DC", "Wireless", "Network", "network", "wifi", "wireless"),
    _item("1F512", "Lock", "Security", "security", "secure", "protect"),
    _item("1F6E1 FE0F", "Shield", "Security", "security", "firewall", "protect"),
    _item("2601 FE0F", "Cloud", "Cloud", "cloud", "azure", "m365"),
    _item("1F4BB", "Laptop", "Development", "terminal", "code", "dev"),
    _item("2328 FE0F", "Keyboard", "Development", "terminal", "input", "keys"),
    _item("2699 FE0F", "Settings", "System", "terminal", "gear", "config"),
    _item("2709 FE0F", "Envelope", "Communication", "mail", "email", "message"),
    _item("1F4E7", "Email", "Communication", "mail", "email", "message"),
    _item("1F4F1", "Mobile Phone", "Devices", "phone", "mobile", "device"),
    _item("260E FE0F", "Telephone", "Communication", "phone", "call", "support"),
]

CATEGORY_ORDER = [
    "Recent",
    "Favorites",
    "Smileys & Emotion",
    "People & Body",
    "Animals & Nature",
    "Food & Drink",
    "Travel & Places",
    "Activities",
    "Objects",
    "Symbols",
    "Flags",
    "AI",
    "Apps",
    "Development",
    "System",
    "Files & Storage",
    "Network",
    "Security",
    "Cloud",
    "Media",
    "Productivity",
    "Work / Office",
    "Devices",
    "Browser / Web",
    "Communication",
    "Tiger / Brand",
]


def _load_catalog() -> list[IconItem]:
    for path in (DATABASE_PATH, BUNDLED_DATABASE_PATH):
        try:
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    raw_items = json.load(f)
                items: list[IconItem] = []
                for raw in raw_items:
                    if not isinstance(raw, dict):
                        continue
                    icon = str(raw.get("icon", "")).strip()
                    name = str(raw.get("name", "")).strip()
                    category = str(raw.get("category", "")).strip()
                    if not icon or not name or not category:
                        continue
                    keywords = tuple(str(x).casefold() for x in raw.get("keywords", []) if str(x).strip())
                    aliases = tuple(str(x).casefold() for x in raw.get("aliases", []) if str(x).strip())
                    items.append(IconItem(icon, name, category, keywords, aliases))
                if items:
                    return items
        except (OSError, json.JSONDecodeError):
            pass
    return FALLBACK_CATALOG


CATALOG: list[IconItem] = _load_catalog()
CATEGORY_RANK = {category: index for index, category in enumerate(CATEGORY_ORDER)}


def _search_score(item: IconItem, terms: list[str]) -> int:
    name = item.name.casefold()
    category = item.category.casefold()
    keywords = set(item.keywords)
    aliases = set(item.aliases)
    score = 0
    for term in terms:
        if term == name:
            score += 120
        if term in keywords or term in aliases:
            score += 90
        if term == category:
            score += 70
        if name.startswith(term):
            score += 45
        if any(part.startswith(term) for part in name.split()):
            score += 25
        if term in name:
            score += 10
        if term in item.icon:
            score += 5
    if item.category in CATEGORY_RANK:
        score += max(0, 30 - CATEGORY_RANK[item.category])
    return score


def _load_state() -> dict[str, list[str]]:
    try:
        if STATE_PATH.exists():
            with open(STATE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            return {
                "recent": list(data.get("recent", [])),
                "favorites": list(data.get("favorites", [])),
            }
    except (OSError, json.JSONDecodeError):
        pass
    return {"recent": [], "favorites": []}


def _save_state(state: dict[str, list[str]]) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


_S_DIALOG = f"""
    QDialog {{ background: {VOID}; color: {BONE}; }}
    QLabel {{ color: {BONE}; }}
    QLineEdit {{
        color: {BONE};
        background: {CHARCOAL};
        border: 1px solid {ASH};
        border-radius: 3px;
        min-height: 36px;
        padding: 0 12px;
        font-size: 14px;
        selection-background-color: {EMBER};
        selection-color: {VOID};
    }}
    QLineEdit:focus {{ border-color: {EMBER}; }}
    QLineEdit:hover {{ border-color: {STEEL}; }}
    QListWidget {{
        background: {CHARCOAL};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        min-height: 30px;
        padding: 5px 9px;
        border-radius: 3px;
    }}
    QListWidget::item:hover {{
        background: {STEEL};
        color: {EMBER};
    }}
    QListWidget::item:selected {{
        background: {EMBER_WASH};
        color: {EMBER};
        font-weight: 600;
    }}
    QListWidget::item:focus {{
        border: 1px solid {EMBER};
    }}
    QScrollArea {{
        background: transparent;
        border: 1px solid {ASH};
        border-radius: 3px;
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
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

_S_ICON_CELL = f"""
    QPushButton {{
        background: {CHARCOAL};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        font-size: 25px;
        padding: 0;
    }}
    QPushButton:hover {{
        background: {STEEL};
        border-color: {EMBER};
    }}
    QPushButton:pressed {{
        background: {VOID};
        border-color: {EMBER};
    }}
    QPushButton:disabled {{
        background: {STEEL};
        color: {FOG};
        border-color: {ASH};
    }}
    QPushButton[selected="true"] {{
        background: {EMBER_WASH};
        border: 2px solid {EMBER};
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
        font-weight: 600;
    }}
    QPushButton:hover {{ background: {EMBER_HOVER}; }}
    QPushButton:pressed {{ background: {EMBER}; }}
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

_S_STAR = f"""
    QPushButton {{
        background: {CHARCOAL};
        color: {FOG};
        border: 1px solid {ASH};
        border-radius: 3px;
        min-height: 36px;
        padding: 0 12px;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: {SIGNAL_AMBER_WASH}; color: {SIGNAL_AMBER}; border-color: {SIGNAL_AMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
    QPushButton[favorite="true"] {{ background: rgba(217, 147, 42, 0.22); color: {SIGNAL_AMBER}; border-color: {SIGNAL_AMBER}; }}
"""


class IconCellButton(QPushButton):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event) -> None:
        self.doubleClicked.emit()
        event.accept()


class EmojiPickerDialog(QDialog):
    """Choose an emoji or symbolic icon for a SmartAction action."""

    COLS = 8
    BTN_SIZE = 52

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.selected_emoji: str = ""
        self._state = _load_state()
        self._selected: IconItem | None = None
        self._visible_items: list[IconItem] = []
        self._buttons: list[IconCellButton] = []
        self._current_category = "Recent"
        self._build_ui()
        self._load_category("Recent")

    def _build_ui(self) -> None:
        self.setWindowTitle("Choose Icon")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        fit_window_to_screen(self, (820, 620), (680, 500), width_ratio=0.86, height_ratio=0.84)
        self.setStyleSheet(_S_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)

        header = QVBoxLayout()
        title = QLabel("Choose Icon")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {BONE};")
        subtitle = QLabel("Pick an emoji or icon for this action.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {FOG};")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search icons, keywords, categories, synonyms...")
        self._search.textChanged.connect(self._on_search)
        root.addWidget(self._search)

        body = QHBoxLayout()
        body.setSpacing(14)

        self._categories = QListWidget()
        self._categories.setFixedWidth(190)
        for category in CATEGORY_ORDER:
            QListWidgetItem(category, self._categories)
        self._categories.currentTextChanged.connect(self._load_category)
        body.addWidget(self._categories)

        grid_panel = QWidget()
        grid_layout = QVBoxLayout(grid_panel)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        self._section_title = QLabel("Recent")
        self._section_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {BONE};")
        grid_layout.addWidget(self._section_title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setHorizontalSpacing(9)
        self._grid.setVerticalSpacing(9)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_container)
        grid_layout.addWidget(self._scroll, stretch=1)

        self._empty_label = QLabel("")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {FOG}; font-size: 13px; padding: 24px;")
        self._empty_label.hide()
        grid_layout.addWidget(self._empty_label)

        body.addWidget(grid_panel, stretch=1)

        preview = QWidget()
        preview.setFixedWidth(190)
        preview.setStyleSheet(f"""
            QWidget {{
                background: {CHARCOAL};
                border: 1px solid {ASH};
                border-radius: 3px;
            }}
        """)
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(10)

        preview_title = QLabel("Preview")
        preview_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {FOG}; border: none;")
        self._preview_icon = QLabel("-")
        self._preview_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_icon.setStyleSheet(
            f"font-size: 50px; color: {BONE}; background: {VOID}; "
            f"border: 1px solid {ASH}; border-radius: 3px; min-height: 92px;"
        )
        self._preview_name = QLabel("Name: None")
        self._preview_name.setWordWrap(True)
        self._preview_name.setStyleSheet(f"font-size: 13px; color: {BONE}; border: none;")
        self._preview_category = QLabel("Category: -")
        self._preview_category.setWordWrap(True)
        self._preview_category.setStyleSheet(f"font-size: 12px; color: {FOG}; border: none;")
        self._favorite_btn = QPushButton("* Favorite")
        self._favorite_btn.setStyleSheet(_S_STAR)
        self._favorite_btn.clicked.connect(self._toggle_favorite)
        self._favorite_btn.setEnabled(False)

        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self._preview_icon)
        preview_layout.addWidget(self._preview_name)
        preview_layout.addWidget(self._preview_category)
        preview_layout.addWidget(self._favorite_btn)
        preview_layout.addStretch()
        body.addWidget(preview)

        root.addLayout(body, stretch=1)

        footer = QHBoxLayout()
        hint = QLabel("Double-click an icon or press Enter to apply.")
        hint.setStyleSheet(f"font-size: 12px; color: {FOG};")
        footer.addWidget(hint)
        footer.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(_S_SECONDARY)
        clear_btn.clicked.connect(self._clear)
        footer.addWidget(clear_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_S_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        self._select_btn = QPushButton("Select")
        self._select_btn.setStyleSheet(_S_PRIMARY)
        self._select_btn.clicked.connect(self._apply_selected)
        self._select_btn.setEnabled(False)
        footer.addWidget(self._select_btn)

        root.addLayout(footer)
        self._categories.setCurrentRow(0)
        self._search.setFocus()

    def _items_for_category(self, category: str) -> list[IconItem]:
        if category == "Recent":
            return self._items_from_icons(self._state.get("recent", []))
        if category == "Favorites":
            return self._items_from_icons(self._state.get("favorites", []))
        return [item for item in CATALOG if item.category == category]

    def _items_from_icons(self, icons: list[str]) -> list[IconItem]:
        by_icon: dict[str, IconItem] = {}
        for item in CATALOG:
            by_icon.setdefault(item.icon, item)
        return [by_icon[icon] for icon in icons if icon in by_icon]

    def _load_category(self, category: str) -> None:
        if not category:
            return
        self._current_category = category
        self._search.blockSignals(True)
        self._search.clear()
        self._search.blockSignals(False)
        self._section_title.setText(category)
        self._render_items(self._items_for_category(category))

    def _on_search(self, text: str) -> None:
        query = text.strip().casefold()
        if not query:
            self._render_items(self._items_for_category(self._current_category))
            return
        terms = query.split()
        results = [item for item in CATALOG if all(term in item.search_text for term in terms)]
        results.sort(key=lambda item: (-_search_score(item, terms), item.category, item.name))
        self._section_title.setText(f"Search results for \"{text.strip()}\"")
        self._render_items(results)

    def _render_items(self, items: list[IconItem]) -> None:
        self._clear_grid()
        self._visible_items = items
        self._buttons = []
        self._selected = None
        self._update_preview()

        if not items:
            self._scroll.hide()
            if self._current_category == "Recent":
                self._empty_label.setText("No recent icons yet.")
            elif self._current_category == "Favorites":
                self._empty_label.setText("No favorite icons yet.")
            else:
                self._empty_label.setText("No matching icons found.")
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._scroll.show()
        for idx, item in enumerate(items):
            btn = IconCellButton(item.icon)
            btn.setFixedSize(self.BTN_SIZE, self.BTN_SIZE)
            btn.setToolTip(f"{item.name} - {item.category}")
            btn.setStyleSheet(_S_ICON_CELL)
            btn.setProperty("selected", "false")
            btn.clicked.connect(lambda _checked=False, index=idx: self._select_index(index))
            btn.doubleClicked.connect(self._apply_selected)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._grid.addWidget(btn, idx // self.COLS, idx % self.COLS)
            self._buttons.append(btn)

    def _clear_grid(self) -> None:
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _select_index(self, index: int) -> None:
        if not (0 <= index < len(self._visible_items)):
            return
        self._selected = self._visible_items[index]
        for idx, btn in enumerate(self._buttons):
            btn.setProperty("selected", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._update_preview()

    def _selected_index(self) -> int:
        if self._selected is None:
            return -1
        try:
            return self._visible_items.index(self._selected)
        except ValueError:
            return -1

    def _move_selection(self, delta: int) -> None:
        if not self._visible_items:
            return
        current = self._selected_index()
        next_index = 0 if current < 0 else max(0, min(current + delta, len(self._visible_items) - 1))
        self._select_index(next_index)

    def _update_preview(self) -> None:
        item = self._selected
        if item is None:
            self._preview_icon.setText("-")
            self._preview_name.setText("Name: None")
            self._preview_category.setText("Category: -")
            self._favorite_btn.setEnabled(False)
            self._favorite_btn.setText("* Favorite")
            self._favorite_btn.setProperty("favorite", "false")
        else:
            self._preview_icon.setText(item.icon)
            self._preview_name.setText(f"Name: {item.name}")
            self._preview_category.setText(f"Category: {item.category}")
            is_favorite = item.icon in self._state.get("favorites", [])
            self._favorite_btn.setEnabled(True)
            self._favorite_btn.setText("* Favorite" if is_favorite else "+ Favorite")
            self._favorite_btn.setProperty("favorite", "true" if is_favorite else "false")
        self._favorite_btn.style().unpolish(self._favorite_btn)
        self._favorite_btn.style().polish(self._favorite_btn)
        self._select_btn.setEnabled(item is not None)

    def _toggle_favorite(self) -> None:
        if self._selected is None:
            return
        favorites = self._state.setdefault("favorites", [])
        icon = self._selected.icon
        if icon in favorites:
            favorites.remove(icon)
        else:
            favorites.insert(0, icon)
        _save_state(self._state)
        self._update_preview()
        if self._current_category == "Favorites" and not self._search.text().strip():
            self._render_items(self._items_for_category("Favorites"))

    def _remember_recent(self, item: IconItem) -> None:
        recent = self._state.setdefault("recent", [])
        if item.icon in recent:
            recent.remove(item.icon)
        recent.insert(0, item.icon)
        del recent[MAX_RECENT:]
        _save_state(self._state)

    def _apply_selected(self) -> None:
        if self._selected is None:
            return
        self.selected_emoji = self._selected.icon
        self._remember_recent(self._selected)
        self.accept()

    def _clear(self) -> None:
        self.selected_emoji = ""
        self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._apply_selected()
            return
        if key == Qt.Key.Key_Left:
            self._move_selection(-1)
            return
        if key == Qt.Key.Key_Right:
            self._move_selection(1)
            return
        if key == Qt.Key.Key_Up:
            self._move_selection(-self.COLS)
            return
        if key == Qt.Key.Key_Down:
            self._move_selection(self.COLS)
            return
        super().keyPressEvent(event)
