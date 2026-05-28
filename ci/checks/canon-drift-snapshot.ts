#!/usr/bin/env bun
// @SID: CI_CHECK_CANON_DRIFT_SNAPSHOT_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/canon-drift-snapshot.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 📜 THE LIBRARY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Memory tier: reads manifest/*_audit.json from sibling membranes,
// ║       appends to manifest/canon_drift_history.ndjson)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/canon-drift-snapshot.ts — Time-series memory of lore canon state.
 *
 * Reads the manifest snapshots emitted by the membrane checks
 * (character-schema, lore-canon-paths, organ-canon-citation, lore-canon-refs)
 * and appends one summary row to manifest/canon_drift_history.ndjson.
 *
 * The history file IS the system's diary — durable record of when canon shifted,
 * what shifted, and whether the shift passed validation. Complements the
 * conversation-bound session-memory and the human-readable memory/*.md files
 * by giving a machine-readable historical signal.
 *
 * Exit code: always 0 unless the snapshot itself errors. This check is a
 * read_only_health tier — it doesn't enforce; it records.
 *
 * Usage:
 *   bun run ci/checks/canon-drift-snapshot.ts
 *
 * Run order: must run AFTER the four membrane checks so their manifests are fresh.
 * In ci/run.ts, declare a soft dependency by listing this check last among the
 * lore-* group.
 */

import { existsSync, mkdirSync, readFileSync, appendFileSync } from "fs";
import { dirname, resolve } from "path";
import { createHash } from "crypto";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const HISTORY_PATH = resolve(REPO_ROOT, "manifest/canon_drift_history.ndjson");

const SCHEMA_MANIFEST = resolve(REPO_ROOT, "manifest/character_schema_audit.json");
const PATHS_MANIFEST = resolve(REPO_ROOT, "manifest/lore_canon_paths_audit.json");
const ORGAN_MANIFEST = resolve(REPO_ROOT, "manifest/organ_canon_citation_audit.json");
const REFS_MANIFEST = resolve(REPO_ROOT, "manifest/lore_canon_refs_audit.json");
const SCHEMA_FILE = resolve(REPO_ROOT, "game/lore/characters/character.schema.json");

function readJsonOrNull(p: string): unknown | null {
  if (!existsSync(p)) return null;
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

const schemaAudit = readJsonOrNull(SCHEMA_MANIFEST) as
  | { file_count: number; pass_count: number; fail_count: number; results: Array<{ path: string; status: string }> }
  | null;
const pathsAudit = readJsonOrNull(PATHS_MANIFEST) as
  | { file_count: number; pass_count: number; fail_count: number; results: Array<{ path: string; fields: { organ?: string; tier?: number } }> }
  | null;
const organAudit = readJsonOrNull(ORGAN_MANIFEST) as
  | {
      file_count: number;
      pass_count: number;
      fail_count: number;
      deferred_count: number;
      ssot_canonical_organs: string[];
      results: Array<{ path: string; organ?: string; status: string }>;
    }
  | null;
const refsAudit = readJsonOrNull(REFS_MANIFEST) as
  | { files_scanned?: number; hit_count: number }
  | null;

let schemaHash = "absent";
if (existsSync(SCHEMA_FILE)) {
  const h = createHash("sha256");
  h.update(readFileSync(SCHEMA_FILE));
  schemaHash = h.digest("hex").slice(0, 16);
}

const missing: string[] = [];
if (!schemaAudit) missing.push("character_schema_audit.json");
if (!pathsAudit) missing.push("lore_canon_paths_audit.json");
if (!organAudit) missing.push("organ_canon_citation_audit.json");
if (!refsAudit) missing.push("lore_canon_refs_audit.json");

if (missing.length > 0) {
  console.error(
    `[canon-drift-snapshot] WARN: ${missing.length} sibling manifest(s) absent — snapshot will be partial.`
  );
  console.error(`  Missing: ${missing.join(", ")}`);
  console.error(`  Re-run the missing membrane checks first for a full snapshot.`);
}

// Organ + tier distribution
const organDistribution: Record<string, number> = {};
const tierDistribution: Record<string, number> = {};
if (pathsAudit) {
  for (const r of pathsAudit.results) {
    const organ = r.fields?.organ ?? "_unknown";
    organDistribution[organ] = (organDistribution[organ] ?? 0) + 1;
    const tier = r.fields?.tier !== undefined ? `T${r.fields.tier}` : "_unknown";
    tierDistribution[tier] = (tierDistribution[tier] ?? 0) + 1;
  }
}

const snapshot = {
  tool: "CI_CHECK_CANON_DRIFT_SNAPSHOT_V1",
  generated_at: new Date().toISOString(),
  schema_hash: schemaHash,
  ssot_canonical_organ_count: organAudit?.ssot_canonical_organs.length ?? null,
  character_count: pathsAudit?.file_count ?? schemaAudit?.file_count ?? null,
  schema: schemaAudit
    ? { pass: schemaAudit.pass_count, fail: schemaAudit.fail_count }
    : null,
  paths: pathsAudit ? { pass: pathsAudit.pass_count, fail: pathsAudit.fail_count } : null,
  organ_citation: organAudit
    ? {
        pass: organAudit.pass_count,
        fail: organAudit.fail_count,
        deferred: organAudit.deferred_count,
      }
    : null,
  refs: refsAudit
    ? {
        stale_hits: refsAudit.hit_count,
        ...(typeof refsAudit.files_scanned === "number" ? { files_scanned: refsAudit.files_scanned } : {}),
      }
    : null,
  organ_distribution: organDistribution,
  tier_distribution: tierDistribution,
  partial: missing.length > 0,
  missing_manifests: missing,
};

mkdirSync(dirname(HISTORY_PATH), { recursive: true });
appendFileSync(HISTORY_PATH, JSON.stringify(snapshot) + "\n", "utf8");

console.log(
  `[canon-drift-snapshot] appended snapshot to ${HISTORY_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`
);
console.log(`  schema_hash=${schemaHash}  characters=${snapshot.character_count}  partial=${snapshot.partial}`);
if (snapshot.organ_distribution && Object.keys(snapshot.organ_distribution).length > 0) {
  const summary = Object.entries(snapshot.organ_distribution)
    .map(([o, n]) => `${o}:${n}`)
    .join(" ");
  console.log(`  organs: ${summary}`);
}

process.exit(0);
