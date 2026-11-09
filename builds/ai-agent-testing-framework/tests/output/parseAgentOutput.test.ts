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
});
