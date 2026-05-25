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

// Deliberate exclusion — check could theoretically have an auto-fix but doesn't,
// for one of these reasons. Surfaced via --autofix-list so the conductor sees
// the full landscape: what's fixable AND what's deliberately manual + why.
type NoAutoFixReason = {
  reason:
    | "semantic"          // fix requires conductor judgment (SID naming, allowlist choice)
    | "destructive"       // fix could break things (package upgrades, force-renames)
    | "no_tool"           // no canonical fix tool exists in repo
    | "wrong_layer"       // fix tooling exists but doesn't address this check's failure mode
    | "read_only_health"; // check is read-only health probe; no fix concept applies
  explanation: string;
  manual_remediation?: string;
};

type Check = {
  name: string;
  aliases?: string[];
  script: string;
  scope: CheckScope;
  speed: CheckSpeed;
  description: string;
  auto_fix?: AutoFix;
  no_auto_fix?: NoAutoFixReason;
};

const CHECKS: Check[] = [
  {
    name: "shebang",
    script: "scripts/shebang-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "Displaced shebangs in .ts files (bun SyntaxError guard)",
    no_auto_fix: {
      reason: "no_tool",
      explanation: "No dedicated .ts shebang-relocator exists. scripts/fix_headers.py handles .py files only.",
      manual_remediation: "Open the offending .ts file and move `#!/usr/bin/env bun` to line 1 (or remove if not an entry-point script).",
    },
  },
  {
    name: "python-headers",
    script: "ci/checks/python-headers.ts",
    scope: "staged",
    speed: "fast",
    description: "Python canonical headers: shebang + UTF-8 encoding line",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/fix_headers.py", "scripts/"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Enforce canonical shebang + encoding on header-bearing files in scripts/ via fix_headers.py (handles .py / .ps1 / .sh by extension). V1.1 scope-correction: fix_headers.py default is repo-wide which over-fixes ~50 files in probes/apps/dumpster-dive/extensions/. Gate restricts to scripts/. For broader fixing, invoke fix_headers.py directly with desired paths.",
    },
  },
  {
    name: "sid-envelope",
    script: "ci/checks/sid-envelope.ts",
    scope: "staged",
    speed: "fast",
    description: "@SID presence in new scripts/*.ts and ci/**/*.ts (Added only)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "@SID values are semantic identities — each file's SID must be hand-chosen to encode its DOMAIN_NAME_V<n> shape (per ALL_CAPS regex at ci/checks/sid-envelope.ts:57). scripts/lib/stamp_sid.py exists but is PS1-only and stamps a SCRIPT_<UPPER>_V1 placeholder pattern — not appropriate for .py/.ts where SIDs encode meaningful domain classification (TOOL_*, CI_CHECK_*, LIB_*, etc.).",
      manual_remediation: "For each missing-SID file: add `# @SID: <DOMAIN_NAME>_V1` on line 2 (.py/.sh/.ps1) or `// @SID: <DOMAIN_NAME>_V1` (.ts). For malformed SIDs: rename to match the ALL_CAPS_DOMAIN_V<n> regex AND update any cross-references via `chthonic resolve --list` to find downstream consumers.",
    },
  },
  {
    name: "uv-guard",
    script: "ci/checks/uv-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "No bare python/python3 invocations — use uv run",
    no_auto_fix: {
      reason: "wrong_layer",
      explanation: "scripts/uv_autofix.py exists but it auto-installs missing Python deps (opt-in via $env:CHTHONIC_UV_AUTOFIX=1) — different purpose. Mechanical prepending of `uv run` to bare `python` invocations is unsafe inside docstring usage examples (would corrupt the doc) and inside .sh/.ps1 shebang lines.",
      manual_remediation: "Open the offending file at the reported line. If the bare `python` is in executable code, prefix with `uv run`. If it's in a docstring/comment usage example, prefix with `uv run` there too for consistency. The check is advisory for Modified files; only Added files block the commit.",
    },
  },
  {
    name: "ignored-source",
    aliases: ["autoignore", "gitignore"],
    script: "ci/checks/ignored-source.ts",
    scope: "staged",
    speed: "fast",
    description: "Ignored source-shaped files in managed roots (allowlist .gitignore drift)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "Resolution requires a conductor decision: either add a narrow `!path` allowlist entry to .gitignore (per docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md), move the file to an already-allowed source lane, OR confirm the file should genuinely stay ignored and delete it. Auto-adding allowlist entries silently broadens the gitignore contract.",
      manual_remediation: "Run `git check-ignore -v <path>` to see which rule matches. Then either: (a) add narrow `!path` allowlist + any required parent-dir allowlists to .gitignore, (b) move the file into an existing allowlisted directory, or (c) delete the file if it's debris.",
    },
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
    no_auto_fix: {
      reason: "destructive",
      explanation: "Auto-fixing would require `bun update <pkg>` which can introduce breaking changes via SemVer minor/major bumps. Vulnerability remediation needs conductor judgment on which packages to upgrade vs. accept-risk vs. patch.",
      manual_remediation: "Read the audit report. For high-severity issues, `bun update <pkg>` (single package) and run tests. For broader vulns, consider `bun update` repo-wide but verify nothing breaks. Dependabot PRs on the GitHub side often handle this automatically.",
    },
  },
  {
    name: "inference-gates",
    script: "ci/checks/inference-gate-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Python 3.14 GPU inference gate ladder status (reads manifest/*.json)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe reading manifest/*.json. Failures indicate upstream gate state changes; no in-repo fix concept applies.",
    },
  },
  {
    name: "terminal-hook",
    script: "ci/checks/terminal-hook-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Terminal session hook health (JSONL merge regression gate + stale _patch:true detector)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe over session JSONL files. Failures indicate hook regression; remediation is in the hook source (not in this check's scope).",
    },
  },
  {
    name: "gh-runs",
    script: "ci/checks/gh-run-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "GitHub Actions run health membrane (reads manifest/gh_runs/index.json — exits 0 if absent)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe over CI run history. Failures indicate upstream workflow regressions; fix is in .github/workflows/ source.",
    },
  },
  {
    name: "ankh-triple-abstraction",
    script: "ci/checks/ankh-triple-abstraction.ts",
    scope: "always",
    speed: "fast",
    description: "ANKH triple abstraction probe (WHR:MAX conformance + entity topology + compression ratio)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only conformance probe. Failures indicate entity-topology drift requiring semantic adjustment, not mechanical fix.",
    },
  },
  {
    name: "lens-refresh",
    script: "ci/checks/lens-refresh.ts",
    scope: "always",
    speed: "slow",
    description: "Refresh all data-plane lenses (git_rot_index, dependabot_index) — Gitological Noise As Structured Data",
    no_auto_fix: {
      reason: "wrong_layer",
      explanation: "This check IS itself a refresh — there's no separate fix tool. To re-run, invoke `bun run ci/run.ts --check lens-refresh` directly. If it fails repeatedly, the underlying lens script (scripts/refresh-lenses.ps1 or scripts/<lens>_index.py) needs inspection.",
      manual_remediation: "Run `bun run ci/run.ts --check lens-refresh` standalone. If it still fails, check scripts/refresh-lenses.ps1 and the individual scripts/*_index.py producers.",
    },
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
    let tag = "";
    if (c.auto_fix) tag = " [autofix]";
    else if (c.no_auto_fix) tag = ` [manual: ${c.no_auto_fix.reason}]`;
    console.log(`  ${c.name.padEnd(24)} [${scope}/${speed}]${tag}  ${c.description}`);
  }
  console.log(`\nFlags:`);
  console.log(`  --staged              Run only staged-scope checks (pre-commit mode)`);
  console.log(`  --full                Include slow checks (bun-audit etc.)`);
  console.log(`  --check <name>        Run a single check (by name or alias)`);
  console.log(`  --autofix             On any failure with registered auto_fix, attempt the fix and report delta`);
  console.log(`  --autofix-list        Show all checks: fix command if registered, or explanation if deliberately manual`);
  console.log(`  --autofix-show <name> Show full registry detail for a single check`);
  console.log(`  --list                This output`);
  process.exit(0);
}

