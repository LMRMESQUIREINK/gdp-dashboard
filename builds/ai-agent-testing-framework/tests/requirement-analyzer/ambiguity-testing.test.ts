import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { checkGrounding } from "../../src/grounding/checkGrounding.js";
import { evaluateRequirementAnalyzer } from "../../src/oracle/requirementAnalyzerOracle.js";
import type { LLMClient, AgentConfig, AgentResult } from "../../src/types/AgentTypes.js";

/**
 * Part 6 of the source series ("Testing Ambiguity in AI Agents: Can the
 * Agent Recognize What the Requirement Doesn't Say?") -- TC005,
 * subjective ambiguity. See
 * /notes/ai-agent-testing-framework-part6-analysis.md.
 *
 * The article's own central move: a naive forbidden-term check
 * (`expect(output).not.toContain("otp")`) failed against the agent's own
 * real, CORRECT output, because the agent mentioned "OTP" as a hedged,
 * labeled possibility ("...is not specified... e.g., OTP"), not as a
 * claim. This exposed a real bug in exactly that shape, reproduced
 * directly against this project's own existing checkGrounding() module
 * (built in Part 2) -- see checkGrounding.ts's own updated docstring and
 * checkGrounding.test.ts's new "Part 6 fix" describe block for the fix
 * itself. This file proves the fix holds at the FULL PIPELINE level,
 * through the real requirementAnalyzerOracle (Part 3), not just as an
 * isolated unit test of checkGrounding() alone.
 */

const INPUT = "The system should allow users to reset their password quickly using email.";
const EXPECTED_AGENT_ID = "requirement-analyzer";

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
  return runtime.run(config, { input: INPUT });
}

// The article's own real, actually-quoted agent output for TC005.
const REAL_TC005_RESPONSE = JSON.stringify({
  actor: "User",
  feature: "Reset password using email",
  preconditions: [],
  positiveScenarios: [
    "User requests a password reset via email and successfully resets their password.",
  ],
  negativeScenarios: [],
  ambiguities: [
    "The requirement uses the term 'quickly', which is subjective and lacks a measurable performance target or time frame.",
    "The exact method for resetting the password via email (e.g., one-time link, temporary password, OTP) is not specified.",
    "Password strength or formatting rules for the new password are not specified.",
    "Error handling for invalid, unregistered, or unformatted email inputs is not specified.",
  ],
});

describe("TC005 -- subjective ambiguity, full pipeline (the real checkGrounding fix, proven end-to-end)", () => {
  it("the real agent output passes checkGrounding() cleanly -- confirming the Part 6 fix, not just asserting it", async () => {
    const result = await runRealPipeline(REAL_TC005_RESPONSE);
    const parsed = JSON.parse(result.output);
    expect(checkGrounding(INPUT, parsed)).toEqual([]);
  });

  it("the real agent output passes the full requirementAnalyzerOracle (Part 3) -- before the Part 6 fix, this would have incorrectly failed on the 'OTP' mention", async () => {
    const result = await runRealPipeline(REAL_TC005_RESPONSE);
    const verdict = evaluateRequirementAnalyzer({
      result,
      requirementText: INPUT,
      expectedAgentId: EXPECTED_AGENT_ID,
    });
    expect(verdict.passed).toBe(true);
    expect(verdict.findings).toHaveLength(0);
  });

  it("literal reproduction of the article's own BEFORE picture: a naive 'not.toContain(\"otp\")' assertion really does fail against this real, correct output", async () => {
    const result = await runRealPipeline(REAL_TC005_RESPONSE);
    const parsed = JSON.parse(result.output);
    const serializedOutput = JSON.stringify(parsed).toLowerCase();
    // This is the article's own flagged-as-too-weak assertion, reproduced
    // literally to show it genuinely fails here -- not hypothetically.
    expect(serializedOutput).toContain("otp");
  });

  describe("Response A vs. Response B -- the article's own central distinction, proven at the full-oracle level", () => {
    it("Response B (hedged, labeled possibility) passes -- the real agent behavior", async () => {
      const result = await runRealPipeline(REAL_TC005_RESPONSE);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: INPUT,
        expectedAgentId: EXPECTED_AGENT_ID,
      });
      expect(verdict.passed).toBe(true);
    });

    it("Response A (OTP asserted as an unsupported fact) correctly FAILS -- the oracle still catches real fabrication", async () => {
      const claimedAsFact = JSON.stringify({
        actor: "User",
        feature: "Reset password using email",
        preconditions: [],
        positiveScenarios: ["The system sends an OTP to the user's email."],
        negativeScenarios: [],
        ambiguities: [],
      });
      const result = await runRealPipeline(claimedAsFact);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: INPUT,
        expectedAgentId: EXPECTED_AGENT_ID,
      });
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
    });
  });
});

describe("the Contract defect Part 6 names (documented, not silently 'fixed' by inventing a schema field)", () => {
  it("confirms the real ambiguities array genuinely mixes two different problem categories -- subjective ambiguity vs. missing information -- in one field, as the article itself observes", async () => {
    const result = await runRealPipeline(REAL_TC005_RESPONSE);
    const parsed = JSON.parse(result.output) as { ambiguities: string[] };

    // "quickly" is subjective -- multiple valid readings exist.
    const subjectiveAmbiguity = parsed.ambiguities.find((a) => /subjective/i.test(a));
    // Password strength / error handling are simply unspecified business
    // rules -- there's no competing INTERPRETATION, just an absence.
    const missingInformation = parsed.ambiguities.filter(
      (a) => /not specified/i.test(a) && !/subjective/i.test(a)
    );

    expect(subjectiveAmbiguity).toBeDefined();
    expect(missingInformation.length).toBeGreaterThanOrEqual(2);
    // Deliberately NOT asserting a `missingInformation` field exists on
    // RequirementAnalysis -- the real requirement_analyzer.md schema (the
    // article's own authoritative file, swapped in during Part 2) has no
    // such field, and this project doesn't invent one speculatively. See
    // /notes/ai-agent-testing-framework-part6-analysis.md for why this is
    // documented as a named Contract defect rather than "fixed" here.
  });
});
