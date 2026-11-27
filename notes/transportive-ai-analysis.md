# Deep analysis: "Building Transportive AI: A Cleaner Way to Code with Agents"

Source: a pasted Medium article by Fareed Khan, the eighth source from
this author this project has analyzed, this time with a real linked
repo given directly (`https://github.com/FareedKhan-dev/transportive-ai.git`).
No accompanying instruction, so per this project's convention the
article itself is the instruction to run the deep-analysis-and-ship
loop. Builds Jose Crespo's "transportive AI" idea (rules recovered from
code and law, checked by a Z3 solver, enforced by verification "rings"
no coder wrote) into a system acting on Saleor's payment module, with
Claude Opus 5.5 and Qwen3.8-27B as the two coders under test.

## What was measured first

Cloned the real repo directly rather than trusting the article's code
samples. Every single module path the article names actually exists:
`transportive/spec/{language,canon,recover,registry}.py`,
`index/{semantic,regions}.py`, `engine/{context,solver,transport}.py`,
`coord/{leases,queue}.py`, `workspace/sandbox.py`,
`agents/{broker,coder,team}.py`, `verify/{rings,model,race,compile,
mutate}.py`, `guard/{schema,monitor}.py`, `ledger/trace.py`,
`loop/{journal,deliver}.py`, `eval/{suite,harness}.py` — a real,
complete, well-organized codebase, the strongest evidentiary bar this
project applies (real, runnable code shown in full, matching the
article's own samples line for line in several spots checked directly).

## The central finding

The repo's own `results/derive.py` turns `results/story.json` into
`eval.json`/`ablation.json`/`headline.json`/`claims.json`, and every
leaf it writes is `{"v": value, "provisional": bool}` — "the flag is
true as long as any input it reads is provisional... a real story.json
replaces every number at once," per the script's own docstring.

Checked directly against the real, committed files:

- `assets/oracles/` — the directory holding all 44 hidden test oracles
  the entire evaluation depends on — contains nothing but a
  `.gitkeep`. Confirmed with `ls -la`.
- `notebook.ipynb` — 16 code cells, every one with `execution_count:
  null` and zero outputs. Confirmed by parsing the notebook's own JSON
  directly. This repo's notebook has never been run, in direct contrast
  to earlier Fareed Khan sources this project has analyzed
  (`agentic-warehouse-analyst`'s real 6,679-line *executed* notebook
  with a real `llm_cache.sqlite` of 4,005 cached calls;
  `dynamic-workflow-agents`' two real executed notebook editions).
- `results/story.json` — 288 records total (36 tickets × 4 arms × 2
  coders, matching the article's own "288 ticket runs" exactly), **every
  single one** carrying `"provisional": true`, including the article's
  own headline claim: `arms.A4.opus.pass` = 33 (provisional), matching
  "the full machine passed 33 of 36 tickets with Opus" word for word.
- The repo's own README states this directly, under a section titled
  **"Not done yet"**: "The hidden oracles. `assets/oracles/` is empty.
  The 44 oracles are written by hand... The fork commits. The
  `bug_commit` and `fix_commit` hashes... are stand-ins until those
  commits exist on a private fork... The fold. A short step that folds
  `results/story.jsonl` into the `results/story.json` shape... is still
  to write. The room check... needs one run in a real room."

Put plainly: the repo's own author discloses, in its own README, that
the 288-run study described in the article has not actually happened —
no real oracles, no real fork commits, no real fold step from raw
execution logs to the shape the numbers come from, no real room check.
`results/story.json` is a hand-authored, internally-consistent mock
dataset built to drive `derive.py`'s pipeline and demonstrate its
design, not captured execution data.

The article's own narrative never discloses any of this. It prints
dozens of specific, confident numbers (pass counts, Wilson intervals,
sha256 patch hashes, minute-level wall-clock timings, an exact "315.01
credits across 288 ticket runs") with zero hedge, except one disclosure
right at the very end, in a "Known Limits" section, about something
else entirely: that the real motivating Saleor issue's own author calls
the bug "unlikely" and "a correctness issue only." That one disclosure
is real and honest (confirmed below) — it just isn't the disclosure the
repo's own README says is actually needed.

## What else was verified, and credited

- **Saleor #19812** is real, confirmed by fetching the live issue:
  "Prevent duplicate automatic transaction release requests," opened
  Sep 21, 2026. Its two acceptance criteria match the article's quotes
  verbatim ("Re-validate refund eligibility against the writer," "Use
  (ordered) row locking for each `TransactionItem`..."). The issue's own
  text does say the bug is "unlikely" and the PSP would reject a
  duplicate request — exactly the caveat the article discloses in its
  own "Known Limits" section, credited as a real, honest disclosure.
- **Medusa #16012** ("Check-then-act races bypass amount guards in
  payment capture/refund and promotion budgets") and **PR #16097**
  (merged, serializes the same guards with row locks) are both real,
  confirmed by fetching the live pages. The quoted "would pass without
  the lock too" line is real, though it's from a PR review comment
  rather than the PR description text itself — a minor precision
  nuance, not a misattribution.
- **UCI Online Retail II** — "1,067,371 lines," CC BY 4.0, Chen (2012)
  — all match the dataset's real official UCI page exactly.
- **The "not rocket science rule"** — real, and Graydon Hoare's 2014
  post is the canonical statement most sources point to, though
  independent sources credit Ben Elliston with originating the idea
  Hoare's post summarizes; a defensible, not misleading, attribution.

## Checked `/builds/` first

`fingerprinted-ledger-prereg/` (hash-locked pre-registration + resume
journal, from an earlier Fareed Khan round), `manifest-drift-guard/`
(byte-identical file-hash drift, from the ontology-driven-observability
round), and `paired-bootstrap-ratchet/` (statistical significance
gating, from the agentic-warehouse-analyst round) are all adjacent —
none of them track provenance *through* a derivation pipeline, and none
gate what gets published against what's actually disclosed. A
genuinely new mechanism.

## Built

**`/builds/provisional-data-gate/`** — `provisional_gate.py` implements
the propagation rule transportive-ai's own `derive.py` states in prose
("provisional if any input is") as an enforced `Leaf`/`combine()` type,
`load_leaf_tree()` to parse any real results file using that
convention, and `publish_check()` — the actual gate, flagging any
`Claim` resting on provisional data unless it's explicitly in a
disclosed set.

24/24 tests pass, including the real, unmodified
`results/eval.json`/`results/claims.json` from the real repo committed
as fixtures, and the actual finding reproduced directly as a test: six
of the article's own real headline numbers, loaded from the real
provisional data, checked against the article's own real disclosure
(which covers an unrelated topic) — all six correctly flagged as
undisclosed, matching exactly what the article's own published text
did.

**One real slip caught in this build's own first draft**: `cli.py`'s
first version carried a dead, unused `load_claims()` function with a
nonsensical placeholder line (`sys.argv[2] if False else None`), never
called anywhere. Caught by re-reading the file before writing tests
against it, removed before any test ran.

## Deliberately not built

A reimplementation of transportive-ai's own architecture (spec mining,
the Z3 context/conflict solver, the agent team, the verification rings)
— that's the article's own content, not a generalizable gap this
project lacks, and several of its component ideas (hash-locked ledgers,
statistical significance gates, checkpoint/resume) already have real
builds here from earlier Fareed Khan sources. A markdown-rendering
integration that would auto-write disclosure footnotes into a generated
report — the gate's job is to refuse silent publication, not ghost-write
the author's own disclosure text.
