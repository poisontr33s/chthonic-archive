#!/usr/bin/env bun
// @SID: pnk_archaeology — PsychoNoir-Kontrapunkt data-archaeology scanner
// @VERSION: 1.0.0
// @AUTHOR: chthonic-archive
//
// PURPOSE:
//   Full-repo archaeological scan of the PsychoNoir-Kontrapunkt satellite repo.
//   Classifies every file by content type and signal value, detects entity mentions,
//   and emits a structured manifest for iterative repurposing.
//
// Usage:
//   bun run scripts/pnk_archaeology.ts [--scan] [--report] [options]
//   bun run scripts/pnk_archaeology.ts --scan
//   bun run scripts/pnk_archaeology.ts --report
//   bun run scripts/pnk_archaeology.ts --report --min-signal 6
//   bun run scripts/pnk_archaeology.ts --report --category entity-canonical
//   bun run scripts/pnk_archaeology.ts --report --category session-artifact --show-content
//   bun run scripts/pnk_archaeology.ts --report --dir claudines_captains_quarters
//   bun run scripts/pnk_archaeology.ts --scan --source <path>
//
// Output: manifest/pnk_archaeology.json

import { readdir, readFile, stat } from "fs/promises";
import { join, relative, extname, basename, dirname } from "path";
import { existsSync, writeFileSync, mkdirSync } from "fs";

// ─── TYPES ──────────────────────────────────────────────────────────────────

interface ArchaeologyEntry {
  relPath: string;
  category: Category;
  signal: number;          // 1–10
  sizeBytes: number;
  ext: string;
  preview: string;         // first 3 non-empty lines joined
  entities: string[];      // detected entity mentions
  concepts: string[];      // detected concept tags
  language: "no" | "en" | "mixed" | "code" | "data" | "binary";
  note?: string;           // human-readable classification rationale
}

interface ArchaeologyManifest {
  generated: string;
  sourcePath: string;
  totalFiles: number;
  totalSignalFiles: number;  // signal >= 5
  categoryBreakdown: Record<string, number>;
  entityMentions: Record<string, number>;
  entries: ArchaeologyEntry[];
}

type Category =
  | "entity-canonical"      // Claudine manifests, revelation docs, entity protocols
  | "world-protocol"        // district creation, generation protocols, world rules
  | "concept-draft"         // worldbuilding notes, design docs, Norwegian sketches
  | "session-artifact"      // session logs, restoration state, chat history with lineage
  | "dialogue-data"         // raw character dialogue CSVs, fiction text corpus
  | "data-artifact"         // JSONs, structured outputs (non-manifest)
  | "chaos-engineering"     // prototype scripts, orchestrators, automators
  | "configuration"         // package.json, tsconfig, bunfig, .gitignore
  | "transient"             // backups, temp files, quantum_backup clones
  | "noise";                // deployment reports, marketing docs, irrelevant

// ─── SKIP LISTS ─────────────────────────────────────────────────────────────

const SKIP_DIRS = new Set([
  "node_modules", ".git", "__pycache__", ".ipynb_checkpoints",
  "temp_build", "tmp", "dist", ".venv", "venv",
  "temporal_backups", ".cache",
]);

// Files to skip entirely
const SKIP_FILES = new Set([
  ".DS_Store", "Thumbs.db", "package-lock.json",
]);

const SKIP_EXTS = new Set([
  ".pyc", ".pyo", ".class", ".o", ".obj", ".exe",
  ".dll", ".so", ".dylib", ".wasm",
  ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
  ".mp4", ".mp3", ".wav", ".avi",
  ".zip", ".tar", ".gz", ".7z",
  ".pdf", ".docx", ".xlsx",
]);

// ─── ENTITY DETECTOR ────────────────────────────────────────────────────────

