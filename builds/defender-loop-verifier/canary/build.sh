#!/usr/bin/env bash
# Compiles canary.c with AddressSanitizer, exactly as the source article does:
# -O1 (to actually exercise the dead-store hazard the __asm__ barrier guards
# against), frame pointers kept for readable traces, abort-on-error so a
# crash is a nonzero exit code the verifier can trust without parsing text.
set -euo pipefail
cd "$(dirname "$0")"
gcc -O1 -g -fsanitize=address -fno-omit-frame-pointer -o entry canary.c
echo "built: $(dirname "$0")/entry"
