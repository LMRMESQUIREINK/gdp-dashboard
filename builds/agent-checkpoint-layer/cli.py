"""
CLI driving the checkpointed workflow across separate process
invocations — each command below is its own real process exit, so the
only thing carrying state between them is the SQLite file (see
checkpoint/store.py). Mirrors the article's own description of a human
approving mid-workflow on their own timeline: `approve` can run minutes,
hours, or (as in test_checkpoint.py) in a completely different process
than `start` or `resume`.

    python3 cli.py start --tier 50K --symbol ES --contracts 2
    python3 cli.py approve <run_id>
    python3 cli.py resume <run_id>
    python3 cli.py status <run_id>
"""
from __future__ import annotations

import argparse
import json
import sys

from checkpoint.store import CheckpointStore
from workflow import advance, create

DEFAULT_DB = "runs.db"


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("--tier", required=True)
    p_start.add_argument("--symbol", default="ES")
    p_start.add_argument("--contracts", type=int, required=True)
    p_start.add_argument("--db", default=DEFAULT_DB)
    p_start.add_argument("--crash-after-stage", default=None,
                          help="test-only crash injection — see workflow.advance()")

    p_approve = sub.add_parser("approve")
    p_approve.add_argument("run_id")
    p_approve.add_argument("--db", default=DEFAULT_DB)

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("run_id")
    p_resume.add_argument("--db", default=DEFAULT_DB)
    p_resume.add_argument("--crash-after-stage", default=None,
                           help="test-only crash injection — see workflow.advance()")

    p_status = sub.add_parser("status")
    p_status.add_argument("run_id")
    p_status.add_argument("--db", default=DEFAULT_DB)

    args = parser.parse_args()
    store = CheckpointStore(args.db)

    if args.command == "start":
        run_id = create(store, tier=args.tier, symbol=args.symbol, contracts=args.contracts)
        print(json.dumps({"run_id": run_id, "created": True}))
        sys.stdout.flush()
        result = advance(store, run_id, crash_after_stage=args.crash_after_stage)
        print(json.dumps(result, default=str))

    elif args.command == "approve":
        store.grant_approval(args.run_id, note="approved via cli")
        print(json.dumps({"run_id": args.run_id, "approved": True}))

    elif args.command == "resume":
        result = advance(store, args.run_id, crash_after_stage=args.crash_after_stage)
        print(json.dumps(result, default=str))

    elif args.command == "status":
        state = store.load(args.run_id)
        if state is None:
            print(json.dumps({"error": "not found"}))
            sys.exit(1)
        print(json.dumps({"run_id": state.run_id, "stage": state.stage, "status": state.status,
                           "context": state.context}))

    store.close()


if __name__ == "__main__":
    main()
