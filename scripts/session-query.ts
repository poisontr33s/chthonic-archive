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
    SELECT sessionId, startTime, turns, userTurns, assistantTurns,
           editCount, cmdCount, commitCount, memoryFileCount,
           SUBSTR(intent, 1, 55) AS intent
    FROM session_timeline
  `).all() as Record<string, unknown>[];
  table(rows, ["sessionId", "startTime", "turns", "editCount", "cmdCount", "commitCount", "intent"]);

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

} else if (flag("--search")) {
  const term = flagArg("--search");
  if (!term) { console.error("Usage: --search <term>"); process.exit(1); }
  console.log(`\n🔍 CORPUS SEARCH: "${term}"\n`);
  // Check if FTS5 tables exist
  const hasFts = (db.prepare("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name='fts_messages'").get() as { n: number }).n > 0;
  if (hasFts) {
    const msgs = db.prepare(`
      SELECT sessionId, role, turn, snippet(fts_messages, 3, '▸', '◂', '…', 20) AS excerpt
      FROM fts_messages WHERE content MATCH ? ORDER BY rank LIMIT 20
    `).all(term) as Array<{ sessionId: string; role: string; turn: number; excerpt: string }>;
    if (msgs.length) {
      console.log("Messages:");
      for (const m of msgs)
        console.log(`  [${m.sessionId.slice(0, 8)}] ${m.role.padEnd(9)} turn ${String(m.turn).padStart(3)}: ${m.excerpt}`);
    }
    const cmds = db.prepare(`
      SELECT sessionId, snippet(fts_cmds, 1, '▸', '◂', '…', 15) AS cmdExcerpt, goal
      FROM fts_cmds WHERE fts_cmds MATCH ? ORDER BY rank LIMIT 10
    `).all(term) as Array<{ sessionId: string; cmdExcerpt: string; goal: string | null }>;
    if (cmds.length) {
      console.log("\nTerminal commands:");
      for (const c of cmds)
        console.log(`  [${c.sessionId.slice(0, 8)}] ${c.cmdExcerpt}${c.goal ? `  [${c.goal}]` : ""}`);
    }
    if (!msgs.length && !cmds.length) console.log("(no matches)");
  } else {
    console.log("FTS5 not indexed yet — run: bun run session:corpus:rebuild");
    const rows = db.prepare(`
      SELECT sessionId, role, turn, SUBSTR(content, MAX(1, INSTR(content, ?) - 60), 140) AS excerpt
      FROM messages WHERE content LIKE ? LIMIT 20
    `).all(term, `%${term}%`) as Record<string, unknown>[];
    table(rows);
  }

} else if (flag("--messages")) {
  const id = flagArg("--messages");
  if (!id) { console.error("Usage: --messages <id>"); process.exit(1); }
  const hasMsgs = (db.prepare("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name='messages'").get() as { n: number }).n > 0;
  if (!hasMsgs) { console.error("No messages table. Rebuild: bun run session:corpus:rebuild"); process.exit(1); }
  const s = db.prepare("SELECT * FROM sessions WHERE sessionId LIKE ?").get(`${id}%`) as Record<string, unknown> | undefined;
  if (!s) { console.error(`Session not found: ${id}`); process.exit(1); }
  const sId = String(s.sessionId);
  console.log(`\n💬 MESSAGES: ${sId}\n  ${String(s.startTime)}  —  ${String(s.intent ?? "").slice(0, 80)}\n`);
  const msgs = db.prepare(`
    SELECT role, turn, ts, SUBSTR(content, 1, 250) AS preview, toolRequestCount
    FROM messages WHERE sessionId = ? ORDER BY turn ASC
  `).all(sId) as Array<{ role: string; turn: number; ts: number | null; preview: string; toolRequestCount: number }>;
  for (const m of msgs) {
    const time = m.ts ? new Date(m.ts).toISOString().slice(11, 19) : "--:--:--";
    const tools = m.toolRequestCount > 0 ? ` [⦀${m.toolRequestCount} tools]` : "";
    const icon  = m.role === "user" ? "👤" : "🤖";
    console.log(`${icon} [${time}] turn ${String(m.turn).padStart(3)}${tools}`);
    console.log(`   ${m.preview.replace(/\n/g, " ").slice(0, 200)}`);
  }
  console.log(`\n${msgs.length} messages`);

} else if (flag("--report-html")) {
  const outPath = join(import.meta.dir, "..", "manifest", "corpus-report.html");

  const sessions = db.prepare(`
    SELECT sessionId, startTime, turns, userTurns, assistantTurns,
           editCount, cmdCount, commitCount,
           SUBSTR(intent, 1, 90) AS intent
    FROM session_timeline ORDER BY startTime DESC
  `).all() as Record<string, unknown>[];

  const hotFiles = db.prepare(`
    SELECT filePath, editCount, sessionCount FROM hot_files LIMIT 25
  `).all() as Array<{ filePath: string; editCount: number; sessionCount: number }>;

  const toolFreq = db.prepare(`
    SELECT toolName, COUNT(*) AS callCount,
           ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS successPct
    FROM tool_calls GROUP BY toolName ORDER BY callCount DESC LIMIT 20
  `).all() as Array<{ toolName: string; callCount: number; successPct: number }>;

  const summary = db.prepare(`
    SELECT
      (SELECT COUNT(*) FROM sessions)       AS sessions,
      (SELECT COUNT(*) FROM messages)       AS messages,
      (SELECT COUNT(*) FROM tool_calls)     AS toolCalls,
      (SELECT COUNT(*) FROM file_edits)     AS fileEdits,
      (SELECT COUNT(*) FROM terminal_cmds)  AS termCmds,
      (SELECT COUNT(*) FROM commit_refs)    AS commits
  `).get() as Record<string, number>;

  const maxEdits   = Math.max(1, ...hotFiles.map(f => f.editCount));
  const maxCalls   = Math.max(1, ...toolFreq.map(t => t.callCount));

  function shortPath(p: string): string {
    return p.replace(/\\/g, "/").split("/").slice(-2).join("/");
  }
  function fmtDate(d: unknown): string {
    if (!d) return "—";
    const s = String(d);
    return s.slice(0, 10) + " " + s.slice(11, 16);
  }

  const sessRows = sessions.map(s => `
    <tr>
      <td title="${s.sessionId}">${String(s.sessionId).slice(0, 8)}</td>
      <td>${fmtDate(s.startTime)}</td>
      <td>${s.turns}</td>
      <td class="num">${s.editCount}</td>
      <td class="num">${s.cmdCount}</td>
      <td class="num">${s.commitCount}</td>
      <td class="intent">${String(s.intent ?? "").replace(/</g, "&lt;")}</td>
    </tr>`).join("");

  const fileRows = hotFiles.map(f => `
    <tr>
      <td class="path" title="${f.filePath}">${shortPath(f.filePath)}</td>
      <td><div class="bar" style="width:${Math.round(100*f.editCount/maxEdits)}%"></div></td>
      <td class="num">${f.editCount}</td>
      <td class="num">${f.sessionCount}</td>
    </tr>`).join("");

  const toolRows = toolFreq.map(t => `
    <tr>
      <td class="path">${t.toolName}</td>
      <td><div class="bar" style="width:${Math.round(100*t.callCount/maxCalls)}%"></div></td>
      <td class="num">${t.callCount}</td>
      <td class="num">${t.successPct}%</td>
    </tr>`).join("");

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Corpus Report — chthonic-archive</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e0e12;--panel:#16161e;--border:#2a2a3a;--text:#d4d4f0;--muted:#666;--accent:#9d7cd8;--green:#73daca;--red:#f7768e;--yellow:#e0af68}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:14px/1.5 "Cascadia Code","JetBrains Mono",monospace;padding:24px}
h1{font-size:1.2rem;color:var(--accent);margin-bottom:4px}
.sub{color:var(--muted);font-size:.8rem;margin-bottom:24px}
h2{font-size:.9rem;color:var(--accent);text-transform:uppercase;letter-spacing:.08em;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:6px;padding:12px 20px;min-width:100px}
.stat .val{font-size:1.5rem;color:var(--green);font-weight:700}
.stat .lbl{font-size:.75rem;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th{text-align:left;color:var(--muted);font-weight:400;padding:4px 8px;border-bottom:1px solid var(--border)}
td{padding:5px 8px;border-bottom:1px solid var(--border)22;vertical-align:middle}
tr:hover td{background:#1e1e2a}
.num{text-align:right;color:var(--accent)}
.path{color:var(--text);font-size:.78rem;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.intent{color:var(--muted);font-size:.78rem;max-width:380px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{height:10px;background:var(--accent);border-radius:3px;opacity:.7;min-width:2px}
.generated{color:var(--muted);font-size:.72rem;margin-top:32px}
</style>
</head>
<body>
<h1>⚡ chthonic-archive — Corpus Report</h1>
<p class="sub">manifest/corpus.sqlite · generated ${new Date().toISOString().slice(0, 16).replace("T", " ")}</p>

<div class="stats">
  <div class="stat"><div class="val">${summary.sessions}</div><div class="lbl">sessions</div></div>
  <div class="stat"><div class="val">${summary.messages.toLocaleString()}</div><div class="lbl">messages</div></div>
  <div class="stat"><div class="val">${summary.toolCalls.toLocaleString()}</div><div class="lbl">tool calls</div></div>
  <div class="stat"><div class="val">${summary.fileEdits.toLocaleString()}</div><div class="lbl">file edits</div></div>
  <div class="stat"><div class="val">${summary.termCmds.toLocaleString()}</div><div class="lbl">terminal cmds</div></div>
  <div class="stat"><div class="val">${summary.commits.toLocaleString()}</div><div class="lbl">commit refs</div></div>
</div>

<h2>Sessions</h2>
<table>
<thead><tr><th>ID</th><th>Start</th><th>Turns</th><th>Edits</th><th>Cmds</th><th>Commits</th><th>Intent</th></tr></thead>
<tbody>${sessRows}</tbody>
</table>

<h2>Hot Files (top 25 by edit count)</h2>
<table>
<thead><tr><th>File</th><th style="width:50%">Activity</th><th>Edits</th><th>Sessions</th></tr></thead>
<tbody>${fileRows}</tbody>
</table>

<h2>Tool Frequency (top 20)</h2>
<table>
<thead><tr><th>Tool</th><th style="width:50%">Calls</th><th>Count</th><th>Success%</th></tr></thead>
<tbody>${toolRows}</tbody>
</table>

<p class="generated">bun run scripts/session-query.ts --report-html · corpus v3 · 18722fea</p>
</body>
</html>`;

  await Bun.write(outPath, html);
  console.log(`✓ Report written: ${outPath}`);
  console.log(`  ${sessions.length} sessions · ${hotFiles.length} hot files · ${toolFreq.length} tools`);

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

  --timeline              all sessions (start, turns, edits, commands, commits)
  --hot-files [N]         top N most edited files across all sessions  (default 20)
  --tool-frequency [N]    top N tools by call count with success %     (default 20)
  --memory-chain <file>   how one memory file evolved across sessions  + latest content
  --memory-search <term>  search across memory file content
  --search <term>         FTS5 search across messages + terminal commands
  --messages <id>         conversation messages for one session (partial id ok)
  --code-langs            language distribution of code blocks
  --sessions              list all sessions
  --session <id>          detailed view of one session (partial id ok)
  --report-html           generate manifest/corpus-report.html (self-contained, no deps)
  --sql "..."             raw SQL query against corpus.sqlite

Tables: sessions, session_restarts, file_edits, terminal_cmds,
        code_blocks, tool_calls, commit_refs, memory_snapshots, messages
FTS5:   fts_messages, fts_cmds
Views:  hot_files, memory_chain, session_timeline
`);
}

db.close();
