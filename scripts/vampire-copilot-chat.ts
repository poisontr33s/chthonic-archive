#!/usr/bin/env bun
// @SID: VAMPIRE_COPILOT_CHAT_V2_CORPUS_REBASE
// Promoted from session-vampire.ts (G7.0) — now corpus-native.
//
// The vampire no longer chews raw transcripts. She reads the corpus.
// session-corpus.ts INGESTS (transcript → DB). vampire-copilot-chat.ts DRAINS (DB → FS artifacts).
// Both are lossless projections of the same canonical data — proof via _corpus_ref frontmatter.
//
// Cross-reference law: sessionId is the shared frontmatter anchor.
//   corpus.sessions.sessionId === drain.json._corpus_ref.sessionId
//   Any consumer of drain.json can verify against corpus.sqlite without re-parsing transcripts.
//
// Usage:
//   bun run scripts/vampire-copilot-chat.ts                         # drain all sessions
//   bun run scripts/vampire-copilot-chat.ts --session <id>          # drain one session
//   bun run scripts/vampire-copilot-chat.ts --blood                 # cross-session blood index
//   bun run scripts/vampire-copilot-chat.ts --extract edits         # hottest files
//   bun run scripts/vampire-copilot-chat.ts --extract commands      # terminal commands
//   bun run scripts/vampire-copilot-chat.ts --extract code          # code blocks
//   bun run scripts/vampire-copilot-chat.ts --extract memories      # memory file inventory
//   bun run scripts/vampire-copilot-chat.ts --nightly               # last-24h digest (nightly escapade)
//   bun run scripts/vampire-copilot-chat.ts --stub-corpus           # in-memory DB (satellite isolation)

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { Database } from "bun:sqlite";

const args = process.argv.slice(2);
const bloodMode    = args.includes("--blood");
const nightlyMode  = args.includes("--nightly");
const stubCorpus   = args.includes("--stub-corpus");
const sessionArgIdx = args.indexOf("--session");
const targetSession = sessionArgIdx >= 0 ? args[sessionArgIdx + 1] : null;
const extractArgIdx = args.indexOf("--extract");
const extractMode   = extractArgIdx >= 0 ? args[extractArgIdx + 1] : null;
const verbose = args.includes("--verbose");

const repoRoot    = join(import.meta.dir, "..");
const manifestDir = join(repoRoot, "manifest");
const sessionsDir = join(manifestDir, "sessions");
const corpusPath  = join(manifestDir, "corpus.sqlite");
const bloodPath   = join(manifestDir, "session_blood.json");

// ─────────────────────────────────────────────────────────────
// Corpus open
// stub-corpus: in-memory shell with drain DDL only — for satellite isolation dev.
// The archive sleeps soundly, the stub stands in.
// ─────────────────────────────────────────────────────────────

function openCorpus(): Database {
  if (stubCorpus) {
    const db = new Database(":memory:");
    db.exec(`
      CREATE TABLE sessions (
        sessionId TEXT PRIMARY KEY, startTime TEXT, workspaceHash TEXT,
        workspaceName TEXT, copilotVersion TEXT, vscodeVersion TEXT,
        turns INTEGER DEFAULT 0, intent TEXT DEFAULT '', topic TEXT,
        tags TEXT, note TEXT, ingestedAt TEXT
      );
      CREATE TABLE file_edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, filePath TEXT,
        tool TEXT, turn INTEGER, ts INTEGER
      );
      CREATE TABLE terminal_cmds (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, command TEXT,
        goal TEXT, explanation TEXT, turn INTEGER, ts INTEGER
      );
      CREATE TABLE code_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, lang TEXT,
        lines INTEGER, preview TEXT, turn INTEGER, ts INTEGER
      );
      CREATE TABLE tool_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, toolName TEXT,
        callId TEXT, turn INTEGER, ts INTEGER, tsComplete INTEGER,
        argsJson TEXT, success INTEGER, resultSnippet TEXT, resultContent TEXT
      );
      CREATE TABLE commit_refs (sha TEXT, sessionId TEXT, turn INTEGER, PRIMARY KEY (sha, sessionId));
      CREATE TABLE memory_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, filename TEXT,
        content TEXT, capturedAt TEXT
      );
      CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sessionId TEXT, role TEXT,
        turn INTEGER, ts INTEGER, content TEXT, toolRequestCount INTEGER DEFAULT 0
      );
    `);
    console.warn("⚠️  --stub-corpus: in-memory DB — no real corpus data");
    return db;
  }
  if (!existsSync(corpusPath)) {
    console.error("corpus.sqlite not found. Run: bun run session:corpus");
    process.exit(1);
  }
  return new Database(corpusPath, { readonly: true });
}

