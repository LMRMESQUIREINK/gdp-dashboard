# Deep analysis: the "10k-websites" Claude Skill + its companion tutorial

A second, distinct "$10K website" bundle from this round, separate from the
first ("Build $10,000 Websites using Claude Code (Ultimate Guide)",
analyzed in `/notes/10k-website-claude-code-analysis.md`). This one is a
full Claude Skill package (`SKILL.md` plus five `references/` files —
`deploy.md`, `design-package.md`, `ffmpeg-recipes.md`, `prompt-laws.md`,
`scrub-pipeline.md`) and its companion tutorial, "How to Build $10K
Websites in Minutes (Claude AI)". Read in full, cross-checked against
each other and, where possible, actually executed rather than taken on
faith — the central move this project repeats on every source.

## What this bundle actually is, and how it differs from round 1

Round 1's bundle was: Frontend Design + UI/UX Pro Max (two free,
unaffiliated Claude skills) building a static HTML/CSS site, no paid
media generation, deployed as a plain zip to Hostinger. This bundle is
architecturally different: a cinematic, scroll-scrubbed hero *video*
(one 6-second AI-generated clip whose playback time is driven by scroll
position) built on three paid/connected tools used together —
**Higgsfield** for image/video generation, **Claude Code** for the
build, and a dedicated **Hostinger MCP connector** for deploy — all
three named as non-negotiable ("the pipeline is where none of
[the creativity] is... never offer [a substitute], never mention it as
an option"). Same end positioning ("$10,000 website," Hostinger as the
host), same general shape as round 1, but a different, more ambitious
technical core.

## A fact worth stating plainly, straight from the file's own text

`SKILL.md` and `deploy.md` both hard-code two affiliate/partner links
directly into the instructions an installing user's Claude session would
run: `https://meticsmedia.com/higgsfield-ESVT` and
`https://meticsmedia.com/hostinger-ESVT`. The skill is honest about this
rather than hiding it — it explicitly instructs "say so plainly in one
line beside it" every time either link is shared — so this isn't a
deceptive-dark-pattern finding, just a material fact about who benefits
financially from this skill's distribution, same category of disclosure
this project already applied to the Factory.ai paper ("every capability
ties to a paid Factory.ai product, page ends on CONTACT SALES") and the
RUTHLESS TRADING GOLD/Hostinger links in round 1's own video. Worth
naming directly: this is a commercial funnel with an engineering
document riding inside it, not a neutral tutorial, and that's a
different category from Anthropic's own `frontend-design` skill
analyzed in round 1, which carries no such link anywhere in its text.

## What's genuinely well-engineered, checked by actually running it

This is the first source in this project's whole run of deep analyses
whose core technical claims could be **executed and measured**, not just
read and critiqued. Two concrete claims from `scrub-pipeline.md` were
independently verified rather than taken on the file's word:

**1. The frame-rate-independent lerp claim.** The file states that its
drive-loop formula —
`shown += (target - shown) * (1 - Math.pow(1 - k, dt / 16.667))` —
converges at the same real-world speed regardless of refresh rate, and
that the "obvious" naive alternative (`shown += (target - shown) * c`
with a flat per-frame constant) converges twice as fast at 120Hz as at
60Hz, which the file calls out as a real bug class ("the site feels
different per machine"). Verified numerically
(`node` simulation, not just read): the documented formula reaches 50%
convergence in **exactly 66.7ms at 30fps, 60fps, and 120fps alike**; the
naive version reaches the same 50% point in 66.7ms at 60fps but only
33.3ms at 120fps — precisely the 2x discrepancy the file describes. The
engineering claim is correct, not just plausible-sounding.

**2. The ffmpeg scrub-encode recipe.** Ran the exact documented command
(`-c:v libx264 -crf 18 -preset slow -g 8 -keyint_min 8 -pix_fmt yuv420p
-movflags +faststart -an`) against a synthetic 1920x1080 6-second test
pattern (this sandbox has no Higgsfield access, so a real generated hero
video doesn't exist here — a `ffmpeg testsrc2` pattern stands in, stated
plainly as a substitute, not a disguised one). The command ran clean,
and `ffprobe`'s own frame-by-frame keyframe flags confirm keyframes
landing at exactly frames 1, 9, 17, 25... — precisely the "every 8
frames" the `-g 8 -keyint_min 8` flags promise, checked at the frame
level rather than trusted from the flag names. The poster-frame and
ending-frame extraction commands also ran clean against the real output.

Both checks came back correct. Combined with the specificity throughout
`scrub-pipeline.md` (real luminance math for the worst-frame contrast
audit, the exact five static-hero media-query strings with an explicit
warning that CSS and JS copies must be character-for-character
identical, the gated-seek deadlock-safe pattern with its own error-path
reset), this is the most rigorously engineered, most independently
verifiable source analyzed in this project's whole run to date — a
materially different evidentiary category from every "I built X, trust
me" claim flagged in prior rounds (the ACP article, the MCP-server
article's uncited stats, "Jev"'s benchmark graph). Credited plainly as
such.

## What can't be checked from this sandbox, and why

Higgsfield and the Hostinger MCP connector are both live, paid,
connected services — no live API access to either exists in this
sandbox (same restriction already documented for Yahoo Finance, EODHD,
FMP, Hugging Face, and the Anthropic API itself elsewhere in this
project). That means the parts of the skill that depend on them
(image/video generation, cost preflighting against a live account,
the actual deploy-and-verify loop) cannot be exercised end-to-end here.
Separately unverifiable: the new video's claims about Claude's own plan
tiers (Fable requiring Max or pay-as-you-go credits on Pro; Opus
included on the $20/month Pro plan) — plausible and consistent with
this project's own session context, but not checked against a live
claude.com pricing page from this sandbox, reported as source-stated
like every other live-pricing claim flagged in earlier rounds.

## What's built from this

Rather than skip the build because the paid tools aren't reachable, the
proportionate move — same discipline as building the Rust/Go extractors
instead of cloning all of REA, or the Jev pattern router instead of
downloading a blocked model — is to build the one piece of this bundle
that is both genuinely the hardest, most load-bearing part of the whole
system (the file's own words: "Each rule either created the polish or
prevented a bug that actually shipped") and fully testable without
Higgsfield or Hostinger: the scroll-scrubbed hero engine itself. Built
as `/builds/scroll-scrub-hero/` — see that build's README for what's
real, what's substituted, and what's verified against the skill's own
self-testing checklist.
