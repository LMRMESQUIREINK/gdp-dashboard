# Analysis: FareedKhan-dev/ontology-driven-observability (ruthless-gate)

Full ledger and rendered verdict page: `/builds/ontology-observability-gate/`
(`index.html`, `data.js`, `test.js`, `README.md`). 193/193 assertions pass.
Generalizable build from the round's central finding:
`/builds/manifest-drift-guard/`.

This is the shortest-form pointer per this project's convention — the real
write-up lives in the build's own README and in `data.js`'s full ledger
(16 findings, 11 credit / 5 stop, across all four DEEP/DEEPER/DEEPEREST/
DEEPEREST-EST levels), not duplicated here.

## What this source is

A public GitHub repository (sixth Fareed Khan source analyzed in this
project), not an article — a real, already-executed 12,141-line jupytext
notebook rebuilding Netflix's October 2026 "Ontology-Driven Observability"
knowledge-graph design from its public description, and measuring all 12 of
the post's claims against real public data (Wikimedia's operations record,
OpenRCA, RCAEval, Wikipedia pageviews). One of the most rigorous, most
independently-verifiable sources this project has analyzed — a real
pre-registration with a SHA-256 fingerprint, 51 logged bugs with their
fixes, an honest 4-of-7 missed-targets table, and explicit disclaimers
separating Netflix's claims from this repo's own measurements throughout.

## The two headline findings

1. **The user-pasted file tree was wrong.** It showed a `kg/` directory of
   13 separate Python modules; the real, cloned repo has no `kg/` directory
   at all — everything lives in one notebook. Confirmed against the real
   `README.md`'s own "Repository layout" section before writing anything
   else — a direct, documented instance of why this project's "measure
   before reading for meaning" rule exists.
2. **The repo's own reproducibility fingerprint doesn't check out.** The
   committed `run_manifest.json` records sha256[:16] fingerprints for the
   three ontology files, matching exactly what the executed notebook
   printed — but recomputing those hashes against the actually-committed
   ontology files gives three different values, for all three files. Ruled
   out: line-ending drift, multiple commits, an alternate repo version
   (one branch, zero tags). The likely explanation: the ontology files were
   edited after the last full run and committed alongside the now-stale
   manifest. This directly contradicts the README's own central claim that
   "the run fingerprints itself... a reader can see that the two agree."

## Rights

The repo states "No licence has been chosen yet, so all rights are
reserved." A rights table is included on the verdict page. Nothing from
the repo's own files is committed in this project — `source/` holds only
this round's own measurements (hashes, counts, a couple of short cited
phrases), checked directly in `test.js`.

## Build: manifest-drift-guard

`/builds/manifest-drift-guard/` generalizes finding `deepest-01` into a
reusable, dependency-free Python tool: given a `{filename: hash}` manifest
and a directory, recompute every hash and report drift/missing/unlisted
files, exit 1 on any problem (CI-gate-ready). 32/32 tests pass against real
temp-directory files (no mocking), including five real CLI subprocess
calls. One real bug found and fixed while testing: a malformed `--key`
originally crashed with a raw `KeyError` traceback instead of a clean exit
code. Also run directly against the real cloned repository (transiently,
not committed) and reproduces the exact real-world drift found during the
gate round, exactly.

## Addendum 1 — the full source article, reconciled against a fresh clone

A later round pasted the full article this repo's notebook was built from
("Building an Agentic Knowledge Graph for Billions of Events") — not just
the bare repo link the gate round above had. The paste repeated the exact
same `kg/`-directory, 13-module file tree (`config.py`, `data.py`,
`identity.py`, `ontology.py`, `store.py`, `enrich.py`, `llm.py`,
`ladder.py`, `signals.py`, `correlate.py`, `agents.py`, `exam.py`,
`replay.py`) the gate round above already found did not match the real
repo, so this round re-cloned fresh (`git clone --depth 1`, single commit
`f208f19`, dated 2026-11-01 — identical to the gate round's commit, so
finding 2 above (the manifest fingerprint drift) still holds without
needing to be re-derived) and checked two things directly rather than
repeating the article's own framing either way:

