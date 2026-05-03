#!/usr/bin/env bun
// @SID: session-viewer — renders Copilot Chat JSONL transcript → markdown, opens in VS Code
// Usage:
//   bun run scripts/session-viewer.ts                          # auto-detect latest transcript
//   bun run scripts/session-viewer.ts --transcript <path>     # specific transcript
//   bun run scripts/session-viewer.ts --output <path>         # custom output path
//   bun run scripts/session-viewer.ts --open                  # also open in VS Code (default: true)
//   bun run scripts/session-viewer.ts --no-open               # write only, do not open
//   bun run scripts/session-viewer.ts --tail                  # only render last N turns (default 40)
//   bun run scripts/session-viewer.ts --tail 20               # last 20 turns

import { readFileSync, existsSync, writeFileSync, statSync, readdirSync, mkdirSync, copyFileSync } from "fs";
import { join, basename } from "path";
import { spawnSync } from "child_process";
import * as os from "os";

// ──────────────────────────────────────────────────────────────
//  CLI args
// ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
function flagValue(flag: string): string | undefined {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : undefined;
}
function hasFlag(flag: string): boolean { return args.includes(flag); }

const explicitTranscript = flagValue("--transcript");
const explicitOutput = flagValue("--output");
const doOpen = !hasFlag("--no-open");
const doArchive = hasFlag("--archive");
const tailFlag = hasFlag("--tail");
const tailN = (() => {
  const v = flagValue("--tail");
  return v ? parseInt(v, 10) : (tailFlag ? 40 : Infinity);
})();

// ──────────────────────────────────────────────────────────────
//  Auto-detect latest transcript
// ──────────────────────────────────────────────────────────────
function findLatestTranscript(): string {
  const appdata = process.env["APPDATA"] ?? join(os.homedir(), "AppData", "Roaming");
  const wsRoot = join(appdata, "Code - Insiders", "User", "workspaceStorage");
  if (!existsSync(wsRoot)) throw new Error(`workspaceStorage not found: ${wsRoot}`);

  const allFiles: string[] = [];
  for (const hash of readdirSync(wsRoot)) {
    const transcriptsDir = join(wsRoot, hash, "GitHub.copilot-chat", "transcripts");
    if (!existsSync(transcriptsDir)) continue;
    for (const f of readdirSync(transcriptsDir)) {
      if (f.endsWith(".jsonl")) allFiles.push(join(transcriptsDir, f));
    }
  }
  if (allFiles.length === 0) throw new Error(`No transcript files found under: ${wsRoot}`);

  // sort by mtime descending
  const sorted = allFiles
    .map(f => ({ f, mtime: statSync(f).mtime.getTime() }))
    .sort((a, b) => b.mtime - a.mtime);
  return sorted[0].f;
}

const transcriptPath = explicitTranscript ?? findLatestTranscript();

if (!existsSync(transcriptPath)) {
  console.error(`Transcript not found: ${transcriptPath}`);
  process.exit(1);
}

// ──────────────────────────────────────────────────────────────
//  JSONL parse
// ──────────────────────────────────────────────────────────────
interface JEntry {
  type: string;
  data: Record<string, unknown>;
  id: string;
  timestamp: string;
  parentId: string | null;
}

const raw = readFileSync(transcriptPath, "utf8");
const lines = raw.split("\n").filter(l => l.trim());
const entries: JEntry[] = [];
for (const line of lines) {
  try { entries.push(JSON.parse(line) as JEntry); } catch { /* skip malformed */ }
}

// ──────────────────────────────────────────────────────────────
//  Reconstruct turns
// ──────────────────────────────────────────────────────────────
interface Turn {
  ts: string;
  role: "user" | "assistant" | "meta";
  content: string;
  tools: Array<{ name: string; args: string; success?: boolean }>;
  reasoning?: string;
}

const turns: Turn[] = [];
const toolSuccessMap: Record<string, boolean> = {};

// first pass: collect tool completion outcomes
for (const e of entries) {
  if (e.type === "tool.execution_complete") {
    const d = e.data as { toolCallId?: string; success?: boolean };
    if (d.toolCallId) toolSuccessMap[d.toolCallId] = d.success ?? true;
  }
}

// second pass: build turns
const sessionData = entries.find(e => e.type === "session.start")?.data as
  { sessionId?: string; startTime?: string; vscodeVersion?: string; copilotVersion?: string } | undefined;

