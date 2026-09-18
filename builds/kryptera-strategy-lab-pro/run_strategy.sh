#!/usr/bin/env bash
# ============================================================
# Kryptera Strategy Lab — Strategy Generator (PRO build)
# Launch Script (macOS/Linux)
# ============================================================
# Runs the strategy generator inside the isolated .venv.
# Make sure you have run "./setup_venv.sh" at least once first.
# ============================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo
echo "============================================================"
echo "  Kryptera Strategy Lab — Pro — Launching..."
echo "============================================================"
echo

if [ ! -d .venv ]; then
    echo "[ERROR] Virtual environment not found."
    echo
    echo "Please run './setup_venv.sh' first to install dependencies."
    exit 1
fi

if [ ! -f strategy_generator_pro.py ]; then
    echo "[ERROR] Strategy script not found in this folder."
    echo
    echo "Make sure all files are kept in the same folder:"
    echo "  - strategy_generator_pro.py"
    echo "  - requirements.txt"
    echo "  - setup_venv.sh"
    echo "  - run_strategy.sh"
    exit 1
fi

echo "Starting strategy generator..."
echo "The generator will search until a strategy beats its benchmark in all"
echo "3 phases, or the attempt cap is reached. This may take several minutes."
echo "Edit the CONFIG block at the top of strategy_generator_pro.py to change"
echo "the ticker/dates, or pass flags — run with --help to see them."
echo "Press Ctrl+C at any time to stop."
echo
echo "------------------------------------------------------------"
echo

.venv/bin/python strategy_generator_pro.py "$@"

echo
echo "------------------------------------------------------------"
echo "  Script finished."
echo "  A discovered_strategy_*.py snapshot and an equity_curve_*.html"
echo "  file (if a strategy passed) were saved in this folder."
echo "============================================================"
