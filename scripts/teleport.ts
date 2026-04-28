#!/usr/bin/env bun
// @SID: teleport — cross-repo agent/instruction briefcase tool
// @VERSION: 1.0.0
// @AUTHOR: chthonic-archive
//
// TELEPORT FUNCTION — packs and migrates agent/instruction DNA
// from a source repo (X) into a target repo (Y).
//
// Usage:
//   bun run scripts/teleport.ts --from <source-repo-path> [--to <target-repo-path>]
//   bun run scripts/teleport.ts --from <source-repo-path> --dry-run
//   bun run scripts/teleport.ts --from <source-repo-path> --apply [--out <briefcase-dir>]
//
// Flags:
//   --from <path>     Source repo root (X)
//   --to <path>       Target repo root (Y) — defaults to CWD
//   --out <path>      Briefcase output directory — defaults to claude/mailbox/briefcase/
//   --dry-run         Scan and report only; write nothing
//   --apply           Write briefcase to --out directory
//   --json            Emit JSON summary to stdout (CI-compatible)
//   --help            Show this help

import { readdir, readFile, stat, mkdir, writeFile } from "fs/promises";
import { join, relative, extname, basename, dirname } from "path";
import { existsSync } from "fs";

// ─── AGENT-RELEVANT FILE SELECTORS ──────────────────────────────────────────

const AGENT_FILETYPES: Record<string, string> = {
  ".agent.md":         "agent-deployment-adapter",
  ".instructions.md":  "instruction-branch",
  ".prompt.md":        "prompt-template",
};

const NAMED_FILES: Record<string, string> = {
  "copilot-instructions.md": "copilot-instructions",
  "AGENTS.md":               "agents-guidance",
  "CLAUDE.md":               "claude-guidance",
  "GEMINI.md":               "gemini-guidance",
  "AGENT_COMMON.md":         "shared-invariants",
  "SKILL.md":                "skill-definition",
};

const SCAN_DIRS: string[] = [
  ".github/agents",
  ".github/instructions",
  ".github/prompts",
  ".github",
  ".claude/skills",
  ".codex/skills",
  ".",
];

// ─── TYPES ──────────────────────────────────────────────────────────────────

interface ExtractedFile {
  relPath: string;
  absPath: string;
  category: string;
  sizeBytes: number;
  firstLine: string;
  entity?: string;
}

interface BriefcaseMeta {
  teleport_version: "1.0.0";
  timestamp: string;
  source_repo: string;
  target_repo: string;
  invoked_by: string;
}

interface Briefcase {
  meta: BriefcaseMeta;
  inventory: ExtractedFile[];
  summary: {
    total_files: number;
    by_category: Record<string, number>;
    agent_names: string[];
    skill_names: string[];
  };
}

// ─── HELPERS ────────────────────────────────────────────────────────────────

async function isDir(p: string): Promise<boolean> {
  try {
    return (await stat(p)).isDirectory();
  } catch {
    return false;
  }
}

async function isFile(p: string): Promise<boolean> {
  try {
    return (await stat(p)).isFile();
  } catch {
    return false;
  }
}

async function readFirstLine(p: string): Promise<string> {
  try {
    const content = await readFile(p, "utf8");
    return content.split("\n")[0].trim().slice(0, 120);
  } catch {
    return "";
  }
}

function categoryFromPath(absPath: string, fileName: string): string | null {
  // Check named files first
  for (const [name, cat] of Object.entries(NAMED_FILES)) {
    if (fileName === name) return cat;
  }
  // Check extension-based patterns
  for (const [ext, cat] of Object.entries(AGENT_FILETYPES)) {
    if (fileName.endsWith(ext)) return cat;
  }
  return null;
}

function extractEntityName(relPath: string, fileName: string): string | undefined {
  // .agent.md: entity is the stem before .agent.md
  if (fileName.endsWith(".agent.md")) {
    return fileName.replace(/\.agent\.md$/, "");
  }
  // SKILL.md: entity is parent directory name
  if (fileName === "SKILL.md") {
    const parts = relPath.split("/");
    return parts[parts.length - 2] ?? undefined;
  }
  return undefined;
}

// ─── SCANNER ────────────────────────────────────────────────────────────────

