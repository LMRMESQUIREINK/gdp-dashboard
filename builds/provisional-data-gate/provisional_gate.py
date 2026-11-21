"""
A provenance-propagation + publish-gate for result trees that mark each
leaf {"v": value, "provisional": bool} -- the exact shape used by
FareedKhan-dev/transportive-ai's real results/derive.py.

That repo's own derive.py does half of this job correctly: every derived
number inherits `provisional=True` if ANY input it was computed from is
still provisional ("the flag is true as long as any input it reads is
provisional. Rates are recomputed from counts, never typed, so a real
story.json replaces every number at once" -- derive.py's own docstring).
And its README discloses, in a dedicated "Not done yet" section, that
`assets/oracles/` is empty, the fork commits are "stand-ins," and the
fold step from a real run to `results/story.json` "is still to write" --
meaning every number in results/ is provisional by the repo's own
admission, confirmed directly: all 288 records in the real
`results/story.json` and every leaf in `results/eval.json` carry
`"provisional": true`.

What the repo's own mechanism does NOT do is stop that provisional data
from being presented as finished. The companion Medium article built
from this exact repo prints detailed, confident receipts (specific
pass/fail counts, Wilson intervals, sha256 hashes, minute-level timings)
for dozens of these provisional numbers with zero disclosure -- except
one, right at the very end, in a "Known Limits" section, which concedes
the motivating issue's own author calls it "unlikely" and "a correctness
issue only." Every other provisional number in the piece ships with no
such note anywhere.

This module closes that real, generalizable gap: a `publish_check()`
that refuses to let a still-provisional value leave the building without
an explicit, matching disclosure -- the enforcement derive.py's own
propagation rule never got paired with.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Leaf:
    """A value plus whether it (or anything it was computed from) is
    still provisional."""
    value: Any
    provisional: bool


def combine(*leaves: Leaf, fn: Callable[..., Any]) -> Leaf:
    """Apply fn to the raw values. The result is provisional if ANY
    input is -- the exact rule transportive-ai's derive.py states in its
    own docstring, reimplemented as an enforced type rather than a
    comment developers must remember to honor."""
    if not leaves:
        raise ValueError("combine() needs at least one Leaf")
    return Leaf(fn(*(leaf.value for leaf in leaves)), any(leaf.provisional for leaf in leaves))


def load_leaf_tree(obj: Any) -> Any:
    """Parse a JSON-shaped object that uses transportive-ai's real
    {"v": ..., "provisional": ...} leaf convention into a tree of real
    Leaf objects, recursively, for dicts/lists of any depth. A plain
    value with no such shape passes through unchanged (not every field
    in a real results file is a leaf -- e.g. the comparison labels in
    meta.json's "arms" map are plain strings)."""
    if isinstance(obj, dict):
        if set(obj.keys()) == {"v", "provisional"} and isinstance(obj["provisional"], bool):
            return Leaf(load_leaf_tree(obj["v"]), obj["provisional"])
        return {k: load_leaf_tree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [load_leaf_tree(v) for v in obj]
    return obj


@dataclass(frozen=True)
class Claim:
    """One statement a report makes, pointing at the leaf(s) backing it."""
    claim_id: str
    text: str
    leaf: Leaf


@dataclass(frozen=True)
class Violation:
    claim_id: str
    text: str
    detail: str


def publish_check(claims: list[Claim], disclosed: set[str]) -> list[Violation]:
    """The gate. A claim built on provisional data is a violation unless
    its claim_id is explicitly in `disclosed` -- matching a real,
    reachable disclosure (e.g. a Known-Limits note), not a blanket
    exemption. A claim resting on fully-confirmed data never needs
    disclosure and is never flagged, even if listed in `disclosed` by
    mistake."""
    violations = []
    for claim in claims:
        if claim.leaf.provisional and claim.claim_id not in disclosed:
            violations.append(
                Violation(
                    claim.claim_id,
                    claim.text,
                    f"rests on provisional data (value={claim.leaf.value!r}) with no matching disclosure",
                )
            )
    return violations


def get_path(tree: Any, path: str) -> Leaf:
    """Walk a dotted path (e.g. 'arms.A4.opus.pass') into a loaded leaf
    tree and return the Leaf found there. Raises KeyError with the exact
    failing segment, not a bare dict KeyError, so a typo'd path is easy
    to diagnose against a large real results file."""
    node = tree
    walked = []
    for part in path.split("."):
        walked.append(part)
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"no such path: {'.'.join(walked)} (full path: {path})")
        node = node[part]
    if not isinstance(node, Leaf):
        raise KeyError(f"path {path} does not resolve to a leaf (got {type(node).__name__})")
    return node
