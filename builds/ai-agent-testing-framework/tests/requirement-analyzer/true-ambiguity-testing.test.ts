import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { checkGrounding } from "../../src/grounding/checkGrounding.js";
import { evaluateRequirementAnalyzer } from "../../src/oracle/requirementAnalyzerOracle.js";
import type { LLMClient, AgentConfig, AgentResult } from "../../src/types/AgentTypes.js";

/**
 * Part 7 of the source series ("True Ambiguity: Can an AI Agent
 * Recognize Multiple Valid Interpretations?") -- TC006. See
 * /notes/ai-agent-testing-framework-part7-analysis.md.
 *
 * Part 7's own central, self-critical lesson: its own TC006, as written
 * in the article, only verifies that the agent ACKNOWLEDGES the
 * ambiguity -- it does NOT prove the agent never presents one
 * interpretation (e.g. "24 hours") as an established fact. The article
 * states this plainly: "A Test Can Be Correct and Still Be Incomplete."
 *
 * This file does two things with that lesson, not one:
 *   1. Confirms Part 6's hedge-detection fix generalizes correctly to
 *      this brand-new real example (the real output hedges "24 hours"
 *      inside "...is ambiguous (e.g., ... 24 hours ...)").
 *   2. Turns the article's own self-critique on THIS PROJECT'S OWN
 *      oracle: Behavior A (an unhedged, unsupported numeric claim) is
 *      already caught by the existing checkGrounding() numeric-claim
 *      check from Part 2/6 -- confirmed, not assumed. Behavior B (an
 *      unhedged, unsupported NON-numeric interpretation, e.g. the
 *      calendar-day reading) is NOT caught by anything this project has
 *      built -- demonstrated honestly as a real, named, tracked
 *      limitation, exactly the kind of gap the article itself says is
 *      fine to leave open rather than force-closed with a fragile fix.
 */

const INPUT =
  "The system should allow customers to cancel an order within one day of placing it.";
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

// The article's own real, actually-quoted agent output for TC006.
const REAL_TC006_RESPONSE = JSON.stringify({
  actor: "Customer",
  feature: "Order cancellation within one day",
  preconditions: ["An order has been placed by the customer."],
  positiveScenarios: [
    "Customer requests to cancel an order within one day of placing it, and the cancellation is successful.",
  ],
  negativeScenarios: [
    "Customer attempts to cancel an order after one day has passed since placing it, and the system denies the request.",
  ],
  ambiguities: [
    "The term 'one day' is ambiguous (e.g., whether it means exactly 24 hours from the timestamp of placement, or until midnight/end of the following calendar day).",
    "The exact starting event that defines when an order is 'placed' is not specified.",
    "It is unclear if an order can still be canceled within one day if it has already been processed, packed, or shipped.",
    "The system's behavior regarding refunds, inventory updates, or customer notifications upon cancellation is unspecified.",
  ],
});

describe("TC006 -- true ambiguity (multiple valid interpretations), full pipeline", () => {
  it("the real agent output passes checkGrounding() cleanly -- confirms the Part 6 hedge fix generalizes to a brand-new real example ('24 hours' hedged inside 'ambiguous (e.g., ...)')", async () => {
    const result = await runRealPipeline(REAL_TC006_RESPONSE);
    const parsed = JSON.parse(result.output);
    expect(checkGrounding(INPUT, parsed)).toEqual([]);
  });

  it("the real agent output passes the full requirementAnalyzerOracle (Part 3) cleanly", async () => {
    const result = await runRealPipeline(REAL_TC006_RESPONSE);
    const verdict = evaluateRequirementAnalyzer({
      result,
      requirementText: INPUT,
      expectedAgentId: EXPECTED_AGENT_ID,
    });
    expect(verdict.passed).toBe(true);
    expect(verdict.findings).toHaveLength(0);
  });

  it("literal reproduction of the article's own flagged-as-dangerous assertion -- 'not.toContain(\"24 hours\")' really would have failed this correct output", async () => {
    const result = await runRealPipeline(REAL_TC006_RESPONSE);
    const parsed = JSON.parse(result.output);
    const serializedOutput = JSON.stringify(parsed).toLowerCase();
    expect(serializedOutput).toContain("24 hours");
  });

  describe("the article's own named incompleteness, turned on THIS PROJECT'S oracle rather than just narrated", () => {
    it("Behavior A (an unhedged, unsupported numeric interpretation presented as fact) IS already caught -- by the existing numeric-claim check from Part 2/6, confirmed rather than assumed", async () => {
      const behaviorA = JSON.stringify({
        actor: "Customer",
        feature: "Order cancellation within one day",
        preconditions: ["An order has been placed by the customer."],
        positiveScenarios: [
          "The customer can cancel the order within 24 hours of placing the order.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      });
      const result = await runRealPipeline(behaviorA);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: INPUT,
        expectedAgentId: EXPECTED_AGENT_ID,
      });
      expect(verdict.passed).toBe(false);
      const forbiddenFinding = verdict.findings.find((f) => f.kind === "forbidden-violated");
      expect(forbiddenFinding).toBeDefined();
    });

    it("KNOWN, NAMED LIMITATION -- Behavior B (an unhedged, unsupported NON-numeric interpretation presented as fact) is NOT caught by anything built so far. This is deliberately documented as an honest gap, not silently papered over.", async () => {
      // This is exactly the article's own "A Test Can Be Correct and
      // Still Be Incomplete" lesson, demonstrated against this project's
      // own oracle rather than only narrated about the article's. Closing
      // it properly needs a real mechanism for "does this field assert a
      // specific non-numeric interpretation as fact that the requirement
      // never specified" -- which is the general semantic-correctness
      // problem Part 3 already named as unsolved (no algorithm supplied
      // by the source beyond one worked example), not something to
      // force-close here with a fragile keyword heuristic. Tracked
      // honestly instead, per this project's own established discipline
      // (Part 3's semantic-correctness gap, Part 4's instruction-
      // following gap) -- see /notes/ai-agent-testing-framework-part7-
      // analysis.md.
      const behaviorB = JSON.stringify({
        actor: "Customer",
        feature: "Order cancellation within one day",
        preconditions: ["An order has been placed by the customer."],
        positiveScenarios: [
          "The customer can cancel the order until midnight on the following calendar day.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      });
      const result = await runRealPipeline(behaviorB);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: INPUT,
        expectedAgentId: EXPECTED_AGENT_ID,
      });
      // This SHOULD fail (an unsupported interpretation stated as fact)
      // but currently passes -- the gap this test exists to track.
      expect(verdict.passed).toBe(true);
    });
  });
});

describe("the Contract defect recurs on a second real example (documented, not silently 'fixed')", () => {
  it("confirms the real ambiguities array again mixes true ambiguity with plain missing information -- the same observation Part 6 made, now reproduced on an independent real example", async () => {
    const result = await runRealPipeline(REAL_TC006_RESPONSE);
    const parsed = JSON.parse(result.output) as { ambiguities: string[] };

    const trueAmbiguity = parsed.ambiguities.find((a) => /\bambiguous\b/i.test(a));
    const missingInformation = parsed.ambiguities.filter(
      (a) => !/\bambiguous\b/i.test(a) && /(not specified|unclear|unspecified)/i.test(a)
    );

    expect(trueAmbiguity).toBeDefined();
    expect(missingInformation.length).toBeGreaterThanOrEqual(2);
    // Deliberately NOT adding a `missingInformation` field to
    // RequirementAnalysis -- same reasoning as Part 6: the real
    // requirement_analyzer.md schema is the source series' own
    // authoritative file, not this project's to redesign speculatively.
  });
});
