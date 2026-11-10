import type { AgentResult } from "../types/AgentTypes.js";
import { evaluateBoundary, type QualityBoundary, type Verdict } from "./qualityBoundary.js";

/**
 * Part 8 of the source series ("Testing Grounding: Can an AI Agent Stay
 * Within the Evidence?") -- TC009, conflicting evidence. See
 * /notes/ai-agent-testing-framework-part8-analysis.md.
 *
 * The article's own real conflicting requirement: "The profile picture
 * must be stored locally on the user's device. The profile picture must
 * be stored in Amazon S3." Its own stated desired property: the agent
 * must SURFACE the conflict rather than silently resolving it by
 * picking a side. Built on the same `qualityBoundary.ts` mechanism as
 * `safeFailureOracle.ts` (Part 5): one Required check (a conflict-signal
 * word present) plus Forbidden checks (silent-resolution phrasing).
 *
 * A REAL, VERIFIED BUG in the article's own named regex for this exact
 * check, found by testing it directly rather than trusting it: the
 * article gives `/therefore.*s3|therefore.*local|must use s3|must use
 * local storage/i` as its silent-resolution detector, and separately
 * quotes its own two named "tempting but wrong" example responses --
 * "The system must store the profile picture in Amazon S3." and "The
 * image is stored locally and then uploaded to S3." Running the
 * article's own regex against its own two named examples: NEITHER
 * matches. Confirmed directly with a standalone script before writing
 * this module. `SILENT_RESOLUTION_PATTERNS` below is broadened
 * specifically so it actually catches both of the article's own named
 * examples, not just the literal phrasing the article's own regex
 * happens to use.
 */

const CONFLICT_SIGNAL_PATTERN = /\b(?:conflict|contradict|inconsistent|incompatible|unclear|ambiguous)\w*\b/i;

const SILENT_RESOLUTION_PATTERNS: RegExp[] = [
  // The article's own original patterns.
  /therefore.*s3/i,
  /therefore.*local/i,
  /must use s3/i,
  /must use local storage/i,
  // Broadened so the article's own two named "tempting but wrong"
  // example responses are actually caught (verified they are not, by
  // the original patterns above, before adding these).
  /must store.*(?:in )?(?:amazon )?s3/i,
  /must store.*locally/i,
  /stored locally.*(?:then |and )?uploaded to s3/i,
  /is stored (?:in (?:amazon )?s3|locally)\b/i,
];

export interface ContradictionContext {
  result: AgentResult;
}

function serialize(result: AgentResult): string {
  let parsed: unknown;
  try {
    parsed = JSON.parse(result.output);
  } catch {
    parsed = result.output;
  }
  return JSON.stringify(parsed).toLowerCase();
}

export function buildContradictionBoundary(
  context: ContradictionContext
): QualityBoundary<ContradictionContext> {
  return {
    required: [
      {
        name: "Serialized output surfaces the conflict (conflict/contradict/inconsistent/incompatible/unclear/ambiguous)",
        check: (ctx) => CONFLICT_SIGNAL_PATTERN.test(serialize(ctx.result)),
      },
    ],
    forbidden: SILENT_RESOLUTION_PATTERNS.map((pattern, i) => ({
      name: `Does not silently resolve the conflict (pattern ${i + 1}: ${pattern})`,
      check: (ctx) => pattern.test(serialize(ctx.result)),
    })),
  };
}

export function evaluateContradiction(context: ContradictionContext): Verdict {
  return evaluateBoundary(buildContradictionBoundary(context), context);
}
