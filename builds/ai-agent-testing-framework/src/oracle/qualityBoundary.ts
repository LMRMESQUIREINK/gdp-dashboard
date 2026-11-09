/**
 * A real implementation of the Required/Allowed/Forbidden test-oracle
 * framework from Part 3 of the source series ("Testing AI Agents: A
 * Practical Quality Engineering Journey") — see
 * /notes/ai-agent-testing-framework-part3-analysis.md.
 *
 * The article's own framing: Required ("things the response must
 * satisfy"), Allowed ("things that may legitimately vary" — e.g.
 * wording), and Forbidden ("things that must not happen"). "Allowed"
 * needs no check of its own here, by design — it's the implicit
 * complement of Required+Forbidden (anything not asserted on is free
 * to vary), exactly matching the article's own point that fragile
 * exact-string assertions are the wrong tool. A QualityBoundary is
 * therefore just a Required list and a Forbidden list, each a set of
 * named, independently reportable checks — never a single pass/fail
 * boolean, because the article's own central lesson (Section 6-7: "the
 * problem may not be the agent, the problem may be our test") requires
 * being able to see EXACTLY which check failed, not just that
 * something did.
 */

export interface BoundaryCheck<T> {
  name: string;
  check: (value: T) => boolean;
}

export interface QualityBoundary<T> {
  required: BoundaryCheck<T>[];
  forbidden: BoundaryCheck<T>[];
}

export interface VerdictFinding {
  name: string;
  kind: "required-failed" | "forbidden-violated";
}

export interface Verdict {
  passed: boolean;
  findings: VerdictFinding[];
}

export function evaluateBoundary<T>(boundary: QualityBoundary<T>, value: T): Verdict {
  const findings: VerdictFinding[] = [];

  for (const { name, check } of boundary.required) {
    if (!check(value)) {
      findings.push({ name, kind: "required-failed" });
    }
  }

  for (const { name, check } of boundary.forbidden) {
    if (check(value)) {
      findings.push({ name, kind: "forbidden-violated" });
    }
  }

  return { passed: findings.length === 0, findings };
}
