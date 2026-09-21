@echo off
:: ============================================================
:: Kryptera Strategy Lab — Strategy Generator (PRO build)
:: Launch Script (Windows)
:: ============================================================
:: Runs the strategy generator inside the isolated .venv.
:: Make sure you have run "setup_venv.bat" at least once first.
:: ============================================================

title Kryptera Strategy Lab — Running
cd /d %~dp0

echo.
echo ============================================================
echo   Kryptera Strategy Lab — Pro — Launching...
echo ============================================================
echo.

if not exist .venv (
    echo [ERROR] Virtual environment not found.
    echo.
    echo Please run "setup_venv.bat" first to install dependencies.
    echo.
    pause
    exit /b 1
)

if not exist strategy_generator_pro.py (
    echo [ERROR] Strategy script not found in this folder.
    echo.
    echo Make sure all files are kept in the same folder:
    echo   - strategy_generator_pro.py
    echo   - requirements.txt
    echo   - setup_venv.bat
    echo   - run_strategy.bat
    echo.
    pause
    exit /b 1
)

echo Starting strategy generator...
echo The generator will search until a strategy beats its benchmark in all
echo 3 phases, or the attempt cap is reached. This may take several minutes.
echo Edit the CONFIG block at the top of strategy_generator_pro.py to change
echo the ticker/dates, or pass flags — run with --help to see them.
echo Press Ctrl+C at any time to stop.
echo.
echo ------------------------------------------------------------
echo.

.venv\Scripts\python.exe strategy_generator_pro.py %*

echo.
echo ------------------------------------------------------------
echo   Script finished.
echo   A discovered_strategy_*.py snapshot and an equity_curve_*.html
echo   file (if a strategy passed) were saved in this folder.
echo ============================================================
echo.
pause
