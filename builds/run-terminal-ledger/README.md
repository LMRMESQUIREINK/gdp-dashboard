# Run Terminal Ledger

A standalone, dependency-free Python reimplementation of one specific
mechanism from [`bytedance/deer-flow`](https://github.com/bytedance/deer-flow)
("DeerFlow 2.0" — a large, real, actively-maintained open-source agent
harness): the **authoritative run-terminal-outcome protocol**, read from the
real source
(`backend/packages/harness/deerflow/runtime/events/terminal.py`,
`backend/docs/RUN_EVENT_STREAM.md`), not guessed from docs prose. Full
analysis in `/notes/deer-flow-analysis.md`.

## The property this protects

A long-running agent run has exactly one true final outcome —
`success`/`error`/`interrupted`/`timeout`. But two different code paths can
each believe they're the one allowed to record it: the Worker that actually
ran it, and a separate recovery process that takes over after a crash. If
both are allowed to write, or a Worker retries a lost acknowledgement and
writes twice, the ledger can end up with two contradictory "final" rows for
one run. DeerFlow's real implementation makes that structurally impossible
with two mechanisms, both reimplemented here:

1. **Idempotent singleton confirmation** — the terminal row is confirmed
   through an atomic check-and-insert (`put_if_absent`). A retried call
   (lost ACK) sees `CONFIRMED_EXISTING`, not an error and not a second row. A
   call with a *different* status than the one already on record sees
   `CONFLICT` and never overwrites the original.
2. **One-shot recovery takeover** — a recovery process may publish an
   `error` terminal only by first presenting proof it won an atomic
   claim-for-takeover elsewhere (`claimed=True`); the resulting
   `RecoveryTarget` can be consumed exactly once, and a stale target issued
   before the run's parent record was deleted is rejected by a lifecycle
   guard rather than resurrecting an orphan event.

## What's reimplemented vs. cut

Reimplemented faithfully: the four confirmation outcomes
(`CONFIRMED_NEW`/`CONFIRMED_EXISTING`/`CONFLICT`/`UNKNOWN`), the bounded
2-attempt retry for a lost ACK, the `authorized()` check before and after the
write, the lifecycle guard hook, the one-shot `RecoveryTarget` (immutable,
raises `RecoveryTargetConsumed` on double use), and the thread-global `seq`
watermark that survives a run's deletion (never reused) — all read directly
from the real DeerFlow source, not inferred.

Cut, deliberately: DeerFlow's real `DbRunEventStore` backs this with a full
Postgres/SQLite schema carrying the entire event envelope (`thread_id`,
`category`, `content`, `metadata`, `user_id`, multiple event types per run,
history/debug/subtask consumer projections) — this build narrows to just the
one `run.terminal` singleton and its watermark, because that's the specific
property being proven, not a port of DeerFlow's event system. DeerFlow's
in-memory store serializes `put_if_absent` with an `asyncio` per-thread lock;
this build uses SQLite's own `UNIQUE` constraint as the real atomic
guarantee instead (closer to what DeerFlow's own doc says the *database*
store must do for multi-process deployments: "JSONL only provides this
guarantee within one process; shared multi-process deployments must use the
database store").

## Proven

```bash
python3 test_run_terminal_ledger.py -v
```

**16/16 tests pass**, including:

- Idempotent retry (`CONFIRMED_EXISTING`), conflicting-status rejection
  (`CONFLICT`, original preserved), unauthorized-caller rejection, invalid
  status rejection, lifecycle-guard rejection.
- The seq watermark surviving a run's deletion without reuse, and being
  scoped per-thread rather than globally shared.
- Recovery takeover: no claim → no target; a successful claim → exactly one
  `recovered=True` error terminal; publishing a consumed target raises
  `RecoveryTargetConsumed`; two independently-"won" takeover claims for the
  same run still converge on one row; a target issued before the run's
  record was deleted is rejected rather than resurrecting it.
- **Real concurrency, not simulated**: 20 OS threads racing
  `confirm_terminal_event` for the same run (one status, and a second,
  harsher version where half the threads race a *different* status) —
  exactly one insert wins, every other caller sees a correctly-classified
  outcome, never two rows.
- **A real cross-process race**, found worth adding while reviewing this
  build's own first draft: the threaded test above shares one
  `TerminalLedger` instance across threads, so its own `threading.Lock`
  — not SQLite's `UNIQUE` constraint — was actually what prevented a double
  insert there, leaving the module's `sqlite3.IntegrityError` fallback
  branch unexercised despite being the one piece of code backing the
  module's central claim. Fixed by adding
  `TestCrossProcessConcurrency`, which forks 6 separate OS processes, each
  constructing its *own* `TerminalLedger` (and therefore its own,
  mutually-unaware lock) against the same SQLite file — the only thing
  that can still prevent a double insert there is the database-level
  constraint. Confirmed: exactly one insert wins, verified independently by
  a third connection counting rows after all six processes exit.

## What's verified about the source, not just read

- The real `terminal.py` confirmation function (`confirm_terminal_event`)
  and `RecoveryTerminalPublisher`/`RecoveryTerminalTarget` classes were read
  in full before writing this reimplementation — the four-outcome enum, the
  bounded two-attempt retry, the immutable one-shot target with a
  `threading.Lock`-guarded `_consume()`, and the `_matches()` validation
  (status, protocol version, `recovered` type, positive `seq`) all trace
  directly to that file.
- DeerFlow's own "ground-up rewrite, shares no code with v1" claim
  (`README.md`) was checked structurally, not taken on faith: the real
  `main-1.x` branch exists (451 files total, flat layout, no `backend/`,
  `frontend/`, or `skills/` split at all), and a direct path-overlap
  diff against `main` (4,389 files) found exactly 13 shared relative
  paths — every one of them repo boilerplate (`README.md`, `LICENSE`,
  `Makefile`, `.gitignore`, `.env.example`, `.github/workflows/
  container.yaml`, language-variant READMEs) and zero shared implementation
  code.
- The "#1 on GitHub Trending" claim (README, Feb 28 2026) is **self-reported
  and not independently confirmed** — a web search found the same wording
  mirrored on other sites and one undated blog post repeating the same
  "41,700 stars" figure, which is secondhand and undated, not a dated
  snapshot from a source independent of the project's own announcement.
  Reported here as such rather than repeated as fact.

## Not reimplemented, and why

- DeerFlow's full `RunEventStore` envelope (categories, message
  projections, `DbRunEventStore`'s `content_is_json` metadata markers) —
  out of scope; this build is about the terminal-outcome protocol alone.
- The "Evidence Ordering" barrier sequence from `RUN_EVENT_STREAM.md`
  (freeze/drain Journal producers, capture an Evidence Receipt's sequence
  boundary, persist an Evidence Seal before releasing the finalizing
  barrier) — read and understood, but it's about *when* a Worker is allowed
  to call confirmation, not the confirmation protocol itself; reimplementing
  it would mean building a synthetic Journal/evidence-producer system with
  nothing real behind it to test against.
- Postgres-specific behavior (DeerFlow's real production backend) — this
  build uses SQLite throughout; the `UNIQUE`-constraint-as-atomicity
  mechanism this build depends on is the same primitive Postgres provides,
  not a SQLite-only shortcut.