for (const e of entries) {
  if (e.type === "user.message") {
    const d = e.data as { content?: string };
    turns.push({
      ts: e.timestamp,
      role: "user",
      content: (d.content ?? "").trim(),
      tools: [],
    });
  } else if (e.type === "assistant.message") {
    const d = e.data as {
      content?: string;
      toolRequests?: Array<{ toolCallId: string; name: string; arguments: string }>;
      reasoningText?: string;
    };
    const tools = (d.toolRequests ?? []).map(tr => ({
      name: tr.name,
      args: tr.arguments,
      success: toolSuccessMap[tr.toolCallId],
    }));
    const content = (d.content ?? "").trim();
    // Only add an assistant turn if there's content OR tools (skip empty delimiters)
    if (content || tools.length > 0) {
      turns.push({
        ts: e.timestamp,
        role: "assistant",
        content,
        tools,
        reasoning: d.reasoningText?.trim(),
      });
    }
  }
}

// ──────────────────────────────────────────────────────────────
//  Apply --tail window
// ──────────────────────────────────────────────────────────────
const visibleTurns = isFinite(tailN) ? turns.slice(-Math.abs(tailN)) : turns;
const isTruncated = visibleTurns.length < turns.length;

// ──────────────────────────────────────────────────────────────
//  Markdown render helpers
// ──────────────────────────────────────────────────────────────
const MAX_CONTENT = 6000;  // chars before truncation
const MAX_ARGS = 800;

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + `\n\n> …*[${s.length - max} chars truncated]*`;
}

function ts(iso: string): string {
  // format as HH:MM:SS UTC
  const d = new Date(iso);
  return d.toISOString().slice(11, 19) + " UTC";
}

function renderTool(t: { name: string; args: string; success?: boolean }, i: number): string {
  const icon = t.success === false ? "❌" : t.success === true ? "✅" : "🔧";
  let argsStr = t.args;
  try {
    argsStr = JSON.stringify(JSON.parse(t.args), null, 2);
  } catch { /* keep raw */ }
  argsStr = truncate(argsStr, MAX_ARGS);
  return [
    `<details>`,
    `<summary>${icon} <code>${t.name}</code></summary>`,
    ``,
    "```json",
    argsStr,
    "```",
    `</details>`,
  ].join("\n");
}

function renderTurn(t: Turn, idx: number): string {
  const lines: string[] = [];
  const timeStr = ts(t.ts);

  if (t.role === "user") {
    lines.push(`---`);
    lines.push(`## 👤 User · ${timeStr}`);
    lines.push(``);
    lines.push(truncate(t.content, MAX_CONTENT));
    lines.push(``);
  } else {
    lines.push(`### 🤖 Assistant · ${timeStr}`);
    lines.push(``);
    if (t.reasoning) {
      lines.push(`<details>`);
      lines.push(`<summary>💭 Reasoning (${t.reasoning.length} chars)</summary>`);
      lines.push(``);
      lines.push(truncate(t.reasoning, 1200));
      lines.push(``);
      lines.push(`</details>`);
      lines.push(``);
    }
    if (t.content) {
      lines.push(truncate(t.content, MAX_CONTENT));
      lines.push(``);
    }
    if (t.tools.length > 0) {
      lines.push(`**Tools called (${t.tools.length}):**`);
      lines.push(``);
      for (let i = 0; i < t.tools.length; i++) {
        lines.push(renderTool(t.tools[i], i));
      }
      lines.push(``);
    }
  }
  return lines.join("\n");
}

// ──────────────────────────────────────────────────────────────
//  Assemble full document
// ──────────────────────────────────────────────────────────────
const sessionId = sessionData?.sessionId ?? basename(transcriptPath, ".jsonl");
const startTime = sessionData?.startTime ?? "";
const vscodeVer = sessionData?.vscodeVersion ?? "";
const copilotVer = sessionData?.copilotVersion ?? "";

const header = [
  `# Session Transcript Viewer`,
  ``,
  `| Field | Value |`,
  `|-------|-------|`,
  `| Session ID | \`${sessionId}\` |`,
  `| Started | ${startTime} |`,
  `| VS Code | ${vscodeVer} |`,
  `| Copilot | ${copilotVer} |`,
  `| Total turns | ${turns.length} |`,
  `| Shown | ${visibleTurns.length}${isTruncated ? ` (last ${tailN} turns — use \`--tail\` to change)` : ""} |`,
  `| Source | \`${transcriptPath}\` |`,
  ``,
  isTruncated
    ? `> ⚠️ Showing last **${visibleTurns.length}** of **${turns.length}** turns. Run with \`--tail 9999\` for full history.`
    : `> Full session — ${turns.length} turns total.`,
  ``,
].join("\n");

