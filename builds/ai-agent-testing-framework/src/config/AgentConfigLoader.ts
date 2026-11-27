import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import type { AgentConfig } from "../types/AgentTypes.js";

export class AgentConfigLoader {
  load(agentPath: string): AgentConfig {
    const absolutePath = path.resolve(agentPath);
    const fileContent = fs.readFileSync(absolutePath, "utf-8");
    const parsed = matter(fileContent);

    return {
      agentId: parsed.data.agentId,
      name: parsed.data.name,
      version: parsed.data.version,
      model: parsed.data.model,
      temperature: parsed.data.temperature,
      instructions: parsed.content.trim(),
    };
  }
}
