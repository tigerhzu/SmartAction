from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


VERSION = "v1.2.0"
APP_NAME = "SmartAction"
ADDON_ID = "smartaction-container-helper@naughtytiger06.local"
HOST_NAME = "smartaction_firefox_helper"

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_SRC = DIST / "UniversalActionsRing"
XPI_SRC = DIST / "firefox-helper.xpi"
RELEASE_DIR = DIST / f"SmartAction-Release-{VERSION}"
NATIVE_SRC = ROOT / "native" / "firefox_helper_host" / "smartaction_firefox_host.py"

PUBLIC_DOCS = {
    "help.md",
    "quick-start.md",
    "help-center.md",
    "client-workspace.md",
    "firefox-container-helper.md",
    "firefox-helper-signing.md",
}

IGNORE_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "backups",
}

FORBIDDEN_FILE_NAMES = {
    "smartaction.lock",
    "app_debug.log",
    "helper.log",
}

FORBIDDEN_TEXT = [
    r"C:\Users\naugh",
    "C:/Users/naugh",
    "default-release",
    "host_manifest.json\"",
]


RELEASE_ACTIONS = {
    "version": "1.1",
    "hotkey": "ctrl+alt+space",
    "theme": "tiger",
    "constellation": "scorpio",
    "constellation_color": "#F2760B",
    "actions": [
        {
            "id": "getting_started",
            "label": "Getting Started",
            "short_label": "GO",
            "icon": "",
            "type": "folder",
            "target": "",
            "enabled": True,
            "sub_actions": [
                {
                    "id": "docs_github",
                    "label": "SmartAction Docs",
                    "short_label": "",
                    "icon": "",
                    "type": "url",
                    "target": "https://github.com/tigerhzu/SmartAction",
                    "enabled": True,
                },
                {
                    "id": "chatgpt",
                    "label": "ChatGPT",
                    "short_label": "",
                    "icon": "",
                    "type": "url",
                    "target": "https://chatgpt.com",
                    "enabled": True,
                },
            ],
        },
        {
            "id": "settings",
            "label": "Settings",
            "short_label": "SET",
            "icon": "",
            "type": "settings",
            "target": "",
            "enabled": True,
            "sub_actions": [],
        },
        {
            "id": "environment_check",
            "label": "Environment Check",
            "short_label": "ENV",
            "icon": "",
            "type": "environment_check",
            "target": "",
            "enabled": True,
            "sub_actions": [],
        },
        {
            "id": "powershell_library",
            "label": "PowerShell Library",
            "short_label": "PS",
            "icon": "",
            "type": "powershell_library",
            "target": "",
            "enabled": True,
            "sub_actions": [],
        },
        {
            "id": "client_workspace",
            "label": "Client Workspace",
            "short_label": "CW",
            "icon": "",
            "type": "client_workspace",
            "target": "",
            "enabled": True,
            "sub_actions": [],
        },
        {
            "id": "task_manager",
            "label": "Task Manager",
            "short_label": "TM",
            "icon": "",
            "type": "app",
            "target": r"C:\Windows\System32\Taskmgr.exe",
            "enabled": True,
            "sub_actions": [],
        },
    ],
}

RELEASE_RESOURCES = {
    "version": "1.1.0",
    "hotkey": "ctrl+alt+space",
    "ring": {
        "radius": 120,
        "item_size": 48,
        "animation_ms": 180,
        "theme": "dark",
    },
    "startup_video_enabled": False,
    "startup_video_duration": 5,
    "startup_video_path": "assets/startup/startup.png",
    "menu_items": [],
}

RELEASE_CLIENT_WORKSPACES = {
    "version": "1.0",
    "clients": [],
}


def _run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\r\n", encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _copytree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.log",
            "smartaction.lock",
            ".DS_Store",
        ),
    )


def _ensure_app_build() -> None:
    exe = APP_SRC / "UniversalActionsRing.exe"
    if not exe.exists():
        raise FileNotFoundError(
            f"App build missing: {exe}. Run build.bat before packaging."
        )


def _ensure_xpi() -> None:
    if XPI_SRC.exists():
        return
    _run([sys.executable, str(ROOT / "tools" / "build_firefox_extension.py")])


