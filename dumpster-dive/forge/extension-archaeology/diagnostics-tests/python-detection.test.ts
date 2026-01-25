// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: python-detection.test.ts                      ║
// ║  TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

import { test, expect } from "bun:test";
import { execSync } from "child_process";

test("python version detection regex works", () => {
  process.env.PYTHONIOENCODING = "utf-8";

  const output = execSync("uv run python --version", {
    encoding: "utf-8",
    timeout: 5000,
  }).trim();

  const match = output.match(/Python\s+(\d+\.\d+(?:\.\d+)?)/);

  expect(match).not.toBeNull();
  expect(match![1]).toMatch(/^\d+\.\d+/);
});

test("python detection handles stdout and stderr", () => {
  process.env.PYTHONIOENCODING = "utf-8";

  const output = execSync("uv run python --version 2>&1", {
    encoding: "utf-8",
  }).trim();

  expect(output).toMatch(/Python\s+\d+\.\d+/);
});
