#!/usr/bin/env bun
// @SID: session-query — query manifest/corpus.sqlite  (Bun built-in SQLite)
//
// Usage:
//   bun run scripts/session-query.ts --timeline              # all sessions with edit/cmd/memory stats
//   bun run scripts/session-query.ts --hot-files [N]         # top N edited files (default 20)
//   bun run scripts/session-query.ts --tool-frequency [N]    # top N tools by call count
//   bun run scripts/session-query.ts --memory-chain <file>   # evolution of a memory file over sessions
//   bun run scripts/session-query.ts --memory-search <term>  # full-text search in memory content
//   bun run scripts/session-query.ts --code-langs            # language distribution of code blocks
//   bun run scripts/session-query.ts --sessions              # list all sessions
//   bun run scripts/session-query.ts --session <id>          # detailed view of one session (partial id ok)
//   bun run scripts/session-query.ts --sql "SELECT ..."      # raw SQL against corpus.sqlite

import { Database } from "bun:sqlite";
import { existsSync } from "fs";
import { join } from "path";

const args       = process.argv.slice(2);
const corpusPath = join(import.meta.dir, "..", "manifest", "corpus.sqlite");

if (!existsSync(corpusPath)) {
  console.error("corpus.sqlite not found. Build it first: bun run session:corpus");
  process.exit(1);
}

const db = new Database(corpusPath, { readonly: true });

// ─────────────────────────────────────────────────────────────
// Output helpers
// ─────────────────────────────────────────────────────────────

function table(rows: Record<string, unknown>[], cols?: string[]) {
  if (!rows.length) { console.log("(no results)"); return; }
  const keys   = cols ?? Object.keys(rows[0]);
  const widths = keys.map(k => Math.max(k.length, ...rows.map(r => String(r[k] ?? "").length)));
  const header = keys.map((k, i) => k.padEnd(widths[i])).join("  ");
  const sep    = widths.map(w => "─".repeat(w)).join("──");
  console.log(header);
  console.log(sep);
  for (const row of rows)
    console.log(keys.map((k, i) => String(row[k] ?? "").padEnd(widths[i])).join("  "));
  console.log(`\n${rows.length} row(s)`);
}

function trunc(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function flag(name: string): boolean { return args.includes(name); }
function flagArg(name: string): string | null {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] ?? null : null;
}
function flagNum(name: string, def: number): number {
  const i = args.indexOf(name);
  const v = i >= 0 ? parseInt(args[i + 1] ?? "", 10) : NaN;
  return isNaN(v) ? def : v;
}

// ─────────────────────────────────────────────────────────────
// Commands
// ─────────────────────────────────────────────────────────────