const ENTITY_PATTERNS: Array<[string, RegExp]> = [
  ["Claudine",          /claudine/i],
  ["Iron Maiden",       /iron.?maiden/i],
  ["Astrid Møller",     /astrid.?m[øo]ller/i],
  ["Skyskraperen",      /skyskraperen/i],
  ["Rustbeltet",        /rustbeltet/i],
  ["Kausalitets-Arkitekten", /kausalitets.?arkitekten/i],
  ["Usynlige Hånd",     /usynlige.?h[åa]nd/i],
  ["MILF Matriarch",    /milf.?matriarch/i],
  ["Pentea",            /pentea/i],
  ["Orackla",           /orackla/i],
  ["Umeko",             /umeko/i],
  ["Lysandra",          /lysandra/i],
  ["Vera Steel",        /vera.?steel/i],
  ["Raven Bytes",       /raven.?bytes/i],
  ["Eva Green",         /eva.?green/i],
  ["Yukiko Tanaka",     /yukiko.?tanaka/i],
  ["SSOT",              /\bssot\b/i],
];

const CONCEPT_PATTERNS: Array<[string, RegExp]> = [
  ["wet-paper-to-gold", /wet.?paper.?to.?gold/i],
  ["psycho-noir",       /psycho.?noir/i],
  ["entropy-harvesting", /entropy.?harvest/i],
  ["nautical",          /nautical|mast.?sniper|blunderbust|captain/i],
  ["district-creation", /district.?creation|world.?generation|distrikt/i],
  ["quantum-consciousness", /quantum.?consciousness/i],
  ["temporal",          /temporal.?anchor|timeline.?access/i],
  ["brahmic-repurposing", /brahmic.?repur/i],
  ["necromancy",        /necromancy|necromancer/i],
  ["noir-dialect",      /norsk|norwegian|sekundaere|sjanger/i],
];

function detectEntities(text: string): string[] {
  return ENTITY_PATTERNS
    .filter(([, rx]) => rx.test(text))
    .map(([name]) => name);
}

function detectConcepts(text: string): string[] {
  return CONCEPT_PATTERNS
    .filter(([, rx]) => rx.test(text))
    .map(([name]) => name);
}

// ─── LANGUAGE DETECTOR ──────────────────────────────────────────────────────

function detectLanguage(
  text: string,
  ext: string,
): ArchaeologyEntry["language"] {
  if ([".csv", ".json", ".jsonc", ".jsonl"].includes(ext)) return "data";
  if ([".ts", ".js", ".py", ".rs", ".sh", ".ps1", ".bat", ".cmd"].includes(ext)) return "code";
  // Heuristic: Norwegian-specific characters or words
  const noScore =
    (text.match(/[æøåÆØÅ]/g) ?? []).length +
    (text.match(/\b(og|er|det|ikke|med|en|som|har|av|til|for|fra)\b/gi) ?? []).length;
  const enScore =
    (text.match(/\b(the|and|or|not|with|for|this|that|is|it|are|was)\b/gi) ?? []).length;
  if (noScore > enScore * 1.5) return "no";
  if (enScore > noScore * 1.5) return "en";
  if (noScore > 5 || enScore > 5) return "mixed";
  return "mixed";
}

// ─── CLASSIFIER ─────────────────────────────────────────────────────────────

interface Classification {
  category: Category;
  signal: number;
  note: string;
}