const body = visibleTurns.map(renderTurn).join("\n");
const footer = `\n\n---\n*Generated ${new Date().toISOString()} · session-viewer.ts*\n`;

const doc = header + "\n" + body + footer;

// ──────────────────────────────────────────────────────────────
//  Write output
// ──────────────────────────────────────────────────────────────
const manifestDir = join(import.meta.dir, "..", "manifest");
const defaultOutput = join(manifestDir, "session_view.md");
const outputPath = explicitOutput ?? defaultOutput;
writeFileSync(outputPath, doc, "utf8");
console.log(`✅ Written: ${outputPath} (${turns.length} turns, ${visibleTurns.length} shown)`);

// ──────────────────────────────────────────────────────────────
//  Archive: copy JSONL + full render into manifest/sessions/<id>/
// ──────────────────────────────────────────────────────────────
if (doArchive) {
  const sessionsDir = join(manifestDir, "sessions");
  const sessionDir = join(sessionsDir, sessionId);
  mkdirSync(sessionDir, { recursive: true });

  // Copy raw JSONL (ground truth — no truncation)
  copyFileSync(transcriptPath, join(sessionDir, "transcript.jsonl"));

  // Write meta.json
  const workspaceHash = transcriptPath.match(/workspaceStorage[\/\\]([^\/\\]+)[\/\\]/)?.[1] ?? "";
  const meta = {
    sessionId,
    startTime,
    archivedAt: new Date().toISOString(),
    sourcePath: transcriptPath,
    workspaceHash,
    vscodeVersion: vscodeVer,
    copilotVersion: copilotVer,
    turns: turns.length,
    lines: lines.length,
  };
  writeFileSync(join(sessionDir, "meta.json"), JSON.stringify(meta, null, 2), "utf8");

  // Full render (all turns, no tail truncation) into session dir
  const archiveHeader = [
    `# Session Transcript — ${sessionId}`,
    ``,
    `| Field | Value |`,
    `|-------|-------|`,
    `| Session ID | \`${sessionId}\` |`,
    `| Started | ${startTime} |`,
    `| VS Code | ${vscodeVer} |`,
    `| Copilot | ${copilotVer} |`,
    `| Total turns | ${turns.length} |`,
    `| JSONL lines | ${lines.length} |`,
    `| Archived | ${meta.archivedAt} |`,
    `| Workspace hash | \`${workspaceHash}\` |`,
    ``,
    `> Full session — ${turns.length} turns total.`,
    ``,
  ].join("\n");
  const archiveBody = turns.map(renderTurn).join("\n");
  const archiveDoc = archiveHeader + "\n" + archiveBody + footer;
  writeFileSync(join(sessionDir, "session_view.md"), archiveDoc, "utf8");

  // Upsert sessions_index.json
  const indexPath = join(manifestDir, "sessions_index.json");
  type MetaEntry = typeof meta;
  let index: MetaEntry[] = [];
  if (existsSync(indexPath)) {
    try { index = JSON.parse(readFileSync(indexPath, "utf8")); } catch { /* start fresh */ }
  }
  const existingIdx = index.findIndex((s: MetaEntry) => s.sessionId === sessionId);
  if (existingIdx >= 0) index[existingIdx] = meta;
  else index.push(meta);
  index.sort((a: MetaEntry, b: MetaEntry) =>
    new Date(b.startTime || b.archivedAt).getTime() - new Date(a.startTime || a.archivedAt).getTime()
  );
  writeFileSync(indexPath, JSON.stringify(index, null, 2), "utf8");

  console.log(`📦 Archived to: ${sessionDir}`);
  console.log(`   - transcript.jsonl (${lines.length} lines — ground truth)`);
  console.log(`   - session_view.md (${turns.length} turns — full render)`);
  console.log(`   - meta.json`);
  console.log(`   - sessions_index.json updated (${index.length} total sessions)`);
}

// ──────────────────────────────────────────────────────────────
//  Open in VS Code (to the side)
// ──────────────────────────────────────────────────────────────
if (doOpen) {
  // Open as markdown preview to the side
  const codeCmd = "code-insiders";
  // First open the raw file (creates the tab), then open preview beside it
  const r1 = spawnSync(codeCmd, ["-r", outputPath], { shell: true });
  if (r1.status !== 0) {
    // Fallback to 'code'
    spawnSync("code", ["-r", outputPath], { shell: true });
  }
  console.log(`📖 Opened in VS Code: ${outputPath}`);
  console.log(`   Tip: right-click the tab → "Open Preview to the Side" for rendered markdown`);
  console.log(`   Or: Ctrl+Shift+V to toggle preview, Ctrl+K V for side-by-side`);
}
