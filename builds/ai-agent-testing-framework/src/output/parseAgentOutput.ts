import type { RequirementAnalysis } from "../types/AgentTypes.js";
import { RequirementAnalysisSchema } from "../schema/RequirementAnalysisSchema.js";

/**
 * Enforces requirement_analyzer.md's own "Output Requirements" section
 * literally: "Return ONLY valid JSON. Do not wrap the JSON in Markdown
 * code fences. Do not include explanations before or after the JSON."
 * That's a real rule stated in the agent's own instructions -- but
 * nothing in either Part 1 or Part 2's own shown code ever actually
 * checks it. AgentRuntime.run() just returns `output: string`
 * unparsed; the article's own prose explicitly says this is deliberate
 * ("we are keeping the runtime relatively generic... our testing layer
 * will eventually determine whether that output satisfies the
 * contract"). This module is that missing enforcement.
 *
 * REFACTORED IN PART 9 ("Testing AI Agent Boundaries") onto the real
 * Zod schema the article introduces (`RequirementAnalysisSchema.ts`),
 * rather than the hand-rolled per-field loops this module originally
 * had. The parse-into-`unknown`-before-validating discipline below
 * matches the article's own explicitly stated practice exactly (this
 * module already did that correctly before Part 9 -- no change needed
 * there) -- but the hand-rolled loops themselves had TWO REAL GAPS,
 * found by checking the article's own schema (`.strict()`,
 * `z.string().min(1)`) against this module as it already existed,
 * confirmed by actually running the unmodified module against both
 * cases before refactoring, not assumed from reading the diff:
 *
 *   1. An unexpected extra field (e.g. `"confidence": 0.92`) was
 *      silently DROPPED rather than rejected -- the old code only
 *      checked that the fields it expected were present and typed
 *      correctly; it never checked for fields it didn't expect. Zod's
 *      `.strict()` closes this for real.
 *   2. An empty string (`"actor": ""`) passed `typeof === "string"`
 *      and was accepted -- the old code never checked length. Zod's
 *      `z.string().min(1)` closes this for real.
 *
 * See /notes/ai-agent-testing-framework-part9-analysis.md for the full
 * reproduction and TC012-TC016's own regression tests.
 */
export class OutputContractViolation extends Error {}

export function parseAgentOutput(raw: string): RequirementAnalysis {
  const trimmed = raw.trim();

  if (trimmed.startsWith("```")) {
    throw new OutputContractViolation(
      "Output Requirements violation: response is wrapped in a Markdown code fence, " +
        "which requirement_analyzer.md's own instructions explicitly prohibit."
    );
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch (err) {
    throw new OutputContractViolation(
      `Output Requirements violation: response is not valid JSON (${(err as Error).message}).`
    );
  }

  const result = RequirementAnalysisSchema.safeParse(parsed);
  if (!result.success) {
    const issues = result.error.issues.map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`);
    throw new OutputContractViolation(`Output Requirements violation: ${issues.join("; ")}`);
  }

  return result.data;
}
