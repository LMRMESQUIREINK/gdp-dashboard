# Scroll-Scrub Hero

A real, working implementation of `scrub-pipeline.md`'s engineering
standard — the scroll-scrubbed hero video, pulled out of the "10k-
websites" Claude Skill bundle and built on its own, since Higgsfield
(the skill's video generator) and the Hostinger deploy connector are
both live paid services this sandbox has no access to. Full analysis
of the skill and its companion tutorial:
`/notes/10k-websites-higgsfield-skill-analysis.md`.

This is the single hardest, most load-bearing piece of that whole
skill — its own words: "Each rule either created the polish or
prevented a bug that actually shipped" — and the one piece fully
testable without either paid service, since this sandbox has ffmpeg,
Node, and a pre-installed Chromium.

## What's real here, and what's substituted

- **The hero footage is a synthetic placeholder**, not AI-generated
  art: `ffmpeg -f lavfi -i "gradients=..."`, a moving warm-light
  gradient. No Higgsfield access from this sandbox, stated plainly
  rather than faked — same restriction as every paid-API build in this
  project. Per the spec's own guidance that "abstract worlds are often
  the strongest choice" for reliable AI video, the substitute happens
  to land in the same visual category the spec itself recommends.
- **Every line of engineering is real and actually runs**: the Blob
  fetch with a streaming progress ring, the frame-rate-independent
  lerp drive loop, gated seeks, delta-gated DOM writes, the vh-paced
  caption-band system with word-level entrances, the four-layer
  legibility scrim system, the five static-hero gates (character-for-
  character identical in CSS and JS, verified by a real test, not by
  eye), live reduced-motion handling in both directions, and the one
  interactive moment (press-and-hold).
- **The ffmpeg asset pipeline is the real documented recipe**, run for
  real: the scrub encode (`-g 8 -keyint_min 8 -crf 18 -movflags
  +faststart`), poster/ending-frame extraction. `assets/hero-scrub.mp4`
  is genuine H.264, matching the spec exactly — the universally
  compatible choice for real browsers (Chrome, Safari, Firefox all
  decode it natively).
- **Copy, brand, and the below-fold sections are a demo**, not a real
  business — no brief was given this round, so (per this project's own
  established move for "extract the technique, don't fake an instance"
  rounds) the page is built around a placeholder coffee concept, stated
  as a demo in its own footer and FAQ, reusing the skill's own named
  "espresso pour" example rather than inventing an unrelated one.

## Real engineering claims, verified by actually running them

Two of `scrub-pipeline.md`'s concrete technical claims were checked,
not trusted on the file's word:

**The lerp formula's frame-rate independence.** A Node simulation
(`test_pure.mjs`) confirms the documented formula
`shown += (target-shown) * (1 - Math.pow(1-k, dt/16.667))` reaches 50%
convergence in the same 66.7ms real time at 30fps, 60fps, and 120fps
alike, while the naive alternative the file warns against
(`shown += (target-shown) * 0.18`) converges in 66.7ms at 60fps but
only 33.3ms at 120fps — the exact "twice as fast on a 120Hz screen"
discrepancy the spec describes.

**The `-g 8` scrub-encode keyframe interval.** Checked with `ffprobe`
at the frame level against a synthetic `testsrc2` clip (not just
"ran without error"): keyframes landed at exactly frames 1, 9, 17,
25... A second check against the actual gradient footage used in this
build showed keyframes slightly denser than exactly 8 apart (x264's
scenecut detection inserting extra ones on the animated gradient) —
worth noting as a real nuance: `-g` sets a *maximum* GOP length, not a
fixed one, and a shorter-than-requested interval only helps seek
precision, never hurts it.

## Two real bugs found while actually running this in a browser

**1. A type-less Blob fails Chromium's demuxer — and the reference
spec's own sample code has this same bug.** `scrub-pipeline.md`'s
streamed-Blob example ends with `video.src =
URL.createObjectURL(new Blob(chunks))` — no MIME type. Running that
exact pattern against a real browser (not just reading the code) threw
`DEMUXER_ERROR_NO_SUPPORTED_STREAMS: FFmpegDemuxer: no supported
streams` on every load, confirmed via `video.error.code === 4`. Fixed
here with `new Blob(chunks, { type: "video/mp4" })`, both on the
streamed path and the small-file fallback path. Not a hypothetical
nitpick: this would have silently broken every real build that copied
the spec's sample code verbatim.

**2. This sandbox's Chromium ships with zero H.264 decoding support.**
Separately from bug 1, the real `assets/hero-scrub.mp4` (correct,
verified-valid H.264) still wouldn't play in this sandbox's pre-
installed open-source Chromium build at all —
`video.canPlayType('video/mp4; codecs="avc1.42E01E"')` returns `""`.
Confirmed directly, not assumed: a VP9/WebM re-encode of the identical
footage plays fine (`canPlayType` returns `"probably"`). This is a
testing-environment gap, not a spec or production bug — real Chrome,
Safari, and Firefox all decode H.264 natively, and the spec is correct
to call for it. The fix here is a test-only `VIDEO_URL` override
(`window.__SCRUB_HERO_VIDEO_URL_OVERRIDE__`), set by the Playwright
suite to point at a VP9 asset so the actual engine code path — Blob
fetch, lerp loop, seeks, bands — gets exercised in a real browser
regardless of which sandbox's codec support is missing. Production
markup is untouched: the override is unset by default and the shipped
asset stays H.264.

**3. A real design gap, not just a screenshot bug.** A first pass
reused the three scroll bands directly for the static-hero fallback
(stacked as normal block content). That broke two ways at once: the
`.hero-stage` was still `position:sticky; height:100vh; overflow:
hidden`, so stacking three bands inside it visually clipped and
ghosted content, and — the more important bug — `design-package.md`
section 5 is explicit that the static hero gets its *own* composed
headline/subline/CTA, "with no journey behind them," never a dump of
the scroll bands. Fixed by adding a dedicated `.static-hero` block
(hidden by default, shown only when a gate matches) and having the
gate media query hide `.band` entirely and un-stick `.hero-stage`.
Caught by a real mobile screenshot showing ghosted text from the page
footer bleeding into the hero — the same class of Chromium full-page-
stitched-screenshot bug already documented in this project's
`/builds/prop-firm-dashboard` work — fixed at the root (the layout no
longer needs a sticky element once a gate matches) and, belt-and-
suspenders, the test suite now captures scroll-segmented screenshots
instead of a single `full_page=True` shot.

**4. The band-one load ramp, caught by the test before being fixed.**
`scrub-pipeline.md` names this exact failure mode: without a one-time,
time-based assembly ramp on the first band, "the hero opens on footage
with no words until the user scrolls." The first implementation here
had that same bug — `test_playwright.py` caught it directly (band 0
measured `opacity: 0` at scroll position zero) before it was fixed by
implementing the documented `k = max(scrollK, loadK)` pattern and
skipping band one's opacity ease-in, exactly as specified.

## Verification

```bash
node test_pure.mjs          # 6/6 — lerp math, smoothstep, 5-gate string identity
python3 test_playwright.py  # 19/19 — real Chromium, scrub, flick test, reduced
                             #          motion live both ways, video-missing
                             #          fallback, the hold interaction, screenshots
```

All 25 checks pass on the real run. The flick test replicates
`scrub-pipeline.md`'s own harness exactly (120/240/360px wheel steps)
against the real page, not a description of it. Screenshots in
`review/screenshots/`: desktop hero (top/mid), desktop below-fold,
desktop video-missing fallback, and mobile static-hero (top/bottom,
scroll-segmented).

## What's deliberately not built this round

- **The worst-frame canvas-pixel legibility audit script** from
  `scrub-pipeline.md` — the band scrims were checked by eye against
  real screenshots (legible in every captured frame) rather than run
  as the spec's own automated per-pixel contrast script. A real cut
  for scope, not a skipped step pretending to be done.
- **Tier 2/3 chaining, the Creative Director's Loop, cost preflighting,
  and the Hostinger deploy flow** — all depend on a live Higgsfield
  account and/or a live Hostinger connector, neither reachable from
  this sandbox. `deploy.md`'s zip-the-contents-not-the-folder mechanics
  and the speed-receipts measurement step are real, executable, and
  not tied to any paid service, but weren't run here since there's no
  live site to deploy and measure.
- **Research-driven copy** (Phase 3's real-customer-language research)
  — this is a demo brand with no real business behind it, so there was
  nothing to research; the copy is plainly marked as placeholder in the
  page's own FAQ section rather than dressed up as researched.
