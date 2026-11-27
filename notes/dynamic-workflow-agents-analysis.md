# `FareedKhan-dev/dynamic-workflow-agents` — analysis

A seventh Fareed Khan source for this project (six prior rounds: the
production-grade MCP server, interface lifting, the three-article
"agentic systems deep dive," the agentic-warehouse-analyst round, and
the ontology-driven-observability `ruthless-gate` round). Confirmed
genuinely new by title and content before touching anything — a bare
`git clone` URL with no accompanying text, same pattern as every prior
bare-link round in this project.

## What it is, measured first

Two self-contained notebook "editions" of the same build — `claude/` and
`qwen/` — each ~26,000 lines of executed Jupyter JSON, each with its own
`pyproject.toml`/lockfile/data/artifacts. A lead agent writes a phased
plan; a plain-Python runtime (threads, an event bus, a shared pause/
resume budget) executes it with parallel workers; the main benchmark is
an audit of a 72-planted-bug algorithm library, with the same engine
later reused on 600 maths-homework gradings and 10,003 customer
messages. No repository-wide license; included datasets carry their own
license notices.

## Verification: the most precisely checkable source analyzed in this
## project's run to date

Unlike most sources here, this one ships the actual computed artifacts
(`artifacts/exp_*.json`, `artifacts/figures/*.png`, a SQLite answer
ledger) alongside the executed notebook, so every headline claim in the
README could be recomputed against primary data rather than taken on the
README's own word. Every single one checked out exactly:

- **Recall/precision table.** `exp_main.json`'s `A_mean`/`C_mean`/
  `D_mean`/`A_prec`/`C_prec`/`D_prec` reproduce the README's claimed
  1.9%/73.2%/74.5% (Claude) and 2.3%/30.1%/44.9% (Qwen) figures to the
  decimal, including the derived "dynamic exceeded fixed by ~1.4 points"
  (Claude) and "~14.8 points, interval +5.6 to +25.5" (Qwen) statements —
  `DC_lo`/`DC_hi` match those interval bounds exactly.
- **Corpus size.** The README's claimed 856 files/98,028 lines (Claude)
  and 849 files/97,269 lines (Qwen) match both `exp_corpus.json`'s
  recorded values AND a direct `find`-based count of the actual files in
  `data/algorithms/audited/` in each edition — three-way agreement
  between the README, the saved experiment record, and the real files on
  disk.
- **Homework and intents.** `exp_hw_run.json`'s `workflow.accuracy`
  (0.965/0.96) and `single.accuracy` (0.8517/0.9367) match the README's
  96.5%/85.2% (Claude) and 96.0%/93.7% (Qwen) exactly; its separate
  `first.accuracy` field (0.9783) is the real source of the README's
  "Claude's first-pass grader reached 97.8%" line — a different metric
  (the same single long grader's un-decayed early performance) from
  "single" (that grader's full-600-item average, which decays with
  position), confirmed by reading both fields rather than assuming one
  number covers both claims. `exp_intents.json`'s `ari`/`topics` (0.0231/
  2 and 0.3796/30) match the README's "0.023"/"2 topics" and "0.380"/
  "30 topics" exactly.
- **Pre-registered claims table.** `exp_claims.json` confirms the
  README's statement that "the evidence-based skeptic and pipeline-speed
  claims did not meet their stated rules in either edition" — H6 and H7
  are NOT SUPPORTED in both editions' recorded verdicts, as stated.

## The one finding the README's own self-critique misses

