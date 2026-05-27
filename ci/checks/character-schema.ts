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
  // Walk filesystem (not git ls-files) so in-flight new files are picked up
  // before they're staged — the contract is "what exists on disk now."
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

// Manifest snapshot for canon-drift-snapshot consumption.
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

console.log(
  `[character-schema] ${passes.length}/${results.length} pass — manifest at ${MANIFEST_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`
);

process.exit(fails.length === 0 ? 0 : 1);
