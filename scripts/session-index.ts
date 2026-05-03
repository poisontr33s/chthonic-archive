#!/usr/bin/env bun
// @SID: session-index — query and search archived Copilot Chat session transcripts
// Usage:
//   bun run scripts/session-index.ts                        # list all archived sessions
//   bun run scripts/session-index.ts --search <term>        # grep across all archived transcripts
//   bun run scripts/session-index.ts --show <session-id>    # re-render a specific archived session
//   bun run scripts/session-index.ts --failures             # show all tool failures across archives
//   bun run scripts/session-index.ts --json                 # output index as JSON

import { existsSync, readFileSync, readdirSync } from "fs";
import { join } from "path";
import { spawnSync } from "child_process";

const args = process.argv.slice(2);
function flagValue(flag: string): string | undefined {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : undefined;
}
function hasFlag(flag: string): boolean { return args.includes(flag); }

const manifestDir = join(import.meta.dir, "..", "manifest");
const sessionsDir = join(manifestDir, "sessions");
const indexPath = join(manifestDir, "sessions_index.json");

// ──────────────────────────────────────────────────────────────
//  Load index
// ──────────────────────────────────────────────────────────────
interface SessionMeta {
  sessionId: string;
  startTime: string;
  archivedAt: string;
  sourcePath: string;
  workspaceHash: string;
  vscodeVersion: string;
  copilotVersion: string;
  turns: number;
  lines: number;
}

function loadIndex(): SessionMeta[] {
  if (!existsSync(indexPath)) return [];
  try { return JSON.parse(readFileSync(indexPath, "utf8")); } catch { return []; }
}

