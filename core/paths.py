"""
Centralized path resolution — works in both development and PyInstaller builds.

Development (python -m app.main)
  All paths resolve relative to the project root.

Frozen (PyInstaller --onedir or --onefile)
  Writable config  → directory containing the .exe  (user's files survive reinstall)
  Bundled assets   → sys._MEIPASS                   (scripts, read-only resources)

Why two roots?
  PyInstaller 6.x puts bundled data in <exe_dir>/_internal/ (sys._MEIPASS).
  That directory is effectively read-only on some setups and is internal to the
  bundle.  User-editable config must live next to the exe so it survives updates.
"""
from __future__ import annotations

import sys
from pathlib import Path


# ── Private helpers ───────────────────────────────────────────────────────────

def _project_root() -> Path:
    """Project root when running from source.  core/paths.py lives at <root>/core/."""
    return Path(__file__).resolve().parent.parent


def _exe_dir() -> Path:
    """
    Writable root — the directory that contains the running executable.

    Dev   → project root  (same as _project_root)
    Frozen → <dist>/<AppName>/   (next to Universal Actions Ring.exe)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _project_root()


def _bundle_dir() -> Path:
    """
    Read-only bundle root — where PyInstaller extracts / stores data files.

    Dev    → project root
    Frozen → sys._MEIPASS  (persistent sub-dir for --onedir; temp for --onefile)
    Falls back to _exe_dir() if _MEIPASS is not set (PyInstaller < 6 --onedir).
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        return Path(meipass).resolve() if meipass else _exe_dir()
    return _project_root()


# ── Public constants (computed once at import time) ───────────────────────────

#: Writable config directory — user edits persist here.
#:   Dev   : <root>/config/
#:   Frozen: <exe_dir>/config/
CONFIG_DIR = _exe_dir() / "config"

#: Writable legacy resources directory (resources/config.json).
#:   Dev   : <root>/resources/
#:   Frozen: <exe_dir>/resources/
RESOURCES_DIR = _exe_dir() / "resources"

#: Writable app data directory.
#:   Dev   : <root>/data/
#:   Frozen: <exe_dir>/data/
DATA_DIR = _exe_dir() / "data"

#: Writable profile backup directory.
#:   Dev   : <root>/backups/
#:   Frozen: <exe_dir>/backups/
BACKUPS_DIR = _exe_dir() / "backups"

#: Read-only bundled project root.
#:   Dev   : <root>/
#:   Frozen: <_MEIPASS>/
BUNDLE_DIR = _bundle_dir()

#: Read-only bundled assets directory.
#:   Dev   : <root>/assets/
#:   Frozen: <_MEIPASS>/assets/
ASSETS_DIR = BUNDLE_DIR / "assets"

#: Read-only bundled docs directory.
#:   Dev   : <root>/docs/
#:   Frozen: <_MEIPASS>/docs/
DOCS_DIR = BUNDLE_DIR / "docs"

#: Read-only PowerShell scripts (bundled by PyInstaller into sys._MEIPASS).
#:   Dev   : <root>/core/scripts/
#:   Frozen: <_MEIPASS>/core/scripts/
SCRIPTS_DIR = BUNDLE_DIR / "core" / "scripts"
