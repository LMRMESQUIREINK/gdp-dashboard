# Deep analysis: four Fareed Khan "build an agentic X system" articles

Source: one upload carrying four full Medium-style build-tutorial
articles, three genuinely new to this project and one a repeat:

1. **"Building Fast Computer Agents to Solve Complex Tasks"** (interface
   lifting, repo `FareedKhan-dev/ai-pc`) — **a duplicate.** This exact
   article was already analyzed and built from earlier in this project —
   see `/notes/interface-lifting-fast-computer-agents-analysis.md` and
   `/builds/interface-lift-toolkit/`. Confirmed by title match before
   doing anything else, same "verify precisely before touching anything"
   discipline as every repeat-upload round in this project (the
   Addendum-4 Trading Jarvis revert, the `oss-ai-engineering-stack`
   Week 21 byte-identical re-upload). No new action taken on this one.
2. **"Building an Agentic Quantum Computing System"** (repo
   `FareedKhan-dev/agentic-quantum-computing`) — new.
3. **"Building an Agentic Security Pipeline That Finds, Proves, and
   Patches Vulnerabilities"** (repo referenced in-text as
   `agentic-quantum-computing.git`, almost certainly a copy-paste error
   in the article itself — the described project, `qadx`-unrelated tool
   registry + ASan canary, has nothing to do with quantum kernels; not
   independently resolvable from this sandbox, flagged as `source-is-
   silent` on the correct repo URL) — new.
4. **"Building a Week-Long Running Agentic System"** (repo
   `FareedKhan-dev/long-running-agent`) — new.

All three new pieces follow the same house style as the first (dense,
code-heavy, "here's what we're building, here's the code, here's the
real output") and the same standing limitation applies: this sandbox has
no live model API, no GPU, and (for the third) no Temporal server, so
nothing claiming a live run against those could be reproduced here.
Where a claim was independently checkable without those — compiling and
running real code, or checking a fact against an outside source — it was
checked, and the results below say which is which.

## Coverage — what this did not check

- No GPU in this sandbox: every H100/PennyLane/vLLM/Qwen3-14B number in
  the quantum article's "real run" output (0.9916 ROC-AUC, the 69-second
  kernel wall time, the per-seed sweep tables) is reported as the
  article's own stated output, `source-is-silent` on independent
  reproduction. Same for the security-pipeline article's vLLM/Qwen2.5-
  Coder-7B numbers and the long-running-agent article's Temporal/Claude-
  Opus trace.
- No Temporal server, no Docker, no E2B in this sandbox: the long-running-
  agent article's crash-and-replay demonstration, its durable-sleep
  timings, and its cost-ledger dollar figures are all `source-is-silent`
  here — the *mechanism* (continue-as-new, replay determinism) was
  checked against Temporal's own docs instead (see DEEPER).
- No HEP/fastjet/cargo-auditable-class deep dive this round: the
  quantum article's jet-clustering physics (anti-kT, dijet invariant
  mass) is reported as described, not independently derived.
- The security-pipeline article's own GitHub repo
  (`FareedKhan-dev/agentic-security-pipeline`, named in its text) was not
  cloned or read — only the pasted article text was audited.

## DEEP — what each new source is, measured by actually running the parts that don't need a GPU

**The dead-store hazard in the security-pipeline article's canary is
real, and was reproduced from scratch before trusting it.** The article
states that its `parse_alpha` function needs an `__asm__ volatile`
barrier because, without it, `gcc -O1` proves the destination buffer is
never read after the overflowing `memcpy` and deletes it as a dead
store — silently curing the bug at compile time. Built a minimal
10-line C repro independently (not copied from the article): a
`memcpy(buf, src, 64)` into an 8-byte heap buffer, compiled with
`-O1 -fsanitize=address`.
- **Without** the barrier: `gcc` emits `-Wstringop-overflow` at compile
  time but the compiled binary runs clean, exit 0 — no ASan crash. The
  optimizer really does remove the write.