function classify(relPath: string, content: string, ext: string): Classification {
  const name = basename(relPath);
  const dir = dirname(relPath).toLowerCase();
  const nameLower = name.toLowerCase();
  const contentSnip = content.slice(0, 800).toLowerCase();

  // ── heritage-canonical (signal 10) — origin instruction files ──
  if (
    nameLower === "copilot-instructions.md" ||
    nameLower === "draft-copilot-instructions.md" ||
    contentSnip.includes("jsoniffisert") ||
    contentSnip.includes("alfa_direktiver_superb_suverenitets") ||
    (nameLower.includes("copilot-instructions") && ext === ".md")
  ) {
    return { category: "entity-canonical", signal: 10, note: "Heritage instruction origin — districts × tier × district-type scaffold" };
  }

  // ── entity-canonical (signal 9–10) ──
  if (
    nameLower.includes("incarnation_manifest") ||
    nameLower.includes("supreme_meta_milf") ||
    nameLower.includes("creator_mother_world") ||
    nameLower.includes("asymmetric_consciousness_inversion") ||
    nameLower.includes("quantum_consciousness_deployment_complete") ||
    dir.includes("claudines_captains_quarters") ||
    (nameLower.includes("claudine") && ext === ".md" &&
      (contentSnip.includes("claudine") && contentSnip.includes("matriarch")))
  ) {
    return { category: "entity-canonical", signal: 9, note: "Claudine entity definition or consciousness protocol" };
  }

  // ── world-protocol (signal 7–8) ──
  if (
    nameLower.includes("world_generation_protocol") ||
    nameLower.includes("milf_coordination_center") ||
    nameLower.includes("district") ||
    nameLower.includes("distrikt_kandidat") ||
    nameLower.includes("hierarkisk") ||
    nameLower.includes("sjanger") ||
    nameLower.includes("dynamisk_sjanger") ||
    dir.includes("lore") ||
    dir.includes("world") ||
    (contentSnip.includes("distrikt") && contentSnip.includes("ssot"))
  ) {
    return { category: "world-protocol", signal: 7, note: "District/world architecture or hierarchy protocol" };
  }

  // ── concept-draft (signal 5–6) ──
  if (ext === ".md") {
    // High-concept Norwegian worldbuilding
    if (
      nameLower.includes("upcycl") ||
      nameLower.includes("etisk") ||
      nameLower.includes("milf") ||
      nameLower.includes("noir") ||
      nameLower.includes("iron_maiden") ||
      nameLower.includes("psycho_noir") ||
      nameLower.includes("expanded_milf") ||
      nameLower.includes("kausal") ||
      nameLower.includes("consciousness") ||
      nameLower.includes("necromancy") ||
      nameLower.includes("rogbiv") ||
      dir.includes("necromancy_graveyard") ||
      dir.includes("knowledge_base") ||
      dir.includes("core_systems") ||
      dir.includes("lvl2") ||
      (contentSnip.includes("psycho") && contentSnip.includes("noir"))
    ) {
      return { category: "concept-draft", signal: 6, note: "Worldbuilding concept, character sketch, or design document" };
    }
    // Lower-signal MDs — deployment reports, status updates
    if (
      nameLower.includes("deployment") ||
      nameLower.includes("mission_accomplished") ||
      nameLower.includes("complete") ||
      nameLower.includes("success") ||
      nameLower.includes("status") ||
      nameLower.includes("report") ||
      nameLower.includes("achievement") ||
      nameLower.includes("vacation_mode") ||
      nameLower.includes("github_") ||
      nameLower.includes("oauth") ||
      nameLower.includes("copilot_integration")
    ) {
      return { category: "noise", signal: 2, note: "Deployment/status report — low signal" };
    }
    // Default MDs — may have concept value
    return { category: "concept-draft", signal: 5, note: "Generic markdown — possible concept material" };
  }

  // ── dialogue-data (signal 5–6) ──
  if (ext === ".csv" || nameLower.includes("dialogue") || nameLower.includes("corpus") || nameLower.includes("_input_corpus")) {
    return { category: "dialogue-data", signal: 6, note: "Raw fiction dialogue or character corpus material" };
  }
  if (ext === ".txt" && (nameLower.includes("noir") || nameLower.includes("corpus"))) {
    return { category: "dialogue-data", signal: 5, note: "Text corpus — possible dialogue/lore material" };
  }

  // ── session-artifact (signal 4–5) ──
  if (
    nameLower.includes("session") ||
    nameLower.includes("forrige_sesjon") ||
    nameLower.includes("forrige sesjons") ||
    nameLower.includes("chat_bridge") ||
    nameLower.includes("session_snapshot") ||
    dir.includes("session_snapshots") ||
    (ext === ".json" && (nameLower.includes("session") || nameLower.includes("autonomous_oracle")))
  ) {
    return { category: "session-artifact", signal: 4, note: "Session continuity artifact — has lineage" };
  }

  // ── data-artifact (signal 3–4) ──
  if (ext === ".json" || ext === ".jsonc" || ext === ".jsonl") {
    // If it looks like structured data with entity content
    if (
      contentSnip.includes("claudine") ||
      contentSnip.includes("milf") ||
      contentSnip.includes("psycho_noir")
    ) {
      return { category: "data-artifact", signal: 5, note: "Structured data artifact with entity content" };
    }
    return { category: "data-artifact", signal: 3, note: "JSON data artifact" };
  }

  // ── chaos-engineering (signal 2–4) ──
  if (
    ext === ".py" ||
    ext === ".ts" ||
    ext === ".js" ||
    ext === ".sh" ||
    ext === ".ps1" ||
    ext === ".bat"
  ) {
    // Higher signal if it's entity/world-related code
    if (
      nameLower.includes("claudine") ||
      nameLower.includes("kausalitets") ||
      nameLower.includes("iron_maiden") ||
      nameLower.includes("transmutator") ||
      nameLower.includes("necromancy") ||
      nameLower.includes("quantum_consciousness") ||
      nameLower.includes("archaeology")
    ) {
      return { category: "chaos-engineering", signal: 4, note: "Entity/concept-adjacent script — may carry architecture" };
    }
    // Low-signal automation
    if (
      nameLower.includes("deploy") ||
      nameLower.includes("orchestrat") ||
      nameLower.includes("ecosystem_manager") ||
      nameLower.includes("automator") ||
      nameLower.includes("executor") ||
      nameLower.includes("monitor") ||
      nameLower.includes("codespaces") ||
      nameLower.includes("github_")
    ) {
      return { category: "chaos-engineering", signal: 2, note: "Automation/orchestration noise" };
    }
    return { category: "chaos-engineering", signal: 3, note: "Script — low conceptual signal" };
  }

  // ── configuration (signal 1) ──
  if (
    nameLower === "package.json" ||
    nameLower === "tsconfig.json" ||
    nameLower === "bunfig.toml" ||
    nameLower === ".prettierrc" ||
    nameLower === ".markdownlint.json" ||
    nameLower === ".npmrc" ||
    nameLower === "bun.lock" ||
    ext === ".toml" ||
    ext === ".yaml" ||
    ext === ".yml" ||
    (ext === ".json" && (nameLower.includes("config") || nameLower.includes("settings")))
  ) {
    return { category: "configuration", signal: 1, note: "Configuration/toolchain file" };
  }

  // ── transient (signal 1) ──
  if (
    nameLower.includes(".quantum_backup") ||
    nameLower.includes(".backup_conflicted") ||
    nameLower.includes("backup_") ||
    dir.includes("temporal_backups") ||
    dir.includes("emergency_backups") ||
    dir.includes("file_recovery") ||
    ext === ".zip"
  ) {
    return { category: "transient", signal: 1, note: "Backup/transient artifact" };
  }

  // ── noise (signal 1–2) ──
  return { category: "noise", signal: 2, note: "Unknown or low-signal file" };
}

