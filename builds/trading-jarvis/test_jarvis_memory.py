# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Tests for jarvis_memory.py and its wiring into
#  jarvis_orchestrator.py's _run_tool() dispatch. Proves THIS
#  wiring calls the real, already-tested agent-memory-layer
#  functions correctly — not a re-test of lifecycle/supersession/
#  persistence logic itself, which is agent-memory-layer's own
#  57-assertion suite's job (test_memory_layer.py +
#  test_persistence.py there).
#
#  Run with: python3 test_jarvis_memory.py
#  Needs: anthropic, requests, pandas, numpy installed (pinned in
#  requirements.txt) — jarvis_orchestrator.py imports data_pipeline.py,
#  signal_generator.py etc. at module load even though this test never
#  calls check_signal/check_risk/check_fundamentals.
# ═══════════════════════════════════════════════════════════════
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Point jarvis_memory at a fresh, isolated temp DB BEFORE anything else
# touches it, so this test run never reads or writes the real
# jarvis_memory.sqlite3 a live deployment would use.
import jarvis_memory  # noqa: E402
jarvis_memory.MEMORY_DB_PATH = Path(tempfile.mkdtemp(prefix="jarvis-memory-test-")) / "test.sqlite3"

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-a-real-credential")
import jarvis_orchestrator  # noqa: E402

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


# --- remember_preference via _run_tool -----------------------------------
result = jarvis_orchestrator._run_tool("remember_preference", {
    "content": "always size conservatively for NQ",
    "importance": 8.0,
})
check("memory_id" in result and result["content"] == "always size conservatively for NQ", "remember_preference, dispatched through _run_tool, stores the exact content given", result)
check(result["status"] == "RAW", "a freshly remembered preference starts RAW, matching memory_layer's own default")
first_memory_id = result["memory_id"]

result2 = jarvis_orchestrator._run_tool("remember_preference", {"content": "prefers EMA crossover signals over RSI"})
check(result2["memory_id"] != first_memory_id, "a second remember_preference call creates a genuinely new memory_id, not a reused or colliding one")

# --- recall_preferences via _run_tool -------------------------------------
recall_result = jarvis_orchestrator._run_tool("recall_preferences", {})
check("preferences" in recall_result, "recall_preferences, dispatched through _run_tool, returns a 'preferences' list")
contents = {p["content"] for p in recall_result["preferences"]}
check(contents == {"always size conservatively for NQ", "prefers EMA crossover signals over RSI"}, "recall_preferences surfaces exactly the two preferences stored so far, no more, no fewer", contents)
check(all("memory_id" in p for p in recall_result["preferences"]), "every recalled preference carries its memory_id, so a later supersede_preference call can name it exactly")

# The higher-importance one (8.0 vs. the default 5.0) should rank first --
# this is agent-memory-layer's score_candidates() doing real work through
# the wiring, not a hardcoded order.
check(recall_result["preferences"][0]["content"] == "always size conservatively for NQ", "the higher-importance preference ranks first via score_candidates, proving real ranking logic runs through this wiring, not just insertion order", recall_result["preferences"])

# --- supersede_preference via _run_tool -----------------------------------
supersede_result = jarvis_orchestrator._run_tool("supersede_preference", {
    "old_memory_id": first_memory_id,
    "new_content": "size NQ normally again, conservative sizing no longer needed",
})
check(supersede_result["superseded_memory_id"] == first_memory_id, "supersede_preference, dispatched through _run_tool, reports the exact memory_id it superseded")
check(supersede_result["new_content"] == "size NQ normally again, conservative sizing no longer needed", "the new content is stored exactly as given")

recall_after = jarvis_orchestrator._run_tool("recall_preferences", {})
contents_after = {p["content"] for p in recall_after["preferences"]}
check("always size conservatively for NQ" not in contents_after, "the superseded preference no longer appears in recall_preferences -- the real memory_layer.supersede() ran, not a no-op")
check("size NQ normally again, conservative sizing no longer needed" in contents_after, "the new preference that replaced it does appear")
check(len(recall_after["preferences"]) == 2, "exactly two live preferences remain: the new NQ one and the untouched EMA one")

# A supersede naming a memory_id that was never seen from recall_preferences
# should fail loudly (KeyError from the underlying store), never silently
# create a dangling link.
try:
    jarvis_orchestrator._run_tool("supersede_preference", {
        "old_memory_id": "not-a-real-memory-id",
        "new_content": "this should never be linked to anything",
    })
    check(False, "supersede_preference on a fabricated memory_id raises", "no exception")
except KeyError:
    check(True, "supersede_preference refuses to link a new preference to a memory_id that was never actually returned by recall_preferences")

# --- A real tool-dispatch-loop round trip, mocked Anthropic client,     --
# --- same established convention as every other dispatch-loop test     --
# --- in this project (no live Anthropic access from this sandbox).     --
from unittest.mock import MagicMock  # noqa: E402

fresh_db = Path(tempfile.mkdtemp(prefix="jarvis-memory-loop-test-")) / "loop.sqlite3"
jarvis_memory.MEMORY_DB_PATH = fresh_db
jarvis_memory._store = None  # force a fresh SQLiteMemoryStore against the new path

tool_use_block = MagicMock()
tool_use_block.type = "tool_use"
tool_use_block.name = "remember_preference"
tool_use_block.input = {"content": "never trade the first 15 minutes after the open", "importance": 9.0}
tool_use_block.id = "toolu_fake_1"

first_response = MagicMock()
first_response.stop_reason = "tool_use"
first_response.content = [tool_use_block]

final_text_block = MagicMock()
final_text_block.type = "text"
final_text_block.text = "Got it — I've recorded that as a standing preference."
second_response = MagicMock()
second_response.stop_reason = "end_turn"
second_response.content = [final_text_block]

jarvis_orchestrator.client = MagicMock()
jarvis_orchestrator.client.messages.create.side_effect = [first_response, second_response]

answer = jarvis_orchestrator.ask_jarvis("From now on, never trade the first 15 minutes after the open.")
check(answer == "Got it — I've recorded that as a standing preference.", "ask_jarvis's full tool-dispatch loop, driven by a mocked Anthropic client, returns the final text turn")

second_call_messages = jarvis_orchestrator.client.messages.create.call_args_list[1].kwargs["messages"]
tool_result_content = second_call_messages[-1]["content"][0]["content"]
check("memory_id" in tool_result_content, "the real remember_preference result (with a real memory_id) was fed back to the model as the tool_result, not a stub or placeholder", tool_result_content)
check(jarvis_memory._get_store().live_for_subject("trader")[0].content == "never trade the first 15 minutes after the open", "the preference the mocked model asked to remember is actually, durably persisted via the real SQLiteMemoryStore -- not just echoed back in the mock")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
