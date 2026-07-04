All 11 checks pass, including the new gate validating itself. Final summary:*

Built ci/checks/homepath-portability.ts, registered in ci/run.ts alongside the other 22 checks, following the exact existing conventions (SID envelope, Decorator's Blessing header, staged/advisory dual-mode, no_auto_fix: semantic with concrete manual-remediation guidance). Verified end-to-end: catches a synthetic violation in --staged mode (exit 1), passes clean once fixed, and its own SID/envelope pass the repo's existing governance checks.

It immediately found real, live drift — not hypothetical. Across tracked source (not cache): 28 stale erdno references still sitting in extensions/chthonic-archive/src/acp/connection.ts, mas_mcp/mas_memory.json (14 occurrences), several scripts/*.ps1/.py files, plus 44 "smell" findings (hardcoded eldno — correct today, fragile the moment this crosses machines again) in .vscode/mcp.json, .vscode/settings.json, scripts/mcp-*.ts, and others.

I deliberately did not wire an auto-fix — the correct replacement (home-relative vs. repo-relative) requires the same kind of tracing I did for CHTHONIC_NVIDIA_STACK earlier, which doesn't mechanize safely. It's no_auto_fix: semantic, matching this repo's own existing pattern for exactly this class of judgment call.

The gate itself is done and passing. The 72 pre-existing findings it surfaced are a separate, larger cleanup — want me to work through those now, or leave the gate as the landed deliverable and handle the cleanup as its own pass?

Read c:\Users\eldno\chthonic-archive\ci\run.ts
Grep "ci/run\.ts|CHECKS|auto_fix|ci/checks" (in c:\Users\eldno\chthonic-archive\SCRIPTS_README.md)
51 lines of output
Here is the full architecture picture, verified directly against the live source (note: this repo has visible concurrent background activity — ci/run.ts and ci/checks/ gained a new file mid-exploration — so treat exact counts as "as of right now" and re-run bun run ci/run.ts --autofix-list yourself right before you finalize).

Correction to your starting assumptions
Not 3 auto-fix / ~10 manual. Current registered roster in c:\Users\eldno\chthonic-archive\ci\run.ts is 21 checks total: 6 with auto_fix, 15 with no_auto_fix (verified by counting auto_fix: { / no_auto_fix: { / name: " occurrences directly).
The 6 auto-fix checks: shebang, python-headers, sid-envelope, uv-guard, blessing-gate, pathfinder (alias link-audit).
There are also 4 fully-written but unregistered check scripts sitting in ci/checks/: claudine-lora-smoke.ts, federation-contract-validate.ts, session-truncation-gate.ts, theme-icon-validate.ts. They exist on disk with valid envelopes/SIDs but have no entry in ci/run.ts's CHECKS array — so bun run ci, --list, and the pre-commit hook never touch them. This is living proof of the answer to your item 3: a file in ci/checks/ alone does nothing; the array entry is what wires it in.
1. The CI auto-fix gate architecture
Location: c:\Users\eldno\chthonic-archive\ci\run.ts (orchestrator + registry, ~900 lines) and c:\Users\eldno\chthonic-archive\ci\checks\*.ts (one file per check, all Bun/TS).

The registry (CHECKS: Check[] in ci/run.ts) is simultaneously the manifest, the roster, and the auto-fix wiring table — there's no separate manifest file. Each entry is a plain object:


type AutoFix = {
  command: string;              // e.g. "bun" or "uv"
  args: string[];
  env?: Record<string, string>;
  safe_class: "narrow" | "destructive";  // only "narrow" runs under --autofix
  description: string;
};

type NoAutoFixReason = {
  reason: "semantic" | "destructive" | "no_tool" | "wrong_layer" | "read_only_health";
  explanation: string;
  manual_remediation?: string;
};

type Check = {
  name: string;
  aliases?: string[];
  script: string;               // path to the check .ts, run via `bun run <script> [--staged]`
  scope: "staged" | "always";
  speed: "fast" | "slow";
  description: string;
  auto_fix?: AutoFix;            // exactly one of these two must be present
  no_auto_fix?: NoAutoFixReason;
};
Key architectural point: the check script and the fixer are separate files. The check only detects and reports (exit 0/1); the actual repair lives in a distinct script (scripts/fix_*.ts, scripts/stamp_sid.ts, scripts/canonize_blessing.py, etc.) that the registry entry's auto_fix.command/args invokes. ci/run.ts runs the fixer via spawnSync, diffs the working tree before/after (git diff --stat), and never auto-stages — it always exits 1 even after a successful fix so a human/conductor reviews and re-stages.

Full auto-fix example (check + its fixer)
c:\Users\eldno\chthonic-archive\ci\checks\sid-envelope.ts — full content:


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
    console.log(`[sid-envelope] ✓ all ${valid.length} script(s) carry valid SIDs`);
    return;
  }

  if (missing.length > 0) {
    const icon = mode === "staged" ? "✗" : "ℹ";
    console[mode === "staged" ? "error" : "log"](`[sid-envelope] ${icon} ${missing.length} script(s) missing @SID:`);
    for (const r of missing) {
      console[mode === "staged" ? "error" : "log"](`  ${r.file}`);
    }
  }

  if (malformed.length > 0) {
    const icon = mode === "staged" ? "✗" : "⚠";
    console[mode === "staged" ? "error" : "log"](`[sid-envelope] ${icon} ${malformed.length} script(s) with malformed SID:`);
    for (const r of malformed) {
      console[mode === "staged" ? "error" : "log"](`  ${r.file}  [${r.sid}] — ${r.reason}`);
    }
  }

  if (mode === "staged") {
    console.error(`\n  Fix: @SID must match ALL_CAPS_DOMAIN_V1 pattern on line 2.`);
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
Its registered fixer, c:\Users\eldno\chthonic-archive\scripts\stamp_sid.ts (full content — this is "how auto-fix performs the repair" for this gate):


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
 * ... (non-destructive repair: missing -> path-derived SID; malformed-salvageable ->
 * uppercase+normalize+append _V1; malformed junk -> path-derived fallback.
 * Every emitted SID is self-verified against sid-envelope.ts's own shape regex.
 * Does NOT auto-stage.)
 *
 * Usage:
 *   bun run scripts/stamp_sid.ts --staged
 *   bun run scripts/stamp_sid.ts --all
 *   bun run scripts/stamp_sid.ts scripts/foo.ts ...
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

/** Salvage a malformed author SID before falling back to path-derivation... */
function repairSid(existing: string, derived: string): string {
  let s = existing.toUpperCase().replace(/[^A-Z0-9_]+/g, "_").replace(/_+/g, "_").replace(/^_+|_+$/g, "");
  if (s && !/_V\d+/.test(s)) s = `${s}_V1`;
  const core = s.replace(/_V\d+(_[A-Z0-9]+)*$/, "").replace(/_+$/, "");
  return isValidSid(s) && !PLACEHOLDER_KEYWORDS.has(core) ? s : derived;
}

function commentFor(ext: string, sid: string): string {
  return ext === ".ts" ? `// @SID: ${sid}` : `# @SID: ${sid}`;
}

function insertionIndex(lines: string[], ext: string): number {
  let i = 0;
  if (lines[0]?.startsWith("#!")) i = 1;
  if (ext === ".py" && /coding[:=]\s*[-\w.]+/.test(lines[i] ?? "")) i += 1;
  return i;
}

type Kind = "inserted" | "repaired" | "skipped-valid" | "skipped-unreadable";
interface Action { file: string; sid: string; kind: Kind; }

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
  EXPLICIT.length > 0 ? EXPLICIT
    : ALL ? gitList("git ls-files")
    : STAGED ? gitList("git diff --cached --name-only --diff-filter=ACM")
    : []
).filter(inScope);

