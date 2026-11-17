# html-ai-sanitizer

A standalone, dependency-free Python reimplementation of Scrapling's real
`_sanitize_for_ai()` — the mechanism credited (and named a deliberate
next-move rather than built) in `/notes/scrapling-ecosystem-analysis.md`.
Built on explicit request: "Build the standalone \_sanitize_for_ai tool!"

## What this is reimplementing, verified against the live source

Scrapling (`D4Vinci/Scrapling`) gates its own markdown/text extraction
behind one switch — `main_content_only`, which the CLI exposes as
`--ai-targeted`. This project's earlier round credited that flag as "a
real, specific, independently-verified prompt-injection defense" and named
its scope as CSS `display:none`/`visibility:hidden`, `aria-hidden="true"`,
hidden `<slot>`, and `<template>`.

**That earlier scope statement is now corrected, in public, rather than
quietly carried forward.** This round installed the real package for real
(`pip install scrapling`, landing on the current PyPI release, 0.5.1) and —
since this sandbox's auto-mode classifier denies *running* a third party's
code even when it's a published package, not just a cloned repo, the same
restriction already documented for `morluto/rea` — read
`scrapling/core/shell.py` directly off disk instead of importing it. The
real, current scope is broader than previously stated:

- CSS `display:none` / `visibility:hidden` (as before).
- **New finding**: CSS `opacity`, `font-size`, `height`, `width`,
  `max-height`, or `max-width` set to any zero value (`0`, `0px`, `.0em`,
  `-0`, …) — a real `_ZERO_HIDING_PROPERTIES` set with its own zero-value
  regex, checked declaration-by-declaration so `opacity:0.95` and
  `line-height:0.9` are correctly left alone (the real source's own
  docstring states both examples explicitly; both are reproduced here as
  tests).
- `aria-hidden="true"` — confirmed **case-sensitive**: the real
  `_is_hidden_element()` checks `element.get("aria-hidden") == "true"` with
  no `.lower()` anywhere, so `aria-hidden="True"` is not caught. Faithfully
  reproduced here, not silently widened.
- `<template>` and a `<slot>` carrying a `hidden` attribute of any value.
- **New finding**: the real `_sanitize_for_ai()` also strips zero-width
  Unicode characters (`​‌‍﻿⁠᠎`) and
  XML-illegal control characters (everything below `\x20` except tab/LF/CR)
  from every surviving text node — not just the ones inside a removed
  element — and drops HTML comments outright
  (`Selector(..., keep_comments=False)`). None of this was in the earlier
  round's analysis.
- **New finding**: noise-tag removal (`_strip_noise_tags`) covers
  `script`, `style`, `noscript`, **and `svg`** — the earlier round only
  named script/style.
- **New finding, and the sharpest one**: `main_content_only` is not a
  refinement of sanitization — it is the entire switch. Reading
  `Convertor._extract_content()` shows `_strip_noise_tags()` and
  `_sanitize_for_ai()` are only ever called inside the
  `if main_content_only:` branch. Without `--ai-targeted`, Scrapling's own
  extraction does not sanitize anything at all. The official skill's
  all-caps "you MUST use `--ai-targeted`" instruction is, on this reading,
  not an exaggeration — it's a literal description of the only on/off
  switch that exists.

One thing already correctly credited last round holds up exactly: the
style check really is declaration-aware, not a substring match, and really
does strip comments/quoted-strings/`url()` before splitting on `;` so a
`;` or a hiding-looking word inside one of those can't be misread as a
real declaration boundary.

## What this tool is (and isn't)

A fresh, independent implementation using only `html.parser.HTMLParser`
(stdlib, no `lxml`, no third-party dependency) — not a copy of
Scrapling's source, which uses `lxml`'s XPath engine. The CSS-declaration
tokenizing approach (blank comments/strings/`url()` before splitting on
`;`) mirrors the real source's specific technique directly, credited as
such rather than claimed as independently invented, since it's the
correct way to do this safely and any faithful reimplementation of the
same requirement converges on the same shape.

Two modes, kept clearly separate:

- **Faithful mode** (`is_hidden_element`, and the default for
  `sanitize_html`/`extract_visible_text`) — matches the real, current
  scope above exactly, including staying case-sensitive on `aria-hidden`.
