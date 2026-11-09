import type { RequirementAnalysis } from "../types/AgentTypes.js";

/**
 * A real, honestly-scoped grounding checker operationalizing
 * requirement_analyzer.md's own Rules 1-4 and 7 ("use only information
 * supported by the supplied requirement," "do not invent business
 * rules," "do not invent technical implementation details," "do not
 * assume unspecified behavior," "do not treat assumptions as facts")
 * as an actual, runnable check -- not just prompt text nobody verifies.
 * Built directly from Part 2's own two worked examples:
 *
 *   1. A response fabricating "OTP" and "within 5 minutes" for a
 *      requirement that never mentions either.
 *   2. A response fabricating "OAuth 2.0" and "AES-256 encryption" for
 *      the same requirement.
 *
 * WHY THIS ISN'T A FULL WORD-PRESENCE CHECK (a deliberate, tested
 * design choice, not an oversight): Part 2 ALSO gives a real
 * paraphrase-equivalence example -- two differently-worded but
 * behaviorally equivalent positive scenarios ("User requests a
 * password reset using email and successfully resets the password."
 * vs. "The user initiates password recovery through email and
 * completes the reset."). A naive "every word in the output must
 * appear in the input" checker flags "initiates"/"recovery"/
 * "completes" as unsupported -- a FALSE POSITIVE against the article's
 * own stated point that different phrasings can be equally valid.
 * Verified directly with a standalone script BEFORE writing this
 * module (not assumed): a naive full-word-presence check against that
 * exact paraphrase really does flag ["user", "initiates", "recovery",
 * "completes"]. That's why this module checks only two narrower,
 * concrete patterns instead: numeric/duration claims, and a
 * curated list of security/auth technical terms -- precisely the two
 * patterns Part 2's own two fabrication examples actually are. This is
 * NOT full semantic correctness checking (the article's own "test
 * oracle problem," explicitly deferred to a future part of its own
 * series) -- it is a narrow, honest, directly-evidenced check for the
 * two concrete fabrication patterns this source actually demonstrates.
 *
 * A SECOND REAL BUG, found in Part 6 ("Testing Ambiguity in AI Agents"),
 * by running THIS exact module against Part 6's own real TC005 output,
 * not a hypothetical: the agent's real ambiguities field says "The exact
 * method for resetting the password via email (e.g., one-time link,
 * temporary password, OTP) is not specified." -- a hedged, labeled
 * POSSIBILITY, explicitly not a claim. Before this fix, checkGrounding()
 * flagged "OTP" here as a fabrication anyway, because it only checked
 * whether a term was literally present in the requirement text, never
 * whether the agent's own sentence was asserting it as fact or naming it
 * as an unresolved possibility. Reproduced directly against this exact
 * module before fixing (not assumed) -- see
 * /notes/ai-agent-testing-framework-part6-analysis.md. The article's own
 * distinction: "The system sends an OTP" (an unsupported claim, still
 * correctly Forbidden) vs. "...is not specified... e.g., OTP" (a hedged
 * possibility, correctly Allowed). `HEDGE_PATTERN` below is the fix: a
 * claim or term is only flagged when the SAME field/array-item text has
 * no hedging language. This widens what's Allowed; it does not narrow
 * what's Forbidden -- every one of Part 2's own original fabrication
 * examples (no hedge words present in either) still flags correctly,
 * confirmed by the unmodified regression tests in checkGrounding.test.ts.
 */

export interface GroundingFinding {
  field: keyof RequirementAnalysis;
  index: number | null; // null for scalar fields (actor, feature); array index otherwise
  term: string;
  kind: "numeric" | "technical-term";
}

// A deliberately small, named, auditable list -- not an attempt at
// exhaustive coverage of every term an LLM might invent. Add to it as
// real fabrication patterns are found, the same way this project's
// /builds/humanizer/ grows its own term list from real finds.
//
// Part 8 ("Testing Grounding") added a whole new vocabulary of real,
// named unsupported-claim examples -- image formats, storage mechanisms,
// and UI/processing details -- none of which are security/auth terms
// like the original Part 2 list. Added below rather than left
// uncovered, from Part 8's own TC007/TC008/TC010 real examples: image
// formats (the real TC007 output's own hedged "e.g., JPEG, PNG"
// mention), storage mechanisms (TC008's real "Amazon S3" evidence, and
// the unsupported AWS/storage expansions TC008 explicitly warns
// against), and the UI/processing claims TC010 names directly
// ("clicks the upload button," "generates a thumbnail").
const TECHNICAL_TERMS = [
  "OTP",
  "2FA",
  "MFA",
  "OAuth",
  "OAuth2",
  "OAuth 2.0",
  "SSO",
  "JWT",
  "SAML",
  "TLS",
  "SSL",
  "AES",
  "AES-256",
  "RSA",
  "bcrypt",
  "HMAC",
  "SHA",
  "SHA-256",
  "PIN",
  "CAPTCHA",
  // Part 8 additions:
  "JPEG",
  "PNG",
  "GIF",
  "WEBP",
  "S3",
  "Amazon S3",
  "database",
  "bucket",
  "bucket name",
  "AWS region",
  "encryption",
  "retention",
  "CDN",
  "thumbnail",
  "upload button",
  "browse button",
  "authentication",
  // "authenticate" (the verb form) listed separately, not implied by
  // "authentication" -- a real gap found while testing this round:
  // TC010's own named claim is "Users MUST AUTHENTICATE before
  // uploading," which this list's literal-substring matching missed
  // entirely until the verb form was added explicitly. Same class of
  // bug as the earlier "user"/"users" singular/plural gap found in
  // requirementAnalyzerOracle.ts (Part 3) -- this list has no stemming,
  // so morphological variants need listing, not assuming.
  "authenticate",
  "login",
];

