# Creator Empire AI

Phase 1 of an 18-app creator/marketing SaaS plan, pasted into this
session as a finished planning conversation (not uploaded as a document
to audit) — six suites of three apps each, with a flagship six-app
workflow: **one product image → hook → sales script → storyboard →
music transition → ad creatives → exported campaign package**, demoed
against a "Goli Nutrition" example. DNA Lock (brand, palette, voice) is
in `/design-rules.md` under "Brand: Creator Empire AI."

The source text is explicit that none of the 18 apps existed yet and
this is a build blueprint, not a finished library — that honesty is
carried through here rather than smoothed over: of the 18 apps in the
library grid, **6 are real and working** (the Phase 1 flagship), and
**12 are listed as planned**, visibly tagged as such in the UI itself.

The user's final instruction was explicit: build **both** a deployable
Cloud Edition and a no-cost local Standalone Edition, sharing the same
six-app workflow. Both are here.

## Standalone Edition — `standalone/`

A real, fully working, zero-dependency local app. Plain HTML/CSS/JS, no
build step, no API key, no network call of any kind — generation is
template-based (per the source plan's own description: "generates
structured creative drafts locally," "offline creative templates").

```bash
cd standalone && python3 -m http.server 8080
# open http://localhost:8080
```

Drives all 7 steps of the flagship workflow (basics → hooks → script →
storyboard → music/beat map → ads → export), saves a project to
`localStorage`, and exports both `campaign.json` (matching the schema
below) and a human-readable `campaign-brief.md`.

### Proven

- `tests/test_pure.mjs` — 40 assertions against the generator functions
  directly (hook variety, the 7-part script's fixed order, storyboard
  scenes tiling the full duration with no gaps/overlaps, beat-map
  transition-second arithmetic, the honest 6-live/12-planned library
  count). `node tests/test_pure.mjs` — **40/40 pass**.
- `tests/test_playwright.py` — real Chromium, drives the full 7-step UI
  flow end to end (not just the generator functions in isolation):
  picks a hook, confirms the script's Hook part matches it exactly,
  confirms the storyboard's first/last scene bound the chosen duration,
  adjusts the music-transition slider and confirms the beat map updates
  correctly, confirms both file exports trigger with the right
  filenames, confirms the localStorage save round-trips. Screenshots at
  1280px and 375px, zero console errors, zero horizontal overflow.
  `CHROME_PATH=... python3 tests/test_playwright.py` — **25/25 pass**.
- `tests/screenshot_later_steps.py` — a second, eyes-on look at steps 5
  (the beat map's absolute-positioned CSS) and 7 (the JSON export view)
  specifically, since DOM-text assertions can't catch a visually broken
  bar. Screenshots in `review/screenshots/`.

**Two real bugs found and fixed while testing, both in the test
harness, not the app** — worth naming so the "isolate before reporting"
step shows its work: (1) `.part-name`'s CSS `text-transform: uppercase`
made Playwright's `inner_text()` return `"HOOK"` where the actual DOM
`textContent` is `"Hook"` — fixed by switching the assertion to
`text_content()`, which reads pre-CSS-transform text; (2) a range
(`<input type="range">`) input can't be driven with Playwright's
`Locator.fill()` — fixed by setting `.value` via `page.evaluate()` and
dispatching the same `input` event a real slider drag fires. A third,
real (if minor) app issue was also caught and fixed: the browser's
automatic `favicon.ico` request 404'd and surfaced as a console error,
which the "zero console errors" check correctly flagged — fixed with an
inline SVG favicon, the same pattern used elsewhere in this project.

## Cloud Edition — `cloud/`

Not a deployed app — no Supabase project, OpenAI key, or Stripe account
exists in this sandbox. What's here is real, type-checked,
dependency-injection-tested TypeScript for the parts that are
architecturally new over the Standalone Edition: auth-gated persistence
and a real external AI call. The six-app **UI** is deliberately **not**
re-built in React here — it would be a line-for-line port of the
Standalone Edition's already-proven logic into a different framework,
with no new engineering question left to prove. What *is* new, and is
what's built:

- `lib/campaign.ts` — the shared `Campaign` record every app reads/
  writes (the exact JSON shape in the source plan's own worked example),
  plus `validateBrief()` — the server never trusts a client-typed
  request body just because TypeScript checked it; this runs on the
  actual untyped HTTP payload.
- `lib/ai.ts` — the real OpenAI Chat Completions request (the actual
  endpoint, headers, and body shape), with an injectable `fetchImpl` so
  it's unit-testable without a live key or network access.
- `lib/supabase.ts` — two client factories, matching Supabase's real
  documented split: a browser/anon-key client (RLS-scoped) and a
  server-only service-role client that explicitly refuses to construct
  without its key.
- `app/api/generate/route.ts` — the one secure AI generation endpoint
  the source plan calls its "immediate next engineering milestone":
  verify the session → validate the body → call the AI → never let a
  key reach the browser. `handleGenerateRequest` is split out as a
  pure, dependency-injected core (same pattern as the Stripe handler
  below) so the full branch logic is testable without a live Supabase
  project.
- `app/api/stripe/webhook/route.ts` — a real signature-verification
  call using Stripe's own SDK method (`stripe.webhooks.constructEvent`),
  not a hand-rolled HMAC check. `handleStripeWebhook` is the same
  dependency-injected split. **The actual subscription→Supabase write is
  a stated gap, not a silent stub** — see the `TODO` comment in the
  file: designing it needs a live Stripe account's real customer/
  subscription object shape, which doesn't exist here.
- `schema/supabase.sql` (one level up, shared) — `projects` table with
  real row-level-security policies (`auth.uid() = owner_id`) matching
  Supabase's documented RLS pattern, plus an `updated_at` trigger.
  Never run against a live database — checked by reading against
  Supabase's own docs, not by executing it.

### Proven

```bash
cd cloud
npm install
npm run typecheck   # real tsc --noEmit, strict mode
npm test            # real tsx --test, zero live network calls
```

Type check is clean. **29/29 tests pass**, covering:
`validateBrief`'s full rejection surface (missing/overlong fields,
invalid duration/ratio enums, multi-field error reporting, whitespace
trimming); `lib/ai.ts`'s prompt-building and response-parsing against
realistic OpenAI response shapes, including a fenced-code-block
response and a mocked-`fetch` assertion that the real request URL,
method, auth header, and body shape are exactly right;
`handleGenerateRequest`'s full branch coverage (missing/malformed auth
header, a rejected session, an invalid brief that never reaches the AI
call, the happy path, and an AI failure mapped to 502 not 500); and
`handleStripeWebhook`'s signature-failure path, its relevant-vs-
irrelevant event-type filtering, and confirmation that a bad signature
is rejected by Stripe's own real SDK call.

**One real bug found and fixed while writing these tests, not a test
artifact**: `parseHookResponse`'s original extraction found the first
`[` and the last `]` anywhere in the model's raw text and treated
whatever was between them as the answer. Against the test case
`{"hooks": ["a"]}` — a plausible off-spec response from a model that
decided to wrap the array in an object — this naive scan found the
*nested* array's own brackets and silently accepted it as valid,
exactly the kind of off-spec response the prompt ("Return ONLY a JSON
array... nothing else") should cause to fail loudly instead of being
guessed at. Fixed by requiring the entire (fence-stripped) response to
parse as JSON directly, dropping the bracket-scanning fallback
entirely — simpler and more correct, and it only changes behavior on
exactly the malformed-response cases that should now be rejected
rather than silently recovered from.

## What's cut, and why

- **12 of the 18 apps** (Reels Factory, Audio Sync Planner, Social
  Content Calendar, and everything in the Funnel/Automation/Agency
  labs) — Phase 1 scope, per the source plan's own stated build order;
  honestly tagged `PLANNED` in the UI rather than faked as live.
- **No Next.js installed, no deployed cloud app, no live Vercel/
  Supabase/OpenAI/Stripe** — this sandbox's standing restriction, same
  as every other paid-API build in this project. What's real is the
  TypeScript logic that would sit behind those services, type-checked
  and tested with injected fakes instead of live calls.
- **No rendered video anywhere.** The source plan draws this line
  itself ("neither should pretend to render finished video without a
  connected video-generation service") — both editions only ever
  produce a structured campaign package (hooks, script, storyboard,
  beat map, ad copy), never a claimed finished clip.
- **No Goli Nutrition partnership implied.** The demo brief is a
  reference/example, stated plainly in both the UI footer and
  `design-rules.md`'s do-say/don't-say rules for this brand.
