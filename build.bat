@echo off
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo  Universal Actions Ring - Clean Build
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    exit /b 1
)

echo [1/7] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    exit /b 1
)
pip install -q "pyinstaller>=5.13" "pyinstaller-hooks-contrib>=2024.0"
if errorlevel 1 (
    echo [ERROR] PyInstaller install failed.
    exit /b 1
)
echo Done.

echo.
echo [2/7] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1
if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller"
echo Done.

echo.
echo [3/7] Preparing isolated PyInstaller cache...
set "PYINSTALLER_CONFIG_DIR=%CD%\build\pyinstaller-cache"
if exist "%PYINSTALLER_CONFIG_DIR%" rmdir /s /q "%PYINSTALLER_CONFIG_DIR%"
echo Cache: %PYINSTALLER_CONFIG_DIR%

echo.
echo [4/7] Running PyInstaller from current app/main.py...
pyinstaller --clean --noconfirm --distpath dist --workpath build smartaction.spec
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. See output above.
    exit /b 1
)

echo.
echo [5/7] Copying writable runtime config next to exe...
set "APPDIR=dist\UniversalActionsRing"
if not exist "%APPDIR%\config" mkdir "%APPDIR%\config"
if exist config\actions.json copy /y config\actions.json "%APPDIR%\config\actions.json" >nul
if exist data\powershell_library.json (
    if not exist "%APPDIR%\data" mkdir "%APPDIR%\data"
    copy /y data\powershell_library.json "%APPDIR%\data\powershell_library.json" >nul
)
if exist data\client_workspaces.json (
    if not exist "%APPDIR%\data" mkdir "%APPDIR%\data"
    copy /y data\client_workspaces.json "%APPDIR%\data\client_workspaces.json" >nul
)
if exist data\icons (
    if not exist "%APPDIR%\data" mkdir "%APPDIR%\data"
    xcopy /e /i /y data\icons "%APPDIR%\data\icons" >nul
)
if exist assets\startup (
    if not exist "%APPDIR%\assets" mkdir "%APPDIR%\assets"
    xcopy /e /i /y assets\startup "%APPDIR%\assets\startup" >nul
)
if exist extensions (
    xcopy /e /i /y extensions "%APPDIR%\extensions" >nul
)
if exist native (
    xcopy /e /i /y native "%APPDIR%\native" >nul
)
if exist resources\config.json (
    if not exist "%APPDIR%\resources" mkdir "%APPDIR%\resources"
    copy /y resources\config.json "%APPDIR%\resources\config.json" >nul
)
echo Done.

echo.
echo [6/7] Building Container Helper Extension XPI...
python tools\build_firefox_extension.py
if errorlevel 1 (
    echo.
    echo [ERROR] Container Helper Extension build failed.
    exit /b 1
)
echo Done.

echo.
echo [7/7] Verifying output and bundled resources...
set "EXE=%APPDIR%\UniversalActionsRing.exe"
if not exist "%EXE%" (
    echo.
    echo BUILD FAILED - exe not found at: %CD%\%EXE%
    exit /b 1
)
if not exist "%APPDIR%\_internal\assets\themes\purple\frames\frame_000.png" (
    echo.
    echo BUILD FAILED - theme animation assets were not bundled.
    exit /b 1
)
if not exist "%APPDIR%\_internal\docs\help.md" (
    echo.
    echo BUILD FAILED - docs/help.md was not bundled.
    exit /b 1
)
if not exist "%APPDIR%\config\actions.json" (
    echo.
    echo BUILD FAILED - config/actions.json was not copied next to exe.
    exit /b 1
)
if exist data\powershell_library.json (
    if not exist "%APPDIR%\data\powershell_library.json" (
        echo.
        echo BUILD FAILED - data/powershell_library.json was not copied next to exe.
        exit /b 1
    )
)
if exist data\client_workspaces.json (
    if not exist "%APPDIR%\data\client_workspaces.json" (
        echo.
        echo BUILD FAILED - data/client_workspaces.json was not copied next to exe.
        exit /b 1
    )
)
if not exist "%APPDIR%\data\icons\emoji_database.json" (
    echo.
    echo BUILD FAILED - data/icons/emoji_database.json was not copied next to exe.
    exit /b 1
)
if not exist "%APPDIR%\_internal\data\icons\emoji_database.json" (
    echo.
    echo BUILD FAILED - data/icons/emoji_database.json was not bundled.
    exit /b 1
)
if exist assets\startup\startup.gif (
    if not exist "%APPDIR%\assets\startup\startup.gif" (
        echo.
        echo BUILD FAILED - assets/startup/startup.gif was not copied next to exe.
        exit /b 1
    )
)
if not exist "%APPDIR%\extensions\firefox-helper\manifest.json" (
    echo.
    echo BUILD FAILED - helper extension was not copied next to exe.
    exit /b 1
)
if not exist "%APPDIR%\native\firefox_helper_host\smartaction_firefox_host.py" (
    echo.
    echo BUILD FAILED - native helper host was not copied next to exe.
    exit /b 1
)
if not exist "dist\firefox-helper.xpi" (
    echo.
    echo BUILD FAILED - helper XPI was not created.
    exit /b 1
)

echo.
echo BUILD SUCCEEDED
echo Output: %CD%\%EXE%
echo Container Helper XPI: %CD%\dist\firefox-helper.xpi
echo.
echo ========================================
echo  Done.
echo ========================================
echo.
