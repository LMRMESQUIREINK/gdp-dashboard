import { describe, it, expect } from "vitest";
import { AgentConfigLoader } from "../../src/config/AgentConfigLoader.js";

describe("AgentConfigLoader", () => {
  it("loads the real requirement_analyzer.md and parses its YAML front matter correctly", () => {
    const loader = new AgentConfigLoader();
    const config = loader.load("./config/agents/requirement_analyzer.md");

    expect(config.agentId).toBe("requirement-analyzer");
    expect(config.name).toBe("Requirement Analyzer Agent");
    expect(config.version).toBe("1.0.0");
    expect(config.model).toBe("gemini-3.6-flash");
    expect(config.temperature).toBe(0);
  });

  it("captures the Markdown body as instructions, trimmed, with the front matter stripped out", () => {
    const loader = new AgentConfigLoader();
    const config = loader.load("./config/agents/requirement_analyzer.md");

    expect(config.instructions).toContain("# Role");
    expect(config.instructions).toContain("software requirement analysis agent");
    // The front matter's own fields must never leak into the instructions body.
    expect(config.instructions).not.toContain("agentId:");
    expect(config.instructions.startsWith("---")).toBe(false);
  });

  it("resolves a relative path, matching path.resolve()'s real behavior", () => {
    const loader = new AgentConfigLoader();
    const relative = loader.load("./config/agents/requirement_analyzer.md");
    const alsoRelative = loader.load("config/agents/requirement_analyzer.md");

    expect(relative).toEqual(alsoRelative);
  });

  it("throws a real Node fs error for a missing file, rather than returning a malformed config silently", () => {
    const loader = new AgentConfigLoader();
    expect(() => loader.load("./config/agents/does-not-exist.md")).toThrow();
  });
});