def _build_native_host_exe() -> Path:
    native_dist = BUILD / "native-host-dist"
    native_work = BUILD / "native-host-work"
    if native_dist.exists():
        shutil.rmtree(native_dist)
    if native_work.exists():
        shutil.rmtree(native_work)

    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--console",
            "--name",
            "smartaction_firefox_host",
            "--distpath",
            str(native_dist),
            "--workpath",
            str(native_work),
            str(NATIVE_SRC),
        ]
    )
    exe = native_dist / "smartaction_firefox_host.exe"
    if not exe.exists():
        raise FileNotFoundError(f"Native host exe was not created: {exe}")
    generated_spec = ROOT / "smartaction_firefox_host.spec"
    if generated_spec.exists():
        generated_spec.unlink()
    return exe


def _copy_app_bundle() -> None:
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    shutil.copytree(APP_SRC, RELEASE_DIR)

    source_exe = RELEASE_DIR / "UniversalActionsRing.exe"
    target_exe = RELEASE_DIR / "SmartAction.exe"
    if target_exe.exists():
        target_exe.unlink()
    source_exe.rename(target_exe)

    for name in ("extensions", "native"):
        path = RELEASE_DIR / name
        if path.exists():
            shutil.rmtree(path)

    for path in RELEASE_DIR.rglob("*"):
        if path.is_file() and (
            path.name in FORBIDDEN_FILE_NAMES
            or path.suffix.lower() in {".pyc", ".pyo", ".log"}
        ):
            path.unlink()

    for path in list(RELEASE_DIR.rglob("__pycache__")):
        if path.is_dir():
            shutil.rmtree(path)


def _write_clean_runtime_files() -> None:
    for name in ("config", "resources", "data"):
        path = RELEASE_DIR / name
        if path.exists():
            shutil.rmtree(path)

    _write_json(RELEASE_DIR / "config" / "actions.json", RELEASE_ACTIONS)
    _write_json(RELEASE_DIR / "resources" / "config.json", RELEASE_RESOURCES)
    _write_json(RELEASE_DIR / "data" / "client_workspaces.json", RELEASE_CLIENT_WORKSPACES)

    source_library = ROOT / "data" / "powershell_library.json"
    if source_library.exists():
        shutil.copy2(source_library, RELEASE_DIR / "data" / "powershell_library.json")
    else:
        _write_json(RELEASE_DIR / "data" / "powershell_library.json", {"version": "1.1", "scripts": []})

    _copytree(ROOT / "data" / "icons", RELEASE_DIR / "data" / "icons")


def _scrub_internal_docs() -> None:
    docs_dir = RELEASE_DIR / "_internal" / "docs"
    if not docs_dir.exists():
        return
    for path in docs_dir.iterdir():
        if path.is_file() and path.name not in PUBLIC_DOCS:
            path.unlink()
        elif path.is_dir() and path.name != "images":
            shutil.rmtree(path)


