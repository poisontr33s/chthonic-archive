#!/usr/bin/env bun
// @SID: CI_CHECK_LORE_CANON_PATHS_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/lore-canon-paths.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: AMETHYST
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Sibling membrane: character-schema.ts, organ-canon-citation.ts)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/lore-canon-paths.ts — Filesystem-shape membrane for character JSONs.
 *
 * Asserts that each game/lore/characters/<organ>/<tier>/<char_id>.json file is at
 * the path implied by its content:
 *   - parent dir slug   == file's `organ` field
 *   - parent-parent dir == "T" + file's `tier` (e.g. T1, T1.5, T3)
 *   - basename (sans .json) == file's `character_id`
 *
 * Catches "file moved to wrong directory" or "organ field edited but file not moved"
 * drift before it ships.
 *
 * Usage:
 *   bun run ci/checks/lore-canon-paths.ts            # always-scope audit
 *   bun run ci/checks/lore-canon-paths.ts --staged   # only check staged character files
 *
 * Auto-fix: none in V1. The mechanical move IS safe when content and path agree
 * (which means the path is wrong); but distinguishing "wrong path" from "wrong
 * content" needs human judgment. Surfaced via manual_remediation.
 */

import { execSync } from "child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "fs";
import { dirname, join, relative, resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest/lore_canon_paths_audit.json");

function walkJsonRel(dir: string, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const s = statSync(full);
    if (s.isDirectory()) walkJsonRel(full, out);
    else if (s.isFile() && entry.endsWith(".json") && entry !== "character.schema.json") {
      out.push(relative(REPO_ROOT, full).replace(/\\/g, "/"));
    }
  }
  return out;
}

function listCharacterFiles(): string[] {
  // Filesystem walk — picks up in-flight new files; matches the actual disk state.
  return walkJsonRel(resolve(REPO_ROOT, "game/lore/characters"));
}

function stagedCharacterFiles(): string[] {
  try {
    const out = execSync(
      "git diff --cached --name-only --diff-filter=ACMR -- 'game/lore/characters/**/*.json'",
      { encoding: "utf8", cwd: REPO_ROOT }
    );
    return out
      .split("\n")
      .filter((f) => f.trim().length > 0 && !f.endsWith("character.schema.json"));
  } catch {
    return [];
  }
}

const files = STAGED ? stagedCharacterFiles() : listCharacterFiles();
if (STAGED && files.length === 0) {
  console.log("[lore-canon-paths] No staged character files — skipping.");
  process.exit(0);
}
if (files.length === 0) {
  console.log("[lore-canon-paths] No tracked character files found.");
  process.exit(0);
}

type Finding = {
  path: string;
  status: "PASS" | "FAIL";
  reasons: string[];
  expected_path?: string;
  fields: { character_id?: string; organ?: string; tier?: number };
};

const results: Finding[] = [];

for (const rel of files) {
  const full = resolve(REPO_ROOT, rel);
  if (!existsSync(full)) {
    // Staged-rename can name a file no longer present; skip with no finding.
    continue;
  }
  let data: { character_id?: string; organ?: string; tier?: number };
  try {
    data = JSON.parse(readFileSync(full, "utf8"));
  } catch (e: unknown) {
    results.push({
      path: rel,
      status: "FAIL",
      reasons: [`JSON parse error: ${(e as Error).message}`],
      fields: {},
    });
    continue;
  }

  const parts = rel.split("/");
  // expected shape: game/lore/characters/<organ>/<tierDir>/<basename>.json
  if (parts.length !== 6 || parts[0] !== "game" || parts[1] !== "lore" || parts[2] !== "characters") {
    results.push({
      path: rel,
      status: "FAIL",
      reasons: [
        `Path depth wrong (got ${parts.length} segments, expected 6: game/lore/characters/<organ>/T<tier>/<id>.json)`,
      ],
      fields: { character_id: data.character_id, organ: data.organ, tier: data.tier },
    });
    continue;
  }
  const [, , , dirOrgan, dirTier, baseFull] = parts;
  const baseId = baseFull.replace(/\.json$/, "");
  const reasons: string[] = [];

  if (data.organ !== dirOrgan) {
    reasons.push(`organ field '${data.organ}' != parent dir '${dirOrgan}'`);
  }
  const expectedTierDir = `T${data.tier}`;
  if (dirTier !== expectedTierDir) {
    reasons.push(`tier ${data.tier} maps to dir '${expectedTierDir}', got '${dirTier}'`);
  }
  if (data.character_id !== baseId) {
    reasons.push(`character_id '${data.character_id}' != filename '${baseId}'`);
  }

  if (reasons.length === 0) {
    results.push({
      path: rel,
      status: "PASS",
      reasons: [],
      fields: { character_id: data.character_id, organ: data.organ, tier: data.tier },
    });
  } else {
    const expectedPath = `game/lore/characters/${data.organ}/T${data.tier}/${data.character_id}.json`;
    results.push({
      path: rel,
      status: "FAIL",
      reasons,
      expected_path: expectedPath,
      fields: { character_id: data.character_id, organ: data.organ, tier: data.tier },
    });
  }
}

const passes = results.filter((r) => r.status === "PASS");
const fails = results.filter((r) => r.status === "FAIL");

for (const r of results) {
  if (r.status === "PASS") {
    console.log(`[lore-canon-paths] PASS ${r.path}`);
  } else {
    console.log(`[lore-canon-paths] FAIL ${r.path}`);
    for (const reason of r.reasons) console.log(`                       - ${reason}`);
    if (r.expected_path) console.log(`                       expected_path: ${r.expected_path}`);
  }
}

mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
const manifest = {
  tool: "CI_CHECK_LORE_CANON_PATHS_V1",
  generated_at: new Date().toISOString(),
  scope: STAGED ? "staged" : "always",
  file_count: results.length,
  pass_count: passes.length,
  fail_count: fails.length,
  results,
};
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + "\n", "utf8");

console.log(
  `[lore-canon-paths] ${passes.length}/${results.length} pass — manifest at ${MANIFEST_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`
);

process.exit(fails.length === 0 ? 0 : 1);
