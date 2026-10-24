import { test } from "node:test";
import assert from "node:assert/strict";
import { handleGenerateRequest } from "../app/api/generate/route";
import { AIGenerationError } from "../lib/ai";

const validBody = {
  brand: "Goli Nutrition",
  product: "ACV gummies",
  audience: "busy parents",
  benefit: "benefit",
  duration_seconds: 40,
  aspect_ratio: "9:16",
};

test("handleGenerateRequest returns 401 with no Authorization header", async () => {
  const result = await handleGenerateRequest(null, validBody, {
    verifyUser: async () => { throw new Error("should never be called"); },
    generateHooksFn: async () => { throw new Error("should never be called"); },
  });
  assert.equal(result.status, 401);
});

test("handleGenerateRequest returns 401 when the Authorization header isn't Bearer-shaped", async () => {
  const result = await handleGenerateRequest("Basic abc123", validBody, {
    verifyUser: async () => { throw new Error("should never be called"); },
    generateHooksFn: async () => { throw new Error("should never be called"); },
  });
  assert.equal(result.status, 401);
});

test("handleGenerateRequest returns 401 when verifyUser rejects the token", async () => {
  const result = await handleGenerateRequest("Bearer bad-token", validBody, {
    verifyUser: async () => null,
    generateHooksFn: async () => { throw new Error("should never be called"); },
  });
  assert.equal(result.status, 401);
});

test("handleGenerateRequest returns 400 on an invalid brief, without ever calling the AI", async () => {
  let aiCalled = false;
  const result = await handleGenerateRequest("Bearer good-token", { brand: "" }, {
    verifyUser: async () => ({ userId: "user-1" }),
    generateHooksFn: async () => { aiCalled = true; return []; },
  });
  assert.equal(result.status, 400);
  assert.equal(aiCalled, false);
});

test("handleGenerateRequest returns 200 with hooks on the full happy path", async () => {
  const result = await handleGenerateRequest("Bearer good-token", validBody, {
    verifyUser: async (token) => (token === "good-token" ? { userId: "user-1" } : null),
    generateHooksFn: async (brief) => {
      assert.equal(brief.brand, "Goli Nutrition");
      return ["hook a", "hook b"];
    },
  });
  assert.equal(result.status, 200);
  assert.deepEqual((result.body as { hooks: string[] }).hooks, ["hook a", "hook b"]);
});

test("handleGenerateRequest returns 502 when AI generation fails, not a 500", async () => {
  const result = await handleGenerateRequest("Bearer good-token", validBody, {
    verifyUser: async () => ({ userId: "user-1" }),
    generateHooksFn: async () => { throw new AIGenerationError("OpenAI API returned 429"); },
  });
  assert.equal(result.status, 502);
});