`exp_claims.json` also marks **H8** ("a crashed run resumes without
paying twice") NOT SUPPORTED in **both** editions — Claude: "paid 0 + 0
= 56 calls; same report: True"; Qwen: "paid 0 + 1 = 20 calls; same
report: True." Read casually this looks like a pass (the report matched,
nothing visibly double-charged), and the README's own "Read the numbers
with their limits" section names only H6 and H7 as the claims that "did
not meet their stated rules" — H8 is never mentioned there, despite
failing the same way, for the same reason, in both editions. Read the
real code (notebook cell computing `H8["holds"]`) rather than stopping at
the summary table: the pre-registered rule requires `paid_crash +
paid_resume == total`, not merely that the outcome matched. In both
recorded runs that sum is 0 (all 56, respectively 20, calls were answered
entirely from a pre-populated cache on both sides of the simulated
crash) — so the experiment, as actually recorded, generated zero fresh
evidence about double payment, and the strict rule correctly refuses to
call that a pass. This is a point of real credit to the source's design
(the rule is stricter and more correct than an outcome-only check would
be, exactly the kind of rigor this project has repeatedly credited in
earlier Fareed Khan rounds — the dead-store ASan repro, the AddressSanitizer-
over-self-report principle), combined with a real, checkable omission in
its own self-reported limits section (H8 isn't named alongside H6/H7
despite failing for a comparably real reason).

Separately noted, not chased further given scope: Claude's `exp_main.json`
records an **A2** arm (one agent given the same turn budget the median
dynamic run's cost would buy, `a2_turns: 400`) scoring **0.0%** mean
recall across its two runs — worse than the plain, turn-capped solo arm A
(1.85%) — a counterintuitive result the README's own prose never
mentions at all. Plausible but unconfirmed from this round: a much larger
turn allowance without a correspondingly larger context/compaction budget
could itself degrade a solo agent's exploration (more opportunities to
lose track of what it already checked), but this wasn't independently
verified against the notebook's own compaction-count fields.

## Built

`/builds/fingerprinted-ledger-prereg/` — two generalizable mechanisms
extracted from the real source and independently reimplemented (not
copied): the `FingerprintedLedger` (one SHA-256-fingerprinted SQLite
table as cache + replay source + resume journal in one, with three
modes — collect/replay/smoke — matching the source's own three run
modes exactly) and `Preregistration`/`resume_holds()` (the hash-locked
hypothesis-verdict harness, with the exact strict resume-rigor rule the
H8 finding above surfaced, generalized rather than left as a one-off
observation). Checked `/builds/` first: `agent-checkpoint-layer/` does
stage-level checkpoint/resume with no request-level fingerprinting;
`run-terminal-ledger/` is a different concern (a terminal-status
singleton-confirmation protocol); neither has a pre-registration hash
lock. 27/27 tests pass, including the real Claude and Qwen H8 numbers
reproduced exactly as permanent regression fixtures (both correctly
fail) alongside the source's own toy S28 demo numbers (correctly
passes) and a synthetic genuine-double-charge case (correctly fails).
Full writeup in `/builds/fingerprinted-ledger-prereg/README.md`.

## Deliberately not built

The actual lead/worker/runtime (needs a live Anthropic or ModelScope key
and hours of real execution against a real code corpus to mean anything
— the same standing no-live-API restriction as every build in this
project); the paired-bootstrap statistics machinery behind the recall/
precision confidence intervals (this project already has a real
implementation in `/builds/paired-bootstrap-ratchet/`, built from a
different Fareed Khan source — a second implementation here would add
nothing); the 72-bug planted-fault benchmark itself (tied to one specific
algorithm corpus, not a generalizable mechanism).

## Addendum 1 — the full source article, reconciled against the real repo

