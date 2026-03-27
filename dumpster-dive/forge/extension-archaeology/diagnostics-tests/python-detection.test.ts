// @SID: FORGE_PYTHON_DETECTION_TEST_V1
// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: python-detection.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_PYTHON_DETECT_V1 @Shabti Test Script @Purpose Validates Python version detection regex. */

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