if (flag("--timeline")) {
  console.log("\n📅 SESSION TIMELINE\n");
  const rows = db.prepare(`
    SELECT sessionId, startTime, turns, editCount, cmdCount, codeBlockCount,
           memoryFileCount, commitCount, SUBSTR(intent, 1, 60) AS intent
    FROM session_timeline
  `).all() as Record<string, unknown>[];
  table(rows, ["sessionId", "startTime", "turns", "editCount", "cmdCount", "memoryFileCount", "commitCount", "intent"]);

} else if (flag("--hot-files")) {
  const n = flagNum("--hot-files", 20);
  console.log(`\n✏️  HOT FILES (top ${n})\n`);
  const rows = db.prepare("SELECT filePath, editCount, sessionCount FROM hot_files LIMIT ?").all(n) as Record<string, unknown>[];
  table(rows);

} else if (flag("--tool-frequency")) {
  const n = flagNum("--tool-frequency", 20);
  console.log(`\n🔧 TOOL FREQUENCY (top ${n})\n`);
  const rows = db.prepare(`
    SELECT toolName,
           COUNT(*) AS callCount,
           COUNT(DISTINCT sessionId) AS sessionCount,
           ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS successPct
    FROM tool_calls
    GROUP BY toolName ORDER BY callCount DESC LIMIT ?
  `).all(n) as Record<string, unknown>[];
  table(rows);

} else if (flag("--memory-chain")) {
  const filename = flagArg("--memory-chain");
  if (!filename) { console.error("Usage: --memory-chain <filename>"); process.exit(1); }
  console.log(`\n💾 MEMORY CHAIN: ${filename}\n`);
  const rows = db.prepare(`
    SELECT sessionId, startTime, capturedAt, contentBytes
    FROM memory_chain WHERE filename = ?
  `).all(filename) as Record<string, unknown>[];
  table(rows);
  if (rows.length) {
    const latest = db.prepare(`
      SELECT ms.content FROM memory_snapshots ms
      JOIN sessions s ON ms.sessionId = s.sessionId
      WHERE ms.filename = ? ORDER BY s.startTime DESC LIMIT 1
    `).get(filename) as { content: string } | undefined;
    if (latest) { console.log("\nLatest content:\n"); console.log(latest.content); }
  }

} else if (flag("--memory-search")) {
  const term = flagArg("--memory-search");
  if (!term) { console.error("Usage: --memory-search <term>"); process.exit(1); }
  console.log(`\n🔍 MEMORY SEARCH: "${term}"\n`);
  const rows = db.prepare(`
    SELECT ms.sessionId, ms.filename, s.startTime, LENGTH(ms.content) AS contentBytes
    FROM memory_snapshots ms
    JOIN sessions s ON ms.sessionId = s.sessionId
    WHERE ms.content LIKE ?
    ORDER BY s.startTime DESC
  `).all(`%${term}%`) as Record<string, unknown>[];
  table(rows);

} else if (flag("--code-langs")) {
  console.log("\n📝 CODE BLOCK LANGUAGES\n");
  const rows = db.prepare(`
    SELECT COALESCE(NULLIF(lang,''), '(unlabelled)') AS lang,
           COUNT(*) AS blockCount, SUM(lines) AS totalLines,
           COUNT(DISTINCT sessionId) AS sessionCount
    FROM code_blocks GROUP BY lang ORDER BY blockCount DESC
  `).all() as Record<string, unknown>[];
  table(rows);

} else if (flag("--session")) {
  const id = flagArg("--session");
  if (!id) { console.error("Usage: --session <id>"); process.exit(1); }
  const s = db.prepare("SELECT * FROM sessions WHERE sessionId LIKE ?").get(`${id}%`) as Record<string, unknown> | undefined;
  if (!s) { console.error(`Session not found: ${id}`); process.exit(1); }
  const sId = String(s.sessionId);
  console.log(`\n🩸 SESSION: ${sId}\n`);
  console.log(`  Start:    ${s.startTime}`);
  console.log(`  Copilot:  ${s.copilotVersion}   VSCode: ${s.vscodeVersion}`);
  console.log(`  Turns:    ${s.turns}`);
  console.log(`  Intent:   ${String(s.intent ?? "").slice(0, 120)}`);

  const counts = db.prepare(`
    SELECT
      (SELECT COUNT(*) FROM file_edits      WHERE sessionId = ?) AS edits,
      (SELECT COUNT(*) FROM terminal_cmds   WHERE sessionId = ?) AS cmds,
      (SELECT COUNT(*) FROM code_blocks     WHERE sessionId = ?) AS blocks,
      (SELECT COUNT(*) FROM memory_snapshots WHERE sessionId = ?) AS mems,
      (SELECT COUNT(*) FROM tool_calls      WHERE sessionId = ?) AS tools,
      (SELECT COUNT(*) FROM commit_refs     WHERE sessionId = ?) AS commits
  `).get(sId, sId, sId, sId, sId, sId) as Record<string, number>;
  console.log(`\n  ${counts.edits} edits  ${counts.cmds} commands  ${counts.blocks} code blocks  ${counts.mems} memory files  ${counts.tools} tool calls  ${counts.commits} commit refs`);

  const topFiles = db.prepare(`
    SELECT filePath, COUNT(*) AS n FROM file_edits WHERE sessionId = ?
    GROUP BY filePath ORDER BY n DESC LIMIT 10
  `).all(sId) as Array<{ filePath: string; n: number }>;
  if (topFiles.length) {
    console.log("\n  Top edited files:");
    for (const f of topFiles) console.log(`    ${String(f.n).padStart(3)}×  ${f.filePath}`);
  }

  const cmds = db.prepare("SELECT command, goal FROM terminal_cmds WHERE sessionId = ? LIMIT 10").all(sId) as Array<{ command: string; goal: string | null }>;
  if (cmds.length) {
    console.log("\n  Terminal commands:");
    for (const c of cmds) console.log(`    ${trunc(c.command, 80)}${c.goal ? `  [${c.goal}]` : ""}`);
  }

  const mems = db.prepare("SELECT filename, LENGTH(content) AS bytes FROM memory_snapshots WHERE sessionId = ?").all(sId) as Array<{ filename: string; bytes: number }>;
  if (mems.length) {
    console.log("\n  Memory files:");
    for (const m of mems) console.log(`    ${m.filename.padEnd(40)} ${String(m.bytes).padStart(7)} B`);
  }

  const topTools = db.prepare(`
    SELECT toolName, COUNT(*) AS n, SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS ok
    FROM tool_calls WHERE sessionId = ? GROUP BY toolName ORDER BY n DESC LIMIT 10
  `).all(sId) as Array<{ toolName: string; n: number; ok: number }>;
  if (topTools.length) {
    console.log("\n  Tool calls:");
    for (const t of topTools) console.log(`    ${String(t.n).padStart(3)}×  ${t.toolName}  (${t.ok} ok)`);
  }

} else if (flag("--sessions")) {
  console.log("\n📋 ALL SESSIONS\n");
  const rows = db.prepare(`
    SELECT sessionId, startTime, turns, SUBSTR(intent, 1, 70) AS intent
    FROM sessions ORDER BY startTime DESC
  `).all() as Record<string, unknown>[];
  table(rows);

} else if (flag("--sql")) {
  const sql = flagArg("--sql");
  if (!sql) { console.error('Usage: --sql "SELECT ..."'); process.exit(1); }
  const rows = db.prepare(sql).all() as Record<string, unknown>[];
  table(rows);

} else {
  console.log(`
session-query — query manifest/corpus.sqlite

  --timeline              all sessions (start, turns, edits, commands, memory files, commits)
  --hot-files [N]         top N most edited files across all sessions  (default 20)
  --tool-frequency [N]    top N tools by call count with success %     (default 20)
  --memory-chain <file>   how one memory file evolved across sessions  + latest content
  --memory-search <term>  full-text search across all memory file content
  --code-langs            language distribution of code blocks
  --sessions              list all sessions
  --session <id>          detailed view of one session (partial id ok)
  --sql "..."             raw SQL query against corpus.sqlite

Tables: sessions, session_restarts, file_edits, terminal_cmds,
        code_blocks, tool_calls, commit_refs, memory_snapshots
Views:  hot_files, memory_chain, session_timeline
`);
}

db.close();
