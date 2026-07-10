"""
Bundled application fonts.

Fonts are shipped under assets/fonts/ (picked up by PyInstaller's existing
assets/ collection in smartaction.spec — no spec changes needed) and must be
registered with QFontDatabase once, before any widget is constructed, so the
family is available regardless of what's installed on the user's machine.
"""
from __future__ import annotations

from PySide6.QtGui import QFontDatabase

from core.debug_log import debug_log
from core.paths import ASSETS_DIR

FONTS_DIR = ASSETS_DIR / "fonts"

#: Display/headline face — Oswald (SIL OFL), used sparingly for dialog
#: titles and ring branding, never for body text.
DISPLAY_FONT_FAMILY = "Oswald"


def load_bundled_fonts() -> None:
    """Register every font file under assets/fonts/ with QFontDatabase. Call once at startup."""
    if not FONTS_DIR.is_dir():
        debug_log(f"fonts dir not found: {FONTS_DIR}")
        return
    for font_path in FONTS_DIR.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        debug_log(f"loaded font {font_path.name}: id={font_id} families={families}")
