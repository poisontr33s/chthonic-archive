#!/usr/bin/env bun
// @SID: CI_CHECK_BLESSING_GATE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/blessing-gate.ts
// ║ Local CI equivalent of .github/workflows/blessing-gate.yml.off
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Runs canonize_blessing.py + radiance_validate.py across canonical targets.
// ║
// ║ Staged mode (--staged):
// ║   Only activates when .py files are in the staged Added set.
// ║   Runs all targets — canonize_blessing validates envelopes repo-wide
// ║   because the drift is structural, not file-local.
// ║
// ║ Default mode:
// ║   Always runs all targets.
// ╚════════════════════════════════════════════════════════════════════════════

import { spawn, spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const STAGED = process.argv.includes("--staged");

const CANONIZE_TARGETS: string[][] = [
  ["scripts/canonize_blessing.py", "--check", "--target", "scripts", "-v"],
  ["scripts/canonize_blessing.py", "--check", "--recursive", "--target", "mas_mcp", "-v"],
  ["scripts/canonize_blessing.py", "--check", "--recursive", "--target", "ankh_atlas", "-v"],
  ["scripts/canonize_blessing.py", "--check", "--recursive", "--target", ".codex", "-v"],
  ["scripts/canonize_blessing.py", "--check", "--recursive", "--target", ".temple", "-v"],
];

function uvRun(args: string[]): Promise<{ ok: boolean; output: string }> {
  return new Promise((res) => {
    const child = spawn("uv", ["run", "--no-sync", ...args], {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" },
    });
    let out = "";
    child.stdout.on("data", (d: Buffer) => { out += d.toString(); });
    child.stderr.on("data", (d: Buffer) => { out += d.toString(); });
    child.on("error", (e: Error) => res({ ok: false, output: e.message }));
    child.on("close", (code: number | null) => res({ ok: (code ?? 1) === 0, output: out.trim() }));
  });
}

function stagedPyFiles(): string[] {
  const result = spawnSync(
    "git",
    ["diff", "--cached", "--name-only", "--diff-filter=A"],
    { encoding: "utf8", cwd: REPO_ROOT }
  );
  return (result.stdout ?? "")
    .split("\n")
    .filter((f) => f.endsWith(".py"))
    .filter((f) => !f.replace(/\\/g, "/").startsWith("birdcage/"));
}

// In staged mode: gate on whether any .py files were Added
if (STAGED) {
  const pyFiles = stagedPyFiles();
  if (pyFiles.length === 0) {
    console.log("[blessing-gate] No staged .py Added files — skipping");
    process.exit(0);
  }
  console.log(`[blessing-gate] ${pyFiles.length} staged .py file(s) — running checks`);
}

let failed = 0;

// Run all envelope-drift targets + radiance in parallel
console.log("[blessing-gate] Running all checks in parallel...");
const [canonizeResults, radiance] = await Promise.all([
  Promise.all(
    CANONIZE_TARGETS.map(async (target) => {
      const label = target[target.indexOf("--target") + 1] ?? "?";
      const r = await uvRun(target);
      return { label, r };
    })
  ),
  uvRun(["scripts/radiance_validate.py"]),
]);

// Print envelope results
console.log("[blessing-gate] Envelope drift checks...");
for (const { label, r } of canonizeResults) {
  if (r.output) {
    for (const line of r.output.split("\n")) {
      if (line.trim()) console.log(`  [${label}] ${line}`);
    }
  }
  if (!r.ok) {
    console.error(`[blessing-gate] ✗ envelope drift in target: ${label}`);
    failed++;
  }
}

// Print radiance result
console.log("[blessing-gate] Radiance cross-reference validation...");
if (radiance.output) {
  for (const line of radiance.output.split("\n")) {
    if (line.trim()) console.log(`  [radiance] ${line}`);
  }
}
if (!radiance.ok) {
  console.error("[blessing-gate] ✗ radiance_validate failed");
  failed++;
}

if (failed > 0) {
  console.error(`[blessing-gate] ✗ ${failed} check(s) failed`);
  process.exit(1);
} else {
  console.log("[blessing-gate] ✓ All envelope + radiance checks passed");
  process.exit(0);
}
