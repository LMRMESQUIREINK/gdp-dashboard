#!/usr/bin/env bash
# ============================================================
# Trading Jarvis — Launch Script (macOS/Linux)
# ============================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d .venv ]; then
    echo "[ERROR] Virtual environment not found. Run ./setup_venv.sh first."
    exit 1
fi

echo "============================================================"
echo "  Trading Jarvis"
echo "============================================================"
echo "  python run_strategy.py <SYMBOL>              one-shot check"
echo "  python run_strategy.py <SYMBOL> --monitor     live monitor"
echo "  python run_strategy.py --ask \"...\"            Jarvis NL mode"
echo "============================================================"
echo

.venv/bin/python run_strategy.py "$@"
