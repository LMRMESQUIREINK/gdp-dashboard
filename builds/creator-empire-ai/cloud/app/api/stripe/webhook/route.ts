// Next.js App Router Route Handler: POST /api/stripe/webhook
//
// Scaffold only -- never exercised against a live Stripe account or a
// real webhook delivery from this sandbox. The actual signature
// verification + event routing logic lives in
// lib/stripeWebhookHandler.ts -- this file only ever exports POST, per
// Next's route-type checker (see that file's own comment for why).
import Stripe from "stripe";
import { handleStripeWebhook } from "../../../../lib/stripeWebhookHandler";

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
