"""Deterministic verification: a real subprocess exit code and ASan trace
decide whether a crash is real, never an agent's claim about it.

This is the single load-bearing idea pulled out of "Building an Agentic
Security Pipeline That Finds, Proves, and Patches Vulnerabilities" (Fareed
Khan): discovery is allowed to be noisy, but nothing is marked a confirmed
finding unless the host independently re-runs the proof-of-concept and
sees AddressSanitizer fire. The agent's own report of what happened is
never trusted.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class DetonationResult:
    exit_code: int
    stdout: str
    stderr: str
    crashed: bool
    crash_type: str | None = None
    top_frame: str | None = None


_SUMMARY_RE = re.compile(r"SUMMARY:\s*AddressSanitizer:\s*([a-zA-Z0-9_\-]+)")
_FRAME_RE = re.compile(r"#\d+\s+0x[0-9a-f]+\s+in\s+(\S+)\s+(\S+\.c:\d+)")
_ASAN_RUNTIME = ("__asan", "__interceptor", "__sanitizer", "memcpy", "memmove", "memset")


def detonate(binary: str, input_path: str, timeout: float = 10.0) -> DetonationResult:
    """Run `binary input_path` for real under ASan and report what actually happened.

    A crash is decided by the exit code (SIGABRT == 134 under
    abort_on_error=1) and corroborated by an AddressSanitizer SUMMARY line,
    never by text matching alone -- a program that prints the literal
    string "AddressSanitizer" in ordinary output must not be mistaken for
    a crash.
    """
    env = {"ASAN_OPTIONS": "abort_on_error=1:detect_leaks=0:halt_on_error=1"}
    try:
        proc = subprocess.run(
            [binary, input_path],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return DetonationResult(
            exit_code=-1, stdout=exc.stdout or "", stderr=exc.stderr or "",
            crashed=True, crash_type="timeout",
        )

    combined = proc.stdout + "\n" + proc.stderr
    summary = _SUMMARY_RE.search(combined)
    crashed = proc.returncode not in (0, 1) and summary is not None

    top_frame = None
    for func, loc in _FRAME_RE.findall(combined):
        if any(p in func for p in _ASAN_RUNTIME):
            continue
        top_frame = f"{func} {loc}"
        break

    return DetonationResult(
        exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr,
        crashed=crashed, crash_type=summary.group(1) if summary else None,
        top_frame=top_frame,
    )


@dataclass
class GraderVerdict:
    passed: bool
    reproductions: int
    evidence: str


def verify_crash(binary: str, input_path: str, runs: int = 3) -> GraderVerdict:
    """Re-detonate the same input `runs` times in fresh calls; require a
    majority to crash before calling a finding reproducible. One flaky
    crash is not a finding."""
    crashed = sum(1 for _ in range(runs) if detonate(binary, input_path).crashed)
    passed = crashed >= (runs // 2 + 1)
    return GraderVerdict(
        passed=passed, reproductions=crashed,
        evidence=f"{crashed}/{runs} detonations crashed",
    )


@dataclass
class PatchVerdict:
    builds: bool = False
    poc_stops: bool = False
    benign_still_works: bool = False

    @property
    def passed(self) -> bool:
        return self.builds and self.poc_stops and self.benign_still_works


def grade_patch(
    build_fn, patched_binary: str, poc_path: str, benign_path: str,
) -> PatchVerdict:
    """The patch ladder: compiles, the original crashing input no longer
    crashes it, and a known-benign input still behaves normally. All three
    must hold -- a patch that merely silences the crash by truncating all
    output (or by segfaulting differently) is still a fail if the benign
    check breaks."""
    v = PatchVerdict()
    v.builds = build_fn()
    if not v.builds:
        return v
    v.poc_stops = not detonate(patched_binary, poc_path).crashed
    if not v.poc_stops:
        return v
    benign = detonate(patched_binary, benign_path)
    v.benign_still_works = (not benign.crashed) and benign.exit_code == 0
    return v