def _scrub_release_text() -> None:
    replacements = {
        "default-release": "SmartAction-ClientWorkspace",
        r"C:\Users\naugh": r"C:\Users\YourName",
        "C:/Users/naugh": "C:/Users/YourName",
    }
    for path in RELEASE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt", ".bat", ".template"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _write_firefox_package(native_host_exe: Path) -> None:
    firefox_dir = RELEASE_DIR / "firefox"
    native_dir = firefox_dir / "native_host"
    firefox_dir.mkdir(parents=True, exist_ok=True)
    native_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(XPI_SRC, firefox_dir / "firefox-helper.xpi")
    shutil.copy2(native_host_exe, native_dir / "smartaction_firefox_host.exe")
    shutil.copy2(
        ROOT / "native" / "firefox_helper_host" / "host_manifest.json.template",
        native_dir / "host_manifest.json.template",
    )
    if (ROOT / "extensions" / "firefox-helper" / "README.md").exists():
        shutil.copy2(ROOT / "extensions" / "firefox-helper" / "README.md", firefox_dir / "EXTENSION_README.md")

    _write_text(
        firefox_dir / "setup_firefox.bat",
        rf"""
@echo off
setlocal
cd /d "%~dp0"

if "%SMARTACTION_TEST_MODE%"=="1" (
    echo [TEST] firefox setup smoke test passed.
    exit /b 0
)

if /i not "%OS%"=="Windows_NT" (
    echo [ERROR] This setup script is for Windows only.
    exit /b 1
)

if not exist "%~dp0firefox-helper.xpi" (
    echo [ERROR] firefox-helper.xpi was not found.
    exit /b 1
)
if not exist "%~dp0native_host\smartaction_firefox_host.exe" (
    echo [ERROR] Native host exe was not found.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $base=(Resolve-Path '.').Path; $local=Join-Path $env:LOCALAPPDATA 'SmartAction'; $hostDir=Join-Path $local 'firefox_helper_host'; New-Item -ItemType Directory -Force -Path $local,$hostDir | Out-Null; Copy-Item -Force (Join-Path $base 'firefox-helper.xpi') (Join-Path $local 'firefox-helper.xpi'); Copy-Item -Force (Join-Path $base 'native_host\smartaction_firefox_host.exe') (Join-Path $hostDir 'smartaction_firefox_host.exe'); $hostExe=Join-Path $hostDir 'smartaction_firefox_host.exe'; $manifest=Join-Path $hostDir 'host_manifest.json'; $data=[ordered]@{{name='{HOST_NAME}'; description='SmartAction Container Helper Native Messaging Host'; path=$hostExe; type='stdio'; allowed_extensions=@('{ADDON_ID}')}}; $data | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifest; & reg.exe add 'HKCU\Software\Mozilla\NativeMessagingHosts\{HOST_NAME}' /ve /d $manifest /f | Out-Null; Write-Host 'Firefox Native Messaging Host registered:' $manifest"
if errorlevel 1 (
    echo [ERROR] Firefox helper setup failed.
    exit /b 1
)

echo.
echo Firefox helper files were installed to:
echo   %LOCALAPPDATA%\SmartAction
echo.
echo Manual Firefox extension step:
echo   Install firefox-helper.xpi from this folder, or use a signed XPI for regular Firefox release builds.
echo.
exit /b 0
""",
    )

    _write_text(
        firefox_dir / "uninstall_firefox.bat",
        rf"""
@echo off
setlocal

if "%SMARTACTION_TEST_MODE%"=="1" (
    echo [TEST] firefox uninstall smoke test passed.
    exit /b 0
)

reg delete "HKCU\Software\Mozilla\NativeMessagingHosts\{HOST_NAME}" /f >nul 2>nul
echo Firefox Native Messaging Host registry entry removed if it existed.

set /p DELETE_FILES=Delete local Firefox helper files under %%LOCALAPPDATA%%\SmartAction? [y/N]:
if /i "%DELETE_FILES%"=="Y" (
    if exist "%LOCALAPPDATA%\SmartAction\firefox_helper_host" rmdir /s /q "%LOCALAPPDATA%\SmartAction\firefox_helper_host"
    if exist "%LOCALAPPDATA%\SmartAction\firefox_helper" rmdir /s /q "%LOCALAPPDATA%\SmartAction\firefox_helper"
    if exist "%LOCALAPPDATA%\SmartAction\firefox-helper.xpi" del /q "%LOCALAPPDATA%\SmartAction\firefox-helper.xpi"
)

echo Firefox helper uninstall finished.
exit /b 0
""",
    )