A later round pasted the full article behind this repo ("Building Dynamic
Workflows: A New Agentic System") — not just the bare link round 1 had.
Its own file tree (a `build/` package of `config.py`/`bench.py`/`llm.py`/
`runtime.py`/`kit.py`/`plans.py`/`lead.py`) does **not** match the real repo
on disk, the same "article describes a package layout that is actually one
big notebook" pattern already found and documented for
`FareedKhan-dev/ontology-driven-observability` in this project's own prior
round. Re-checked directly rather than assumed: the real repo is still
exactly the two notebooks round 1 already found, same single commit, no
`build/` directory anywhere. But the mechanisms the article names under
those module labels are real, grepped directly in the actual notebook text:
`class Ledger`, `class Budget`, `class Run`, `class Thread`,
`ALLOWED_NODES`, `rule_names`, `dry_run`, `approve`, `AUTO_APPROVE`,
`PlanRejected`, `check_program`, `class AuditKit`, `scan`/`check`/`vote`/
`report`, `class Lead`, `write_program`, `FIXED_PROGRAM`, `match`,
`function_at` all appear verbatim. Two named functions (`rule_syntax`,
`blind`) don't exist under those literal names, but the same behavior
does — found by searching for the behavior once the literal name came up
empty, the same discipline already applied to `ladder.py`/`correlate.py`
in the ontology-driven-observability round.

**The round's strongest finding, nailed down precisely against the real
`exp_main.json` files in both editions**: the article's own A/A2/B/C/D
evaluation table (mean recall 0.02/0.04/0.17/0.30/0.45, mean cost
23.7/46.4/10.3/13.8/48.4) matches the **Qwen** edition's real recorded
numbers, not the Claude edition's — confirmed by comparing both editions'
full `A_mean`/`A2_mean`/`B_mean`/`C_mean`/`D_mean`/`*_cost` fields side by
side; every cost figure in the article matches Qwen's to the decimal (e.g.
`A2_cost: 46.4`, `B_cost: 10.3`, exact), while Claude's equivalents
(`A2_cost: 1.8071`, `B_cost: 70.4852`) are nowhere close. Within that same
reconciliation, one real, precisely-explained discrepancy: the article's
table states design A's mean precision as 1.00, but Qwen's own
`exp_main.json` records `A_prec: 0.6667`. Read the per-run `arms` list
rather than stopping at the aggregate field: design A's three individual
Qwen runs have precision `None` (run 0, which found zero bugs — tp=fp=0,
precision undefined), `1.0`, `1.0` (runs 1-2). The committed `A_prec`
field is the mean treating the undefined run as 0 — `(0 + 1.0 + 1.0) / 3 =
0.6667`, confirmed by hand — while the article's own printed "1.00" is the
mean over only the two runs where precision is actually defined,
`(1.0 + 1.0) / 2 = 1.0`. Both numbers are internally consistent with the
same three real runs; they differ only in which convention excludes a
zero-finding run from a precision average, a real and checkable
discrepancy between the committed summary statistic and the article's own
displayed table, not an error on either side alone. Cost, confirmed
unaffected by the same ambiguity: `A_cost: 23.7333` is the real mean of
`25.8, 19.2, 26.2` exactly, since cost (unlike precision) is always
defined.

**A real, verified gap found in the source's own published whitelist**,
grepped directly rather than assumed from the article's text: the real
`ALLOWED_NODES` set has no `ast.Pass`, meaning the real static checker
would reject a harmless, idiomatic empty loop body
(`for _ in range(n): pass`) outright. A second, honestly-preserved
limitation rather than a bug: the article's own worst-case hostile
example, `for i in range(1000000): agent(...)`, is explicitly reported by
the article's own text as passing the static check ("runaway passes the
rules: True"), because a bound of exactly one million is not "larger
than" the million-literal limit — the real system only catches it later,
via a separate runtime worker-count cap at dry-run time, not the static
whitelist.

**Built**: extended `/builds/fingerprinted-ledger-prereg/` (same source,
same build, not a new one) with `plan_guard.py` — `check_program()`/
`run_checked()` (the AST whitelist: syntax, method, and name checks, a
length cap, a required `result` assignment) and `ApprovalPolicy` (the
`approved`/`held`/`refused` three-way gate against a budget). Deliberately
adds `ast.Pass` to this build's own whitelist, on top of the real source's,
with the reason stated directly in the module — a backward-compatible
widening of an independent reimplementation this project owns, not a
silent fix of code it doesn't. Deliberately does **not** tighten the
one-million-literal check to catch the runaway example, since the real
source's own text states plainly that its static check doesn't either;
`test_plan_guard.py` asserts the real, documented behavior instead of a
wrong assumption about it. 26 new tests (53/53 total, up from 27), proven
including a rejected program genuinely never reaching `exec()` (a call
counter inside the would-be worker function, not just the exception) and
the runaway example confirmed to pass the static check exactly as the
source's own text says it does. Full writeup in
`/builds/fingerprinted-ledger-prereg/README.md`.