async function scanRepo(repoRoot: string): Promise<ExtractedFile[]> {
  const found: ExtractedFile[] = [];
  const seen = new Set<string>();

  async function walkDir(dir: string, maxDepth: number) {
    if (maxDepth < 0) return;
    let entries: string[];
    try {
      entries = await readdir(dir);
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = join(dir, entry);
      if (seen.has(full)) continue;

      const category = categoryFromPath(full, entry);
      if (category) {
        if (await isFile(full)) {
          seen.add(full);
          const s = await stat(full);
          const firstLine = await readFirstLine(full);
          const rel = relative(repoRoot, full).replace(/\\/g, "/");
          found.push({
            relPath: rel,
            absPath: full,
            category,
            sizeBytes: s.size,
            firstLine,
            entity: extractEntityName(rel, entry),
          });
        }
      } else if (await isDir(full)) {
        // Skip heavy dirs
        if (["node_modules", ".git", "target", "dist", ".venv", "__pycache__"].includes(entry)) continue;
        await walkDir(full, maxDepth - 1);
      }
    }
  }

  for (const scanDir of SCAN_DIRS) {
    const target = join(repoRoot, scanDir);
    if (await isDir(target)) {
      await walkDir(target, scanDir === "." ? 2 : 4);
    }
  }

  return found;
}

// ─── BRIEFCASE BUILDER ──────────────────────────────────────────────────────

function buildBriefcase(
  inventory: ExtractedFile[],
  sourceRepo: string,
  targetRepo: string,
): Briefcase {
  const byCat: Record<string, number> = {};
  const agentNames: string[] = [];
  const skillNames: string[] = [];

  for (const f of inventory) {
    byCat[f.category] = (byCat[f.category] ?? 0) + 1;
    if (f.category === "agent-deployment-adapter" && f.entity) agentNames.push(f.entity);
    if (f.category === "skill-definition" && f.entity) skillNames.push(f.entity);
  }

  return {
    meta: {
      teleport_version: "1.0.0",
      timestamp: new Date().toISOString(),
      source_repo: sourceRepo,
      target_repo: targetRepo,
      invoked_by: process.env.USERNAME ?? process.env.USER ?? "unknown",
    },
    inventory,
    summary: {
      total_files: inventory.length,
      by_category: byCat,
      agent_names: agentNames,
      skill_names: skillNames,
    },
  };
}

// ─── MARKDOWN MANIFEST ──────────────────────────────────────────────────────

function renderMarkdown(bc: Briefcase): string {
  const ts = bc.meta.timestamp;
  const lines: string[] = [
    `# Teleport Briefcase — ${new Date(ts).toLocaleDateString("en-GB")}`,
    ``,
    `**Source:** \`${bc.meta.source_repo}\`  `,
    `**Target:** \`${bc.meta.target_repo}\`  `,
    `**Timestamp:** ${ts}  `,
    `**Invoked by:** ${bc.meta.invoked_by}  `,
    ``,
    `---`,
    ``,
    `## Summary`,
    ``,
    `| Category | Count |`,
    `|----------|-------|`,
  ];

  for (const [cat, count] of Object.entries(bc.summary.by_category)) {
    lines.push(`| \`${cat}\` | ${count} |`);
  }

  lines.push(``, `**Total files extracted:** ${bc.summary.total_files}`);

  if (bc.summary.agent_names.length > 0) {
    lines.push(``, `### Agents Found`);
    for (const a of bc.summary.agent_names) lines.push(`- \`${a}\``);
  }

  if (bc.summary.skill_names.length > 0) {
    lines.push(``, `### Skills Found`);
    for (const s of bc.summary.skill_names) lines.push(`- \`${s}\``);
  }

  lines.push(``, `---`, ``, `## Inventory`);
  lines.push(``, `| File | Category | Size | First Line |`);
  lines.push(`|------|----------|------|------------|`);

  for (const f of bc.inventory) {
    const first = f.firstLine.replace(/\|/g, "\\|").slice(0, 60);
    lines.push(`| \`${f.relPath}\` | \`${f.category}\` | ${f.sizeBytes}B | ${first} |`);
  }

  lines.push(``, `---`, ``, `*Generated by \`scripts/teleport.ts\` — chthonic-archive*`);
  return lines.join("\n");
}

// ─── WRITE BRIEFCASE ────────────────────────────────────────────────────────

