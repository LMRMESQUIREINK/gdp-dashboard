# OKF Navigator

A standalone, independent Python implementation of the navigation,
trust-tier, and lifecycle-staleness rules from Google's real **Open
Knowledge Format (OKF) v0.2**, built from a 5-article PDF bundle
("Google's New OKF Could Change How We Build RAG Systems for AI Agents"
and four companion production-AI-systems articles) — see
`/notes/okf-rag-agentic-bundle-analysis.md` for the full source
verification this build is based on.

## What was verified before writing any code

OKF is real: Google Cloud's own blog and the real GitHub repo
`GoogleCloudPlatform/knowledge-catalog` (Apache 2.0) were cloned directly,
and `okf/SPEC.md` (v0.2) was read in full before writing a single line of
this module. Every mechanism below is implemented against that spec text,
not the article's paraphrase of it, and **not** copied from the real
reference agent's own Python implementation that also lives in that repo
(it was not read, by design — this is an independent reimplementation).

One precision note worth recording: the real repo has since moved — the
original `okf/` subdirectory in `knowledge-catalog` is explicitly marked a
"frozen snapshot, no longer maintained" in its own README, with current
work continuing at `GoogleCloudPlatform/open-knowledge-format`. The article
cites the frozen snapshot's location; that was accurate at the time the
article and this clone were made, not a factual error.

## Mechanisms implemented, each tied to a spec section

- **Concept parsing** (YAML frontmatter + Markdown body) and **link
  resolution**, per SPEC.md §6. Both the "recommended" absolute
  bundle-relative form (a link beginning with `/`) and the ordinary
  relative form (`./other.md`, `../dir/other.md`) are resolved correctly,
  including `..` traversal. A link to a concept that doesn't exist in the
  bundle is tolerated, not treated as an error — the spec states this
  explicitly, and `navigate()` simply doesn't step there rather than
  raising.
