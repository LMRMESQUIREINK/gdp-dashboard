import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";
import { AgentRuntime } from "../../src/runtime/AgentRuntime.js";
import { parseAgentOutput } from "../../src/output/parseAgentOutput.js";
import { checkGrounding } from "../../src/grounding/checkGrounding.js";
import type { LLMClient, AgentConfig } from "../../src/types/AgentTypes.js";

/**
 * This is the deterministic test the source article's own prose names as
 * the goal of having an LLMClient abstraction at all ("particularly
 * useful when we start writing deterministic tests for the testing
 * framework itself") -- but the article's own shown code doesn't
 * actually deliver it: AgentRuntime's real constructor types against
 * the CONCRETE LLMClient class, which a plain mock cannot satisfy under
 * strict TypeScript (see /notes/ai-agent-testing-framework-analysis.md
 * for the exact reproduced tsc error). This test is only possible
 * because this build's own fix -- AgentRuntime now depends on the
 * LLMClient INTERFACE from AgentTypes.ts -- actually closes that gap.
 *
 * No live Gemini API access from this sandbox (same standing egress
 * restriction as every other build in this project), so this proves
 * the real AgentConfigLoader -> AgentRuntime wiring end-to-end against
 * a scripted mock, the same "mocked client" convention this project's
 * Python builds have used throughout, applied here for the first time
 * to a TypeScript/Vitest build.
 */
class MockLLMClient implements LLMClient {
  public calls: Array<{ instructions: string; input: string; model: string }> = [];
  constructor(private readonly response: string) {}

  async generate(instructions: string, input: string, model: string): Promise<string> {
    this.calls.push({ instructions, input, model });
    return this.response;
  }
}

describe("requirement-analyzer agent (TC001-style, mocked LLMClient)", () => {
  it("loads the real agent config, runs it through AgentRuntime, and returns a well-formed AgentResult", async () => {
    const loader = new AgentConfigLoader();
    const config: AgentConfig = loader.load("./config/agents/requirement_analyzer.md");

    // The REAL JSON schema from requirement_analyzer.md's own Output
    // Requirements section, given in full for the first time in Part 2
    // (Part 1 only showed a fragment of this agent's instructions, so
    // this project's earlier placeholder used a different, prose-based
    // contract -- see /notes/ai-agent-testing-framework-part2-analysis.md).
    const mockClient = new MockLLMClient(
      JSON.stringify({
        actor: "User",
        feature: "Password reset using email",
        preconditions: [],
        positiveScenarios: [
          "User requests a password reset using email and successfully resets the password.",
        ],
        negativeScenarios: [],
        ambiguities: [],
      })
    );
    const runtime = new AgentRuntime(mockClient);

    const result = await runtime.run(config, {
      input: "The user should be able to reset their password using their registered email address.",
    });

    expect(result).toBeDefined();
    expect(result.agentId).toBe("requirement-analyzer");
    expect(result.agentVersion).toBe("1.0.0");
    expect(result.output).toBeTruthy();

    // The real end-to-end pipeline this round's two new modules make
    // possible: the raw string output enforced against the agent's own
    // Output Requirements contract, then checked for grounding.
    const parsed = parseAgentOutput(result.output);
    expect(parsed.actor).toBe("User");
    expect(
      checkGrounding("The user should be able to reset their password using their registered email address.", parsed)
    ).toEqual([]);
  });

  it("passes the agent's REAL instructions and the caller's input through to the LLM client unmodified", async () => {
    const loader = new AgentConfigLoader();
    const config = loader.load("./config/agents/requirement_analyzer.md");
    const mockClient = new MockLLMClient("mocked output");
    const runtime = new AgentRuntime(mockClient);

    await runtime.run(config, { input: "A specific requirement text." });

    expect(mockClient.calls).toHaveLength(1);
    expect(mockClient.calls[0].instructions).toBe(config.instructions);
    expect(mockClient.calls[0].input).toBe("A specific requirement text.");
    expect(mockClient.calls[0].model).toBe("gemini-3.6-flash");
  });

  it("surfaces an empty string gracefully if the LLM returns no content, instead of throwing", async () => {
    const loader = new AgentConfigLoader();
    const config = loader.load("./config/agents/requirement_analyzer.md");
    const mockClient = new MockLLMClient("");
    const runtime = new AgentRuntime(mockClient);

    const result = await runtime.run(config, { input: "x" });
    expect(result.output).toBe("");
  });

  it("the mock's call count proves the runtime delegates to the LLM client exactly once per run -- never caches or fabricates a result", async () => {
    const loader = new AgentConfigLoader();
    const config = loader.load("./config/agents/requirement_analyzer.md");
    const mockClient = new MockLLMClient("first");
    const runtime = new AgentRuntime(mockClient);

    await runtime.run(config, { input: "a" });
    await runtime.run(config, { input: "b" });

    expect(mockClient.calls).toHaveLength(2);
    expect(mockClient.calls.map((c) => c.input)).toEqual(["a", "b"]);
  });
});