1. **The `kg/` package still doesn't exist.** The fresh clone has the same
   layout the gate round found: `README.md`, `ontology/` (`ops.ttl`,
   `shapes.ttl`, `competency.rq`), `notebook/` (one `.ipynb` + its `.py`
   export, 12,141 lines — byte-identical line count to the gate round),
   `scripts/`, `pyproject.toml`, `uv.lock`. No `kg/` directory anywhere.
   The article's 13-module breakdown is the author's own expository
   reorganization of the one notebook's cells into an imagined package
   layout for readability, not a description of files that exist in the
   repo — confirmed again, on a second independent read, rather than
   assumed to have been a one-off slip the first time.
2. **But the mechanisms the article describes under those module names are
   real**, checked by grepping the actual notebook export for each one
   rather than trusting the prose: `class Enricher` and `class Coverage`
   both exist; `BoundedSemaphore`-gated concurrency, `visible()`/`AS_OF`
   SPARQL time-travel queries, and `PROV` provenance triples are all
   present; `mcnemar`/`holm` statistical testing and `RCAEval` both appear
   repeatedly. The article's "closed-vocabulary ladder" and "correlate.py"
   module names don't appear as literal function names — the real
   functions are `ladder_123()` and `best_chains()` — same mechanism,
   different name, found by searching for the *behavior* after the
   *literal name* came up empty rather than concluding the mechanism was
   fabricated from a naming mismatch alone.
3. **The replay benchmark is genuinely multi-process, not just
   multi-threaded.** Read `replay(processes, seconds)` in full: it spawns
   real OS subprocesses with `subprocess.Popen`, each running its own
   `threads = cores // processes` internal thread pool — a real two-level
   parallelism matching the article's "one laptop replays... at 26.1
   million events a second" claim, which also appears verbatim in the
   notebook's own prose (line 11479) rather than being invented by the
   article.
4. **The ontology triple/class/property counts check out exactly, but not
   on the first, naive check.** A first-pass `grep -c "a owl:Class"`
   against `ops.ttl` gave 22, far short of the article's claimed 43 —
   initially looked like a real discrepancy. Reading the notebook's own
   counting code (line 4254) showed why: it counts the union of explicit
   `owl:Class` declarations *and* every subject of `rdfs:subClassOf`
   (subclasses declared without a separate `a owl:Class` statement don't
   show up under a naive grep). Recomputing with `rdflib`, using that
   exact union method: **272 triples, 43 classes, 77 properties** — all
   three match the article exactly. This is the gate skill's own "a
   detector that disagrees with the data is wrong until the line says
   otherwise" rule firing for real: the naive regex was the wrong
   instrument, not the article.
5. **The "65 million concurrent streams" / "38 million events a second"
   figures are Netflix's own stated scale, not this repo's claim about
   itself** — confirmed by reading the surrounding prose in the notebook
   (lines 3454-3455, 3758, 10683), which quotes them explicitly as "the
   post opens with its scale" before building its own, separately-labeled
   measurements against them. The RCAEval ranker's real reported figures
   (line 10443-10449) are also more specific than a loose paraphrase would
   suggest: top-3 accuracy 80% against BARO's 82% and TraceRCA's 79%, with
   first-place accuracy at 31% against BARO's 69% — a real, named
   shortfall the repo states about its own model-free ranker, not a round
   number.

No new generalizable mechanism was built this round — the one real,
checkable gap this source surfaces (the stale reproducibility manifest)
was already extracted into `/builds/manifest-drift-guard/` during the
original gate round, and a second implementation of the same finding from
the same unchanged commit would add nothing. This addendum exists because
the article, read on its own, could easily be mistaken for evidence that
the repo had been restructured since the gate round — it hasn't, and the
underlying mechanisms it describes are real even though its file-tree
framing isn't.