// ─────────────────────────────────────────────────────────────
// Types — drain.json contract preserved; _corpus_ref block added
// ─────────────────────────────────────────────────────────────

interface CorpusRef {
  sessionId:      string;
  schema_version: number;
  corpus_path:    string;
  workspaceHash:  string | null;
  startTime:      string | null;
  drainedAt:      string;
}

interface FileEdit      { tool: string; filePath: string; turn: number; }
interface TerminalCommand { command: string; explanation?: string; goal?: string; turn: number; }
interface CodeBlock      { lang: string; lines: number; preview: string; turn: number; }

interface SessionDrain {
  _corpus_ref:       CorpusRef;   // frontmatter — shared anchor with corpus.sessions row
  sessionId:         string;
  drainedAt:         string;
  sourcePath:        string;      // transcript path (provenance only — not re-parsed)
  sessionIntent:     string;
  turns:             number;
  userMessages:      number;
  assistantMessages: number;
  fileEdits:         FileEdit[];
  terminalCommands:  TerminalCommand[];
  codeBlocks:        CodeBlock[];
  toolCallSummary:   Record<string, number>;
  commitRefs:        string[];
  memoryFiles:       string[];
}

interface BloodEntry {
  sessionId:       string;
  drainedAt:       string;
  sessionIntent:   string;
  turns:           number;
  fileEditCount:   number;
  commandCount:    number;
  codeBlockCount:  number;
  memoryFileCount: number;
  topFiles:        string[];
  topTools:        string[];
}

// ─────────────────────────────────────────────────────────────
// Drain one session — reads corpus.sqlite, NOT transcript.jsonl
// ─────────────────────────────────────────────────────────────

function drainSession(db: Database, sessionId: string): SessionDrain | null {
  const row = db.prepare(
    "SELECT sessionId, startTime, workspaceHash, intent, turns, ingestedAt FROM sessions WHERE sessionId = ?"
  ).get(sessionId) as Record<string, unknown> | null;
  if (!row) return null;

  const fileEdits = (db.prepare(
    "SELECT filePath, tool, turn FROM file_edits WHERE sessionId = ? ORDER BY turn, id"
  ).all(sessionId) as Array<{ filePath: string; tool: string; turn: number }>).map(r => ({
    filePath: r.filePath,
    tool:     r.tool ?? "unknown",
    turn:     r.turn ?? 0,
  }));

  const terminalCommands = (db.prepare(
    "SELECT command, goal, explanation, turn FROM terminal_cmds WHERE sessionId = ? ORDER BY turn, id"
  ).all(sessionId) as Array<{ command: string; goal: string | null; explanation: string | null; turn: number }>).map(r => ({
    command: r.command,
    ...(r.goal        ? { goal: r.goal }               : {}),
    ...(r.explanation ? { explanation: r.explanation } : {}),
    turn: r.turn ?? 0,
  }));

  const codeBlocks = (db.prepare(
    "SELECT lang, lines, preview, turn FROM code_blocks WHERE sessionId = ? ORDER BY turn, id"
  ).all(sessionId) as Array<{ lang: string | null; lines: number; preview: string | null; turn: number }>).map(r => ({
    lang:    r.lang    ?? "",
    lines:   r.lines   ?? 0,
    preview: r.preview ?? "",
    turn:    r.turn    ?? 0,
  }));

  const toolRows = db.prepare(
    "SELECT toolName, COUNT(*) AS c FROM tool_calls WHERE sessionId = ? GROUP BY toolName"
  ).all(sessionId) as Array<{ toolName: string; c: number }>;
  const toolCallSummary: Record<string, number> = {};
  for (const r of toolRows) toolCallSummary[r.toolName] = r.c;

  const commitRefs = (db.prepare(
    "SELECT sha FROM commit_refs WHERE sessionId = ?"
  ).all(sessionId) as Array<{ sha: string }>).map(r => r.sha);

  const memoryFiles = (db.prepare(
    "SELECT filename FROM memory_snapshots WHERE sessionId = ? ORDER BY filename"
  ).all(sessionId) as Array<{ filename: string }>).map(r => r.filename);

  const msgCounts = db.prepare(
    "SELECT role, COUNT(*) AS c FROM messages WHERE sessionId = ? GROUP BY role"
  ).all(sessionId) as Array<{ role: string; c: number }>;
  const roleMap: Record<string, number> = {};
  for (const r of msgCounts) roleMap[r.role] = r.c;

  const drainedAt  = new Date().toISOString();
  const sourcePath = join(sessionsDir, sessionId, "transcript.jsonl"); // provenance ref

  return {
    _corpus_ref: {
      sessionId,
      schema_version: 2,
      corpus_path:    "manifest/corpus.sqlite",
      workspaceHash:  (row.workspaceHash as string | null) ?? null,
      startTime:      (row.startTime     as string | null) ?? null,
      drainedAt,
    },
    sessionId,
    drainedAt,
    sourcePath,
    sessionIntent:    (row.intent as string) ?? "",
    turns:            (row.turns  as number) ?? 0,
    userMessages:     roleMap["user"]      ?? 0,
    assistantMessages:roleMap["assistant"] ?? 0,
    fileEdits,
    terminalCommands,
    codeBlocks,
    toolCallSummary,
    commitRefs,
    memoryFiles,
  };
}

