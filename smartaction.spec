# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for Universal Actions Ring.

Usage
-----
  # From the project root:
  pyinstaller smartaction.spec

  # Or use the helper script:
  build.bat

Output
------
  dist/UniversalActionsRing/UniversalActionsRing.exe
  dist/UniversalActionsRing/...  (Qt/Python runtime DLLs)

Path layout in the frozen exe directory
---------------------------------------
  <exe_dir>/Universal Actions Ring.exe   鈫?launch this
  <exe_dir>/_internal/                   鈫?PyInstaller 6.x bundle (sys._MEIPASS)
      core/scripts/join_domain.ps1
      core/scripts/add_local_user.ps1
  <exe_dir>/config/actions.json          鈫?auto-created on first run (writable)
  <exe_dir>/resources/config.json        鈫?auto-created by app on first save
"""

from pathlib import Path

ROOT = Path(SPECPATH)   # SPECPATH is injected by PyInstaller = dir of this .spec

block_cipher = None


def collect_tree(src: Path, dest: str) -> list[tuple[str, str]]:
    if not src.exists():
        return []
    files: list[tuple[str, str]] = []
    for path in src.rglob("*"):
        if path.is_file():
            rel_parent = path.parent.relative_to(src)
            target = Path(dest) / rel_parent
            files.append((str(path), str(target).replace("\\", "/")))
    return files


def collect_public_docs() -> list[tuple[str, str]]:
    """Bundle end-user docs only; keep internal redesign/release notes out."""
    public_docs = [
        "help.md",
        "quick-start.md",
        "help-center.md",
        "client-workspace.md",
        "firefox-container-helper.md",
        "firefox-helper-signing.md",
    ]
    files: list[tuple[str, str]] = []
    for name in public_docs:
        path = ROOT / "docs" / name
        if path.exists():
            files.append((str(path), "docs"))
    files += collect_tree(ROOT / "docs" / "images", "docs/images")
    return files
# 鈹€鈹€ Data files (bundled into sys._MEIPASS) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Only truly read-only files go here.
# Writable configs (config/actions.json, resources/config.json) are NOT bundled
# because ActionsConfig auto-creates actions.json and ConfigManager falls back
# to in-memory defaults 鈥?both handle a missing file gracefully.

_datas = [
    # PowerShell scripts 鈥?must be on a real filesystem path for powershell.exe -File
    (str(ROOT / 'core' / 'scripts' / 'join_domain.ps1'),    'core/scripts'),
    (str(ROOT / 'core' / 'scripts' / 'add_local_user.ps1'), 'core/scripts'),
    # Emoji catalog 鈥?read-only asset, safe to bundle
]

_datas += collect_tree(ROOT / 'assets', 'assets')
_datas += collect_public_docs()
_datas += collect_tree(ROOT / 'data' / 'icons', 'data/icons')

# 鈹€鈹€ Hidden imports 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Modules that are imported at runtime (not statically analysable by PyInstaller).

_hidden = [
    # ps_form_action.py does `import ui.forms` inside execute() 鈥?not statically visible
    'ui.forms',
    'ui.forms.join_domain_form',
    'ui.forms.add_local_user_form',
    'ui.forms.form_registry',
    'ui.powershell_library_window',
    'ui.client_workspace_window',
    'ui.startup_splash',

    # core.actions submodules are imported via side-effects in __init__.py;
    # include explicitly so PyInstaller does not miss any.
    'core.actions.url_action',
    'core.actions.command_action',
    'core.actions.app_action',
    'core.actions.powershell_action',
    'core.actions.powershell_library_action',
    'core.actions.environment_check_action',
    'core.actions.client_workspace_action',
    'core.actions.settings_action',
    'core.actions.ps_form_action',
    'core.actions.paste_action',
    'core.actions.form_action',
    'core.actions.submenu_action',

    # keyboard library (fallback hotkeys and synthetic paste input)
    'keyboard',
    'keyboard._winkeyboard',

]

# 鈹€鈹€ Analysis 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

a = Analysis(
    [str(ROOT / 'app' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=_datas,
    hiddenimports=_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Remove heavy packages we don't use
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPrintSupport',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PySide's generic hooks collect optional plugins for capabilities SmartAction
# never invokes. Keep the Windows QWidget platform and common raster formats,
# but omit Multimedia, Network, QML/Quick, virtual keyboard, PDF/SVG and
# headless/test backends.
_unused_qt_binaries = {
    'Qt6OpenGL.dll',
    'Qt6Network.dll',
    'Qt6Pdf.dll',
    'Qt6Qml.dll',
    'Qt6QmlMeta.dll',
    'Qt6QmlModels.dll',
    'Qt6QmlWorkerScript.dll',
    'Qt6Quick.dll',
    'Qt6Svg.dll',
    'Qt6VirtualKeyboard.dll',
    'QtNetwork.pyd',
    'qcertonlybackend.dll',
    'qdirect2d.dll',
    'qicns.dll',
    'qminimal.dll',
    'qnetworklistmanager.dll',
    'qoffscreen.dll',
    'qopensslbackend.dll',
    'qpdf.dll',
    'qschannelbackend.dll',
    'qsvg.dll',
    'qsvgicon.dll',
    'qtga.dll',
    'qtiff.dll',
    'qtuiotouchplugin.dll',
    'qtvirtualkeyboardplugin.dll',
    'qwbmp.dll',
    'qwebp.dll',
}
a.binaries = [
    entry for entry in a.binaries
    if Path(entry[0]).name not in _unused_qt_binaries
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 鈹€鈹€ Executable 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,           # binaries go into COLLECT (one-dir mode)
    name='UniversalActionsRing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                       # set True if UPX is installed and desired
    console=False,                   # windowed 鈥?no console popup
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icons/app.ico',  # uncomment and add icon when available
)

# 鈹€鈹€ Collection (one-dir bundle) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='UniversalActionsRing',
)

