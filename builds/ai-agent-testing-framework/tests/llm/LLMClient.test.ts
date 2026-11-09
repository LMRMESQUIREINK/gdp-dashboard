import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { LLMClient } from "../../src/llm/LLMClient.js";

describe("LLMClient", () => {
  const originalKey = process.env.GEMINI_API_KEY;

  afterEach(() => {
    if (originalKey === undefined) {
      delete process.env.GEMINI_API_KEY;
    } else {
      process.env.GEMINI_API_KEY = originalKey;
    }
  });

  it("fails fast at construction time when GEMINI_API_KEY is missing, before any network call is attempted", () => {
    delete process.env.GEMINI_API_KEY;
    expect(() => new LLMClient()).toThrow("GEMINI_API_KEY environment variable is not configured.");
  });

  it("constructs successfully once a key is present (no live network call made by the constructor itself)", () => {
    process.env.GEMINI_API_KEY = "test-key-not-a-real-credential";
    expect(() => new LLMClient()).not.toThrow();
  });
});
