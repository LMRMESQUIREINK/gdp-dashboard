"""Tests for memory_layer.py, including hand-recomputed checks of the real
Generative Agents scoring formula and the article's own worked
Flask-to-FastAPI supersession example.

Run with: python3 test_memory_layer.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_layer import (  # noqa: E402
    MemoryRecord,
    MemoryStatus,
    MemoryStore,
    IllegalTransitionError,
    transition,
    supersede,
    score_generative_agents,
    score_extended,
)

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("ok   - " + name)
    else:
        failed += 1
        print("FAIL - " + name + (f" ({detail})" if detail else ""))


def mk(mid, **kw):
    kw.setdefault("subject_id", "user_1")
    kw.setdefault("content", "x")
    kw.setdefault("type", "semantic.preference")
    kw.setdefault("created_at", 0.0)
    kw.setdefault("valid_from", 0.0)
    return MemoryRecord(memory_id=mid, **kw)


# --- MemoryRecord validation -----------------------------------------
try:
    mk("a", confidence=1.5)
    check(False, "confidence > 1 raises", "no exception")
except ValueError:
    check(True, "confidence out of [0,1] raises ValueError")

try:
    mk("a", importance=11)
    check(False, "importance > 10 raises", "no exception")
except ValueError:
    check(True, "importance out of [0,10] raises ValueError")

r = mk("a", status="ACTIVE")
check(r.status == MemoryStatus.ACTIVE, "a string status is coerced to the real MemoryStatus enum")

# --- Lifecycle transitions ---------------------------------------------
r = mk("a")
check(r.status == MemoryStatus.RAW, "a fresh record starts RAW")
transition(r, MemoryStatus.ACTIVE)
check(r.status == MemoryStatus.ACTIVE, "RAW -> ACTIVE is legal")
transition(r, MemoryStatus.CONFIRMED)
check(r.status == MemoryStatus.CONFIRMED, "ACTIVE -> CONFIRMED is legal")
transition(r, MemoryStatus.ARCHIVED)
check(r.status == MemoryStatus.ARCHIVED, "CONFIRMED -> ARCHIVED is legal")

try:
    transition(r, MemoryStatus.ACTIVE)
    check(False, "ARCHIVED -> ACTIVE raises", "no exception")
except IllegalTransitionError as e:
    check(True, "ARCHIVED is a real terminal state -- moving back to ACTIVE is refused", str(e)[:60])

r2 = mk("b")
try:
    transition(r2, MemoryStatus.CONFIRMED)
    check(False, "RAW -> CONFIRMED (skipping ACTIVE) raises", "no exception")
except IllegalTransitionError:
    check(True, "RAW -> CONFIRMED is refused -- promotion must pass through ACTIVE first")

r3 = mk("c")
transition(r3, MemoryStatus.SUPERSEDED)
check(r3.status == MemoryStatus.SUPERSEDED, "RAW -> SUPERSEDED is legal (a still-raw memory can be contradicted before it's ever confirmed, matching the article's own real-world case)")

for terminal in (MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN):
    r4 = mk(f"term-{terminal.value}")
    transition(r4, terminal)
    for target in MemoryStatus:
        if target == terminal:
            continue
        try:
            transition(r4, target)
            check(False, f"{terminal.value} -> {target.value} should be refused", "no exception")
        except IllegalTransitionError:
            pass
    check(True, f"{terminal.value} is a true terminal state: every other transition out of it is refused")

# --- supersede() --------------------------------------------------------
old = mk("pref-1", content="prefers Flask")
new = mk("pref-2", content="prefers FastAPI", created_at=1000.0, valid_from=1000.0)
result = supersede(old, new, now=1000.0)
check(old.status == MemoryStatus.SUPERSEDED, "the article's own Flask->FastAPI example: the old preference is marked SUPERSEDED, not deleted or merged")
check(old.valid_until == 1000.0, "the superseded record's validity window is closed at the supersession time")
check(new.supersedes == "pref-1", "the new record links back to the one it superseded")
check(result is new, "supersede() returns the new record")

different_subject = mk("pref-other", subject_id="user_2", created_at=2000.0, valid_from=2000.0)
try:
    supersede(old, different_subject, now=2000.0)
    check(False, "superseding across different subjects raises", "no exception")
except ValueError:
    check(True, "supersede() refuses to link records with different subject_ids -- a guard the article never states but a real supersede() needs")

# --- MemoryStore.live_for_subject --------------------------------------
store = MemoryStore()
flask_pref = mk("s-pref-1", content="prefers Flask", created_at=0.0, valid_from=0.0)
store.add(flask_pref)
check(store.live_for_subject("user_1") == [flask_pref], "a fresh RAW record is live (RAW is a live status)")

fastapi_pref = mk("s-pref-2", content="prefers FastAPI", created_at=5000.0, valid_from=5000.0)
store.supersede("s-pref-1", fastapi_pref, now=5000.0)
live = store.live_for_subject("user_1")
check(live == [fastapi_pref], "after supersession, querying live memories for this subject returns ONLY the new preference, not both", [r.memory_id for r in live])
check(flask_pref not in live, "the superseded Flask preference no longer appears in live results")

unrelated = mk("s-pref-3", subject_id="user_2", content="prefers Go")
store.add(unrelated)
check(store.live_for_subject("user_1") == [fastapi_pref], "a different subject's memory never leaks into this subject's live results")

try:
    store.add(flask_pref)
    check(False, "re-adding a duplicate memory_id raises", "no exception")
except ValueError:
    check(True, "MemoryStore.add refuses a duplicate memory_id rather than silently overwriting")

# ---------------------------------------------------------------------
# Hand-recomputed Generative Agents scoring (Park et al. 2023,
# arXiv:2304.03442, web-verified this round -- /notes/
# memory-engineering-analysis.md): score = recency + importance +
# relevance, equally weighted. Recomputed independently here, not taken
# on the function's own word.
NOW = 100 * 3600.0  # 100 hours after epoch, in seconds

rec = mk("score-1", importance=8.0, embedding=(1.0, 0.0), created_at=0.0)
query_emb = (1.0, 0.0)  # identical direction -> cosine similarity 1.0

expected_recency = 0.995 ** 100  # 100 hours elapsed, default decay
expected_importance = 8.0 / 10.0
expected_relevance = (1.0 + 1.0) / 2.0  # cosine=1.0 -> normalized 1.0
expected_score = expected_recency + expected_importance + expected_relevance

actual_score = score_generative_agents(rec, query_emb, now=NOW)
check(abs(actual_score - expected_score) < 1e-9, "score_generative_agents matches an independent hand recomputation of recency+importance+relevance exactly", f"expected={expected_score!r} actual={actual_score!r}")

# A record accessed recently (last_accessed_at close to now) scores higher
# on recency than an equally-old-but-never-reaccessed one.
rec_recent_access = mk("score-2", importance=8.0, embedding=(1.0, 0.0), created_at=0.0, last_accessed_at=NOW - 3600.0)
rec_stale_access = mk("score-3", importance=8.0, embedding=(1.0, 0.0), created_at=0.0, last_accessed_at=0.0)
score_recent = score_generative_agents(rec_recent_access, query_emb, now=NOW)
score_stale = score_generative_agents(rec_stale_access, query_emb, now=NOW)
check(score_recent > score_stale, "a recently-re-accessed memory scores strictly higher on recency than one accessed only once, long ago")

# Orthogonal embedding -> cosine 0 -> normalized relevance 0.5, not 0 or 1.
rec_orthogonal = mk("score-4", importance=0.0, embedding=(0.0, 1.0), created_at=NOW, last_accessed_at=NOW)
score_orth = score_generative_agents(rec_orthogonal, query_emb, now=NOW)
check(abs(score_orth - (1.0 + 0.0 + 0.5)) < 1e-9, "an orthogonal (cosine=0) embedding normalizes to relevance 0.5, not 0 -- the [-1,1] -> [0,1] mapping is a real, easy-to-get-wrong detail", score_orth)

# A record with no embedding at all scores 0 relevance, not an error and
# not a crash from an empty-vector cosine similarity.
rec_no_embedding = mk("score-5", importance=5.0, created_at=NOW, last_accessed_at=NOW)
score_no_emb = score_generative_agents(rec_no_embedding, query_emb, now=NOW)
check(abs(score_no_emb - (1.0 + 0.5 + 0.0)) < 1e-9, "a record with no embedding contributes exactly 0 relevance, no crash")

mismatched = mk("score-6", embedding=(1.0, 0.0, 0.0), created_at=NOW, last_accessed_at=NOW)
try:
    score_generative_agents(mismatched, (1.0, 0.0), now=NOW)
    check(False, "mismatched embedding dimensions raise", "no exception")
except ValueError:
    check(True, "a query embedding of a different dimension than the record's raises ValueError rather than silently misscoring")

# --- score_extended is a genuinely separate function, never silently
# aliased to the real Generative Agents formula ---
rec_ext = mk("ext-1", importance=5.0, confidence=0.9, authority="user_explicit", embedding=(1.0, 0.0), created_at=NOW, last_accessed_at=NOW)
base = score_generative_agents(rec_ext, query_emb, now=NOW)
extended = score_extended(rec_ext, query_emb, now=NOW, task_alignment=0.2, contradiction_penalty=0.1)
check(extended != base, "score_extended produces a different number than score_generative_agents for the same record -- they are not aliases")
expected_extended = base + 0.9 + 1.0 + 0.2 - 0.1 - 0.0
check(abs(extended - expected_extended) < 1e-9, "score_extended matches an independent hand recomputation of the article's own proposed formula exactly", f"expected={expected_extended!r} actual={extended!r}")

rec_ext2 = mk("ext-2", importance=5.0, confidence=0.9, authority="system_inferred", embedding=(1.0, 0.0), created_at=NOW, last_accessed_at=NOW)
extended_unknown_authority = score_extended(rec_ext2, query_emb, now=NOW)
rec_ext3 = mk("ext-3", importance=5.0, confidence=0.9, authority="user_explicit", embedding=(1.0, 0.0), created_at=NOW, last_accessed_at=NOW)
extended_user_authority = score_extended(rec_ext3, query_emb, now=NOW)
check(extended_user_authority > extended_unknown_authority, "user_explicit authority scores strictly higher than system_inferred authority, as this build's stated convention requires")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