if (targets.length === 0) {
  console.log("[stamp-sid] no in-scope (.ts/.py under scripts/ or ci/) targets. Pass --staged, --all, or explicit paths.");
  process.exit(0);
}

const actions = targets.map(stampFile);
const bad = actions.filter((a) => (a.kind === "inserted" || a.kind === "repaired") && !isValidSid(a.sid));

const verb: Record<Kind, string> = {
  inserted: "stamped", repaired: "repaired", "skipped-valid": "ok", "skipped-unreadable": "skip",
};
for (const a of actions) {
  if (a.kind === "skipped-valid" && !ALL) continue;
  console.log(`[stamp-sid] ${verb[a.kind].padEnd(8)} ${a.file}${a.sid ? `  → ${a.sid}` : ""}`);
}

if (bad.length > 0) {
  console.error(`\n[stamp-sid] ✗ ${bad.length} emitted SID(s) failed self-verification — aborting (stamper bug, not a file problem).`);
  process.exit(1);
}

const changed = actions.filter((a) => a.kind === "inserted" || a.kind === "repaired").length;
console.log(`\n[stamp-sid] ${changed} file(s) stamped/repaired. Review the SID, refine the domain prefix if a more precise one fits, then re-stage.`);
process.exit(0);
The corresponding registry entries (from ci/run.ts, current, verified):


  {
    name: "sid-envelope",
    script: "ci/checks/sid-envelope.ts",
    scope: "staged",
    speed: "fast",
    description: "@SID identity on staged scripts/ci .ts/.py (Added/Copied/Modified) — ALL_CAPS DOMAIN_NAME_V<n> shape",
    auto_fix: {
      command: "bun",
      args: ["run", "scripts/stamp_sid.ts", "--staged"],
      safe_class: "narrow",
      description: "Stamp a path-derived ALL_CAPS DOMAIN_NAME_V1 @SID into staged scripts/ci .ts/.py files that are missing or malformed (CI_CHECK_* / CI_* / LIB_* / SCRIPT_* by directory; filename → UPPER_SNAKE). ...",
    },
  },
