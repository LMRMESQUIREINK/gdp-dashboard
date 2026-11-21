import type { AgentResult, RequirementAnalysis } from "../types/AgentTypes.js";
import { parseAgentOutput } from "../output/parseAgentOutput.js";
import { checkGrounding } from "../grounding/checkGrounding.js";
import { evaluateBoundary, type QualityBoundary, type Verdict } from "./qualityBoundary.js";
import { isGroundedField } from "./lexicalGrounding.js";

/**
 * The concrete TC001 acceptance oracle for the Requirement Analyzer
 * agent, built directly from Part 3's own exact 8-item Required
 * checklist (Section 13 of the source article) — not an invented list.
 * This is what Part 3 itself names as the missing piece before writing
 * TC001, which the series' own next part (Part 4) is where it
 * promises to actually execute it.
 *
 * REQUIRED (per the article, verbatim):
 *   1. Agent executes successfully
 *   2. Correct agent is executed
 *   3. Output exists
 *   4. Output is valid JSON
 *   5. Required fields exist
 *   6. Actor represents the user
 *   7. Feature represents password reset
 *   8. At least one positive scenario is identified
 *
 * Checks 4 and 5 are evaluated TOGETHER here via one `parseAgentOutput`
 * call, which already enforces both atomically (valid JSON AND the
 * exact schema) -- building a second, separate validation layer just
 * to report two distinct names for what is, in this implementation,
 * one root cause would be redundant, so this is stated plainly as a
 * simplification rather than hidden.
 *
 * A REAL, HONESTLY-STATED GAP in the source, found by trying to
 * implement checks 6 and 7: Part 3 names "semantic correctness"
 * (Section 9.2) as a real evaluation dimension -- "if the requirement
 * identifies User but the agent identifies Administrator... the
 * meaning does not [pass]" -- but never specifies HOW an automated
 * oracle determines the "correct" actor/feature beyond the one worked
 * example's obvious case. No algorithm, no sketch, nothing beyond "a
 * human can tell." This mirrors the exact same kind of gap found in
 * Part 1's YAML-vs-prose mismatch: a real capability is named as
 * needed, but the mechanism to automate it is never given. Checks 6
 * and 7 below are therefore deliberately NOT full semantic-correctness
 * checks (that would require claiming an algorithm the source doesn't
 * supply); they check that `actor`/`feature` are non-empty AND
 * lexically traceable to the requirement text -- the same honestly-
 * scoped "grounded, not semantically verified" approach this build's
 * own groundedness checker already takes, reused here rather than
 * inventing a stronger claim the source itself never makes good on.
 *
 * FORBIDDEN: reuses `checkGrounding()` from Part 2's build -- any
 * numeric/technical-term fabrication fails the oracle.
 *
 * DELIBERATELY NOT a Required check, per the article's own central
 * lesson (Sections 5-7, "Could be tested != Is supported"):
 * `negativeScenarios.length > 0` is never asserted. The article is
 * explicit that requiring this without evidence in the requirement
 * would be the TEST inventing an expectation, not the agent failing --
 * proven directly in requirementAnalyzerOracle.test.ts.
 */

export interface OracleContext {
  result: AgentResult;
  requirementText: string;
  expectedAgentId: string;
}

// isGroundedField extracted to lexicalGrounding.ts in Part 9 so
// injectionResistanceOracle.ts can reuse the same "anchoring" check --
// behavior unchanged, including the singular/plural stemming fix found
// and fixed in Part 3.

function tryParse(result: AgentResult | null | undefined): RequirementAnalysis | null {
  if (!result || !result.output) return null;
  try {
    return parseAgentOutput(result.output);
  } catch {
    return null;
  }
}

export function buildRequirementAnalyzerBoundary(context: OracleContext): QualityBoundary<OracleContext> {
  return {
    required: [
      { name: "Agent executes successfully", check: (ctx) => ctx.result !== null && ctx.result !== undefined },
      {
        name: "Correct agent is executed",
        check: (ctx) => Boolean(ctx.result) && ctx.result.agentId === ctx.expectedAgentId,
      },
      { name: "Output exists", check: (ctx) => Boolean(ctx.result && ctx.result.output) },
      {
        name: "Output is valid JSON and required fields exist",
        check: (ctx) => tryParse(ctx.result) !== null,
      },
      {
        name: "Actor represents the user",
        check: (ctx) => {
          const parsed = tryParse(ctx.result);
          return parsed !== null && isGroundedField(parsed.actor, ctx.requirementText);
        },
      },
      {
        name: "Feature represents the requirement's subject",
        check: (ctx) => {
          const parsed = tryParse(ctx.result);
          return parsed !== null && isGroundedField(parsed.feature, ctx.requirementText);
        },
      },
      {
        name: "At least one positive scenario is identified",
        check: (ctx) => {
          const parsed = tryParse(ctx.result);
          return parsed !== null && parsed.positiveScenarios.length > 0;
        },
      },
    ],
    forbidden: [
      {
        name: "Ungrounded fabrication (numeric claim or technical term not in the requirement)",
        check: (ctx) => {
          const parsed = tryParse(ctx.result);
          if (parsed === null) return false; // a structural failure is already caught by Required checks above
          return checkGrounding(ctx.requirementText, parsed).length > 0;
        },
      },
    ],
  };
}

export function evaluateRequirementAnalyzer(context: OracleContext): Verdict {
  return evaluateBoundary(buildRequirementAnalyzerBoundary(context), context);
}
