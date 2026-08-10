@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ========================================
echo  SmartAction - Clean Portable Build
echo ========================================
echo.

set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    set "PYTHON=python"
)
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found. Create the project .venv or add Python to PATH.
    exit /b 1
)

echo [1/8] Checking required release sources...
for %%F in (
    "app\main.py"
    "config\actions.json"
    "resources\config.json"
    "data\powershell_library.json"
    "data\client_workspaces.json"
    "data\icons\emoji_database.json"
    "assets\ui\cute-default-background.png"
    "assets\themes\purple\frames\frame_000.png"
    "web_control_center\index.html"
    "web_control_center\control-center.css"
    "web_control_center\control-center.js"
    "web_control_center\smartaction-logo.png"
    "extensions\firefox-helper\manifest.json"
    "extensions\firefox-helper\background.js"
    "native\firefox_helper_host\smartaction_firefox_host.py"
) do (
    if not exist %%F (
        echo [ERROR] Required release source is missing: %%~F
        exit /b 1
    )
)
echo Done.

echo.
echo [2/8] Installing build dependencies into the selected Python environment...
"%PYTHON%" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency install failed.
    exit /b 1
)
"%PYTHON%" -m pip install -q "pyinstaller>=5.13" "pyinstaller-hooks-contrib>=2024.0"
if errorlevel 1 (
    echo [ERROR] PyInstaller install failed.
    exit /b 1
)
echo Done.

echo.
echo [3/8] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist build (
    echo [ERROR] Could not remove build. Close programs using it and try again.
    exit /b 1
)
if exist dist rmdir /s /q dist
if exist dist (
    echo [ERROR] Could not remove dist. Exit any running SmartAction instance and try again.
    exit /b 1
)
echo Done.

echo.
echo [4/8] Preparing isolated PyInstaller cache...
set "PYINSTALLER_CONFIG_DIR=%CD%\build\pyinstaller-cache"
echo Cache: %PYINSTALLER_CONFIG_DIR%

echo.
echo [5/8] Building onedir application bundle...
"%PYTHON%" -m PyInstaller --clean --noconfirm --distpath dist --workpath build smartaction.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See output above.
    exit /b 1
)

set "APPDIR=dist\SmartAction"
echo.
echo [6/8] Copying writable starter data beside the executable...
if not exist "%APPDIR%\config" mkdir "%APPDIR%\config"
copy /y config\actions.json "%APPDIR%\config\actions.json" >nul
if not exist "%APPDIR%\resources" mkdir "%APPDIR%\resources"
copy /y resources\config.json "%APPDIR%\resources\config.json" >nul
if not exist "%APPDIR%\data" mkdir "%APPDIR%\data"
copy /y data\powershell_library.json "%APPDIR%\data\powershell_library.json" >nul
copy /y data\client_workspaces.json "%APPDIR%\data\client_workspaces.json" >nul
xcopy /e /i /y data\icons "%APPDIR%\data\icons" >nul
echo Done.

echo.
echo [7/8] Building Firefox helper extension...
"%PYTHON%" tools\build_firefox_extension.py
if errorlevel 1 (
    echo [ERROR] Container Helper Extension build failed.
    exit /b 1
)
echo Done.

echo.
echo [8/8] Verifying onedir output and bundled resources...
for %%F in (
    "%APPDIR%\SmartAction.exe"
    "%APPDIR%\_internal\assets\themes\purple\frames\frame_000.png"
    "%APPDIR%\_internal\assets\ui\cute-default-background.png"
    "%APPDIR%\_internal\web_control_center\index.html"
    "%APPDIR%\_internal\web_control_center\control-center.css"
    "%APPDIR%\_internal\web_control_center\control-center.js"
    "%APPDIR%\_internal\web_control_center\smartaction-logo.png"
    "%APPDIR%\_internal\data\icons\emoji_database.json"
    "%APPDIR%\_internal\core\scripts\join_domain.ps1"
    "%APPDIR%\config\actions.json"
    "%APPDIR%\resources\config.json"
    "%APPDIR%\data\powershell_library.json"
    "%APPDIR%\data\client_workspaces.json"
    "%APPDIR%\data\icons\emoji_database.json"
    "dist\firefox-helper.xpi"
) do (
    if not exist %%F (
        echo [ERROR] Build output is incomplete: %%~F
        exit /b 1
    )
)

echo.
echo BUILD SUCCEEDED
echo Portable app folder: %CD%\%APPDIR%
exit /b 0
