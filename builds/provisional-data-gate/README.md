# provisional-data-gate

A dependency-free Python tool built from a pasted Medium article,
"Building Transportive AI: A Cleaner Way to Code with Agents"
(Fareed Khan, an eighth source from this author this project has
analyzed), with a real linked repo —
[`FareedKhan-dev/transportive-ai`](https://github.com/FareedKhan-dev/transportive-ai).
Full analysis: `/notes/transportive-ai-analysis.md`.

## The real finding

The repo is real, well-organized, and every module path the article
names actually exists (`spec/`, `index/`, `engine/`, `coord/`,
`verify/`, `guard/`, `ledger/`, `loop/`, `eval/` — all present, matching
the article's code samples closely). Unlike several earlier Fareed Khan
sources this project has analyzed (`agentic-warehouse-analyst`,
`dynamic-workflow-agents`), which shipped real *executed* notebooks and
cached model-call databases backing their numbers, this repo's own
`notebook.ipynb` has **zero executed cells** — all 16 code cells carry
`execution_count: null` and no outputs — and `assets/oracles/` (the 44
hidden test oracles the entire evaluation depends on) is **empty**, just
a `.gitkeep`.

The repo's own README states this plainly, in a section titled
**"Not done yet"**:

> "The hidden oracles. `assets/oracles/` is empty... The fork commits.
> The `bug_commit` and `fix_commit` hashes... are stand-ins... The fold.
> A short step that folds `results/story.jsonl` into the
> `results/story.json` shape that `derive.py` reads is still to write."

And in "Results": *"Each value is a `{"v": ..., "provisional": ...}`
leaf, and it stays marked provisional until a full run replaces it."*
Confirmed directly against the real files: every one of the 288 records
in `results/story.json` (36 tickets × 4 arms × 2 coders, matching the
article's own "288 ticket runs" exactly) and every leaf in
`results/eval.json` carries `"provisional": true` — including the
article's own headline claim, "the full machine passed 33 of 36 tickets
with Opus" (`arms.A4.opus.pass` = 33, `provisional: true`).

The article's own narrative never says any of this. It presents
detailed, confident receipts — specific pass/fail counts, Wilson
confidence intervals, sha256 patch hashes, minute-level wall-clock
times, an exact "315.01 credits across 288 ticket runs" total cost — as
settled empirical results, with only one disclosed caveat anywhere in
the whole piece, right at the very end in a "Known Limits" section: that
the real Saleor issue motivating the whole study (#19812, confirmed real
and verified against the live issue) calls the bug "unlikely" and "a
correctness issue only" — a real, honest disclosure, but about severity,
not about whether the 288-run study happened at all.

## What else was checked and credited

- **Saleor #19812** is real (confirmed live): "Prevent duplicate
  automatic transaction release requests," and its two stated acceptance
  criteria match the article's quotes verbatim.
- **Medusa #16012 and PR #16097** are both real and closely match the
  article's description, including the quoted "would pass without the
  lock too" line — confirmed real, though it's from a PR *comment*
  rather than the PR description itself, a small precision nuance.
- **UCI Online Retail II**'s "1,067,371 lines," CC BY 4.0 license, and
  Chen (2012) citation all match the dataset's own official UCI page
  exactly.
- **The "not rocket science rule"** attribution to Graydon Hoare is
  reasonable — he's the one who popularized and named it in 2014, though
  independent sources credit the underlying idea to Ben Elliston.

Credited: the article's closing "Known Limits" section is a real,
voluntary disclosure in the same spirit this project has credited
before (the quantum-computing and Jev articles' own honest negative
results) — it just discloses the wrong thing relative to what the repo's
own README says is actually unverified.

## Checked `/builds/` first

This project already has `fingerprinted-ledger-prereg/` (hash-locked
pre-registration + resume journal), `manifest-drift-guard/`
(byte-identical file-hash drift), and `paired-bootstrap-ratchet/`
(statistical significance gating) — all adjacent, none of them track
*data provenance through a derivation pipeline* or *gate what gets
published against what's disclosed*. A genuinely new mechanism.

## What this builds

`provisional_gate.py`:

- **`Leaf(value, provisional)`** — the exact `{"v", "provisional"}`
  shape transportive-ai's real `derive.py` uses, as an enforced type.
- **`combine(*leaves, fn=...)`** — applies `fn` to the raw values, and
  the result is provisional if *any* input is — the rule derive.py's own
  docstring states but only applies as a convention developers have to
  remember, not as something the type system enforces.
- **`load_leaf_tree(obj)`** — recursively parses a real results JSON
  file (any depth of nested dicts/lists) into a tree of `Leaf` objects.
- **`Claim(claim_id, text, leaf)`** and **`publish_check(claims,
  disclosed)`** — the actual gate: a claim resting on provisional data
  is a violation unless its id is in the disclosed set. A confirmed
  claim is never flagged, disclosed or not.

## Proof

`python3 -m unittest tests.test_provisional_gate tests.test_cli -v` —
**24/24 tests pass**, including:

- The real, unmodified `results/eval.json` and `results/claims.json`
  from `FareedKhan-dev/transportive-ai`, committed as fixtures
  (`tests/fixtures/transportive_eval.json`,
  `tests/fixtures/transportive_claims.json`).
- **The actual finding reproduced as a test**: six of the article's own
  real headline numbers, loaded from the real provisional `eval.json`,
  checked against the article's own real disclosure set (which covers
  the #19812 severity note, an entirely different topic) — all six
  flagged as undisclosed, matching exactly what the article actually
  did.
- A real subprocess CLI (`cli.py check <results.json> <claims.json>`)
  tested against the real fixture, including clean, non-traceback error
  handling for a missing file, malformed JSON, and a claim path that
  doesn't resolve.

**One real slip caught in this build's own first draft, not
manufactured**: `cli.py`'s first version had a dead, unused
`load_claims()` function left over from an earlier draft, including a
nonsensical `sys.argv[2] if False else None` placeholder line that was
never called by `main()`. Caught by re-reading the file before writing
tests against it, not by a failing run — removed before any test was
written.

## Deliberately not built

- A clone of transportive-ai's own system (the spec/engine/Z3-solver/
  agent-team/verification-rings architecture) — that's the article's own
  content, not a generalizable gap; several of its individual pieces
  (hash-locked ledgers, statistical gates, checkpoint/resume) already
  have real builds elsewhere in this project from earlier Fareed Khan
  sources.
- A markdown-rendering integration that would auto-insert disclosure
  footnotes into a generated report — the gate's job is to refuse
  silent publication, not to write the disclosure text for the author;
  stated plainly rather than oversold.