// ─────────────────────────────────────────────────────────────
// All session IDs — ordered by startTime (ascending)
// ─────────────────────────────────────────────────────────────

function allSessionIds(db: Database): string[] {
  return (db.prepare(
    "SELECT sessionId FROM sessions ORDER BY startTime"
  ).all() as Array<{ sessionId: string }>).map(r => r.sessionId);
}

// ─────────────────────────────────────────────────────────────
// Drain all — writes drain.json per session
// ─────────────────────────────────────────────────────────────

function drainAll(db: Database, ids: string[]): SessionDrain[] {
  const results: SessionDrain[] = [];
  for (const id of ids) {
    const drain = drainSession(db, id);
    if (!drain) continue;
    const outDir = join(sessionsDir, id);
    if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
    writeFileSync(join(outDir, "drain.json"), JSON.stringify(drain, null, 2), "utf8");
    if (verbose) {
      console.log(`  🩸 ${id.slice(0, 8)}  turns=${drain.turns}  edits=${drain.fileEdits.length}  cmds=${drain.terminalCommands.length}  blocks=${drain.codeBlocks.length}`);
    }
    results.push(drain);
  }
  return results;
}

// ─────────────────────────────────────────────────────────────
// Blood index — cross-session summary (session_blood.json)
// Shape unchanged from session-vampire.ts contract
// ─────────────────────────────────────────────────────────────

function buildBlood(drains: SessionDrain[]) {
  const fname = (p: string) => p.replace(/\\/g, "/").split("/").pop() ?? p;
  const blood: BloodEntry[] = drains.map(d => {
    const fileCounts: Record<string, number> = {};
    for (const e of d.fileEdits) fileCounts[e.filePath] = (fileCounts[e.filePath] ?? 0) + 1;
    return {
      sessionId:       d.sessionId,
      drainedAt:       d.drainedAt,
      sessionIntent:   d.sessionIntent,
      turns:           d.turns,
      fileEditCount:   d.fileEdits.length,
      commandCount:    d.terminalCommands.length,
      codeBlockCount:  d.codeBlocks.length,
      memoryFileCount: d.memoryFiles.length,
      topFiles: Object.entries(fileCounts).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([p]) => p),
      topTools: Object.entries(d.toolCallSummary).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([t]) => t),
    };
  });
  writeFileSync(bloodPath, JSON.stringify(blood, null, 2), "utf8");
  return blood;
}