const AUTOFIX_SHOW_IDX = process.argv.indexOf("--autofix-show");
const AUTOFIX_SHOW = AUTOFIX_SHOW_IDX !== -1 ? process.argv[AUTOFIX_SHOW_IDX + 1] : null;

if (AUTOFIX_SHOW) {
  const c = CHECKS.find((x) => x.name === AUTOFIX_SHOW || x.aliases?.includes(AUTOFIX_SHOW));
  if (!c) {
    console.error(`[ci] Unknown check: "${AUTOFIX_SHOW}". Run --list for available checks.`);
    process.exit(1);
  }
  console.log(`[ci] ${c.name}\n`);
  console.log(`  scope:       ${c.scope}`);
  console.log(`  speed:       ${c.speed}`);
  console.log(`  description: ${c.description}`);
  console.log(`  script:      ${c.script}`);
  if (c.auto_fix) {
    console.log(`\n  AUTO-FIX REGISTERED [${c.auto_fix.safe_class}]`);
    console.log(`    command: ${c.auto_fix.command} ${c.auto_fix.args.join(" ")}`);
    if (c.auto_fix.env) console.log(`    env:     ${JSON.stringify(c.auto_fix.env)}`);
    console.log(`    purpose: ${c.auto_fix.description}`);
  } else if (c.no_auto_fix) {
    console.log(`\n  NO AUTO-FIX (deliberate) [reason: ${c.no_auto_fix.reason}]`);
    console.log(`    explanation: ${c.no_auto_fix.explanation}`);
    if (c.no_auto_fix.manual_remediation) {
      console.log(`    manual:      ${c.no_auto_fix.manual_remediation}`);
    }
  } else {
    console.log(`\n  (no auto_fix and no no_auto_fix declared — registry gap)`);
  }
  process.exit(0);
}