- **Trust tiers**, per SPEC.md §5.3 exactly: three tiers only
  (`unverified` / `machine-confirmed` / `human-reviewed`), derived from
  whether any `verified` entry's `by` field starts with `human:`. This is
  purely advisory per the spec ("Trust tiers are advisory signals, not
  access control") — the module never raises on an untrusted or unverified
  concept, only reports its tier.
- **Lifecycle staleness**, per SPEC.md §5.5 exactly: a concept is stale iff
  `now >= stale_after` — an absolute instant, never a relative TTL. The
  boundary itself counts as stale, tested directly.
- **Status**, per SPEC.md §5.4: `draft | stable | deprecated`, defaulting
  to `stable` when absent.
- **Bounded-depth navigation** (`navigate()`, `impact_report()`) — this
  project's own addition, built directly from the article's worked example
  (discovering the impact of an Authentication Service's token-expiration
  change by following links to Token Policy / API Gateway / Customer
  Login, rather than loading an entire knowledge base into context). A
  real breadth-first traversal bounded by hop count, never a full-bundle
  dump — the article's own "progressive disclosure" idea made concrete and
  testable.

## A real finding from the real Google sample fixtures

Three real, unmodified sample files were copied from
`GoogleCloudPlatform/knowledge-catalog`'s real `okf/bundles/` directory
(Apache 2.0 — see `fixtures/real-google-samples/UPSTREAM-LICENSE.md`) and
used as test fixtures, not just synthetic data:

- `gross-margin.md` (from `bundles/acme_retail/metrics/`) — a rich,
  human-verified concept exercising `stale_after`, `status: stable`, and
  real relative links at different depths (`./revenue.md`,
  `../computations/gross-margin-period.md`).
- `bad_question_flag_ratio.md` (from
  `bundles/stackoverflow/references/metrics/`) — has `generated` but
  deliberately **no** `verified` key at all: the real-world case for the
  `unverified` trust tier.
- `references-index.md` (from `bundles/stackoverflow/references/index.md`)
  — copied in expecting it to exercise the progressive-disclosure
  `index.md` convention as a loadable concept. **Running the real test
  suite against it immediately surfaced that it isn't one**: the real
  file has no YAML frontmatter block at all — it's a plain bulleted list
  of links. Confirmed by reading the file directly rather than assumed.
  This is a genuine, checked property of OKF's real `index.md`
  convention, not a bug in the sample: these entry points are lightweight
  navigational lists, not concepts carrying trust/staleness metadata.

That finding also caught **a real bug in this module's own first draft**:
`load_bundle()` initially called `parse_concept()` unconditionally on
every `.md` file under a bundle root, so the real upstream
`UPSTREAM-LICENSE.md` copy sitting alongside the real fixtures (itself a
plain `.md` file with no frontmatter) raised `OkfParseError` and crashed
the whole load on the very first real run. Fixed in `load_bundle()`: a
`.md` file is now only parsed as a concept if it actually opens a
frontmatter block (`---` on the first line); a file that opens one but
then fails to parse (invalid YAML, non-mapping frontmatter) still raises
immediately, since that's a genuinely malformed concept, not a missing
one. Both the real bug and the real `index.md` finding are locked in as
permanent regression tests.

**Stated scope boundary, not a silent gap**: because `index.md` files
carry no frontmatter under this real convention, this module does not
currently treat their own links as navigable edges — `navigate()` only
walks links that originate from a parsed concept. A future extension
could give `index.md` files a lightweight non-concept node type purely
for navigation purposes; not built this round since the article's own
worked example (and every real sample this round tested against) doesn't
need it.

## Proven

`python3 -m unittest test_okf_navigator.py` — **41/41 tests pass**,
including:

- The three real, unmodified Google-authored sample fixtures above (the
  human-reviewed/unverified trust-tier distinction, the real
  `stale_after` boundary, and the real non-frontmatter `index.md`
  finding).
- A reconstruction of the article's own described Authentication Service
  / Token Policy / API Gateway / Customer Login scenario
  (`fixtures/auth-scenario/`) — stated plainly as this build's own
  content, written from the article's narrative description, not a
  verbatim transcript the article never actually printed (the article
  doesn't print literal file contents for this example).
- Absolute vs. relative link resolution, including `..` traversal from
  different depths.
- Explicit broken-link tolerance (`navigate()` never raises on a dangling
  link; it simply isn't a step anywhere).
- Bounded-depth traversal actually stopping at the configured hop limit,
  with a cycle (API Gateway linking back to Authentication Service)
  correctly not causing a revisit or infinite loop.
- All three trust tiers and the exact stale-boundary semantics
  (`now >= stale_after`, including the equality case).

## Dependency

`PyYAML` (real nested frontmatter structures — nested maps, lists of
flow-style maps — appear throughout real OKF concepts; a hand-rolled
regex parser, the convention `skill_md_validator.py` uses elsewhere in
this project, would risk under-parsing them). Stated as a deliberate,
justified new dependency, same precedent as `verify_signature.py` needing
`cryptography` in an earlier round.

## Checked `/builds/` first

Nothing in this project parses a markdown-with-YAML-frontmatter knowledge
graph or implements multi-tier trust/staleness semantics over one.
`agent-memory-layer`'s lifecycle states are for agent memory records, a
different domain; `manifest-drift-guard` checks file-hash drift, not
semantic trust tiers. Genuinely new.

## Deliberately not built this round

See `/notes/okf-rag-agentic-bundle-analysis.md` for the full source
bundle's other generalizable mechanisms (the Security-Trimmed Index's
ACL-filtered-query pattern, the Verified Identity Agent Bridge's /
Delegated Boundary OAuth's credential-exchange chain, the Production
Agentic AI Blueprint's stage/confirm/commit write-tier pattern) — each a
candidate next move, not built reflexively this round in favor of one
well-tested mechanism.
