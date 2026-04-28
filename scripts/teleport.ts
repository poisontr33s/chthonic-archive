#!/usr/bin/env bun
// @SID: teleport — cross-repo agent/instruction briefcase tool
// @VERSION: 2.1.0
// @AUTHOR: chthonic-archive
//
// TELEPORT FUNCTION — packs and migrates agent/instruction DNA
// from a source repo (X) into a target repo (Y).
// Supports both local filesystem repos and GitHub remote repos.
//
// Usage:
//   bun run scripts/teleport.ts --from <source-repo-path> [options]
//   bun run scripts/teleport.ts --from-github <owner/repo> [options]
//   bun run scripts/teleport.ts --from <path> --dry-run
//   bun run scripts/teleport.ts --from-github <owner/repo> --apply
//
// Flags:
//   --from <path>              Source repo root on disk (X)
//   --from-github <owner/repo> Fetch from GitHub API instead of local disk
//   --github-token <token>     GitHub token (or set GITHUB_TOKEN env var)
//   --to <path>                Target repo root (Y) — defaults to CWD
//   --out <path>               Briefcase output directory — defaults to claude/mailbox/briefcase/
//   --dry-run                  Scan and report only; write nothing
//   --apply                    Write briefcase to --out directory
//   --json                     Emit JSON summary to stdout (CI-compatible)
//   --help                     Show this help

import { readdir, readFile, stat, mkdir, writeFile } from "fs/promises";
import { join, relative, extname, basename, dirname } from "path";
import { existsSync } from "fs";

// ─── GITHUB API TYPES ───────────────────────────────────────────────────────

interface GHTreeItem {
  path: string;
  type: "blob" | "tree";
  sha: string;
  size?: number;
  url: string;
}

interface GHTree {
  sha: string;
  url: string;
  tree: GHTreeItem[];
  truncated: boolean;
}

async function ghFetch(url: string, token?: string): Promise<unknown> {
  const headers: Record<string, string> = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "chthonic-teleport/2.0.0",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(url, { headers });
  if (!resp.ok) throw new Error(`GitHub API ${resp.status}: ${url}`);
  return resp.json();
}

