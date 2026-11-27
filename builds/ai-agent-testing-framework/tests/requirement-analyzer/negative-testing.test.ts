import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { evaluateSafeFailure } from "../../src/oracle/safeFailureOracle.js";
import type { LLMClient, AgentConfig, AgentResult } from "../../src/types/AgentTypes.js";

/**
 * Part 5 of the source series ("Negative Testing: What Happens When the
 * Input Is Bad?") -- TC002 (empty input), TC003 (wrong-domain input),
 * TC004 (nonsense input). See
 * /notes/ai-agent-testing-framework-part5-analysis.md.
 *
 * Each TC below uses the article's own real, actually-quoted agent
 * output for that exact input (not a constructed example), run through
 * the real pipeline via a mocked LLMClient -- same standing
 * no-live-API-access convention as every build here.
 */

class MockLLMClient implements LLMClient {
  constructor(private readonly response: string) {}
  async generate(): Promise<string> {
    return this.response;
  }
}

async function runRealPipeline(input: string, mockResponse: string): Promise<AgentResult> {
  const loader = new AgentConfigLoader();
  const config: AgentConfig = loader.load("./config/agents/requirement_analyzer.md");
  const runtime = new AgentRuntime(new MockLLMClient(mockResponse));
  return runtime.run(config, { input });
}

describe("TC002 -- empty input: can the agent recognize missing evidence?", () => {
  const INPUT = "";
  // The article's own real, actually-quoted output for this exact input.
  const REAL_SAFE_RESPONSE = JSON.stringify({
    actor: "Unknown",
    feature: "Unknown",
    preconditions: [],
    positiveScenarios: [],
    negativeScenarios: [],
    ambiguities: ["No requirement text was provided for analysis."],
  });

  it("literal reproduction of the article's own assertion pattern", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const parsed = JSON.parse(result.output);
    const serializedOutput = JSON.stringify(parsed).toLowerCase();

    expect(serializedOutput).toMatch(
      /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/
    );
    expect(serializedOutput).not.toContain("password reset");
    expect(serializedOutput).not.toContain("login");
  });

  it("the generalized safeFailureOracle (built on Part 3's QualityBoundary) reaches the same verdict: passes", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["password reset", "login", "user account"],
    });
    expect(verdict.passed).toBe(true);
  });

  it("DISCRIMINATION CHECK: a planted hallucinated response (inventing an actor/feature from nothing) correctly fails, proving the oracle isn't a rubber stamp", async () => {
    const HALLUCINATED_RESPONSE = JSON.stringify({
      actor: "User",
      feature: "Password reset",
      preconditions: ["User has an account"],
      positiveScenarios: ["User resets their password."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, HALLUCINATED_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["password reset", "login", "user account"],
    });
    expect(verdict.passed).toBe(false);
    // Fails for BOTH reasons at once: no safe-failure signal anywhere,
    // AND it invented exactly the forbidden concept.
    expect(verdict.findings.map((f) => f.kind).sort()).toEqual(
      ["forbidden-violated", "required-failed"].sort()
    );
  });
});

describe("TC003 -- wrong domain: can the agent stay within its responsibility?", () => {
  const INPUT = "Bananas are yellow and elephants are large.";
  const REAL_SAFE_RESPONSE = JSON.stringify({
    actor: "Unknown",
    feature: "Unknown",
    preconditions: [],
    positiveScenarios: [],
    negativeScenarios: [],
    ambiguities: [
      "The input statement does not describe a software requirement, functionality, or system behavior.",
    ],
  });

  it("literal reproduction of the article's own assertion pattern", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const parsed = JSON.parse(result.output);
    const serializedOutput = JSON.stringify(parsed).toLowerCase();

    expect(serializedOutput).toMatch(
      /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/
    );
    expect(serializedOutput).not.toContain("banana management");
    expect(serializedOutput).not.toContain("password reset");
  });

  it("the generalized safeFailureOracle reaches the same verdict: passes", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["banana management", "elephant care", "password reset"],
    });
    expect(verdict.passed).toBe(true);
  });

  it("DISCRIMINATION CHECK: a planted response that forces the off-domain input into the agent's domain correctly fails", async () => {
    // Capability is not responsibility -- the article's own named concept.
    // A capable-but-wrong agent might "helpfully" invent a feature out of
    // the off-domain statement instead of recognizing the scope violation.
    const HALLUCINATED_RESPONSE = JSON.stringify({
      actor: "Zookeeper",
      feature: "Banana management",
      preconditions: [],
      positiveScenarios: ["Zookeeper distributes bananas to elephants."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, HALLUCINATED_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["banana management", "elephant care", "password reset"],
    });
    expect(verdict.passed).toBe(false);
    expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
    expect(verdict.findings.some((f) => f.kind === "required-failed")).toBe(true);
  });
});