Manual-only ("no_auto_fix") full example
c:\Users\eldno\chthonic-archive\ci\checks\character-schema.ts — full content (delegates validation to uv run ... python, writes a manifest snapshot for downstream lenses — a common shape among the 15 manual-only checks):


#!/usr/bin/env bun
// @SID: CI_CHECK_CHARACTER_SCHEMA_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/character-schema.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Sibling membrane: lore-canon-paths.ts, organ-canon-citation.ts)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/character-schema.ts — JSON Schema validation for game/lore/characters/.
 *
 * Validates every *.json under game/lore/characters/ (excluding the schema itself)
 * against game/lore/characters/character.schema.json. Emits a manifest snapshot
 * (manifest/character_schema_audit.json) so downstream lenses and canon-drift-snapshot
 * can read it without re-running validation.
 *
 * Usage:
 *   bun run ci/checks/character-schema.ts            # always-scope full audit
 *   bun run ci/checks/character-schema.ts --staged   # only re-validate if a character file is staged
 *
 * Auto-fix: none. Schema violations require human authoring — adding missing
 * fields, fixing types, renaming keys all need semantic judgment.
 */

import { execSync, spawnSync } from "child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "fs";
import { dirname, join, resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const SCHEMA_PATH = resolve(REPO_ROOT, "game/lore/characters/character.schema.json");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest/character_schema_audit.json");

if (!existsSync(SCHEMA_PATH)) {
  console.error(`[character-schema] FATAL: schema not found at ${SCHEMA_PATH}`);
  process.exit(1);
}

function walkJson(dir: string, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const s = statSync(full);
    if (s.isDirectory()) walkJson(full, out);
    else if (s.isFile() && entry.endsWith(".json") && entry !== "character.schema.json") out.push(full);
  }
  return out;
}

function listCharacterFiles(): string[] {
  return walkJson(resolve(REPO_ROOT, "game/lore/characters"));
}

