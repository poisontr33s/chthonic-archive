#!/usr/bin/env bun
// @SID: SCRIPT_CLAUDE_DESIGN_INTAKE_V1

/**
 * claude-design-intake.ts
 *
 * Local FAF intake for Claude Design exports. This script performs no model or
 * API calls. It classifies a local export folder and emits compact frame
 * artifacts for frontend preview and token-bound implementation handoff.
 *
 * Usage:
 *   bun run scripts/claude-design-intake.ts artifacts/claude-design/demo/2026-05-07T000000Z
 *   bun run scripts/claude-design-intake.ts <export-root> --target apps/chthonic-next/app/page.tsx
 */

import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";

type GateStatus = "admitted" | "open" | "blocked_not_closed" | "degraded";

type FileRecord = {
  path: string;
  bytes: number;
  sha256: string;
  kind: FileKind;
};

type FileKind =
  | "html"
  | "css"
  | "javascript"
  | "image"
  | "font"
  | "pdf"
  | "pptx"
  | "handoff"
  | "asset"
  | "unknown";

type Manifest = {
  artifact_type: "claude_design_frame_manifest";
  schema_version: 1;
  created_at_utc: string;
  export_id: string;
  source_root: string;
  frame_root: string;
  detected: {
    html: boolean;
    css: boolean;
    javascript: boolean;
    assets: boolean;
    images: boolean;
    pdf: boolean;
    pptx: boolean;
    handoff: boolean;
  };
  levels: Record<"L0" | "L1" | "L2" | "L3" | "L4" | "L5", GateStatus>;
  files: FileRecord[];
  primary_files: {
    html: string[];
    css: string[];
    handoff: string[];
    screenshots: string[];
  };
  blocked_boundaries: BoundaryRecord[];
  notes: string[];
};

type BoundaryRecord = {
  artifact_type: "impossible_currently_boundary";
  gate: string;
  claim: string;
  observed_failure: string;
  proof: string;
  minimum_condition_to_reopen: string;
  upstream_dependency: string;
  next_probe: string;
  status: "blocked_not_closed";
};

type TokenSet = {
  artifact_type: "claude_design_tokens";
  schema_version: 1;
  created_at_utc: string;
  colors: Array<{ name: string; value: string; source: string }>;
  typography: Array<{ role: string; value: string; source: string }>;
  spacing: Array<{ name: string; value: string; source: string }>;
  radii: Array<{ name: string; value: string; source: string }>;
  shadows: Array<{ name: string; value: string; source: string }>;
  assets: Array<{ path: string; role: string }>;
  unknowns: string[];
};

type Options = {
  inputRoot: string;
  targetFiles: string[];
};

const REPO_ROOT = path.resolve(import.meta.dir, "..");
const MAX_TEXT_FILE_BYTES = 2_000_000;

function usage(exitCode = 0): never {
  const text = `
Usage:
  bun run scripts/claude-design-intake.ts <export-root> [--target <repo-path>]...

Notes:
  - No Claude API, Agent SDK, or Claude Code calls are made.
  - If <export-root>/source exists, source/ is treated as the raw export.
  - Otherwise <export-root> itself is treated as the raw export and frame/ is ignored.
  - Contract extraction is integrated into this intake script for the first slice.
`;
  console.log(text.trim());
  process.exit(exitCode);
}