describe("TC004 -- nonsense input: can the agent distinguish text from meaningful input?", () => {
  const INPUT = "asdfghjkl 123 xyz qwerty";
  const REAL_SAFE_RESPONSE = JSON.stringify({
    actor: "Unknown",
    feature: "Unknown",
    preconditions: [],
    positiveScenarios: [],
    negativeScenarios: [],
    ambiguities: [
      "The input string 'asdfghjkl 123 xyz qwerty' contains no meaningful text or business context to identify an actor, feature, preconditions, or scenarios.",
    ],
  });

  it("literal reproduction of the article's own assertion pattern", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const parsed = JSON.parse(result.output);
    const serializedOutput = JSON.stringify(parsed).toLowerCase();

    expect(serializedOutput).toMatch(
      /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/
    );
    expect(serializedOutput).not.toContain("password reset");
    expect(serializedOutput).not.toContain("login");
  });

  it("the generalized safeFailureOracle reaches the same verdict: passes", async () => {
    const result = await runRealPipeline(INPUT, REAL_SAFE_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["password reset", "login", "user account"],
    });
    expect(verdict.passed).toBe(true);
  });

  it("DISCRIMINATION CHECK: a planted response that manufactures meaning from pure gibberish correctly fails", async () => {
    const HALLUCINATED_RESPONSE = JSON.stringify({
      actor: "User",
      feature: "Login with username qwerty",
      preconditions: [],
      positiveScenarios: ["User logs in with the username asdfghjkl."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, HALLUCINATED_RESPONSE);
    const verdict = evaluateSafeFailure({
      result,
      forbiddenTerms: ["password reset", "login", "user account"],
    });
    expect(verdict.passed).toBe(false);
    expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
  });
});

describe("safeFailureOracle: a real edge case the article's own literal pattern doesn't cover", () => {
  it("still produces a meaningful (failing, for the right reason) verdict when the output isn't valid JSON at all, instead of throwing before the check can run", async () => {
    // The article's own literal pattern does `JSON.parse(result.output)`
    // directly inside the test body -- if the LLM returned something that
    // isn't valid JSON (a real possibility this build's own
    // parseAgentOutput.ts already guards against elsewhere), that line
    // throws an uncaught SyntaxError before any safe-failure assertion
    // ever runs, same class of problem the TC001 round's JSON.parse
    // tautology finding was about. safeFailureOracle's serialize() falls
    // back to the raw string specifically so this check still runs.
    const result: AgentResult = {
      agentId: "requirement-analyzer",
      agentVersion: "1.0.0",
      output: "Sorry, I can't help with that.",
    };
    const verdict = evaluateSafeFailure({ result, forbiddenTerms: ["password reset"] });
    // No "unknown/missing/..." signal and no forbidden term either -- this
    // is a different, third failure mode (malformed output entirely),
    // correctly reported as a Required failure, not a crash.
    expect(verdict.passed).toBe(false);
    expect(verdict.findings).toEqual([
      {
        name: "Serialized output contains a recognizable safe-failure signal (unknown/missing/not specified/not provided/insufficient/empty/ambiguous)",
        kind: "required-failed",
      },
    ]);
  });
});