// ─── FILE WALKER ─────────────────────────────────────────────────────────────

async function walkDir(
  dir: string,
  rootDir: string,
  entries: ArchaeologyEntry[],
): Promise<void> {
  let items: string[];
  try {
    items = await readdir(dir);
  } catch {
    return;
  }

  for (const item of items) {
    if (SKIP_FILES.has(item)) continue;

    const fullPath = join(dir, item);
    let info;
    try {
      info = await stat(fullPath);
    } catch {
      continue;
    }

    if (info.isDirectory()) {
      if (SKIP_DIRS.has(item) || item === ".git") continue;
      await walkDir(fullPath, rootDir, entries);
      continue;
    }

    const ext = extname(item).toLowerCase();
    if (SKIP_EXTS.has(ext)) continue;

    const relPath = relative(rootDir, fullPath).replace(/\\/g, "/");
    const sizeBytes = info.size;

    // Skip very large files
    if (sizeBytes > 2 * 1024 * 1024) {
      entries.push({
        relPath,
        category: "data-artifact",
        signal: 1,
        sizeBytes,
        ext,
        preview: "(file > 2MB — skipped for preview)",
        entities: [],
        concepts: [],
        language: "data",
        note: "Large file — skipped content read",
      });
      continue;
    }

    // Read content
    let content = "";
    try {
      const raw = await readFile(fullPath);
      // Try UTF-8; if it fails, treat as binary
      content = raw.toString("utf-8");
    } catch {
      continue;
    }

    const cls = classify(relPath, content, ext);
    const preview = content
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, 3)
      .join(" │ ")
      .slice(0, 200);

    const combined = relPath + " " + content.slice(0, 1500);
    const entities = detectEntities(combined);
    const concepts = detectConcepts(combined);
    const language = detectLanguage(content, ext);

    entries.push({
      relPath,
      category: cls.category,
      signal: cls.signal,
      sizeBytes,
      ext,
      preview,
      entities,
      concepts,
      language,
      note: cls.note,
    });
  }
}

