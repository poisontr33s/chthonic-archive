#!/usr/bin/env bun
// @SID: CI_CHECK_ORGAN_CANON_CITATION_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/organ-canon-citation.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: AMETHYST
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Sibling membrane: character-schema.ts, lore-canon-paths.ts)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/organ-canon-citation.ts — SSOT §295-326 organ-citation membrane.
 *
 * For every character with organ ≠ "_deferred_organ", asserts the organ slug is
 * present in the SSOT's Organ-Level Entity Canon (Section "Body-System-Tier-Mapping").
 * Catches drift where a character is authored claiming an organ that SSOT does not
 * yet canonize — forcing the conductor to either:
 *   (a) update SSOT first to add the organ row, or
 *   (b) place the character at _deferred_organ/T<tier>/ until SSOT promotion.
 *
 * Slug derivation: lowercase, strip non-[a-z0-9], split on whitespace, join with "_".
 * Example: "Natural Killer (NK) Cells" → "nk_cells" (manual whitelist also supported
 * for canonical short-forms like nk_cells / cerebrospinal_fluid).
 *
 * Usage:
 *   bun run ci/checks/organ-canon-citation.ts            # always-scope audit
 *   bun run ci/checks/organ-canon-citation.ts --staged   # only check staged character files
 *
 * Auto-fix: none. New organs require SSOT update (a semantic act, not mechanical).
 */

import { execSync } from "child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "fs";
import { dirname, join, relative, resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const SSOT_PATH = resolve(REPO_ROOT, ".chthonic/SSOT.md");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest/organ_canon_citation_audit.json");

const DEFERRED_ORGAN_SENTINEL = "_deferred_organ";

// Canonical slug-form for multi-word organs that don't reduce to obvious snake_case.
// Read by the slug-extractor: the slug appears in the SSOT cell once and is matched
// against this map; the directory name uses the slug.
const CANONICAL_ORGAN_SLUGS: Record<string, string> = {
  "natural killer (nk) cells": "nk_cells",
  "cerebrospinal fluid": "cerebrospinal_fluid",
  "pituitary gland": "pituitary_gland",
  "pineal gland": "pineal_gland",
  "femoral artery": "femoral_artery",
  "natural killer cells": "nk_cells",
  "olfactory bulb": "olfactory_bulb",
  "adrenal glands": "adrenal_glands",
  "apoptotic-markers": "apoptotic_markers",
  "lymph-nodes": "lymph_nodes",
};

function slugify(organName: string): string {
  const lower = organName.toLowerCase().trim();
  if (CANONICAL_ORGAN_SLUGS[lower] !== undefined) return CANONICAL_ORGAN_SLUGS[lower];
  return lower
    .replace(/\(([^)]+)\)/g, " $1 ")
    .replace(/[^a-z0-9\s_-]/g, "")
    .trim()
    .split(/\s+/)
    .join("_");
}

function extractSsotOrgans(): { canonical: Set<string>; raw: string[] } {
  if (!existsSync(SSOT_PATH)) {
    console.error(`[organ-canon-citation] FATAL: SSOT not found at ${SSOT_PATH}`);
    process.exit(1);
  }
  const text = readFileSync(SSOT_PATH, "utf8");
  const lines = text.split("\n");
  // Find the Organ-Level Entity Canon table and parse its Organ column.
  // Table header line includes "| **Organ** |" — start parsing from the row after `|---|`.
  let inTable = false;
  let headerSeen = false;
  const raw: string[] = [];
  for (const line of lines) {
    if (!headerSeen) {
      if (line.includes("**Organ**") && line.includes("**Tier**") && line.includes("**Body System**")) {
        headerSeen = true;
        continue;
      }
      continue;
    }
    if (!inTable) {
      if (/^\s*\|[\s\-:|]+\|\s*$/.test(line)) {
        inTable = true;
      }
      continue;
    }
    // In-table — rows start with "|" and have ≥4 pipes. Empty line or non-pipe terminates.
    if (!line.trim().startsWith("|")) break;
    const cells = line.split("|").map((c) => c.trim());
    // cells[0] = "" (leading pipe), cells[1] = Tier, cells[2] = Organ, ...
    if (cells.length >= 3 && cells[2].length > 0) {
      // Strip bolding ** from organ name
      const organ = cells[2].replace(/\*\*/g, "").trim();
      if (organ) raw.push(organ);
    }
  }
  const canonical = new Set<string>(raw.map(slugify));
  canonical.add(DEFERRED_ORGAN_SENTINEL); // always accepted
  return { canonical, raw };
}

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

