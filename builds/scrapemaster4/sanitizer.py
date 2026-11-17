"""Standalone reimplementation of Scrapling's real `_sanitize_for_ai()`.

Scrapling (D4Vinci/Scrapling, PyPI package `scrapling`, read directly from a
pip-installed copy -- version 0.5.1 -- at
`scrapling/core/shell.py`) gates its markdown/text extraction behind a single
switch, `main_content_only` (the CLI's `--ai-targeted` flag), which the real
`Convertor._extract_content()` wires to two calls in sequence:
`_strip_noise_tags()` (drops `script`/`style`/`noscript`/`svg` subtrees
outright) then `_sanitize_for_ai()` (drops elements hidden via CSS, ARIA, or
HTML, then strips zero-width Unicode characters and XML-illegal control
characters from whatever text remains, and drops HTML comments). Without that
flag, Scrapling's own extraction does not sanitize anything at all -- the flag
is not a refinement, it is the entire defense.

This module is an independent reimplementation, not a copy: it parses HTML
with the stdlib's `html.parser.HTMLParser` (no `lxml`, no third-party
dependency) and reimplements the same real, checkable logic from reading the
real source directly, named at each function. It is split into two modes:

- The FAITHFUL mode (`is_hidden_element`, `sanitize_html`, `extract_visible_text`
  with no `extended=True`) matches the real `_sanitize_for_ai()`'s exact,
  current scope -- including deliberately staying case-SENSITIVE on
  `aria-hidden="true"`, exactly matching the real source's own
  `element.get("aria-hidden") == "true"` check, not a widened version of it.
- The EXTENDED mode (`extended=True`) is this project's own, clearly-separate
  addition, catching one more real hiding technique the faithful mode still
  does not: text pushed off-screen via a large negative `text-indent`. It is
  OPT-IN and never silently merged into the faithful behavior.

What remains out of scope even in extended mode, stated plainly rather than
assumed closed: off-screen hiding via `position` plus a large negative
`left`/`top` offset (needs tracking two declarations together against the
element's actual positioning context, not a single-declaration check), and
any hiding that depends on resolving the full CSS cascade -- a `color` that
happens to match its `background-color`, or hiding achieved only via an
external or `<style>` stylesheet rather than an inline `style` attribute.
Scrapling's own real scope has exactly the same stylesheet/cascade blind
spot (it only ever inspects inline `style` attributes), confirmed by reading
`_is_hidden_element()` directly -- not a gap unique to this reimplementation.
"""

from __future__ import annotations

import html as _html_mod
import re
from html.parser import HTMLParser

# --- Faithful scope: ported understanding of scrapling/core/shell.py's real
# _HIDDEN_XPATH / _HIDING_DECLARATIONS / _ZERO_HIDING_PROPERTIES / _is_hidden_element,
# read directly from the pip-installed scrapling==0.5.1 source. ---------------

HIDING_DECLARATIONS = frozenset({("display", "none"), ("visibility", "hidden")})
ZERO_HIDING_PROPERTIES = frozenset({"opacity", "font-size", "height", "width", "max-height", "max-width"})

# CSS reads CRLF/CR/FF as a single LF, which can end an unterminated string.
_CSS_NEWLINE_PATTERN = re.compile(r"\r\n?|\f")

# Blanks comments and quoted strings / url(...) calls before a style attribute is
# split on ";", so a ";" or a hiding-looking substring inside one of those can
# never be misread as a real declaration boundary or a real declaration.
_STYLE_TOKEN_PATTERN = re.compile(
    r"""(\\.)|"(?:[^"\\\n]|\\.)*"?|'(?:[^'\\\n]|\\.)*'?"""
    r"""|(?<![\w-])url\((?![ \t\n]*["'])(?:[^)\\]|\\.?)*\)?|(/\*.*?(?:\*/|\Z))""",
    re.DOTALL | re.IGNORECASE,
)
_ZERO_VALUE_PATTERN = re.compile(r"[+-]?(?:0+(?:\.0+)?|\.0+)(?:e[+-]?[0-9]+)?[a-z%]*")
_IMPORTANT_SUFFIX_PATTERN = re.compile(r"![ \t\n]*important$")

# Zero-width Unicode characters a scraper's raw text extraction would otherwise
# pass through invisibly; XML-illegal control characters (tab/LF/CR excepted).
ZWC_PATTERN = re.compile("[​‌‍﻿⁠᠎]")
CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

