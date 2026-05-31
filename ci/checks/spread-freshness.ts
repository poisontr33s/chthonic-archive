#!/usr/bin/env bun
// @SID: CI_CHECK_SPREAD_FRESHNESS_V1

/**
 * ci/checks/spread-freshness.ts — Read-only health probe for the spread index.
 *
 * Reads manifest/spread_index.json (the wide-angle polyglot scan emitted by
 * scripts/spread-sweep.ts) and reports its currency + headline shape. Surfaces
 * the snipe/sweep/noise classification + native-stack count + age in days, so
 * the spread doesn't silently rot.
 *
 * Exit code: always 0 unless --max-age-days <N> is passed AND the manifest is
 * older than N days (opt-in strict mode). Default behavior is health-surface,
 * not enforcement — the spread is exploratory metadata, not a contract.
 *
 * Usage:
 *   bun run ci/checks/spread-freshness.ts                    # surface only
 *   bun run ci/checks/spread-freshness.ts --max-age-days 14  # fail if older than 14d
 *
 * Refresh: `bun run scripts/spread-sweep.ts --summary` regenerates the manifest.
 */

import { existsSync, readFileSync, statSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const INDEX_PATH = resolve(REPO_ROOT, "manifest/spread_index.json");

const MAX_AGE_IDX = process.argv.indexOf("--max-age-days");
const MAX_AGE_DAYS = MAX_AGE_IDX !== -1 ? parseInt(process.argv[MAX_AGE_IDX + 1] ?? "", 10) : null;

if (!existsSync(INDEX_PATH)) {
  console.log("[spread-freshness] manifest/spread_index.json absent");
  console.log("[spread-freshness] refresh with: bun run scripts/spread-sweep.ts --summary");
  // Read-only health — absent manifest is informational, not a failure.
  process.exit(0);
}

interface SpreadIndex {
  generated_at: string;
  root_dirs: string[];
  project_count: number;
  projects: Array<{
    name: string;
    languages: string[];
    mode_hint: "snipe" | "sweep" | "noise";
    has_native_stack: boolean;
    repurposability_score: number;
    total_source_lines: number;
  }>;
}

let idx: SpreadIndex;
try {
  idx = JSON.parse(readFileSync(INDEX_PATH, "utf8")) as SpreadIndex;
} catch (err) {
  console.error(`[spread-freshness] failed to parse spread_index.json: ${err}`);
  process.exit(1);
}

// Compute age from generated_at (preferred) or fall back to mtime.
let ageMs: number;
let ageSource: string;
const generatedAt = idx.generated_at ? new Date(idx.generated_at).getTime() : NaN;
if (!Number.isNaN(generatedAt)) {
  ageMs = Date.now() - generatedAt;
  ageSource = "generated_at";
} else {
  const stat = statSync(INDEX_PATH);
  ageMs = Date.now() - stat.mtimeMs;
  ageSource = "mtime";
}
const ageDays = ageMs / (1000 * 60 * 60 * 24);

// Aggregate the shape.
const modeCounts = { snipe: 0, sweep: 0, noise: 0 };
let nativeCount = 0;
let polyglotCount = 0;
let totalLines = 0;
for (const p of idx.projects ?? []) {
  if (p.mode_hint) modeCounts[p.mode_hint]++;
  if (p.has_native_stack) nativeCount++;
  if ((p.languages ?? []).length > 1) polyglotCount++;
  totalLines += p.total_source_lines ?? 0;
}

console.log(
  `[spread-freshness] ${idx.project_count} projects | snipe=${modeCounts.snipe} sweep=${modeCounts.sweep} noise=${modeCounts.noise} | native-stack=${nativeCount} polyglot=${polyglotCount}`,
);
console.log(
  `[spread-freshness] total source lines: ${totalLines.toLocaleString()} | roots: ${(idx.root_dirs ?? []).join(", ")}`,
);
console.log(
  `[spread-freshness] age: ${ageDays.toFixed(1)} days (via ${ageSource})`,
);

if (MAX_AGE_DAYS != null && Number.isFinite(MAX_AGE_DAYS)) {
  if (ageDays > MAX_AGE_DAYS) {
    console.error(
      `[spread-freshness] FAIL — manifest age ${ageDays.toFixed(1)}d exceeds --max-age-days ${MAX_AGE_DAYS}d`,
    );
    console.error(`[spread-freshness] refresh: bun run scripts/spread-sweep.ts --summary`);
    process.exit(1);
  }
  console.log(`[spread-freshness] OK — within --max-age-days ${MAX_AGE_DAYS}d threshold`);
}

process.exit(0);
