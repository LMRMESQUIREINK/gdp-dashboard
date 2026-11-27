# recursive-harness-primitives

Two real, independently reimplemented mechanisms from Google Research's
**Harness²** (`google-research/harness2`, Apache 2.0, arXiv:2610.14224) —
not the vendor's own OpenCode/Codex-coupled recursive-harness-optimization
framework itself (which needs a live model and an execution substrate
neither of which exist in this sandbox), but the two concrete, fully
verifiable, model-free invariants underneath it. Analyzed in
`/notes/harness2-recursive-agent-optimization-analysis.md`.

## What's real here, and what it's built from

Both modules were built by reading the real source files in full
(`core/ledger.py`, `core/library.py`, and the real call site in
`core/schedule.py`) — not copied verbatim (Apache 2.0 would permit that,
but this project's standing convention, same as `go-buildinfo-extractor`
and `run-terminal-ledger`, is an independent implementation built from
understanding the invariant, so a shared bug in the original isn't
silently inherited and the reference stays a genuine comparison point).

### `budget_ledger.py` — the R=4k/P=3k budget identity + duplicate-label detection

Confirmed directly against the real `core/ledger.py`: for a recursion
budget `k`, one correct mode/task run produces exactly R = 4k execution
rollouts and P = 3k improvement stages. The real module's own
`assert_identity()` checks for duplicate rollout/session labels **before**
checking the counts — because a duplicate write can make the raw count
come out numerically correct while actually meaning two stages wrote the
same run id and one candidate the ledger thinks exists was never really
produced. That ordering (and that exact failure mode) is reproduced here,
not simplified away — it's the entire reason the check exists.

### `experience_library.py` — the ordered, per-domain experience library

Confirmed against the real `core/library.py` **and** its real call site in
`core/schedule.py`: `Library.retain(task_ids)` keeps only the given task
ids. The real sweep loop calls `lib.retain(task_ids[: i - 1])` before every
task `i`, so a task only ever sees experience from strictly-earlier tasks —
never one that hasn't run yet.

**A real limitation found while reading both files together, not assumed
from either one alone**: the real `Library.retain()` trusts whatever task-id
list it's handed — it has no idea what order tasks actually run in. The
no-future-leakage guarantee is correctly implemented at the one real call
site in `schedule.py`, but it's a **caller convention**, not a structural
invariant of `Library` itself. A different or future call site with the
slicing even slightly wrong (`task_ids[:i]` instead of `task_ids[:i - 1]`,
say) would silently violate the guarantee with no error raised anywhere.

This build's own addition, not in the original: `OrderedStream` wraps an
`ExperienceLibrary` with a fixed `task_order` and makes the guarantee
structural — it computes `task_order[:index]` **itself** on every step,
never trusting a caller-supplied slice, and refuses (`OutOfOrderError`) to
process a task out of its declared order at all.

## Proven

```bash
python3 test_budget_ledger.py       # 24/24
python3 test_experience_library.py  # 15/15
```

`test_budget_ledger.py` includes the one test that matters most: a ledger
with a duplicate rollout label whose **raw count still matches** 4k exactly
(`R == 4` with only 3 real distinct rollouts, one double-recorded) — proving
`assert_identity()` catches the exact failure mode the real module's own
docstring describes, not just an obviously-wrong count.

`test_experience_library.py` proves the found limitation two ways: (1) a
direct `ExperienceLibrary.retain()` call, given the wrong task-id slice
(including a task that hasn't "happened" yet relative to the one being
processed), **does** leak that future task's entry — reproducing the real
design's real gap, not a strawman; (2) `OrderedStream` refuses the same
attack by construction, and separately refuses out-of-order `run()` calls
and duplicate task ids in `task_order` at construction time.

## What's deliberately not built here

- **Propose–Probe–Compose itself** — the actual harness-editing/execution
  loop needs a live model and an execution substrate (OpenCode or Codex in
  the real release); neither exists in this sandbox, same standing
  no-live-model-access restriction as every other build in this project.
- **The eight editable harness components** (system prompt, guardrails,
  memory, tool guidance, skills, scripts, subagents, plugins) — confirmed
  real and present in the repo's own `third_party/jb_runner/harness_baseline_oc/`
  baseline tree, but there's no agent here to apply them to.
- **The contrastive-judge/selection machinery** (`core/judge.py`,
  `core/selection.py`) — scores candidate harnesses from execution
  evidence; out of scope without a real execution loop producing that
  evidence.

Both pieces built here are the load-bearing correctness primitives a
real Harness²-style system needs regardless of model or substrate —
usable standalone by anyone building their own recursion-budget
accounting or ordered cross-task experience retention, independent of
Google's own OpenCode/Codex-specific implementation.
