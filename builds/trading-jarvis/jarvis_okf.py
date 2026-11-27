"""check_module_impact — a fourth, independent tool category for
jarvis_orchestrator.py: "if I change module X in this codebase, what's
the real, documented impact radius, and how fresh/trusted is that
documentation?" Wraps okf_navigator.py (copied in unmodified from
/builds/okf-navigator/, same convention memory_layer.py/persistence.py
already follow here) over a real OKF-formatted knowledge bundle,
okf_knowledge/, describing THIS BUILD's own actual module dependency
graph.

Not fictional data: every concept file's `links` section was written
after directly grepping this repo's own real import statements (see
/notes/okf-rag-agentic-bundle-analysis.md Addendum 2 for the full
account), and every trust tier is honestly `machine-confirmed` rather
than `human-reviewed` -- this session's own grep verified the graph,
no human has reviewed it yet, and the module says so plainly rather
than overclaiming the stronger tier.

Deliberately independent of the other three tool categories
(symbol-trading, prop-firm sizing, session memory): this is a
development/maintenance aid for someone changing THIS CODEBASE, not a
trading-decision tool, and the system prompt tells Claude not to mix
the two.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from okf_navigator import impact_report, load_bundle

_BUNDLE_DIR = Path(__file__).parent / "okf_knowledge"
_KNOWN_MODULES = (
    "data-pipeline.md", "signal-generator.md", "risk-manager.md",
    "positions-store.md", "swamp-intelligence.md", "jarvis-swamp-bridge.md",
    "prop-firm-sizing.md", "prop-firm-position-sizing.md", "prop-pass-simulator.md",
    "memory-layer.md", "persistence.md", "jarvis-memory.md", "jarvis-orchestrator.md",
)


def _slugify(module_name: str) -> str:
    """Accepts either the real filename ("risk_manager.py") or the
    bundle's own concept-file name ("risk-manager.md") and resolves to
    the concept-file name, so a caller doesn't need to know the
    bundle's own file-naming convention."""
    stem = module_name
    for suffix in (".py", ".md"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("_", "-") + ".md"


def check_module_impact(module: str, max_hops: int = 2) -> dict:
    """Returns the real impact report for one module in this codebase's
    own documented dependency graph, plus a plain list of known modules
    so an unrecognized name surfaces a helpful error instead of a raw
    KeyError."""
    slug = _slugify(module)
    bundle = load_bundle(_BUNDLE_DIR)
    if slug not in bundle:
        return {
            "error": f"{module!r} is not a known module in this build's OKF knowledge bundle",
            "known_modules": sorted(_KNOWN_MODULES),
        }
    now = datetime.now(timezone.utc)
    report_text = impact_report(bundle, slug, max_hops=max_hops, now=now)
    return {
        "module": slug,
        "max_hops": max_hops,
        "report": report_text,
    }