NOISE_TAGS = frozenset({"script", "style", "noscript", "svg"})

VOID_ELEMENTS = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
)


def _blank_style_token(match: "re.Match[str]") -> str:
    """Keep an escape; replace a comment with a space; replace a string/url() with "" .

    A comment separates tokens instead of joining them -- "no/**/ne" never
    reads as "none" -- matching the real source's own stated, deliberate
    non-goal (it does not try to defeat a comment used to break up a value).
    """
    if match.group(1):
        return match.group(1)
    return " " if match.group(2) else '""'


def _iter_style_declarations(style_attr: str):
    """Yield (prop, value) pairs from an inline style attribute, lowercased,
    with any trailing "!important" stripped -- the same normalization the
    real source applies before comparing against a hiding declaration."""
    style = _CSS_NEWLINE_PATTERN.sub("\n", style_attr or "")
    style = _STYLE_TOKEN_PATTERN.sub(_blank_style_token, style)
    for declaration in style.split(";"):
        prop, _, value = declaration.partition(":")
        prop = prop.strip(" \t\n").lower()
        value = _IMPORTANT_SUFFIX_PATTERN.sub("", value.strip(" \t\n").lower()).rstrip(" \t\n")
        yield prop, value


def is_hidden_by_style(style_attr: str) -> bool:
    """CSS-declaration-level check, not a substring check -- "opacity:0.95" and
    "line-height:0.9" are both correctly kept, matching the real source's own
    stated reason for parsing declaration-by-declaration."""
    for prop, value in _iter_style_declarations(style_attr):
        if (prop, value) in HIDING_DECLARATIONS:
            return True
        if prop in ZERO_HIDING_PROPERTIES and _ZERO_VALUE_PATTERN.fullmatch(value):
            return True
    return False


def is_hidden_element(node: "_Node") -> bool:
    """Faithful reimplementation of the real `_is_hidden_element()`'s scope.

    Deliberately case-SENSITIVE on aria-hidden, matching the real source's own
    `element.get("aria-hidden") == "true"` exactly -- not a widened check."""
    if node.tag == "template" or node.attrs.get("aria-hidden") == "true":
        return True
    if node.tag == "slot" and "hidden" in node.attrs:
        return True
    return is_hidden_by_style(node.attrs.get("style") or "")


def _hidden_reason(node: "_Node") -> str:
    """Names which rule matched, for transparency/testing -- not part of the
    real source's own API, which only ever returns a bool."""
    if node.tag == "template":
        return "template"
    if node.attrs.get("aria-hidden") == "true":
        return "aria-hidden"
    if node.tag == "slot" and "hidden" in node.attrs:
        return "hidden-slot"
    for prop, value in _iter_style_declarations(node.attrs.get("style") or ""):
        if (prop, value) in HIDING_DECLARATIONS:
            return f"style:{prop}:{value}"
        if prop in ZERO_HIDING_PROPERTIES and _ZERO_VALUE_PATTERN.fullmatch(value):
            return f"style:{prop}:zero"
    return "unknown"


# --- Extended scope: this project's own, clearly-separate addition. ----------

_NEGATIVE_TEXT_INDENT_PATTERN = re.compile(r"^-")


def is_hidden_extended(node: "_Node") -> bool:
    """Faithful scope PLUS one more real hiding technique: text pushed
    off-screen via a negative `text-indent` -- a classic image-replacement/
    SEO-cloaking trick never covered by the real source's own declaration
    set. Opt-in; never applied unless a caller explicitly asks for it."""
    if is_hidden_element(node):
        return True
    for prop, value in _iter_style_declarations(node.attrs.get("style") or ""):
        if prop == "text-indent" and _NEGATIVE_TEXT_INDENT_PATTERN.match(value):
            return True
    return False


def strip_invisible_chars(text: str) -> str:
    """Zero-width Unicode characters and XML-illegal control characters,
    matching the real `_sanitize_for_ai()`'s own text/tail cleanup -- applied
    to every surviving text node, not just ones inside a once-hidden element."""
    return CONTROL_CHARS_PATTERN.sub("", ZWC_PATTERN.sub("", text))


# --- HTML parsing: a minimal stdlib-only tree, no third-party dependency. ----


