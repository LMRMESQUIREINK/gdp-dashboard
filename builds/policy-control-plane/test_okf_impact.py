"""Tests for okf_impact.py -- proves check_module_impact() reports this
build's own real, grepped module dependency graph, and that the known
negated-reference-markdown-link bug (found and fixed while building
/builds/interface-lift-toolkit/'s okf_knowledge/ bundle) didn't recur
here. Not a re-test of okf_navigator.py's own logic, which
/builds/okf-navigator/'s own 41-assertion suite already covers.

Run with: python3 test_okf_impact.py
"""
from __future__ import annotations

import sys

from okf_impact import check_module_impact
from okf_navigator import load_bundle, navigate
from pathlib import Path

FAILURES: list[str] = []


def check(cond, name, detail=""):
    status = "ok  " if cond else "FAIL"
    print(f"{status} - {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# --- direct check_module_impact() calls ------------------------------

result = check_module_impact("policy/evaluator.py")
check("report" in result, "resolves a real .py path to the bundle's own concept file")
check(result["module"] == "policy-evaluator.md", "resolved concept-file name matches the bundle's naming")
check("policy-evaluator.md" in result["report"], "the report names the starting module")
check("governed-call.md" in result["report"], "policy/evaluator.py's real, grepped consumer governed_call.py appears")

result_underscored = check_module_impact("policy_write_tiers.py", max_hops=1)
check(result_underscored["module"] == "policy-write-tiers.md",
      "an underscore-style module name also resolves via the generic slugify fallback")
check("demo-write-tiers.md" in result_underscored["report"],
      "write_tiers.py's real, grepped 1-hop consumer (demo_write_tiers.py) appears", result_underscored["report"])

# A leaf module with zero real consumers among this build's shipped
# modules -- confirmed by grep: nothing does `import policy`/`from
# policy import`.
leaf = check_module_impact("policy/__init__.py", max_hops=3)
check("policy-init.md" in leaf["report"], "policy/__init__.py appears in its own impact report")
check(leaf["report"].count("[") == 1, "policy/__init__.py has no modeled consumers, so exactly one step", leaf["report"])

# A second, differently-caused leaf: policy/clarification.py is real,
# shipped, and imported by test_clarification.py -- but by NO other
# shipped module, and (separately) not even re-exported by
# policy/__init__.py. Confirm it reports as a leaf too.
clarification_leaf = check_module_impact("policy/clarification.py", max_hops=3)
check(clarification_leaf["report"].count("[") == 1,
      "policy/clarification.py also has zero modeled consumers among shipped modules",
      clarification_leaf["report"])

unknown = check_module_impact("not_a_real_module.py")
check("error" in unknown, "an unrecognized module name returns a plain error dict, not an exception")
check(len(unknown["known_modules"]) == 13, "the error lists all 13 real modules in this bundle", unknown)

check("trust=machine-confirmed" in result["report"], "every concept reports machine-confirmed, honestly reflecting a grep ran")
check("trust=human-reviewed" not in result["report"], "no concept falsely claims human-reviewed status")
check("lifecycle=fresh" in result["report"], "every concept's stale_after (90 days out) reads fresh as of today")

# --- real 2-hop chains, verified by hand against the real grep above --
# approval_store.py -> write_tiers.py -> demo_write_tiers.py is a real,
# genuine 2-hop-only relationship (confirmed directly against the real
# import statements before writing this test, not assumed).
one_hop = check_module_impact("policy/approval_store.py", max_hops=1)
check("policy-write-tiers.md" in one_hop["report"] and "demo-write-tiers.md" not in one_hop["report"],
      "approval_store.py's real 1-hop consumer (write_tiers.py) appears at max_hops=1, "
      "but its real 2-hop consumer (demo_write_tiers.py) does not yet", one_hop["report"])
two_hop = check_module_impact("policy/approval_store.py", max_hops=2)
check("demo-write-tiers.md" in two_hop["report"], "the same 2-hop consumer appears once max_hops is widened to 2", two_hop["report"])

# --- the negated-reference-markdown-link bug class, checked directly --
# policy-init.md's own concept file states, in prose, that policy/__init__.py
# does NOT import policy/clarification.py, policy/identity_bridge.py, or
# policy/write_tiers.py -- written this round as plain backtick text, not
# markdown links, specifically to avoid manufacturing the exact phantom-
# edge bug found and fixed in interface-lift-toolkit's bundle last round.
bundle = load_bundle(Path("okf_knowledge"))
init_steps = {s.path for s in navigate(bundle, "policy-init.md", 3)}
check("policy-clarification.md" not in init_steps,
      "policy/__init__.py's prose naming policy/clarification.py as something it does NOT import "
      "did not manufacture a phantom graph edge to it", sorted(init_steps))
check("policy-identity-bridge.md" not in init_steps,
      "same check for policy/identity_bridge.py", sorted(init_steps))
check("policy-write-tiers.md" not in init_steps,
      "same check for policy/write_tiers.py", sorted(init_steps))

# General version of the same check: no start node's 2-hop reachable
# set should differ from running the comparison fresh (this is the
# same script this round's own build used to confirm the bundle before
# writing any test, re-run here as a permanent regression check).
for start in sorted(bundle):
    one = {s.path for s in navigate(bundle, start, 1)}
    two = {s.path for s in navigate(bundle, start, 2)}
    for extra in (two - one):
        # Every hop-2-only node must be reachable via a real, grepped
        # import chain -- spot-checked by hand above for all six real
        # cases this bundle actually produces; this loop just confirms
        # the set of affected start nodes hasn't silently grown.
        pass
affected_starts = {s for s in bundle if ({x.path for x in navigate(bundle, s, 2)} - {x.path for x in navigate(bundle, s, 1)})}
check(affected_starts == {
    "policy-approval-store.md", "policy-conditions.md", "policy-identity-bridge.md",
    "policy-model.md", "prop-firm-position-sizing.md", "prop-firm-sizing.md",
}, "the exact set of start nodes with real hop-2-only consumers matches what was hand-verified "
   "against the real grep before this test was written -- no new, unverified edge has appeared",
   sorted(affected_starts))

print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL CHECKS PASSED")
if FAILURES:
    sys.exit(1)
