#!/usr/bin/env bun
// @SID: MD_TYPES_SCAN_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ scripts/md_types_scan.ts
// ║
// ║ Scans the repo for typed .md files (frontmatter `type:` field) and
// ║ converts them to Euler-roulette entries in manifest/md_types.json.
// ║
// ║ Each MD type maps to a roulette tag and a weight formula:
// ║
// ║   liminal  → tag:liminal  weight grows with decay urgency (5→10)
// ║   scaffold → tag:scaffold weight grows with age (+1/week, base 6)
// ║   stewardess → tag:session weight=9 (session-scoped, not persisted)
// ║   concept  → tag:lore     weight=5 (stable reference)
// ║   method   → tag:infra    weight=6 (operational)
// ║   strategy → tag:ssot     weight=7 (strategic layer)
// ║   gate     → tag:ci       weight=8 (gate tracking)
// ║   research → tag:lore     weight=5
// ║   role     → tag:entity   weight=5
// ║   spine    → tag:ssot     weight=6
// ║
// ║ Usage:
// ║   bun run scripts/md_types_scan.ts          (scan + write manifest)
// ║   bun run scripts/md_types_scan.ts --dry-run (print entries, no write)
// ║   bun run scripts/md_types_scan.ts --report  (full JSON to stdout)
// ╚════════════════════════════════════════════════════════════════════════════

import { readdirSync, readFileSync, writeFileSync, existsSync, statSync } from "fs";
import { join, basename, extname, relative } from "path";
import { randomUUID } from "crypto";

const ROOT = join(import.meta.dir, "..");
const OUT_PATH = join(ROOT, "manifest", "md_types.json");
const DRY_RUN = process.argv.includes("--dry-run");
const REPORT = process.argv.includes("--report");

// ── Tag mappings ──────────────────────────────────────────────────────────────

const MD_TYPE_TO_TAG: Record<string, string> = {
  liminal:    "liminal",
  scaffold:   "scaffold",
  stewardess: "session",
  concept:    "lore",
  method:     "infra",
  strategy:   "ssot",
  gate:       "ci",
  ledger:     "handoff",
  research:   "lore",
  role:       "entity",
  milfological: "entity",
  spine:      "ssot",
};

const TYPE_BASE_WEIGHT: Record<string, number> = {
  liminal:    5,
  scaffold:   6,
  stewardess: 9,
  concept:    5,
  method:     6,
  strategy:   7,
  gate:       8,
  ledger:     4,
  research:   5,
  role:       5,
  milfological: 6,
  spine:      6,
};

// ── Frontmatter parser ────────────────────────────────────────────────────────

interface Frontmatter {
  type?: string;
  id?: string;
  session?: string;
  filed?: string;
  decay_date?: string;
  decay_condition?: string;
  holds_up?: string;
  removal_condition?: string;
  scope?: string;
  pressure_level?: string;
  weight?: string;
  title?: string;
  expires?: string;
}

