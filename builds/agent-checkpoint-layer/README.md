# agent-checkpoint-layer

A real, durable checkpoint/pause/resume layer — the one piece of an
agentic-harness framework an uploaded survey article calls non-negotiable
("this logic of managing workflow pausing, resuming and checkpointing is
very complex and MUST be there") that this project was actually missing.
Full critique of the source article in
`/notes/agentic-harness-frameworks-analysis.md`.

## The real gap this fills

`/builds/trading-jarvis/jarvis_swamp_bridge.py`'s `route_through_bus()`
hard-gates a risk-sizing step behind `approval_required=True` — but when
that gate isn't satisfied, it just raises a `GovernanceError` and the run
is gone. Nothing is saved. Nothing can be resumed. A crash, a restart, or
a human who wants to say "yes" an hour from now instead of right this
second all lose the entire workflow. Checked directly before writing
this: nothing anywhere in this repo persists workflow state across a
process boundary.

This build implements the source article's own six-step checkpoint
pattern literally, against a real multi-stage workflow shaped like
`jarvis_swamp_bridge.py`'s (built on the same already-proven
`prop_firm_sizing.py`/`prop_firm_position_sizing.py`, copied in
unmodified — same convention every other interface in this project
follows):

1. Persist the run's state and context under a UUID — `checkpoint/store.py`
2. Mint that UUID when the run is created — `workflow.create()`
3. Return a partial result when a human gate isn't satisfied — `advance()`'s `paused_for_approval`
4. Find the run later by its UUID — `CheckpointStore.load()`
5. Reinstate its state and context exactly as last saved — same method
6. Resume execution from that point, looping back to the same gate if still not approved

Two senses of "WAL" meet in `checkpoint/store.py`, on purpose: SQLite's
own write-ahead-log journal mode (`PRAGMA journal_mode=WAL`, enabled for
real) for crash-safe writes to the `.db` file itself, and an app-level
`wal` table — an append-only log of every stage transition a run goes
through — which is the article's own "Checkpoints & WALs" concept,
implemented as a real table rather than a loose analogy.

## Verification — real subprocess crash recovery, not a mocked one

```bash
python3 test_checkpoint.py
```

Every step spawns a genuine separate subprocess (`subprocess.run([...,
"cli.py", ...])`) — not a function call inside one long-lived process —
because the entire point is proving state survives a process boundary,
the same thing a real crash or restart would test. `workflow.py`'s
`--crash-after-stage` flag calls `os._exit(1)` right after a stage's
result is computed but *before* its checkpoint write — exactly what a
real `kill -9` does — so the recovery proven here is real, not simulated
by skipping a step in code.

Real output from this build:

```
=== a run pauses for approval with the suggestion already computed ===
  [PASS] run paused at finalize
  [PASS] risk_sizing result already computed and persisted
  [PASS] the over-25%-rule flag actually fired (2 contracts on 50K is over the limit)

=== resuming without approval stays paused, never silently proceeds ===
  [PASS] still paused_for_approval with no approval granted

=== approve in one process, resume in another, matches a direct evaluate_size() call ===
  [PASS] approval recorded
  [PASS] run completed
  [PASS] checkpointed risk_sizing result matches a direct evaluate_size() call
  [PASS] finalize suggestion reflects the over-limit flag

=== real crash recovery: os._exit after risk_sizing, before its checkpoint write ===
  [PASS] exactly one line printed before the crash (run_id only — advance() never returned)
  [PASS] the crashed stage's checkpoint was NOT written (stage is still signal_check)
  [PASS] the crashed stage's result is NOT in the persisted context either
  [PASS] resume recovers past the crash and reaches the approval gate
  [PASS] resuming an already-paused run twice is idempotent (same result both times)
  [PASS] post-crash-recovery run reaches the same final answer a direct call would, despite the crash

=== the WAL has a full, ordered history of this run — not just the latest snapshot ===
  [PASS] WAL records the full real sequence, including the crash gap and both pause cycles
  [PASS] signal_check appears only ONCE in the WAL (never recomputed after the crash — only risk_sizing, the stage that actually lost its checkpoint, was)

============================================================
ALL CHECKS PASSED
```

## A real bug this testing caught and fixed

Writing the crash-recovery test (not just the happy-path one) surfaced a
real bug: `advance()`'s "which stage did we actually last complete"
bookkeeping was computed once at the top of the function from where the
resume *started*, and never updated as the loop progressed. A resume that
completed more than one stage before hitting the next pause point would
record the *wrong* last-completed stage — harmless here only because
every stage happens to be a deterministic, side-effect-free recomputation;
in a workflow with a non-idempotent stage (sending a message, charging a
card), this bug would have made a resume silently re-run a stage it had
already completed, which is exactly the failure mode a checkpoint layer
exists to prevent. Fixed by tracking `last_completed` as a variable
updated inside the loop itself, not derived from the resume's starting
point. `test_checkpoint.py`'s WAL-ordering check (verifying `signal_check`
appears exactly once across the whole crash-and-recover sequence) is what
would catch a regression of this specific bug.

## Using it

```bash
python3 cli.py start --tier 50K --symbol ES --contracts 2   # prints run_id, pauses for approval
python3 cli.py status <run_id>                               # inspect the persisted state
python3 cli.py approve <run_id>                               # a human, any time later, in any process
python3 cli.py resume <run_id>                                # continues from exactly where it paused
```

## What's cut, and why

This implements the orchestration layer's checkpoint/pause/resume piece
only — not a new agentic framework. The source article's other four
layers (Tools, RAG, Observability, Cloud/model ecosystem) either already
have a real answer elsewhere in this project (Tools: the whole
`/builds/` directory; a thin slice of Observability: `audit.py` in
`/builds/prop-firm-mcp-server/`) or don't apply to a single local
codebase with no vector store and no multi-cloud deployment question
(RAG, Cloud) — stated as out of scope rather than padded in to look more
complete.
