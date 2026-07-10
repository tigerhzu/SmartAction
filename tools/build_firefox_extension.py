from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_SRC = ROOT / "extensions" / "firefox-helper"
DIST_DIR = ROOT / "dist"
STAGING_DIR = DIST_DIR / "firefox-helper"
XPI_PATH = DIST_DIR / "firefox-helper.xpi"
LOCALAPPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SmartAction"
LOCAL_XPI_PATH = LOCALAPPDATA_DIR / "firefox-helper.xpi"

REQUIRED_FILES = ("manifest.json", "background.js", "README.md")


def _copy_extension() -> None:
    if not EXTENSION_SRC.exists():
        raise FileNotFoundError(f"Extension source not found: {EXTENSION_SRC}")

    for filename in REQUIRED_FILES:
        if not (EXTENSION_SRC / filename).exists():
            raise FileNotFoundError(f"Missing extension file: {EXTENSION_SRC / filename}")

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        EXTENSION_SRC,
        STAGING_DIR,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def _build_xpi() -> None:
    if XPI_PATH.exists():
        XPI_PATH.unlink()

    with zipfile.ZipFile(XPI_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(STAGING_DIR.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(STAGING_DIR).as_posix()
            zf.write(path, rel)


def _copy_to_localappdata() -> None:
    LOCALAPPDATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(XPI_PATH, LOCAL_XPI_PATH)


def main() -> int:
    _copy_extension()
    _build_xpi()
    _copy_to_localappdata()

    print("Container Helper Extension package created.")
    print(f"Staging: {STAGING_DIR}")
    print(f"XPI: {XPI_PATH}")
    print(f"Fixed local copy: {LOCAL_XPI_PATH}")
    print()
    print("Production installs require a signed XPI.")
    print("Use this XPI as the package to submit/sign, then install the signed XPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
