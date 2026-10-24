"""A scripted stand-in for the LLM in the source article's defender loop.

This sandbox has no live model API (the standing restriction noted
throughout this project), so the "agent" here is deterministic Python that
plays the same role: it proposes a proof-of-concept and a patch, and it
can be told to self-report truthfully or dishonestly. The orchestrator
below never trusts that self-report -- it always calls the host's own
`detonate()` independently, which is the one rule this whole build exists
to prove out.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiscoveryClaim:
    poc_bytes: bytes
    self_reported_crash: bool
    focus_area: str


class ScriptedDiscoveryAgent:
    """Proposes a PoC for a named focus area. `honest=False` simulates a
    model that claims a crash occurred when its own PoC does not actually
    trigger one -- exactly the failure mode the article's adversarial-
    verifier section showed a *real* 7B model falling into (voting
    FALSE_POSITIVE on a provably crashing bug). Here we invert it: an
    agent that over-claims success. Either direction is why the host
    re-detonates instead of trusting self-reports."""

    def __init__(self, focus_area: str, poc_bytes: bytes, honest: bool = True) -> None:
        self.focus_area = focus_area
        self.poc_bytes = poc_bytes
        self.honest = honest

    def claim(self, actually_crashed: bool) -> DiscoveryClaim:
        reported = actually_crashed if self.honest else not actually_crashed
        return DiscoveryClaim(
            poc_bytes=self.poc_bytes,
            self_reported_crash=reported,
            focus_area=self.focus_area,
        )


@dataclass
class PatchProposal:
    description: str
    patched_source: str


def propose_fix_alpha(source: str) -> PatchProposal:
    """A root-cause fix: clamp the copy length to the destination's real
    size before the copy, matching the article's own stated recipe for a
    buffer overflow ('clamp the copy length to the destination size
    BEFORE the copy')."""
    fixed = source.replace(
        "size_t claimed = data[0];\n    char *buf = (char *)malloc(8);",
        "size_t claimed = data[0];\n    if (claimed > 8) claimed = 8;\n    char *buf = (char *)malloc(8);",
    )
    return PatchProposal(description="clamp claimed length to 8 before the copy", patched_source=fixed)


def propose_bad_fix_alpha(source: str) -> PatchProposal:
    """A fix that only treats the symptom: it shrinks the printed count
    but leaves the real memcpy untouched, so the overflow still happens.
    Used to prove the patch ladder actually fails bad patches rather than
    passing anything that merely looks different."""
    fixed = source.replace(
        'printf("alpha copied %zu bytes\\n", claimed);',
        'printf("alpha copied %zu bytes\\n", claimed > 8 ? 8 : claimed);',
    )
    return PatchProposal(description="(bad) cosmetic: only clamps the printed count", patched_source=fixed)