- **Extended mode** (`extended=True`) — this project's own addition, not
  Scrapling's: also catches text pushed off-screen via a negative
  `text-indent`. Opt-in, never silently merged into faithful behavior.

**What stays out of scope in either mode, stated plainly:**
`position:absolute`/`fixed` combined with a large negative `left`/`top`
offset (needs tracking two declarations together against the element's
actual positioning context — a materially different check than a single
zero-value declaration), and anything needing full CSS-cascade resolution
— a `color` that happens to match its `background-color`, or hiding
achieved only via an external or `<style>`-block stylesheet rather than an
inline `style` attribute. That last one is not a gap unique to this
reimplementation: Scrapling's own real `_is_hidden_element()` only ever
inspects the inline `style` attribute too, confirmed by reading it
directly — a stylesheet-driven `display:none` rule would defeat the real
library exactly as it defeats this one.

Because sanitizing is this tool's entire purpose rather than a side effect
of restricting to `<body>`, `sanitize_html()`/`extract_visible_text()`
*always* sanitize — `main_content_only` here only narrows the scope to the
document's `<body>`, unlike the real source where the flag turns
sanitization on at all. Stated as a deliberate design difference, not an
oversight.

## API

```python
import sanitizer

sanitizer.extract_visible_text(html, main_content_only=False, extended=False)  # -> str
sanitizer.sanitize_html(html, main_content_only=False, extended=False)         # -> str (HTML)
sanitizer.find_removed_elements(html, extended=False)  # -> list[{"tag", "attrs", "reason"}]
sanitizer.is_hidden_element(node)    # faithful-mode check on a parsed node
sanitizer.is_hidden_extended(node)   # faithful + text-indent check
```

## Proof

`test_sanitizer.py`, 37/37 passing on a real run (`python3 test_sanitizer.py`):

- Every real hiding rule, positive and negative (the zero-value properties
  across six spellings each; the real source's own two docstring examples,
  `opacity:0.95` and `line-height:0.9`, both correctly kept; the
  case-sensitive `aria-hidden` check; the comment-splits-a-value non-goal;
  a semicolon inside a quoted string not breaking declaration parsing).
- Nested hidden subtrees fully removed, not just their wrapper tag.
- Noise tags (`script`/`style`/`noscript`/`svg`) and HTML comments removed.
- Zero-width-character and control-character stripping, independent of
  hidden-element removal, with tab/LF/CR confirmed kept.
- `main_content_only` scoping, including the no-`<body>` fallback.
- `find_removed_elements()`'s reasons checked against a planted fixture
  with one of each removal type.
- **The real scope boundary, locked in as a regression, not left as
  prose**: off-screen `position`+negative-offset hiding and
  color-matches-background hiding are both proven *not* caught in either
  mode; negative `text-indent` is proven not caught in faithful mode and
  proven caught in extended mode — a true discrimination pair, not just
  one direction.
- A realistic multi-technique adversarial fixture (a fake "SYSTEM:"
  instruction hidden via `display:none`, a fake instruction via
  `aria-hidden`, a fake instruction via `<template>`) fully stripped while
  real surrounding article text survives.
- Malformed HTML (unclosed tags, a mismatched end tag) tolerated without
  crashing.

No bug was found in this round's own first draft — stated plainly rather
than manufactured, unlike several other builds in this project's run where
a first draft did need a fix.

## A third mode: `render_sanitizer.py` — not faithful, more capable

`sanitizer.py`'s two modes are both regex-over-raw-HTML, the same
category of approach Scrapling itself uses — which is exactly why they
share Scrapling's real blind spots: neither catches off-screen
`position`+offset hiding, neither catches text colour matching its
background, and neither ever reads a `<style>` block or external
stylesheet (only inline `style` attributes). This sandbox happens to
have a real headless Chromium already set up for this project's own
screenshot-verification work (`/opt/pw-browsers/chromium`), so
`render_sanitizer.py` renders the page for real and asks the browser
itself — via `getComputedStyle()` and `getBoundingClientRect()` — what a
human would actually see. That closes every one of those gaps at once,
rather than adding one more hand-written heuristic:

- `render_and_find_hidden(html, ...)`, `render_sanitize_html(html, ...)`,
  `render_extract_visible_text(html, ...)` — the same three-function
  shape as `sanitizer.py`, one real Chromium launch per call.
