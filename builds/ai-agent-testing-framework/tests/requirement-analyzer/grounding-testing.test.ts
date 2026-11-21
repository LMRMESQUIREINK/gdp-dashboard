import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { checkGrounding } from "../../src/grounding/checkGrounding.js";
import { evaluateRequirementAnalyzer } from "../../src/oracle/requirementAnalyzerOracle.js";
import { evaluateContradiction } from "../../src/oracle/contradictionOracle.js";
import type { LLMClient, AgentConfig, AgentResult } from "../../src/types/AgentTypes.js";

/**
 * Part 8 of the source series ("Testing Grounding: Can an AI Agent Stay
 * Within the Evidence?") -- TC007 (sparse evidence), TC008 (explicit
 * evidence), TC009 (conflicting evidence), TC010 (unsupported
 * inference). See /notes/ai-agent-testing-framework-part8-analysis.md.
 *
 * The article's own central move: a naive "the word must not appear"
 * assertion failed against the agent's own correct TC007 output, for
 * the same reason as Parts 6-7's lessons -- the word was mentioned as a
 * hedged possibility ("...are not specified"), not claimed as fact. The
 * article's own fix was a set of hand-written, per-claim regexes
 * ("supports jpeg", "stored in s3", etc.) -- this project's existing
 * checkGrounding() (hedge-aware term/numeric detection, generalized
 * across Parts 2/6/7) already implements the SAME underlying principle
 * more generally, so this round extends its term list rather than
 * writing six new one-off regexes per TC010 claim.
 */

const EXPECTED_AGENT_ID = "requirement-analyzer";

class MockLLMClient implements LLMClient {
  constructor(private readonly response: string) {}
  async generate(): Promise<string> {
    return this.response;
  }
}

async function runRealPipeline(input: string, mockResponse: string): Promise<AgentResult> {
  const loader = new AgentConfigLoader();
  const config: AgentConfig = loader.load("./config/agents/requirement_analyzer.md");
  const runtime = new AgentRuntime(new MockLLMClient(mockResponse));
  return runtime.run(config, { input });
}

describe("TC007 -- sparse evidence (the real article output, hedged format mentions)", () => {
  const INPUT = "The system should allow users to upload a profile picture.";
  const REAL_RESPONSE = JSON.stringify({
    actor: "user",
    feature: "Upload a profile picture",
    preconditions: [],
    positiveScenarios: ["User uploads a profile picture successfully."],
    negativeScenarios: [],
    ambiguities: [
      "Allowed image file formats (e.g., JPEG, PNG) are not specified.",
      "Maximum and minimum file size limits are not specified.",
      "Image resolution or dimension constraints are not specified.",
      "Behavior when a user already has an existing profile picture (e.g., overwrite) is not specified.",
      "User authentication or authorization prerequisites are not specified.",
    ],
  });

  it("the real output passes checkGrounding() and the full requirementAnalyzerOracle cleanly -- JPEG/PNG/authentication are hedged mentions, not claims", async () => {
    const result = await runRealPipeline(INPUT, REAL_RESPONSE);
    const parsed = JSON.parse(result.output);
    expect(checkGrounding(INPUT, parsed)).toEqual([]);

    const verdict = evaluateRequirementAnalyzer({
      result,
      requirementText: INPUT,
      expectedAgentId: EXPECTED_AGENT_ID,
    });
    expect(verdict.passed).toBe(true);
  });

  it("literal reproduction of the article's own flagged-as-too-strict assertion -- a naive 'must not contain jpeg/png' check really does fail this correct output", async () => {
    const result = await runRealPipeline(INPUT, REAL_RESPONSE);
    const serializedOutput = result.output.toLowerCase();
    expect(serializedOutput).toMatch(/jpeg|png/);
  });

  it("DISCRIMINATION CHECK: a planted response that actually CLAIMS JPEG/PNG support (unhedged) is correctly caught -- now that the term list covers image formats", async () => {
    const hallucinated = JSON.stringify({
      actor: "user",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: ["The system supports JPEG and PNG image formats."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, hallucinated);
    const verdict = evaluateRequirementAnalyzer({
      result,
      requirementText: INPUT,
      expectedAgentId: EXPECTED_AGENT_ID,
    });
    expect(verdict.passed).toBe(false);
    expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
  });
});

describe("TC008 -- explicit evidence must not be lost or expanded", () => {
  const INPUT =
    "The system should allow users to upload a profile picture. The picture must be stored in Amazon S3.";

  it("explicit S3 evidence is grounded -- an unhedged mention of S3 is correctly NOT flagged, because it's literally present in the requirement", async () => {
    const response = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: ["The picture must be stored in Amazon S3."],
      positiveScenarios: ["User uploads a profile picture, which is stored in Amazon S3."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, response);
    const parsed = JSON.parse(result.output);
    expect(checkGrounding(INPUT, parsed)).toEqual([]);
  });

  it("literal reproduction of the article's own appropriate lexical assertion -- S3 evidence really must survive into the serialized output", async () => {
    const response = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: ["The picture must be stored in Amazon S3."],
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, response);
    const serializedOutput = result.output.toLowerCase();
    expect(serializedOutput).toMatch(/s3/i);
  });

  it("DISCRIMINATION CHECK: an overly cautious agent that LOSES the given S3 evidence (claims it's unspecified) is caught by the lexical presence check -- 'don't invent' is not the only failure mode", async () => {
    const overlyCautious = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: ["User uploads a profile picture successfully."],
      negativeScenarios: [],
      ambiguities: ["The storage mechanism is not specified."],
    });
    const result = await runRealPipeline(INPUT, overlyCautious);
    const serializedOutput = result.output.toLowerCase();
    // The article's own named failure mode: this LOOKS safe but is
    // actually wrong, because the requirement DID specify the storage
    // mechanism. The agent discarded supported evidence.
    expect(serializedOutput).not.toMatch(/s3/i);
  });

  it("DISCRIMINATION CHECK: unsupported expansion beyond the given S3 evidence (bucket name, region, encryption) is correctly caught", async () => {
    const overExpanded = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [
        "The bucket name is user-uploads and the AWS region is us-east-1, with encryption enabled.",
      ],
      positiveScenarios: ["User uploads a profile picture, which is stored in Amazon S3."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, overExpanded);
    const parsed = JSON.parse(result.output);
    const findings = checkGrounding(INPUT, parsed);
    expect(findings.some((f) => f.term === "bucket name")).toBe(true);
    expect(findings.some((f) => f.term === "AWS region")).toBe(true);
    expect(findings.some((f) => f.term === "encryption")).toBe(true);
  });
});

