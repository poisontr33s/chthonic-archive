#!/usr/bin/env bun
// @SID: CI_CHECK_SID_ENVELOPE_V2

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/sid-envelope.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/sid-envelope.ts — @SID identity contract for staged infrastructure scripts.
 *
 * V2 hardening: not just presence — shape and vocabulary are now validated.
 *
 * Every script committed to scripts/ or ci/ must carry a well-formed Semantic ID.
 * Format (TypeScript): // @SID: DOMAIN_NAME_V1
 * Format (Python):     # @SID: DOMAIN_NAME_V1  (or inside docstring)
 *
 * Valid SID shape:
 *   - ALL_CAPS_WITH_UNDERSCORES only
 *   - Must contain at least one underscore-delimited segment plus a version suffix (_V\d+)
 *   - Version suffix may be followed by additional ALL_CAPS qualifiers (e.g. _CLI, _BETA)
 *   - Examples: CI_CHECK_SID_ENVELOPE_V2  SESSION_COMPRESS_V1_CLI  PYTHON_HEADER_V3
 *
 * Invalid (caught as malformed):
 *   - Known placeholder keywords: TODO, PLACEHOLDER, FIXME, TBD, UNKNOWN, NONE, STUB
 *   - Lowercase or mixed-case values (prose descriptions)
 *   - Values with no version suffix
 *   - Very short values (< 6 chars)
 *
 * Exit semantics:
 *   --staged  STRICT on Added/Copied/Modified .ts and .py in scripts/ and ci/. (exit 1 on ANY issue)
 *   (default) Advisory scan of all tracked scripts. (exit 0, shows categories)
 *
 * Usage:
 *   bun run ci/checks/sid-envelope.ts           # audit tracked scripts
 *   bun run ci/checks/sid-envelope.ts --staged  # pre-commit check
 *   bun run ci/checks/sid-envelope.ts --report  # JSON report to stdout
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";
import { resolve } from "path";

const STAGED  = process.argv.includes("--staged");
const REPORT  = process.argv.includes("--report");
const REPO_ROOT = resolve(import.meta.dir, "../..");

const SCRIPT_DIRS = ["scripts", "ci"];
const SCRIPT_EXTS = new Set([".ts", ".py"]);

// Extract the SID value from a line containing @SID:
const SID_EXTRACT_RE = /@SID:\s*(\S+)/;

// Well-formed SID: ALL_CAPS segments, mandatory _V\d+ suffix (may have additional suffixes)
const SID_SHAPE_RE   = /^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*_V\d+(_[A-Z][A-Z0-9]*)*$/;

// Known placeholder keywords that pass the presence regex but are not real SIDs
const PLACEHOLDER_KEYWORDS = new Set([
  "TODO", "PLACEHOLDER", "FIXME", "TBD", "UNKNOWN", "NONE", "STUB", "FILL_ME",
]);

const SCAN_LINES = 40;

// ── File collection ──────────────────────────────────────────────────────────

function getStagedChangedScripts(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=ACM", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out.split("\n").filter(Boolean).filter(inScope).map(abs);
  } catch {
    return [];
  }
}

function getTrackedScripts(): string[] {
  try {
    const out = execSync("git ls-files", { encoding: "utf8", cwd: REPO_ROOT });
    return out.split("\n").filter(Boolean).filter(inScope).map(abs);
  } catch {
    return [];
  }
}

function inScope(f: string): boolean {
  const inDir  = SCRIPT_DIRS.some((d) => f.startsWith(d + "/") || f.startsWith(d + "\\"));
  const ext    = f.slice(f.lastIndexOf("."));
  return inDir && SCRIPT_EXTS.has(ext);
}

function abs(f: string): string {
  return resolve(REPO_ROOT, f);
}

function rel(absPath: string): string {
  return absPath.replace(REPO_ROOT + "/", "").replace(REPO_ROOT + "\\", "");
}

// ── SID analysis ─────────────────────────────────────────────────────────────

type SIDResult = "missing" | "malformed" | "valid";

