#!/usr/bin/env bun
// @SID: session-corpus — build manifest/corpus.sqlite from all mirrored session artifacts
// Sources: manifest/sessions/*/  (meta.json + transcript.jsonl + debug.jsonl + memories/*.md)
// Output:  manifest/corpus.sqlite  (Bun built-in SQLite, zero external deps)
//
// Ingest order per session:
//   meta.json        → sessions row (id, startTime, workspaceHash, versions)
//   transcript.jsonl → file_edits, terminal_cmds, code_blocks, tool_calls, commit_refs
//   debug.jsonl      → session_restarts (one row per VS Code restart within session)
//   memories/*.md    → memory_snapshots (FULL CONTENT — enables SQL search across agent state)
//
// Usage:
//   bun run scripts/session-corpus.ts                    # incremental (skip up-to-date)
//   bun run scripts/session-corpus.ts --rebuild          # drop all tables + full rebuild
//   bun run scripts/session-corpus.ts --session <id>     # re-ingest one session
//   bun run scripts/session-corpus.ts --stats            # row counts per table
//   bun run scripts/session-corpus.ts --watch            # hot-reload: re-ingest on transcript change

import { Database } from "bun:sqlite";
import { existsSync, readdirSync, readFileSync, statSync, watch } from "fs";
import { join } from "path";

const args = process.argv.slice(2);
const rebuildMode   = args.includes("--rebuild");
const statsMode     = args.includes("--stats");
const watchMode     = args.includes("--watch");
const classifyMode  = args.includes("--classify");
const sessionArgIdx = args.indexOf("--session");
const targetSession = sessionArgIdx >= 0 ? args[sessionArgIdx + 1] : null;

const manifestDir = join(import.meta.dir, "..", "manifest");
const sessionsDir = join(manifestDir, "sessions");
const corpusPath  = join(manifestDir, "corpus.sqlite");

// ─────────────────────────────────────────────────────────────
// DDL
// ─────────────────────────────────────────────────────────────

const DDL_TABLES = `
CREATE TABLE IF NOT EXISTS sessions (
  sessionId      TEXT PRIMARY KEY,
  startTime      TEXT,
  workspaceHash  TEXT,
  workspaceName  TEXT,
  copilotVersion TEXT,
  vscodeVersion  TEXT,
  turns          INTEGER DEFAULT 0,
  intent         TEXT    DEFAULT '',
  topic          TEXT    DEFAULT NULL,
  tags           TEXT    DEFAULT NULL,
  ingestedAt     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS session_restarts (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId      TEXT NOT NULL REFERENCES sessions(sessionId),
  ts             INTEGER,
  copilotVersion TEXT,
  vscodeVersion  TEXT
);

CREATE TABLE IF NOT EXISTS file_edits (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId TEXT NOT NULL REFERENCES sessions(sessionId),
  filePath  TEXT NOT NULL,
  tool      TEXT,
  turn      INTEGER,
  ts        INTEGER
);

CREATE TABLE IF NOT EXISTS terminal_cmds (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId   TEXT NOT NULL REFERENCES sessions(sessionId),
  command     TEXT NOT NULL,
  goal        TEXT,
  explanation TEXT,
  turn        INTEGER,
  ts          INTEGER
);

CREATE TABLE IF NOT EXISTS code_blocks (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId TEXT NOT NULL REFERENCES sessions(sessionId),
  lang      TEXT,
  lines     INTEGER,
  preview   TEXT,
  turn      INTEGER,
  ts        INTEGER
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId     TEXT NOT NULL REFERENCES sessions(sessionId),
  toolName      TEXT NOT NULL,
  callId        TEXT,
  turn          INTEGER,
  ts            INTEGER,
  tsComplete    INTEGER,
  argsJson      TEXT,
  success       INTEGER,  -- 1=success  0=failure  NULL=no completion record
  resultSnippet TEXT
);

CREATE TABLE IF NOT EXISTS commit_refs (
  sha       TEXT NOT NULL,
  sessionId TEXT NOT NULL REFERENCES sessions(sessionId),
  turn      INTEGER,
  PRIMARY KEY (sha, sessionId)
);

CREATE TABLE IF NOT EXISTS memory_snapshots (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId  TEXT NOT NULL REFERENCES sessions(sessionId),
  filename   TEXT NOT NULL,
  content    TEXT,
  capturedAt TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  sessionId        TEXT NOT NULL REFERENCES sessions(sessionId),
  role             TEXT NOT NULL,
  turn             INTEGER,
  ts               INTEGER,
  content          TEXT,
  toolRequestCount INTEGER DEFAULT 0
);
`;

