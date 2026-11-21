#!/usr/bin/env python3
"""
CLI for second-brain-toolkit.

Usage:
    python3 cli.py audit-prompt <instructions.txt>
    python3 cli.py lag-profile
"""
import json
import sys

from prompt_auditor import audit, summarize
from review_scheduler import weekly_lag_profile


def cmd_audit_prompt(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    findings = audit(text)
    symbols = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}
    for f in findings:
        print(f"[{symbols[f.status.value]}] {f.rule_id}: {f.detail}")

    counts = summarize(findings)
    print(f"\n{counts['pass']} pass, {counts['warn']} warn, {counts['fail']} fail")
    return 1 if counts["fail"] > 0 else 0


def cmd_lag_profile() -> int:
    print(json.dumps(weekly_lag_profile(), indent=2, default=str))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 cli.py audit-prompt <instructions.txt> | lag-profile", file=sys.stderr)
        return 2

    cmd = sys.argv[1]
    if cmd == "audit-prompt":
        if len(sys.argv) != 3:
            print("Usage: python3 cli.py audit-prompt <instructions.txt>", file=sys.stderr)
            return 2
        return cmd_audit_prompt(sys.argv[2])
    if cmd == "lag-profile":
        return cmd_lag_profile()

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
