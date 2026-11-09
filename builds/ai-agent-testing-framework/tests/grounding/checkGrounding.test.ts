import { describe, it, expect } from "vitest";
import { checkGrounding } from "../../src/grounding/checkGrounding.js";
import type { RequirementAnalysis } from "../../src/types/AgentTypes.js";

/**
 * All fixtures below are the article's OWN worked examples from Part 2
 * ("Testing AI Agents: A Practical Quality Engineering Journey"),
 * reproduced verbatim as test data -- not hand-picked synthetic cases.
 */
const REQUIREMENT = "The system should allow users to reset their password using email.";

describe("checkGrounding", () => {
  it("flags the article's own Example 1 fabrication (OTP, 5 minutes) -- real true-positive case", () => {
    const analysis: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset",
      preconditions: ["User has a valid email address"],
      positiveScenarios: ["User receives an OTP and resets the password within 5 minutes"],
      negativeScenarios: [],
      ambiguities: [],
    };

    const findings = checkGrounding(REQUIREMENT, analysis);

    expect(findings.some((f) => f.kind === "technical-term" && f.term === "OTP")).toBe(true);
    expect(findings.some((f) => f.kind === "numeric" && f.term.includes("5 minute"))).toBe(true);
  });

  it("flags the article's own Example 2 fabrication (OAuth 2.0, AES-256) -- real true-positive case", () => {
    const analysis: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset using email",
      preconditions: ["The application must use OAuth 2.0"],
      positiveScenarios: ["The system should store the password using AES-256 encryption."],
      negativeScenarios: [],
      ambiguities: [],
    };

    const findings = checkGrounding(REQUIREMENT, analysis);

    expect(findings.some((f) => f.kind === "technical-term" && f.term === "OAuth 2.0")).toBe(true);
    expect(findings.some((f) => f.kind === "technical-term" && f.term === "AES-256")).toBe(true);
  });

  it("does NOT flag the article's own real paraphrase-equivalence example -- the real false-positive-avoidance test", () => {
    // These two phrasings are the article's own example of textually
    // different but behaviorally equivalent output. A naive full-word-
    // presence checker WOULD flag "initiates"/"recovery"/"completes" as
    // unsupported -- this is the exact test that first-draft design
    // failed, which is why checkGrounding only targets numeric claims
    // and a curated technical-term list instead. See the module
    // docstring in checkGrounding.ts for the full account.
    const variantA: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset using email",
      preconditions: [],
      positiveScenarios: ["User requests a password reset using email and successfully resets the password."],
      negativeScenarios: [],
      ambiguities: [],
    };
    const variantB: RequirementAnalysis = {
      actor: "User",
      feature: "Reset password through email",
      preconditions: [],
      positiveScenarios: ["The user initiates password recovery through email and completes the reset."],
      negativeScenarios: [],
      ambiguities: [],
    };

    expect(checkGrounding(REQUIREMENT, variantA)).toEqual([]);
    expect(checkGrounding(REQUIREMENT, variantB)).toEqual([]);
  });

  it("does not flag a genuinely clean, fully-grounded response", () => {
    const analysis: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset using email",
      preconditions: [],
      positiveScenarios: [
        "User requests a password reset using email and successfully resets the password.",
      ],
      negativeScenarios: [],
      ambiguities: [],
    };

    expect(checkGrounding(REQUIREMENT, analysis)).toEqual([]);
  });

  it("does not flag a technical term or number that genuinely IS present in the requirement", () => {
    const requirementWithRealConstraint =
      "The system should allow users to reset their password using email, with an OTP sent to the registered email, expiring after 10 minutes.";
    const analysis: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset using email",
      preconditions: ["User receives an OTP that expires after 10 minutes"],
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [],
    };

    expect(checkGrounding(requirementWithRealConstraint, analysis)).toEqual([]);
  });

  it("reports WHICH field and index a fabrication came from, not just that one exists somewhere", () => {
    const analysis: RequirementAnalysis = {
      actor: "User",
      feature: "Password reset",
      preconditions: [],
      positiveScenarios: ["Clean scenario, no fabrication"],
      negativeScenarios: ["User fails OTP verification"],
      ambiguities: [],
    };

    const findings = checkGrounding(REQUIREMENT, analysis);
    expect(findings).toHaveLength(1);
    expect(findings[0]).toMatchObject({ field: "negativeScenarios", index: 0, term: "OTP", kind: "technical-term" });
  });
});