const DDL_INDEXES = `
CREATE INDEX IF NOT EXISTS idx_fe_path     ON file_edits(filePath);
CREATE INDEX IF NOT EXISTS idx_fe_session  ON file_edits(sessionId);
CREATE INDEX IF NOT EXISTS idx_tc_session  ON terminal_cmds(sessionId);
CREATE INDEX IF NOT EXISTS idx_tl_name     ON tool_calls(toolName);
CREATE INDEX IF NOT EXISTS idx_tl_session  ON tool_calls(sessionId);
CREATE INDEX IF NOT EXISTS idx_ms_file     ON memory_snapshots(filename);
CREATE INDEX IF NOT EXISTS idx_ms_session  ON memory_snapshots(sessionId);
CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(sessionId);
CREATE INDEX IF NOT EXISTS idx_msg_role    ON messages(sessionId, role);
`;

const DDL_VIEWS = `
CREATE VIEW IF NOT EXISTS hot_files AS
  SELECT filePath,
         COUNT(*)                  AS editCount,
         COUNT(DISTINCT sessionId) AS sessionCount
  FROM file_edits
  GROUP BY filePath
  ORDER BY editCount DESC;

CREATE VIEW IF NOT EXISTS memory_chain AS
  SELECT ms.filename, ms.sessionId, s.startTime, ms.capturedAt,
         LENGTH(ms.content) AS contentBytes,
         ms.content
  FROM memory_snapshots ms
  JOIN sessions s ON ms.sessionId = s.sessionId
  ORDER BY ms.filename, s.startTime;

CREATE VIEW IF NOT EXISTS session_timeline AS
  SELECT
    s.sessionId, s.startTime, s.intent, s.turns,
    s.copilotVersion, s.workspaceHash, s.workspaceName,
    s.topic, s.tags,
    (SELECT COUNT(*) FROM file_edits       WHERE sessionId = s.sessionId) AS editCount,
    (SELECT COUNT(*) FROM terminal_cmds    WHERE sessionId = s.sessionId) AS cmdCount,
    (SELECT COUNT(*) FROM code_blocks      WHERE sessionId = s.sessionId) AS codeBlockCount,
    (SELECT COUNT(*) FROM memory_snapshots WHERE sessionId = s.sessionId) AS memoryFileCount,
    (SELECT COUNT(*) FROM commit_refs      WHERE sessionId = s.sessionId) AS commitCount,
    (SELECT COUNT(*) FROM messages WHERE sessionId = s.sessionId AND role = 'user')      AS userTurns,
    (SELECT COUNT(*) FROM messages WHERE sessionId = s.sessionId AND role = 'assistant') AS assistantTurns
  FROM sessions s
  ORDER BY s.startTime DESC;
`;

const DDL_FTS5 = `
CREATE VIRTUAL TABLE IF NOT EXISTS fts_messages USING fts5(
  sessionId UNINDEXED,
  role      UNINDEXED,
  turn      UNINDEXED,
  content
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_cmds USING fts5(
  sessionId UNINDEXED,
  command,
  goal
);
`;

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

function tryAlter(db: Database, sql: string) {
  try { db.exec(sql); } catch { /* column already exists */ }
}

function asObj(v: unknown): Record<string, unknown> {
  if (!v) return {};
  if (typeof v === "string") {
    try { return JSON.parse(v) as Record<string, unknown>; } catch { return {}; }
  }
  if (typeof v === "object" && !Array.isArray(v)) return v as Record<string, unknown>;
  return {};
}

