@echo off
setlocal

cd /d "%~dp0"

python tools\build_firefox_extension.py
if errorlevel 1 (
    echo.
    echo [ERROR] Container Helper Extension build failed.
    exit /b 1
)

echo.
echo Output: %CD%\dist\firefox-helper.xpi
echo Fixed local copy: %LOCALAPPDATA%\SmartAction\firefox-helper.xpi
echo.
