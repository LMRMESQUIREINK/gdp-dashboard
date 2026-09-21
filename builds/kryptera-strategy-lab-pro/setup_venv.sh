#!/usr/bin/env bash
# ============================================================
# Kryptera Strategy Lab — Setup Script (PRO build, macOS/Linux)
# ============================================================
# Mirrors setup_venv.bat: creates an isolated .venv in this folder,
# does NOT touch any system Python packages. Run this ONCE.
# ============================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo
echo "============================================================"
echo "  Kryptera Strategy Lab — Setup (Pro)"
echo "============================================================"
echo

PYTHON=""
for candidate in python3.11 python3.10 python3.9 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python not found."
    echo
    echo "Install Python 3.9-3.11 from https://www.python.org/downloads/"
    echo "(or via your OS package manager / pyenv) and re-run this script."
    exit 1
fi

echo "[1/4] Python found:"
"$PYTHON" --version
echo "       Path: $(command -v "$PYTHON")"
echo

echo "[2/4] Creating virtual environment (.venv)..."
if [ -d .venv ]; then
    echo "       .venv already exists - skipping."
else
    "$PYTHON" -m venv .venv
    echo "       Done."
fi
echo

echo "[3/4] Upgrading pip..."
.venv/bin/python -m pip install --upgrade pip --quiet
echo "       Done."
echo

echo "[4/4] Installing dependencies (5-10 min first run)..."
echo "       vectorbt, numba, matplotlib are large — please wait."
echo
if ! .venv/bin/pip install -r requirements.txt; then
    echo
    echo "[ERROR] Some packages failed to install."
    echo
    echo "Common fixes:"
    echo "  - Check internet connection"
    echo "  - Re-run this script"
    echo "  - On Apple Silicon, make sure you're on a native arm64 Python"
    echo "    (not Python running under Rosetta) if numba wheels fail"
    exit 1
fi

echo
echo "============================================================"
echo "  Setup complete!"
echo "  Run ./run_strategy.sh to start Kryptera Strategy Lab."
echo "============================================================"
