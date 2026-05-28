#!/usr/bin/env bun
// @SID: CI_CHECK_LORE_CANON_REFS_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/lore-canon-refs.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: AMETHYST
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Sibling membrane: character-schema.ts, lore-canon-paths.ts, organ-canon-citation.ts)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/lore-canon-refs.ts — Stale-path drift detection for character canon refs.
 *
 * Greps active markdown and json files for path strings of shape
 *   game/lore/characters/<id>.json
 * (flat — no organ/tier segment). Stale-ness is derived from the current
 * git-tracked game/lore/characters tree: if that exact flat file is not tracked
 * now, the ref is stale. When a current nested character file with the same
 * basename exists, this check reports that canonical target.
 *
 * Scope: active files only. Frozen archives (claude/mailbox/GEMINI_POC_BACKBONE_BUNDLE_*,
 * claude/mailbox/GEMINI3_1_PRO_DEEP_RESEARCH_ARTIFACTS/, dumpster-dive/, node_modules/)
 * are excluded — their refs are historical snapshots, not drift.
 *
 * Usage:
 *   bun run ci/checks/lore-canon-refs.ts            # always-scope audit
 *   bun run ci/checks/lore-canon-refs.ts --staged   # only check staged files
 *
 * Auto-fix: none. Path-corrections need to know the new organ/tier dir, which
 * is in the character file's own content. The character-schema + lore-canon-paths
 * checks resolve the canonical path; that path then becomes the rewrite target.
 * Could be added in V2 by reading manifest/lore_canon_paths_audit.json and
 * mechanically rewriting; deliberately deferred to keep V1 narrow.
 */

import { execSync } from "child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { dirname, resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest/lore_canon_refs_audit.json");
const CHARACTER_SCHEMA_PATH = "game/lore/characters/character.schema.json";

// Flat path pattern: game/lore/characters/<id>.json with NO organ/tier segments.
const FLAT_REF_RE = /game\/lore\/characters\/[A-Za-z0-9_.-]+\.json/g;

const EXCLUDE_DIRS = [
  // Frozen archives: refs are historical snapshots of past state, not active drift.
  "claude/mailbox/GEMINI_POC_BACKBONE_BUNDLE_2026_05_26",
  "claude/mailbox/GEMINI3_1_PRO_DEEP_RESEARCH_ARTIFACTS",
  "claude/mailbox/GEMINI_POC_BACKBONE_RESEARCH_BRIEF_2026_05_26.md",
  "dumpster-dive/",
  "node_modules/",
  // Session memory + compaction artifacts: machine-generated diary entries of
  // session state at snapshot time. Like the bundle: frozen by intent.
  "manifest/sessions/",
  // Don't grep ourselves (our own pattern declaration would always self-match)
  "manifest/lore_canon_refs_audit.json",
  "ci/checks/lore-canon-refs.ts",
];

const EXCLUDE_FILE_PATTERNS = [
  // Session compaction snapshots: per-session manifest captures, not active canon.
  /^manifest\/session_compaction_[0-9a-f]+\.json$/,
  // Session blood/scoring artifacts: machine-generated snapshots.
  /^manifest\/session_blood\.json$/,
  /^manifest\/gpu_scores_[0-9a-f]+\.json$/,
];

function isExcluded(path: string): boolean {
  const norm = path.replace(/\\/g, "/");
  if (EXCLUDE_DIRS.some((ex) => norm.startsWith(ex) || norm.includes(`/${ex}`))) return true;
  if (EXCLUDE_FILE_PATTERNS.some((re) => re.test(norm))) return true;
  return false;
}

function trackedFiles(): string[] {
  try {
    const out = execSync("git ls-files", { encoding: "utf8", cwd: REPO_ROOT });
    return out
      .split("\n")
      .map((f) => f.trim())
      .filter((f) => f.length > 0)
      .filter((f) => /\.(md|json|ts|py|ps1|yml|yaml|toml|gitignore)$/.test(f) || f.endsWith(".gitignore"))
      .filter((f) => !isExcluded(f));
  } catch {
    return [];
  }
}

