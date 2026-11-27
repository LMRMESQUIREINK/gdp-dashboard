"""check_module_impact — a new, independent tool category for this
toolkit's own ToolRegistry: wraps okf_navigator.py (copied unmodified
from /builds/okf-navigator/, same convention /builds/trading-jarvis/
already follows) over a real OKF-formatted knowledge bundle,
okf_knowledge/, describing THIS TOOLKIT's own actual module dependency
graph — not the binary-metadata tools, not the prop-firm-sizing demo
tools.

The bundle was built by directly grepping every real import/from
statement in this repo's own .py files first (see okf_knowledge/*.md's
own "## Consumers" sections) — never fictional data. Every concept
honestly reports generated/verified by this session's own grep scan,
never a human, so trust_tier() always comes back "machine-confirmed,"
never "human-reviewed" — and the tool's own output says so plainly.

Registered the same way binary_metadata_tools.py/tools_demo.py already
register their own tools:

    from okf_impact_tool import register_okf_impact_tool
    register_okf_impact_tool(registry)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from okf_navigator import impact_report, load_bundle

from toolkit.registry import ToolRegistry
from toolkit.result import result

_BUNDLE_DIR = Path(__file__).resolve().parent / "okf_knowledge"

_KNOWN_MODULES = (
    "toolkit-registry.md", "toolkit-result.md", "toolkit-shortlist.md",
    "toolkit-approval.md", "toolkit-ledger.md", "toolkit-chain.md",
    "toolkit-loop.md", "toolkit-skill-compiler.md", "toolkit-init.md",
    "binary-metadata-tools.md", "go-buildinfo.md", "rust-cargo-auditable.md",
    "prop-firm-sizing.md", "prop-firm-position-sizing.md",
    "prop-pass-simulator.md", "tools-demo.md",
)

# toolkit/registry.py -> toolkit-registry.md etc: a submodule's real
# filename includes a directory this bundle's flat naming doesn't, so a
# plain "strip suffix, swap underscores for hyphens" slugify would miss
# the "toolkit/" prefix entirely (and toolkit/__init__.py has no stem to
# hyphenate at all) -- both are handled by this explicit table instead
# of a cleverer, easier-to-get-wrong general rule.
_SLUG_OVERRIDES = {
    "toolkit/registry.py": "toolkit-registry.md",
    "toolkit/result.py": "toolkit-result.md",
    "toolkit/shortlist.py": "toolkit-shortlist.md",
    "toolkit/approval.py": "toolkit-approval.md",
    "toolkit/ledger.py": "toolkit-ledger.md",
    "toolkit/chain.py": "toolkit-chain.md",
    "toolkit/loop.py": "toolkit-loop.md",
    "toolkit/skill_compiler.py": "toolkit-skill-compiler.md",
    "toolkit/__init__.py": "toolkit-init.md",
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


def register_okf_impact_tool(registry: ToolRegistry) -> None:
    @registry.tool(effect="local")
    def check_module_impact(module: str, max_hops: int = 2) -> dict:
        """For a question about CHANGING THIS TOOLKIT'S OWN CODE (never a
        binary-metadata or prop-firm-sizing question) -- "what depends on
        toolkit/chain.py", "what would I need to re-check if I change
        prop_firm_sizing.py" -- look up this build's own real, documented
        module dependency graph (an OKF-formatted knowledge bundle,
        machine-confirmed by a real grep of this repo's own import
        statements, never human-reviewed) and report the real impact
        radius plus how fresh/trusted that documentation is. module: a
        module filename, e.g. 'toolkit/chain.py' or 'prop_firm_sizing.py'.
        max_hops: how many dependency hops out to report."""
        slug = _slugify(module)
        bundle = load_bundle(_BUNDLE_DIR)
        if slug not in bundle:
            return result(
                f"{module!r} is not a known module in this toolkit's OKF knowledge bundle",
                checks=[("module recognized", False)],
                known_modules=sorted(_KNOWN_MODULES),
            )
        now = datetime.now(timezone.utc)
        report_text = impact_report(bundle, slug, max_hops=max_hops, now=now)
        return result(
            report_text,
            checks=[("module recognized", True), ("bundle loaded", True)],
            module=slug,
            max_hops=max_hops,
            report=report_text,
        )