// ─────────────────────────────────────────────────────────────
// --blood report
// ─────────────────────────────────────────────────────────────

function showBlood() {
  if (!existsSync(bloodPath)) {
    console.error("No blood yet. Run: bun run vampire:drain");
    process.exit(1);
  }
  const blood = JSON.parse(readFileSync(bloodPath, "utf8")) as BloodEntry[];
  const totals = blood.reduce((acc, b) => ({
    edits: acc.edits + b.fileEditCount,
    cmds:  acc.cmds  + b.commandCount,
  }), { edits: 0, cmds: 0 });
  const totalMem = blood.reduce((acc, b) => acc + (b.memoryFileCount ?? 0), 0);
  console.log(`\n🩸 SESSION BLOOD — ${blood.length} sessions · ${totals.edits} total edits · ${totals.cmds} terminal commands · ${totalMem} memory files\n`);
  for (const b of [...blood].sort((a, z) => z.turns - a.turns)) {
    const sid   = b.sessionId.slice(0, 8);
    const files = b.topFiles.slice(0, 3).map(p => p.replace(/\\/g, "/").split("/").pop() ?? p).join(", ");
    console.log(`  ${sid}  turns=${String(b.turns).padStart(4)}  edits=${String(b.fileEditCount).padStart(3)}  cmds=${String(b.commandCount).padStart(3)}`);
    if (b.sessionIntent) console.log(`           ${b.sessionIntent.slice(0, 100)}`);
    if (files)            console.log(`           → ${files}`);
    if ((b.memoryFileCount ?? 0) > 0) console.log(`           💾 ${b.memoryFileCount} memory file(s)`);
  }
  console.log();
}

// ─────────────────────────────────────────────────────────────
// --nightly: last-24h digest
// The nightly escapade window — catches what ran while you slept.
// ─────────────────────────────────────────────────────────────

function runNightly(db: Database) {
  const cutoff    = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const recent    = (db.prepare(
    "SELECT sessionId FROM sessions WHERE startTime > ? ORDER BY startTime"
  ).all(cutoff) as Array<{ sessionId: string }>).map(r => r.sessionId);

  if (!recent.length) {
    console.log("🌙  Nightly: no sessions in the last 24h — the archive sleeps soundly.");
    return;
  }

  const drains   = recent.map(id => drainSession(db, id)).filter((d): d is SessionDrain => d !== null);
  const allFiles = drains.flatMap(d => d.fileEdits.map(e => e.filePath));
  const fileCounts: Record<string, number> = {};
  for (const f of allFiles) fileCounts[f] = (fileCounts[f] ?? 0) + 1;
  const hotFiles = Object.entries(fileCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);

  const dateStamp  = new Date().toISOString().slice(0, 10);
  const nightlyOut = join(manifestDir, `vampire_nightly_${dateStamp}.json`);

  const report = {
    _corpus_ref:     { schema_version: 2, corpus_path: "manifest/corpus.sqlite" },
    window:          { from: cutoff, to: new Date().toISOString(), hours: 24 },
    sessions:        recent.length,
    edits:           drains.reduce((n, d) => n + d.fileEdits.length, 0),
    commands:        drains.reduce((n, d) => n + d.terminalCommands.length, 0),
    codeBlocks:      drains.reduce((n, d) => n + d.codeBlocks.length, 0),
    hotFiles,
    sessionSummaries: drains.map(d => ({
      sessionId: d.sessionId,
      intent:    d.sessionIntent,
      turns:     d.turns,
      edits:     d.fileEdits.length,
      commands:  d.terminalCommands.length,
    })),
  };

  writeFileSync(nightlyOut, JSON.stringify(report, null, 2), "utf8");

  console.log(`\n🌙  NIGHTLY DIGEST — ${dateStamp}`);
  console.log(`   Sessions : ${report.sessions}`);
  console.log(`   Edits    : ${report.edits}`);
  console.log(`   Commands : ${report.commands}`);
  console.log(`   Code blk : ${report.codeBlocks}`);
  if (hotFiles.length) {
    console.log(`   Hot files:`);
    for (const [fp, n] of hotFiles.slice(0, 5)) {
      const fname = fp.replace(/\\/g, "/").split("/").pop() ?? fp;
      console.log(`     ${String(n).padStart(3)}×  ${fname}`);
    }
  }
  console.log(`\n   → ${nightlyOut}\n`);
}

