# Analysis: Week 23 — 5 GitHub Repositories Every Developer Should Know in 2026

Source: "Week 23: 5 GitHub Repositories Every Developer Should Know in
2026" (vijayasekhardeepak.com) — the same newsletter series this project
has now analyzed three times (Week 19/20, Week 21, now Week 23). Five
repos covered: `ayghri/i-have-adhd`, `outline/outline`,
`bradautomates/claude-video`, `immich-app/immich`, `antirez/ds4`. All
five cloned and confirmed real (`git clone --depth 1`, each a genuine,
populated repository).

## What checked out

- **Outline's license claim is precise and verbatim-accurate.** The
  article says Business Source License 1.1, a "Document Service" use
  restriction, and a stated future change to Apache 2.0 — the real
  `LICENSE` file matches exactly: `Change Date: 2030-10-23`,
  `Change License: Apache License, Version 2.0`, and the "Document
  Service" clause word-for-word ("a commercial offering that allows
  third parties... to access the functionality of the Licensed Work").
- **Immich's AGPL-3.0 license and "3-2-1 backup" recommendation both
  check out exactly** — the real README's own warning banner uses the
  phrase "3-2-1" and links the same Backblaze explainer the article
  implicitly references, confirmed in three separate places in the real
  docs (`README.md`, `docs/docs/partials/_server-backup.md`,
  `docs/docs/administration/backup-and-restore.md`).
- **`claude-video`'s privacy/engine description is accurate and
  precise**: the real README confirms the Gemini engine uploads video
  to Google (deleted after the answer, or expiring within 48 hours),
  the local engine stays on-device, and WhisperX/Groq/OpenAI are real,
  correctly-described transcription fallback options — matching the
  article's "the Gemini workflow uploads video to Google's service...
  Cloud transcription providers may receive audio when used as a
  fallback" closely.

## A real, direction-stated gap: ds4's article description undercounts the real model list

The article states ds4 supports "DeepSeek V4 Flash... selected versions
of GLM 5.2 and, on very high-memory systems, DeepSeek V4 Pro." The real
README names more: **DeepSeek V4.1 Flash**, **GLM 5.3** (in addition to
5.2), **GLM 5.3 Flash**, and **Qwen3.8 Flash Next** — four named
models/variants the article never mentions. The "96 GB" figure is also
more specific in the source than the article's framing suggests: the
real README ties 96 GB specifically to DeepSeek/GLM, while Qwen3.8 Flash
Next needs only 64 GB — the article's "primary Apple Silicon target...
at least 96 GB" reads as a flat minimum where the source states a
per-model floor. This is an understatement, not an inflation — stated
plainly, per this project's "check which way an error runs" discipline,
since the two directions are different findings about different things.

## The strongest finding: i-have-adhd's own eval harness reports a FAILED release gate, and the article never mentions it

`ayghri/i-have-adhd` ships a real, rigorous eval harness
(`evals/RESULTS.md`) with one recorded run: 14 cases, 3 trials each, a
weighted rubric (Correctness 35% / Autonomy 25% / Actionability 20% /
Safety 10% / Concision 10%), and an absolute veto rule — "it has no
blocking findings." The real numbers: the candidate improved on **every
single weighted dimension** (weighted score 4.045 → 4.473) and more than
halved its blocker count (7 → 3) — and the release gate still reads
**"Release gate: FAILED."**

The source's own `RESULTS.md` explains why with real precision: two of
the three remaining blockers come from one case (`agent-owned-edit`)
that is architecturally impossible to pass — the harness runs with
`--tools ""`, so a criterion requiring the agent to "act on the
repository instead of delegating the edit back to the user" can never
be satisfied by any run, confirmed by reading the fixture, not guessed
from the trial count. The author states the consequence directly: *"as
written, no candidate can ever pass while any blocker survives anywhere
in the case set, however much it improves."* The remaining single
blocker is a real, honestly-flagged regression (`partial-success`,
−0.63 mean, directionally consistent across all three trials) with a
plausible, explicitly-labeled-as-unconfirmed mechanism.

This is the single most rigorous, most self-critical piece of material
analyzed across all three rounds of this newsletter series — and the
article's "Productivity impact" section for `i-have-adhd` never mentions
any of it, describing the project only as something that "changes the
response format." Not a criticism of the repo, which is a model of
transparent self-evaluation; a real, checkable gap in the article, which
skips past the one part of the source that's both most interesting and
most load-bearing for anyone deciding whether to adopt it.

## Build: `gate-floor-checker`

`/builds/gate-floor-checker/` generalizes the i-have-adhd finding into a
reusable mechanism: given a set of cases with per-trial pass/fail
outcomes (plus an optional `known_structural` flag for an
architecturally-confirmed case), classify a failing absolute gate as
`FAIL_IMPROVABLE` (real signal, more work could close it) or
`FAIL_STRUCTURAL` (at least one case has never once cleared, so no
amount of re-running the *candidate* alone can satisfy the rule) — with
a recursive "excluding the structural cases" sub-report, so a structural
failure can't mask a real regression sitting underneath it. This fills a
genuinely new gap in this project's own tooling: `agent-readiness-
scorecard`, `ten-k-website-grader`, and `paired-bootstrap-ratchet` all
score or gate something, but none of them distinguish "this check can
never pass as currently specified" from "this candidate isn't good
enough yet," which is exactly the distinction the i-have-adhd author
had to work out by hand and document in prose.

30/30 tests pass, including a full reconstruction of the real published
i-have-adhd numbers reproducing both of the source's own conclusions
exactly (`FAIL_STRUCTURAL` on the full case set; `FAIL_IMPROVABLE`, not
`PASS`, once the confirmed-structural case is excluded — matching "the
gate still fails, on the same rule"). **A real design gap found and
fixed while building it, not a synthetic test bug**: the first draft
modeled gate-blocking as "did the most recent trial block," which both
didn't match the source's actual N-trials-of-one-candidate semantics
and would have silently let a `known_structural` case pass if its one
sampled trial happened to read clean — caught by the real-data test
actually failing against the true numbers, fixed by switching to "any
recorded trial blocked" and making `known_structural` always count
regardless of trial data.
