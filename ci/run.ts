#!/usr/bin/env bun
// @SID: CI_RUNNER_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/run.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Standalone — local CI orchestrator, called by pre-commit hook)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/run.ts — Registry-driven local CI orchestrator for chthonic-archive.
 *
 * Each check declares scope (staged | always) and speed (fast | slow).
 * Checks run in parallel. Exits 1 if any check fails.
 *
 * Usage:
 *   bun run ci/run.ts              # all fast checks (tracked files)
 *   bun run ci/run.ts --staged     # staged-only checks (pre-commit mode)
 *   bun run ci/run.ts --full       # all checks including slow (bun-audit)
 *   bun run ci/run.ts --check shebang   # single named check
 *   bun run ci/run.ts --list       # list registered checks
 */

import { spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");

type CheckScope = "staged" | "always";
type CheckSpeed = "fast" | "slow";

type Check = {
  name: string;
  script: string;
  scope: CheckScope;
  speed: CheckSpeed;
  description: string;
};

const CHECKS: Check[] = [
  {
    name: "shebang",
    script: "scripts/shebang-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "Displaced shebangs in .ts files (bun SyntaxError guard)",
  },
  {
    name: "python-headers",
    script: "ci/checks/python-headers.ts",
    scope: "staged",
    speed: "fast",
    description: "Python canonical headers: shebang + UTF-8 encoding line",
  },
  {
    name: "sid-envelope",
    script: "ci/checks/sid-envelope.ts",
    scope: "staged",
    speed: "fast",
    description: "@SID presence in new scripts/*.ts and ci/**/*.ts (Added only)",
  },
  {
    name: "uv-guard",
    script: "ci/checks/uv-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "No bare python/python3 invocations — use uv run",
  },
  {
    name: "blessing-gate",
    script: "ci/checks/blessing-gate.ts",
    scope: "staged",
    speed: "fast",
    description: "Script envelope drift (canonize_blessing) + radiance cross-ref validation",
  },
  {
    name: "bun-audit",
    script: "ci/checks/bun-audit.ts",
    scope: "always",
    speed: "slow",
    description: "Dependency security audit via bun audit (slow — full mode only)",
  },
];

const STAGED = process.argv.includes("--staged");
const FULL = process.argv.includes("--full");
const LIST = process.argv.includes("--list");
const CHECK_IDX = process.argv.indexOf("--check");
const SINGLE = CHECK_IDX !== -1 ? process.argv[CHECK_IDX + 1] : null;

if (LIST) {
  console.log("[ci] Registered checks:\n");
  for (const c of CHECKS) {
    const scope = c.scope.padEnd(7);
    const speed = c.speed.padEnd(5);
    console.log(`  ${c.name.padEnd(18)} [${scope}/${speed}]  ${c.description}`);
  }
  process.exit(0);
}

function selectChecks(): Check[] {
  if (SINGLE) {
    const found = CHECKS.find((c) => c.name === SINGLE);
    if (!found) {
      console.error(`[ci] ✗ Unknown check: "${SINGLE}". Run --list for available checks.`);
      process.exit(1);
    }
    return [found];
  }
  if (STAGED) return CHECKS.filter((c) => c.scope === "staged");
  if (FULL) return CHECKS;
  return CHECKS.filter((c) => c.speed === "fast");
}

function runCheck(check: Check): { name: string; ok: boolean; output: string } {
  const scriptPath = resolve(REPO_ROOT, check.script);
  const args: string[] = STAGED ? ["--staged"] : [];

  const result = spawnSync("bun", ["run", scriptPath, ...args], {
    encoding: "utf8",
    cwd: REPO_ROOT,
    env: { ...process.env },
  });

  const output = ((result.stdout ?? "") + (result.stderr ?? "")).trim();
  const ok = result.status === 0;
  return { name: check.name, ok, output };
}

const selected = selectChecks();
const modeLabel = STAGED ? "--staged" : FULL ? "--full" : SINGLE ? `--check ${SINGLE}` : "default";
console.log(`[ci] ${selected.length} check(s) | mode: ${modeLabel}\n`);

const results = await Promise.all(selected.map(runCheck));

let failed = 0;
for (const r of results) {
  if (r.output) console.log(r.output);
  if (!r.ok) {
    failed++;
    console.error(`[ci] ✗ ${r.name} FAILED`);
  }
}

console.log();
if (failed === 0) {
  console.log(`[ci] ✓ All ${selected.length} check(s) passed`);
  process.exit(0);
} else {
  console.error(`[ci] ✗ ${failed}/${selected.length} check(s) failed`);
  process.exit(1);
}
