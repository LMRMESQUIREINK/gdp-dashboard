@echo off
:: ============================================================
:: Trading Jarvis — Launch Script (Windows)
:: ============================================================
cd /d %~dp0

if not exist .venv (
    echo [ERROR] Virtual environment not found. Run setup_venv.bat first.
    pause
    exit /b 1
)

echo ============================================================
echo   Trading Jarvis
echo ============================================================
echo   python run_strategy.py SYMBOL              one-shot check
echo   python run_strategy.py SYMBOL --monitor     live monitor
echo   python run_strategy.py --ask "..."           Jarvis NL mode
echo ============================================================
echo.

.venv\Scripts\python.exe run_strategy.py %*
pause