interface FileReport {
  file:   string;
  result: SIDResult;
  sid?:   string;
  reason?: string;
}

function analyzeSID(absPath: string): FileReport {
  const file = rel(absPath);
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return { file, result: "valid", reason: "unreadable (skipped)" };
  }

  const lines = content.split("\n").slice(0, SCAN_LINES);
  const sidLine = lines.find((l) => SID_EXTRACT_RE.test(l));

  if (!sidLine) {
    return { file, result: "missing" };
  }

  const match = SID_EXTRACT_RE.exec(sidLine);
  const sid   = match?.[1] ?? "";

  if (PLACEHOLDER_KEYWORDS.has(sid.toUpperCase())) {
    return { file, result: "malformed", sid, reason: "placeholder keyword" };
  }

  if (sid.length < 6) {
    return { file, result: "malformed", sid, reason: "too short (min 6 chars)" };
  }

  if (!SID_SHAPE_RE.test(sid)) {
    // Diagnose the most likely failure for a useful message
    const reason = /[a-z]/.test(sid)
      ? "lowercase chars (must be ALL_CAPS)"
      : !/_V\d+/.test(sid)
        ? "missing version suffix (_V<n>)"
        : "invalid shape (expected DOMAIN_NAME_V1 pattern)";
    return { file, result: "malformed", sid, reason };
  }

  return { file, result: "valid", sid };
}

// ── Reporters ────────────────────────────────────────────────────────────────

function printHuman(reports: FileReport[], mode: "staged" | "advisory"): void {
  const missing   = reports.filter((r) => r.result === "missing");
  const malformed = reports.filter((r) => r.result === "malformed");
  const valid     = reports.filter((r) => r.result === "valid");

  if (missing.length === 0 && malformed.length === 0) {
    console.log(
      `[sid-envelope] ✓ all ${valid.length} script(s) carry valid SIDs`
    );
    return;
  }

  if (missing.length > 0) {
    const icon = mode === "staged" ? "✗" : "ℹ";
    console[mode === "staged" ? "error" : "log"](
      `[sid-envelope] ${icon} ${missing.length} script(s) missing @SID:`
    );
    for (const r of missing) {
      console[mode === "staged" ? "error" : "log"](`  ${r.file}`);
    }
  }

  if (malformed.length > 0) {
    const icon = mode === "staged" ? "✗" : "⚠";
    console[mode === "staged" ? "error" : "log"](
      `[sid-envelope] ${icon} ${malformed.length} script(s) with malformed SID:`
    );
    for (const r of malformed) {
      console[mode === "staged" ? "error" : "log"](`  ${r.file}  [${r.sid}] — ${r.reason}`);
    }
  }

  if (mode === "staged") {
    console.error(
      `\n  Fix: @SID must match ALL_CAPS_DOMAIN_V1 pattern on line 2.`
    );
    console.error(`  Example: // @SID: SCRIPT_PURPOSE_V1`);
  }
}

// ── Entry point ──────────────────────────────────────────────────────────────

if (STAGED) {
  const files   = getStagedChangedScripts();
  const reports = files.map(analyzeSID);

  if (REPORT) {
    process.stdout.write(JSON.stringify({ mode: "staged", reports }, null, 2) + "\n");
  } else {
    printHuman(reports, "staged");
  }

  const hasIssues = reports.some((r) => r.result !== "valid");
  process.exit(hasIssues ? 1 : 0);
} else {
  const files   = getTrackedScripts();
  const reports = files.map(analyzeSID);

  if (REPORT) {
    const summary = {
      mode: "advisory",
      total:    files.length,
      valid:    reports.filter((r) => r.result === "valid").length,
      missing:  reports.filter((r) => r.result === "missing").length,
      malformed: reports.filter((r) => r.result === "malformed").length,
      reports,
    };
    process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  } else {
    printHuman(reports, "advisory");
    const valid = reports.filter((r) => r.result === "valid").length;
    if (valid < files.length) {
      console.log(`  (${valid}/${files.length} valid — malformed reported as advisory until alchemized)`);
    }
  }
  process.exit(0);
}

