// Next.js App Router Route Handler: POST /api/generate
//
// The one secure AI generation endpoint the architecture table in the
// source plan calls the "immediate next engineering milestone." Three
// things happen in order, each one a real gate, not a comment:
//   1. the caller's Supabase session is verified server-side
//   2. the request body is validated against validateBrief() -- never
//      trusted just because it type-checked on the client
//   3. the OpenAI key is read from the server environment only -- it
//      never reaches the browser, closing the exact gap the source
//      plan's own "production safeguards" section names ("server-side
//      API key protection").
//
// handleGenerateRequest is the testable core, split from POST the same
// way app/api/stripe/webhook/route.ts splits handleStripeWebhook from
// its own POST -- dependencies (auth verification, the AI call) are
// injected, so the real branching logic can be unit-tested with fakes
// instead of a live Supabase project and a live OpenAI key, neither of
// which exist in this sandbox.
import { validateBrief, type CampaignBrief } from "../../../lib/campaign";
import { generateHooks, AIGenerationError } from "../../../lib/ai";
import { createServerSupabaseClient, readSupabaseEnv } from "../../../lib/supabase";

export interface GenerateDeps {
  verifyUser: (token: string) => Promise<{ userId: string } | null>;
  generateHooksFn: (brief: CampaignBrief) => Promise<string[]>;
}

export interface HttpResult {
  status: number;
  body: unknown;
}

export async function handleGenerateRequest(
  authHeader: string | null,
  rawBody: unknown,
  deps: GenerateDeps
): Promise<HttpResult> {
  const token = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : null;
  if (!token) {
    return { status: 401, body: { error: "missing Authorization: Bearer <token>" } };
  }

  const user = await deps.verifyUser(token);
  if (!user) {
    return { status: 401, body: { error: "invalid or expired session" } };
  }

  const validated = validateBrief(rawBody);
  if (!validated.ok) {
    return { status: 400, body: { error: "invalid campaign brief", details: validated.errors } };
  }

  try {
    const hooks = await deps.generateHooksFn(validated.brief);
    return { status: 200, body: { hooks } };
  } catch (err) {
    if (err instanceof AIGenerationError) {
      return { status: 502, body: { error: err.message } };
    }
    throw err;
  }
}

export async function POST(req: Request): Promise<Response> {
  const supabaseEnv = readSupabaseEnv(process.env as Record<string, string | undefined>);
  const supabase = createServerSupabaseClient(supabaseEnv);
  const apiKey = process.env.OPENAI_API_KEY;

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "request body must be valid JSON" }), { status: 400 });
  }

  const result = await handleGenerateRequest(req.headers.get("authorization"), body, {
    verifyUser: async (token) => {
      const { data, error } = await supabase.auth.getUser(token);
      if (error || !data?.user) return null;
      return { userId: data.user.id };
    },
    generateHooksFn: async (brief) => {
      if (!apiKey) throw new AIGenerationError("server is not configured with OPENAI_API_KEY");
      return generateHooks({ apiKey, brief });
    },
  });

  return new Response(JSON.stringify(result.body), {
    status: result.status,
    headers: { "Content-Type": "application/json" },
  });
}