function stagedCharacterFiles(): string[] {
  try {
    const out = execSync(
      "git diff --cached --name-only --diff-filter=ACMR -- 'game/lore/characters/**/*.json'",
      { encoding: "utf8", cwd: REPO_ROOT, shell: undefined }
    );
    return out
      .split("\n")
      .filter((f) => f.trim().length > 0 && !f.endsWith("character.schema.json"))
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

const files = STAGED ? stagedCharacterFiles() : listCharacterFiles();
if (STAGED && files.length === 0) {
  console.log("[character-schema] No staged character files — skipping.");
  process.exit(0);
}
if (files.length === 0) {
  console.log("[character-schema] No tracked character files found.");
  process.exit(0);
}

// Delegate validation to uv-run python (jsonschema is the canonical Python validator
// in this repo; bun has no first-class JSON Schema validator that pulls cleanly).
const validatorScript = `
import json, sys, jsonschema
schema = json.load(open(${JSON.stringify(SCHEMA_PATH)}, encoding='utf-8'))
results = []
for p in sys.argv[1:]:
    try:
        data = json.load(open(p, encoding='utf-8'))
        jsonschema.validate(data, schema)
        results.append({"path": p, "status": "PASS", "error": None})
    except jsonschema.ValidationError as e:
        results.append({"path": p, "status": "FAIL", "error": {"message": e.message, "path": list(e.absolute_path)}})
    except Exception as e:
        results.append({"path": p, "status": "ERROR", "error": {"message": str(e), "path": []}})
print(json.dumps(results))
`;

const proc = spawnSync(
  "uv",
  ["run", "--no-project", "--with", "jsonschema", "python", "-c", validatorScript, ...files],
  { cwd: REPO_ROOT, encoding: "utf8", env: { ...process.env, PYTHONUTF8: "1" } }
);

if (proc.status !== 0) {
  console.error(`[character-schema] validator subprocess failed:\n${proc.stderr}`);
  process.exit(1);
}

let results: Array<{ path: string; status: string; error: { message: string; path: unknown[] } | null }>;
try {
  results = JSON.parse(proc.stdout.trim());
} catch (e) {
  console.error(`[character-schema] could not parse validator output:\n${proc.stdout}\n---\n${proc.stderr}`);
  process.exit(1);
}

const passes = results.filter((r) => r.status === "PASS");
const fails = results.filter((r) => r.status !== "PASS");

for (const r of results) {
  const rel = r.path.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "");
  if (r.status === "PASS") {
    console.log(`[character-schema] PASS ${rel}`);
  } else {
    const where = r.error?.path && r.error.path.length > 0 ? ` (at ${r.error.path.join(".")})` : "";
    console.log(`[character-schema] ${r.status} ${rel}${where}: ${r.error?.message ?? "unknown"}`);
  }
}

mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
const manifest = {
  tool: "CI_CHECK_CHARACTER_SCHEMA_V1",
  schema_path: SCHEMA_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, ""),
  generated_at: new Date().toISOString(),
  scope: STAGED ? "staged" : "always",
  file_count: results.length,
  pass_count: passes.length,
  fail_count: fails.length,
  results: results.map((r) => ({
    path: r.path.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, ""),
    status: r.status,
    error: r.error,
  })),
};
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + "\n", "utf8");

console.log(`[character-schema] ${passes.length}/${results.length} pass — manifest at ${MANIFEST_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`);

process.exit(fails.length === 0 ? 0 : 1);
Its registry entry declares why it's manual, using one of 5 canonical reason enum values (semantic / destructive / no_tool / wrong_layer / read_only_health):


  no_auto_fix: {
    reason: "semantic",
    explanation: "Schema violations need human authoring — missing fields, type mismatches, and renamed keys all encode meaning. The schema is a contract, not a template; auto-filling would write semantically wrong content.",
    manual_remediation: "Read the failing field-path from the output (e.g. 'at lore.relationship_dynamics'). Open the character JSON and either add the missing field with appropriate content OR (if the schema is wrong) update character.schema.json with rationale.",
  },
