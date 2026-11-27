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
    // Found and fixed while verifying this build: tsc's own dist/
    // output (a compiled copy of every tests/**/*.ts file) was being
    // picked up by Vitest's default include pattern alongside the real
    // source, silently double-running every test. Vitest's default
    // excludes cover node_modules/ but not a project's own build
    // output dir -- this is a real, worthwhile exclusion, not specific
    // to the bug that prompted finding it.
    exclude: ["**/node_modules/**", "**/dist/**"],
  },
});
