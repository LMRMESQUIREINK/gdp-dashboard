import type { RequirementAnalysis } from "../types/AgentTypes.js";

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

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new OutputContractViolation("Output Requirements violation: parsed JSON is not an object.");
  }

  const obj = parsed as Record<string, unknown>;
  const stringFields: Array<keyof RequirementAnalysis> = ["actor", "feature"];
  const arrayFields: Array<keyof RequirementAnalysis> = [
    "preconditions",
    "positiveScenarios",
    "negativeScenarios",
    "ambiguities",
  ];

  for (const field of stringFields) {
    if (typeof obj[field] !== "string") {
      throw new OutputContractViolation(`Output Requirements violation: "${field}" must be a string.`);
    }
  }

  for (const field of arrayFields) {
    const value = obj[field];
    if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
      throw new OutputContractViolation(`Output Requirements violation: "${field}" must be an array of strings.`);
    }
  }

  return {
    actor: obj.actor as string,
    feature: obj.feature as string,
    preconditions: obj.preconditions as string[],
    positiveScenarios: obj.positiveScenarios as string[],
    negativeScenarios: obj.negativeScenarios as string[],
    ambiguities: obj.ambiguities as string[],
  };
}
