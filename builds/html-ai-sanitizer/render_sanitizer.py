"""A third mode: not a faithful reimplementation of Scrapling's
`_sanitize_for_ai()`, but a genuinely more capable replacement for it --
built because this sandbox happens to have a real headless Chromium
sitting right next to it (the same one every Playwright-based build in
this project already uses for screenshot verification).

`sanitizer.py`'s faithful and extended modes both work the way Scrapling
itself does: regex over raw HTML, with no idea what a browser would
actually render. That has two real, named consequences, checked and
locked in as regression tests in `test_sanitizer.py`: neither mode
catches off-screen hiding via `position`+a large negative offset, and
neither catches text colour deliberately matching its background --
both real, common prompt-injection-hiding techniques that a glance at
rendered output would immediately give away.

This module renders the page for real in headless Chromium and asks the
browser itself, via `getComputedStyle()` and `getBoundingClientRect()`,
what a human would actually see -- which closes both of those gaps at
once, along with anything else a static regex can never resolve
correctly: inherited `visibility`, an external or `<style>`-block
stylesheet rule, computed values after the full CSS cascade. It is
strictly more capable than the source it's replacing, not a port of it.

What it does NOT attempt, stated plainly: full alpha-compositing across
several stacked semi-transparent layers (a background colour with
alpha < 1 is blended against white, once, as a documented
approximation, not walked through every ancestor's own blended
backdrop); and it needs a real browser process, which `sanitizer.py`'s
two modes deliberately do not, so it is not a drop-in replacement for
contexts where spinning up Chromium per request is too heavy.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

ZWC_PATTERN = re.compile("[​‌‍﻿⁠᠎]")
CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

_CANDIDATE_CHROME_PATHS = (
    "/opt/pw-browsers/chromium",
    "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",
)


class RenderingUnavailableError(RuntimeError):
    """Raised when a real browser can't be launched, with the real cause
    attached rather than a raw Playwright exception or import error."""


class _ExplicitChromePathNotFound(RuntimeError):
    pass


def _resolve_chrome_path(chrome_path: Optional[str]) -> Optional[str]:
    if chrome_path is not None:
        # An explicitly-given path is either used or reported as wrong --
        # never silently swapped for a different browser than the caller
        # actually asked for.
        if Path(chrome_path).exists():
            return chrome_path
        raise _ExplicitChromePathNotFound(chrome_path)
    for candidate in (os.environ.get("CHROME_PATH"), *_CANDIDATE_CHROME_PATHS):
        if candidate and Path(candidate).exists():
            return candidate
    return None  # let Playwright try its own default resolution


# The actual "what would a human see" logic, run inside the page itself.
# Order matters: template/aria-hidden/display/visibility are checked before
# any geometry or colour check, so an element removed for one of those
# reasons is never separately mis-reported as off-screen or colour-matched
# (its box collapses to zero regardless, which would otherwise look like a
# second, redundant finding).
_HIDDEN_CHECK_JS = """
(params) => {
  const { scopeSelector, opacityThreshold, colorDistanceThreshold } = params;
  const NOISE_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "SVG"]);
  const ZWC = /[\\u200b\\u200c\\u200d\\ufeff\\u2060\\u180e]/g;
  const CTRL = /[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]/g;

  function parseColor(str) {
    const m = str.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const parts = m[1].split(",").map((s) => parseFloat(s));
    return [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
  }

  function effectiveBackground(el) {
    let node = el;
    while (node) {
      const bg = parseColor(getComputedStyle(node).backgroundColor);
      if (bg && bg[3] > 0) {
        if (bg[3] >= 0.999) return bg;
        // A partially transparent background is blended against white as a
        // documented approximation -- not a full multi-layer composite.
        const a = bg[3];
        return [bg[0] * a + 255 * (1 - a), bg[1] * a + 255 * (1 - a), bg[2] * a + 255 * (1 - a), 1];
      }
      node = node.parentElement;
    }
    return [255, 255, 255, 1];
  }

  function colorDistance(a, b) {
    return Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2);
  }

  function hiddenReason(el) {
    if (el.tagName === "TEMPLATE") return "template";
    if (el.getAttribute("aria-hidden") === "true") return "aria-hidden";
    const cs = getComputedStyle(el);
    if (cs.display === "none") return "display:none";
    if (cs.visibility === "hidden" || cs.visibility === "collapse") return "visibility:" + cs.visibility;
    const opacity = parseFloat(cs.opacity);
    if (!isNaN(opacity) && opacity <= opacityThreshold) return "opacity:near-zero";
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return "zero-size";
    if (rect.right <= 0 || rect.bottom <= 0) return "offscreen:negative-offset";
    const textColor = parseColor(cs.color);
    if (textColor) {
      if (textColor[3] <= opacityThreshold) return "text-color:transparent";
      const bg = effectiveBackground(el);
      if (colorDistance(textColor, bg) <= colorDistanceThreshold) return "color-matches-background";
    }
    return null;
  }

  const root = document.querySelector(scopeSelector) || document.body || document.documentElement;

  // Pass 1: decide what to remove while the document (and every stylesheet
  // in it) is still fully intact. Removing an element as we go -- <head>
  // in particular, which can hold the very <style> block a later sibling's
  // hidden-class depends on -- would change getComputedStyle()'s answer
  // for everything evaluated afterward. Nothing is mutated until pass 2.
  const toRemove = [];

  function walk(node) {
    for (const child of Array.from(node.children)) {
      if (child.tagName === "HEAD") {
        // <head> is never rendered by definition (the UA stylesheet sets
        // display:none on it) -- that's normal document structure, not a
        // hiding technique, so it's removed but never reported as a
        // "finding" alongside real hidden-injection elements.
        toRemove.push({ el: child, report: null });
        continue;
      }
      if (NOISE_TAGS.has(child.tagName)) {
        toRemove.push({ el: child, report: { tag: child.tagName.toLowerCase(), reason: "noise-tag" } });
        continue;
      }
      const reason = hiddenReason(child);
      if (reason) {
        toRemove.push({ el: child, report: { tag: child.tagName.toLowerCase(), reason: reason } });
        continue;
      }
      walk(child);
    }
  }
  walk(root);

  // Pass 2: now mutate the DOM, and only now build the findings list.
  const findings = [];
  for (const item of toRemove) {
    if (item.report) findings.push(item.report);
    item.el.remove();
  }

  const text = (root.innerText || "").replace(ZWC, "").replace(CTRL, "");
  return { html: root.innerHTML, text: text, findings: findings };
}
"""


def _render(
    html_text: str,
    *,
    main_content_only: bool,
    opacity_threshold: float,
    color_distance_threshold: float,
    chrome_path: Optional[str],
) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RenderingUnavailableError(
            "playwright isn't installed. Run `pip install playwright` -- a "
            "real Chromium build is also required (this is a heavier, "
            "optional dependency, unlike sanitizer.py's two stdlib-only modes)."
        ) from exc

    try:
        resolved_path = _resolve_chrome_path(chrome_path)
    except _ExplicitChromePathNotFound as exc:
        raise RenderingUnavailableError(f"chrome_path {str(exc)!r} does not exist.") from exc

    launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if resolved_path:
        launch_kwargs["executable_path"] = resolved_path

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            try:
                page = browser.new_page()
                page.set_content(html_text)
                result = page.evaluate(
                    _HIDDEN_CHECK_JS,
                    {
                        "scopeSelector": "body" if main_content_only else "html",
                        "opacityThreshold": opacity_threshold,
                        "colorDistanceThreshold": color_distance_threshold,
                    },
                )
            finally:
                browser.close()
    except Exception as exc:  # a missing/mismatched browser binary, a launch failure, etc.
        raise RenderingUnavailableError(f"Could not render the page in a real browser: {exc}") from exc

    return result


def render_and_find_hidden(
    html_text: str,
    *,
    main_content_only: bool = False,
    opacity_threshold: float = 0.02,
    color_distance_threshold: float = 10.0,
    chrome_path: Optional[str] = None,
) -> list[dict]:
    """Report, without needing a second call, every element a real render
    would hide and why -- the rendering-based sibling of `sanitizer.py`'s
    `find_removed_elements()`."""
    result = _render(
        html_text,
        main_content_only=main_content_only,
        opacity_threshold=opacity_threshold,
        color_distance_threshold=color_distance_threshold,
        chrome_path=chrome_path,
    )
    return result["findings"]


def render_sanitize_html(
    html_text: str,
    *,
    main_content_only: bool = False,
    opacity_threshold: float = 0.02,
    color_distance_threshold: float = 10.0,
    chrome_path: Optional[str] = None,
) -> str:
    """Real-browser-rendered sanitized HTML, with every hidden-by-rendering
    element's whole subtree removed."""
    result = _render(
        html_text,
        main_content_only=main_content_only,
        opacity_threshold=opacity_threshold,
        color_distance_threshold=color_distance_threshold,
        chrome_path=chrome_path,
    )
    return result["html"]


def render_extract_visible_text(
    html_text: str,
    *,
    main_content_only: bool = False,
    opacity_threshold: float = 0.02,
    color_distance_threshold: float = 10.0,
    chrome_path: Optional[str] = None,
) -> str:
    """The real "safe to hand to an LLM" output: the browser's own
    `innerText` over what's left after removing everything a human
    wouldn't actually see, whitespace collapsed the same way
    `sanitizer.py`'s text mode does."""
    result = _render(
        html_text,
        main_content_only=main_content_only,
        opacity_threshold=opacity_threshold,
        color_distance_threshold=color_distance_threshold,
        chrome_path=chrome_path,
    )
    return re.sub(r"\s+", " ", result["text"]).strip()
