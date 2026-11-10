# Analysis: `coreyhaines31/marketingskills`

Source: a bare GitHub repo link,
`https://github.com/coreyhaines31/marketingskills.git`, no accompanying
instruction — handled per this project's standing `/analyze-and-ship`
loop. Cloned and read directly rather than summarized from its own
README, same discipline as every other bare-repo-link round in this
project (`bytedance/deer-flow`, `morluto/rea`, `oil-oil/oil-ui`).

## What it is, measured first

A real, MIT-licensed, actively-maintained Claude Skills marketplace —
53 skills, by Corey Haines. Independently confirmed real and currently
active via web search before trusting anything about it: Corey Haines
is a real, well-known SaaS marketing consultant (Swipe Files,
Conversion Factory), and multiple distinct third-party sources
(landing.so, claudecodeformarketers.com, riffkit.ai, tosea.ai,
pawgrammer.com, marketing-skills.com, mrtechking.com, aiskill.market)
independently cover this exact repo. Those sources disagree on the
exact skill count (33–53) — attributed to different repo snapshots over
time, not treated as a discrepancy against the source itself, since a
growing, actively-committed repo is expected to show a higher count the
later it's checked.

It targets the Agent Skills open spec (`agentskills.io`) explicitly,
working across Claude Code, Codex, Cursor, and Windsurf — not a
Claude-Code-only tool. Real CI exists and runs more than a lint pass:
`regression-tests.yml`, `validate-skill.yml`, `skill-packaging.yml`,
`sync-skills.yml`, `check-versions.yml`, plus a plugin-marketplace
structure and a disclosed-sponsorship `tools/PARTNERS.md` with a stated
non-influence boundary on the sponsored content.

## The real, dated, checkable finding: a character budget, not a vague warning

`evals/triggers/README.md` documents something concrete and
reproducible: Claude Code caps the total skill-listing text it sends
the model at roughly **30,000 characters**. Skills whose descriptions
push the pack past that cap get truncated to a bare name with no
description at all in the listing — silently losing their only real
shot at triggering correctly, since the model never sees what the
skill is for.