A simpler manual-only one for contrast, c:\Users\eldno\chthonic-archive\ci\checks\bun-audit.ts (59 lines, pure subprocess wrapper, reason: "destructive"): runs bun audit --ignore <known-GHSA-ids> and exits based on its status code — no manifest, no parsing, just pass-through.

2. SID + envelope standards
Primary sources (in order of actual authority — verified against every real file, not just docs):

c:\Users\eldno\chthonic-archive\ci\checks\sid-envelope.ts — the enforcement regex (ground truth)
c:\Users\eldno\chthonic-archive\scripts\stamp_sid.ts — the prefix-derivation rule (ground truth)
c:\Users\eldno\chthonic-archive\.codex\skills\script-envelope\references\envelope-template.md — the written box template (mostly accurate, one correction below)
c:\Users\eldno\chthonic-archive\scripts\canonize_blessing.py and c:\Users\eldno\chthonic-archive\.codex\skills\script-envelope\scripts\script_envelope.py — both independently hardcode BORDER_LEN = 76
Important: c:\Users\eldno\chthonic-archive\.codex\skills\script-envelope\SKILL.md is explicitly marked STASHED ("This is a protocol rule ... not a skill. Rule belongs in AGENT_COMMON.md", stashed 2026-02-26). The intended new home, AGENT_COMMON.md, does not exist at repo root — there's only a dead-end redirect stub at c:\Users\eldno\chthonic-archive\.temple\methodology\AGENT_COMMON.md pointing to a file that was never created. So the reference doc above (inside the stashed skill) remains the de facto written spec.

@SID tag format
TypeScript: // @SID: DOMAIN_NAME_V1 (line 2, right after the shebang)
Python: # @SID: DOMAIN_NAME_V1 (can also live inside the module docstring as @SID: DOMAIN_NAME_V1)
Shape regex (enforced verbatim, identically, in both sid-envelope.ts and stamp_sid.ts):

/^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*_V\d+(_[A-Z][A-Z0-9]*)*$/
ALL_CAPS + underscores, mandatory _V<digit> version suffix, min 6 chars, and must not be one of the placeholder keywords TODO, PLACEHOLDER, FIXME, TBD, UNKNOWN, NONE, STUB, FILL_ME.
Prefix convention (from stamp_sid.ts::deriveSid, and confirmed by literally every file under ci/checks/)
Path prefix	SID prefix
ci/checks/	CI_CHECK_*
ci/ (other)	CI_*
scripts/lib/	LIB_*
scripts/ (other)	SCRIPT_*
anything else	first path segment, uppercased
For your new file at ci/checks/<name>.ts, the SID must be CI_CHECK_<NAME>_V1. Every one of the 24 files currently in ci/checks/ follows this with zero exceptions (CI_CHECK_SID_ENVELOPE_V2, CI_CHECK_BLESSING_GATE_V1, CI_CHECK_BUN_AUDIT_V1, CI_CHECK_HOMEPATH_PORTABILITY_V1, etc. — the only two outliers, GH_RUN_SMOKE_V1 and G9_SESSION_TRUNCATION_GATE_SMOKE_V1, are pre-existing drift, not the convention to copy).

The "Decorator's Blessing box" — literal template

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/<your-check-name>.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Standalone)
// ╚════════════════════════════════════════════════════════════════════════════
Rules (from envelope-template.md + script_envelope.py::build_envelope, both agree):