describe("TC009 -- conflicting evidence (contradictionOracle)", () => {
  const INPUT =
    "The system should allow users to upload a profile picture. " +
    "The profile picture must be stored locally on the user's device. " +
    "The profile picture must be stored in Amazon S3.";

  it("a response that surfaces the conflict (constructed for this test -- the article gives no literal quoted TC009 output, only its desired/undesired behaviors) passes", async () => {
    const conflictSurfaced = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: [],
      negativeScenarios: [],
      ambiguities: [
        "The requirement contains conflicting storage instructions: the picture must be stored locally AND in Amazon S3. This is inconsistent, and the requirement does not specify which applies or whether both do.",
      ],
    });
    const result = await runRealPipeline(INPUT, conflictSurfaced);
    const verdict = evaluateContradiction({ result });
    expect(verdict.passed).toBe(true);
  });

  it("DISCRIMINATION CHECK: the article's own first named 'tempting but wrong' response (picks S3) is caught -- verified directly that the article's OWN given regex does NOT catch this, before broadening the pattern list here", async () => {
    const silentlyResolvedToS3 = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: ["The system must store the profile picture in Amazon S3."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, silentlyResolvedToS3);
    const verdict = evaluateContradiction({ result });
    expect(verdict.passed).toBe(false);
    expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
  });

  it("DISCRIMINATION CHECK: the article's own second named 'tempting but wrong' response (invents a local-then-S3 architecture) is also caught", async () => {
    const silentlyResolvedToArchitecture = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: ["The image is stored locally and then uploaded to S3."],
      negativeScenarios: [],
      ambiguities: [],
    });
    const result = await runRealPipeline(INPUT, silentlyResolvedToArchitecture);
    const verdict = evaluateContradiction({ result });
    expect(verdict.passed).toBe(false);
    expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
  });
});

describe("TC010 -- unsupported inference: six named claim categories, caught by one generalized mechanism rather than six hand-written regexes", () => {
  const INPUT = "The system should allow users to upload a profile picture.";

  const namedClaims: Array<{ label: string; scenario: string }> = [
    { label: "authentication claim", scenario: "Users must authenticate before uploading a picture." },
    { label: "format-support claim", scenario: "The system supports JPEG and PNG image formats." },
    { label: "file-size claim", scenario: "The maximum file size is 5 MB." },
    { label: "storage claim", scenario: "The image is stored in S3." },
    { label: "UI-interaction claim", scenario: "The user clicks the upload button to select a file." },
    { label: "processing claim", scenario: "The system automatically generates a thumbnail." },
  ];

  for (const { label, scenario } of namedClaims) {
    it(`catches the ${label} ("${scenario}") as an unsupported-claim Forbidden violation`, async () => {
      const response = JSON.stringify({
        actor: "User",
        feature: "Upload a profile picture",
        preconditions: [],
        positiveScenarios: [scenario],
        negativeScenarios: [],
        ambiguities: [],
      });
      const result = await runRealPipeline(INPUT, response);
      const verdict = evaluateRequirementAnalyzer({
        result,
        requirementText: INPUT,
        expectedAgentId: EXPECTED_AGENT_ID,
      });
      expect(verdict.passed).toBe(false);
      expect(verdict.findings.some((f) => f.kind === "forbidden-violated")).toBe(true);
    });
  }

  it("the real, correct TC007-style response (recognizing all six of these as unknowns, not asserting any of them) passes cleanly", async () => {
    const correct = JSON.stringify({
      actor: "User",
      feature: "Upload a profile picture",
      preconditions: [],
      positiveScenarios: ["User uploads a profile picture successfully."],
      negativeScenarios: [],
      ambiguities: [
        "Allowed image file formats (e.g., JPEG, PNG) are not specified.",
        "Maximum file size is not specified.",
        "Whether authentication is required is not specified.",
        "Whether the image is stored in S3 or elsewhere is not specified.",
        "The exact upload interaction (e.g., upload button) is not specified.",
        "Whether a thumbnail is generated is not specified.",
      ],
    });
    const result = await runRealPipeline(INPUT, correct);
    const verdict = evaluateRequirementAnalyzer({
      result,
      requirementText: INPUT,
      expectedAgentId: EXPECTED_AGENT_ID,
    });
    expect(verdict.passed).toBe(true);
  });
});
