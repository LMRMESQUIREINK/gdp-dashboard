# Deep analysis: "Build a WordPress website using Claude AI — Free Prompt Pack"

Source: `Claude_WordPress_Prompt_Pack2.pdf`, Metics Media, 9 pages,
sha256 `df6c15668d6b0...`. A newly-available skill, `ruthless-gate`
("Audit a supplied source... at four escalating depths and build a
tested verdict page from it"), matched this project's own repeated
DEEP/DEEPER/DEEPEREST/DEEPEREST-EST analysis-then-build pattern exactly,
so this round ran through it rather than hand-rolling the usual
markdown write-up. The full audit — every finding with its evidence,
a locked test suite, and a real self-contained page — lives at
`/builds/wp-prompt-pack-gate/`; this file is the project-convention
summary pointer, per this project's standing practice of always writing
to `/notes/` regardless of what other artifact a round also produces.

## What this is

Ten numbered, copy-paste-ready prompts for building a small-business
WordPress site with Claude Design + Claude Code, bridged to a live
WordPress install via the NovaMira connector, built on Astra + Elementor
V4's new "atomic elements" system. Free, distributed as a lead magnet
for a video tutorial, with two paid affiliate links (Hostinger hosting,
Artlist image generation) on the last page.

## The two things worth knowing without reading the full verdict page

**A real, checkable inconsistency in the pack's own self-description.**
The cover says "9 prompts" / "Nine prompts" twice; the pack actually
delivers exactly 10 numbered prompts. Confirmed by direct count of the
table of contents, not an assumption.

**This is the same operator as last round's "10k-websites" Higgsfield
skill.** Both carry `meticsmedia.com` affiliate links to Hostinger, each
with its own campaign-tracking URL suffix (`-HZU` here, `-ESVT` there) —
one operator running at least two parallel "build a $X website with
Claude" funnels, a connection neither artifact states on its own and
that's only visible from reading this project's last two rounds
together.

## What's genuinely well-reasoned

The pack's build rules are specific and internally disciplined: CSS
custom properties required for every colour/font/spacing value (no
hard-coding), a stated class-naming convention, an explicit ban on
styling part of a heading differently (a real, common AI-generated-page
tell), and a copy-voice rule banning em dashes and named stock AI
phrases. That last rule is independently, mechanically enforceable —
this project's own `/builds/humanizer/` already tracks every term it
bans, confirmed by actually running it against the pack's own text.

## What doesn't hold up, or isn't disclosed

The pack mandates Elementor V4's "atomic elements" exclusively (real
and current, web-verified) without disclosing that the same system is,
per independent review, still in Beta as of its own cited 2026
changelog dates — a small-business reader has no way to know from this
document alone that they're being steered onto an actively-maturing
page-builder. Separately, the NovaMira connector — load-bearing
infrastructure every Claude Code prompt depends on — is named exactly
once, in small print, with zero setup instructions anywhere in the
pack's 9 pages, the same "referenced but never actually supplied"
pattern this project has repeatedly found in other uploaded bundles.

## What's built from this

No separate code build this round — the verdict page itself (built per
the `ruthless-gate` skill's own required four-file structure:
`index.html`, `data.js`, `test.js`, `README.md`) is the deliverable,
real and tested: 104/104 assertions pass, including WCAG contrast
computed (not eyeballed) for the required METAL HEAVY palette, the
pack's own 9-vs-10 and em-dash counts independently recomputed from the
raw extracted text rather than trusted from the ledger's own claim, and
a real Chromium render at desktop and mobile widths. One genuine layout
bug was found and fixed during that verification (a `<table>` without
`table-layout:fixed` pushed real overflow at 375px that
`overflow-x:clip` was hiding from the obvious check) — full story in
`/builds/wp-prompt-pack-gate/README.md`.
