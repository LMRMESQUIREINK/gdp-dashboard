import { describe, it, expect } from "vitest";
import { evaluateBoundary, type QualityBoundary } from "../../src/oracle/qualityBoundary.js";

describe("evaluateBoundary (generic Required/Forbidden mechanism)", () => {
  it("passes when every Required check passes and no Forbidden check fires", () => {
    const boundary: QualityBoundary<number> = {
      required: [{ name: "is positive", check: (n) => n > 0 }],
      forbidden: [{ name: "is over 100", check: (n) => n > 100 }],
    };
    const verdict = evaluateBoundary(boundary, 5);
    expect(verdict.passed).toBe(true);
    expect(verdict.findings).toHaveLength(0);
  });

  it("reports a required-failed finding by name when a Required check fails", () => {
    const boundary: QualityBoundary<number> = {
      required: [{ name: "is positive", check: (n) => n > 0 }],
      forbidden: [],
    };
    const verdict = evaluateBoundary(boundary, -1);
    expect(verdict.passed).toBe(false);
    expect(verdict.findings).toEqual([{ name: "is positive", kind: "required-failed" }]);
  });

  it("reports a forbidden-violated finding by name when a Forbidden check fires", () => {
    const boundary: QualityBoundary<number> = {
      required: [],
      forbidden: [{ name: "is over 100", check: (n) => n > 100 }],
    };
    const verdict = evaluateBoundary(boundary, 200);
    expect(verdict.passed).toBe(false);
    expect(verdict.findings).toEqual([{ name: "is over 100", kind: "forbidden-violated" }]);
  });

  it("reports every failing check, not just the first -- this is the whole point of the article's Section 6-7 lesson: see exactly which check failed", () => {
    const boundary: QualityBoundary<number> = {
      required: [
        { name: "is positive", check: (n) => n > 0 },
        { name: "is even", check: (n) => n % 2 === 0 },
      ],
      forbidden: [{ name: "is over 100", check: (n) => n > 100 }],
    };
    const verdict = evaluateBoundary(boundary, 201);
    expect(verdict.passed).toBe(false);
    expect(verdict.findings).toHaveLength(2);
    expect(verdict.findings.map((f) => f.name).sort()).toEqual(["is even", "is over 100"].sort());
  });

  it("never asserts anything about Allowed -- there is no Allowed list anywhere in the API, by design", () => {
    const boundary: QualityBoundary<string> = {
      required: [{ name: "non-empty", check: (s) => s.length > 0 }],
      forbidden: [],
    };
    // Two completely different strings, neither constrained beyond "non-empty",
    // both pass -- proving "anything not asserted on is free to vary."
    expect(evaluateBoundary(boundary, "hello").passed).toBe(true);
    expect(evaluateBoundary(boundary, "a totally different wording entirely").passed).toBe(true);
  });
});