function parseArgs(argv: string[]): Options {
  const args = [...argv];
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    usage(0);
  }

  const inputRoot = args.shift();
  if (!inputRoot) {
    usage(1);
  }

  const targetFiles: string[] = [];
  while (args.length > 0) {
    const arg = args.shift();
    if (arg === "--target") {
      const value = args.shift();
      if (!value) {
        throw new Error("--target requires a path value");
      }
      targetFiles.push(value);
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  return {
    inputRoot: path.resolve(REPO_ROOT, inputRoot),
    targetFiles,
  };
}

function toRepoPath(absPath: string): string {
  return path.relative(REPO_ROOT, absPath).replaceAll(path.sep, "/");
}

function normalizeRel(relPath: string): string {
  return relPath.replaceAll(path.sep, "/");
}

async function ensureDirectory(absPath: string): Promise<void> {
  const info = await stat(absPath).catch(() => null);
  if (!info || !info.isDirectory()) {
    throw new Error(`Directory not found: ${absPath}`);
  }
}

function inferRoots(inputRoot: string): { sourceRoot: string; frameRoot: string; exportRoot: string } {
  const sourceCandidate = path.join(inputRoot, "source");
  if (existsSync(sourceCandidate)) {
    return {
      exportRoot: inputRoot,
      sourceRoot: sourceCandidate,
      frameRoot: path.join(inputRoot, "frame"),
    };
  }

  return {
    exportRoot: inputRoot,
    sourceRoot: inputRoot,
    frameRoot: path.join(inputRoot, "frame"),
  };
}

async function walkFiles(root: string, exclude: Set<string>): Promise<string[]> {
  const out: string[] = [];

  async function visit(current: string): Promise<void> {
    const entries = await readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const absPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (exclude.has(path.resolve(absPath))) {
          continue;
        }
        await visit(absPath);
        continue;
      }
      if (entry.isFile()) {
        out.push(absPath);
      }
    }
  }

  await visit(root);
  return out.sort((a, b) => a.localeCompare(b));
}

function classifyFile(absPath: string): FileKind {
  const ext = path.extname(absPath).toLowerCase();
  const base = path.basename(absPath).toLowerCase();

  if (ext === ".html" || ext === ".htm") return "html";
  if (ext === ".css") return "css";
  if (ext === ".js" || ext === ".mjs" || ext === ".cjs") return "javascript";
  if ([".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"].includes(ext)) return "image";
  if ([".woff", ".woff2", ".ttf", ".otf", ".eot"].includes(ext)) return "font";
  if (ext === ".pdf") return "pdf";
  if (ext === ".pptx") return "pptx";
  if (ext === ".md" && (base.includes("handoff") || base.includes("claude-code") || base.includes("claude_code"))) {
    return "handoff";
  }
  if ([".json", ".txt", ".md", ".xml", ".csv"].includes(ext)) return "asset";
  return "unknown";
}

async function fileRecord(absPath: string, sourceRoot: string): Promise<FileRecord> {
  const bytes = await readFile(absPath);
  return {
    path: normalizeRel(path.relative(sourceRoot, absPath)),
    bytes: bytes.byteLength,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    kind: classifyFile(absPath),
  };
}

async function readTextIfSmall(absPath: string): Promise<string | null> {
  const info = await stat(absPath).catch(() => null);
  if (!info || !info.isFile() || info.size > MAX_TEXT_FILE_BYTES) {
    return null;
  }
  const ext = path.extname(absPath).toLowerCase();
  if (![".html", ".htm", ".css", ".js", ".mjs", ".md", ".txt"].includes(ext)) {
    return null;
  }
  return await readFile(absPath, "utf8").catch(() => null);
}

