import { AgentConfigLoader } from "./config/AgentConfigLoader.js";
import { AgentRuntime } from "./runtime/AgentRuntime.js";
import { LLMClient } from "./llm/LLMClient.js";

async function main() {
  const loader = new AgentConfigLoader();
  const config = loader.load("./config/agents/requirement_analyzer.md");

  const runtime = new AgentRuntime(new LLMClient());

  const result = await runtime.run(config, {
    input: "The user should be able to reset their password using their registered email address.",
  });

  console.log(result);
}

main().catch(console.error);