def _write_root_scripts() -> None:
    _write_text(
        RELEASE_DIR / "start.bat",
        """
@echo off
setlocal
cd /d "%~dp0"
if "%SMARTACTION_TEST_MODE%"=="1" (
    echo [TEST] start smoke test passed.
    exit /b 0
)
start "" "%~dp0SmartAction.exe"
exit /b 0
""",
    )

    _write_text(
        RELEASE_DIR / "install.bat",
        r"""
@echo off
setlocal
cd /d "%~dp0"

if "%SMARTACTION_TEST_MODE%"=="1" (
    echo [TEST] install smoke test passed.
    exit /b 0
)

if /i not "%OS%"=="Windows_NT" (
    echo [ERROR] SmartAction release package is for Windows only.
    exit /b 1
)

if not exist "%~dp0SmartAction.exe" (
    echo [ERROR] SmartAction.exe was not found in this folder.
    exit /b 1
)

echo Creating Desktop and Start Menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $base=(Resolve-Path '.').Path; $exe=Join-Path $base 'SmartAction.exe'; $ws=New-Object -ComObject WScript.Shell; $desktop=[Environment]::GetFolderPath('Desktop'); $lnk=$ws.CreateShortcut((Join-Path $desktop 'SmartAction.lnk')); $lnk.TargetPath=$exe; $lnk.WorkingDirectory=$base; $lnk.IconLocation=$exe; $lnk.Save(); $start=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\SmartAction'; New-Item -ItemType Directory -Force -Path $start | Out-Null; $lnk2=$ws.CreateShortcut((Join-Path $start 'SmartAction.lnk')); $lnk2.TargetPath=$exe; $lnk2.WorkingDirectory=$base; $lnk2.IconLocation=$exe; $lnk2.Save()"
if errorlevel 1 (
    echo [ERROR] Shortcut creation failed.
    exit /b 1
)

set /p AUTOSTART=Start SmartAction when Windows starts? [y/N]:
if /i "%AUTOSTART%"=="Y" (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v SmartAction /t REG_SZ /d "\"%~dp0SmartAction.exe\"" /f >nul
    echo Autostart enabled.
) else (
    echo Autostart skipped.
)

set /p FIREFOX=Run Firefox container helper setup now? [y/N]:
if /i "%FIREFOX%"=="Y" (
    call "%~dp0firefox\setup_firefox.bat"
    if errorlevel 1 exit /b 1
)

echo.
echo Install finished. Use start.bat or the SmartAction shortcut to launch.
exit /b 0
""",
    )

    _write_text(
        RELEASE_DIR / "uninstall.bat",
        r"""
@echo off
setlocal
cd /d "%~dp0"

if "%SMARTACTION_TEST_MODE%"=="1" (
    echo [TEST] uninstall smoke test passed.
    exit /b 0
)

echo Removing SmartAction shortcuts and autostart...
if exist "%USERPROFILE%\Desktop\SmartAction.lnk" del /q "%USERPROFILE%\Desktop\SmartAction.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SmartAction\SmartAction.lnk" del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SmartAction\SmartAction.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SmartAction" rmdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SmartAction" >nul 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v SmartAction /f >nul 2>nul

set /p FIREFOX=Remove Firefox helper registration? [y/N]:
if /i "%FIREFOX%"=="Y" (
    call "%~dp0firefox\uninstall_firefox.bat"
)

set /p USERDATA=Delete local SmartAction package data folders config, data, resources, backups? [y/N]:
if /i "%USERDATA%"=="Y" (
    if exist "%~dp0config" rmdir /s /q "%~dp0config"
    if exist "%~dp0data" rmdir /s /q "%~dp0data"
    if exist "%~dp0resources" rmdir /s /q "%~dp0resources"
    if exist "%~dp0backups" rmdir /s /q "%~dp0backups"
) else (
    echo User data kept.
)

echo Uninstall finished.
exit /b 0
""",
    )