if (AUTOFIX_LIST) {
  const withFix = CHECKS.filter((c) => c.auto_fix);
  const withoutFix = CHECKS.filter((c) => c.no_auto_fix);
  const unspecified = CHECKS.filter((c) => !c.auto_fix && !c.no_auto_fix);

  console.log("[ci] Auto-fix registry — comprehensive view\n");

  console.log(`=== AUTOMATIC (${withFix.length} check(s) — runnable via --autofix) ===\n`);
  if (withFix.length === 0) {
    console.log("  (none registered)\n");
  } else {
    for (const c of withFix) {
      const af = c.auto_fix!;
      console.log(`  ${c.name.padEnd(24)} [${af.safe_class}]`);
      console.log(`    command: ${af.command} ${af.args.join(" ")}`);
      console.log(`    purpose: ${af.description}`);
      console.log();
    }
  }

  console.log(`=== MANUAL ONLY (${withoutFix.length} check(s) — deliberate non-auto-fix) ===\n`);
  if (withoutFix.length === 0) {
    console.log("  (none classified)\n");
  } else {
    for (const c of withoutFix) {
      const nf = c.no_auto_fix!;
      console.log(`  ${c.name.padEnd(24)} [reason: ${nf.reason}]`);
      console.log(`    ${nf.explanation}`);
      if (nf.manual_remediation) {
        console.log(`    Manual fix: ${nf.manual_remediation}`);
      }
      console.log();
    }
  }

  if (unspecified.length > 0) {
    console.log(`=== REGISTRY GAP (${unspecified.length} check(s) — no auto_fix and no no_auto_fix declared) ===\n`);
    for (const c of unspecified) {
      console.log(`  ${c.name}`);
    }
    console.log();
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

// Surface the staged file landscape in the banner so vacuous passes are visible
// (3 gitlink changes + 7 checks all "passing" with 0 files inspected = not a real pass).
// Each registered check has a narrow file-type scope; if staged content doesn't match
// any scope, the gate yawns silently. The breakdown below makes the gap obvious.
function stagedFileLandscape(): { count: number; ext_summary: string; files: string[] } {
  if (!STAGED) return { count: -1, ext_summary: "", files: [] };
  const r = spawnSync("git", ["diff", "--cached", "--name-only", "--diff-filter=ACMRT"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  const files = (r.stdout ?? "").split("\n").filter(Boolean);
  const ext_counts: Record<string, number> = {};
  for (const f of files) {
    const dot = f.lastIndexOf(".");
    const slash = Math.max(f.lastIndexOf("/"), f.lastIndexOf("\\"));
    const ext = dot > slash ? f.slice(dot) : "(no-ext/gitlink)";
    ext_counts[ext] = (ext_counts[ext] || 0) + 1;
  }
  const ext_summary = Object.entries(ext_counts)
    .sort((a, b) => b[1] - a[1])
    .map(([e, c]) => `${e}:${c}`)
    .join(" ");
  return { count: files.length, ext_summary, files };
}

const staged = stagedFileLandscape();
const stagedBanner =
  STAGED && staged.count >= 0
    ? ` | staged: ${staged.count} file(s)${staged.ext_summary ? ` [${staged.ext_summary}]` : ""}`
    : "";
console.log(`[ci] ${selected.length} check(s) | mode: ${modeLabel}${stagedBanner}\n`);

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