function extractCodeBlocks(content: string, turn: number) {
  const blocks: Array<{ lang: string; lines: number; preview: string; turn: number }> = [];
  const re = /```([^\n`]*)\n([\s\S]*?)```/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) {
    const body = m[2] ?? "";
    if (body.trim().length < 3) continue;
    blocks.push({
      lang: m[1]?.trim() ?? "",
      lines: body.split("\n").length,
      preview: body.slice(0, 80).replace(/\n/g, "↵"),
      turn,
    });
  }
  return blocks;
}

function extractCommits(content: string): string[] {
  const re = /\b([0-9a-f]{7,12})\b/g;
  const found: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) found.push(m[1]);
  return [...new Set(found)];
}

// ─────────────────────────────────────────────────────────────
// Session ingestion
// ─────────────────────────────────────────────────────────────

function ingestSession(db: Database, sessionId: string): boolean {
  const sessionDir = join(sessionsDir, sessionId);
  const metaPath   = join(sessionDir, "meta.json");
  const tPath      = join(sessionDir, "transcript.jsonl");
  if (!existsSync(tPath)) return false;

  let meta: Record<string, unknown> = {};
  try { meta = JSON.parse(readFileSync(metaPath, "utf8")); } catch { /* ok */ }

  const now = new Date().toISOString();

  // Clean-slate re-ingest: delete all existing rows for this session
  db.prepare("DELETE FROM messages          WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM memory_snapshots  WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM commit_refs       WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM tool_calls        WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM code_blocks       WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM terminal_cmds     WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM file_edits        WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM session_restarts  WHERE sessionId = ?").run(sessionId);
  db.prepare("DELETE FROM sessions          WHERE sessionId = ?").run(sessionId);
  // FTS5 cleanup (graceful — tables may not exist on schema migration)
  try { db.prepare("DELETE FROM fts_messages WHERE sessionId = ?").run(sessionId); } catch { /* ok */ }
  try { db.prepare("DELETE FROM fts_cmds     WHERE sessionId = ?").run(sessionId); } catch { /* ok */ }

  // Insert sessions row (turns + intent updated after transcript pass)
  db.prepare(`
    INSERT INTO sessions (sessionId, startTime, workspaceHash, workspaceName, copilotVersion, vscodeVersion, turns, intent, ingestedAt)
    VALUES (?, ?, ?, ?, ?, ?, 0, '', ?)
  `).run(
    sessionId,
    String(meta.startTime      ?? ""),
    String(meta.workspaceHash  ?? ""),
    String(meta.workspaceName  ?? ""),
    String(meta.copilotVersion ?? ""),
    String(meta.vscodeVersion  ?? ""),
    now,
  );

  // ── Transcript pass ──
  let raw = "";
  try { raw = readFileSync(tPath, "utf8"); } catch { return false; }

  const insFileEdit  = db.prepare("INSERT INTO file_edits  (sessionId, filePath, tool, turn, ts) VALUES (?, ?, ?, ?, ?)");
  const insTermCmd   = db.prepare("INSERT INTO terminal_cmds (sessionId, command, goal, explanation, turn, ts) VALUES (?, ?, ?, ?, ?, ?)");
  const insCodeBlock = db.prepare("INSERT INTO code_blocks (sessionId, lang, lines, preview, turn, ts) VALUES (?, ?, ?, ?, ?, ?)");
  const insToolCall  = db.prepare("INSERT INTO tool_calls (sessionId, toolName, callId, turn, ts, argsJson, success) VALUES (?, ?, ?, ?, ?, ?, NULL) RETURNING id");
  const updComplete  = db.prepare("UPDATE tool_calls SET success = ?, tsComplete = ? WHERE id = ?");
  const insCommit    = db.prepare("INSERT OR IGNORE INTO commit_refs (sha, sessionId, turn) VALUES (?, ?, ?)");
  const insMessage   = db.prepare("INSERT INTO messages (sessionId, role, turn, ts, content, toolRequestCount) VALUES (?, ?, ?, ?, ?, ?)");
  const insFtsMsg    = db.prepare("INSERT INTO fts_messages (sessionId, role, turn, content) VALUES (?, ?, ?, ?)");
  const insFtsCmd    = db.prepare("INSERT INTO fts_cmds (sessionId, command, goal) VALUES (?, ?, ?)");

  // callId correlation: toolRequests from assistant.message → dequeue on execution_start
  const pendingCallIds = new Map<string, string[]>(); // toolName → ordered queue of callIds
  const callIdToRowId  = new Map<string, number>();   // callId   → tool_calls.id

  let userMessages    = 0;
  let assistantMessages = 0;
  let turnIdx = 0;
  let intent  = "";

  const ingest = db.transaction(() => {
    for (const line of raw.split("\n")) {
      if (!line.trim()) continue;
      let entry: { type: string; ts?: number; timestamp?: string; data: Record<string, unknown> };
      try { entry = JSON.parse(line); } catch { continue; }
      const { type, data } = entry;
      // transcript uses ISO "timestamp", not numeric "ts"
      const tsRaw = entry.ts ?? entry.timestamp;
      const ts: number | null = typeof tsRaw === "number" ? tsRaw
        : typeof tsRaw === "string" && tsRaw ? new Date(tsRaw).getTime() : null;

      if (type === "user.message") {
        userMessages++;
        turnIdx++;
        const content = String(data?.content ?? data?.text ?? "");
        if (!intent && content.trim()) intent = content.slice(0, 200).replace(/\s+/g, " ").trim();
        insMessage.run(sessionId, "user", turnIdx, ts, content, 0);
        try { insFtsMsg.run(sessionId, "user", turnIdx, content); } catch { /* FTS not ready */ }

      } else if (type === "assistant.message") {
        assistantMessages++;
        turnIdx++;
        const content = String(data?.content ?? data?.text ?? "");
        const toolRequests = data?.toolRequests as Array<{ name?: string; toolCallId?: string }> | undefined;
        const toolReqCount = Array.isArray(toolRequests) ? toolRequests.length : 0;
        if (content) {
          for (const cb of extractCodeBlocks(content, turnIdx))
            insCodeBlock.run(sessionId, cb.lang, cb.lines, cb.preview, cb.turn, ts);
          for (const sha of extractCommits(content))
            insCommit.run(sha, sessionId, turnIdx);
        }
        insMessage.run(sessionId, "assistant", turnIdx, ts, content, toolReqCount);
        try { insFtsMsg.run(sessionId, "assistant", turnIdx, content); } catch { /* FTS not ready */ }
        // Collect callIds from toolRequests for execution matching
        if (Array.isArray(toolRequests)) {
          for (const req of toolRequests) {
            const name = String(req.name ?? "");
            const cid  = String(req.toolCallId ?? "");
            if (name && cid) {
              const q = pendingCallIds.get(name) ?? [];
              q.push(cid);
              pendingCallIds.set(name, q);
            }
          }
        }

      } else if (type === "tool.execution_start") {
        const toolName = String(data?.toolName ?? data?.name ?? "");
        if (!toolName) continue;
        const toolArgs = asObj(data?.arguments);
        const argsJson = JSON.stringify(toolArgs).slice(0, 1024);

        // Prefer direct callId from execution_start event; fall back to FIFO queue
        const directCallId = String(data?.toolCallId ?? "");
        const q      = pendingCallIds.get(toolName);
        const callId = directCallId || (q?.length ? q.shift()! : null);
        // Keep FIFO queue in sync when direct callId was used
        if (directCallId && q?.length && q[0] === directCallId) q.shift();

        const row = insToolCall.get(sessionId, toolName, callId ?? null, turnIdx, ts, argsJson) as { id: number } | undefined;
        if (row && callId) callIdToRowId.set(callId, row.id);

        // file_edits
        if (toolName === "replace_string_in_file" || toolName === "create_file") {
          const fp = String(toolArgs.filePath ?? toolArgs.path ?? "");
          if (fp) insFileEdit.run(sessionId, fp, toolName, turnIdx, ts);
        } else if (toolName === "multi_replace_string_in_file") {
          const reps = toolArgs.replacements as Array<{ filePath?: string }> | undefined;
          const seen = new Set<string>();
          if (Array.isArray(reps)) {
            for (const r of reps) {
              const fp = String(r.filePath ?? "");
              if (fp && !seen.has(fp)) { seen.add(fp); insFileEdit.run(sessionId, fp, toolName, turnIdx, ts); }
            }
          }
        }

        // terminal_cmds
        if (toolName === "run_in_terminal" || toolName === "execute_command") {
          const cmd = String(toolArgs.command ?? toolArgs.cmd ?? "");
          if (cmd) {
            insTermCmd.run(
              sessionId,
              cmd.slice(0, 300),
              toolArgs.goal        ? String(toolArgs.goal)        : null,
              toolArgs.explanation ? String(toolArgs.explanation) : null,
              turnIdx,
              ts,
            );
            try { insFtsCmd.run(sessionId, cmd.slice(0, 300), toolArgs.goal ? String(toolArgs.goal) : null); } catch { /* FTS not ready */ }
          }
        }

      } else if (type === "tool.execution_complete") {
        const callId  = String(data?.toolCallId ?? "");
        const success = data?.success === true ? 1 : data?.success === false ? 0 : null;
        const rowId   = callId ? callIdToRowId.get(callId) : undefined;
        if (rowId !== undefined) updComplete.run(success ?? null, ts, rowId);
      }
    }
  });
  ingest();

  // Update sessions row with final turn count + intent
  db.prepare("UPDATE sessions SET turns = ?, intent = ? WHERE sessionId = ?").run(
    userMessages + assistantMessages,
    intent,
    sessionId,
  );

  // ── Debug log pass ──
  const debugPath = join(sessionDir, "debug.jsonl");
  if (existsSync(debugPath)) {
    let dbgRaw = "";
    try { dbgRaw = readFileSync(debugPath, "utf8"); } catch { /* ok */ }
    const insRestart = db.prepare(
      "INSERT INTO session_restarts (sessionId, ts, copilotVersion, vscodeVersion) VALUES (?, ?, ?, ?)"
    );
    db.transaction(() => {
      for (const line of dbgRaw.split("\n")) {
        if (!line.trim()) continue;
        let e: Record<string, unknown>;
        try { e = JSON.parse(line); } catch { continue; }
        if (e.type === "session_start") {
          const attrs = asObj(e.attrs);
          insRestart.run(
            sessionId,
            typeof e.ts === "number" ? e.ts : null,
            attrs.copilotVersion ?? null,
            attrs.vscodeVersion  ?? null,
          );
        }
      }
    })();
  }

  // ── Result snippet backfill ──
  // For each tool call, grab the first assistant message in the same or later turn
  // as a proxy for "what did the tool accomplish" (ephemeral result content is not persisted).
  db.exec(`
    UPDATE tool_calls
    SET resultSnippet = (
      SELECT SUBSTR(m.content, 1, 400)
      FROM messages m
      WHERE m.sessionId = tool_calls.sessionId
        AND m.role = 'assistant'
        AND m.turn >= tool_calls.turn
        AND m.content != ''
      ORDER BY m.turn ASC
      LIMIT 1
    )
    WHERE sessionId = '${sessionId}'
      AND resultSnippet IS NULL
  `);

  // ── Memory snapshots pass ──
  const memoriesDir = join(sessionDir, "memories");
  if (existsSync(memoriesDir)) {
    const insMemory  = db.prepare(
      "INSERT INTO memory_snapshots (sessionId, filename, content, capturedAt) VALUES (?, ?, ?, ?)"
    );
    const capturedAt = new Date().toISOString();
    db.transaction(() => {
      for (const f of readdirSync(memoriesDir)) {
        if (!f.endsWith(".md") && !f.endsWith(".json")) continue;
        let content = "";
        try { content = readFileSync(join(memoriesDir, f), "utf8"); } catch { continue; }
        insMemory.run(sessionId, f, content, capturedAt);
      }
    })();
  }

  return true;
}

// ─────────────────────────────────────────────────────────────
// Session classification
// ─────────────────────────────────────────────────────────────

interface TopicSignature {
  topic: string;
  fileRe:   RegExp[];
  cmdRe:    RegExp[];
  intentRe: RegExp[];
}

const TOPIC_SIGS: TopicSignature[] = [
  {
    topic:    "vulkan",
    fileRe:   [/vulkan-lab/i, /\.comp\.glsl$/i, /\.spv$/i, /vulkan/i],
    cmdRe:    [/glslc/i, /\bash\b/i, /vulkan/i],
    intentRe: [/vulkan/i, /shader/i, /compute.*pipeline/i, /framebuffer/i],
  },
  {
    topic:    "tabby-inference",
    fileRe:   [/tabby/i, /probes[\\/]python/i, /flash.attn/i, /exllama/i, /tabby.modern/i],
    cmdRe:    [/tabby/i, /flash.attn/i, /exllama/i, /probes/i, /uv run probes/i],
    intentRe: [/tabby/i, /gpu inference/i, /flash.attn/i, /exllama/i, /inference/i],
  },
  {
    topic:    "corpus-builder",
    fileRe:   [/session-corpus/i, /corpus-mcp/i, /session-query/i, /session-watcher/i],
    cmdRe:    [/session.corpus/i, /corpus/i, /session.query/i],
    intentRe: [/corpus/i, /sqlite/i, /session.*mirror/i, /mcp.*server/i],
  },
  {
    topic:    "mas-mcp",
    fileRe:   [/mas_mcp[\\/]/i, /mas.mcp/i],
    cmdRe:    [/mas.mcp/i, /mas_mcp/i, /fastmcp/i],
    intentRe: [/mas.mcp/i, /mas_mcp/i, /mas pulse/i],
  },
  {
    topic:    "extension",
    fileRe:   [/chthonic.vscode.extension[\\/]/i, /extensions[\\/]chthonic/i, /activateCockpit/i],
    cmdRe:    [/vsce/i, /extension.*build/i],
    intentRe: [/vscode.*extension/i, /extension.*cockpit/i, /webview/i],
  },
  {
    topic:    "theme-system",
    fileRe:   [/chthonic.golden[\\/]/i, /theme_contrast/i, /icon_scaffold/i, /SFS_SLABSTONE/i, /\.tmTheme/i],
    cmdRe:    [/theme.*contrast/i, /icon.*scaffold/i, /sfs.*slabstone/i],
    intentRe: [/theme/i, /icon.*font/i, /color.*palette/i, /contrast.*ratio/i],
  },
  {
    topic:    "ssot-governance",
    fileRe:   [/copilot-instructions\.archive/i, /\.github[\\/]instructions/i, /SSOT/i],
    cmdRe:    [/ssot/i, /copilot.instructions/i],
    intentRe: [/ssot/i, /§\d+/i, /entity.*profile/i, /governance/i, /triumvirate/i],
  },
  {
    topic:    "ruby-zjit",
    fileRe:   [/ruby.zjit/i, /patch-jit/i, /ruby[\\/]build/i],
    cmdRe:    [/\brv\b/i, /zjit/i, /yjit/i, /ruby.*build/i, /ridk/i],
    intentRe: [/zjit/i, /yjit/i, /ruby.*port/i, /ruby.*build/i],
  },
  {
    topic:    "game",
    fileRe:   [/[\\/]game[\\/]/i, /dungeon/i, /crpg/i, /iron.maiden/i],
    cmdRe:    [/game/i],
    intentRe: [/dungeon/i, /crpg/i, /game.*world/i, /iron.*maiden/i],
  },
  {
    topic:    "ci-gates",
    fileRe:   [/ci[\\/]checks/i, /probes[\\/]/i, /gate.smoke/i],
    cmdRe:    [/ci[\\/]checks/i, /gate.smoke/i, /probe/i],
    intentRe: [/gate/i, /ci.*check/i, /probe/i, /inference.*gate/i],
  },
];

function classifySession(
  files: string[],
  cmds:  string[],
  intent: string,
): { topic: string | null; tags: string } {
  const scores: Record<string, number> = {};
  for (const sig of TOPIC_SIGS) {
    let score = 0;
    for (const re of sig.fileRe)   if (files.some(f => re.test(f)))  score += 2;
    for (const re of sig.cmdRe)    if (cmds.some(c => re.test(c)))   score += 1;
    for (const re of sig.intentRe) if (re.test(intent))              score += 1;
    if (score > 0) scores[sig.topic] = score;
  }
  const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const topic   = entries[0]?.[0] ?? null;
  const tags    = JSON.stringify(entries.map(e => e[0]));
  return { topic, tags };
}

function classifyAll(db: Database): void {
  const sessions = db.prepare("SELECT sessionId, intent FROM sessions").all() as Array<{ sessionId: string; intent: string }>;
  const updSession = db.prepare("UPDATE sessions SET topic = ?, tags = ? WHERE sessionId = ?");
  let classified = 0;
  db.transaction(() => {
    for (const s of sessions) {
      const files = (db.prepare("SELECT DISTINCT filePath FROM file_edits WHERE sessionId = ?").all(s.sessionId) as Array<{ filePath: string }>).map(r => r.filePath);
      const cmds  = (db.prepare("SELECT command FROM terminal_cmds WHERE sessionId = ?").all(s.sessionId) as Array<{ command: string }>).map(r => r.command);
      const { topic, tags } = classifySession(files, cmds, s.intent ?? "");
      updSession.run(topic, tags, s.sessionId);
      classified++;
      process.stdout.write(`  🏷  ${s.sessionId.slice(0, 8)}  topic=${topic ?? "—"}  tags=${tags}\n`);
    }
  })();
  console.log(`\n✅ Classified ${classified} session(s)`);
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

if (!existsSync(sessionsDir)) {
  console.error("No manifest/sessions/ found. Run: bun run session:watch --once");
  process.exit(1);
}

const db = new Database(corpusPath, { create: true });
db.exec("PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA foreign_keys = ON;");

if (rebuildMode) {
  console.log("⚡ Rebuild: dropping all tables and views...");
  for (const v of ["session_timeline", "memory_chain", "hot_files"])
    db.exec(`DROP VIEW IF EXISTS ${v}`);
  for (const t of ["fts_messages", "fts_cmds", "messages", "memory_snapshots", "commit_refs", "tool_calls", "code_blocks", "terminal_cmds", "file_edits", "session_restarts", "sessions"])
    db.exec(`DROP TABLE IF EXISTS ${t}`);
}

// Column migration for incremental upgrades (no-op if columns already exist)
if (!rebuildMode) {
  tryAlter(db, "ALTER TABLE tool_calls    ADD COLUMN ts             INTEGER");
  tryAlter(db, "ALTER TABLE tool_calls    ADD COLUMN tsComplete     INTEGER");
  tryAlter(db, "ALTER TABLE tool_calls    ADD COLUMN argsJson       TEXT");
  tryAlter(db, "ALTER TABLE tool_calls    ADD COLUMN resultSnippet  TEXT");
  tryAlter(db, "ALTER TABLE file_edits    ADD COLUMN ts          INTEGER");
  tryAlter(db, "ALTER TABLE terminal_cmds ADD COLUMN ts          INTEGER");
  tryAlter(db, "ALTER TABLE code_blocks   ADD COLUMN ts          INTEGER");
  tryAlter(db, "ALTER TABLE sessions      ADD COLUMN topic         TEXT");
  tryAlter(db, "ALTER TABLE sessions      ADD COLUMN tags          TEXT");
  tryAlter(db, "ALTER TABLE sessions      ADD COLUMN workspaceName TEXT");
  tryAlter(db, "ALTER TABLE sessions      ADD COLUMN note          TEXT");
}

db.exec(DDL_TABLES);
db.exec(DDL_INDEXES);
// Always drop+recreate views (safe — views carry no data)
for (const v of ["session_timeline", "memory_chain", "hot_files"])
  db.exec(`DROP VIEW IF EXISTS ${v}`);
db.exec(DDL_VIEWS);
// FTS5 (graceful — created once, only dropped on --rebuild)
try { db.exec(DDL_FTS5); } catch (e) { console.warn("⚠️  FTS5 not available:", e); }

// Standalone classify mode (no ingest, just re-score existing sessions)
if (classifyMode && !rebuildMode && !statsMode) {
  console.log("🏷  Classifying sessions...\n");
  classifyAll(db);
  db.close();
  process.exit(0);
}

if (statsMode) {
  console.log("\n📊 CORPUS STATS\n");
  for (const t of ["sessions", "session_restarts", "file_edits", "terminal_cmds", "code_blocks", "tool_calls", "commit_refs", "memory_snapshots", "messages"]) {
    const row = db.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get() as { n: number };
    console.log(`  ${t.padEnd(22)} ${String(row.n).padStart(6)} rows`);
  }
  for (const t of ["fts_messages", "fts_cmds"]) {
    try {
      const row = db.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get() as { n: number };
      console.log(`  ${t.padEnd(22)} ${String(row.n).padStart(6)} rows (FTS5)`);
    } catch { /* FTS5 not available */ }
  }
  const top = db.prepare("SELECT filePath, editCount FROM hot_files LIMIT 5").all() as Array<{ filePath: string; editCount: number }>;
  if (top.length) {
    console.log("\n  Top files:");
    for (const r of top) console.log(`    ${String(r.editCount).padStart(4)}×  ${r.filePath}`);
  }
  db.close();
  process.exit(0);
}

// Determine which sessions to ingest
if (!existsSync(sessionsDir)) { console.error("No manifest/sessions/ dir"); process.exit(1); }
const allIds = readdirSync(sessionsDir).filter(d => existsSync(join(sessionsDir, d, "transcript.jsonl")));
const ids    = targetSession ? [targetSession] : allIds;

console.log(`session-corpus: ${ids.length} session(s)${rebuildMode ? " (rebuild)" : ""}...`);

let ingested = 0;
let skipped  = 0;

for (const id of ids) {
  // Incremental: skip if already ingested and transcript hasn't grown since
  if (!targetSession && !rebuildMode) {
    const row = db.prepare("SELECT ingestedAt FROM sessions WHERE sessionId = ?").get(id) as { ingestedAt: string } | undefined;
    if (row) {
      const tPath = join(sessionsDir, id, "transcript.jsonl");
      const mtime = existsSync(tPath) ? statSync(tPath).mtime : new Date(0);
      if (new Date(row.ingestedAt) >= mtime) { skipped++; continue; }
    }
  }

  if (ingestSession(db, id)) { process.stdout.write(`  ✅ ${id.slice(0, 8)}\n`); ingested++; }
  else { process.stdout.write(`  ⚠️  ${id.slice(0, 8)} — skipped (no transcript)\n`); }
}

if (!watchMode) {
  // Auto-classify after any ingest pass (or when explicitly requested with --classify)
  if (ingested > 0 || rebuildMode || classifyMode) {
    console.log("\n🏷  Classifying sessions...\n");
    classifyAll(db);
  }
  db.close();
  console.log(`\nDone: ${ingested} ingested, ${skipped} up-to-date  →  ${corpusPath}`);
  process.exit(0);
}

// ─────────────────────────────────────────────────────────────
// Watch mode — re-ingest sessions as transcript.jsonl grows
// ─────────────────────────────────────────────────────────────
console.log(`\n👁  Watching ${sessionsDir} for changes (Ctrl+C to stop)...`);

const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

watch(sessionsDir, { recursive: true }, (event, filename) => {
  if (!filename) return;
  const norm = filename.replace(/\\/g, "/");
  if (!norm.endsWith("transcript.jsonl")) return;
  const sessionId = norm.split("/")[0];
  if (!sessionId) return;

  // Debounce per session — wait 1.5s of quiet before re-ingesting
  const existing = debounceTimers.get(sessionId);
  if (existing) clearTimeout(existing);
  debounceTimers.set(sessionId, setTimeout(() => {
    debounceTimers.delete(sessionId);
    const before = db.prepare("SELECT COUNT(*) AS n FROM messages WHERE sessionId = ?").get(sessionId) as { n: number } | undefined;
    const ok = ingestSession(db, sessionId);
    if (ok) {
      const after = db.prepare("SELECT COUNT(*) AS n FROM messages WHERE sessionId = ?").get(sessionId) as { n: number };
      const delta = after.n - (before?.n ?? 0);
      const sign  = delta > 0 ? `+${delta}` : String(delta);
      console.log(`  ↻ [${sessionId.slice(0, 8)}] re-ingested  ${after.n} messages (${sign} new)  ${new Date().toISOString().slice(11, 19)}`);
    }
  }, 1500));
});