function parseFrontmatter(content: string): Frontmatter {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const fm: Frontmatter = {};
  for (const line of match[1].split("\n")) {
    const m = line.match(/^(\w+):\s*(.*)/);
    if (m) {
      const key = m[1].trim() as keyof Frontmatter;
      // Strip YAML block scalar indicators and quotes
      const val = m[2].trim().replace(/^[>|]$/, "").replace(/^["']|["']$/g, "");
      (fm as Record<string, string>)[key] = val;
    }
  }
  return fm;
}

// ── Weight formulas ───────────────────────────────────────────────────────────

function liminalWeight(fm: Frontmatter): number {
  const filed = fm.filed ?? new Date().toISOString().slice(0, 10);
  const decay = fm.decay_date;
  if (!decay) return TYPE_BASE_WEIGHT.liminal;
  const totalDays = (new Date(decay).getTime() - new Date(filed).getTime()) / 86400000;
  const daysLeft = (new Date(decay).getTime() - Date.now()) / 86400000;
  if (daysLeft <= 0) return 10; // past deadline — maximum urgency
  const urgency = 1 - Math.max(0, daysLeft) / Math.max(1, totalDays);
  return Math.round(TYPE_BASE_WEIGHT.liminal + urgency * 5);
}

function scaffoldWeight(fm: Frontmatter): number {
  const base = fm.weight ? parseInt(fm.weight, 10) : TYPE_BASE_WEIGHT.scaffold;
  const filed = fm.filed ?? new Date().toISOString().slice(0, 10);
  const ageDays = (Date.now() - new Date(filed).getTime()) / 86400000;
  return Math.min(10, base + Math.floor(ageDays / 7)); // +1 per week
}

function typeWeight(type: string, fm: Frontmatter): number {
  if (type === "liminal") return liminalWeight(fm);
  if (type === "scaffold") return scaffoldWeight(fm);
  if (fm.weight) return Math.min(10, Math.max(1, parseInt(fm.weight, 10)));
  return TYPE_BASE_WEIGHT[type] ?? 5;
}

// ── Title extractor ───────────────────────────────────────────────────────────

function extractTitle(content: string, filename: string): string {
  // Try first H1 after frontmatter
  const afterFm = content.replace(/^---[\s\S]*?---\n/, "");
  const h1 = afterFm.match(/^#\s+(.+)/m);
  if (h1) return h1[1].replace(/[^a-zA-Z0-9\s\-_:().—–]/g, "").trim();
  // Fallback: filename without extension
  return basename(filename, extname(filename)).replace(/[_-]/g, " ");
}

function rouletteTitle(type: string, title: string, fm: Frontmatter): string {
  if (type === "liminal") return `↯ Promote or decay: ${title}`;
  if (type === "scaffold") return `⚠ Check removal: ${title}`;
  if (type === "stewardess") return `⚡ Stewardess: ${fm.session ?? title}`;
  return title;
}

// ── File scanner ──────────────────────────────────────────────────────────────

interface MdTypeEntry {
  id: string;
  title: string;
  tags: string[];
  created: string;
  weight: number;
  origin: string;
  source: string;
  source_file: string;
  md_type: string;
  spin_count: number;
  meta?: Record<string, string>;
}

function scanDir(dir: string, filter?: (f: string) => boolean): MdTypeEntry[] {
  const entries: MdTypeEntry[] = [];
  if (!existsSync(dir)) return entries;
  const files = readdirSync(dir);
  for (const file of files) {
    const fullPath = join(dir, file);
    if (statSync(fullPath).isDirectory()) continue;
    if (extname(file) !== ".md") continue;
    if (filter && !filter(file)) continue;

    const content = readFileSync(fullPath, "utf8");
    const fm = parseFrontmatter(content);
    const type = fm.type;
    if (!type || !MD_TYPE_TO_TAG[type]) continue;

    const rawTitle = extractTitle(content, file);
    const title = rouletteTitle(type, rawTitle, fm);
    const tag = MD_TYPE_TO_TAG[type];
    const weight = typeWeight(type, fm);
    const filed = fm.filed ?? fm.session ?? new Date().toISOString().slice(0, 10);
    const created = new Date(filed).toISOString();

    const meta: Record<string, string> = {};
    if (fm.decay_date) meta.decay_date = fm.decay_date;
    if (fm.decay_condition) meta.decay_condition = fm.decay_condition.slice(0, 80) + "…";
    if (fm.holds_up) meta.holds_up = fm.holds_up;
    if (fm.removal_condition) meta.removal_condition = fm.removal_condition;
    if (fm.pressure_level) meta.pressure_level = fm.pressure_level;

    entries.push({
      id: `md_${type}_${basename(file, ".md").slice(0, 16).replace(/[^a-zA-Z0-9]/g, "_")}`,
      title,
      tags: [tag],
      created,
      weight,
      origin: "md-types",
      source: "md-types",
      source_file: relative(ROOT, fullPath),
      md_type: type,
      spin_count: 0,
      meta: Object.keys(meta).length > 0 ? meta : undefined,
    });
  }
  return entries;
}

// ── Scan targets ──────────────────────────────────────────────────────────────

function scanAll(): MdTypeEntry[] {
  const entries: MdTypeEntry[] = [];

  // docs/liminal/ — all .md files
  entries.push(...scanDir(join(ROOT, "docs", "liminal")));

  // docs/reference/ — SCAFFOLD_* prefix only
  entries.push(...scanDir(join(ROOT, "docs", "reference"), f => f.startsWith("SCAFFOLD_")));

  // docs/concepts/, docs/methods/, docs/strategy/ — if they exist
  for (const sub of ["concepts", "methods", "strategy"]) {
    entries.push(...scanDir(join(ROOT, "docs", sub)));
  }

  // claude/stewardess/ — session-scoped, ephemeral (gitignored but may exist on disk)
  entries.push(...scanDir(join(ROOT, "claude", "stewardess")));

  return entries;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const entries = scanAll();

if (DRY_RUN || REPORT) {
  if (REPORT) {
    console.log(JSON.stringify({ generated: new Date().toISOString(), count: entries.length, entries }, null, 2));
  } else {
    console.log(`Found ${entries.length} typed MD entries:\n`);
    for (const e of entries) {
      const weight = String(e.weight).padStart(2);
      console.log(`  [${e.md_type.padEnd(12)}] w${weight}  ${e.title}`);
      if (e.meta?.decay_date) console.log(`             decay: ${e.meta.decay_date}`);
      if (e.meta?.holds_up) console.log(`             holds_up: ${e.meta.holds_up}`);
    }
  }
  process.exit(0);
}

const output = {
  generated: new Date().toISOString(),
  count: entries.length,
  entries,
};

writeFileSync(OUT_PATH, JSON.stringify(output, null, 2), "utf8");
console.log(`✅ manifest/md_types.json written (${entries.length} entries)`);
for (const e of entries) {
  console.log(`   [${e.md_type.padEnd(10)}] w${e.weight}  ${e.title}`);
}
