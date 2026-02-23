// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: gpu-parsing.test.ts                           ║
// ║ TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE                                                 ║
// ║ Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):                                      ║
// ║   (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════

import { test, expect } from "bun:test";
import { execSync } from "child_process";

test.skipIf(!hasNvidiaGPU())("gpu stats parsing works", () => {
  const output = execSync(
    "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits",
    { encoding: "utf-8", timeout: 3000 }
  ).trim();

  const [used, total] = output.split(",").map((s) => parseInt(s.trim()));

  expect(used).toBeGreaterThan(0);
  expect(total).toBeGreaterThan(0);
  expect(used).toBeLessThanOrEqual(total);
});

test.skipIf(!hasNvidiaGPU())("gpu percentage calculation is valid", () => {
  const output = execSync(
    "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits",
    { encoding: "utf-8", timeout: 3000 }
  ).trim();

  const [used, total] = output.split(",").map((s) => parseInt(s.trim()));
  const percent = (used / total) * 100;

  expect(percent).toBeGreaterThanOrEqual(0);
  expect(percent).toBeLessThanOrEqual(100);
});

function hasNvidiaGPU(): boolean {
  try {
    execSync("nvidia-smi --version", { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}
