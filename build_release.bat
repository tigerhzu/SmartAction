@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found. Create the project .venv or add Python to PATH.
    exit /b 1
)

echo [1/3] Compiling source files...
"%PYTHON%" -m compileall -q app core ui platforms native\firefox_helper_host tools
if errorlevel 1 exit /b 1

echo [2/3] Building PyInstaller portable bundle...
call build.bat
if errorlevel 1 exit /b 1

echo [3/3] Finalising clean portable release and ZIP...
"%PYTHON%" tools\build_release_package.py
if errorlevel 1 exit /b 1

echo.
echo Release folder: %CD%\dist\SmartAction
echo Shareable ZIP:  %CD%\dist\SmartAction-v1.4.0-portable.zip
exit /b 0
