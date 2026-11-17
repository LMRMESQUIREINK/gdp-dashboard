# Fingerprinted Ledger + Pre-Registration

Two small, dependency-free Python modules extracted from
`FareedKhan-dev/dynamic-workflow-agents` (a real two-edition — Claude and
Qwen — notebook build of a lead-agent/parallel-worker runtime, audited for
real against a 72-planted-bug code library). Not a port of the notebook's
own runtime, which needs a live model and a real code corpus to mean
anything — these two mechanisms, read directly from the real source and
independently reimplemented, generalize cleanly without either:

1. **`ledger.py` — `FingerprintedLedger`.** One SQLite table, keyed by a
   SHA-256 fingerprint of the normalized request (model + messages +
   params + an explicit sample index, so a deliberate repeat gets its own
   slot), gives three properties for free: a cache (don't pay twice for
   the same question), a replay source (run the same notebook offline and
   get the same answers), and a resume journal (a crash just means asking
   the same questions again — everything already answered comes back
   instantly, only the gap costs anything). Three modes: `collect` (call
   live on a genuine miss, cache it), `replay` (serve cache only, raise
   `LedgerMiss` rather than silently falling back to a live call), `smoke`
   (never touches the ledger at all).

2. **`prereg.py` — `Preregistration` + `resume_holds()`.** A hash-locked
   pre-registered hypothesis set: the rules are fixed and SHA-256'd before
   any result exists, and `verify_unchanged()` refuses to decide anything
   if the rule set drifted after the fact — a real anti-p-hacking guard,
   not a cosmetic one. `decide()` turns a boolean into SUPPORTED/NOT
   SUPPORTED/REPORTED (`None` holds means "no comparison exists this run,"
   reported rather than forced into a verdict).

## The real finding this build operationalizes

Verifying the source round, every one of its headline numbers checked out
to the decimal against the real committed artifacts (`exp_main.json`'s
recall/precision figures, the 856/98,028 and 849/97,269 file/line corpus
counts matched against the actual files on disk, the homework and intents
numbers) — the most precisely verifiable source this project has analyzed.
One hypothesis, **H8** ("a crashed run resumes without paying twice"), is
marked **NOT SUPPORTED in both editions** — `exp_claims.json` records
"paid 0 + 0 = 56 calls; same report: True" for Claude and "paid 0 + 1 = 20
calls; same report: True" for Qwen. Read casually, both of those look like
a pass: the report matched, nothing was visibly double-charged. The
notebook's own pre-registered rule is stricter than that, and it's stricter
for a good reason, confirmed by reading the real `decide("H8", H8["holds"],
...)` call site: `H8["holds"]` requires `paid_crash + paid_resume ==
total`, not just "the outcome matched." In both recorded runs,
`paid_crash + paid_resume` is 0 — the whole crash-then-resume sequence was
answered entirely from a pre-populated cache, with zero fresh evidence on
either side of the simulated crash. A naive "did it work" check would have
passed this; the real rule correctly refuses to, because a fully-cached
replay proves nothing about whether a genuinely interrupted, genuinely
resumed run avoids double payment. The source's own README's "Read the
numbers with their limits" section names H6 and H7 as the hypotheses that
"did not meet their stated rules in either edition" — it never mentions
H8, even though H8 fails the same way, for the same reason, in both
editions. `resume_holds()` is that exact rule, generalized, with the real
Claude and Qwen numbers as permanent regression tests proving it still
catches this specific gap.

## Checked against `/builds/` first

`agent-checkpoint-layer/` does stage-level checkpoint/pause/resume with a
WAL table, not call-level request caching. `run-terminal-ledger/` is an
idempotent singleton-confirmation protocol for a run's terminal status, a
different concern entirely. Neither implements "one fingerprinted table
gives cache+replay+resume for free," and neither has anything like the
hash-locked pre-registration guard.

## Proven

27/27 tests across `test_ledger.py` and `test_prereg.py`, including:
cross-process persistence (a fresh `FingerprintedLedger` instance against
the same file sees prior writes — not two in-process objects sharing one
Python process); replay mode genuinely never falls back to a live call on
a miss (asserted by a live-call counter, not just by not raising); the
hash lock catching both a changed claim and an added hypothesis; and the
`resume_holds()` suite reproducing the real Claude and Qwen H8 numbers
exactly (correctly fails), the source's own toy S28 demo numbers exactly
(correctly passes), a genuine double-charge (correctly fails), and a
run that never actually crashed (correctly fails regardless of the
accounting).

## Deliberately not built

The notebook's actual lead/worker/runtime (needs a live Anthropic or
ModelScope key and a real multi-hour run to mean anything — this
sandbox has no live access to either, the same standing restriction as
every build here), the paired-bootstrap statistics behind the recall/
precision intervals (this project already has a real paired-bootstrap
significance gate in `/builds/paired-bootstrap-ratchet/`, built from a
different Fareed Khan source, and duplicating it here would add nothing),
and the 72-bug planted-fault benchmark itself (specific to that one
algorithm corpus, not a generalizable mechanism).
