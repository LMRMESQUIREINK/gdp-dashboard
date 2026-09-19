#!/usr/bin/env bash
# ============================================================
# Trading Jarvis — Setup Script (macOS/Linux)
# ============================================================
# Creates an isolated .venv in this folder — does NOT touch any
# system Python packages, and does NOT use --break-system-packages.
# Run this ONCE.
# ============================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo
echo "============================================================"
echo "  Trading Jarvis — Setup"
echo "============================================================"
echo

PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python not found."
    echo "Install Python 3.10+ from https://www.python.org/downloads/ and re-run."
    exit 1
fi

echo "[1/3] Python found:"
"$PYTHON" --version
echo

echo "[2/3] Creating virtual environment (.venv)..."
if [ -d .venv ]; then
    echo "       .venv already exists - skipping."
else
    "$PYTHON" -m venv .venv
    echo "       Done."
fi
echo

echo "[3/3] Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt

echo
echo "============================================================"
echo "  Setup complete!"
echo "  Set your API keys, then run ./run_jarvis.sh"
echo "    export EODHD_API_KEY=\"your_key_here\""
echo "    export FMP_API_KEY=\"your_key_here\""
echo "    export ANTHROPIC_API_KEY=\"your_key_here\""
echo "============================================================"
