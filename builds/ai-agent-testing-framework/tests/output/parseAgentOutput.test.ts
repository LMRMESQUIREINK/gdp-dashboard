import { describe, it, expect } from "vitest";
import { parseAgentOutput, OutputContractViolation } from "../../src/output/parseAgentOutput.js";

describe("parseAgentOutput", () => {
  it("parses the article's own real 'valid response' example exactly", () => {
    const raw = JSON.stringify({
      actor: "User",
      feature: "Password reset using email",
      preconditions: [],
      positiveScenarios: [
        "User requests a password reset using email and successfully resets the password.",
      ],
      negativeScenarios: [],
      ambiguities: [],
    });

    const result = parseAgentOutput(raw);
    expect(result.actor).toBe("User");
    expect(result.feature).toBe("Password reset using email");
    expect(result.positiveScenarios).toHaveLength(1);
  });

  it("rejects a response wrapped in Markdown code fences -- explicitly prohibited by requirement_analyzer.md's own Output Requirements", () => {
    const raw = "```json\n" + JSON.stringify({ actor: "User", feature: "x", preconditions: [], positiveScenarios: [], negativeScenarios: [], ambiguities: [] }) + "\n```";
    expect(() => parseAgentOutput(raw)).toThrow(OutputContractViolation);
    expect(() => parseAgentOutput(raw)).toThrow(/code fence/);
  });

  it("rejects explanatory prose before or after the JSON -- also explicitly prohibited", () => {
    const raw = "Here is the analysis:\n" + JSON.stringify({ actor: "User", feature: "x", preconditions: [], positiveScenarios: [], negativeScenarios: [], ambiguities: [] });
    expect(() => parseAgentOutput(raw)).toThrow(OutputContractViolation);
  });

  it("rejects malformed JSON with a clear OutputContractViolation, not a raw SyntaxError leaking to the caller", () => {
    expect(() => parseAgentOutput("{not valid json")).toThrow(OutputContractViolation);
  });

  it("rejects a JSON array at the top level (the contract requires an object)", () => {
    expect(() => parseAgentOutput("[]")).toThrow(OutputContractViolation);
  });

  for (const field of ["actor", "feature"] as const) {
    it(`rejects a response missing the required string field "${field}"`, () => {
      const obj: Record<string, unknown> = {
        actor: "User",
        feature: "x",
        preconditions: [],
        positiveScenarios: [],
        negativeScenarios: [],
        ambiguities: [],
      };
      delete obj[field];
      expect(() => parseAgentOutput(JSON.stringify(obj))).toThrow(OutputContractViolation);
    });
  }

  it("rejects a response where an array field contains a non-string item", () => {
    const raw = JSON.stringify({
      actor: "User",
      feature: "x",
      preconditions: [42],
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [],
    });
    expect(() => parseAgentOutput(raw)).toThrow(OutputContractViolation);
  });

  it("rejects a response where an array field is itself not an array", () => {
    const raw = JSON.stringify({
      actor: "User",
      feature: "x",
      preconditions: "not an array",
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [],
    });
    expect(() => parseAgentOutput(raw)).toThrow(OutputContractViolation);
  });

  describe("Part 9: TC012-TC016, deterministic contract tests (no live agent call needed)", () => {
    const valid = {
      actor: "User",
      feature: "Password reset using email",
      preconditions: [],
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [],
    };

    it("TC012 -- missing required field (covered above too; named explicitly here to match the article's own TC numbering)", () => {
      const { actor, ...withoutActor } = valid;
      expect(() => parseAgentOutput(JSON.stringify(withoutActor))).toThrow(OutputContractViolation);
    });

    it("TC013 -- incorrect field type (preconditions as a string instead of an array; covered above too)", () => {
      expect(() =>
        parseAgentOutput(JSON.stringify({ ...valid, preconditions: "not an array" }))
      ).toThrow(OutputContractViolation);
    });

    it("TC014 -- unexpected field is REJECTED, not silently dropped -- a real gap this round closed via Zod's .strict()", () => {
      // Before the Part 9 refactor, this project's own parseAgentOutput
      // silently dropped an extra field like "confidence" instead of
      // rejecting it -- reproduced directly against the unmodified
      // module before refactoring, not assumed. See
      // /notes/ai-agent-testing-framework-part9-analysis.md.
      const withExtraField = { ...valid, confidence: 0.92 };
      expect(() => parseAgentOutput(JSON.stringify(withExtraField))).toThrow(OutputContractViolation);
      expect(() => parseAgentOutput(JSON.stringify(withExtraField))).toThrow(/confidence/);
    });

    it("TC015 -- empty required string is REJECTED -- a real gap this round closed via Zod's z.string().min(1)", () => {
      // Before the Part 9 refactor, `"actor": ""` passed the old
      // `typeof === "string"` check (an empty string IS typeof
      // "string") -- reproduced directly before refactoring.
      expect(() => parseAgentOutput(JSON.stringify({ ...valid, actor: "" }))).toThrow(
        OutputContractViolation
      );
    });

    it("TC016 -- Markdown/code-fence output is a contract violation, never silently repaired (covered above too; the harness must observe the violation, not manufacture a better version of it)", () => {
      const raw = "```json\n" + JSON.stringify(valid) + "\n```";
      expect(() => parseAgentOutput(raw)).toThrow(OutputContractViolation);
    });

    it("arrays may legitimately stay empty -- the contract never forces the agent to invent information just to pass validation (the Part 4 lesson, now enforced by the same schema)", () => {
      expect(() => parseAgentOutput(JSON.stringify(valid))).not.toThrow();
    });
  });
});
