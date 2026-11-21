#!/usr/bin/env python3
"""
CLI for provisional-data-gate.

Usage:
    python3 cli.py check <results.json> <claims.json>

results.json: a JSON file using the {"v": ..., "provisional": ...} leaf
              convention (e.g. transportive-ai's real results/eval.json).
claims.json:  [{"claim_id": "...", "text": "...", "path": "dotted.path",
                "disclosed": false}, ...]
"""
import json
import sys

from provisional_gate import Claim, get_path, load_leaf_tree, publish_check


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] != "check":
        print("Usage: python3 cli.py check <results.json> <claims.json>", file=sys.stderr)
        return 2

    results_path, claims_path = sys.argv[2], sys.argv[3]

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            results_raw = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {results_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Malformed results JSON: {e}", file=sys.stderr)
        return 1

    try:
        with open(claims_path, "r", encoding="utf-8") as f:
            claims_raw = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {claims_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Malformed claims JSON: {e}", file=sys.stderr)
        return 1

    tree = load_leaf_tree(results_raw)
    disclosed = {c["claim_id"] for c in claims_raw if c.get("disclosed")}

    try:
        claims = [Claim(c["claim_id"], c["text"], get_path(tree, c["path"])) for c in claims_raw]
    except KeyError as e:
        print(f"Malformed input: {e}", file=sys.stderr)
        return 1

    violations = publish_check(claims, disclosed)
    if not violations:
        print("Clean -- every provisional claim has a matching disclosure.")
        return 0

    for v in violations:
        print(f"[UNDISCLOSED] {v.claim_id}: {v.text}\n  {v.detail}")
    print(f"\n{len(violations)} undisclosed provisional claim(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
