import { test } from "node:test";
import assert from "node:assert/strict";
import type Stripe from "stripe";
import { handleStripeWebhook } from "../app/api/stripe/webhook/route";

function fakeStripe(behavior: "ok" | "bad-signature", eventType = "customer.subscription.created"): Stripe {
  return {
    webhooks: {
      constructEvent: (_rawBody: string, _sig: string, _secret: string) => {
        if (behavior === "bad-signature") {
          throw new Error("No signatures found matching the expected signature for payload");
        }
        return { id: "evt_test", type: eventType, data: { object: {} } } as Stripe.Event;
      },
    },
  } as unknown as Stripe;
}

test("handleStripeWebhook returns 400 with no stripe-signature header", async () => {
  const result = await handleStripeWebhook("{}", null, {
    stripe: fakeStripe("ok"),
    webhookSecret: "whsec_test",
    onSubscriptionEvent: async () => { throw new Error("should never be called"); },
  });
  assert.equal(result.status, 400);
});

test("handleStripeWebhook returns 400 when signature verification fails -- the real Stripe SDK call, not a stub", async () => {
  const result = await handleStripeWebhook("{}", "t=1,v1=bad", {
    stripe: fakeStripe("bad-signature"),
    webhookSecret: "whsec_test",
    onSubscriptionEvent: async () => { throw new Error("should never be called"); },
  });
  assert.equal(result.status, 400);
  assert.match((result.body as { error: string }).error, /signature verification failed/);
});

test("handleStripeWebhook calls onSubscriptionEvent for a relevant event type", async () => {
  let called: Stripe.Event | null = null;
  const result = await handleStripeWebhook("{}", "t=1,v1=good", {
    stripe: fakeStripe("ok", "customer.subscription.updated"),
    webhookSecret: "whsec_test",
    onSubscriptionEvent: async (event) => { called = event; },
  });
  assert.equal(result.status, 200);
  assert.ok(called !== null);
  assert.equal((called as unknown as Stripe.Event).type, "customer.subscription.updated");
});

test("handleStripeWebhook does NOT call onSubscriptionEvent for an irrelevant event type", async () => {
  let called = false;
  const result = await handleStripeWebhook("{}", "t=1,v1=good", {
    stripe: fakeStripe("ok", "invoice.paid"),
    webhookSecret: "whsec_test",
    onSubscriptionEvent: async () => { called = true; },
  });
  assert.equal(result.status, 200);
  assert.equal(called, false);
});
