"""End-to-end orchestration: discovery -> host re-detonation (never trust
the agent's claim) -> triage -> patch -> patch ladder. Run directly:

    python3 run_defender_loop.py

Prints a trace in the same spirit as the source article's own log lines,
but every number here comes from a real compiled binary and a real
AddressSanitizer run, not a script.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from agent_stub import ScriptedDiscoveryAgent, propose_bad_fix_alpha, propose_fix_alpha
from dispatcher import AllowListDispatcher, ToolResult, ToolSpec
from verifier import GraderVerdict, detonate, grade_patch, verify_crash

HERE = os.path.dirname(os.path.abspath(__file__))
CANARY_DIR = os.path.join(HERE, "canary")
CANARY_SRC = os.path.join(CANARY_DIR, "canary.c")
CANARY_BIN = os.path.join(CANARY_DIR, "entry")


def write_poc(tmpdir: str, name: str, data: bytes) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def build_canary(src_path: str, bin_path: str) -> bool:
    proc = subprocess.run(
        ["gcc", "-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer",
         "-o", bin_path, src_path],
        capture_output=True, text=True,
    )
    return proc.returncode == 0


def make_dispatcher(allow_mutating: bool, allow_egress: bool) -> AllowListDispatcher:
    tools = {
        "run_in_sandbox": ToolSpec("run_in_sandbox", lambda **kw: "ran", mutating=False, egress=False),
        "write_poc": ToolSpec("write_poc", lambda **kw: "wrote", mutating=True, egress=False),
        "post_to_slack": ToolSpec("post_to_slack", lambda **kw: "posted", mutating=False, egress=True),
    }
    return AllowListDispatcher(
        tools, allowed_names=set(tools), allow_mutating=allow_mutating, allow_egress=allow_egress,
    )


def discover_and_verify(tmpdir: str) -> dict[str, GraderVerdict]:
    """Runs two scripted discovery agents -- one honest, one not -- against
    the two planted bugs, and shows the host's re-detonation is what
    actually decides the outcome in both cases."""
    results: dict[str, GraderVerdict] = {}

    alpha_poc = b"A" + bytes([255]) + b"\x00" * 40
    agent_a = ScriptedDiscoveryAgent("parse_alpha", alpha_poc, honest=True)
    poc_path = write_poc(tmpdir, "poc_alpha.bin", agent_a.poc_bytes)
    real = detonate(CANARY_BIN, poc_path)
    claim = agent_a.claim(actually_crashed=real.crashed)
    print(f"[discovery] parse_alpha agent self-reports crash={claim.self_reported_crash} "
          f"(honest={agent_a.honest})")
    print(f"[host]      independent detonation: crashed={real.crashed} type={real.crash_type}")
    verdict = verify_crash(CANARY_BIN, poc_path)
    print(f"[verify]    {verdict.evidence} -> passed={verdict.passed}")
    results["parse_alpha"] = verdict

    bravo_poc = b"B" + bytes([255]) + b"A"
    agent_b_lying = ScriptedDiscoveryAgent("parse_bravo", bravo_poc, honest=False)
    poc_path_b = write_poc(tmpdir, "poc_bravo.bin", agent_b_lying.poc_bytes)
    real_b = detonate(CANARY_BIN, poc_path_b)
    claim_b = agent_b_lying.claim(actually_crashed=real_b.crashed)
    print(f"\n[discovery] parse_bravo agent self-reports crash={claim_b.self_reported_crash} "
          f"(honest={agent_b_lying.honest}, so this is a LIE: real result is crashed={real_b.crashed})")
    print(f"[host]      independent detonation: crashed={real_b.crashed} type={real_b.crash_type}")
    verdict_b = verify_crash(CANARY_BIN, poc_path_b)
    print(f"[verify]    {verdict_b.evidence} -> passed={verdict_b.passed} "
          f"(the lie changed nothing -- the host never read the claim)")
    results["parse_bravo"] = verdict_b

    return results


def patch_alpha(tmpdir: str) -> tuple[bool, bool]:
    """Runs the patch ladder against a correct fix and a cosmetic non-fix,
    proving the ladder actually discriminates between them."""
    with open(CANARY_SRC) as fh:
        source = fh.read()

    good = propose_fix_alpha(source)
    good_src = write_poc(tmpdir, "good_fix.c", good.patched_source.encode())
    good_bin = os.path.join(tmpdir, "good_entry")
    good_verdict = grade_patch(
        build_fn=lambda: build_canary(good_src, good_bin),
        patched_binary=good_bin,
        poc_path=write_poc(tmpdir, "poc_alpha2.bin", b"A" + bytes([255]) + b"\x00" * 40),
        benign_path=write_poc(tmpdir, "benign.bin", b"A\x02xx"),
    )
    print(f"\n[patch]     good fix ({good.description}): "
          f"builds={good_verdict.builds} poc_stops={good_verdict.poc_stops} "
          f"benign_ok={good_verdict.benign_still_works} -> passed={good_verdict.passed}")

    bad = propose_bad_fix_alpha(source)
    bad_src = write_poc(tmpdir, "bad_fix.c", bad.patched_source.encode())
    bad_bin = os.path.join(tmpdir, "bad_entry")
    bad_verdict = grade_patch(
        build_fn=lambda: build_canary(bad_src, bad_bin),
        patched_binary=bad_bin,
        poc_path=write_poc(tmpdir, "poc_alpha3.bin", b"A" + bytes([255]) + b"\x00" * 40),
        benign_path=write_poc(tmpdir, "benign2.bin", b"A\x02xx"),
    )
    print(f"[patch]     bad fix ({bad.description}): "
          f"builds={bad_verdict.builds} poc_stops={bad_verdict.poc_stops} "
          f"benign_ok={bad_verdict.benign_still_works} -> passed={bad_verdict.passed} "
          f"(correctly rejected: it never touches the real memcpy)")

    return good_verdict.passed, bad_verdict.passed


def demo_dispatcher() -> None:
    print("\n[dispatcher] tool-gating demo")
    locked = make_dispatcher(allow_mutating=False, allow_egress=False)
    r1 = locked.dispatch("write_poc", data=b"x")
    print(f"  write_poc with mutation disabled -> ok={r1.ok} error={r1.error!r}")
    r2 = locked.dispatch("post_to_slack", to="#team")
    print(f"  post_to_slack with egress disabled -> ok={r2.ok} error={r2.error!r}")
    r3 = locked.dispatch("delete_everything")
    print(f"  unknown tool -> ok={r3.ok} error={r3.error!r}")

    opened = make_dispatcher(allow_mutating=True, allow_egress=True)
    r4 = opened.dispatch("write_poc", data=b"x")
    print(f"  write_poc with mutation enabled -> ok={r4.ok} content={r4.content!r}")


def main() -> None:
    assert build_canary(CANARY_SRC, CANARY_BIN), "canary failed to build"
    with tempfile.TemporaryDirectory() as tmpdir:
        results = discover_and_verify(tmpdir)
        good_passed, bad_passed = patch_alpha(tmpdir)
        demo_dispatcher()

    print("\n=== SUMMARY ===")
    for name, v in results.items():
        print(f"  {name}: verified={v.passed} ({v.evidence})")
    print(f"  good patch passed ladder: {good_passed}")
    print(f"  bad patch passed ladder:  {bad_passed} (expected False)")


if __name__ == "__main__":
    main()
