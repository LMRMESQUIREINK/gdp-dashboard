import "dotenv/config";
import OpenAI from "openai";
import type { LLMClient as LLMClientContract } from "../types/AgentTypes.js";

export class LLMClient implements LLMClientContract {
  private readonly client: OpenAI;

  constructor() {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is not configured.");
    }

    this.client = new OpenAI({
      apiKey,
      baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/",
    });
  }

  async generate(instructions: string, input: string, model: string): Promise<string> {
    const response = await this.client.chat.completions.create({
      model,
      messages: [
        { role: "system", content: instructions },
        { role: "user", content: input },
      ],
    });

    return response.choices[0]?.message?.content ?? "";
  }
}
