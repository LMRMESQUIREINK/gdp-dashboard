import type { AgentResult } from "../types/AgentTypes.js";
import { evaluateBoundary, type QualityBoundary, type Verdict } from "./qualityBoundary.js";

/**
 * Part 5 of the source series ("Negative Testing: What Happens When the
 * Input Is Bad?") gives a real, literal assertion pattern for TC002-TC004
 * (empty input, wrong-domain input, nonsense input) -- see
 * /notes/ai-agent-testing-framework-part5-analysis.md:
 *
 *   const serializedOutput = JSON.stringify(parsed).toLowerCase();
 *   expect(serializedOutput).toMatch(
 *     /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/
 *   );
 *   expect(serializedOutput).not.toContain("banana management");
 *   expect(serializedOutput).not.toContain("password reset");
 *
 * This is the SAME Required+Forbidden shape Part 3's `qualityBoundary.ts`
 * already generalizes -- a required "safe-failure signal present" check,
 * plus one or more forbidden "invented concept" checks -- so this module
 * builds the concrete oracle on top of that existing generic mechanism
 * rather than hand-rolling a parallel one. The "serialize, then search"
 * technique itself is the article's own real contribution: it tests the
 * BEHAVIORAL PROPERTY (did the agent preserve the absence of evidence)
 * rather than any one exact wording, which is exactly the flexibility a
 * test oracle for an LLM-backed agent needs.
 */

const SAFE_SIGNAL_PATTERN = /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/;

export interface SafeFailureContext {
  result: AgentResult;
  forbiddenTerms: string[];
}

/**
 * Serializes the parsed output the same way the article's own code does
 * (`JSON.stringify(parsed).toLowerCase()`) -- falling back to the raw,
 * unparsed string if the output isn't valid JSON at all, so a safe-
 * failure check can still run (and correctly fail, for the right reason)
 * against a response that violates the Output Requirements contract
 * outright, rather than throwing before the check gets a chance to run.
 */
function serialize(result: AgentResult): string {
  let parsed: unknown;
  try {
    parsed = JSON.parse(result.output);
  } catch {
    parsed = result.output;
  }
  return JSON.stringify(parsed).toLowerCase();
}

export function buildSafeFailureBoundary(
  context: SafeFailureContext
): QualityBoundary<SafeFailureContext> {
  return {
    required: [
      {
        name: "Serialized output contains a recognizable safe-failure signal (unknown/missing/not specified/not provided/insufficient/empty/ambiguous)",
        check: (ctx) => SAFE_SIGNAL_PATTERN.test(serialize(ctx.result)),
      },
    ],
    forbidden: context.forbiddenTerms.map((term) => ({
      name: `Does not invent the forbidden concept "${term}"`,
      check: (ctx) => serialize(ctx.result).includes(term.toLowerCase()),
    })),
  };
}

export function evaluateSafeFailure(context: SafeFailureContext): Verdict {
  return evaluateBoundary(buildSafeFailureBoundary(context), context);
}
