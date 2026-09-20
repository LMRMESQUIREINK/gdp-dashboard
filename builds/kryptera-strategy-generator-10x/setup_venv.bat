@echo off
:: ============================================================
:: Kryptera Strategy Generator 10X — Setup Script (Windows)
:: ============================================================
:: Auto-detects Python from PATH or common install locations.
:: Creates isolated .venv — does NOT affect system Python.
:: Run this ONCE before first use.
:: ============================================================

title Kryptera Strategy Generator 10X — Setup
cd /d %~dp0

echo.
echo ============================================================
echo   Kryptera Strategy Generator 10X — Setup
echo ============================================================
echo.

:: ── 1. Find Python ──────────────────────────────────────────
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

for %%D in (D C) do (
    for %%V in (313 312 311 310 39) do (
        if exist "%%D:\Python%%V\python.exe" (
            set PYTHON=%%D:\Python%%V\python.exe
            goto :found_python
        )
        if exist "%%D:\Python\Python%%V\python.exe" (
            set PYTHON=%%D:\Python\Python%%V\python.exe
            goto :found_python
        )
    )
)

for %%V in (3.13 3.12 3.11 3.10 3.9) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe
        goto :found_python
    )
)

echo [ERROR] Python not found.
echo.
echo Please install Python from: https://www.python.org/downloads/
echo During install: check "Add Python to PATH"
echo OR install to D:\Python3xx\ and re-run this script.
echo.
pause
exit /b 1

:found_python
echo [1/4] Python found:
"%PYTHON%" --version
echo        Path: %PYTHON%
echo.

:: ── 2. Create virtual environment ───────────────────────────
echo [2/4] Creating virtual environment (.venv)...
if exist .venv (
    echo        .venv already exists - skipping.
) else (
    "%PYTHON%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        echo         Try running as Administrator.
        pause
        exit /b 1
    )
    echo        Done.
)
echo.

:: ── 3. Upgrade pip ──────────────────────────────────────────
echo [3/4] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
echo        Done.
echo.

:: ── 4. Install dependencies ─────────────────────────────────
echo [4/4] Installing dependencies (5-10 min first run)...
echo        vectorbt, numba are large — please wait.
echo.
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Some packages failed to install.
    echo.
    echo Common fixes:
    echo   - Check internet connection
    echo   - Disable antivirus temporarily
    echo   - Re-run this script
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete!
echo   Run:
echo     .venv\Scripts\python.exe run_10x.py
echo     .venv\Scripts\python.exe ruthless_strategy_lab_10x.py
echo ============================================================
echo.
pause