function stagedFiles(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=ACMR", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .map((f) => f.trim())
      .filter((f) => f.length > 0)
      .filter((f) => /\.(md|json|ts|py|ps1|yml|yaml|toml|gitignore)$/.test(f) || f.endsWith(".gitignore"))
      .filter((f) => !isExcluded(f));
  } catch {
    return [];
  }
}

type CharacterPathIndex = {
  trackedFlatPaths: Set<string>;
  canonicalByFlatPath: Map<string, string>;
};

function characterPathIndex(): CharacterPathIndex {
  const trackedFlatPaths = new Set<string>();
  const canonicalByFlatPath = new Map<string, string>();
  let out = "";

  try {
    out = execSync("git ls-files game/lore/characters", { encoding: "utf8", cwd: REPO_ROOT });
  } catch {
    return { trackedFlatPaths, canonicalByFlatPath };
  }

  const characterFiles = out
    .split("\n")
    .map((f) => f.trim().replace(/\\/g, "/"))
    .filter((f) => f.length > 0)
    .filter((f) => f.endsWith(".json"))
    .filter((f) => f !== "game/lore/characters/character.schema.json");

  for (const rel of characterFiles) {
    const parts = rel.split("/");
    if (parts.length === 4) {
      trackedFlatPaths.add(rel);
      continue;
    }

    const basename = parts[parts.length - 1];
    if (!basename) continue;
    canonicalByFlatPath.set(`game/lore/characters/${basename}`, rel);
  }

  return { trackedFlatPaths, canonicalByFlatPath };
}

const files = STAGED ? stagedFiles() : trackedFiles();
if (files.length === 0) {
  console.log("[lore-canon-refs] No files in scope — skipping.");
  process.exit(0);
}

type Hit = { path: string; line: number; match: string; canonical_path?: string };
const paths = characterPathIndex();
const hits: Hit[] = [];

for (const rel of files) {
  const full = resolve(REPO_ROOT, rel);
  if (!existsSync(full)) continue;
  let text: string;
  try {
    text = readFileSync(full, "utf8");
  } catch {
    continue;
  }
  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const matches = lines[i].match(FLAT_REF_RE);
    if (!matches) continue;
    for (const m of matches) {
      if (m === CHARACTER_SCHEMA_PATH) continue;
      if (paths.trackedFlatPaths.has(m)) continue;
      const canonical_path = paths.canonicalByFlatPath.get(m);
      hits.push({ path: rel, line: i + 1, match: m, ...(canonical_path ? { canonical_path } : {}) });
    }
  }
}

if (hits.length === 0) {
  console.log(`[lore-canon-refs] PASS — no stale flat-path refs found across ${files.length} files`);
} else {
  console.log(`[lore-canon-refs] FAIL — ${hits.length} stale flat-path ref(s) across active files:`);
  for (const h of hits) {
    const target = h.canonical_path ? `  -> ${h.canonical_path}` : "";
    console.log(`  ${h.path}:${h.line}  ${h.match}${target}`);
  }
  console.log("");
  console.log("To fix: replace each flat path with the current canonical target shown above.");
  console.log("If no target is shown, the ref points at no current tracked character file.");
}

mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
const manifest = {
  tool: "CI_CHECK_LORE_CANON_REFS_V1",
  hit_count: hits.length,
  hits,
  excluded_dirs: EXCLUDE_DIRS,
};
const nextManifest = JSON.stringify(manifest, null, 2) + "\n";
let previousManifest = "";
if (existsSync(MANIFEST_PATH)) {
  try {
    previousManifest = readFileSync(MANIFEST_PATH, "utf8");
  } catch {
    previousManifest = "";
  }
}

if (previousManifest !== nextManifest) {
  writeFileSync(MANIFEST_PATH, nextManifest, "utf8");
}

console.log(
  `[lore-canon-refs] manifest ${previousManifest === nextManifest ? "unchanged" : "updated"} at ${MANIFEST_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`
);

process.exit(hits.length === 0 ? 0 : 1);
