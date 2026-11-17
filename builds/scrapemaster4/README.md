# ScrapeMaster 4.0

A completed, working build of `LMRESQUIREINK/ScrapeMaster4.0` — a public
GitHub repo pasted into this session with no instruction attached, which
(per this project's own convention) is itself the instruction to run the
deep-analysis-and-ship loop. Full write-up of what the real upload actually
contained: `/notes/scrapemaster4-analysis.md`.

## What was actually in the upload

Every intended `.py` file in the real repo — `scraper.py`, `streamlit_app.py`,
`api_management.py`, `assets.py`, `pagination_detector.py`, `test.py`,
`__init__.py`, `__main__.py`, `__pip-runner__.py` — was **0 bytes**. The
real content never made it into any of them. Instead it was scattered
across oddly-named scratch files: `README.mdgit` literally contains
unexecuted shell commands run together with no newlines (`"# ScrapeMaster4.0"
initgit add README.mdgit commit -m "first commit"...`), `"Navigate to Your
Project Directory.txt"` is a pasted AI-assistant chat reply about a venv
error (quoting the real Windows path `C:\Users\LMRESQUIREINK\ScrapeMaster4.0`
— the owner's own username, confirmed matching the GitHub account this repo
is under), and a 115KB file literally named `"from bs4 import
BeautifulSoup.txt"` contains four separate draft scraper scripts, each
wrapped in its own "Here's the complete script..." AI-chat framing. The
pattern reads as: whatever tool the uploader pasted text into saved each
paste as a new file named after its first words, rather than running the
commands or landing the code in the files meant to hold it.

`requirements.txt` also names two package versions that **do not exist on
PyPI at all** — confirmed directly with `pip index versions`, not assumed:
`html2text==2023.3.9` (real versions jump from `2020.1.16` to `2024.2.25`;
no `2023.3.9` anywhere) and `streamlit-tags==1.3.0` (real versions top out
at `1.2.8`). Both would make `pip install -r requirements.txt` fail outright.

## What this build does

Assembles the real, working app the file names and `requirements.txt`
clearly intended, using the salvageable logic from the pasted drafts as
reference material rather than starting from nothing — the same move this
project made for Trading Jarvis, Kryptera Pro, and every other "scaffold
named but never filled in" upload:

- **`scraper.py`** — `fetch_html()` (retried, real headers), `clean_html_to_text()`
  (strips `<nav>`/`<footer>`/`<header>`/`<aside>`/`<script>`/`<style>`
  structurally, then runs `readability-lxml` + `html2text` on what's left),
  `scrape()` (fetches, extracts via an `LLMClient`, follows detected
  pagination up to `max_pages`).
- **`pagination_detector.py`** — a real heuristic: `rel="next"` first, then
  `<link rel="next">`, then common "next page" link text (`Next`, `Older`,
  `More`, `›`, `»`, `→`), resolved to an absolute URL.
- **`api_management.py`** — a provider layer for OpenAI/Groq/Gemini, each
  reachable through one injectable `call_fn` so it's testable without a
  real key or network call; `load_api_key()` fails with a plain-English
  message on a missing *or placeholder-looking* key, never a raw SDK auth
  error; `truncate_text()` uses `tiktoken` for exact token counting with a
  documented approximate-length fallback (see below).
- **`assets.py`** — the provider/model list and default field-tag examples.
- **`streamlit_app.py`** — the UI: URL input, a `streamlit-tags` field list,
  provider selector, a pages-to-follow stepper, a results table, and CSV/
  Excel export via `pandas`/`openpyxl`.
- **`requirements.txt`** — both fabricated versions replaced, and every
  other package bumped to a real, current, actually-installed-and-tested
  version rather than preserved at its original (also years-stale) pin —
  including swapping `google-generativeai` (confirmed, by actually
  importing it, to print "**All support for the `google.generativeai`
  package has ended**... switch to `google.genai`" at import time — not
  just old, fully retired) for the real current `google-genai` SDK, with
  `api_management.py` written against its real, current
  `genai.Client(api_key=...).models.generate_content(...)` call shape,
  confirmed by introspecting the installed package directly rather than
  guessed.
- `__main__.py` and `__init__.py` aren't needed for a flat Streamlit script
  and weren't recreated; `__pip-runner__.py` is almost certainly pip's own
  internal temp-file artifact, accidentally committed rather than an
  intended module — flagged here rather than silently dropped or given
  invented content.

## A real bug found while testing, not assumed working from reading the code

The first version of `clean_html_to_text()` relied only on
`readability-lxml`'s link-density/text-volume scoring to separate the real
article from navigation and footer boilerplate. Tested against this
build's own short fixture page, it kept the `<nav>` and `<footer>` text
verbatim — the page is simply too short for readability's heuristic to
have enough signal to work with, confirmed by printing the actual output
rather than assuming the dependency "just works." Fixed by stripping
`<nav>`/`<footer>`/`<header>`/`<aside>`/`<script>`/`<style>` structurally
*before* handing the page to readability, which is unambiguous regardless
of page length, then letting readability do what it's actually good at
(density-based noise like sidebars and related-post widgets) on what's left.

## tiktoken's own first-run network dependency, found and handled

`tiktoken` ships no vocabulary data in its pip package — it downloads the
real encoding file from `openaipublic.blob.core.windows.net` on first use
and caches it after. That host is blocked by this sandbox's egress proxy,
confirmed directly (a real run raised a 403 through the proxy, not assumed
from the standing restriction list). Since a real user's first run could
hit the same failure on a firewalled or offline machine, `truncate_text()`
falls back to a documented approximate word-based truncation on any
encoding-load failure rather than crashing — a real, if small, piece of
genuinely better engineering than what the original scaffold would have
had even if its code had existed, since nothing in the pasted drafts
accounted for this at all. The exact-tiktoken code path itself is
unverified from this sandbox for the same reason; only the fallback path
has actually been exercised.

## Proof

`test.py`, 19/19 real assertions, `python3 test.py`:

- `fetch_html`/`clean_html_to_text`/pagination detection run against a
  **real local `http.server` fixture over loopback** (five real HTML
  fixtures, including a two-page `rel="next"` pagination chain, a
  text-link pagination case, and a no-next-page case) — not mocked HTTP.
- `api_management`: missing-key and placeholder-key rejection, a
  real-shaped key accepted, the truncation fallback bounded correctly,
  and `LLMClient.extract()` exercised through its injectable `call_fn` —
  valid JSON parsed, a Markdown code fence stripped, a missing requested
  field defaulted to `""`, and a non-JSON response raising `ExtractionError`
  rather than crashing.
- `scraper.scrape()` end-to-end against the real local server with a
  mocked LLM call: a single page, following real pagination for exactly
  two real HTTP fetches, stopping at `max_pages` even though a further
  `rel="next"` link exists, and stopping naturally at a real no-next-page
  fixture.

`streamlit_app.py` served locally and screenshotted with Playwright/Chromium
(desktop 1280px, mobile 375px) per the screenshot-before-done rule — clean
on the first pass, zero layout bugs, zero real console errors (only the
expected, harmless block of Streamlit's own telemetry beacon by this
sandbox's egress proxy). A third check drove the actual "Scrape" button
with no API key configured: it surfaces the plain-English
`MissingAPIKeyError` message as a normal Streamlit warning banner, not a
crash or a traceback.

## Round 2: the three suggested next-moves, all three, not a subset

### 1. Selenium/`webdriver-manager` fallback for JS-heavy sites

`fetch_html_selenium()` and `scrape(..., use_selenium=True)` — resolving
a matching chromedriver via `webdriver-manager` rather than committing a
platform-specific binary into the repo (the real anti-pattern the
original upload's empty `chromedriver.exe` placeholder pointed at).

**A real, checked environment limitation, not a hypothetical one**: this
sandbox has a real `chromedriver` already on disk (147.0.7727.24, from a
Node.js toolchain) but the only installed Chrome/Chromium is six major
versions ahead (`153.0.8010.12`) — Selenium refuses the session outright
on that gap (`This version of ChromeDriver only supports Chrome version
147`). `webdriver-manager`'s own fallback — downloading a matching
driver — is also blocked, confirmed directly (`ConnectionError: Could
not reach host`), the same egress-proxy restriction as every other
blocked host in this project. `fetch_html_selenium()` is written for a
normal deployment with ordinary internet access (where
`webdriver-manager` resolves a real matching driver), but is **not**
verified end-to-end against a real browser-rendered page from this
sandbox — only that it fails *cleanly*, as a typed
`SeleniumUnavailableError` with the real cause attached, rather than a
raw Selenium stack trace. That clean-failure behavior is what the test
suite actually locks in.

### 2. A schema/content preview before spending an API call

`preview_page()` fetches and cleans a page with zero LLM calls, shown in
the UI as a "Preview page" button producing a text area of the cleaned
content — lets a user confirm their requested fields actually appear on
the page before paying for an extraction that won't find them. A
separate "Output columns for this run" table (driven by the real
`fields` list, no LLM call either) previews the literal CSV/Excel
columns a run will produce, satisfying the csv/xlsx-schema reading of
"preview" as well as the content reading.

### 3. Batch/unattended mode

`batch_scrape()` runs one field set over a list of URLs, aggregating
every page from every URL into one flat result list — one sheet, not
one per URL. The UI gained a "Batch mode" toggle swapping the single URL
input for a multi-line URL textarea. For the "scheduled" half of the
ask, rather than faking a cron daemon inside this sandbox (there's
nothing here to schedule against), the real deliverable is
**`batch_scrape.py`**, a standalone CLI any real scheduler (cron,
Windows Task Scheduler) can point at directly:

```
python3 batch_scrape.py --urls urls.txt --fields title,price \
    --provider openai --out results.csv
```

A single bad URL doesn't abort the batch by default (`--stop-on-error`
to change that) — matching this project's own established
continue-on-error convention from `github-repo-manager-safety-wrapper`.

## Proof, round 2

`test.py` is now 28/28 (up from 19), all real: `preview_page()` and
`batch_scrape()` run against the same real local `http.server` fixtures
as round 1 (a multi-URL aggregation test, a skip-vs-raise bad-URL test),
`fetch_html_selenium()`'s clean-failure path is exercised for real
against this sandbox's actual blocked state rather than mocked, and
`batch_scrape.py` is driven as two real subprocess calls (a missing-flags
`argparse` error, and a no-API-key run that fails with the plain-English
message rather than a traceback). `streamlit_app.py`'s updated UI
(batch toggle, browser-rendering checkbox, schema-preview table, preview
button) was screenshotted again per the screenshot-before-done rule —
the first pass found one real cosmetic bug (the "Browser rendering
(JS-heavy sites)" checkbox label truncated inside its column at desktop
width), fixed by shortening the label and moving the detail to a
tooltip, then re-verified clean on a second pass at both widths.

## Deliberately not built

- Pushing this back to `LMRESQUIREINK/scrapemaster4.0` itself — this
  session has read-only access to that repo (no fork, no push
  credentials), the same standing limit as every other external-repo
  build in this project; the completed work lands here instead, same
  precedent as `github-repo-manager-safety-wrapper`.
- Any real scraping against a live third-party site — this sandbox's
  standing no-live-network-access restriction, same as every other build
  here; every test runs against this build's own local fixture server.
- A real, successful browser-rendered fetch — blocked by this sandbox's
  chromedriver/Chrome version mismatch plus the blocked driver download,
  stated above rather than worked around with a fake pass.
