#!/usr/bin/env bun
// @SID: SCRIPT_STAMP_SID_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: scripts/stamp_sid.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * scripts/stamp_sid.ts — the auto-fixer for the `sid-envelope` gate.
 *
 * A gate that rebukes without fixing what it rebukes is a distraction. This makes
 * sid-envelope self-heal: it stamps / repairs a well-formed `@SID` on staged scripts/ci
 * `.ts`/`.py` files that are missing or malformed, so the commit can land after a
 * review-and-re-stage rather than a hand-edit.
 *
 * NON-DESTRUCTIVE repair — author intent is salvaged before any path-derivation:
 *   - missing            → insert a path-derived SID  (CI_CHECK_* / CI_* / LIB_* / SCRIPT_*)
 *   - malformed, salvageable (e.g. `TOOL_APPLY_DOC_FIXES`, lowercase `session-corpus`)
 *                        → uppercase, normalize separators, append `_V1` — the hand-chosen
 *                          domain prefix survives (TOOL_APPLY_DOC_FIXES_V1, SESSION_CORPUS_V1)
 *   - malformed junk (placeholder `todo`, too short) → fall back to the path-derived SID
 *
 * Every emitted SID is self-verified against the SAME shape regex sid-envelope.ts enforces,
 * so the stamper can never write something the gate would then reject.
 *
 * Contract: does NOT auto-stage (per the --autofix governance contract). The conductor
 * reviews the derived/repaired SID, refines the domain prefix if a more precise one fits,
 * and re-stages.
 *
 * Usage:
 *   bun run scripts/stamp_sid.ts --staged           # fix staged scripts/ci .ts/.py (autofix mode)
 *   bun run scripts/stamp_sid.ts --all              # sweep ALL tracked in-scope files (backlog)
 *   bun run scripts/stamp_sid.ts scripts/foo.ts ... # fix explicit files
 */

import { execSync } from "child_process";
import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");
const STAGED = process.argv.includes("--staged");
const ALL = process.argv.includes("--all");
const EXPLICIT = process.argv.slice(2).filter((a) => !a.startsWith("--"));

const SCRIPT_DIRS = ["scripts", "ci"];
const SCRIPT_EXTS = new Set([".ts", ".py"]);

// Kept in lockstep with ci/checks/sid-envelope.ts (extract + shape + placeholder set).
const SID_EXTRACT_RE = /@SID:\s*(\S+)/;
const SID_SHAPE_RE = /^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*_V\d+(_[A-Z][A-Z0-9]*)*$/;
const PLACEHOLDER_KEYWORDS = new Set([
  "TODO", "PLACEHOLDER", "FIXME", "TBD", "UNKNOWN", "NONE", "STUB", "FILL_ME",
]);
const SCAN_LINES = 40;

function isValidSid(sid: string): boolean {
  return sid.length >= 6 && SID_SHAPE_RE.test(sid) && !PLACEHOLDER_KEYWORDS.has(sid.toUpperCase());
}

function inScope(f: string): boolean {
  const norm = f.replace(/\\/g, "/");
  const inDir = SCRIPT_DIRS.some((d) => norm.startsWith(d + "/"));
  const ext = norm.slice(norm.lastIndexOf("."));
  return inDir && SCRIPT_EXTS.has(ext);
}

function gitList(args: string): string[] {
  try {
    const out = execSync(args, { encoding: "utf8", cwd: REPO_ROOT });
    return out.split("\n").filter(Boolean).filter(inScope);
  } catch {
    return [];
  }
}

/** Path → ALL_CAPS DOMAIN_NAME_V1 SID (used for missing files + as repair fallback). */
function deriveSid(relPath: string): string {
  const norm = relPath.replace(/\\/g, "/");
  const parts = norm.split("/");
  const fileBase = parts[parts.length - 1].replace(/\.[^.]+$/, "");

  let prefix: string;
  if (norm.startsWith("ci/checks/")) prefix = "CI_CHECK";
  else if (norm.startsWith("ci/")) prefix = "CI";
  else if (norm.startsWith("scripts/lib/")) prefix = "LIB";
  else if (norm.startsWith("scripts/")) prefix = "SCRIPT";
  else prefix = (parts[0] ?? "TOOL").toUpperCase().replace(/[^A-Z0-9]+/g, "_");

  const name = fileBase.toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return `${prefix}_${name}_V1`.replace(/_+/g, "_");
}

