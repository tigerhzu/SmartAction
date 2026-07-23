@echo off
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo  SmartAction Release Build
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    exit /b 1
)

echo [1/3] Compiling source files...
python -m compileall -q app core ui platforms native\firefox_helper_host tools
if errorlevel 1 (
    echo [ERROR] compileall failed.
    exit /b 1
)

echo.
echo [2/3] Building PyInstaller app bundle...
call build.bat
if errorlevel 1 (
    echo [ERROR] build.bat failed.
    exit /b 1
)

echo.
echo [3/3] Creating clean release package...
python tools\build_release_package.py
if errorlevel 1 (
    echo [ERROR] SmartAction release package build failed.
    exit /b 1
)

echo.
echo Release package: %CD%\dist\SmartAction-Release-v1.3.0
echo.
exit /b 0
