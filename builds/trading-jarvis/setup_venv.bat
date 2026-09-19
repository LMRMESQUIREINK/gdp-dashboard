@echo off
:: ============================================================
:: Trading Jarvis — Setup Script (Windows)
:: ============================================================
:: Creates an isolated .venv in this folder — does NOT touch any
:: system Python packages, and does NOT use --break-system-packages.
:: Run this ONCE.
:: ============================================================

title Trading Jarvis — Setup
cd /d %~dp0

echo.
echo ============================================================
echo   Trading Jarvis — Setup
echo ============================================================
echo.

set PYTHON=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :found_python
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py
    goto :found_python
)

echo [ERROR] Python not found.
echo.
echo Install Python 3.10+ from https://www.python.org/downloads/
echo During install: check "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo [1/3] Python found:
"%PYTHON%" --version
echo.

echo [2/3] Creating virtual environment (.venv)...
if exist .venv (
    echo        .venv already exists - skipping.
) else (
    "%PYTHON%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
    echo        Done.
)
echo.

echo [3/3] Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Some packages failed to install. Check your internet connection and re-run.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete!
echo   Set your API keys, then run run_jarvis.bat
echo     setx EODHD_API_KEY "your_key_here"
echo     setx FMP_API_KEY "your_key_here"
echo     setx ANTHROPIC_API_KEY "your_key_here"
echo   (restart your terminal after setx so the values take effect)
echo ============================================================
echo.
pause
