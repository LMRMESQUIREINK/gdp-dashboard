// Next.js App Router Route Handler: POST /api/stripe/webhook
//
// Scaffold only -- never exercised against a live Stripe account or a
// real webhook delivery from this sandbox (no Stripe account exists
// here, same standing restriction as every live-paid-API claim in this
// project). What IS real: the signature-verification call itself,
// Stripe's actual SDK method, used the way Stripe's own docs specify --
// not a hand-rolled HMAC check that could silently drift from their
// format.
import Stripe from "stripe";

export interface StripeWebhookDeps {
  stripe: Stripe;
  webhookSecret: string;
  onSubscriptionEvent: (event: Stripe.Event) => Promise<void>;
}

/** Framework-agnostic handler body, separated from the Route Handler
 * export below so it can be unit-tested with a fake Stripe client
 * instead of a real signed payload. */
export async function handleStripeWebhook(
  rawBody: string,
  signatureHeader: string | null,
  deps: StripeWebhookDeps
): Promise<{ status: number; body: unknown }> {
  if (!signatureHeader) {
    return { status: 400, body: { error: "missing stripe-signature header" } };
  }

  let event: Stripe.Event;
  try {
    event = deps.stripe.webhooks.constructEvent(rawBody, signatureHeader, deps.webhookSecret);
  } catch (err) {
    return { status: 400, body: { error: `signature verification failed: ${(err as Error).message}` } };
  }

  const relevant = [
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
  ];
  if (relevant.includes(event.type)) {
    await deps.onSubscriptionEvent(event);
  }

  return { status: 200, body: { received: true } };
}

export async function POST(req: Request): Promise<Response> {
  const secretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secretKey || !webhookSecret) {
    return new Response(JSON.stringify({ error: "Stripe is not configured" }), { status: 500 });
  }

  const stripe = new Stripe(secretKey);
  const rawBody = await req.text();
  const signature = req.headers.get("stripe-signature");

  const result = await handleStripeWebhook(rawBody, signature, {
    stripe,
    webhookSecret,
    onSubscriptionEvent: async (event) => {
      // TODO (not implemented, not claimed): write the subscription
      // status onto the owning user's row in Supabase. Needs a real
      // Stripe customer <-> Supabase user_id mapping, which needs a
      // live Stripe account to design against -- stated as a real gap,
      // not silently stubbed out.
      void event;
    },
  });

  return new Response(JSON.stringify(result.body), { status: result.status });
}
