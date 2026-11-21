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
// The actual branching logic lives in lib/generateHandler.ts -- this
// file is a thin wrapper that only ever exports POST, which is what
// Next's route-type checker requires (see that file's own comment for
// why handleGenerateRequest can't live here directly).
import { handleGenerateRequest } from "../../../lib/generateHandler";
import { generateHooks, AIGenerationError } from "../../../lib/ai";
import { createServerSupabaseClient, readSupabaseEnv } from "../../../lib/supabase";

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