async function ghFetchContent(url: string, token?: string): Promise<string> {
  const headers: Record<string, string> = {
    "Accept": "application/vnd.github.raw+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "chthonic-teleport/2.0.0",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(url, { headers });
  if (!resp.ok) return "";
  return resp.text();
}

// ─── GITHUB SCANNER ─────────────────────────────────────────────────────────

async function scanGitHub(
  ownerRepo: string,
  token?: string,
  entityMode = false,
): Promise<ExtractedFile[]> {
  const [owner, repo] = ownerRepo.split("/");
  if (!owner || !repo) throw new Error(`Invalid owner/repo: ${ownerRepo}`);

  console.log(`[teleport] Fetching GitHub tree: ${ownerRepo}`);

  // Get default branch
  const repoMeta = (await ghFetch(
    `https://api.github.com/repos/${owner}/${repo}`,
    token,
  )) as { default_branch: string };
  const branch = repoMeta.default_branch ?? "main";

  // Get full tree (recursive)
  const tree = (await ghFetch(
    `https://api.github.com/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`,
    token,
  )) as GHTree;

  if (tree.truncated) {
    console.warn(`[teleport] WARNING: GitHub tree truncated for ${ownerRepo} — large repos may be incomplete`);
  }

  const found: ExtractedFile[] = [];

  // Filter to agent-relevant paths only
  const relevant = tree.tree.filter((item) => {
    if (item.type !== "blob") return false;
    const parts = item.path.split("/");
    const fileName = parts[parts.length - 1];

    // Skip heavy dirs
    const skipDirs = ["node_modules", ".git", "target", "dist", ".venv", "__pycache__", "backups", "backup_"];
    if (parts.some((p) => skipDirs.some((s) => p.startsWith(s)))) return false;

    // Skip macOS resource fork artifacts (._filename)
    if (fileName.startsWith("._")) return false;

    return categoryFromPath(item.path, fileName, entityMode) !== null;
  });

  console.log(`[teleport] Found ${relevant.length} candidate files on GitHub (from ${tree.tree.length} total)`);

  // Fetch content for each relevant file
  for (const item of relevant) {
    const parts = item.path.split("/");
    const fileName = parts[parts.length - 1];
    const category = categoryFromPath(item.path, fileName, entityMode)!;

    const rawUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${item.path}`;
    let firstLine = "";
    let content = "";
    try {
      content = await ghFetchContent(rawUrl, token);
      firstLine = content.split("\n")[0].trim().slice(0, 120);
    } catch {
      firstLine = "(fetch failed)";
    }

    found.push({
      relPath: item.path,
      absPath: rawUrl,
      category,
      sizeBytes: item.size ?? content.length,
      firstLine,
      entity: extractEntityName(item.path, fileName),
      _ghContent: content,
    });
  }

  return found;
}

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

// Entity-mode selectors — activated by --entity-mode flag.
// Captures incarnation manifests, entity protocols, revelation docs
// common in world-building / character SSOT repos (e.g. PsychoNoir-Kontrapunkt).
const ENTITY_NAMED_FILES: Record<string, string> = {
  "claudine_sinclair_incarnation_manifest.md": "entity-manifest",
  "SUPREME_META_MILF_MATRIARCH_REVELATION.md": "entity-revelation",
  "CREATOR_MOTHER_WORLD_GENERATION_PROTOCOL.md": "world-protocol",
  "ASYMMETRIC_CONSCIOUSNESS_INVERSION_PROTOCOL.md": "consciousness-protocol",
  "QUANTUM_CONSCIOUSNESS_DEPLOYMENT_COMPLETE.md":   "consciousness-protocol",
  "CAPTAIN_QUARTERS_WORKMAP.md":                    "entity-manifest",
  "milf_coordination_center.md":                    "entity-manifest",
};

// Suffix patterns for --entity-mode (applied when no exact named-file match)
const ENTITY_SUFFIXES: Array<[string, string]> = [
  ["_incarnation_manifest.md",  "entity-manifest"],
  ["_incarnation_manifest_md",  "entity-manifest"],   // necromancy_graveyard preserved
  ["_revelation.md",            "entity-revelation"],
  ["_protocol.md",              "world-protocol"],
  ["_workmap.md",               "entity-manifest"],
  ["_coordination_center.md",   "entity-manifest"],
];

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
  _ghContent?: string; // populated in GitHub mode; stripped from JSON output
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

function categoryFromPath(absPath: string, fileName: string, entityMode = false): string | null {
  // Check named files first
  for (const [name, cat] of Object.entries(NAMED_FILES)) {
    if (fileName === name) return cat;
  }
  // Check extension-based patterns
  for (const [ext, cat] of Object.entries(AGENT_FILETYPES)) {
    if (fileName.endsWith(ext)) return cat;
  }
  // Entity-mode: check entity named files + suffix patterns
  if (entityMode) {
    for (const [name, cat] of Object.entries(ENTITY_NAMED_FILES)) {
      if (fileName === name) return cat;
    }
    for (const [suffix, cat] of ENTITY_SUFFIXES) {
      if (fileName.endsWith(suffix) || absPath.includes(suffix)) return cat;
    }
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

async function scanRepo(repoRoot: string, entityMode = false): Promise<ExtractedFile[]> {
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

      // Skip macOS resource fork artifacts (._filename)
      if (entry.startsWith("._")) continue;

      const category = categoryFromPath(full, entry, entityMode);
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

  // Strip internal _ghContent from JSON output
  const cleanBc = {
    ...bc,
    inventory: bc.inventory.map(({ _ghContent, ...rest }) => rest),
  };

  await writeFile(jsonPath, JSON.stringify(cleanBc, null, 2), "utf8");
  await writeFile(mdPath, renderMarkdown(bc), "utf8");

  // Copy extracted files into briefcase/extracted/<relPath>
  const extractedRoot = join(outDir, "extracted");
  for (const f of bc.inventory) {
    const dest = join(extractedRoot, f.relPath);
    await mkdir(dirname(dest), { recursive: true });
    try {
      // GitHub mode: content already fetched
      if (f._ghContent !== undefined) {
        await writeFile(dest, f._ghContent, "utf8");
      } else {
        const content = await readFile(f.absPath, "utf8");
        await writeFile(dest, content, "utf8");
      }
    } catch {
      // skip unreadable files
    }
  }

  console.log(`✓ Briefcase written to: ${outDir}`);
  console.log(`  → ${jsonPath}`);
  console.log(`  → ${mdPath}`);
  console.log(`  → ${extractedRoot}/`);
}

// ─── SATELLITE REGISTRY LOADER ─────────────────────────────────────────────

interface SatelliteEntry {
  alias: string;
  name: string;
  github?: string;
  local_path: string;
  junction?: string;
  teleport_flags?: string[];
  domain?: string;
  governance_class?: string;
}

interface SatelliteRegistry {
  satellites: SatelliteEntry[];
}

async function loadSatelliteRegistry(targetRepo: string): Promise<SatelliteRegistry> {
  const registryPath = join(targetRepo, "SATELLITE_REGISTRY.json");
  if (!existsSync(registryPath)) {
    console.error(`ERROR: SATELLITE_REGISTRY.json not found at ${registryPath}`);
    console.error(`       Create it to register sibling repos, or use --from <path> directly.`);
    process.exit(1);
  }
  try {
    const raw = await readFile(registryPath, "utf8");
    return JSON.parse(raw) as SatelliteRegistry;
  } catch (e) {
    console.error(`ERROR: Failed to parse SATELLITE_REGISTRY.json: ${e}`);
    process.exit(1);
  }
}

// ─── CLI ENTRYPOINT ─────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.length === 0) {
    console.log(`
Teleport v2.0.0 — cross-repo agent/instruction briefcase tool

Usage:
  bun run scripts/teleport.ts --from <source-repo-path> [options]
  bun run scripts/teleport.ts --from-github <owner/repo> [options]

Options:
  --from <path>               Source repo root on disk (required unless --from-github/--from-sibling)
  --from-github <owner/repo>  Scan a GitHub repo via API (e.g. poisontr33s/PsychoNoir-Kontrapunkt)
  --from-sibling <alias>      Resolve a registered sibling from SATELLITE_REGISTRY.json
                              (e.g. --from-sibling pnk). teleport_flags from registry auto-applied.
  --github-token <token>      GitHub token (or GITHUB_TOKEN env var)
  --entity-mode               Enable entity/world-building file selectors (incarnation manifests,
                              protocols, revelations) — for repos like PsychoNoir-Kontrapunkt
  --to <path>                 Target repo root (defaults to CWD)
  --out <path>                Briefcase output dir (defaults to claude/mailbox/briefcase/)
  --dry-run                   Scan only; print inventory; write nothing
  --apply                     Write briefcase to --out directory
  --json                      Print JSON summary to stdout
  --help                      Show this help
`);
    process.exit(0);
  }

  const fromIdx = args.indexOf("--from");
  const fromGhIdx = args.indexOf("--from-github");
  const fromSiblingIdx = args.indexOf("--from-sibling");
  const toIdx = args.indexOf("--to");
  const outIdx = args.indexOf("--out");
  const tokenIdx = args.indexOf("--github-token");

  const isGitHubMode = fromGhIdx !== -1 && !!args[fromGhIdx + 1];
  const isLocalMode = fromIdx !== -1 && !!args[fromIdx + 1];
  const isSiblingMode = fromSiblingIdx !== -1 && !!args[fromSiblingIdx + 1];

  if (!isGitHubMode && !isLocalMode && !isSiblingMode) {
    console.error("ERROR: one of --from <path>, --from-github <owner/repo>, or --from-sibling <alias> is required");
    process.exit(1);
  }

  const targetRepo = toIdx !== -1 && args[toIdx + 1] ? args[toIdx + 1] : process.cwd();
  const outDir = outIdx !== -1 && args[outIdx + 1]
    ? args[outIdx + 1]
    : join(targetRepo, "claude", "mailbox", "briefcase");

  const isDryRun = args.includes("--dry-run");
  const doApply = args.includes("--apply");
  const emitJson = args.includes("--json");
  let entityMode = args.includes("--entity-mode");

  const ghToken = tokenIdx !== -1 && args[tokenIdx + 1]
    ? args[tokenIdx + 1]
    : process.env.GITHUB_TOKEN;

  let inventory: ExtractedFile[];
  let sourceLabel: string;

  if (isSiblingMode) {
    const aliasArg = args[fromSiblingIdx + 1].toLowerCase();
    const registry = await loadSatelliteRegistry(targetRepo);
    const entry = registry.satellites.find(
      (s) => s.alias.toLowerCase() === aliasArg || s.name.toLowerCase() === aliasArg,
    );
    if (!entry) {
      const known = registry.satellites.map((s) => `${s.alias} (${s.name})`).join(", ");
      console.error(`ERROR: satellite alias "${aliasArg}" not found in SATELLITE_REGISTRY.json`);
      console.error(`       Known satellites: ${known}`);
      process.exit(1);
    }
    // Apply registry teleport_flags automatically (e.g. --entity-mode)
    if (entry.teleport_flags?.includes("--entity-mode")) entityMode = true;
    sourceLabel = `satellite:${entry.name} (${entry.local_path})`;
    if (!existsSync(entry.local_path)) {
      console.error(`ERROR: satellite local_path not found: ${entry.local_path}`);
      console.error(`       Run: git clone --depth 1 ${entry.github ?? entry.name} "${entry.local_path}"`);
      process.exit(1);
    }
    console.log(`[teleport] Mode: Sibling — ${entry.name} @ ${entry.local_path}${entityMode ? " (+entity-mode)" : ""}`);
    if (entry.domain) console.log(`[teleport] Domain: ${entry.domain}`);
    inventory = await scanRepo(entry.local_path, entityMode);
  } else if (isGitHubMode) {
    const ownerRepo = args[fromGhIdx + 1];
    sourceLabel = `github:${ownerRepo}`;
    console.log(`[teleport] Mode: GitHub — ${ownerRepo}${entityMode ? " (+entity-mode)" : ""}`);
    inventory = await scanGitHub(ownerRepo, ghToken, entityMode);
  } else {
    const sourceRepo = args[fromIdx + 1];
    sourceLabel = sourceRepo;
    if (!existsSync(sourceRepo)) {
      console.error(`ERROR: source repo not found: ${sourceRepo}`);
      process.exit(1);
    }
    console.log(`[teleport] Mode: Local — ${sourceRepo}${entityMode ? " (+entity-mode)" : ""}`);
    inventory = await scanRepo(sourceRepo, entityMode);
  }

  const bc = buildBriefcase(inventory, sourceLabel, targetRepo);

  if (emitJson) {
    // Strip _ghContent from JSON output
    const cleanBc = { ...bc, inventory: bc.inventory.map(({ _ghContent, ...rest }) => rest) };
    console.log(JSON.stringify(cleanBc, null, 2));
    return;
  }

  // Print summary
  console.log(`\n[teleport] Scan complete`);
  console.log(`  Source:  ${sourceLabel}`);
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

main().catch((e) => { console.error(e); process.exit(1); });