const { canonical, raw } = extractSsotOrgans();
console.log(
  `[organ-canon-citation] SSOT canonical organs (${canonical.size - 1}): ${[...canonical].filter((s) => s !== DEFERRED_ORGAN_SENTINEL).sort().join(", ")}`
);

const files = STAGED ? stagedCharacterFiles() : listCharacterFiles();
if (STAGED && files.length === 0) {
  console.log("[organ-canon-citation] No staged character files — skipping.");
  process.exit(0);
}
if (files.length === 0) {
  console.log("[organ-canon-citation] No tracked character files found.");
  process.exit(0);
}

type Finding = {
  path: string;
  organ: string | undefined;
  status: "PASS" | "FAIL" | "DEFERRED";
  reason?: string;
};

const results: Finding[] = [];

for (const rel of files) {
  const full = resolve(REPO_ROOT, rel);
  if (!existsSync(full)) continue;
  let data: { organ?: string };
  try {
    data = JSON.parse(readFileSync(full, "utf8"));
  } catch (e: unknown) {
    results.push({
      path: rel,
      organ: undefined,
      status: "FAIL",
      reason: `JSON parse error: ${(e as Error).message}`,
    });
    continue;
  }
  const organ = data.organ;
  if (organ === DEFERRED_ORGAN_SENTINEL) {
    results.push({ path: rel, organ, status: "DEFERRED" });
  } else if (organ && canonical.has(organ)) {
    results.push({ path: rel, organ, status: "PASS" });
  } else {
    results.push({
      path: rel,
      organ,
      status: "FAIL",
      reason: organ
        ? `organ '${organ}' not in SSOT §295-326 (canonical: ${[...canonical].filter((s) => s !== DEFERRED_ORGAN_SENTINEL).sort().join(", ")})`
        : "organ field missing or empty",
    });
  }
}

const passes = results.filter((r) => r.status === "PASS");
const fails = results.filter((r) => r.status === "FAIL");
const deferred = results.filter((r) => r.status === "DEFERRED");

for (const r of results) {
  if (r.status === "PASS") {
    console.log(`[organ-canon-citation] PASS     ${r.path}  (organ: ${r.organ})`);
  } else if (r.status === "DEFERRED") {
    console.log(`[organ-canon-citation] DEFERRED ${r.path}  (organ assignment pending SSOT promotion)`);
  } else {
    console.log(`[organ-canon-citation] FAIL     ${r.path}: ${r.reason}`);
  }
}

mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
const manifest = {
  tool: "CI_CHECK_ORGAN_CANON_CITATION_V1",
  ssot_path: SSOT_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, ""),
  generated_at: new Date().toISOString(),
  scope: STAGED ? "staged" : "always",
  ssot_canonical_organs: [...canonical].filter((s) => s !== DEFERRED_ORGAN_SENTINEL).sort(),
  ssot_organs_raw: raw,
  file_count: results.length,
  pass_count: passes.length,
  fail_count: fails.length,
  deferred_count: deferred.length,
  results,
};
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + "\n", "utf8");

console.log(
  `[organ-canon-citation] ${passes.length} PASS, ${deferred.length} DEFERRED, ${fails.length} FAIL — manifest at ${MANIFEST_PATH.replace(REPO_ROOT, "").replace(/\\/g, "/").replace(/^\//, "")}`
);

process.exit(fails.length === 0 ? 0 : 1);