- **With** the barrier (`__asm__ volatile("" : : "r"(buf) : "memory")`):
  identical binary now crashes correctly —
  `AddressSanitizer: heap-buffer-overflow ... WRITE of size 64`.

This is a genuinely useful, independently-reproducible engineering fact,
credited as such, and it is also the central mechanism of this round's
real build (`/builds/defender-loop-verifier/`), which hits the identical
hazard in its own `canary.c` and documents it the same way.

**The security-pipeline article's canonical worst-case finding — a
small open model voting a provably-crashing bug `FALSE_POSITIVE` with
95% confidence, three times out of three — reads as a genuine, specific,
falsifiable claim rather than a vague "small models are unreliable"
gesture**, because the article shows the actual prompt, the actual
tally, and states plainly that the deterministic re-detonation (not the
model) is what decided the verdict. That exact "never trust the claim,
always re-detonate" rule is what this round's build reproduces and
tests directly (see the build's README — two scripted agents, one
denying a real crash, one claiming a fake one, both outcomes unaffected
because the verifier never reads the self-report).

**The quantum article's central number — 0.9916 ROC-AUC for the quantum
kernel vs. 0.9580 for the best classical baseline on KDD — is presented
with real discipline about its own fragility**, not oversold: the
article itself runs the same 8-qubit setup across five seeds later in
the piece and shows the quantum kernel only wins on two of them (0.973
mean quantum AUC vs. a classical baseline that also moves around and
wins three of five races), explicitly stating "calling it a clean win
requires picking the right seed." That self-undercutting of its own
headline number, stated by the source itself rather than extracted by
this audit, is a credit — it's the opposite of the Factory.ai paper's
"10x code-gen ≈ +10% overall" claim flagged in an earlier round of this
project, which was asserted with no such caveat.

**The long-running-agent article's central durability claim — a mid-
task host reboot loses zero tokens and produces zero double-commits — is
architecturally sound, not just claimed:** Temporal's replay model
really does work this way (see DEEPER below), and the article's own
idempotency discipline (`_execute_cycle` always re-reads git state first
and returns a no-op if the checklist shows nothing actionable) is a
correct, checkable implementation pattern for making that replay safe,
independent of whether this exact trace was captured live.

## DEEPER — the frameworks, checked against outside sources