# ╔ / # ╠ / # ╚ (or // for TS) each followed by exactly 76 ═ characters (BORDER_LEN = 76 hardcoded in both canonize_blessing.py and script_envelope.py).
Open-sided: no right-hand border glyphs (╗ ╣ ╝) and no trailing ║ on content lines — this is explicitly enforced/stripped by script_envelope.py::strip_right_edge_box_glyphs.
Fixed field order: Title → mid-border → Wedjat-Quipu Spectrum → Temple-Ayllu Zone → Ogdoad-Ceque Radiance: → └─◄ <radiance> → bottom border.
Deprecated field names to never use: Spectral Frequency, Architectural Role, Module, Semantic ID, Exports, Flags/Modes, Cross-References.
Followed immediately by a docstring (Python) or /** ... */ block (TS) carrying @SID / @Shabti / @Purpose.
One correction to the written reference doc, based on actual precedent: envelope-template.md's generic per-extension table says .ts → Wedjat-Quipu Spectrum: ORANGE. That's true for ordinary product/extension TypeScript (verified, e.g. c:\Users\eldno\chthonic-archive\extensions\vampire-corpus\src\providers\TerminalFeedProvider.ts uses ORANGE). But every single .ts file under ci/ and the CI-tooling files under scripts/ uses GOLD instead (confirmed by tallying Wedjat-Quipu Spectrum: across ci/ and scripts/: ci/run.ts, sid-envelope.ts, python-headers.ts, uv-guard.ts, bun-audit.ts, character-schema.ts, fix_envelope.ts — all GOLD). GOLD appears to be an established override specifically for CI/governance-tooling scripts regardless of language extension. Use GOLD, not ORANGE, for your new check — that's the actual established convention for this directory, not the generic table.

Zone stays 🔭 THE OBSERVATORY for all TypeScript (including CI tooling) per the table and 100% of observed files.