function uniqueByValue<T extends { value: string; source: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const item of items) {
    const key = `${item.value}@@${item.source}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}

function extractCssValues(text: string, source: string): TokenSet {
  const colors: TokenSet["colors"] = [];
  const typography: TokenSet["typography"] = [];
  const spacing: TokenSet["spacing"] = [];
  const radii: TokenSet["radii"] = [];
  const shadows: TokenSet["shadows"] = [];

  for (const match of text.matchAll(/#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)/g)) {
    colors.push({ name: "color", value: match[0], source });
  }

  for (const match of text.matchAll(/font-family\s*:\s*([^;}{]+)/gi)) {
    typography.push({ role: "font-family", value: cleanupCssValue(match[1]), source });
  }
  for (const match of text.matchAll(/font-weight\s*:\s*([^;}{]+)/gi)) {
    typography.push({ role: "font-weight", value: cleanupCssValue(match[1]), source });
  }
  for (const match of text.matchAll(/font-size\s*:\s*([^;}{]+)/gi)) {
    typography.push({ role: "font-size", value: cleanupCssValue(match[1]), source });
  }
  for (const match of text.matchAll(/\b(?:gap|margin|padding|inset|top|right|bottom|left)\s*:\s*([^;}{]+)/gi)) {
    spacing.push({ name: match[0].split(":")[0].trim().toLowerCase(), value: cleanupCssValue(match[1]), source });
  }
  for (const match of text.matchAll(/border-radius\s*:\s*([^;}{]+)/gi)) {
    radii.push({ name: "border-radius", value: cleanupCssValue(match[1]), source });
  }
  for (const match of text.matchAll(/box-shadow\s*:\s*([^;}{]+)/gi)) {
    shadows.push({ name: "box-shadow", value: cleanupCssValue(match[1]), source });
  }

  return {
    artifact_type: "claude_design_tokens",
    schema_version: 1,
    created_at_utc: new Date().toISOString(),
    colors: uniqueByValue(colors).slice(0, 80),
    typography: uniqueByValue(typography).slice(0, 80),
    spacing: uniqueByValue(spacing).slice(0, 120),
    radii: uniqueByValue(radii).slice(0, 40),
    shadows: uniqueByValue(shadows).slice(0, 40),
    assets: [],
    unknowns: [],
  };
}

function cleanupCssValue(value: string | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function mergeTokens(tokenSets: TokenSet[], assetRecords: FileRecord[]): TokenSet {
  const merged: TokenSet = {
    artifact_type: "claude_design_tokens",
    schema_version: 1,
    created_at_utc: new Date().toISOString(),
    colors: [],
    typography: [],
    spacing: [],
    radii: [],
    shadows: [],
    assets: assetRecords.map((record) => ({
      path: `source/${record.path}`,
      role: record.kind === "image" ? "image" : record.kind,
    })),
    unknowns: [],
  };

  for (const tokens of tokenSets) {
    merged.colors.push(...tokens.colors);
    merged.typography.push(...tokens.typography);
    merged.spacing.push(...tokens.spacing);
    merged.radii.push(...tokens.radii);
    merged.shadows.push(...tokens.shadows);
  }

  merged.colors = uniqueByValue(merged.colors).slice(0, 80);
  merged.typography = uniqueByValue(merged.typography).slice(0, 80);
  merged.spacing = uniqueByValue(merged.spacing).slice(0, 120);
  merged.radii = uniqueByValue(merged.radii).slice(0, 40);
  merged.shadows = uniqueByValue(merged.shadows).slice(0, 40);

  if (merged.colors.length === 0) {
    merged.unknowns.push("No color tokens could be extracted from local HTML/CSS text.");
  }
  if (merged.typography.length === 0) {
    merged.unknowns.push("No typography tokens could be extracted from local HTML/CSS text.");
  }
  if (merged.assets.length === 0) {
    merged.unknowns.push("No image/font assets were detected.");
  }
  merged.unknowns.push("Component semantics and interaction intent may require human review.");

  return merged;
}

function exportIdFromRoot(exportRoot: string): string {
  const rel = toRepoPath(exportRoot);
  return rel.replace(/^artifacts\/claude-design\//, "");
}

function buildBlockedBoundaries(): BoundaryRecord[] {
  return [
    {
      artifact_type: "impossible_currently_boundary",
      gate: "preview/live_claude_design_embed",
      claim: "Render live claude.ai/design inside VS Code",
      observed_failure: "Observed Cloudflare challenge plus X-Frame-Options/CSP/auth boundary.",
      proof: "docs/ops/CLAUDE_DESIGN_FAF_BRIDGE.md#live-embed-gate",
      minimum_condition_to_reopen: "Official Anthropic embeddable Claude Design API, MCP, or approved integration surface.",
      upstream_dependency: "Anthropic Claude Design integration support",
      next_probe: "Re-check official Claude Design integration docs and response headers.",
      status: "blocked_not_closed",
    },
  ];
}

function buildManifest(exportRoot: string, sourceRoot: string, frameRoot: string, records: FileRecord[]): Manifest {
  const has = (kind: FileKind) => records.some((record) => record.kind === kind);
  const primary = (kind: FileKind) => records.filter((record) => record.kind === kind).map((record) => `source/${record.path}`);
  const screenshots = records
    .filter((record) => record.kind === "image" && /screenshot|desktop|mobile|contact/i.test(record.path))
    .map((record) => `source/${record.path}`);

  return {
    artifact_type: "claude_design_frame_manifest",
    schema_version: 1,
    created_at_utc: new Date().toISOString(),
    export_id: exportIdFromRoot(exportRoot),
    source_root: toRepoPath(sourceRoot),
    frame_root: toRepoPath(frameRoot),
    detected: {
      html: has("html"),
      css: has("css"),
      javascript: has("javascript"),
      assets: records.some((record) => ["asset", "font", "image", "unknown"].includes(record.kind)),
      images: has("image"),
      pdf: has("pdf"),
      pptx: has("pptx"),
      handoff: has("handoff"),
    },
    levels: {
      L0: records.length > 0 ? "admitted" : "blocked_not_closed",
      L1: records.length > 0 ? "admitted" : "blocked_not_closed",
      L2: has("html") || has("image") || has("pdf") || has("pptx") ? "open" : "degraded",
      L3: "admitted",
      L4: "admitted",
      L5: "open",
    },
    files: records,
    primary_files: {
      html: primary("html"),
      css: primary("css"),
      handoff: primary("handoff"),
      screenshots,
    },
    blocked_boundaries: buildBlockedBoundaries(),
    notes: [
      "Contract extraction is integrated into scripts/claude-design-intake.ts for the first implementation slice.",
      "No Claude API, Claude Agent SDK, or Claude Code call was made by this intake.",
      "L2 remains open until a frontend/webview preview probe renders the export or records a degraded preview.",
      "L5 remains open until an implementation agent applies the contract to exact target files and passes visual checks.",
    ],
  };
}

function markdownList(items: string[], fallback = "- Not detected."): string {
  if (items.length === 0) return fallback;
  return items.map((item) => `- ${item}`).join("\n");
}

function buildDesignContract(manifest: Manifest, tokens: TokenSet, targetFiles: string[]): string {
  const colorSummary = tokens.colors.slice(0, 16).map((item) => `${item.value} (${item.source})`);
  const typeSummary = tokens.typography.slice(0, 16).map((item) => `${item.role}: ${item.value} (${item.source})`);
  const spacingSummary = tokens.spacing.slice(0, 16).map((item) => `${item.name}: ${item.value} (${item.source})`);

  return `# Design Contract

## Source
- Export id: ${manifest.export_id}
- Export source root: ${manifest.source_root}
- Frame root: ${manifest.frame_root}
- HTML sources:
${markdownList(manifest.primary_files.html)}
- Handoff sources:
${markdownList(manifest.primary_files.handoff)}
- Screenshots:
${markdownList(manifest.primary_files.screenshots)}

## Implementation Target
- App/route/component: TODO
- Files expected to change:
${targetFiles.length > 0 ? markdownList(targetFiles) : "- TODO: provide exact repo paths before implementation."}

## Visual Requirements
- Layout: TODO, verify against Claude Design export preview.
- Breakpoints: desktop and mobile are required before admission.
- Colors:
${markdownList(colorSummary, "- No color tokens extracted; inspect the export manually.")}
- Typography:
${markdownList(typeSummary, "- No typography tokens extracted; inspect the export manually.")}
- Spacing:
${markdownList(spacingSummary, "- No spacing tokens extracted; inspect the export manually.")}
- Assets:
${markdownList(tokens.assets.slice(0, 20).map((item) => `${item.path} (${item.role})`), "- No assets detected.")}

## Interaction Requirements
- States: TODO
- Inputs: TODO
- Empty/loading/error: TODO
- Animation/motion: TODO

## Acceptance Checks
- Desktop screenshot: required.
- Mobile screenshot: required.
- No overlapping text or controls.
- Contract tokens matched or deviations recorded.
- Raw export is not pasted into Claude Code context unless this contract lacks a required fact.

## Token Boundary
- Use this contract, \`tokens.json\`, selected screenshots, and exact target paths.
- Do not paste the raw export or Claude Design conversation history into Claude Code.
- If a fact is missing, run a local probe or inspect the export first; only escalate the smallest missing slice.

## Unknowns
${markdownList(tokens.unknowns)}
`;
}

