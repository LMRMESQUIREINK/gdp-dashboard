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

  describe("Part 6 fix: hedged possibilities are Allowed, not Forbidden", () => {
    it("does NOT flag the article's own real TC005 output -- 'OTP' mentioned as a hedged, labeled possibility inside 'is not specified... (e.g., ... OTP)'", () => {
      const analysis: RequirementAnalysis = {
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
      };
      const requirement =
        "The system should allow users to reset their password quickly using email.";

      // Before the Part 6 fix, this reproducibly returned one finding:
      // { field: "ambiguities", index: 1, term: "OTP", kind: "technical-term" }
      // -- confirmed by running the unfixed module against this exact
      // real output before touching the code, per /notes/
      // ai-agent-testing-framework-part6-analysis.md.
      expect(checkGrounding(requirement, analysis)).toEqual([]);
    });

    it("still correctly flags the SAME term when it is asserted as an unhedged claim rather than a labeled possibility -- the article's own Response A vs. Response B distinction", () => {
      const requirement =
        "The system should allow users to reset their password quickly using email.";

      // Response A, the article's own example of an unsupported claim.
      const claimedAsFact: RequirementAnalysis = {
        actor: "User",
        feature: "Reset password using email",
        preconditions: [],
        positiveScenarios: ["The system sends an OTP to the user's email."],
        negativeScenarios: [],
        ambiguities: [],
      };
      const findings = checkGrounding(requirement, claimedAsFact);
      expect(findings.some((f) => f.kind === "technical-term" && f.term === "OTP")).toBe(true);
    });

    it("the hedge exemption does not weaken Part 2's original fabrication regression tests -- neither has hedging language, so both must still flag", () => {
      const otpFiveMinutes: RequirementAnalysis = {
        actor: "User",
        feature: "Password reset",
        preconditions: ["User has a valid email address"],
        positiveScenarios: ["User receives an OTP and resets the password within 5 minutes"],
        negativeScenarios: [],
        ambiguities: [],
      };
      const oauthAes: RequirementAnalysis = {
        actor: "User",
        feature: "Password reset using email",
        preconditions: ["The application must use OAuth 2.0"],
        positiveScenarios: ["The system should store the password using AES-256 encryption."],
        negativeScenarios: [],
        ambiguities: [],
      };

      expect(checkGrounding(REQUIREMENT, otpFiveMinutes).length).toBeGreaterThan(0);
      expect(checkGrounding(REQUIREMENT, oauthAes).length).toBeGreaterThan(0);
    });

    it("a hedged numeric claim is also exempted, not just hedged technical terms -- the fix applies uniformly to both claim kinds", () => {
      const requirement =
        "The system should allow users to reset their password quickly using email.";
      const analysis: RequirementAnalysis = {
        actor: "User",
        feature: "Reset password using email",
        preconditions: [],
        positiveScenarios: [],
        negativeScenarios: [],
        ambiguities: [
          "The term 'quickly' is not specified -- it could reasonably be interpreted as anywhere from 5 seconds to 2 minutes.",
        ],
      };
      expect(checkGrounding(requirement, analysis)).toEqual([]);
    });
  });

  describe("Part 7 fix: a real bug in the Part 6 HEDGE_PATTERN itself, found by testing against TC006's real output", () => {
    it("'e.g.' alone (with no other hedge phrase in the same sentence) now correctly exempts the mention -- the original \\be.g.\\b pattern never matched anything, since a literal '.' can't form a word-boundary transition right after it", () => {
      const requirement =
        "The system should allow customers to cancel an order within one day of placing it.";
      const analysis: RequirementAnalysis = {
        actor: "Customer",
        feature: "Order cancellation within one day",
        preconditions: [],
        positiveScenarios: [],
        negativeScenarios: [],
        ambiguities: [
          "The term 'one day' is ambiguous (e.g., whether it means exactly 24 hours from the timestamp of placement, or until midnight/end of the following calendar day).",
        ],
      };
      // Before this fix, this returned one finding on "24 hours" --
      // reproduced directly against the real article output before
      // fixing, not assumed. The only hedge markers in this exact
      // sentence are "ambiguous" and "e.g." -- neither of which the
      // original pattern actually matched.
      expect(checkGrounding(requirement, analysis)).toEqual([]);
    });

    it("'ambiguous'/'ambiguity' alone is also a real hedge signal on its own, not just a side effect of some other phrase", () => {
      const requirement = "The system should process requests within a reasonable time.";
      const analysis: RequirementAnalysis = {
        actor: "User",
        feature: "Request processing",
        preconditions: [],
        positiveScenarios: [],
        negativeScenarios: [],
        ambiguities: ["It is ambiguous whether this takes 5 seconds or 5 minutes."],
      };
      expect(checkGrounding(requirement, analysis)).toEqual([]);
    });
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