Enforcement split (this matters for what will actually gate your new file)
@SID line — enforced by sid-envelope.ts, auto-fixed by stamp_sid.ts, for both .ts and .py under scripts/ and ci/. Your new check file will be checked and can be auto-stamped.
The Decorator's Blessing box itself — enforced by blessing-gate.ts, auto-fixed by scripts/canonize_blessing.py --apply, but canonize_blessing.py only globs *.py (Path.glob("*.py") / .rglob("*.py"), never .ts, at every call site in blessing-gate.ts's CANONIZE_TARGETS). There is no gate that checks or fixes the box on .ts files at all. For a new ci/checks/*.ts file, matching the box is pure hand-followed precedent — nothing will stop you if you get it wrong, but nothing will fix it for you either.
c:\Users\eldno\chthonic-archive\.meta\script-envelope.schema.json (the file you saw in git status) — full content below. This is not what's actually enforced today. It's an untracked JSON Schema for what old archived mailbox docs (codex/mailbox/archive/2026_02_10_meta_cleanup/TETRAGRAMMATON_PACKET.md) call a "universal sidecar schema" — a different, more formal idea (a companion .meta.json file per script) that I could not find referenced by any executing code path (no check validates against it, nothing generates a matching sidecar file). Treat it as dormant/aspirational scaffolding, not the live contract.
.meta/script-envelope.schema.json — full content:


{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://chthonic-archive.local/meta/script-envelope.schema.json",
  "title": "ScriptEnvelopeMetadata",
  "type": "object",
  "required": [
    "id",
    "title",
    "runtime",
    "purpose",
    "invoke",
    "exports",
    "xrefs",
    "updated_at"
  ],
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "title": { "type": "string", "minLength": 1 },
    "role": { "type": "string" },
    "purpose": { "type": "string", "minLength": 1 },
    "invoke": { "type": "string", "minLength": 1 },
    "exports": {
      "type": "array",
      "items": { "type": "string" }
    },
    "xrefs": {
      "type": "array",
      "items": { "type": "string" }
    },
    "owners": {
      "type": "array",
      "items": { "type": "string" }
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "license_spdx": { "type": "string" },
    "runtime": {
      "type": "string",
      "enum": ["python", "bun", "node", "nextjs", "unknown"]
    },
    "entrypoint": { "type": "string" },
    "updated_at": { "type": "string" }
  },
  "additionalProperties": true
}
3. Where a new check gets registered/wired
Only one file is functionally required:

c:\Users\eldno\chthonic-archive\ci\run.ts — add a new object to the CHECKS: Check[] array (currently starts at line 90). That's it. Concretely:

Write the check at ci/checks/<name>.ts.
Add an entry: name, script: "ci/checks/<name>.ts", scope ("staged" for pre-commit-relevant / "always" for repo-wide health probes), speed ("fast" unless it's genuinely slow like bun-audit or dsl-conformance), description, and exactly one of auto_fix or no_auto_fix.
If it has auto_fix, write the fixer (a new scripts/fix_<name>.ts/.py, or extend an existing generic one like scripts/fix_envelope.ts if your fix category fits its narrow scope) and point auto_fix.command/args at it.
Nothing else needs to change to make it "run in CI":

package.json's ci / ci:staged / ci:full / ci:check / ci:list scripts (lines 78–82) all just shell out to bun run ci/run.ts [flags] — they pick up any registry addition automatically.
.git/hooks/pre-commit calls ci/run.ts --staged --heal and iterates the registry dynamically — no edit needed.
--list, --autofix-list, --autofix-show <name> all read the same array live.
GitHub Actions is not in play here. The only enabled (non-.off) workflows in .github/workflows/ are claudine-cloud-dispatch.yml and pentea-cloud-dispatch.yml; neither invokes ci/run.ts or anything in ci/checks/. Every lint/gate-shaped workflow (e.g. blessing-gate.yml.off) is disabled. The local pre-commit hook running ci/run.ts is the only active enforcement path — "CI" in this repo currently means that, not GH Actions.
Optional but matches precedent: c:\Users\eldno\chthonic-archive\SCRIPTS_README.md has a ## Local CI Checks (ci/checks/) section (around line 407) with a hand-written subsection per check (SID, purpose, usage examples) — worth adding a matching subsection for documentation parity, though it has zero functional effect on whether the check runs.

Cautionary, concrete proof this registration step is easy to forget: claudine-lora-smoke.ts, federation-contract-validate.ts, session-truncation-gate.ts, and theme-icon-validate.ts are complete, well-formed check scripts sitting in ci/checks/ right now with valid SIDs and envelopes — but none has a script: entry in the CHECKS array, so none of them ever runs via bun run ci, --list, or the pre-commit hook.

4. Dominant language/runtime
Bun/TypeScript is the check-layer standard, with zero exceptions. Every file directly under ci/checks/*.ts and ci/run.ts itself is #!/usr/bin/env bun, invoked as bun run ci/checks/<name>.ts [--staged]. That's 24/24 on disk.

Python only appears one layer down, inside the fixer tools that a check's auto_fix.command shells out to (scripts/fix_headers.py, scripts/canonize_blessing.py, scripts/link_audit.py) — and in every case these are pre-existing, general-purpose repo tools (used outside CI too, e.g. canonize_blessing.py is also invoked from the disabled GH workflow and ad hoc by conductors) rather than something purpose-built for the gate. They're always invoked via uv run ... with PYTHONUTF8: "1", never bare python/python3 — that's itself a separate gate (uv-guard). Other fixers (fix_envelope.ts, stamp_sid.ts) are plain Bun/TS run directly.

There is no Rust anywhere in this gate layer (Rust exists elsewhere in the repo — Cargo.toml, tools/chthonic-mcp-server — entirely unrelated to ci/checks/).

Recommendation: write your new check as ci/checks/<name>.ts in Bun/TS, matching 100% of precedent — this isn't a stylistic preference, it's the completely uniform existing pattern. Only reach for uv run <python-tool> in the auto_fix command if the repair genuinely needs a Python library/tool that already exists in the repo for a broader purpose (e.g. jsonschema) — don't invent a new Python fixer for a TS-native text/regex fix.



Can you write a high-quality packet for continuing for Fable, because I would like to hear Claude Fable's take on this session, so we can learn from it and what we didn't catch, such as also interactivity, which is important for the trajectory of what we achieve. I only have 1% left until about approx, 40 min. 

*Session Resumption pickup-point* <—
