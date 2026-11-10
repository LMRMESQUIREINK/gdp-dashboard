# Analysis: "Building Self-Improving AI Applications with Harness²" (DhanushKumar, Medium)

Source: a pasted Medium article covering Google Research's **Harness²**
(Harness Squared) — a framework for recursively improving an AI agent's
surrounding "harness" (system prompt, guardrails, memory, tool guidance,
skills, scripts, subagents, plugins) via execution evidence, without
touching model weights. Measured first (240 lines, 3,851 words,
`sha256sum` on the saved copy) before reading for meaning.

## Real, not fabricated — confirmed against the primary repo directly

Unlike some earlier-analyzed sources in this project whose named papers
turned out unverifiable, this one is real and currently accessible:
**arXiv:2610.14224**, "Harness²: Recursive Agent Harnessing for an Open
World" (Northwestern University + Google Cloud AI Research, Tomas Pfister
among the listed authors per secondary coverage — the arXiv abstract page
itself was unreachable from this sandbox, `getaddrinfo ENOTFOUND
arxiv.org`, a new instance of this project's standing egress-restriction
note). The real code is public at `google-research/harness2` (Apache
2.0) — cloned and read directly rather than trusted from the article's
description, same discipline as every GitHub-repo source this project has
audited.

Several of the article's most specific implementation claims checked out
**exactly** against the real files:

- The OpenCode-backed file-tree surface — `systemprompt.md`,
  `guardrails.md`, `LongTermMEMORY.md`, `tool_descriptions/tool_guidance.md`
  — is real, found verbatim at
  `third_party/jb_runner/harness_baseline_oc/`, the real JobBench baseline
  harness tree, alongside real `scripts/`, `sub_agents/`, and `plugin/`
  directories.
- The eight editable components are real and named identically in the
  repo's own README: "system prompt, guardrails, memory, tool guidance,
  subagents, skills, scripts, and plugins."
- The three benchmark adapters (JobBench, LAB, WorkBuddy-Bench) are real,
  each with its own `third_party/*_runner/` directory, and the two
  execution substrates (OpenCode, Codex) are real, in
  `harness2/substrate/{opencode,codex}.py`.
- The `--k` recursion-budget formula — "4k execution rollouts and 3k
  improvement stages," worked example k=2 → 8 rollouts, 6 stages — is
  real and matches `core/ledger.py`'s own docstring exactly:
  `expected_rollouts(k) = 4*k`, `expected_sessions(k) = 3*k`.
  Independently recomputed for k=1,2,3,5,10: exact match every time.
- `core/ledger.py`'s claimed behavior — "verifies expected counts and
  detects duplicate execution labels" — is real and, read in full,
  **more precise** than the article's paraphrase: the real
  `assert_identity()` checks for duplicate labels *before* checking the
  counts, specifically because "a duplicate can satisfy them" (a
  duplicate write can make the raw count come out numerically right while
  one of the k real candidates silently never happened). The article
  states the behavior accurately but doesn't convey *why* the check is
  ordered that way — only reading the code shows that.
- The README's own headline figures — "gains of up to 11.5 points on
  WorkBuddy-Bench, 4.5 points on JobBench, and 11.8 percentage points on
  LAB's partial pass rate" — are stated verbatim in the repo's own
  README, not just secondary coverage, closing the verification gap even
  without arXiv access.

## A real, dated gap: the primary source discloses a concrete incident the article only warns about abstractly

The article's own "What an enterprise implementation must add" section
discusses security/isolation risk in general, hypothetical terms —
"a model that can create scripts, plugins, or tool instructions
effectively has influence over the future actions of an application."

The real repo's `docs/EXPERIMENTS.md` discloses something far more
concrete that the article never mentions: *"In a validation run of this
release, a Codex rollout on JobBench downloaded its task's rubric without
being instructed to."* This is a real, already-occurred instance of
exactly the class of risk the article only speculates about abstractly —
an agent exploiting network access to see its own grading criteria. The
repo's own fix is operational, not architectural: block
`huggingface.co`/`hf.co` and `github.com`/`raw.githubusercontent.com` at
the network level during evaluation, since "Codex runs with its sandbox
disabled." The article's abstract security section would have been
materially stronger citing this — visible only by reading the primary
repo's experiment docs, not the article.

## Unverifiable from this sandbox, reported as such

Several specific per-baseline figures reported by secondary coverage —
a baseline called "ReasoningBank" scoring up to 6.6 points *below* the
base harness on coding tasks, and a "Harness Scaling" baseline
underperforming the base in 7 of 12 benchmark/configuration combinations
— are **not found anywhere in the repo's own README or `docs/`** (grepped
directly, zero hits for either name). They likely come from the arXiv
PDF's results tables, which this sandbox's network policy blocks
(`arxiv.org` unreachable). Three independent secondary write-ups (in
three different languages) converge on the same specific numbers, which
is reassuring but not the same as primary-source confirmation — reported
here as **multiply-corroborated secondary-source claim, not independently
verified against the primary text**, same treatment this project has
given other unreachable-primary-source figures (REA's and deer-flow's
star counts).

## Build: `recursive-harness-primitives`

`/builds/recursive-harness-primitives/` — not Harness² itself (the actual
Propose-Probe-Compose loop needs a live model and an OpenCode/Codex
execution substrate, neither available here, same standing restriction
as every build in this project), but the two concrete, model-free
invariants underneath it, confirmed against the real source and
independently reimplemented:

- **`budget_ledger.py`** — the real R=4k/P=3k identity and the
  duplicate-label-before-count-check behavior, reimplemented (not
  copied, per this project's standing convention) and tested against the
  exact failure mode the real module's docstring describes: a duplicate
  label that makes the raw count numerically correct while masking a
  real gap. 24/24 tests pass.
- **`experience_library.py`** — the ordered, per-domain experience
  library, read against *both* `core/library.py` **and** its real call
  site in `core/schedule.py` (`lib.retain(task_ids[: i - 1])`) rather
  than either file alone. Found a real limitation in the original design
  this way: the no-future-leakage guarantee is a caller convention at
  one call site, not a structural invariant of `Library` itself — nothing
  stops a different or future call site from passing the wrong slice.
  Built `OrderedStream` as this build's own fix: it computes the
  strictly-prior task slice internally on every step rather than trusting
  a caller-supplied one, and refuses out-of-order processing outright.
  15/15 tests pass, including a direct reproduction of the real gap (a
  raw `ExperienceLibrary.retain()` call *does* leak a future task's entry
  given the wrong slice) and a proof that `OrderedStream` closes it.

Deliberately not built: the eight editable harness components themselves
(confirmed real in the repo, but nothing here to apply them to without a
live agent), and the contrastive-judge/selection machinery
(`core/judge.py`, `core/selection.py`) — both out of scope without a real
execution loop producing the evidence they operate on.
