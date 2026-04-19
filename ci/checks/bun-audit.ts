#!/usr/bin/env bun
// @SID: CI_CHECK_BUN_AUDIT_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/bun-audit.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/bun-audit.ts — Dependency security audit wrapper.
 *
 * Runs `bun audit` with the repo's known-ignore list.
 * SLOW — not suitable for pre-commit. Run with: bun run ci --full
 *
 * Known ignored advisories (all reviewed and accepted):
 *   GHSA-26pp-8wgv-hjvm, GHSA-r5rp-j6wh-rvv4, GHSA-xpcf-pg52-r92g,
 *   GHSA-xf4j-xp2r-rqqx, GHSA-wmmm-f939-6g9c
 *
 * Usage:
 *   bun run ci/checks/bun-audit.ts
 */

import { spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");

// Known-accepted advisories — reviewed and suppressed
const IGNORED = [
  "GHSA-26pp-8wgv-hjvm",
  "GHSA-r5rp-j6wh-rvv4",
  "GHSA-xpcf-pg52-r92g",
  "GHSA-xf4j-xp2r-rqqx",
  "GHSA-wmmm-f939-6g9c",
];

const ignoreArgs = IGNORED.flatMap((id) => ["--ignore", id]);

console.log("[bun-audit] Running dependency security audit...");

const result = spawnSync("bun", ["audit", ...ignoreArgs], {
  encoding: "utf8",
  cwd: REPO_ROOT,
  env: { ...process.env },
});

const output = ((result.stdout ?? "") + (result.stderr ?? "")).trim();
if (output) console.log(output);

if (result.status === 0) {
  console.log("[bun-audit] ✓ No unacknowledged vulnerabilities");
  process.exit(0);
} else {
  console.error("[bun-audit] ✗ Audit failed — review output above");
  process.exit(1);
}