/** Salvage a malformed author SID before falling back to path-derivation, so a hand-chosen
 *  domain prefix (TOOL_/LIB_/…) survives rather than being clobbered to a generic one. */
function repairSid(existing: string, derived: string): string {
  let s = existing.toUpperCase().replace(/[^A-Z0-9_]+/g, "_").replace(/_+/g, "_").replace(/^_+|_+$/g, "");
  if (s && !/_V\d+/.test(s)) s = `${s}_V1`;
  const core = s.replace(/_V\d+(_[A-Z0-9]+)*$/, "").replace(/_+$/, "");
  return isValidSid(s) && !PLACEHOLDER_KEYWORDS.has(core) ? s : derived;
}

function commentFor(ext: string, sid: string): string {
  return ext === ".ts" ? `// @SID: ${sid}` : `# @SID: ${sid}`;
}

/** Insert after a contiguous header block (shebang, then a Python coding line). */
function insertionIndex(lines: string[], ext: string): number {
  let i = 0;
  if (lines[0]?.startsWith("#!")) i = 1;
  if (ext === ".py" && /coding[:=]\s*[-\w.]+/.test(lines[i] ?? "")) i += 1;
  return i;
}

type Kind = "inserted" | "repaired" | "skipped-valid" | "skipped-unreadable";
interface Action {
  file: string;
  sid: string;
  kind: Kind;
}

function stampFile(rel: string): Action {
  const absPath = resolve(REPO_ROOT, rel);
  const ext = rel.slice(rel.lastIndexOf("."));
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return { file: rel, sid: "", kind: "skipped-unreadable" };
  }

  const eol = content.includes("\r\n") ? "\r\n" : "\n";
  const lines = content.split(/\r?\n/);
  const sidIdx = lines.slice(0, SCAN_LINES).findIndex((l) => SID_EXTRACT_RE.test(l));
  const derived = deriveSid(rel);

  if (sidIdx !== -1) {
    const existing = SID_EXTRACT_RE.exec(lines[sidIdx])![1];
    if (isValidSid(existing)) return { file: rel, sid: existing, kind: "skipped-valid" };
    const fixed = repairSid(existing, derived);
    lines[sidIdx] = lines[sidIdx].replace(SID_EXTRACT_RE, `@SID: ${fixed}`);
    writeFileSync(absPath, lines.join(eol));
    return { file: rel, sid: fixed, kind: "repaired" };
  }

  lines.splice(insertionIndex(lines, ext), 0, commentFor(ext, derived));
  writeFileSync(absPath, lines.join(eol));
  return { file: rel, sid: derived, kind: "inserted" };
}

const targets = (
  EXPLICIT.length > 0
    ? EXPLICIT
    : ALL
      ? gitList("git ls-files")
      : STAGED
        ? gitList("git diff --cached --name-only --diff-filter=ACM")
        : []
).filter(inScope);

if (targets.length === 0) {
  console.log("[stamp-sid] no in-scope (.ts/.py under scripts/ or ci/) targets. Pass --staged, --all, or explicit paths.");
  process.exit(0);
}

const actions = targets.map(stampFile);

// Verify-vs-truth: every SID we wrote MUST satisfy the gate's own shape regex.
const bad = actions.filter((a) => (a.kind === "inserted" || a.kind === "repaired") && !isValidSid(a.sid));

const verb: Record<Kind, string> = {
  inserted: "stamped",
  repaired: "repaired",
  "skipped-valid": "ok",
  "skipped-unreadable": "skip",
};
for (const a of actions) {
  if (a.kind === "skipped-valid" && !ALL) continue; // quiet on the no-ops unless sweeping
  console.log(`[stamp-sid] ${verb[a.kind].padEnd(8)} ${a.file}${a.sid ? `  → ${a.sid}` : ""}`);
}

if (bad.length > 0) {
  console.error(`\n[stamp-sid] ✗ ${bad.length} emitted SID(s) failed self-verification — aborting (stamper bug, not a file problem).`);
  process.exit(1);
}

const changed = actions.filter((a) => a.kind === "inserted" || a.kind === "repaired").length;
console.log(
  `\n[stamp-sid] ${changed} file(s) stamped/repaired. Review the SID, refine the domain prefix if a more precise one fits, then re-stage.`,
);
process.exit(0);
