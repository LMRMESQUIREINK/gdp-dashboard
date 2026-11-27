# gate-floor-checker

A dependency-free Python tool that tells "this candidate needs more
work" apart from "this gate can never pass as written" — built from a
real finding in [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd)'s
`evals/RESULTS.md`, analyzed in `/notes/week23-github-repos-analysis.md`.

## The gap this closes

That repository's eval harness scores a candidate against a weighted,
continuous rubric (Correctness/Autonomy/Actionability/Safety/Concision)
*and* an absolute veto rule: "it has no blocking findings." On its one
recorded run, the candidate improved on every weighted dimension and
more than halved its blocker count (7 → 3) — and the release gate still
reported **FAILED**, because the absolute rule doesn't care how much
better things got, only whether any blocker remains anywhere.

The repo's own `RESULTS.md` traces the failure precisely: two of the
three remaining blockers come from one test case (`agent-owned-edit`)
that is architecturally impossible to pass — the harness strips tool
access (`--tools ""`), so a criterion requiring the agent to "act on the
repository" can never be satisfied by any run, confirmed by reading the
fixture, not inferred from the trial count. The author states the
consequence directly: *"no candidate can ever pass while any blocker
survives anywhere in the case set, however much it improves."* That is
a property of the *gate's design*, not a verdict on the candidate — and
nothing in the repo (or any eval/scoring framework this project has
read, including its own `agent-readiness-scorecard` and
`ten-k-website-grader`) names that distinction as a thing to check for
before trusting a gate shaped this way. This tool is that check.

## Use

```python
from gate_floor_checker import CaseTrials, check_gate_floor

cases = [
    CaseTrials("happy-path", [False, False, False]),
    CaseTrials("broken-by-design", [True, True, False], known_structural=True),
    CaseTrials("real-regression", [True, False, False]),
]
report = check_gate_floor(cases)
print(report.summary())
```

- A case blocks the gate if **any** of its recorded trials drew a
  blocker (matching the real source's own semantics: N trials of one
  candidate, summed) — or if it's `known_structural`.
- `known_structural=True` is how a human who has actually confirmed an
  architectural cause (read the fixture, found the design flaw) records
  the *stronger* claim the source itself makes — a trial-based
  `never_cleared` check alone is evidence, never proof, especially at
  three trials with per-case standard deviations the source's own
  numbers show reaching 0.95.
- `check_gate_floor` returns `PASS`, `FAIL_IMPROVABLE` (every blocking
  case has cleared at least once — more trials or real fixes could
  plausibly close the gap), or `FAIL_STRUCTURAL` (at least one blocking
  case has never once cleared, confirmed or empirical) — with a
  recursive `excluding_never_cleared` sub-report showing what the
  verdict would be with the structural cases set aside, so a structural
  failure doesn't hide a real, improvable regression sitting underneath
  it (exactly what happened in the source: excluding the unpassable
  case still left the gate failing, on the same rule, for a genuine
  reason).

## Proven

```bash
python3 test_gate_floor_checker.py
```

**30/30 assertions pass**, including a reconstruction of the real
published `ayghri/i-have-adhd` numbers — 14 cases, 3 trials, baseline 7
blockers / candidate 3, `agent-owned-edit` architecturally confirmed
unpassable, `partial-success` the one real regression — that reproduces
the source's own conclusions exactly: `check_gate_floor` on the full
case set returns `FAIL_STRUCTURAL`; excluding the confirmed-structural
case returns `FAIL_IMPROVABLE`, not `PASS`, matching the source's own
"the gate still fails, on the same rule" finding precisely.

**What's reconstructed vs. stated exactly**, documented in the test
file itself: the total blocker counts and which case caused which
portion are stated exactly in `RESULTS.md`'s own prose; the precise
per-trial pattern for `agent-owned-edit` is not published in full (the
source says "most trials," not an exact matrix) and is reconstructed to
match every number that *is* published, with the architectural claim
carried by `known_structural` rather than faked into an invented 3-of-3
trial pattern.

**A real design gap found and fixed while building this, not a bug in
test code**: the first draft modeled "is this case blocking right now"
as "did its *most recent* trial block," with a `known_structural` flag
that only mattered if that one trial also happened to block. Writing
the real-data reconstruction surfaced two problems with that design:
(1) it doesn't match the source's own semantics at all — the real
harness runs N trials of *one* candidate and sums blockers across the
whole batch, not a timeline of successive candidates — and (2) under
that wrong model, a `known_structural` case whose single sampled trial
happened to read clean would be reported as passing, silently
discarding the stronger confirmed fact in favor of one trial's noise.
Fixed by dropping the single-trial-index model entirely: a case now
blocks if *any* recorded trial blocked, and `known_structural` always
counts as blocking regardless of what the trial data shows — caught by
the real-data test actually failing against the true source numbers,
not by re-reading the code.

## What's not built here

- No eval harness of its own — this tool consumes a case/trial outcome
  table already produced by some other scorer (the real source's own
  harness, or any rubric-plus-veto-rule design shaped like it), not a
  replacement for one.
- No automatic `known_structural` detection — confirming an
  architectural cause (reading a fixture, a flag, a design doc) is
  exactly the judgement call this tool deliberately leaves to a human,
  the same way the real source's own author did.
