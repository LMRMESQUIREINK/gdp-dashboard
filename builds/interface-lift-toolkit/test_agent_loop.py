"""
End-to-end test of run_agent() against a MOCKED Anthropic client — same
pattern this project has used for every tool-dispatch loop since
/builds/trading-jarvis/jarvis_orchestrator.py, because this sandbox has
no live Anthropic API access (same restriction stated for every other
build here). The mock stands in for client.messages.create() and returns
a scripted sequence of responses shaped exactly like the real SDK's:
a tool_use turn, then a final text turn. What's tested is real: the
registry dispatches the call to the real prop_firm_sizing code, the
approval gate really holds an outward call, and the messages list is
really built up turn by turn the way the real loop would build it.

Run with:
    python3 test_agent_loop.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from binary_metadata_tools import register_binary_metadata_tools
from tools_demo import register_demo_tools

from toolkit.approval import ApprovalGate
from toolkit.ledger import TaskCounters
from toolkit.loop import run_agent
from toolkit.registry import ToolRegistry

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    id: str = "toolu_1"


@dataclass
class FakeResponse:
    stop_reason: str
    content: list


class MockAnthropicClient:
    """Stands in for `anthropic.Anthropic()`. `.messages.create(...)`
    pops the next scripted response and records every call it was made
    with, so the test can assert on exactly what the loop sent."""

    def __init__(self, scripted_responses: list[FakeResponse]):
        self._responses = list(scripted_responses)
        self.calls: list[dict] = []
        self.messages = self

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self._responses.pop(0)


def main() -> None:
    registry = ToolRegistry()
    gate = ApprovalGate()
    register_demo_tools(registry)
    register_binary_metadata_tools(registry)

    # ── scripted turn 1: Claude asks for prop_firm_size_check ───────────
    print("=== run_agent: a local tool call, then a final answer ===")
    client = MockAnthropicClient([
        FakeResponse(stop_reason="tool_use", content=[
            FakeBlock(type="tool_use", name="prop_firm_size_check",
                      input={"tier": "50K", "symbol": "ES", "contracts": 1}, id="toolu_1"),
        ]),
        FakeResponse(stop_reason="end_turn", content=[
            FakeBlock(type="text", text="1 contract on 50K ES is within the 25% rule."),
        ]),
    ])
    counters = TaskCounters()
    answer = run_agent("check sizing for 1 ES contract on a 50K account", client, "claude-opus-5",
                        registry, gate, system="test system prompt", counters=counters)

    check("final answer is the scripted text", answer == "1 contract on 50K ES is within the 25% rule.")
    check("exactly 2 model calls were made (matches the 2 scripted responses)",
          len(client.calls) == 2 and counters.model_calls == 2)
    check("exactly 1 real tool call was made", counters.tool_calls == 1)

    # The second model call's messages must contain the real tool_result,
    # not a placeholder — prove the registry's real computation flowed back.
    second_call_messages = client.calls[1]["messages"]
    tool_result_msg = next(m for m in second_call_messages if m["role"] == "user" and isinstance(m["content"], list))
    tool_result_content = tool_result_msg["content"][0]["content"]
    check("the real tool result (not a stub) was fed back to the model",
          "size_rule" in tool_result_content and "within_rule" in tool_result_content,
          detail=tool_result_content)

    # ── scripted turn: Claude asks for the OUTWARD tool, unapproved ──────
    print("\n=== run_agent: an outward tool call is held, never executed inline ===")
    client2 = MockAnthropicClient([
        FakeResponse(stop_reason="tool_use", content=[
            FakeBlock(type="tool_use", name="publish_report",
                      input={"filename": "agent_test.txt", "body": "hello from run_agent"}, id="toolu_2"),
        ]),
        FakeResponse(stop_reason="end_turn", content=[
            FakeBlock(type="text", text="Ready to publish — waiting for your yes."),
        ]),
    ])
    counters2 = TaskCounters()
    run_agent("publish a report", client2, "claude-opus-5", registry, gate,
              system="test system prompt", counters=counters2)
    check("an outward call makes zero real tool calls (held, not executed)", counters2.tool_calls == 0,
          detail=f"tool_calls={counters2.tool_calls}")
    second_call_messages2 = client2.calls[1]["messages"]
    held_msg = next(m for m in second_call_messages2 if m["role"] == "user" and isinstance(m["content"], list))
    held_content = held_msg["content"][0]["content"]
    check("the held call's own pending preview came back, not a stub error",
          '"pending"' in held_content and "agent_test.txt" in held_content, detail=held_content)
    import os
    check("the file was NOT actually written (approval was never granted)",
          not os.path.exists("outbox/agent_test.txt"))

    # ── scripted turn: Claude asks for go_buildinfo_check on a real binary ──
    if shutil.which("go"):
        print("\n=== run_agent: a local binary-metadata tool call, against a real Go binary ===")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "go.mod").write_text("module example.com/agentlooptest\n\ngo 1.21\n")
            (root / "main.go").write_text("package main\n\nfunc main() {}\n")
            bin_path = root / "agentlooptest_bin"
            subprocess.run(["go", "build", "-o", str(bin_path), "."], cwd=root, check=True, capture_output=True)

            client3 = MockAnthropicClient([
                FakeResponse(stop_reason="tool_use", content=[
                    FakeBlock(type="tool_use", name="go_buildinfo_check",
                              input={"binary_path": str(bin_path)}, id="toolu_3"),
                ]),
                FakeResponse(stop_reason="end_turn", content=[
                    FakeBlock(type="text", text="That binary was built with the Go toolchain."),
                ]),
            ])
            counters3 = TaskCounters()
            answer3 = run_agent("is this binary built with Go?", client3, "claude-opus-5",
                                 registry, gate, system="test system prompt", counters=counters3)
            check("final answer is the scripted text", answer3 == "That binary was built with the Go toolchain.")
            check("exactly 1 real tool call was made", counters3.tool_calls == 1)

            direct = registry.call("go_buildinfo_check", binary_path=str(bin_path))
            second_call_messages3 = client3.calls[1]["messages"]
            tool_result_msg3 = next(
                m for m in second_call_messages3 if m["role"] == "user" and isinstance(m["content"], list)
            )
            tool_result_content3 = tool_result_msg3["content"][0]["content"]
            check("the real go_buildinfo_check result (not a stub) was fed back to the model",
                  direct["module_path"] in tool_result_content3 and direct["go_version"] in tool_result_content3,
                  detail=tool_result_content3)
    else:
        print("\n=== run_agent: binary-metadata tool call check: SKIPPED (no go toolchain) ===")

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
