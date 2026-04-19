#!/usr/bin/env bun
// @SID: CI_CHECK_SID_ENVELOPE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/sid-envelope.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/sid-envelope.ts — @SID presence check for new scripts.
 *
 * Every script committed to scripts/ or ci/ must carry a Semantic ID.
 * Format (TypeScript): // @SID: DOMAIN_NAME_V1
 * Format (Python):    // @SID: DOMAIN_NAME_V1  (inside docstring)
 *
 * Behavior:
 *   --staged  STRICT on Added .ts and .py files in scripts/ and ci/. (exit 1)
 *   (default) Advisory scan of all tracked scripts. (exit 0)
 *
 * Usage:
 *   bun run ci/checks/sid-envelope.ts           # audit tracked scripts
 *   bun run ci/checks/sid-envelope.ts --staged  # pre-commit check
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";
import { resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");

// Directories that are in scope for @SID enforcement
const SCRIPT_DIRS = ["scripts", "ci"];
const SCRIPT_EXTS = new Set([".ts", ".py"]);

const SID_RE = /@SID:\s*\S+/;
const SCAN_LINES = 40; // Check first N lines for @SID

function getStagedAddedScripts(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=A", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .filter((f) => f.trim().length > 0)
      .filter((f) => {
        const inScope = SCRIPT_DIRS.some((d) => f.startsWith(d + "/") || f.startsWith(d + "\\"));
        const ext = f.slice(f.lastIndexOf("."));
        return inScope && SCRIPT_EXTS.has(ext);
      })
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function getTrackedScripts(): string[] {
  try {
    const out = execSync("git ls-files", { encoding: "utf8", cwd: REPO_ROOT });
    return out
      .split("\n")
      .filter((f) => f.trim().length > 0)
      .filter((f) => {
        const inScope = SCRIPT_DIRS.some((d) => f.startsWith(d + "/") || f.startsWith(d + "\\"));
        const ext = f.slice(f.lastIndexOf("."));
        return inScope && SCRIPT_EXTS.has(ext);
      })
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function hasSID(absPath: string): boolean {
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return true; // Can't read = skip
  }
  const lines = content.split("\n").slice(0, SCAN_LINES);
  return lines.some((line) => SID_RE.test(line));
}

function relPath(abs: string): string {
  return abs.replace(REPO_ROOT + "/", "").replace(REPO_ROOT + "\\", "");
}

if (STAGED) {
  const files = getStagedAddedScripts();
  const missing = files.filter((f) => !hasSID(f)).map(relPath);

  if (missing.length === 0) {
    console.log(
      `[sid-envelope] ✓ @SID present in ${files.length} new staged script(s)`
    );
    process.exit(0);
  } else {
    console.error(
      `[sid-envelope] ✗ ${missing.length} new script(s) missing @SID:`
    );
    for (const f of missing) {
      console.error(`  ${f}`);
    }
    console.error(
      `\n  Fix: Add '// @SID: DOMAIN_NAME_V1' on line 2 of each script.`
    );
    process.exit(1);
  }
} else {
  // Advisory scan
  const files = getTrackedScripts();
  const missing = files.filter((f) => !hasSID(f)).map(relPath);

  if (missing.length === 0) {
    console.log(
      `[sid-envelope] ✓ @SID present in all ${files.length} tracked script(s)`
    );
  } else {
    console.log(
      `[sid-envelope] ℹ ${missing.length}/${files.length} tracked script(s) missing @SID:`
    );
    for (const f of missing) {
      console.log(`  ${f}`);
    }
  }
  process.exit(0);
}