- **Credit** (quantum article): `lightning.gpu` is a real PennyLane
  device, a GPU state-vector simulator built on NVIDIA's cuQuantum SDK,
  confirmed via PennyLane's own docs and blog posts
  ([docs.pennylane.ai](https://docs.pennylane.ai/projects/lightning/en/latest/lightning_gpu/device.html),
  [pennylane.ai/devices/lightning-gpu](https://pennylane.ai/devices/lightning-gpu)).
  The vendor's own guidance recommends it for ~20+ qubit workloads and
  cites a single-GPU ceiling around 30–32 qubits — consistent with the
  article's own finding that its kernel's usefulness peaks around 8
  qubits and *degrades* past that from kernel concentration, a different
  failure mode than running out of GPU memory, correctly distinguished
  in the source.
- **Stop** (quantum article): PennyLane's own docs state that calling
  `lightning.gpu` directly without the cuQuantum libraries installed
  *raises an error* rather than silently falling back to CPU. The
  article's `make_device()` wrapper only avoids hitting that error because
  it checks `_device_importable()` *before* constructing the device — a
  real design detail doing real work, but the article's prose doesn't
  make clear that the graceful fallback is the wrapper's own doing and
  not a property of the PennyLane API itself. Minor, but worth stating
  precisely rather than letting the distinction blur.
- **Credit** (security-pipeline article): the six-step "find, prove,
  triage, patch" loop it attributes to Anthropic is real and
  independently corroborated — Anthropic's own published work on
  AI-discovered vulnerabilities (the "LLM-discovered 0 days" page and
  "Project Glasswing") and a third-party (ZenML) summary of an Anthropic
  talk both describe the same threat-model → sandbox → discovery →
  verification → triage → patching shape, with the ZenML summary citing
  up to 90% true-positive rates in Anthropic's own reported work
  ([anthropic.com/research/zero-days](https://www.anthropic.com/research/zero-days),
  [zenml.io llmops-database](https://www.zenml.io/llmops-database/ai-powered-vulnerability-discovery-and-patching-at-scale)).
  The article is not inventing a framework and attributing it loosely —
  the shape really is Anthropic's.
- **Stop-leaning / dated** (security-pipeline article): the article's
  chosen model, Qwen2.5-Coder-7B-Instruct, is real (Alibaba's Qwen team,
  released September 2024) but independent trackers (Artificial
  Analysis, OpenRouter) now list it as superseded by newer Qwen
  checkpoints
  ([huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct),
  [artificialanalysis.ai](https://artificialanalysis.ai/models/qwen2-5-coder-7b-instruct)).
  Worth naming because the fourth article in this same upload, by the
  same author, uses Qwen3-14B instead — see DEEPEREST-EST below.
- **Credit** (long-running-agent article): Temporal's own docs confirm
  both mechanisms the article leans on — Continue-As-New resets a
  workflow's event history while keeping its Workflow ID
  ([docs.temporal.io/design-patterns/continue-as-new](https://docs.temporal.io/design-patterns/continue-as-new)),
  and replay determinism works exactly as described: replaying recorded
  history against the same deterministic workflow code reproduces the
  same decisions, which is what makes "crash mid-cycle, replay, resume
  exactly where it left off" a real property rather than a narrative
  convenience
  ([temporal.io/blog/very-long-running-workflows](https://temporal.io/blog/very-long-running-workflows)).
  The event-history cap the article implicitly works around (continue-
  as-new every N cycles) matches Temporal's own stated ~51,200-event /
  50MB ceiling.
- **Credit** (quantum article, cross-checked independently of the
  article's own text): the LHC Olympics 2020 R&D dataset at Zenodo record
  `2629073` is real and matches the article's description — 1M QCD
  background events, a W'→XY signal injection, authored by Kasieczka,
  Nachman and Shih
  ([zenodo.org/records/2629073](https://zenodo.org/records/2629073)).
  One caveat the search itself surfaced, not from the article: the
  record page notes a newer version exists, and at least one external
  preprint cites a DOI one digit off (`.2629072`) — worth checking the
  exact DOI before citing this dataset elsewhere, a `sourced-dated`
  flag on the citation mechanics, not on the article's description.

## DEEPEREST — internal seams, within and across the three new pieces

- **Stop** (security-pipeline article, internal): the article names its
  own GitHub repo as `github.com/FareedKhan-dev/agentic-security-
  pipeline.git` in its opening line, but every subsequent "all the code
  is on GitHub" link in the piece points at
  `github.com/FareedKhan-dev/agentic-quantum-computing.git` instead —
  the same repo the *quantum* article links. One of the two is almost
  certainly a publishing error (most likely the security-pipeline repo
  was never actually re-linked after the quantum article's repo was
  created), but which one is wrong isn't resolvable from the pasted text
  alone. Not checked further since this sandbox has no instruction to
  fetch either repo.
- **Credit** (cross-article, security-pipeline vs. long-running-agent):
  both articles independently build the same core discipline — a
  deterministic, re-runnable check decides truth, never the model's
  self-report — from two different angles. The security-pipeline
  article does it with AddressSanitizer exit codes; the long-running-
  agent article does it with `git`-committed checklist items that only
  flip to `done` after `ruff`/`mypy`/`pytest` all exit zero. Neither
  article cites the other or calls out the shared principle explicitly,
  but read together they're the same idea applied to two different
  domains — a genuine, non-obvious consistency across two pieces written
  independently enough that even their canary bugs and their model
  choices differ.
- **Stop** (long-running-agent article, internal): its "Governor" cost
  ceiling (`$400` for the worked example) and its per-cycle cost
  estimates are computed from `ledger.mean_usd_per_cycle()` — a running
  average projected forward. The article never states what happens if a
  single upcoming cycle is unusually expensive (e.g., a large
  compaction call) right as the budget is nearly exhausted; the governor
  as described can authorize a cycle whose *actual* cost, once it runs,
  pushes the real total past the ceiling, since the check happens on the
  *projected* mean, not a hard per-call cap. A real, if minor, gap in an
  otherwise carefully specified budget mechanism.
- **Credit** (quantum article, internal): the article is unusually
  honest about a negative result inside its own narrative — on the
  fraud and LHC domains, the classical baselines beat the quantum kernel
  outright, and the article states this plainly rather than only
  showcasing the one domain (KDD) where quantum wins. Flagged as a
  genuine positive the same way this project credited one of the Jev
  sources for an honestly-reported negative Bitcoin-prediction result in
  an earlier round.

## DEEPEREST-EST — what breaks, or becomes visible, reading all four together

**The clearest finding this round comes from reading the security-
pipeline article against the long-running-agent article — both by the
same author, in the same upload, and both choosing different Qwen
models for structurally similar reasons.** The security-pipeline article
(dated to an Oct-2026-era reference to Anthropic's OSS Scanner inside
this same text) runs its whole defender loop on Qwen2.5-Coder-7B-
Instruct — a model independent trackers now list as superseded. The
long-running-agent article, in the same upload, picks Qwen3-14B for its
"lead engineer" role. Neither article explains the choice or acknowledges
the other's model, and nothing here claims the older model was a mistake
— a 7B coder-tuned model for a narrow C-memory-safety task and a 14B
general model for an open-ended multi-role agent team are defensible,
different choices for different jobs. But read together, it's a visible,
real inconsistency in how carefully "pick the current model" was applied
across the same author's own back-to-back pieces, the kind of gap that's
invisible reading either article alone.

**A second, smaller cross-article finding:** the quantum article's own
mid-piece self-correction (the 8-qubit KDD "win" only holding on 2 of 5
seeds) and the security-pipeline article's adversarial-verifier failure
(a 7B model voting a real crash `FALSE_POSITIVE` 3/3) are the same
underlying lesson stated two different ways — *a single run, or a single
model's opinion, is not evidence; only a repeated, independently-checked
result is.* The quantum article applies this lesson to its own headline
number by rerunning it across seeds. The security-pipeline article
applies the identical lesson to verification by re-detonating instead of
trusting the model. Neither article names this as a shared principle;
read together, it's the actual thesis connecting both pieces, stronger
than either piece's own stated thesis in isolation.

## What's built from this

No separate build from the quantum-computing article or the long-
running-agent article this round — both describe genuinely well-reasoned
systems, but neither has a piece that's both novel to this project *and*
fully testable without a GPU/Temporal server (the quantum kernel's value
proposition is inseparable from the GPU numbers it reports; the long-
running-agent's durability story is inseparable from Temporal's actual
replay engine, and this project already has a hand-built checkpoint/
resume layer at `/builds/agent-checkpoint-layer/` covering the same
general territory with SQLite+WAL instead).

**Built:** `/builds/defender-loop-verifier/` — the one idea from the
security-pipeline article that is both genuinely novel to this project
(nothing here previously implemented "re-detonate, never trust the
agent's self-report, as a tested rule") and fully reproducible with
nothing but `gcc` and Python's standard library, already present in this
sandbox. A 2-bug ASan canary (reusing the exact dead-store hazard
verified above), a deterministic verifier, an allow-list tool dispatcher,
and a scripted stand-in for the model that can be told to lie in either
direction — proving the orchestration layer's correctness is independent
of what the model says, which is the part of the article's design that
most needed proving rather than just reading. 18/18 tests pass, clean on
the first real run. Full write-up in
`/builds/defender-loop-verifier/README.md`.