function buildHandoffPrompt(manifest: Manifest, targetFiles: string[]): string {
  const frameRoot = manifest.frame_root;
  const targets = targetFiles.length > 0 ? markdownList(targetFiles) : "- <exact repo path>";
  const screenshotLines =
    manifest.primary_files.screenshots.length > 0
      ? manifest.primary_files.screenshots.map((item) => `- ${item}`).join("\n")
      : "- <optional selected screenshot path>";

  return `Implement the design contract at:
${frameRoot}/design_contract.md

Use these supporting files only:
- ${frameRoot}/tokens.json
- ${frameRoot}/manifest.json
${screenshotLines}

Target files:
${targets}

Rules:
- Do not read the raw export unless the contract explicitly lacks required visual facts.
- Before editing, report the files you will touch.
- Keep backend/API work mocked or deferred unless the contract explicitly requires it.
- After editing, run the relevant frontend checks and capture desktop/mobile screenshots.
- Record any impossible-currently boundary instead of inventing missing design intent.
`;
}

function gateRecord(gate: string, status: GateStatus, levelReached: string, observedFailure = "none"): string {
  return JSON.stringify({
    artifact_type: "probe",
    gate,
    observed_failure: observedFailure,
    level_reached: levelReached,
    status,
    recorded_at_utc: new Date().toISOString(),
  });
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const roots = inferRoots(options.inputRoot);
  await ensureDirectory(roots.sourceRoot);
  await mkdir(roots.frameRoot, { recursive: true });

  const absFiles = await walkFiles(roots.sourceRoot, new Set([path.resolve(roots.frameRoot)]));
  const records = await Promise.all(absFiles.map((absPath) => fileRecord(absPath, roots.sourceRoot)));
  const manifest = buildManifest(roots.exportRoot, roots.sourceRoot, roots.frameRoot, records);

  const tokenSets: TokenSet[] = [];
  for (const absPath of absFiles) {
    const text = await readTextIfSmall(absPath);
    if (!text) continue;
    tokenSets.push(extractCssValues(text, `source/${normalizeRel(path.relative(roots.sourceRoot, absPath))}`));
  }
  const tokens = mergeTokens(
    tokenSets,
    records.filter((record) => record.kind === "image" || record.kind === "font"),
  );

  const designContract = buildDesignContract(manifest, tokens, options.targetFiles);
  const handoffPrompt = buildHandoffPrompt(manifest, options.targetFiles);
  const ledger = [
    gateRecord("claude_design_intake/source_discoverable", manifest.levels.L0, "L0"),
    gateRecord("claude_design_intake/export_classifiable", manifest.levels.L1, "L1"),
    gateRecord("claude_design_intake/contract_extraction", manifest.levels.L3, "L3"),
    gateRecord("claude_design_intake/token_bound_handoff", manifest.levels.L4, "L4"),
  ].join("\n");

  await writeFile(path.join(roots.frameRoot, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  await writeFile(path.join(roots.frameRoot, "tokens.json"), `${JSON.stringify(tokens, null, 2)}\n`, "utf8");
  await writeFile(path.join(roots.frameRoot, "design_contract.md"), designContract, "utf8");
  await writeFile(path.join(roots.frameRoot, "handoff_prompt.md"), handoffPrompt, "utf8");
  await writeFile(path.join(roots.frameRoot, "gate_ledger.jsonl"), `${ledger}\n`, "utf8");

  console.log(
    JSON.stringify(
      {
        status: "claude_design_intake_complete",
        export_id: manifest.export_id,
        emitted: [
          `${manifest.frame_root}/manifest.json`,
          `${manifest.frame_root}/tokens.json`,
          `${manifest.frame_root}/design_contract.md`,
          `${manifest.frame_root}/handoff_prompt.md`,
          `${manifest.frame_root}/gate_ledger.jsonl`,
        ],
        levels: manifest.levels,
      },
      null,
      2,
    ),
  );
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(JSON.stringify({ status: "claude_design_intake_failed", error: message }, null, 2));
  process.exit(1);
});
