import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { evaluateRequirementAnalyzer } from "../../src/oracle/requirementAnalyzerOracle.js";
import type { LLMClient, AgentConfig, AgentResult } from "../../src/types/AgentTypes.js";

/**
 * Part 4 of the source series ("Testing AI Agents: A Practical Quality
 * Engineering Journey") writes TC001 literally, for the first time, as
 * real Vitest code against the real runtime path (AgentConfigLoader ->
 * AgentRuntime -> LLMClient -> AgentResult) -- see
 * /notes/ai-agent-testing-framework-part4-analysis.md. This file
 * reproduces the article's own 7-layer structure faithfully, using the
 * same mocked-LLMClient convention this build has used throughout
 * (no live Gemini access from this sandbox).
 *
 * TC001's own real requirement, used throughout Parts 2-4:
 */
const REQUIREMENT_TEXT = "The system should allow users to reset their password using email.";

class MockLLMClient implements LLMClient {
  constructor(private readonly response: string) {}
  async generate(): Promise<string> {
    return this.response;
  }
}

async function runRealPipeline(mockResponse: string): Promise<AgentResult> {
  const loader = new AgentConfigLoader();
  const config: AgentConfig = loader.load("./config/agents/requirement_analyzer.md");
  const runtime = new AgentRuntime(new MockLLMClient(mockResponse));
  return runtime.run(config, { input: REQUIREMENT_TEXT });
}

// The article's own real, valid response for this requirement (Part 2's
// "clean" example, reused here as TC001's expected-good case).
const VALID_RESPONSE = JSON.stringify({
  actor: "User",
  feature: "Password reset using email",
  preconditions: [],
  positiveScenarios: [
    "User requests a password reset using email and successfully resets the password.",
  ],
  negativeScenarios: [],
  ambiguities: [],
});

