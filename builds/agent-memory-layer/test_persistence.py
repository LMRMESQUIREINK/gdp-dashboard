"""Tests for persistence.py's SQLiteMemoryStore -- including a real
cross-process restart test, not just a second in-process object, since
the whole point of this module is surviving a process restart.

Run with: python3 test_persistence.py
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_layer import MemoryRecord, MemoryStatus, IllegalTransitionError  # noqa: E402
from persistence import SQLiteMemoryStore  # noqa: E402

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


tmpdir = tempfile.mkdtemp(prefix="agent-memory-layer-test-")
db_path = Path(tmpdir) / "memory.sqlite3"

# --- Basic add/get round-trip, including every field ---------------------
store = SQLiteMemoryStore(db_path)
rec = mk(
    "a", content="prefers Flask", importance=7.0, confidence=0.8,
    authority="user_explicit", scope="project", embedding=(0.1, 0.2, 0.3),
    last_accessed_at=123.0, valid_until=999.0,
)
store.add(rec)
fetched = store.get("a")
check(fetched.memory_id == "a" and fetched.content == "prefers Flask", "a saved record round-trips with the right id and content")
check(fetched.importance == 7.0 and fetched.confidence == 0.8, "numeric fields round-trip exactly")
check(fetched.authority == "user_explicit" and fetched.scope == "project", "string fields round-trip exactly")
check(fetched.embedding == (0.1, 0.2, 0.3), "the embedding tuple round-trips through JSON exactly, not corrupted or dropped", fetched.embedding)
check(fetched.valid_until == 999.0 and fetched.last_accessed_at == 123.0, "optional float fields round-trip exactly")
check(fetched.status == MemoryStatus.RAW, "a fresh record persists as RAW")

rec_no_embedding = mk("b", content="no embedding here")
store.add(rec_no_embedding)
check(store.get("b").embedding is None, "a record with no embedding round-trips as None, not an empty list or a crash")

try:
    store.get("does-not-exist")
    check(False, "get() on a missing memory_id raises", "no exception")
except KeyError:
    check(True, "get() on a missing memory_id raises KeyError, matching MemoryStore.get's dict semantics")

try:
    store.add(mk("a", content="duplicate"))
    check(False, "add() on a duplicate memory_id raises", "no exception")
except ValueError:
    check(True, "add() refuses a duplicate memory_id rather than silently overwriting, matching MemoryStore")

# --- transition() persists AND logs to the transitions WAL table --------
store.transition("a", MemoryStatus.ACTIVE)
check(store.get("a").status == MemoryStatus.ACTIVE, "transition() persists the new status")
wal = store.transitions_for("a")
check(len(wal) == 2, "transitions_for returns the full history: the initial (none)->RAW row plus RAW->ACTIVE", wal)
check(wal[0]["to_status"] == "RAW" and wal[1]["from_status"] == "RAW" and wal[1]["to_status"] == "ACTIVE", "the WAL rows are in order and record the real from/to statuses", wal)

try:
    store.transition("a", MemoryStatus.RAW)
    check(False, "an illegal transition through the store raises", "no exception")
except IllegalTransitionError:
    check(True, "transition() on the store still enforces memory_layer's own legality rules (ACTIVE can't go back to RAW)")
check(store.get("a").status == MemoryStatus.ACTIVE, "a rejected transition leaves the persisted record unchanged")

# --- supersede() persists both sides and logs it -------------------------
old = mk("pref-1", content="prefers Flask", created_at=0.0, valid_from=0.0)
store.add(old)
new = mk("pref-2", content="prefers FastAPI", created_at=1000.0, valid_from=1000.0)
store.supersede("pref-1", new, now=1000.0)
check(store.get("pref-1").status == MemoryStatus.SUPERSEDED, "supersede() persists the old record's new SUPERSEDED status")
check(store.get("pref-1").valid_until == 1000.0, "supersede() persists the closed validity window")
check(store.get("pref-2").supersedes == "pref-1", "supersede() persists the new record's link back to the old one")

different_subject = mk("pref-other", subject_id="user_2", created_at=2000.0, valid_from=2000.0)
try:
    store.supersede("pref-1", different_subject, now=2000.0)
    check(False, "supersede() across different subjects raises", "no exception")
except ValueError:
    check(True, "the store's supersede() still enforces memory_layer's subject-mismatch guard")

# --- live_for_subject matches MemoryStore's own semantics ----------------
live = store.live_for_subject("user_1")
live_ids = {r.memory_id for r in live}
check("pref-2" in live_ids and "pref-1" not in live_ids, "live_for_subject excludes the superseded record and includes the new one", live_ids)
check("a" in live_ids, "live_for_subject includes an ACTIVE record (a live status)")
unrelated = mk("other-user", subject_id="user_2", content="prefers Go")
store.add(unrelated)
check("other-user" not in {r.memory_id for r in store.live_for_subject("user_1")}, "a different subject's memory never leaks into this subject's live results")

store.close()

# ---------------------------------------------------------------------
# THE test that actually proves persistence: a real subprocess writes
# records and exits, then THIS process opens a fresh connection to the
# same file and confirms the data is there. Two in-process objects
# sharing one Python process would not prove this -- it has to cross a
# real process boundary, the same discipline agent-checkpoint-layer's
# crash-recovery test uses (a real os._exit(1), not a mocked one).
# ---------------------------------------------------------------------
cross_process_db = Path(tmpdir) / "cross_process.sqlite3"
writer_script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent)!r})
from persistence import SQLiteMemoryStore
from memory_layer import MemoryRecord, MemoryStatus

store = SQLiteMemoryStore({str(cross_process_db)!r})
store.add(MemoryRecord(
    memory_id="cross-1", type="semantic.preference", subject_id="trader",
    content="always size conservatively for NQ", created_at=0.0, valid_from=0.0,
    importance=8.0,
))
store.transition("cross-1", MemoryStatus.ACTIVE)
store.add(MemoryRecord(
    memory_id="cross-2", type="semantic.preference", subject_id="trader",
    content="prefers EMA crossover signals", created_at=1.0, valid_from=1.0,
    importance=6.0,
))
store.close()
"""
result = subprocess.run([sys.executable, "-c", writer_script], capture_output=True, text=True, timeout=30)
check(result.returncode == 0, "the writer subprocess exits cleanly", result.stderr[-500:] if result.returncode != 0 else "")

# A brand new store object, in THIS process, pointed at the same file --
# never touched by the writer process's own in-memory connection.
reader = SQLiteMemoryStore(cross_process_db)
live_after_restart = reader.live_for_subject("trader")
live_contents = {r.memory_id: r for r in live_after_restart}
check(len(live_after_restart) == 2, "both records written by the OTHER process are visible after a real process boundary", [r.memory_id for r in live_after_restart])
check(live_contents.get("cross-1") is not None and live_contents["cross-1"].content == "always size conservatively for NQ", "the exact content written by the writer process round-trips correctly")
check(live_contents.get("cross-1") is not None and live_contents["cross-1"].status == MemoryStatus.ACTIVE, "the status transition made by the writer process (RAW->ACTIVE) is visible after the restart, not just the original RAW")
check(live_contents.get("cross-2") is not None and live_contents["cross-2"].importance == 6.0, "the second record's fields are intact after the restart")
wal_after_restart = reader.transitions_for("cross-1")
check(len(wal_after_restart) == 2, "the transition WAL written by the other process is also durable across the restart, not just the current-state snapshot", wal_after_restart)
reader.close()

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
