# Proposal: Checkout Clarity & Mobile Cleanup — Thistle & Oat

*(SYNTHETIC — demonstrates the `proposal-generator` skill end-to-end
against the synthetic notes in `example-discovery-notes.md`. No real
client, agency, or deal.)*

## Project understanding

You're seeing checkout abandonment on Thistle & Oat that you believe
traces back to shipping cost only showing up at the final step — your
instinct from watching session recordings, not something analytics has
confirmed yet. Since nearly all your traffic comes from Instagram,
that's also almost entirely a mobile problem. You want shipping shown
earlier in the flow and a cleaner mobile checkout, live before your
influencer push in 5 weeks — and you were clear this isn't a redesign
or a platform switch: a past agency turned a "small fix" into a full
rebuild, and that's exactly what this isn't.

## Scope

**In scope:**
- Add an estimated-shipping display on the product page and cart (by
  destination/region, pulling from Shopify's existing shipping rules —
  no new shipping logic built from scratch).
- Mobile checkout cleanup: simplified field layout, larger tap targets,
  and removing/collapsing steps that cause drop-off on small screens.
- Before/after instrumentation on the checkout flow (step-by-step
  funnel tracking), so the shipping-cost theory gets tested against
  real data instead of staying an instinct — and so the influencer
  push has a real baseline to measure against.
- One round of mobile QA across the device/browser mix your Shopify
  analytics shows your actual traffic using.

**Out of scope** (confirmed with you, not assumed): any change to
desktop checkout beyond what the mobile fix naturally improves, store
branding or visual redesign, migration off Shopify, and any new
product/catalog work.

## Timeline

Five weeks to your influencer push — built with a buffer, not cutting it
to the wire:

- **Week 1**: Funnel instrumentation live; shipping-display build
  starts.
- **Week 2**: Shipping display done on product page + cart; mobile
  checkout cleanup starts.
- **Week 3**: Mobile checkout build complete; QA across your real
  device/browser mix.
- **Week 4**: Fixes from QA; funnel data reviewed against the
  shipping-cost theory.
- **Week 5 (buffer)**: Held open for fixes, not new work — live with a
  full week to spare before the push, not the day before it.

## Pricing

*(In a real engagement, this section is built from this agency's own
established day rate or service menu per the skill's own rule — none
exists in this demonstration, so the three tiers below are anchored to
the one real number the client gave, "somewhere under $5K," rather than
an invented rate. Flagged here rather than silently presented as if a
real rate was used.)*

| Tier | Price | What's different |
|---|---|---|
| **Essentials** | $2,800 | Shipping display + funnel instrumentation only. Mobile checkout cleanup limited to the two highest-drop-off steps your funnel data flags, not a full pass. |
| **Standard** | $4,200 | Everything in Essentials, plus the full mobile checkout cleanup and the full QA pass across your real device/browser mix. |
| **Standard + Monitoring** | $4,800 | Everything in Standard, plus two weeks of post-launch funnel monitoring after the influencer push, with one round of tuning if the data shows a specific step still underperforming. |

## Terms

- 50% to start, 50% on delivery (before the Week 5 buffer, not after).
- **If it takes longer than expected** (your own question, answered
  directly): scope stays fixed at what's listed above for the quoted
  price — a delay inside this scope doesn't cost more. A change *to*
  the scope (a new request beyond what's listed) is quoted separately
  before any work starts on it, never added silently.
- Shipping-rule changes inside Shopify's own settings stay yours to
  make; this proposal covers the display/checkout work, not your
  shipping-rate strategy itself.
