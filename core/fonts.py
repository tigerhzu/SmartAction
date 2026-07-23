"""
Bundled application fonts.

Fonts are shipped under assets/fonts/ (picked up by PyInstaller's existing
assets/ collection in smartaction.spec — no spec changes needed) and must be
registered with QFontDatabase once, before any widget is constructed, so the
family is available regardless of what's installed on the user's machine.
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from core.debug_log import debug_log
from core.paths import ASSETS_DIR

FONTS_DIR = ASSETS_DIR / "fonts"

#: Display/headline face — Oswald (SIL OFL), used sparingly for dialog
#: titles and ring branding, never for body text.
UI_FONT_CANDIDATES = (
    "Segoe UI Variable Text",
    "Segoe UI",
    "Microsoft JhengHei UI",
    "Noto Sans TC",
    "Arial",
)
UI_DISPLAY_FONT_CANDIDATES = (
    "Segoe UI Variable Display Semibold",
    "Segoe UI Variable Display",
    "Segoe UI Semibold",
    "Segoe UI",
)

# Compatibility alias for existing callers. Headings now use a softer native
# display face instead of the condensed bundled Oswald face.
DISPLAY_FONT_FAMILY = UI_DISPLAY_FONT_CANDIDATES[0]


def load_bundled_fonts() -> None:
    """Register every font file under assets/fonts/ with QFontDatabase. Call once at startup."""
    if not FONTS_DIR.is_dir():
        debug_log(f"fonts dir not found: {FONTS_DIR}")
        return
    for font_path in FONTS_DIR.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        debug_log(f"loaded font {font_path.name}: id={font_id} families={families}")


def _first_available(candidates: tuple[str, ...]) -> str:
    available = set(QFontDatabase.families())
    return next((family for family in candidates if family in available), candidates[-1])


def preferred_ui_font_family() -> str:
    return _first_available(UI_FONT_CANDIDATES)


def preferred_display_font_family() -> str:
    return _first_available(UI_DISPLAY_FONT_CANDIDATES)


def configure_application_font(app: QApplication) -> None:
    """Apply an iOS-like, highly legible native UI face throughout the app."""
    family = preferred_ui_font_family()
    font = QFont(family)
    font.setPointSizeF(10.0)
    font.setWeight(QFont.Weight.Normal)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    debug_log(f"application UI font: family={family!r} point_size={font.pointSizeF()}")
