export interface AgentConfig {
  agentId: string;
  name: string;
  version: string;
  model: string;
  temperature: number;
  instructions: string;
}

export interface AgentInput {
  input: string;
}

export interface AgentResult {
  agentId: string;
  agentVersion: string;
  output: string;
}

/**
 * A real gap found and fixed while testing this build: the source
 * article's own AgentRuntime takes the CONCRETE LLMClient class as its
 * constructor parameter type. Under strict TypeScript, that means a
 * plain mock object implementing only `generate()` does NOT satisfy
 * that type -- `tsc --strict` rejects it with "Property 'client' is
 * missing in type '...' but required in type 'LLMClient'", because
 * class types in TypeScript are matched structurally INCLUDING their
 * private fields. That directly undermines the article's own stated
 * motivation for having an LLMClient abstraction at all: "particularly
 * useful when we start writing deterministic tests for the testing
 * framework itself." This interface is what AgentRuntime depends on
 * instead -- the real LLMClient class below implements it, and a test
 * double only needs to implement `generate()`, nothing more.
 */
export interface LLMClient {
  generate(instructions: string, input: string, model: string): Promise<string>;
}
