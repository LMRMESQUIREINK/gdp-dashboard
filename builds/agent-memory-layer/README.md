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
python3 test_memory_layer.py
```

**30/30 assertions pass**, including:

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

- No actual vector store, embedding model, or persistence layer — this
  is the scoring/lifecycle/supersession logic only, the generalizable
  mechanism the article's own prose names but never implements, not a
  full memory service.
- No implementation of the article's 30-plus-category taxonomy — that's
  prose classification with nothing to execute or test, not a
  generalizable mechanism in the sense this project's builds require.
