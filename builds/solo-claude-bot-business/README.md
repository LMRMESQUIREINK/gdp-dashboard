# Solo Claude Bot Business

A real, working, zero-dependency local app for a one-operator
custom-AI-agent business: price the offer, track the client pipeline,
and run the build checklist. Built from the audited content of the
`ruthless-gate` round at `/builds/solo-bot-business-gate/`
(`/notes/solo-bot-business-gate-analysis.md`) — not from its
unverified claims. DNA Lock: `/design-rules.md` → "Brand: Solo Claude
Bot Business."

**Every mention of "Grok"/"GrokBot" eliminated from the app itself**,
per the user's explicit instruction. (One developer-facing provenance
comment in `assets/app.js` names the real source title factually —
this project's standing documentation convention requires every build
to cite what it was actually built from; that's internal code
commentary, not the app's own user-facing branding, which is clean.)

Open `index.html` in a browser (served locally, not `file://`), or run
the tests below.

## Why these three panels, not a platform clone

The source transcript's actual offer involves real third-party
services (a cloud compute provider, an agent-email provider, an
agent-phone provider, a connector platform) this sandbox has no
credentials or network access to reach — same restriction as every
other build in this project. Rather than fake a live multi-tenant bot
platform, this build operationalizes the three parts of the pitch that
are genuinely real, credited, and fully testable without any external
API:

1. **Offer Calculator** — the pricing math, computed honestly.
2. **Client Pipeline** — the audit's own credited client-acquisition
   sequence (call 50 people you know, free first build for a case
   study, trade for 3 warm intros), made trackable.
3. **Build Checklist** — the real Research → Design → Build process,
   with the four generalized stack categories (compute/email/phone/
   connectors) left for the user to name their own real tool per
   category — not hardcoded to the source's own named vendors, since
   the audit found "Agent Mail"/"Agent Phone" don't exactly match any
   locatable real product under those literal names.

## The one bug this build deliberately does not repeat

The audit's own `deepest-03` finding: the source's "$3,000/month is
like $12/hour" line is exact only under a hidden, never-stated
250-hours-a-month assumption. This app's hourly-rate figure is always
computed from a **visible, editable** hours-per-month input, labeled
directly under the number (`#result-hourly-basis`) — change the
assumption and the rate updates in front of you, instead of a round
number appearing from nowhere.

## Proven

```bash
node test_pure.js       # pure logic, no DOM
python3 test_playwright.py   # real Chromium render, desktop + mobile
```

**21/21 pure-logic assertions, 22/22 real-browser assertions**, all
passing, including:

- `computeOffer` reproduces the source's own real numbers exactly when
  fed the source's own real inputs: $200/mo baseline × 15 = the
  source's actual $3,000/mo retainer; the real 25000/3000 upfront
  ratio applied to that gives exactly $25,000, the source's actual
  upfront figure; and the $12.00/hr rate *only* appears when 250 hours/
  month is explicitly entered — never as a silent default (the default
  shipped in the app is a standard 173.33hr full-time month instead).
- A real end-to-end client-pipeline flow in a real browser: add a
  contact, change status to "case-study," log referrals, confirm the
  progress counters update correctly (1 case study → a referral goal
  of 3), confirm a blank-name submission is rejected with a visible
  error rather than silently ignored or silently added, confirm
  removing a contact updates the list.
- The build checklist's four stack categories start with **zero**
  vendor names pre-filled (confirmed on the real rendered page, not
  just read from the source), and the stack step only counts as
  complete once all four categories have both a tool name and
  "docs read" checked — partial completion doesn't count, matching the
  source's own stated discipline ("read the docs and the API
  references... those are the two things I do with every feature").
- Full state persistence verified with a **real page reload** in the
  browser (not just a localStorage unit test): offer inputs and
  checklist state both survive.
- Zero `"grok"` (case-insensitive) anywhere in the rendered page text
  — checked directly against the live DOM, not just the source files.
- Zero console errors and zero horizontal overflow at 375px.
- **One real bug found and fixed during screenshot verification**: the
  pricing-multiplier range slider rendered with the browser's native
  blue thumb/track, clashing with the locked teal palette — caught on
  the first screenshot pass, fixed with `accent-color: var(--brand)`,
  confirmed clean on the second pass (the project's own minimum-two-
  passes screenshot rule).

## What's not built here

- No live integration with any real compute/email/phone/connector
  provider — this sandbox has no credentials or network access to any
  of them, same restriction as every other build in this project.
- No multi-tenant hosting, no per-client data isolation — this is a
  single operator's own local planning tool, not a platform for
  managing multiple live client deployments.
- No revenue tracking beyond the offer calculator's projected figures
  — this app doesn't claim or track real income, consistent with the
  audit's own finding that the source's "$1M+" headline was never
  substantiated anywhere in its own material.
