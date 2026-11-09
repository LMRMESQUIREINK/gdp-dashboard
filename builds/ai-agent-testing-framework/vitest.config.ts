import { defineConfig } from "vitest/config";

// The source article's own shown vitest.config.ts has one extra closing
// brace (an unbalanced object literal: 3 "{" to 4 "}") -- reproduced and
// confirmed as a real SyntaxError ("missing ) after argument list"), not
// a markdown rendering artifact. See /notes/ai-agent-testing-framework-
// analysis.md for the exact repro. Fixed below.
export default defineConfig({
  test: {
    testTimeout: 50000,
    fileParallelism: false, // runs one test file at a time
  },
});