async function writeBriefcase(bc: Briefcase, outDir: string): Promise<void> {
  await mkdir(outDir, { recursive: true });

  const jsonPath = join(outDir, "briefcase.json");
  const mdPath = join(outDir, "BRIEFCASE.md");

  await writeFile(jsonPath, JSON.stringify(bc, null, 2), "utf8");
  await writeFile(mdPath, renderMarkdown(bc), "utf8");

  // Copy extracted files into briefcase/extracted/<relPath>
  const extractedRoot = join(outDir, "extracted");
  for (const f of bc.inventory) {
    const dest = join(extractedRoot, f.relPath);
    await mkdir(dirname(dest), { recursive: true });
    try {
      const content = await readFile(f.absPath, "utf8");
      await writeFile(dest, content, "utf8");
    } catch {
      // skip unreadable files
    }
  }

  console.log(`✓ Briefcase written to: ${outDir}`);
  console.log(`  → ${jsonPath}`);
  console.log(`  → ${mdPath}`);
  console.log(`  → ${extractedRoot}/`);
}

// ─── CLI ENTRYPOINT ─────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.length === 0) {
    console.log(`
Teleport — cross-repo agent/instruction briefcase tool

Usage:
  bun run scripts/teleport.ts --from <source-repo-path> [options]

Options:
  --from <path>   Source repo root to scan (required)
  --to <path>     Target repo root (defaults to CWD)
  --out <path>    Briefcase output dir (defaults to claude/mailbox/briefcase/)
  --dry-run       Scan only; print inventory; write nothing
  --apply         Write briefcase to --out directory
  --json          Print JSON summary to stdout
  --help          Show this help
`);
    process.exit(0);
  }

  const fromIdx = args.indexOf("--from");
  const toIdx = args.indexOf("--to");
  const outIdx = args.indexOf("--out");

  if (fromIdx === -1 || !args[fromIdx + 1]) {
    console.error("ERROR: --from <source-repo-path> is required");
    process.exit(1);
  }

  const sourceRepo = args[fromIdx + 1];
  const targetRepo = toIdx !== -1 && args[toIdx + 1] ? args[toIdx + 1] : process.cwd();
  const outDir = outIdx !== -1 && args[outIdx + 1]
    ? args[outIdx + 1]
    : join(targetRepo, "claude", "mailbox", "briefcase");

  const isDryRun = args.includes("--dry-run");
  const doApply = args.includes("--apply");
  const emitJson = args.includes("--json");

  if (!existsSync(sourceRepo)) {
    console.error(`ERROR: source repo not found: ${sourceRepo}`);
    process.exit(1);
  }

  console.log(`[teleport] Scanning source: ${sourceRepo}`);
  const inventory = await scanRepo(sourceRepo);
  const bc = buildBriefcase(inventory, sourceRepo, targetRepo);

  if (emitJson) {
    console.log(JSON.stringify(bc, null, 2));
    return;
  }

  // Print summary
  console.log(`\n[teleport] Scan complete`);
  console.log(`  Source:  ${sourceRepo}`);
  console.log(`  Target:  ${targetRepo}`);
  console.log(`  Files:   ${bc.summary.total_files}`);
  for (const [cat, count] of Object.entries(bc.summary.by_category)) {
    console.log(`    ${cat.padEnd(36)} ${count}`);
  }
  if (bc.summary.agent_names.length > 0) {
    console.log(`  Agents:  ${bc.summary.agent_names.join(", ")}`);
  }
  if (bc.summary.skill_names.length > 0) {
    console.log(`  Skills:  ${bc.summary.skill_names.join(", ")}`);
  }

  if (isDryRun) {
    console.log(`\n[teleport] DRY RUN — no files written`);
    console.log(`  Would write briefcase to: ${outDir}`);
    console.log(`\nInventory:`);
    for (const f of bc.inventory) {
      console.log(`  [${f.category}] ${f.relPath} (${f.sizeBytes}B)`);
    }
    return;
  }

  if (doApply) {
    await writeBriefcase(bc, outDir);
  } else {
    console.log(`\n[teleport] Run with --apply to write briefcase, or --dry-run to inspect`);
  }
}

main().catch((err) => {
  console.error("[teleport] FATAL:", err);
  process.exit(1);
});