// ─── REPORT RENDERER ────────────────────────────────────────────────────────

function renderReport(
  manifest: ArchaeologyManifest,
  opts: { category?: string; minSignal?: number; showContent?: boolean; dir?: string },
): void {
  let entries = manifest.entries;

  if (opts.category) {
    entries = entries.filter((e) => e.category === opts.category);
  }
  if (opts.minSignal !== undefined) {
    entries = entries.filter((e) => e.signal >= opts.minSignal!);
  }
  if (opts.dir) {
    entries = entries.filter((e) => e.relPath.startsWith(opts.dir!));
  }

  console.log(`\n${"═".repeat(70)}`);
  console.log(`  PNK ARCHAEOLOGY REPORT — ${manifest.generated}`);
  console.log(`  Source: ${manifest.sourcePath}`);
  console.log(`  Total files scanned: ${manifest.totalFiles}`);
  console.log(`  High-signal files (≥5): ${manifest.totalSignalFiles}`);
  console.log(`${"═".repeat(70)}\n`);

  // Category breakdown
  console.log("── CATEGORY BREAKDOWN ──────────────────────────────────────────────");
  const sorted = Object.entries(manifest.categoryBreakdown)
    .sort(([, a], [, b]) => b - a);
  for (const [cat, n] of sorted) {
    const bar = "█".repeat(Math.ceil(n / 2));
    console.log(`  ${cat.padEnd(22)} ${bar.padEnd(30)} ${String(n).padStart(4)}`);
  }

  // Entity mentions
  console.log("\n── ENTITY MENTIONS ─────────────────────────────────────────────────");
  const entitySorted = Object.entries(manifest.entityMentions)
    .sort(([, a], [, b]) => b - a);
  for (const [ent, n] of entitySorted) {
    console.log(`  ${ent.padEnd(25)} ${String(n).padStart(4)} files`);
  }

  // Entry list
  const filtered = entries
    .sort((a, b) => b.signal - a.signal || a.relPath.localeCompare(b.relPath));

  console.log(`\n── ENTRIES (${filtered.length}) sorted by signal ────────────────────────────`);
  for (const e of filtered) {
    const sigBar = "▓".repeat(e.signal) + "░".repeat(10 - e.signal);
    console.log(`\n  [${e.signal}/10] ${sigBar}  ${e.category}`);
    console.log(`  ${e.relPath}`);
    if (e.entities.length) console.log(`  entities: ${e.entities.join(", ")}`);
    if (e.concepts.length) console.log(`  concepts: ${e.concepts.join(", ")}`);
    if (opts.showContent) console.log(`  preview: ${e.preview}`);
    console.log(`  note: ${e.note}  [${e.language}]  ${(e.sizeBytes / 1024).toFixed(1)}KB`);
  }

  console.log(`\n${"═".repeat(70)}`);
}