Their own measured table across pack versions, with a dated,
reproducible methodology stated plainly ("Checked on 2026-11-09 with
Claude Code 2.1.319 by reading the `skill_listing` the session
recorded"):

| Pack version | Total chars | Name-only alone | Name-only crowded |
| --- | --- | --- | --- |
| before 2.14.3 | 42,105 | 26/53 | 29/53 |
| 2.14.3 | 19,259 | 0/53 | 2/53 |
| 2.14.8 | 18,676 | 0/53 | 0/53 |
| 2.14.9 | 18,662 | 0/53 | 0/53 |

Their own recommendation, derived from that real data rather than
asserted: keep each skill's description at **≤500 characters**.

## A real, well-evidenced three-way discrepancy

`AGENTS.md` (this repo's own contributor guide) states: "`description`
is 1-500 characters (the spec allows 1024; this repo caps it, see
below)" — i.e. the Agent Skills open spec's own documented max is
claimed to be **1024** characters.

That claim could **not** be independently verified from this sandbox.
A `web-fetch` subagent dispatch to confirm it against `agentskills.io`
directly failed: `getaddrinfo ENOTFOUND agentskills.io` — the domain
doesn't resolve from this session. This is the same restriction class
already documented repeatedly in this project for other domains (EODHD,
FMP, Hugging Face, arXiv, ui.oiloil.org), now extended to one more.
Reported here as "AGENTS.md's own stated claim, not independently
confirmed," not as settled fact.

That leaves three different numbers describing the same kind of limit,
none of them in agreement:

1. **1024 characters** — the Agent Skills spec's claimed max, per
   marketingskills' own `AGENTS.md` (unverified from this sandbox).
2. **500 characters** — marketingskills' own real, dated, self-imposed
   recommendation, derived from the actual `skill_listing` measurement
   above.
3. **1500 characters** — this project's own pre-existing
   `skill_md_validator.py` "too long" **error** threshold, from an
   earlier round, looser than even the unverified spec max.

This directly closes a gap that validator's own pre-existing docstring
had explicitly flagged as unconfirmable ("a hard limit this build could
not independently confirm") — not by picking a winner among the three,
but by recognizing they measure different things. The 1500-char
threshold answers "is this no longer a description at all" (a
structural sanity check). The 500-char figure answers a materially
different, now-measured question: "will this description actually
survive being shown to the model once the whole pack is loaded
alongside others." Collapsing them into one number would have thrown
away that distinction.

## Decision: extend, don't duplicate

Checked `/builds/` first, per this project's standing rule. The
natural home for this finding is the existing
`/builds/skill-md-validator/` (built two rounds ago from a different
AgentsKit.co bundle, already checking exactly this class of thing
against this project's own real skills) — not a new build. Extended it
rather than forking:

- Added a new, separate `description-over-recommended` **warning**
  (500 chars) alongside the existing `description-too-long` **error**
  (1500 chars) — additive, not a replacement, preserving every existing
  caller's behavior.
- Added `check_pack_description_budget()` — the same 19,000-char
  warn / 30,000-char cap figures, applied at the whole-pack level via a
  new `validate_pack()` entry point, returning warning-level findings
  only (never error-level — a deliberate design choice, since neither
  figure is a hard failure the way a broken reference is).
- Added `check_description_overlap()` — a Jaccard-word-overlap
  heuristic across every pair of descriptions in the pack, flagging
  pairs that might compete for the same trigger. Deliberately uses a
  **separate** stopword list (`OVERLAP_STOPWORDS`) from the
  pre-existing, unfiltered `_similarity()` helper used for thin-body
  detection, specifically to avoid false-flagging two skills that
  merely share this project's own trigger-phrase boilerplate ("use when
  the user wants to...") as if that were real content overlap — proven
  directly with a dedicated test
  (`test_shared_boilerplate_trigger_phrasing_alone_does_not_count_as_overlap`),
  which passes.

## Real findings against this project's own material, not synthetic fixtures

Ran both new pack-level checks against this project's own 12 real
skills (`.claude/skills/*`), not just synthetic test fixtures:

- **Per-skill 500-char warning**: four skills genuinely exceed it —
  `launch-kit-writer` (721 chars), `sales-page-engine` (613),
  `voice-extractor` (576), `launch-pad` (519) — confirmed by direct
  character count. (A first draft of the corresponding test only named
  three, having miscounted `launch-pad`'s 519 as under the 500-char
  line when it plainly isn't — the test suite's own first real run
  caught the miscount immediately, and the test was corrected to match
  the real, re-verified count rather than the other way around; see
  `test_four_real_skills_now_warn_over_the_real_500char_recommendation`
  in the build's own test file.) All four are warnings, still well
  under this project's existing 1500-char error ceiling.
- **Pack-level budget**: this project's own 12 skills total roughly
  5,549 characters of description text combined — nowhere near either
  the 19,000-char warn line or the 30,000-char hard cap. An honest,
  non-manufactured "no problem found" result.
- **Description overlap**: zero cross-skill overlap detected across
  all 12 skills. Also an honest, non-manufactured "no problem found"
  result, consistent with those 12 skills covering genuinely distinct
  domains (sales copy vs. voice matching vs. code review vs. retro,
  etc.) rather than crowding each other.

## What's deliberately not built

The one thing marketingskills has that this validator structurally
cannot reproduce from this sandbox: a real trigger-*accuracy* eval.
`evals/triggers/scripts/trigger-eval.mjs` runs several hundred real
prompts (`prompts.json`: 3 per skill, direct/indirect/near-miss, plus
12 deliberately non-marketing prompts; several `heldout*.json` sets)
through headless `claude -p` with the pack loaded as a real plugin, and
scores which skill the model actually invokes against an `expect` list
— outcomes of `pass`, `wrong-skill`, `other-skill`, `no-trigger`,
`false-trigger`, `error`. That harness's own README documents real
measurement noise even with a live model (three identical crowded runs
scoring 80.2%/84.0%/87.7%) and an honest "what's left" section (~7% of
judgement-style prompts under a crowded, 90-other-skills install still
get answered with no skill invoked at all).

This sandbox has no live Anthropic API access to run a nested `claude
-p` against real prompts — the same standing restriction as every
other build in this project that would need a live model call
(`trading-jarvis`'s mocked-Anthropic-client convention, `jev-pattern-
router`'s classifier substitute, etc.). `check_description_overlap()`'s
Jaccard heuristic is stated plainly, in both the module's own docstring
and the build's README, as a cheap, model-free *proxy* for the same
underlying risk marketingskills measures directly with a live model —
never claimed as a substitute for it, and explicitly noted as unable to
reproduce the real noise/variance the live-model harness documents in
its own numbers.

## Verification

```bash
cd builds/skill-md-validator
python3 -m pytest test_skill_md_validator.py -v
```

31/31 tests pass (up from 19), including the four new real/synthetic
test classes covering `check_pack_description_budget`,
`check_description_overlap`, and `validate_pack()`'s combined
`{"skills": [...], "pack_level": [...]}` JSON output shape, plus the
corrected real-skill count (this project now has 12 skills, not 11).