const NUMERIC_CLAIM_PATTERN =
  /\b\d+(?:\.\d+)?\s*(?:second|minute|hour|day|week|month|year|%|percent|attempt|time|byte|KB|MB|GB|TB|pixel|px)s?\b/gi;

// The Part 6 fix: a term/claim mentioned alongside hedging language in
// the SAME field/array-item text is a labeled possibility (Allowed),
// not a claim presented as fact (Forbidden) -- see the module docstring.
//
// A REAL BUG in this exact pattern, found in Part 7 by testing it
// against TC006's real output (not assumed from reading the regex): (1)
// `\be\.g\.\b` never matches anywhere, because a literal `.` is not a
// word character, so the trailing `\b` can never find a word/non-word
// transition right after it -- `\b` requires one side of the boundary to
// be a word character, and nothing immediately after "e.g." in real text
// ever is. Part 6's own test fixture happened to also contain "is not
// specified" in the same sentence, which matched a DIFFERENT alternative
// and masked this one being dead code. (2) "ambiguous" itself was never
// in this list at all, even though an agent explicitly saying "the term
// is ambiguous" is the clearest possible hedge signal there is. Fixed:
// dropped the unmatchable trailing `\b` from the e.g./for example
// alternatives, and added `\bambigu\w*\b` (matches "ambiguous",
// "ambiguity", "ambiguities").
const HEDGE_PATTERN =
  /\bnot specified\b|\bunspecified\b|\bnot defined\b|\bnot provided\b|\bpossibl\w*\b|\bhypothetical\w*\b|\be\.g\.|\bfor example\b|\bunclear\b|\bambigu\w*\b/i;

function isHedged(value: string): boolean {
  return HEDGE_PATTERN.test(value);
}

function findNumericClaims(text: string): string[] {
  return [...text.matchAll(NUMERIC_CLAIM_PATTERN)].map((m) => m[0].toLowerCase().replace(/\s+/g, " ").trim());
}

function findTechnicalTerms(text: string): string[] {
  const found: string[] = [];
  for (const term of TECHNICAL_TERMS) {
    const pattern = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (pattern.test(text)) {
      found.push(term);
    }
  }
  return found;
}

function isGrounded(claim: string, requirementTextLower: string): boolean {
  return requirementTextLower.includes(claim.toLowerCase());
}

function checkField(
  field: keyof RequirementAnalysis,
  value: string,
  index: number | null,
  requirementTextLower: string,
  out: GroundingFinding[]
): void {
  const hedged = isHedged(value);
  for (const claim of findNumericClaims(value)) {
    if (!isGrounded(claim, requirementTextLower) && !hedged) {
      out.push({ field, index, term: claim, kind: "numeric" });
    }
  }
  for (const term of findTechnicalTerms(value)) {
    if (!isGrounded(term, requirementTextLower) && !hedged) {
      out.push({ field, index, term, kind: "technical-term" });
    }
  }
}

export function checkGrounding(requirementText: string, analysis: RequirementAnalysis): GroundingFinding[] {
  const requirementTextLower = requirementText.toLowerCase();
  const findings: GroundingFinding[] = [];

  checkField("actor", analysis.actor, null, requirementTextLower, findings);
  checkField("feature", analysis.feature, null, requirementTextLower, findings);

  const arrayFields: Array<keyof RequirementAnalysis> = [
    "preconditions",
    "positiveScenarios",
    "negativeScenarios",
    "ambiguities",
  ];
  for (const field of arrayFields) {
    const items = analysis[field] as string[];
    items.forEach((item, index) => checkField(field, item, index, requirementTextLower, findings));
  }

  return findings;
}
