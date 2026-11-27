# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Tests for jarvis_okf.py and its wiring into
#  jarvis_orchestrator.py's _run_tool() dispatch. Proves THIS
#  wiring calls the real okf_navigator.py functions correctly
#  against the real okf_knowledge/ bundle -- not a re-test of
#  okf_navigator's own logic, which /builds/okf-navigator/'s own
#  41-assertion suite already covers.
#
#  Run with: python3 test_jarvis_okf.py
#  Needs: anthropic, requests, pandas, numpy, PyYAML installed
#  (pinned in requirements.txt) -- jarvis_orchestrator.py imports
#  data_pipeline.py, signal_generator.py etc. at module load even
#  though this test never calls check_signal/check_risk/check_fundamentals.
# ═══════════════════════════════════════════════════════════════
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-a-real-credential")
import jarvis_orchestrator  # noqa: E402
import jarvis_okf  # noqa: E402

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


# --- direct jarvis_okf.check_module_impact() calls -----------------------

result = jarvis_okf.check_module_impact("risk_manager.py")
check("report" in result, "check_module_impact resolves a real .py filename to the bundle's own concept file")
check(result["module"] == "risk-manager.md", "the resolved concept-file name matches the bundle's real naming convention")
check("risk-manager.md" in result["report"], "the report names the starting module")
check("jarvis-orchestrator.md" in result["report"], "risk_manager.py's real, grepped consumer (jarvis_orchestrator.py) appears within 2 hops")

result_md = jarvis_okf.check_module_impact("signal-generator.md", max_hops=1)
check(result_md["module"] == "signal-generator.md", "a bare concept-file name (not a .py filename) also resolves correctly")
check("risk-manager.md" in result_md["report"] and "jarvis-orchestrator.md" in result_md["report"],
      "signal_generator.py's two real, grepped consumers (risk_manager.py AND jarvis_orchestrator.py) both appear at exactly 1 hop",
      result_md["report"])

# Leaf module with no outgoing links in this bundle -- must not crash, and
# must report only itself.
leaf_result = jarvis_okf.check_module_impact("jarvis_orchestrator.py", max_hops=3)
check("jarvis-orchestrator.md" in leaf_result["report"], "the top-level orchestrator module itself appears")
check(leaf_result["report"].count("[") == 1, "the orchestrator has no modeled consumers in this bundle, so the report contains exactly one step", leaf_result["report"])

# Unknown module name -- a helpful error, not a raw KeyError/exception.
unknown_result = jarvis_okf.check_module_impact("not_a_real_module.py")
check("error" in unknown_result, "an unrecognized module name returns a plain error dict, not a raised exception")
check("known_modules" in unknown_result and len(unknown_result["known_modules"]) == 13,
      "the error response lists all 13 real modules in the bundle, so the caller can see valid options", unknown_result)

# Trust tier and staleness are real, not placeholders: every concept in
# this bundle was machine-verified this session, never human-reviewed --
# the report must say so honestly rather than overclaiming.
check("trust=machine-confirmed" in result["report"], "every concept in this bundle reports machine-confirmed, honestly reflecting that a grep ran, not a human review")
check("trust=human-reviewed" not in result["report"], "no concept in this bundle falsely claims human-reviewed status")
check("lifecycle=fresh" in result["report"], "every concept's stale_after (90 days out) means it reports fresh as of today")

# --- dispatched through jarvis_orchestrator._run_tool() -------------------

dispatched = jarvis_orchestrator._run_tool("check_module_impact", {"module": "data_pipeline.py"})
check(dispatched == jarvis_okf.check_module_impact("data_pipeline.py"),
      "check_module_impact, dispatched through _run_tool with the default max_hops, matches a direct call exactly")

dispatched_hops = jarvis_orchestrator._run_tool("check_module_impact", {"module": "memory_layer.py", "max_hops": 1})
check("persistence.md" in dispatched_hops["report"] and "jarvis-memory.md" in dispatched_hops["report"],
      "max_hops is honored through the dispatch: memory_layer's own real import graph has BOTH "
      "persistence.py AND jarvis_memory.py as direct (1-hop) consumers -- jarvis_memory.py genuinely "
      "imports from memory_layer.py directly, confirmed by the real grep this bundle was built from, "
      "not a 2-hop relationship as a first-draft assumption of this test wrongly expected",
      dispatched_hops["report"])

# A real, genuinely 2-hop-only relationship DOES exist in this bundle:
# jarvis_orchestrator.py never imports persistence.py directly -- only
# through jarvis_memory.py -- so at max_hops=1 from persistence.md, the
# orchestrator must NOT yet appear, and at max_hops=2 it must.
one_hop_from_persistence = jarvis_orchestrator._run_tool("check_module_impact", {"module": "persistence.py", "max_hops": 1})
check("jarvis-memory.md" in one_hop_from_persistence["report"] and "jarvis-orchestrator.md" not in one_hop_from_persistence["report"],
      "persistence.py's real 1-hop consumer (jarvis_memory.py) appears at max_hops=1, "
      "but its real 2-hop consumer (jarvis_orchestrator.py) does not yet",
      one_hop_from_persistence["report"])
two_hops_from_persistence = jarvis_orchestrator._run_tool("check_module_impact", {"module": "persistence.py", "max_hops": 2})
check("jarvis-orchestrator.md" in two_hops_from_persistence["report"],
      "the same 2-hop consumer (jarvis_orchestrator.py) does appear once max_hops is widened to 2",
      two_hops_from_persistence["report"])

# --- a real tool-dispatch-loop round trip, mocked Anthropic client,      --
# --- same established convention as every other dispatch-loop test      --
# --- in this project (no live Anthropic access from this sandbox).      --
from unittest.mock import MagicMock  # noqa: E402

tool_use_block = MagicMock()
tool_use_block.type = "tool_use"
tool_use_block.name = "check_module_impact"
tool_use_block.input = {"module": "positions_store.py", "max_hops": 2}
tool_use_block.id = "toolu_fake_okf_1"

first_response = MagicMock()
first_response.stop_reason = "tool_use"
first_response.content = [tool_use_block]

final_text_block = MagicMock()
final_text_block.type = "text"
final_text_block.text = "If you change positions_store.py, re-check jarvis_swamp_bridge.py and jarvis_orchestrator.py."
second_response = MagicMock()
second_response.stop_reason = "end_turn"
second_response.content = [final_text_block]

jarvis_orchestrator.client = MagicMock()
jarvis_orchestrator.client.messages.create.side_effect = [first_response, second_response]

answer = jarvis_orchestrator.ask_jarvis("What depends on positions_store.py in this codebase?")
check(answer == "If you change positions_store.py, re-check jarvis_swamp_bridge.py and jarvis_orchestrator.py.",
      "ask_jarvis's full tool-dispatch loop, driven by a mocked Anthropic client, returns the final text turn")

second_call_messages = jarvis_orchestrator.client.messages.create.call_args_list[1].kwargs["messages"]
tool_result_content = second_call_messages[-1]["content"][0]["content"]
check("jarvis-swamp-bridge.md" in tool_result_content and "jarvis-orchestrator.md" in tool_result_content,
      "the real check_module_impact result (both real, grepped consumers of positions_store.py) was fed "
      "back to the model as the tool_result, not a stub or placeholder",
      tool_result_content)

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
