"""check_module_impact for policy-control-plane -- wraps okf_navigator.py
(from /builds/okf-navigator/, copied in unmodified a fourth time: first
okf-navigator itself, then trading-jarvis, then interface-lift-toolkit,
now here) over a real OKF-formatted knowledge bundle, okf_knowledge/,
describing THIS BUILD's own actual module dependency graph.

Deliberate adaptation, stated plainly rather than forced: trading-jarvis
and interface-lift-toolkit both wire this in as an LLM-callable tool
(jarvis_orchestrator.py's TOOLS list / toolkit's ToolRegistry), because
both of those builds already have a real tool-dispatch loop to attach
it to. This build has no such loop -- policy-control-plane is a plain
governance library, not an agent harness -- so check_module_impact is
exposed the way every other function in this build is: a plain,
directly-importable Python function, plus a small CLI for the same
"what depends on this module" question asked from a terminal instead
of through a model.

    python3 okf_impact.py policy/evaluator.py
    python3 okf_impact.py policy/write_tiers.py --max-hops 1
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from okf_navigator import impact_report, load_bundle

_BUNDLE_DIR = Path(__file__).resolve().parent / "okf_knowledge"

_KNOWN_MODULES = (
    "demo-policies.md", "demo-write-tiers.md", "governed-call.md",
    "policy-init.md", "policy-approval-store.md", "policy-clarification.md",
    "policy-conditions.md", "policy-evaluator.md", "policy-identity-bridge.md",
    "policy-model.md", "policy-write-tiers.md",
    "prop-firm-position-sizing.md", "prop-firm-sizing.md",
)

# "policy/evaluator.py" -> "policy-evaluator.md": a submodule's real
# filename carries a directory this bundle's flat naming doesn't, and
# "policy/__init__.py" has no stem to hyphenate at all -- both handled
# by this explicit table, same convention as interface-lift-toolkit's
# okf_impact_tool.py, rather than a cleverer general rule that gets one
# of the two cases wrong.
_SLUG_OVERRIDES = {
    "policy/__init__.py": "policy-init.md",
    "policy/approval_store.py": "policy-approval-store.md",
    "policy/clarification.py": "policy-clarification.md",
    "policy/conditions.py": "policy-conditions.md",
    "policy/evaluator.py": "policy-evaluator.md",
    "policy/identity_bridge.py": "policy-identity-bridge.md",
    "policy/model.py": "policy-model.md",
    "policy/write_tiers.py": "policy-write-tiers.md",
}


def _slugify(module_name: str) -> str:
    if module_name in _SLUG_OVERRIDES:
        return _SLUG_OVERRIDES[module_name]
    stem = module_name
    for suffix in (".py", ".md"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("_", "-") + ".md"


def check_module_impact(module: str, max_hops: int = 2) -> dict:
    """For a question about CHANGING THIS BUILD'S OWN CODE -- "what
    depends on policy/evaluator.py", "what would break if I change
    policy/write_tiers.py" -- look up this build's own real, documented
    module dependency graph and report the real impact radius plus how
    fresh/trusted that documentation is."""
    slug = _slugify(module)
    bundle = load_bundle(_BUNDLE_DIR)
    if slug not in bundle:
        return {
            "error": f"{module!r} is not a known module in this build's OKF knowledge bundle",
            "known_modules": sorted(_KNOWN_MODULES),
        }
    now = datetime.now(timezone.utc)
    report_text = impact_report(bundle, slug, max_hops=max_hops, now=now)
    return {"module": slug, "max_hops": max_hops, "report": report_text}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="What depends on this module, in this build's own real import graph?")
    parser.add_argument("module", help="a module filename, e.g. 'policy/evaluator.py' or 'prop_firm_sizing.py'")
    parser.add_argument("--max-hops", type=int, default=2)
    args = parser.parse_args()

    result = check_module_impact(args.module, max_hops=args.max_hops)
    if "error" in result:
        print(result["error"])
        print("Known modules:", ", ".join(result["known_modules"]))
        raise SystemExit(1)
    print(result["report"])


if __name__ == "__main__":
    main()
