# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Session memory — wires /builds/agent-memory-layer/'s real,
#  tested MemoryStore/SQLiteMemoryStore into Jarvis as a standing-
#  preference layer, so "always size conservatively for NQ" or
#  "prefers EMA crossover signals" said once persists across
#  sessions instead of needing to be re-stated every query.
#  Generated: 2026-11-08 (round-3 next-move #1 on agent-memory-layer)
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: jarvis_memory.py                               ║
║      Role:      Thin wrapper giving jarvis_orchestrator.py's   ║
║                  tool-dispatch loop a persistent, tested place ║
║                  to store and recall standing trading          ║
║                  preferences                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

memory_layer.py and persistence.py here are COPIED IN UNMODIFIED from
/builds/agent-memory-layer/ — same convention prop_firm_sizing.py,
prop_firm_position_sizing.py, and prop_pass_simulator.py already follow
in this same directory: one real, already-tested implementation, reused
as a file copy rather than a package dependency, not a second
implementation with its own bugs to find.

DESIGN PRINCIPLE, matching positions_store.py's own stated one exactly:
this module assumes a SINGLE trader, not a multi-user deployment —
every memory is scoped to the fixed subject_id "trader" below. A real
multi-user deployment would need a real identity layer (this project
has none — no auth, no per-user config anywhere in trading-jarvis)
before per-subject scoping would mean anything; faking multi-tenancy on
top of a single-user system would be worse than not having it.

WHY remember_preference() NEVER AUTO-SUPERSEDES
A tempting shortcut would be: when a new preference arrives, scan
existing live preferences for anything "about the same topic" and
auto-supersede it. This module deliberately does NOT do that — there's
no real topic-matching here (no embeddings are ever computed in this
codebase; nothing in trading-jarvis calls an embedding model), so
"same topic" would have to be guessed from keyword overlap, which is
exactly the kind of fabricated-intelligence shortcut this project's own
rules warn against. Instead, recall_preferences() surfaces every live
preference with its memory_id, and Claude (which can actually read
and compare the text) decides whether something the user just said
should supersede a specific prior preference — then calls
supersede_preference() naming that exact memory_id. The mechanism is
real (memory_layer.supersede()'s own subject-mismatch guard and all);
the matching judgment stays with the model that can read, not a regex.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from memory_layer import MemoryRecord, MemoryStatus, score_candidates
from persistence import SQLiteMemoryStore

SUBJECT_ID = "trader"  # single-trader convention, see module docstring
MEMORY_DB_PATH = Path(__file__).parent / "jarvis_memory.sqlite3"

_store: SQLiteMemoryStore | None = None


def _get_store() -> SQLiteMemoryStore:
    global _store
    if _store is None:
        _store = SQLiteMemoryStore(MEMORY_DB_PATH)
    return _store


def remember_preference(content: str, importance: float = 5.0) -> dict:
    """Store a new standing preference as a RAW memory for the single
    trader this deployment serves. Always creates a NEW record — see
    the module docstring for why this never auto-supersedes anything."""
    store = _get_store()
    record = MemoryRecord(
        memory_id=str(uuid.uuid4()),
        type="semantic.preference",
        subject_id=SUBJECT_ID,
        content=content,
        created_at=time.time(),
        valid_from=time.time(),
        importance=importance,
        authority="user_explicit",  # the trader stated this directly, not inferred
    )
    store.add(record)
    return {"memory_id": record.memory_id, "content": record.content, "status": record.status.value}


def recall_preferences() -> list[dict]:
    """Return every live standing preference for the single trader,
    ranked via score_candidates() (recency+importance; relevance is a
    wash since this module never computes embeddings — see
    score_candidates()'s own documented behavior for an all-missing-
    embeddings pool). Returns memory_id on every row so Claude can name
    a specific one in a later supersede_preference() call."""
    store = _get_store()
    live = store.live_for_subject(SUBJECT_ID)
    if not live:
        return []
    ranked = score_candidates(live, query_embedding=(), now=time.time())
    return [
        {
            "memory_id": r.memory_id,
            "content": r.content,
            "importance": r.importance,
            "status": r.status.value,
            "created_at": r.created_at,
            "relevance_rank_score": round(score, 4),
        }
        for r, score in ranked
    ]


def supersede_preference(old_memory_id: str, new_content: str, importance: float = 5.0) -> dict:
    """Replace one specific prior preference (named by memory_id, as
    returned from recall_preferences()) with a new one — the real
    memory_layer.supersede(): the old record is marked SUPERSEDED (never
    deleted), not merged or silently overwritten."""
    store = _get_store()
    new_record = MemoryRecord(
        memory_id=str(uuid.uuid4()),
        type="semantic.preference",
        subject_id=SUBJECT_ID,
        content=new_content,
        created_at=time.time(),
        valid_from=time.time(),
        importance=importance,
        authority="user_explicit",
    )
    store.supersede(old_memory_id, new_record, now=time.time())
    return {
        "superseded_memory_id": old_memory_id,
        "new_memory_id": new_record.memory_id,
        "new_content": new_record.content,
    }