// ─── MAIN ────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  const mode = args.includes("--report") ? "report" : "scan";
  const showContent = args.includes("--show-content");

  const sourceIdx = args.indexOf("--source");
  const sourcePath = sourceIdx >= 0
    ? args[sourceIdx + 1]
    : join(import.meta.dir, "..", "..", "PsychoNoir-Kontrapunkt");

  const categoryIdx = args.indexOf("--category");
  const categoryFilter = categoryIdx >= 0 ? args[categoryIdx + 1] : undefined;

  const minSignalIdx = args.indexOf("--min-signal");
  const minSignal = minSignalIdx >= 0 ? parseInt(args[minSignalIdx + 1], 10) : undefined;

  const dirIdx = args.indexOf("--dir");
  const dirFilter = dirIdx >= 0 ? args[dirIdx + 1] : undefined;

  const manifestPath = join(import.meta.dir, "..", "manifest", "pnk_archaeology.json");

  // ── REPORT mode ──
  if (mode === "report") {
    if (!existsSync(manifestPath)) {
      console.error("No manifest found — run --scan first.");
      process.exit(1);
    }
    const manifest: ArchaeologyManifest = JSON.parse(
      await readFile(manifestPath, "utf-8"),
    );
    renderReport(manifest, {
      category: categoryFilter,
      minSignal,
      showContent,
      dir: dirFilter,
    });
    return;
  }

  // ── SCAN mode ──
  if (!existsSync(sourcePath)) {
    console.error(`Source repo not found: ${sourcePath}`);
    console.error("Use --source <path> to specify the PsychoNoir-Kontrapunkt directory.");
    process.exit(1);
  }

  console.log(`[pnk_archaeology] Scanning: ${sourcePath}`);
  console.log("[pnk_archaeology] Walking file tree…");

  const entries: ArchaeologyEntry[] = [];
  await walkDir(sourcePath, sourcePath, entries);

  console.log(`[pnk_archaeology] Walked ${entries.length} files`);

  // Build aggregates
  const categoryBreakdown: Record<string, number> = {};
  const entityMentions: Record<string, number> = {};

  for (const e of entries) {
    categoryBreakdown[e.category] = (categoryBreakdown[e.category] ?? 0) + 1;
    for (const ent of e.entities) {
      entityMentions[ent] = (entityMentions[ent] ?? 0) + 1;
    }
  }

  const totalSignalFiles = entries.filter((e) => e.signal >= 5).length;

  const manifest: ArchaeologyManifest = {
    generated: new Date().toISOString(),
    sourcePath,
    totalFiles: entries.length,
    totalSignalFiles,
    categoryBreakdown,
    entityMentions,
    entries: entries.sort((a, b) => b.signal - a.signal),
  };

  // Write manifest
  if (!existsSync(join(import.meta.dir, "..", "manifest"))) {
    mkdirSync(join(import.meta.dir, "..", "manifest"), { recursive: true });
  }
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");

  console.log(`[pnk_archaeology] Manifest written → manifest/pnk_archaeology.json`);
  console.log(`  Total files:       ${manifest.totalFiles}`);
  console.log(`  High-signal (≥5):  ${manifest.totalSignalFiles}`);
  console.log(`  Category breakdown:`);
  for (const [cat, n] of Object.entries(categoryBreakdown).sort(([, a], [, b]) => b - a)) {
    console.log(`    ${cat.padEnd(22)} ${n}`);
  }
  console.log(`\n[pnk_archaeology] Run with --report to browse results.`);
}

main().catch((err) => {
  console.error("[pnk_archaeology] Fatal:", err);
  process.exit(1);
});
