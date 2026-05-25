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
 *   bun run ci/run.ts                        # all fast checks (tracked files)
 *   bun run ci/run.ts --staged               # staged-only checks (pre-commit mode)
 *   bun run ci/run.ts --staged --autofix     # staged + auto-attempt narrow fixes on failure
 *   bun run ci/run.ts --full                 # all checks including slow (bun-audit)
 *   bun run ci/run.ts --check shebang        # single named check
 *   bun run ci/run.ts --list                 # list registered checks
 *   bun run ci/run.ts --autofix-list         # list checks with registered auto-fix
 *
 * --autofix opt-in contract (per GOVERNANCE_RECONCILIATION_ENGINE_V1_CLAUDE §VI):
 *   - Only runs for checks whose registry entry declares auto_fix
 *   - Only attempts safe_class="narrow" fixers (semantic/destructive fixes excluded by design)
 *   - Does NOT auto-stage the resulting modification — conductor reviews the delta and re-stages
 *   - Reports working-tree delta via `git diff --stat` so the modification trail is visible
 *   - Exit 1 even after successful fix, so commit is blocked until conductor re-stages
 */

import { spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");

type CheckScope = "staged" | "always";
type CheckSpeed = "fast" | "slow";

type AutoFixSafetyClass = "narrow" | "destructive";

type AutoFix = {
  // Command to invoke (bare command, not `bun run` wrapper — that's per-script convention)
  command: string;
  args: string[];
  // Env vars to merge in (e.g., PYTHONUTF8=1 for uv-run Python tools)
  env?: Record<string, string>;
  // Safety classification — only "narrow" fixers run under --autofix
  safe_class: AutoFixSafetyClass;
  // Human description of what the fixer does
  description: string;
};

type Check = {
  name: string;
  aliases?: string[];
  script: string;
  scope: CheckScope;
  speed: CheckSpeed;
  description: string;
  auto_fix?: AutoFix;
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
    name: "ignored-source",
    aliases: ["autoignore", "gitignore"],
    script: "ci/checks/ignored-source.ts",
    scope: "staged",
    speed: "fast",
    description: "Ignored source-shaped files in managed roots (allowlist .gitignore drift)",
  },
  {
    name: "blessing-gate",
    script: "ci/checks/blessing-gate.ts",
    scope: "staged",
    speed: "fast",
    description: "Script envelope drift (canonize_blessing) + radiance cross-ref validation",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/canonize_blessing.py", "--target", "scripts", "--apply"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Apply canonical Decorator's Blessing envelope to drifted .py files in scripts/ via canonize_blessing.py --apply. V1 covers scripts/ target only; other blessing-gate targets (mas_mcp/, ankh_atlas/, .codex/, .temple/) require manual canonization.",
    },
  },
  {
    name: "pathfinder",
    aliases: ["link-audit"],
    script: "ci/checks/link-audit.ts",
    scope: "staged",
    speed: "fast",
    description: "Markdown paths, heading/line anchors, offline GitHub/GFM URL shapes, and staged renames",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/link_audit.py", "scan", "--fix"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Auto-resolve broken/disambiguatable markdown links across the repo via link_audit.py scan --fix. Fixes only unique-match cases; ambiguous links remain for conductor judgment.",
    },
  },
  {
    name: "bun-audit",
    script: "ci/checks/bun-audit.ts",
    scope: "always",
    speed: "slow",
    description: "Dependency security audit via bun audit (slow — full mode only)",
  },
  {
    name: "inference-gates",
    script: "ci/checks/inference-gate-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Python 3.14 GPU inference gate ladder status (reads manifest/*.json)",
  },
  {
    name: "terminal-hook",
    script: "ci/checks/terminal-hook-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Terminal session hook health (JSONL merge regression gate + stale _patch:true detector)",
  },
  {
    name: "gh-runs",
    script: "ci/checks/gh-run-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "GitHub Actions run health membrane (reads manifest/gh_runs/index.json — exits 0 if absent)",
  },
  {
    name: "ankh-triple-abstraction",
    script: "ci/checks/ankh-triple-abstraction.ts",
    scope: "always",
    speed: "fast",
    description: "ANKH triple abstraction probe (WHR:MAX conformance + entity topology + compression ratio)",
  },
  {
    name: "lens-refresh",
    script: "ci/checks/lens-refresh.ts",
    scope: "always",
    speed: "slow",
    description: "Refresh all data-plane lenses (git_rot_index, dependabot_index) — Gitological Noise As Structured Data",
  },
];

const STAGED = process.argv.includes("--staged");
const FULL = process.argv.includes("--full");
const LIST = process.argv.includes("--list");
const AUTOFIX = process.argv.includes("--autofix");
const AUTOFIX_LIST = process.argv.includes("--autofix-list");
const CHECK_IDX = process.argv.indexOf("--check");
const SINGLE = CHECK_IDX !== -1 ? process.argv[CHECK_IDX + 1] : null;

if (LIST) {
  console.log("[ci] Registered checks:\n");
  for (const c of CHECKS) {
    const scope = c.scope.padEnd(7);
    const speed = c.speed.padEnd(5);
    const fix = c.auto_fix ? " [autofix]" : "";
    console.log(`  ${c.name.padEnd(18)} [${scope}/${speed}]${fix}  ${c.description}`);
  }
  process.exit(0);
}

