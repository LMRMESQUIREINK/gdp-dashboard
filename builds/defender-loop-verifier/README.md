# Defender-Loop Verifier

A small, real, tested implementation of the single load-bearing idea in
Fareed Khan's "Building an Agentic Security Pipeline That Finds, Proves,
and Patches Vulnerabilities": **a program that crashes under a sanitizer
is proof; the model's opinion is not.** Built after a DEEP/DEEPER/
DEEPEREST/DEEPEREST-EST read of that article plus two others uploaded in
the same round — see `/notes/agentic-systems-deep-dive-analysis.md` for
the full critique of all three (and why this was the one picked to build).

## What's here

- `canary/canary.c` — a 2-bug C program (`parse_alpha`: heap-buffer-
  overflow; `parse_bravo`: heap-use-after-free), compiled with
  `-fsanitize=address`. `parse_alpha`'s `__asm__ volatile` barrier is not
  decoration — verified by hand in this build (see below) that without
  it, `gcc -O1` proves the buffer is dead after the copy and deletes the
  overflowing `memcpy` outright, silently curing the bug at compile time.
- `verifier.py` — `detonate()` runs the real binary under ASan and reads
  the real exit code + `SUMMARY:` line; `verify_crash()` re-detonates 3
  times and requires a majority to crash before calling a finding
  reproducible; `grade_patch()` is the patch ladder (builds, the original
  PoC stops crashing, a benign input still behaves normally).
- `dispatcher.py` — the allow-list tool gate: unknown tool, not-on-the-
  list, mutation disabled, egress disabled (default-deny) — four checks,
  enforced in code, and a tool's own exception becomes a failure result
  instead of crashing the caller.
- `agent_stub.py` — a scripted stand-in for the LLM (no live model API in
  this sandbox, same standing restriction as every other build here). It
  can be told to self-report honestly or dishonestly about whether its
  own PoC crashed.
- `run_defender_loop.py` — wires it all together end to end and prints a
  trace.
- `tests/test_defender_loop.py` — 18 real tests, zero mocks for anything
  that matters (the compiler, ASan, the subprocess boundary).

## What this proves, for real

Run it:

```bash
cd canary && ./build.sh && cd ..
python3 run_defender_loop.py
python3 tests/test_defender_loop.py
```

18/18 tests pass, clean on the first real run. The result that matters
most is `TestHostNeverTrustsTheAgentsClaim`: one scripted agent lies and
*denies* a crash that really happens (`heap-use-after-free`), another
lies and *claims* a crash on an input that's actually harmless. In both
cases the verdict is unaffected, because `verify_crash()` never reads
`claim.self_reported_crash` at all — it only ever looks at what
`detonate()` measured by re-running the real binary. This is a direct,
testable version of the article's own finding that a 7B verifier model
voted a provably-crashing bug `FALSE_POSITIVE` with 95% confidence three
times in a row — the fix in both the article and here is the same: the
deterministic oracle overrules the model, never the other way round.

The patch ladder is likewise proven to discriminate, not just pass
everything: a root-cause fix (clamp the copy length before the `memcpy`,
the article's own stated recipe) passes all three rungs; a cosmetic fix
that only changes what gets printed — leaving the real overflow untouched
— correctly fails at the second rung (`poc_stops=False`), because the
ladder re-detonates the *compiled* patched binary, not the diff text.

## What was cut, and why

- **No live model.** `agent_stub.py` is scripted, not an LLM call — this
  sandbox has no outbound API access (the same restriction noted on every
  build in this project). The dishonest-agent tests substitute for the
  article's own 7B-model experiment: they show the orchestration layer
  is correct regardless of what the "agent" says, which is the part that
  needed proving independent of which model sits behind it.
- **No Docker sandbox / network isolation.** The article's `detonate()`
  runs inside a `--network none`, read-only, capability-dropped container
  per PoC. This whole session already runs inside one container with no
  outbound default access, so a second nested sandbox would be isolating
  against a threat (this session escaping to the host) that isn't the one
  the article is actually defending against (an agent's crafted input
  reaching the internet). Noted as a real, deliberate scope cut, not an
  oversight — a production version of this would still want it.
- **No multi-agent swarm, no recon/triage/severity-rubric stages.** The
  article's full six-step loop (threat model → sandbox → discovery →
  verification → triage → patching) is scaled down to the two stages that
  are genuinely load-bearing and fully verifiable without a model in the
  loop: verification (did it really crash) and the patch ladder (did the
  fix really work). Threat modeling and severity scoring are judgment
  calls a model makes well; they weren't the thing worth re-proving here.
- **Two planted bugs, not three.** The article's canary has three parser
  bugs across three bug classes; two (overflow + UAF) already exercise
  both the dead-store hazard and the "lie in either direction" test
  without a third class adding new coverage.

## Independently verified while building this

The `__asm__ volatile` dead-store hazard the article calls out for its
own `parse_alpha` was reproduced from scratch in this sandbox before
trusting it: a minimal `memcpy` into an undersized heap buffer, compiled
at `-O1` with ASan and *no* barrier, ran clean (exit 0 — the optimizer
proved the buffer dead and removed the overflowing write); the identical
code with the barrier added crashed exactly as expected. Both runs are
summarized in `/notes/agentic-systems-deep-dive-analysis.md`.
