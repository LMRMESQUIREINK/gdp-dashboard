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

`approve`/`resume` both take an optional `--mandate-db` -- when given,
`approve` ALSO grants a durable Mandate (checkpoint/mandate.py) recording
the run's context at that exact moment, and `resume` revalidates it
against whatever the CURRENT prop-firm rules say before letting the
approval-gated stage run. Omitting `--mandate-db` (the default) is the
original behavior from before this flag existed: the boolean approval
flag alone decides, with no revalidation at all.
"""
from __future__ import annotations

import argparse
import json
import sys

from checkpoint.mandate import MandateStore
from checkpoint.store import CheckpointStore
from workflow import advance, create, grant_approval_mandate

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
    p_approve.add_argument("--mandate-db", default=None,
                            help="also grant a durable, revalidated-on-resume Mandate — see checkpoint/mandate.py")

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("run_id")
    p_resume.add_argument("--db", default=DEFAULT_DB)
    p_resume.add_argument("--crash-after-stage", default=None,
                           help="test-only crash injection — see workflow.advance()")
    p_resume.add_argument("--mandate-db", default=None,
                           help="revalidate this run's Mandate against current rules before resuming — see checkpoint/mandate.py")

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
        mandate_id = None
        if args.mandate_db:
            mandate_store = MandateStore(args.mandate_db)
            mandate_id = grant_approval_mandate(store, mandate_store, args.run_id)
            mandate_store.close()
        print(json.dumps({"run_id": args.run_id, "approved": True, "mandate_id": mandate_id}))

    elif args.command == "resume":
        mandate_store = MandateStore(args.mandate_db) if args.mandate_db else None
        result = advance(store, args.run_id, crash_after_stage=args.crash_after_stage,
                          mandate_store=mandate_store)
        if mandate_store is not None:
            mandate_store.close()
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
