import { test } from "node:test";
import assert from "node:assert/strict";
import { buildHookPrompt, parseHookResponse, generateHooks, AIGenerationError } from "../lib/ai";
import type { CampaignBrief } from "../lib/campaign";

const brief: CampaignBrief = {
  brand: "Goli Nutrition",
  product: "ACV gummies",
  audience: "busy parents",
  benefit: "a gut-health habit that actually tastes good",
  duration_seconds: 40,
  aspect_ratio: "9:16",
};

test("buildHookPrompt includes every brief field", () => {
  const prompt = buildHookPrompt(brief);
  assert.match(prompt, /Goli Nutrition/);
  assert.match(prompt, /ACV gummies/);
  assert.match(prompt, /busy parents/);
  assert.match(prompt, /gut-health habit/);
  assert.match(prompt, /JSON array/);
});

test("parseHookResponse parses a bare JSON array", () => {
  const hooks = parseHookResponse('["hook one", "hook two"]');
  assert.deepEqual(hooks, ["hook one", "hook two"]);
});

test("parseHookResponse parses JSON wrapped in a markdown code fence", () => {
  const hooks = parseHookResponse('Sure! Here you go:\n```json\n["a", "b", "c"]\n```\nHope that helps!');
  assert.deepEqual(hooks, ["a", "b", "c"]);
});

test("parseHookResponse rejects a response with no JSON array", () => {
  assert.throws(() => parseHookResponse("I cannot help with that."), AIGenerationError);
});

test("parseHookResponse rejects a non-array JSON value", () => {
  assert.throws(() => parseHookResponse('{"hooks": ["a"]}'), AIGenerationError);
});

test("parseHookResponse rejects an array of non-strings", () => {
  assert.throws(() => parseHookResponse("[1, 2, 3]"), AIGenerationError);
});

test("parseHookResponse rejects an empty array", () => {
  assert.throws(() => parseHookResponse("[]"), AIGenerationError);
});

test("generateHooks sends the real OpenAI request shape and parses a real-shaped response", async () => {
  let capturedUrl = "";
  let capturedInit: RequestInit | undefined;
  const fakeFetch = async (url: string, init?: RequestInit): Promise<Response> => {
    capturedUrl = url;
    capturedInit = init;
    const body = JSON.stringify({
      choices: [{ message: { content: '["Stop scrolling.", "What if...", "Nobody tells you this."]' } }],
    });
    return new Response(body, { status: 200 });
  };

  const hooks = await generateHooks({ apiKey: "sk-test-key", brief, fetchImpl: fakeFetch });

  assert.equal(capturedUrl, "https://api.openai.com/v1/chat/completions");
  assert.equal(capturedInit?.method, "POST");
  const headers = capturedInit?.headers as Record<string, string>;
  assert.equal(headers.Authorization, "Bearer sk-test-key");
  const sentBody = JSON.parse(capturedInit?.body as string);
  assert.equal(sentBody.model, "gpt-4o-mini");
  assert.match(sentBody.messages[0].content, /Goli Nutrition/);

  assert.deepEqual(hooks, ["Stop scrolling.", "What if...", "Nobody tells you this."]);
});

test("generateHooks throws AIGenerationError on a non-200 response, never a raw exception", async () => {
  const fakeFetch = async (): Promise<Response> => new Response("rate limited", { status: 429 });
  await assert.rejects(
    () => generateHooks({ apiKey: "sk-test", brief, fetchImpl: fakeFetch }),
    AIGenerationError
  );
});

test("generateHooks throws AIGenerationError when the API returns no message content", async () => {
  const fakeFetch = async (): Promise<Response> =>
    new Response(JSON.stringify({ choices: [] }), { status: 200 });
  await assert.rejects(
    () => generateHooks({ apiKey: "sk-test", brief, fetchImpl: fakeFetch }),
    AIGenerationError
  );
});
