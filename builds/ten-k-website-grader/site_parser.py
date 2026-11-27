"""
Pure parsing/extraction for ten_k_grader.py — no scoring logic here, just
"what's actually in these files." Kept separate so it can be unit-tested
without the scoring rules, same separation discipline as every other
regex-based tool in this project (patterns.py vs humanizer.py,
voice_profile.py vs voice_match.py).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

GENERIC_FONT_KEYWORDS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "-apple-system", "ui-sans-serif", "ui-serif", "ui-monospace", "inherit",
    "initial", "unset", "blinkmacsystemfont",
}

# The common default-blue tells design-rules.md already bans in this
# project (Tailwind/Bootstrap primary blues and indigo), reused here as a
# named flag rather than re-invented.
GENERIC_BLUE_HEXES = {
    "2563eb", "3b82f6", "007bff", "0d6efd", "4f46e5", "4338ca", "0066ff",
    "1d4ed8", "2b6cb0",
}

SKIP_URL_PREFIXES = ("http://", "https://", "//", "data:", "mailto:", "tel:", "#", "javascript:")
LOCAL_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}


@dataclass
class SiteData:
    html_files: list[Path] = field(default_factory=list)
    css_text: str = ""
    img_tags: list[dict] = field(default_factory=list)
    media_tags: list[dict] = field(default_factory=list)  # video/source/audio
    meta_tags: list[dict] = field(default_factory=list)
    local_refs: list[tuple[Path, str]] = field(default_factory=list)  # (html_file, resolved-relative-url)
    ids_by_file: dict[str, list[str]] = field(default_factory=dict)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_style = False
        self.style_chunks: list[str] = []
        self.imgs: list[dict] = []
        self.media: list[dict] = []
        self.metas: list[dict] = []
        self.inline_styles: list[str] = []
        self.refs: list[tuple[str, str]] = []  # (tag, url)
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs_list) -> None:
        attrs = dict(attrs_list)
        if tag == "style":
            self.in_style = True
        if "id" in attrs and attrs["id"]:
            self.ids.append(attrs["id"])
        if "style" in attrs and attrs["style"]:
            self.inline_styles.append(attrs["style"])
        if tag == "img":
            self.imgs.append(attrs)
            if attrs.get("src"):
                self.refs.append(("img", attrs["src"]))
        elif tag in ("video", "source", "audio"):
            self.media.append(attrs)
            if attrs.get("src"):
                self.refs.append((tag, attrs["src"]))
        elif tag == "meta":
            self.metas.append(attrs)
        elif tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href"):
            self.refs.append(("link", attrs["href"]))
        elif tag == "script" and attrs.get("src"):
            self.refs.append(("script", attrs["src"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.style_chunks.append(data)


def _is_local_url(url: str) -> bool:
    return not url.lower().startswith(SKIP_URL_PREFIXES)


def load_site(root: Path) -> SiteData:
    data = SiteData()
    html_files = sorted(root.rglob("*.html")) + sorted(root.rglob("*.htm"))
    data.html_files = html_files

    css_parts: list[str] = []
    for css_file in sorted(root.rglob("*.css")):
        try:
            css_parts.append(css_file.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue

    for html_path in html_files:
        try:
            text = html_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parser = _PageParser()
        parser.feed(text)
        css_parts.extend(parser.style_chunks)
        css_parts.extend(f"__inline__ {{ {s} }}" for s in parser.inline_styles)
        data.img_tags.extend(parser.imgs)
        data.media_tags.extend(parser.media)
        data.meta_tags.extend(parser.metas)
        data.ids_by_file[str(html_path)] = parser.ids
        for _tag, url in parser.refs:
            if _is_local_url(url):
                data.local_refs.append((html_path, url))

    data.css_text = "\n".join(css_parts)
    return data


def extract_font_families(css_text: str) -> list[str]:
    families: list[str] = []
    for match in re.findall(r"font-family\s*:\s*([^;}{]+)", css_text, re.I):
        first = match.split(",")[0].strip().strip("'\"")
        if first and first.lower() not in GENERIC_FONT_KEYWORDS:
            families.append(first)
    # Dedupe case-insensitively, preserve first-seen casing.
    seen: dict[str, str] = {}
    for fam in families:
        seen.setdefault(fam.lower(), fam)
    return list(seen.values())


def extract_font_sizes_px(css_text: str) -> list[float]:
    sizes: list[float] = []
    for value, unit in re.findall(r"font-size\s*:\s*([0-9]*\.?[0-9]+)(px|rem|em)", css_text, re.I):
        px = float(value) * (16.0 if unit.lower() in ("rem", "em") else 1.0)
        sizes.append(px)
    return sizes


def extract_colors(css_text: str) -> set[str]:
    colors: set[str] = set()
    for hexval in re.findall(r"#([0-9a-fA-F]{3,8})\b", css_text):
        h = hexval.lower()
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        elif len(h) in (4, 8):  # drop alpha channel if present
            h = h[:6] if len(h) == 8 else h[:3] * 2
        if len(h) == 6:
            colors.add(h)
    for r, g, b in re.findall(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css_text, re.I):
        colors.add(f"{int(r):02x}{int(g):02x}{int(b):02x}")
    return colors


def has_reduced_motion_media(css_text: str) -> bool:
    return re.search(r"@media[^{]*prefers-reduced-motion\s*:\s*reduce", css_text, re.I) is not None


def has_any_motion(css_text: str) -> bool:
    return bool(
        re.search(r"\btransition\s*:", css_text, re.I)
        or re.search(r"\banimation\s*:", css_text, re.I)
        or re.search(r"@keyframes\b", css_text, re.I)
        or re.search(r"\btransform\s*:", css_text, re.I)
    )


def has_viewport_meta(meta_tags: list[dict]) -> bool:
    return any(
        m.get("name") == "viewport" and "width=device-width" in (m.get("content") or "")
        for m in meta_tags
    )


def media_query_breakpoints(css_text: str) -> list[str]:
    return re.findall(r"@media[^{]*\((?:max|min)-width\s*:\s*[0-9]+px\)", css_text, re.I)


def fixed_width_container_hits(css_text: str) -> int:
    """Heuristic only: broad selectors with a hardcoded pixel width, which
    tends to break on small screens. Explicitly a heuristic, not a real
    layout analysis — stated plainly in the grader's output, not just here."""
    hits = 0
    for selector_block in re.findall(r"(?:^|\})\s*((?:body|html|main|\.container|\.wrapper)[^{}]*)\{([^{}]*)\}", css_text, re.I):
        _selector, body = selector_block
        if re.search(r"width\s*:\s*(?:[5-9]\d{2}|\d{4,})px", body, re.I):
            hits += 1
    return hits