- Catches everything the faithful/extended modes catch (`display:none`,
  `visibility:hidden`, `aria-hidden`, `<template>`, noise tags) **plus**
  off-screen positioning (`left`/`top` pushed negative), near-zero
  opacity, a zero-area clipped box (`height:0;overflow:hidden`), text
  colour matching its resolved background, and hiding driven by an
  external or `<style>`-block stylesheet rule — all genuinely impossible
  for a static-HTML regex to resolve, since several of them depend on
  the full CSS cascade (inheritance, specificity, stylesheet rules) being
  actually computed, not guessed at from the raw markup.
- `opacity_threshold` and `color_distance_threshold` are real, tested,
  configurable parameters, not hardcoded magic numbers — proven with a
  genuine borderline case on each side of both defaults.

**Stated limits, not hidden ones**: alpha-compositing across several
stacked semi-transparent backgrounds is approximated (blended once
against white, not walked through every ancestor's own blended
backdrop) rather than fully solved; it needs a real browser process per
call, so it is not a drop-in replacement for a context where spinning up
Chromium per request is too expensive — that's exactly when
`sanitizer.py`'s two free, dependency-light modes are the right choice
instead.

**A real bug found and fixed while building this, not assumed working
from the design**: the first draft removed `<head>` from the DOM
immediately upon finding it (reasonable — `<head>` is never rendered, so
reporting it as a "hidden element finding" would be noise), before
walking the rest of the document. That silently deleted whatever
`<style>` block lived inside `<head>` *before* later sibling elements
whose hidden state depended on that exact stylesheet were ever checked
— `getComputedStyle()` on a `.hide`-classed paragraph came back fully
visible once its own stylesheet had already been deleted out from under
it mid-walk. Caught immediately by
`test_external_stylesheet_hiding_is_caught` reporting zero findings
where three were expected. Fixed architecturally, not by special-casing
`<head>` later: the walk now runs in two passes — every hidden-reason
decision is made first, against the fully-intact document, and only
once that whole pass is done does a second pass actually remove
anything from the DOM. A second real bug, found in the same debugging
session: the original zero-size check required *both* width and height
to be exactly zero (`rect.width === 0 && rect.height === 0`), which
never matches the common `height:0;overflow:hidden` clamp pattern (a
block element keeps its full container width even at zero height) —
fixed to flag on either dimension being zero. A third, smaller
correction: an explicitly-passed `chrome_path` that doesn't exist on
disk was silently falling back to one of the real default browser
paths instead of failing on the path the caller actually asked for —
fixed so an explicit bad path always raises, while an *omitted*
`chrome_path` still searches the real defaults.

Proof: `test_render_sanitizer.py`, 24/24 passing on the real run,
including a direct discrimination proof against `sanitizer.py`'s own
two modes (the exact same off-screen and colour-matching fixtures that
both static modes fail on, confirmed failing on them in the same test
that confirms this mode catches them) and a realistic multi-technique
adversarial fixture combining four different hiding techniques at once.

## Deliberately not built

- An `lxml`-based version matching Scrapling's own parser exactly, for
  `sanitizer.py`'s two static modes — the point of those two modes is to
  be usable without that dependency; the stdlib parser's tree-building
  semantics (especially malformed-HTML recovery) will not match
  `lxml`'s byte-for-byte in every edge case, though every case this
  suite actually exercises matches the real source's documented
  behavior.
- A live cross-check against the actual installed `scrapling` package by
  importing and calling it — attempted, and blocked by this sandbox's
  auto-mode classifier ("Unauthorized Access" denial on executing the
  installed package's code), the same restriction this project already
  hit and documented for `morluto/rea`. Verification of `sanitizer.py`'s
  two static modes instead came from reading the real source file
  directly off disk (Grep + Read), the same method already established
  and credited elsewhere in this project when live execution isn't
  available. `render_sanitizer.py` is not a reimplementation of
  anything Scrapling has, so this limitation doesn't apply to it —
  every one of its own tests runs a real browser for real.
- Full, exact multi-layer alpha-compositing in `render_sanitizer.py`'s
  colour check — named above as a stated approximation, not silently
  left unmentioned.