class _Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs) -> None:
        self.tag = tag
        self.attrs: dict[str, str | None] = dict(attrs)
        self.children: list["_Node | str"] = []


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {})
        self.stack: list[_Node] = [self.root]

    def handle_starttag(self, tag, attrs) -> None:
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs) -> None:
        self.stack[-1].children.append(_Node(tag, attrs))

    def handle_endtag(self, tag) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # Tolerate an unmatched end tag -- malformed HTML should not raise.

    def handle_data(self, data) -> None:
        if data:
            self.stack[-1].children.append(data)

    def handle_comment(self, data) -> None:
        # Comments are dropped outright, matching the real
        # `Selector(..., keep_comments=False)`.
        pass


def _parse(html_text: str) -> _Node:
    builder = _TreeBuilder()
    builder.feed(html_text)
    builder.close()
    return builder.root


def _find_first(node: _Node, tag: str) -> "_Node | None":
    for child in node.children:
        if isinstance(child, str):
            continue
        if child.tag == tag:
            return child
        found = _find_first(child, tag)
        if found is not None:
            return found
    return None


def _strip(node: _Node, *, extended: bool) -> None:
    is_hidden = is_hidden_extended if extended else is_hidden_element
    kept: list["_Node | str"] = []
    for child in node.children:
        if isinstance(child, str):
            kept.append(strip_invisible_chars(child))
            continue
        if child.tag in NOISE_TAGS:
            continue
        if is_hidden(child):
            continue
        _strip(child, extended=extended)
        kept.append(child)
    node.children = kept


def find_removed_elements(html_text: str, *, extended: bool = False) -> list[dict]:
    """Report, without mutating, every element `sanitize_html()`/
    `extract_visible_text()` would drop and why -- for transparency and tests."""
    is_hidden = is_hidden_extended if extended else is_hidden_element
    root = _parse(html_text)
    found: list[dict] = []

    def walk(node: _Node) -> None:
        for child in node.children:
            if isinstance(child, str):
                continue
            if child.tag in NOISE_TAGS:
                found.append({"tag": child.tag, "attrs": dict(child.attrs), "reason": "noise-tag"})
                continue
            if is_hidden(child):
                if extended and not is_hidden_element(child):
                    reason = "text-indent:negative"
                else:
                    reason = _hidden_reason(child)
                found.append({"tag": child.tag, "attrs": dict(child.attrs), "reason": reason})
                continue
            walk(child)

    walk(root)
    return found


def _text(node: "_Node | str") -> str:
    if isinstance(node, str):
        return node
    return "".join(_text(c) for c in node.children)


def _serialize(node: "_Node | str") -> str:
    if isinstance(node, str):
        return _html_mod.escape(node)
    attrs = "".join(
        f' {name}="{_html_mod.escape(value if value is not None else "", quote=True)}"'
        for name, value in node.attrs.items()
    )
    if node.tag in VOID_ELEMENTS:
        return f"<{node.tag}{attrs}>"
    inner = "".join(_serialize(c) for c in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


def _scoped_target(root: _Node, *, main_content_only: bool) -> _Node:
    if main_content_only:
        body = _find_first(root, "body")
        if body is not None:
            return body
    return root


def sanitize_html(html_text: str, *, main_content_only: bool = False, extended: bool = False) -> str:
    """Return sanitized HTML: hidden elements and noise tags removed, their
    whole subtree gone, with invisible characters stripped from surviving
    text. Unlike the real source (where sanitization only happens at all when
    `main_content_only` is set), this tool always sanitizes -- `main_content_only`
    here only narrows the scope to `<body>`, since sanitizing is this tool's
    entire purpose, not a side effect of restricting to the main content."""
    root = _parse(html_text)
    target = _scoped_target(root, main_content_only=main_content_only)
    _strip(target, extended=extended)
    return "".join(_serialize(c) for c in target.children)


def extract_visible_text(html_text: str, *, main_content_only: bool = False, extended: bool = False) -> str:
    """Sanitize, then return the remaining plain visible text, whitespace
    collapsed -- the actual "safe to hand to an LLM" output."""
    root = _parse(html_text)
    target = _scoped_target(root, main_content_only=main_content_only)
    _strip(target, extended=extended)
    raw = _text(target)
    return re.sub(r"\s+", " ", raw).strip()