// ─────────────────────────────────────────────────────────────
// --extract modes — all queries hit corpus.sqlite
// ─────────────────────────────────────────────────────────────

function showExtract(db: Database, mode: string) {
  const ids = targetSession ? [targetSession] : allSessionIds(db);

  if (mode === "edits") {
    const rows = (targetSession
      ? db.prepare("SELECT filePath, COUNT(*) AS c FROM file_edits WHERE sessionId = ? GROUP BY filePath ORDER BY c DESC").all(targetSession)
      : db.prepare("SELECT filePath, COUNT(*) AS c FROM file_edits GROUP BY filePath ORDER BY c DESC").all()
    ) as Array<{ filePath: string; c: number }>;
    const total = rows.reduce((n, r) => n + r.c, 0);
    console.log(`\n✏️  FILE EDITS — ${total} total across ${ids.length} session(s)\n`);
    for (const r of rows) console.log(`  ${String(r.c).padStart(3)}×  ${r.filePath}`);
    console.log();

  } else if (mode === "commands") {
    console.log(`\n$ TERMINAL COMMANDS\n`);
    for (const id of ids) {
      const cmds = db.prepare(
        "SELECT command, goal, turn FROM terminal_cmds WHERE sessionId = ? ORDER BY turn, id"
      ).all(id) as Array<{ command: string; goal: string | null; turn: number }>;
      if (!cmds.length) continue;
      console.log(`  ── ${id.slice(0, 8)} ──`);
      for (const c of cmds) console.log(`    ${c.command.slice(0, 120)}${c.goal ? ` [${c.goal}]` : ""}`);
    }
    console.log();

  } else if (mode === "code") {
    const rows = (targetSession
      ? db.prepare("SELECT lang, lines, preview FROM code_blocks WHERE sessionId = ? ORDER BY turn, id").all(targetSession)
      : db.prepare("SELECT lang, lines, preview FROM code_blocks ORDER BY sessionId, turn, id").all()
    ) as Array<{ lang: string | null; lines: number; preview: string | null }>;
    for (const r of rows) {
      const label = (r.lang ? `[${r.lang}]` : "[?]").padEnd(14);
      console.log(`${label} ${String(r.lines).padStart(3)}L  ${(r.preview ?? "").slice(0, 60)}`);
    }
    console.log(`\n${rows.length} code blocks total`);

  } else if (mode === "memories") {
    console.log(`\n💾 MEMORY FILES\n`);
    const rows = (targetSession
      ? db.prepare("SELECT sessionId, filename, LENGTH(content) AS sz FROM memory_snapshots WHERE sessionId = ? ORDER BY filename").all(targetSession)
      : db.prepare("SELECT sessionId, filename, LENGTH(content) AS sz FROM memory_snapshots ORDER BY sessionId, filename").all()
    ) as Array<{ sessionId: string; filename: string; sz: number }>;
    let lastSid = "";
    for (const r of rows) {
      if (r.sessionId !== lastSid) { console.log(`  ── ${r.sessionId.slice(0, 8)} ──`); lastSid = r.sessionId; }
      console.log(`    ${r.filename.padEnd(40)} ${String(r.sz ?? 0).padStart(7)}B`);
    }
    console.log(`\n${rows.length} memory file(s) total`);

  } else {
    console.error(`Unknown extract mode: ${mode}. Use: edits | commands | code | memories`);
    process.exit(1);
  }
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

const db = openCorpus();

if (nightlyMode) {
  runNightly(db);
} else if (bloodMode) {
  showBlood();
} else if (extractMode) {
  showExtract(db, extractMode);
} else {
  const ids = targetSession ? [targetSession] : allSessionIds(db);
  if (!verbose) process.stdout.write(`vampire-copilot-chat: draining ${ids.length} session(s) from corpus...`);
  const drains = drainAll(db, ids);
  buildBlood(drains);
  if (!verbose) console.log(` done. ${drains.length} drained → manifest/session_blood.json`);
}

db.close();
