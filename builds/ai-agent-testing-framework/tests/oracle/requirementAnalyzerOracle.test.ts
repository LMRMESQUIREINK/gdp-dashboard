import { describe, it, expect } from "vitest";
import {
  evaluateRequirementAnalyzer,
  type OracleContext,
} from "../../src/oracle/requirementAnalyzerOracle.js";
import type { AgentResult } from "../../src/types/AgentTypes.js";

// The article's own canonical requirement, reused throughout Part 2 and Part 3.
const REQUIREMENT_TEXT = "The system should allow users to reset their password using email.";
const EXPECTED_AGENT_ID = "requirement-analyzer";

function makeResult(output: string, agentId = EXPECTED_AGENT_ID): AgentResult {
  return { agentId, agentVersion: "1.0.0", output };
}

function makeContext(output: string, agentId = EXPECTED_AGENT_ID): OracleContext {
  return {
    result: makeResult(output, agentId),
    requirementText: REQUIREMENT_TEXT,
    expectedAgentId: EXPECTED_AGENT_ID,
  };
}

describe("evaluateRequirementAnalyzer -- the concrete TC001 acceptance oracle", () => {
  it("passes a real, grounded, well-formed response -- all 8 Required items satisfied, no Forbidden violation", () => {
    const output = JSON.stringify({
      actor: "User",
      feature: "Password reset using email",
      preconditions: ["User has access to the email account on file."],
      positiveScenarios: [
        "User requests a password reset using email and successfully resets the password.",
      ],
      negativeScenarios: [],
      ambiguities: ["The requirement does not specify a password reset link expiry time."],
    });

    const verdict = evaluateRequirementAnalyzer(makeContext(output));
    expect(verdict.passed).toBe(true);
    expect(verdict.findings).toHaveLength(0);
  });

  describe("the central Part 3 lesson: 'Could be tested != Is supported'", () => {
    it("Situation A: a response with EMPTY negativeScenarios for a requirement with no negative-path evidence must NOT fail -- this is the article's own point, not a convenient exception", () => {
      // The real requirement text above never describes what happens on a
      // WRONG input (invalid email, no account found, etc.) -- there is no
      // evidence in the requirement for any negative scenario at all. A test
      // that required `negativeScenarios.length > 0` here would be the TEST
      // inventing an expectation the source material never supports -- exactly
      // what Part 3 names as the mistake to avoid ("we should not weaken a
      // test because the AI failed... we should change an assertion only when
      // our expectation was stronger than the evidence justified").
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "User requests a password reset using email and successfully resets the password.",
        ],
        negativeScenarios: [], // deliberately empty -- must still pass
        ambiguities: [],
      });

      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(true);
    });

    it("Situation B: a response that INVENTS a negative scenario the requirement gives no evidence for is a Forbidden fabrication, not a Required success", () => {
      // Fabricating a specific negative-path mechanism ("locks the account
      // after 3 failed attempts") that the requirement never mentions is
      // exactly the kind of invented business rule Rule 2 of
      // requirement_analyzer.md prohibits -- caught here by the existing
      // checkGrounding() numeric-claim check (reused from Part 2's build),
      // wired in as this oracle's one Forbidden check.
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "User requests a password reset using email and successfully resets the password.",
        ],
        negativeScenarios: ["System locks the account after 3 attempts."],
        ambiguities: [],
      });

      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings).toEqual([
        {
          name: "Ungrounded fabrication (numeric claim or technical term not in the requirement)",
          kind: "forbidden-violated",
        },
      ]);
    });

    it("the real article paraphrase pair (Part 2) is Allowed, not Forbidden -- different wording, same meaning, must not be flagged", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "The user initiates password recovery through email and completes the reset.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      });

      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(true);
    });
  });

  describe("each of the 8 Required items, failing one at a time", () => {
    it("1. 'Agent executes successfully' fails when there is no result at all", () => {
      const context: OracleContext = {
        result: null as unknown as AgentResult,
        requirementText: REQUIREMENT_TEXT,
        expectedAgentId: EXPECTED_AGENT_ID,
      };
      const verdict = evaluateRequirementAnalyzer(context);
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain("Agent executes successfully");
    });

    it("2. 'Correct agent is executed' fails when a different agentId answered", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: ["x"],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output, "some-other-agent"));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain("Correct agent is executed");
    });

    it("3. 'Output exists' fails on an empty string", () => {
      const verdict = evaluateRequirementAnalyzer(makeContext(""));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain("Output exists");
    });

    it("4+5. 'Output is valid JSON and required fields exist' fails on malformed JSON", () => {
      const verdict = evaluateRequirementAnalyzer(makeContext("{not valid json"));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain(
        "Output is valid JSON and required fields exist"
      );
    });

    it("4+5. also fails when the output is wrapped in Markdown code fences, per the real Output Requirements contract", () => {
      const inner = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: ["x"],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext("```json\n" + inner + "\n```"));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain(
        "Output is valid JSON and required fields exist"
      );
    });

    it("6. 'Actor represents the user' fails when actor is empty", () => {
      const output = JSON.stringify({
        actor: "",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: ["x"],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain("Actor represents the user");
    });

    it("6. also fails when actor shares no vocabulary with the requirement at all (the honest lexical-grounding limit, not true semantic verification -- see the module's own gap statement)", () => {
      const output = JSON.stringify({
        actor: "Administrator",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: ["x"],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain("Actor represents the user");
    });

    it("7. 'Feature represents the requirement's subject' fails when feature is unrelated to the requirement", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Export invoices to PDF",
        preconditions: [],
        positiveScenarios: ["x"],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain(
        "Feature represents the requirement's subject"
      );
    });

    it("8. 'At least one positive scenario is identified' fails when positiveScenarios is empty", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.map((f) => f.name)).toContain(
        "At least one positive scenario is identified"
      );
    });
  });

  describe("Forbidden: reuses Part 2's checkGrounding() directly, not reimplemented", () => {
    it("flags the article's own real OTP/5-minutes fabrication example", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "User receives an OTP via email and must enter it within 5 minutes to reset the password.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
    });

    it("flags the article's own real OAuth 2.0/AES-256 fabrication example", () => {
      const output = JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "User resets their password via OAuth 2.0 and the new password is stored with AES-256 encryption.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      });
      const verdict = evaluateRequirementAnalyzer(makeContext(output));
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
    });

    it("does not double-report a Forbidden finding when the output is already structurally invalid (Required checks already cover that failure)", () => {
      const verdict = evaluateRequirementAnalyzer(makeContext("{not valid json"));
      expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(false);
    });
  });
});