if (AUTOFIX_LIST) {
  console.log("[ci] Checks with registered auto-fix:\n");
  const withFix = CHECKS.filter((c) => c.auto_fix);
  if (withFix.length === 0) {
    console.log("  (none)");
  } else {
    for (const c of withFix) {
      const af = c.auto_fix!;
      console.log(`  ${c.name.padEnd(18)} [${af.safe_class}]`);
      console.log(`    command: ${af.command} ${af.args.join(" ")}`);
      console.log(`    purpose: ${af.description}`);
      console.log();
    }
  }
  process.exit(0);
}

function selectChecks(): Check[] {
  if (SINGLE) {
    const found = CHECKS.find((c) => c.name === SINGLE || c.aliases?.includes(SINGLE));
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

function gitWorkingTreeDiffStat(): string {
  const r = spawnSync("git", ["diff", "--stat"], { encoding: "utf8", cwd: REPO_ROOT });
  return (r.stdout ?? "").trim();
}

type AutoFixResult = {
  name: string;
  attempted: boolean;
  fix_command: string;
  fix_output: string;
  fix_exit: number;
  delta_before: string;
  delta_after: string;
  changed: boolean;
};

function runAutoFix(check: Check): AutoFixResult {
  const af = check.auto_fix;
  if (!af) {
    return {
      name: check.name,
      attempted: false,
      fix_command: "",
      fix_output: "[autofix] no auto_fix registered for this check",
      fix_exit: 0,
      delta_before: "",
      delta_after: "",
      changed: false,
    };
  }
  if (af.safe_class !== "narrow") {
    return {
      name: check.name,
      attempted: false,
      fix_command: `${af.command} ${af.args.join(" ")}`,
      fix_output: `[autofix] safe_class=${af.safe_class} not in narrow allowlist — manual fix only`,
      fix_exit: 0,
      delta_before: "",
      delta_after: "",
      changed: false,
    };
  }

  const fix_command = `${af.command} ${af.args.join(" ")}`;
  const delta_before = gitWorkingTreeDiffStat();
  const env = { ...process.env, ...(af.env ?? {}) };
  const r = spawnSync(af.command, af.args, {
    encoding: "utf8",
    cwd: REPO_ROOT,
    env,
  });
  const fix_output = ((r.stdout ?? "") + (r.stderr ?? "")).trim();
  const fix_exit = r.status ?? 1;
  const delta_after = gitWorkingTreeDiffStat();
  const changed = delta_before !== delta_after;
  return {
    name: check.name,
    attempted: true,
    fix_command,
    fix_output,
    fix_exit,
    delta_before,
    delta_after,
    changed,
  };
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
}

console.error(`[ci] ✗ ${failed}/${selected.length} check(s) failed`);

if (!AUTOFIX) {
  process.exit(1);
}

// --autofix branch: attempt registered narrow-class fixes for each failed check
console.log(`\n[autofix] --autofix flag detected; attempting registered narrow-class fixes for ${failed} failure(s)...\n`);

let attempted = 0;
let changed = 0;
const fix_summaries: AutoFixResult[] = [];

for (const r of results) {
  if (r.ok) continue;
  const check = selected.find((c) => c.name === r.name);
  if (!check) continue;
  const af_result = runAutoFix(check);
  fix_summaries.push(af_result);
  if (!af_result.attempted) {
    console.log(`[autofix] ${r.name}: ${af_result.fix_output}`);
    continue;
  }
  attempted++;
  console.log(`[autofix] ${r.name} → ${af_result.fix_command}`);
  if (af_result.fix_exit !== 0) {
    console.log(`[autofix] ${r.name}: fix command exited ${af_result.fix_exit}`);
  }
  if (af_result.changed) {
    changed++;
    console.log(`[autofix] ${r.name}: working-tree CHANGED`);
  } else {
    console.log(`[autofix] ${r.name}: fix command produced no working-tree delta`);
  }
  console.log();
}

if (attempted === 0) {
  console.error(`\n[autofix] No registered narrow-class fixes for any failure. Manual remediation required.`);
  process.exit(1);
}

if (changed === 0) {
  console.error(`\n[autofix] Attempted ${attempted} fix(es); none produced a working-tree change. Manual remediation required.`);
  process.exit(1);
}

console.log(`\n[autofix] Summary: ${attempted} fix(es) attempted, ${changed} produced working-tree changes.`);
console.log(`[autofix] Working-tree delta (post-fix):`);
const final_delta = gitWorkingTreeDiffStat();
if (final_delta) {
  console.log(final_delta.split("\n").map((l) => `  ${l}`).join("\n"));
} else {
  console.log(`  (none)`);
}
console.log(`\n[autofix] Next conductor step:`);
console.log(`  1. Review the working-tree delta above (or run: git diff)`);
console.log(`  2. If satisfied, re-stage: git add -u  (or specific files)`);
console.log(`  3. Re-attempt commit. The pre-commit guard will re-run all checks against the new staged set.`);
console.log(`\n[autofix] Per GOVERNANCE_RECONCILIATION_ENGINE_V1_CLAUDE §VI: auto-fix does NOT auto-stage. The modification trail stays visible. The conductor's keen disposes.`);

// Still exit 1 — the commit is blocked until the conductor re-stages.
process.exit(1);
