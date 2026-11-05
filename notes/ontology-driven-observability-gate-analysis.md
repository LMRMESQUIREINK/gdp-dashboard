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
