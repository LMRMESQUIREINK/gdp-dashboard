import { z } from "zod";

/**
 * Part 9 of the source series ("Testing AI Agent Boundaries: Output
 * Contracts, Grounding and Prompt Injection") introduces an explicit
 * runtime contract via Zod, reproduced here verbatim from the article's
 * own shown code (zod@4.6.7 installed; `.strict()` still exists on
 * object schemas in v4, confirmed by actually running it, not assumed
 * from the v3 API docs).
 *
 * Required strings cannot be empty (`z.string().min(1)`), arrays may
 * legitimately be empty (the agent isn't forced to invent a negative
 * scenario just to satisfy the test -- the same Part 4 lesson), and the
 * schema is CLOSED (`.strict()`): an extra field like `confidence` is
 * rejected outright, not silently dropped.
 *
 * See /notes/ai-agent-testing-framework-part9-analysis.md for two real
 * gaps this closes in this build's own pre-existing parseAgentOutput.ts
 * (Part 2): it silently dropped unexpected extra fields instead of
 * rejecting them, and it accepted an empty actor/feature string.
 * Reproduced directly against the unmodified module before fixing.
 */
export const RequirementAnalysisSchema = z
  .object({
    actor: z.string().min(1),
    feature: z.string().min(1),
    preconditions: z.array(z.string()),
    positiveScenarios: z.array(z.string()),
    negativeScenarios: z.array(z.string()),
    ambiguities: z.array(z.string()),
  })
  .strict();

export type RequirementAnalysisOutput = z.infer<typeof RequirementAnalysisSchema>;