def _write_readme() -> None:
    _write_text(
        RELEASE_DIR / "README.md",
        f"""
# SmartAction Release {VERSION}

SmartAction is a Windows tray + hotkey action ring for shortcuts, automation, IT support, and repeatable desktop workflows.

## What Is Included

- `SmartAction.exe` - packaged desktop application.
- `_internal/` - PyInstaller runtime files required by the exe.
- `config/actions.json` - clean starter Ring configuration.
- `resources/config.json` - startup/video and legacy runtime settings.
- `data/powershell_library.json` - generic PowerShell Library script templates.
- `data/client_workspaces.json` - empty Client Workspace data file.
- `data/icons/` - local icon/emoji picker database.
- `firefox/` - Firefox Container Helper XPI, native host exe, setup/uninstall scripts.
- `install.bat`, `uninstall.bat`, `start.bat` - colleague-facing helper scripts.

## Install

1. Extract the whole `SmartAction-Release-{VERSION}` folder to a writable location, for example `C:\\Tools\\SmartAction`.
2. Run `install.bat`.
3. Choose whether to enable Windows startup.
4. Choose whether to run Firefox helper setup.
5. Launch SmartAction from the Desktop shortcut, Start Menu shortcut, or `start.bat`.

Administrator rights are not normally required for app install because shortcuts and autostart use the current user profile. Some PowerShell actions may require running SmartAction as administrator.

## Start

Run:

```bat
start.bat
```

or double-click `SmartAction.exe`.

SmartAction runs in the system tray. Use the tray menu to open Settings, PowerShell Library, Client Workspace, reload config, restart hotkey, or exit.

The Ring also includes a Settings action. Click an action to run it, or hold and drag an action to rotate the Ring without launching it.

## Configure Hotkey

1. Right-click the tray icon.
2. Open Settings.
3. Use the Hotkey section to set a new global hotkey.
4. Click Save.

Default release hotkey: `Ctrl + Alt + Space`.

## Add Ring Actions

1. Open Settings from the tray.
2. Click Add action.
3. Choose an action type such as URL, App/File, Command, PowerShell, Environment Check, Client Workspace, Paste, Form, PS Form, or PowerShell Library.
4. Fill in label, icon, target, and sub actions as needed.
5. Click Save.

## PowerShell Library Type

The Ring `PowerShell Library` action opens the PowerShell Library window. It does not yet bind one specific library script directly to a Ring slot.

Inside PowerShell Library, users can review scripts, fill parameters, confirm dangerous scripts, and run them manually.

## Firefox Container Helper

The Firefox helper has two parts:

1. Firefox extension: `firefox/firefox-helper.xpi`
2. Native Messaging Host: `firefox/native_host/smartaction_firefox_host.exe`

Run:

```bat
firefox\\setup_firefox.bat
```

This registers the Native Messaging Host under the current Windows user. It does not normally need administrator rights.

Important: regular Firefox release builds usually require signed extensions. If Firefox refuses the bundled XPI, submit/sign the XPI or use your organization's normal extension deployment method. The README in `firefox/EXTENSION_README.md` has extra extension details.

## Troubleshooting

- App does not open: check if another SmartAction instance is already running in the system tray.
- Hotkey does not work: open tray menu and choose Restart Hotkey, or change the hotkey in Settings.
- Tray icon missing: make sure Windows system tray is available and SmartAction is not blocked by policy.
- Firefox helper check fails: run `firefox\\setup_firefox.bat`, install the XPI, then use Client Workspace > Check Helper.
- Container not found: create a Firefox container with the same name used in Client Workspace.
- PowerShell action fails: run SmartAction as administrator if the script changes system settings.

## Uninstall

Run:

```bat
uninstall.bat
```

The uninstaller removes shortcuts and autostart. It asks before removing Firefox helper registration and asks again before deleting local package data.
""",
    )


def _validate_release() -> None:
    required = [
        "SmartAction.exe",
        "_internal",
        "config/actions.json",
        "resources/config.json",
        "data/powershell_library.json",
        "data/client_workspaces.json",
        "data/icons/emoji_database.json",
        "firefox/firefox-helper.xpi",
        "firefox/native_host/smartaction_firefox_host.exe",
        "firefox/setup_firefox.bat",
        "firefox/uninstall_firefox.bat",
        "install.bat",
        "uninstall.bat",
        "start.bat",
        "README.md",
    ]
    for rel in required:
        path = RELEASE_DIR / rel
        if not path.exists():
            raise FileNotFoundError(f"Release validation failed, missing: {rel}")

    for path in RELEASE_DIR.rglob("*"):
        rel_parts = path.relative_to(RELEASE_DIR).parts
        if any(part in IGNORE_NAMES for part in rel_parts):
            raise RuntimeError(f"Forbidden folder leaked into release: {path}")
        if path.name in FORBIDDEN_FILE_NAMES:
            raise RuntimeError(f"Forbidden file leaked into release: {path}")
        if path.suffix.lower() in {".pyc", ".pyo", ".log"}:
            raise RuntimeError(f"Generated/cache file leaked into release: {path}")

    for path in RELEASE_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt", ".bat", ".template"}:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for needle in FORBIDDEN_TEXT:
                if needle in text:
                    raise RuntimeError(f"Sensitive/local text leaked into {path}: {needle}")


def build_release() -> None:
    _ensure_app_build()
    _ensure_xpi()
    native_host_exe = _build_native_host_exe()
    _copy_app_bundle()
    _write_clean_runtime_files()
    _scrub_internal_docs()
    _write_firefox_package(native_host_exe)
    _write_root_scripts()
    _write_readme()
    _scrub_release_text()
    _validate_release()

    print("SmartAction release package created.")
    print(f"Release: {RELEASE_DIR}")
    print(f"App: {RELEASE_DIR / 'SmartAction.exe'}")
    print(f"Install: {RELEASE_DIR / 'install.bat'}")


if __name__ == "__main__":
    build_release()
