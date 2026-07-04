#!/usr/bin/env bun
// @SID: CI_CHECK_HOMEPATH_PORTABILITY_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/homepath-portability.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/homepath-portability.ts — literal per-user home-directory paths
 * baked into tracked scripts/configs, instead of resolved dynamically.
 *
 * Root incident (2026-07-04): extensions/chthonic-archive/.chthonic/mise.toml
 * env vars used {{cwd}} (invocation-relative) instead of {{config_root}}
 * (file-relative), and toolpool-scan.ts used process.cwd() instead of
 * import.meta.dir — both resolved to a DIFFERENT wrong path depending on
 * where they were invoked from. Same session: a Feb-18 cache snapshot turned
 * up carrying a literal home-path with a prior machine's username baked in
 * (a laptop account, one letter off from this desktop's) — surviving a
 * "lossless" repo transition unflagged for ~4.5 months. Same disease as the
 * mise bug above: a machine-identity string baked into a path where a
 * dynamic primitive belongs. This check generalizes the catch beyond the
 * one instance that was found by hand.
 *
 * Detects literal `C:\Users\<name>\` (backslash or forward-slash, plus the
 * git-bash/MSYS `/c/Users/<name>/` mount form) in tracked scripts/configs.
 * Windows-only forms — this repo is confirmed Windows-only (see slab
 * mise.toml's own [env] comment), so Unix `/home/`/`/Users/` forms are
 * deliberately omitted rather than added as unverified false-positive risk.
 *
 * Two severities:
 *   - stale : <name> does not match the CURRENT resolved username — proven
 *             cross-machine/cross-account drift (the erdno-on-eldno case).
 *   - smell : <name> DOES match the current username — works today, breaks
 *             the moment this file crosses to another machine/account.
 *             The latent form of the same bug, caught before it can drift.
 *
 * Cache/manifest outputs are exempt — their job IS to record a resolved path
 * at scan time; this gate targets SOURCE (scripts/configs), not their
 * outputs. (The stale erdno file itself was exactly such an output, found by
 * hand this session — this check would not have re-flagged it as a bug in
 * itself, only in whatever SCRIPT wrote it, which is where the real fix went.)
 *
 * Deliberately no auto-fix (see registry entry in ci/run.ts): the correct
 * replacement depends on whether the path is meant to be home-relative
 * ({{env.USERPROFILE}} / $env:USERPROFILE / os.homedir()) or repo-relative
 * ({{config_root}} / import.meta.dir) — a semantic read of intent, not a
 * mechanical username swap. A blind fixer risks producing a DIFFERENT wrong
 * value silently (this exact repo's CHTHONIC_NVIDIA_STACK fix needed a
 * different relative depth than its three siblings purely because someone
 * traced where the real file actually lived — that judgment doesn't
 * mechanize).
 *
 * Exit semantics:
 *   --staged  STRICT on staged Added/Copied/Modified in-scope files. (exit 1 on ANY finding)
 *   (default) Advisory scan of all tracked in-scope files. (exit 0, reports both severities)
 *
 * Usage:
 *   bun run ci/checks/homepath-portability.ts           # audit tracked files
 *   bun run ci/checks/homepath-portability.ts --staged  # pre-commit check
 *   bun run ci/checks/homepath-portability.ts --report  # JSON report to stdout
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";
import { resolve } from "path";
import * as os from "os";

const STAGED = process.argv.includes("--staged");
const REPORT = process.argv.includes("--report");
const REPO_ROOT = resolve(import.meta.dir, "../..");

function currentUser(): string {
  try {
    const u = os.userInfo().username;
    if (u) return u;
  } catch {
    /* fall through to env */
  }
  return (process.env.USERNAME ?? process.env.USER ?? "").trim();
}

const CURRENT_USER = currentUser();

// Managed roots: where a hardcoded machine path actually matters (live
// scripts/configs), not vendored/build/data noise. Root-level loose config
// files (mise.toml, .cargo/config.toml equivalents) have no directory
// prefix, so they're matched via ROOT_FILES instead.
const MANAGED_ROOTS = [
  "ci/", "scripts/", "extensions/", "apps/", "mcp/", "mas_mcp/", "src/", "native/",
  ".cargo/", ".vscode/", ".chthonic/",
];
const ROOT_FILES = new Set(["mise.toml", "bunfig.toml", "package.json", "tsconfig.json"]);

const SCAN_EXTS = new Set([
  ".ts", ".js", ".mjs", ".cjs", ".ps1", ".psm1", ".toml", ".json",
  ".yaml", ".yml", ".rs", ".py", ".sh", ".cfg",
]);

// Cache/report/manifest outputs legitimately capture a resolved path at scan
// time — that's their job, not a portability bug. Exempt by path fragment
// (git ls-files always returns forward-slash paths, but match both defensively).
const EXEMPT_PARTS = ["/cache/", "\\cache\\", "/manifest/", "\\manifest\\"];

function ext(f: string): string {
  return f.slice(f.lastIndexOf("."));
}

function isExempt(f: string): boolean {
  return EXEMPT_PARTS.some((p) => f.includes(p));
}

function inScope(f: string): boolean {
  if (isExempt(f)) return false;
  if (!SCAN_EXTS.has(ext(f))) return false;
  const isRootFile = !f.includes("/") && !f.includes("\\") && ROOT_FILES.has(f);
  const isInManagedRoot = MANAGED_ROOTS.some((r) => f.startsWith(r));
  return isRootFile || isInManagedRoot;
}

// ── File collection ──────────────────────────────────────────────────────────

function getStagedChangedFiles(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=ACM", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out.split("\n").filter(Boolean).filter(inScope);
  } catch {
    return [];
  }
}

function getTrackedFiles(): string[] {
  try {
    const out = execSync("git ls-files", { encoding: "utf8", cwd: REPO_ROOT });
    return out.split("\n").filter(Boolean).filter(inScope);
  } catch {
    return [];
  }
}

// ── Pattern analysis ─────────────────────────────────────────────────────────

type Severity = "stale" | "smell";

interface Finding {
  file: string;
  line: number;
  matched: string;
  capturedUser: string;
  severity: Severity;
}

// Each pattern captures a username segment for one Windows path convention.
// Backslash form handles both raw (\) and JSON/TS-escaped (\\) separators.
const PATTERNS: RegExp[] = [
  /C:\\{1,2}Users\\{1,2}([A-Za-z][\w.\-]{1,31})\\{1,2}/g,
  /C:\/Users\/([A-Za-z][\w.\-]{1,31})\//g,
  /\/c\/Users\/([A-Za-z][\w.\-]{1,31})\//g,
];

function scanFile(relPath: string): Finding[] {
  const absPath = resolve(REPO_ROOT, relPath);
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return [];
  }

  const lines = content.split(/\r?\n/);
  const findings: Finding[] = [];
  const seen = new Set<string>();

  lines.forEach((lineText, idx) => {
    for (const pattern of PATTERNS) {
      pattern.lastIndex = 0;
      let m: RegExpExecArray | null;
      while ((m = pattern.exec(lineText)) !== null) {
        const capturedUser = m[1];
        const key = `${idx}:${capturedUser}:${m[0]}`;
        if (seen.has(key)) continue;
        seen.add(key);
        findings.push({
          file: relPath,
          line: idx + 1,
          matched: m[0],
          capturedUser,
          severity: capturedUser === CURRENT_USER ? "smell" : "stale",
        });
      }
    }
  });

  return findings;
}

// ── Reporters ────────────────────────────────────────────────────────────────

function printHuman(findings: Finding[], mode: "staged" | "advisory"): void {
  if (findings.length === 0) {
    console.log(`[homepath-portability] ✓ no hardcoded home-directory paths found (current user: ${CURRENT_USER})`);
    return;
  }

  const stale = findings.filter((f) => f.severity === "stale");
  const smell = findings.filter((f) => f.severity === "smell");

  if (stale.length > 0) {
    const icon = mode === "staged" ? "✗" : "⚠";
    console[mode === "staged" ? "error" : "log"](
      `[homepath-portability] ${icon} ${stale.length} STALE reference(s) — username doesn't match current (${CURRENT_USER}):`
    );
    for (const f of stale) {
      console[mode === "staged" ? "error" : "log"](`  ${f.file}:${f.line}  [${f.capturedUser}]  ${f.matched}`);
    }
  }

  if (smell.length > 0) {
    const icon = mode === "staged" ? "✗" : "ℹ";
    console[mode === "staged" ? "error" : "log"](
      `[homepath-portability] ${icon} ${smell.length} portability smell(s) — hardcoded but currently matches (${CURRENT_USER}):`
    );
    for (const f of smell) {
      console[mode === "staged" ? "error" : "log"](`  ${f.file}:${f.line}  ${f.matched}`);
    }
  }

  if (mode === "staged") {
    console.error(`\n  Fix: resolve dynamically instead of a literal username. Which primitive depends`);
    console.error(`  on intent (home-relative vs repo-relative) — see ci/run.ts --autofix-show homepath-portability.`);
  }
}

// ── Entry point ──────────────────────────────────────────────────────────────

if (STAGED) {
  const files = getStagedChangedFiles();
  const findings = files.flatMap(scanFile);

  if (REPORT) {
    process.stdout.write(JSON.stringify({ mode: "staged", currentUser: CURRENT_USER, findings }, null, 2) + "\n");
  } else {
    printHuman(findings, "staged");
  }

  process.exit(findings.length > 0 ? 1 : 0);
} else {
  const files = getTrackedFiles();
  const findings = files.flatMap(scanFile);

  if (REPORT) {
    const summary = {
      mode: "advisory",
      currentUser: CURRENT_USER,
      totalFiles: files.length,
      stale: findings.filter((f) => f.severity === "stale").length,
      smell: findings.filter((f) => f.severity === "smell").length,
      findings,
    };
    process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  } else {
    printHuman(findings, "advisory");
  }
  process.exit(0);
}
