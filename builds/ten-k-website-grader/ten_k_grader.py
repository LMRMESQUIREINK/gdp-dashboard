#!/usr/bin/env python3
"""
10K Website Grader — a locally-checkable implementation of the 8-pillar
checklist from the "Build $10,000 Websites using Claude Code" video
(point of view, typography, colour, hierarchy, imagery, motion, mobile,
and "the invisible stuff" / felt-quality-performance).

Same move this project already made for the Factory.ai Autonomy Maturity
Model paper (/builds/agent-readiness-scorecard/): take a creator's
checklist and turn it into a real, static-file-checkable grader instead
of a thing a person applies by eye — while being honest that several of
the eight pillars are genuinely NOT checkable from files on disk alone.
"Point of view" requires knowing the brief and intent behind the design,
which no static analysis can recover, and parts of "imagery" and "motion"
are about whether something *feels* premium, not whether a tag is
present. Those are reported as not-assessable, not faked with a proxy
score, same discipline /builds/agent-readiness-scorecard/ uses for
Level 4/5 operational signals it can't observe either.

Full analysis of the source video and the two linked design-skill repos:
/notes/10k-website-claude-code-analysis.md

Usage:
    python3 ten_k_grader.py SITE_DIR [--json] [--min-score 0.7]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from site_parser import (
    GENERIC_BLUE_HEXES,
    extract_colors,
    extract_font_families,
    extract_font_sizes_px,
    fixed_width_container_hits,
    has_any_motion,
    has_reduced_motion_media,
    has_viewport_meta,
    load_site,
    media_query_breakpoints,
)


@dataclass
class PillarResult:
    name: str
    assessable: bool
    passed: bool | None = None
    reason: str = ""
    checks: list[str] = field(default_factory=list)


@dataclass
class Report:
    site_dir: str
    pillars: list[PillarResult]
    flags: list[str]

    @property
    def overall_score(self) -> float:
        assessable = [p for p in self.pillars if p.assessable]
        if not assessable:
            return 0.0
        return sum(1.0 for p in assessable if p.passed) / len(assessable)

    @property
    def assessable_count(self) -> int:
        return sum(1 for p in self.pillars if p.assessable)

    def to_dict(self) -> dict:
        return {
            "site_dir": self.site_dir,
            "overall_score": round(self.overall_score, 3),
            "assessable_pillars": self.assessable_count,
            "total_pillars": len(self.pillars),
            "pillars": [asdict(p) for p in self.pillars],
            "flags": self.flags,
        }


def grade_site(root: Path) -> Report:
    data = load_site(root)
    css = data.css_text
    pillars: list[PillarResult] = []
    flags: list[str] = []

    if not data.html_files:
        pillars.append(PillarResult("point-of-view", False, reason="requires knowing the brief/intent behind the design — not observable from files"))
        for name in ("typography", "colour", "hierarchy", "imagery", "motion", "mobile", "invisible-stuff"):
            pillars.append(PillarResult(name, True, False, reason="no .html files found in site_dir"))
        return Report(str(root), pillars, ["no .html files found — nothing to grade"])

    # 1. Point of view — never assessable from static files.
    pillars.append(PillarResult(
        "point-of-view", assessable=False,
        reason="requires knowing the brief and intent behind the design choices; not observable from the files themselves",
    ))

    # 2. Typography
    families = extract_font_families(css)
    sizes = extract_font_sizes_px(css)
    distinct_sizes = sorted(set(round(s, 1) for s in sizes))
    typo_checks = [f"{len(families)} distinct non-generic font-family value(s): {families}"]
    typo_pass = 1 <= len(families) <= 4 and len(distinct_sizes) >= 3
    typo_checks.append(f"{len(distinct_sizes)} distinct font-size value(s) (type scale proxy)")
    if any(f.lower() == "inter" for f in families):
        flags.append("Typography: 'Inter' is in use — the source video calls this the single most overused AI-generated-site font; not an automatic fail, but worth a deliberate look")
    pillars.append(PillarResult("typography", True, typo_pass, "; ".join(typo_checks)))

    # 3. Colour
    colors = extract_colors(css)
    colour_pass = 3 <= len(colors) <= 10
    colour_checks = [f"{len(colors)} distinct colour value(s) in CSS (3-10 reads as a deliberate restrained palette)"]
    hit_blues = colors & GENERIC_BLUE_HEXES
    if hit_blues:
        flags.append(f"Colour: default framework-blue hex(es) detected ({sorted(hit_blues)}) — design-rules.md's own 'never default blue/indigo' tell")
    pillars.append(PillarResult("colour", True, colour_pass, "; ".join(colour_checks)))

    # 4. Hierarchy (weak proxy: real type-scale spread; genuine layout hierarchy needs eyes on it)
    if len(distinct_sizes) >= 2:
        spread_ratio = max(distinct_sizes) / max(min(distinct_sizes), 1.0)
        hierarchy_pass = len(distinct_sizes) >= 4 and spread_ratio >= 2.0
        hierarchy_reason = (
            f"heuristic only: {len(distinct_sizes)} distinct font sizes, "
            f"largest/smallest ratio {spread_ratio:.1f}x — a real hierarchy check needs eyes on the rendered layout, not just CSS values"
        )
    else:
        hierarchy_pass = False
        hierarchy_reason = "fewer than 2 distinct font sizes found — flat sizing is a strong tell against real hierarchy"
    pillars.append(PillarResult("hierarchy", True, hierarchy_pass, hierarchy_reason))

    # 5. Imagery
    imgs = data.img_tags
    media = data.media_tags
    real_media_count = sum(1 for i in imgs if (i.get("src") or "").strip()) + sum(1 for m in media if (m.get("src") or "").strip())
    non_decorative = [i for i in imgs if i.get("role") != "presentation" and i.get("aria-hidden") != "true"]
    with_alt = [i for i in non_decorative if (i.get("alt") or "").strip()]
    alt_coverage = (len(with_alt) / len(non_decorative)) if non_decorative else 1.0
    lazy_used = any((i.get("loading") == "lazy") for i in imgs) or any((m.get("loading") == "lazy") for m in media)
    imagery_pass = real_media_count >= 1 and alt_coverage >= 0.9
    imagery_checks = [
        f"{real_media_count} real image/video reference(s) with a non-empty src",
        f"alt-text coverage {alt_coverage:.0%} of {len(non_decorative)} non-decorative <img> tag(s)",
        f"loading=\"lazy\" used: {lazy_used}",
    ]
    pillars.append(PillarResult("imagery", True, imagery_pass, "; ".join(imagery_checks)))
    flags.append("Imagery: whether assets read as custom/premium vs. generic stock is NOT checked here — that needs a human looking at the actual pictures")

    # 6. Motion
    motion_present = has_any_motion(css)
    reduced_motion = has_reduced_motion_media(css)
    motion_pass = motion_present and reduced_motion
    pillars.append(PillarResult(
        "motion", True, motion_pass,
        f"transition/animation/transform present: {motion_present}; prefers-reduced-motion respected: {reduced_motion}",
    ))
    flags.append("Motion: whether it feels restrained/premium vs. gimmicky is NOT checked here — presence and accessibility only")

    # 7. Mobile
    viewport_ok = has_viewport_meta(data.meta_tags)
    breakpoints = media_query_breakpoints(css)
    fixed_hits = fixed_width_container_hits(css)
    mobile_pass = viewport_ok and len(breakpoints) >= 1
    mobile_checks = [
        f"viewport meta present: {viewport_ok}",
        f"{len(breakpoints)} max/min-width media query breakpoint(s)",
    ]
    pillars.append(PillarResult("mobile", True, mobile_pass, "; ".join(mobile_checks)))
    if fixed_hits:
        flags.append(f"Mobile: {fixed_hits} broad selector(s) (body/main/.container/.wrapper) with a hardcoded large pixel width — heuristic, worth checking by hand on a real phone width")

    # 8. Invisible stuff (performance & finish, as far as static files show it)
    broken_refs: list[str] = []
    for html_path, url in data.local_refs:
        resolved = (html_path.parent / url.split("#")[0].split("?")[0]).resolve()
        if not resolved.exists():
            broken_refs.append(f"{html_path.name} -> {url}")
    dup_ids: list[str] = []
    for fname, ids in data.ids_by_file.items():
        seen: set[str] = set()
        for i in ids:
            if i in seen:
                dup_ids.append(f"{Path(fname).name}: #{i}")
            seen.add(i)
    oversized_images: list[str] = []
    for img_path in root.rglob("*"):
        if img_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"} and img_path.is_file():
            size_kb = img_path.stat().st_size / 1024
            if size_kb > 1500:
                oversized_images.append(f"{img_path.name} ({size_kb:.0f} KB)")
    invisible_pass = not broken_refs and not dup_ids and not oversized_images
    invisible_checks = [
        f"{len(broken_refs)} broken local reference(s)",
        f"{len(dup_ids)} duplicate id(s)",
        f"{len(oversized_images)} unoptimized raster image(s) over 1.5MB",
    ]
    pillars.append(PillarResult("invisible-stuff", True, invisible_pass, "; ".join(invisible_checks)))
    if oversized_images:
        flags.append(f"Invisible stuff: oversized image file(s) — {oversized_images}")
    if broken_refs:
        flags.append(f"Invisible stuff: broken local reference(s) — {broken_refs}")
    if dup_ids:
        flags.append(f"Invisible stuff: duplicate id(s) — {dup_ids}")

    return Report(str(root), pillars, flags)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site_dir", help="Path to a built static site's root folder (containing .html files)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of a formatted report")
    parser.add_argument("--min-score", type=float, default=None, help="Exit non-zero if overall_score falls below this threshold")
    args = parser.parse_args()

    root = Path(args.site_dir)
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 2

    report = grade_site(root)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"10K Website Grader — {root}")
        print(f"Overall score: {report.overall_score:.0%} (across {report.assessable_count}/{len(report.pillars)} assessable pillars)\n")
        for p in report.pillars:
            if not p.assessable:
                print(f"  [not assessable] {p.name} — {p.reason}")
            else:
                mark = "PASS" if p.passed else "FAIL"
                print(f"  [{mark}] {p.name} — {p.reason}")
        if report.flags:
            print("\nFlags (informational, not pass/fail):")
            for f in report.flags:
                print(f"  - {f}")

    if args.min_score is not None and report.overall_score < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