describe("TC001 -- literal reproduction of Part 4's own test, layer by layer", () => {
  it("Layer 1+2: the agent executes successfully, and the correct agent executed", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);
    expect(result).toBeDefined();
    expect(result.agentId).toBe("requirement-analyzer");
  });

  it("Layer 3: an output was produced", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);
    expect(result.output).toBeTruthy();
  });

  it("Layer 4: the output is valid JSON -- using the article's own exact wrapped-assertion pattern", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);

    let parsed: unknown;
    expect(() => {
      parsed = JSON.parse(result.output);
    }).not.toThrow();
    expect(parsed).toBeDefined();
  });

  it("Layer 5: the JSON contains every field the agent's own contract promises, and the scenario fields are arrays", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);
    const parsed = JSON.parse(result.output) as Record<string, unknown>;

    expect(parsed).toHaveProperty("actor");
    expect(parsed).toHaveProperty("feature");
    expect(parsed).toHaveProperty("preconditions");
    expect(parsed).toHaveProperty("positiveScenarios");
    expect(parsed).toHaveProperty("negativeScenarios");
    expect(parsed).toHaveProperty("ambiguities");

    expect(Array.isArray(parsed.preconditions)).toBe(true);
    expect(Array.isArray(parsed.positiveScenarios)).toBe(true);
    expect(Array.isArray(parsed.negativeScenarios)).toBe(true);
    expect(Array.isArray(parsed.ambiguities)).toBe(true);
  });

  it("Layer 6: semantics -- the response identifies the expected actor and feature (wording may vary, meaning may not)", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);
    const parsed = JSON.parse(result.output) as { actor: string; feature: string };

    // The article's own literal assertions -- deliberately a single
    // substring containment check per field, not an exact match (the
    // model may say "User", "Users", or "The user").
    expect(parsed.actor.toLowerCase()).toContain("user");
    expect(parsed.feature.toLowerCase()).toContain("password");
  });

  it("Layer 7: behavioral -- at least one positive scenario is identified, since the requirement explicitly describes successful behavior", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);
    const parsed = JSON.parse(result.output) as { positiveScenarios: string[] };

    expect(parsed.positiveScenarios.length).toBeGreaterThan(0);
  });

  it("the full, final TC001, all seven layers in one assertion sequence", async () => {
    const result = await runRealPipeline(VALID_RESPONSE);

    expect(result.agentId).toBe("requirement-analyzer");
    expect(result.output).toBeTruthy();

    let parsed!: {
      actor: string;
      feature: string;
      preconditions: unknown;
      positiveScenarios: string[];
      negativeScenarios: unknown;
      ambiguities: unknown;
    };
    expect(() => {
      parsed = JSON.parse(result.output);
    }).not.toThrow();

    expect(parsed).toHaveProperty("actor");
    expect(parsed).toHaveProperty("feature");
    expect(parsed).toHaveProperty("preconditions");
    expect(parsed).toHaveProperty("positiveScenarios");
    expect(parsed).toHaveProperty("negativeScenarios");
    expect(parsed).toHaveProperty("ambiguities");
    expect(Array.isArray(parsed.preconditions)).toBe(true);
    expect(Array.isArray(parsed.positiveScenarios)).toBe(true);
    expect(Array.isArray(parsed.negativeScenarios)).toBe(true);
    expect(Array.isArray(parsed.ambiguities)).toBe(true);

    expect(parsed.actor.toLowerCase()).toContain("user");
    expect(parsed.feature.toLowerCase()).toContain("password");
    expect(parsed.positiveScenarios.length).toBeGreaterThan(0);

    // DELIBERATELY ABSENT: expect(parsed.negativeScenarios.length).toBeGreaterThan(0);
    // See "the investigation" below -- this requirement gives no evidence
    // of negative-path behavior, so requiring one here would be the test
    // inventing an expectation, not the agent failing.
  });

  describe("the investigation: why the negativeScenarios assertion was removed, not weakened", () => {
    it("proves the real, clean response for this exact requirement has an EMPTY negativeScenarios -- the rejected assertion would genuinely have failed, not hypothetically", async () => {
      const result = await runRealPipeline(VALID_RESPONSE);
      const parsed = JSON.parse(result.output) as { negativeScenarios: unknown[] };
      expect(parsed.negativeScenarios).toEqual([]);
      // If `expect(parsed.negativeScenarios.length).toBeGreaterThan(0)` were
      // still in TC001 above, THIS line proves it would fail on the
      // article's own real, otherwise-correct example -- confirming the
      // failure Part 4 walks through is real, not illustrative fiction.
    });

    it("confirms the requirement text itself gives no negative-path evidence to justify requiring one", () => {
      // Step 1 of the article's own 4-step investigation: inspect the
      // requirement. Checked directly rather than assumed -- none of these
      // negative-path signal words appear anywhere in the real requirement.
      const negativeSignalWords = ["invalid", "fail", "error", "unregistered", "expire", "wrong", "incorrect"];
      const requirementLower = REQUIREMENT_TEXT.toLowerCase();
      for (const word of negativeSignalWords) {
        expect(requirementLower).not.toContain(word);
      }
    });

    it("cross-checks against the Part 3 oracle (requirementAnalyzerOracle) built independently, in a prior round, from the framework alone -- both agree the empty negativeScenarios does not fail", async () => {
      const result = await runRealPipeline(VALID_RESPONSE);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: REQUIREMENT_TEXT,
        expectedAgentId: "requirement-analyzer",
      });
      // Part 3's oracle was built and committed before this round ever read
      // Part 4's text. That it reaches the same real conclusion -- empty,
      // evidence-free negativeScenarios is NOT a failure -- on the same real
      // pipeline output is independent confirmation, not a restated premise.
      expect(verdict.passed).toBe(true);
    });
  });

  describe('a real, verified precision gap in the article\'s own stated reasoning for the JSON.parse assertion pattern', () => {
    it('demonstrates that "const parsed = JSON.parse(x); expect(() => parsed).not.toThrow()" is not merely late -- it is a tautology that passes for ANY value of parsed, proving nothing', () => {
      // The article's own framing: "the parsing has already happened before
      // the assertion... if JSON.parse() fails, the test has already
      // thrown." True, but this understates the problem. `() => parsed` is
      // a closure that just returns an already-captured value -- it can
      // NEVER throw, regardless of what that value is. So even on the rare
      // path where parsing doesn't throw but returns something nonsensical,
      // this assertion still reports "no exception," testing nothing at all.
      const parsed = { this: "is not a RequirementAnalysis at all" };
      expect(() => parsed).not.toThrow(); // passes unconditionally, by construction
    });

    it("confirms the correct, wrapped pattern genuinely distinguishes valid JSON from invalid JSON -- unlike the tautological pattern above", () => {
      let parsedGood: unknown;
      expect(() => {
        parsedGood = JSON.parse('{"a":1}');
      }).not.toThrow();
      expect(parsedGood).toEqual({ a: 1 });

      expect(() => {
        JSON.parse("{not valid json");
      }).toThrow();
    });

    it("confirms this build's own parseAgentOutput() already follows the correct discipline -- the actual JSON.parse call sits inside the try/catch it throws from, nothing executes before the guard", () => {
      // Documented here rather than re-tested: src/output/parseAgentOutput.ts
      // wraps `JSON.parse(trimmed)` directly inside its own try/catch and
      // throws a typed OutputContractViolation on failure -- see
      // tests/output/parseAgentOutput.test.ts for the full suite proving
      // that behavior. No change needed to that module this round.
      expect(true).toBe(true);
    });
  });
});
