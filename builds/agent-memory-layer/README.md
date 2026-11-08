# agent-memory-layer

A real, dependency-free Python implementation of the one genuinely
concrete, well-specified, independently-verifiable mechanism inside a
pasted Medium article, "Memory Engineering for AI Agents" (DhanushKumar)
— analyzed in `/notes/memory-engineering-analysis.md`. The article itself
is mostly a 30-plus-category prose taxonomy with nothing to execute; this
build is the small part of it that actually is a mechanism: a scoring
formula, a lifecycle state machine, and a supersession rule for
conflicting preferences.

## What's real, what's the article's own invention, and why that distinction matters

- **`score_generative_agents()`** implements the real formula the article
  attributes to Generative Agents (Park et al. 2023, "Generative Agents:
  Interactive Simulacra of Human Behavior," arXiv:2304.03442) — web-
  verified this round: the paper's retrieval function really is an
  equally-weighted sum of recency, importance, and relevance. The exact
  recency decay constant (0.995/hour, commonly cited in secondary
  sources) was **not** independently confirmed against the primary paper
  in this round's research, so it's always an explicit, overridable
  parameter here — never hardcoded as a fact the way the article implies
  it.
- **`score_extended()`** is a *separate* function implementing the
  article's own proposed extension (+confidence +authority +task_alignment
  −contradiction_penalty −staleness_penalty). This is the article's own
  invention, not sourced to Generative Agents or anything else it cites —
  kept as a distinct function specifically so neither this code nor a
  future reader can mistake its output for the real, attributed formula.
- **`transition()`** validates the article's own proposed lifecycle (RAW
  → ACTIVE → CONFIRMED → SUPERSEDED → STALE → ARCHIVED → FORGOTTEN),
  which the article states only in prose, with no validation that a move
  is actually legal. Read literally as a strict chain, the article's own
  sequence would forbid superseding a still-RAW memory — but the
  article's own worked example (a preference changing from Flask to
  FastAPI) has no reason to require confirmation first. This build
  resolves that as a considered DAG, documented in the module itself:
  every live state can move directly to SUPERSEDED, STALE, ARCHIVED, or
  FORGOTTEN; only ACTIVE/CONFIRMED are promotion targets; the four end
  states are truly terminal. That resolution is this build's own choice,
  stated plainly, not the article's.
- **`supersede()`** makes the article's own Flask→FastAPI preference
  example real and testable, plus one guard the article never states:
  refusing to link two records with different `subject_id`s, since a
  supersede call that silently overwrote the *wrong person's* preference
  would be a materially worse failure than the feature simply being
  missing.

## Round 2: `score_candidates()` and `SQLiteMemoryStore` (this project's own suggested next moves, all three built)

`score_generative_agents()`'s own docstring states a real gap: a single
memory has no "other candidates" to normalize against, so its own
per-record relevance/importance mapping (a fixed cosine-to-[0,1] affine
map, importance/10) isn't a fair ranking across a candidate set. This
round closes that gap for real:

- **`score_candidates(records, query_embedding, *, now)`** — the real
  Generative Agents retrieval step: min-max normalizes RAW recency,
  importance, and relevance SEPARATELY across the whole candidate set,
  then sums. A record missing an embedding gets the worst possible raw
  relevance (-1.0) so it ranks at the pool's relevance floor rather than
  an arbitrary fixed value; if the WHOLE pool lacks embeddings, every
  candidate ties, so relevance becomes a correct no-op rather than a
  penalty. Returns `(record, score)` pairs sorted descending. 9 new
  tests, including an independent hand recomputation of the min-max
  normalization for a 3-record pool, a tied-pool check, a single-record
  pool (normalizes against itself without a `ZeroDivisionError`), and an
  empty-pool `ValueError`. All passed on the first run.
- **`persistence.SQLiteMemoryStore`** (`persistence.py`) — the
  persistence layer `MemoryStore` doesn't have, following the exact WAL
  convention already established in
  `/builds/agent-checkpoint-layer/checkpoint/store.py`: SQLite's own
  write-ahead-log journal mode plus an app-level, append-only
  `transitions` table logging every lifecycle change. Same `add`/`get`/
  `live_for_subject`/`supersede` surface as `MemoryStore`, backed by a
  file instead of a dict, delegating all legality checks to
  `memory_layer.transition()`/`supersede()` rather than re-implementing
  them. Proven with 27 tests, including the one that actually matters:
  a real **cross-process** restart — a genuine subprocess writes two
  records and a status transition, exits, and this process opens a
  fresh `SQLiteMemoryStore` against the same file and confirms
  everything (including the transition WAL) survived. All 27 passed on
  the first run — no bug found this round, unlike round 1's
  normalization bug.

Both extensions are wired into `/builds/trading-jarvis/jarvis_orchestrator.py`
as a new session-memory tool category (`remember_preference`,
`recall_preferences`, `supersede_preference`) — see that build's README
for the integration and its own 16-assertion wiring test.

## Use

```python
from memory_layer import MemoryRecord, MemoryStore, score_generative_agents

store = MemoryStore()
flask_pref = MemoryRecord(
    memory_id="pref-1", type="semantic.preference", subject_id="user_1",
    content="prefers Flask", created_at=0.0, valid_from=0.0,
)
store.add(flask_pref)

fastapi_pref = MemoryRecord(
    memory_id="pref-2", type="semantic.preference", subject_id="user_1",
    content="prefers FastAPI", created_at=5000.0, valid_from=5000.0,
)
store.supersede("pref-1", fastapi_pref, now=5000.0)

store.live_for_subject("user_1")  # -> [fastapi_pref] only
```

## Proven

```bash
python3 test_memory_layer.py    # 39/39
python3 test_persistence.py     # 27/27
```

**39/39 assertions pass in `test_memory_layer.py`**, including:

- Every legal and illegal lifecycle transition in the DAG above, not just
  the happy path — both terminal states (`ARCHIVED`, `FORGOTTEN`) are
  confirmed to refuse every other transition out of them.
- The article's own Flask→FastAPI supersession example, end to end: the
  old preference is marked `SUPERSEDED` (never deleted or merged), its
  validity window closes at the supersession time, the new record links
  back via `supersedes`, and querying live memories for that subject
  afterward returns the new preference only.
- `score_generative_agents()` checked against an **independently
  recomputed** hand calculation of recency + importance + relevance for
  a worked example, not trusted from the function's own output — exact
  match.
- A real, instructive bug found and fixed while writing these same
  tests: the first draft's cosine-to-[0,1] normalization line
  (`relevance = (relevance + 1.0) / 2.0`) ran unconditionally, even when
  a record had no embedding at all and `relevance` had just been set to
  the "no embedding" sentinel `0.0` — turning that sentinel into `0.5`
  instead of the correct `0`, silently inflating every embedding-less
  memory's score. Caught by a dedicated no-embedding test, not by
  re-reading the code; fixed by only applying the normalization when a
  real cosine value was actually computed.

## What's not built here

- No actual vector store or embedding model — embeddings are always
  caller-supplied tuples here, never computed.
- No multi-tenant/multi-subject identity layer beyond `subject_id` as a
  plain string field — a real deployment scoping memories to real users
  needs real authentication, which is out of scope for this module.
- No implementation of the article's 30-plus-category taxonomy — that's
  prose classification with nothing to execute or test, not a
  generalizable mechanism in the sense this project's builds require.