function formatDate(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

// ──────────────────────────────────────────────────────────────
//  --list (default)
// ──────────────────────────────────────────────────────────────
function cmdList() {
  const index = loadIndex();
  if (index.length === 0) {
    console.log("No archived sessions found.");
    console.log(`Run: bun run scripts/session-viewer.ts --archive`);
    return;
  }

  if (hasFlag("--json")) {
    console.log(JSON.stringify(index, null, 2));
    return;
  }

  console.log(`\n📚 Archived Sessions (${index.length})\n`);
  console.log("─".repeat(100));
  const idW = 38, dateW = 20, turnsW = 8;
  console.log(
    "Session ID".padEnd(idW) +
    "Started".padEnd(dateW) +
    "Turns".padStart(turnsW) +
    "  " +
    "Archived"
  );
  console.log("─".repeat(100));
  for (const s of index) {
    console.log(
      s.sessionId.slice(0, 36).padEnd(idW) +
      formatDate(s.startTime).padEnd(dateW) +
      String(s.turns).padStart(turnsW) +
      "  " +
      formatDate(s.archivedAt)
    );
  }
  console.log("─".repeat(100));
  console.log(`\nTotal turns archived: ${index.reduce((n, s) => n + s.turns, 0)}`);
  console.log(`Sessions dir: ${sessionsDir}`);
}

// ──────────────────────────────────────────────────────────────
//  --search <term>  — grep user messages + assistant content
// ──────────────────────────────────────────────────────────────
function cmdSearch(term: string) {
  const index = loadIndex();
  if (index.length === 0) {
    console.log("No archived sessions. Run --archive first.");
    return;
  }

  const pattern = new RegExp(term, "gi");
  let totalHits = 0;
  const CONTEXT = 200; // chars around match

  for (const s of index) {
    const jsonlPath = join(sessionsDir, s.sessionId, "transcript.jsonl");
    if (!existsSync(jsonlPath)) continue;

    const raw = readFileSync(jsonlPath, "utf8");
    const lines = raw.split("\n").filter(l => l.trim());
    const hits: Array<{ ts: string; role: string; excerpt: string }> = [];

    for (const line of lines) {
      let entry: { type: string; data: Record<string, unknown>; timestamp: string };
      try { entry = JSON.parse(line); } catch { continue; }

      let searchable = "";
      let role = "";
      if (entry.type === "user.message") {
        searchable = String((entry.data as { content?: string }).content ?? "");
        role = "user";
      } else if (entry.type === "assistant.message") {
        searchable = String((entry.data as { content?: string }).content ?? "");
        role = "assistant";
      }
      if (!searchable) continue;

      const m = pattern.exec(searchable);
      if (m) {
        const start = Math.max(0, m.index - CONTEXT / 2);
        const end = Math.min(searchable.length, m.index + term.length + CONTEXT / 2);
        const excerpt = (start > 0 ? "…" : "") + searchable.slice(start, end).replace(/\n/g, " ") + (end < searchable.length ? "…" : "");
        hits.push({ ts: entry.timestamp, role, excerpt });
        totalHits++;
      }
      pattern.lastIndex = 0; // reset for global flag
    }

    if (hits.length > 0) {
      console.log(`\n🔍 Session: ${s.sessionId} (${formatDate(s.startTime)})`);
      console.log(`   ${hits.length} hit(s)`);
      for (const h of hits.slice(0, 10)) {
        const time = new Date(h.ts).toISOString().slice(11, 19);
        console.log(`   [${time}] ${h.role.padEnd(10)} ${h.excerpt}`);
      }
      if (hits.length > 10) console.log(`   … and ${hits.length - 10} more`);
    }
  }

  console.log(`\nTotal hits across ${index.length} sessions: ${totalHits}`);
}

// ──────────────────────────────────────────────────────────────
//  --failures  — tool execution failures across archives
// ──────────────────────────────────────────────────────────────
function cmdFailures() {
  const index = loadIndex();
  let totalFails = 0;

  for (const s of index) {
    const jsonlPath = join(sessionsDir, s.sessionId, "transcript.jsonl");
    if (!existsSync(jsonlPath)) continue;

    const raw = readFileSync(jsonlPath, "utf8");
    const lines = raw.split("\n").filter(l => l.trim());
    const fails: Array<{ ts: string; toolName: string; toolCallId: string }> = [];

    // Build name map from execution_start
    const nameMap: Record<string, string> = {};
    for (const line of lines) {
      let entry: { type: string; data: Record<string, unknown>; timestamp: string };
      try { entry = JSON.parse(line); } catch { continue; }
      if (entry.type === "tool.execution_start") {
        const d = entry.data as { toolCallId?: string; toolName?: string };
        if (d.toolCallId && d.toolName) nameMap[d.toolCallId] = d.toolName;
      }
      if (entry.type === "tool.execution_complete") {
        const d = entry.data as { toolCallId?: string; success?: boolean };
        if (d.toolCallId && d.success === false) {
          fails.push({
            ts: entry.timestamp,
            toolName: nameMap[d.toolCallId] ?? "unknown",
            toolCallId: d.toolCallId,
          });
          totalFails++;
        }
      }
    }

    if (fails.length > 0) {
      console.log(`\n❌ Session: ${s.sessionId} (${formatDate(s.startTime)}) — ${fails.length} failures`);
      for (const f of fails) {
        const time = new Date(f.ts).toISOString().slice(11, 19);
        console.log(`   [${time}] ${f.toolName}`);
      }
    }
  }

  console.log(`\nTotal tool failures across ${index.length} sessions: ${totalFails}`);
}

// ──────────────────────────────────────────────────────────────
//  --show <session-id>  — open archived session_view.md
// ──────────────────────────────────────────────────────────────
function cmdShow(sessionId: string) {
  const viewPath = join(sessionsDir, sessionId, "session_view.md");
  if (!existsSync(viewPath)) {
    console.error(`No archive for session: ${sessionId}`);
    console.error(`Run: bun run scripts/session-viewer.ts --archive --transcript <path>`);
    process.exit(1);
  }
  const r = spawnSync("code-insiders", ["-r", viewPath], { shell: true });
  if (r.status !== 0) spawnSync("code", ["-r", viewPath], { shell: true });
  console.log(`📖 Opened: ${viewPath}`);
}

// ──────────────────────────────────────────────────────────────
//  Dispatch
// ──────────────────────────────────────────────────────────────
const searchTerm = flagValue("--search");
const showId = flagValue("--show");

if (searchTerm) {
  cmdSearch(searchTerm);
} else if (showId) {
  cmdShow(showId);
} else if (hasFlag("--failures")) {
  cmdFailures();
} else {
  cmdList();
}
