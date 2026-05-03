#!/usr/bin/env bun
// @SID: SCRIPT_CORPUS_MCP_V2

/**
 * corpus-mcp — Bun stdio MCP server for manifest/corpus.sqlite
 *
 * Exposes the Copilot Chat session corpus as MCP tools so agents can
 * query session history, search messages, inspect tool usage, etc.
 * without any manual CLI invocations.
 *
 * Tools (13):
 *   corpus_timeline      — session list ordered by time
 *   corpus_search        — FTS5 full-text search across all messages
 *   corpus_messages      — messages for a specific session
 *   corpus_hot_files     — most-edited files across all sessions
 *   corpus_tool_freq     — tool usage frequency ranking
 *   corpus_stats         — row counts per table
 *   corpus_sql           — raw SELECT-only SQL (sandboxed)
 *   corpus_classify      — sessions grouped by topic
 *   corpus_session_context — full resume-packet for one session
 *   corpus_tool_result   — G2: tool call details + full result content (lossless) by callId
 *   corpus_memories      — G2: memory snapshots (session + global)
 *   corpus_annotate      — G4: write topic/tags/note to a session record
 *   corpus_memory_write  — G4: inject a memory snapshot programmatically
 *
 * Registration: .mcp.json → "corpus" → "command": "bun run scripts/corpus-mcp.ts"
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Database } from "bun:sqlite";
import { existsSync } from "fs";
import { join } from "path";

// ─────────────────────────────────────────────────────────────
// DB setup
// ─────────────────────────────────────────────────────────────

const manifestDir = join(import.meta.dir, "..", "manifest");
const corpusPath  = join(manifestDir, "corpus.sqlite");

function openDB(): Database {
  if (!existsSync(corpusPath)) {
    throw new Error(`corpus.sqlite not found at ${corpusPath}. Run: bun run session:corpus`);
  }
  const db = new Database(corpusPath, { readonly: true });
  db.exec("PRAGMA foreign_keys = ON;");
  return db;
}

function openDBWrite(): Database {
  if (!existsSync(corpusPath)) {
    throw new Error(`corpus.sqlite not found at ${corpusPath}. Run: bun run session:corpus`);
  }
  const db = new Database(corpusPath, { readonly: false });
  db.exec("PRAGMA foreign_keys = ON;");
  return db;
}

// ─────────────────────────────────────────────────────────────
// Tool implementations
// ─────────────────────────────────────────────────────────────

function toolTimeline(limit: number, workspaceHash?: string): unknown[] {
  const db = openDB();
  try {
    if (workspaceHash) {
      return db.prepare(`
        SELECT sessionId, startTime, turns, copilotVersion,
               workspaceHash, workspaceName,
               editCount, cmdCount, commitCount, userTurns, assistantTurns,
               topic, tags,
               SUBSTR(intent, 1, 150) AS intent
        FROM session_timeline
        WHERE workspaceHash = ?
        LIMIT ?
      `).all(workspaceHash, limit);
    }
    return db.prepare(`
      SELECT sessionId, startTime, turns, copilotVersion,
             workspaceHash, workspaceName,
             editCount, cmdCount, commitCount, userTurns, assistantTurns,
             topic, tags,
             SUBSTR(intent, 1, 150) AS intent
      FROM session_timeline
      LIMIT ?
    `).all(limit);
  } finally { db.close(); }
}

function toolClassify(): unknown[] {
  const db = openDB();
  try {
    // Group sessions by topic, include per-group session list
    const rows = db.prepare(`
      SELECT topic, tags, sessionId, startTime, turns,
             SUBSTR(intent, 1, 120) AS intent
      FROM session_timeline
      ORDER BY COALESCE(topic,'zzz'), startTime DESC
    `).all() as Array<{ topic: string | null; tags: string | null; sessionId: string; startTime: string; turns: number; intent: string }>;

    // Group by topic
    const groups: Record<string, { topic: string; sessions: unknown[] }> = {};
    for (const r of rows) {
      const key = r.topic ?? "(unclassified)";
      if (!groups[key]) groups[key] = { topic: key, sessions: [] };
      groups[key].sessions.push({
        sessionId: r.sessionId,
        startTime: r.startTime,
        turns:     r.turns,
        tags:      r.tags ? JSON.parse(r.tags) : [],
        intent:    r.intent,
      });
    }
    return Object.values(groups).map(g => ({
      topic:    g.topic,
      count:    g.sessions.length,
      sessions: g.sessions,
    }));
  } finally { db.close(); }
}

function toolSessionContext(sessionId: string): unknown {
  const db = openDB();
  try {
    // Resolve prefix
    let sid = sessionId;
    if (sid.length < 36) {
      const row = db.prepare(
        "SELECT sessionId FROM sessions WHERE sessionId LIKE ? LIMIT 1"
      ).get(sid + "%") as { sessionId: string } | undefined;
      if (!row) throw new Error(`No session matching prefix: ${sid}`);
      sid = row.sessionId;
    }

    const meta = db.prepare(
      "SELECT sessionId, startTime, turns, copilotVersion, workspaceHash, topic, tags, intent FROM sessions WHERE sessionId = ?"
    ).get(sid) as Record<string, unknown> | undefined;
    if (!meta) throw new Error(`Session not found: ${sid}`);

    const topFiles = db.prepare(
      "SELECT filePath, COUNT(*) AS edits FROM file_edits WHERE sessionId = ? GROUP BY filePath ORDER BY edits DESC LIMIT 15"
    ).all(sid) as Array<{ filePath: string; edits: number }>;

    const recentCmds = db.prepare(
      "SELECT command, goal, turn FROM terminal_cmds WHERE sessionId = ? ORDER BY turn DESC LIMIT 10"
    ).all(sid);

    const commits = db.prepare(
      "SELECT sha, turn FROM commit_refs WHERE sessionId = ? ORDER BY turn DESC LIMIT 10"
    ).all(sid) as Array<{ sha: string; turn: number }>;

    const recentMsgs = db.prepare(`
      SELECT role, turn, SUBSTR(content, 1, 400) AS preview
      FROM messages WHERE sessionId = ?
      ORDER BY turn DESC LIMIT 8
    `).all(sid) as Array<{ role: string; turn: number; preview: string }>;
    recentMsgs.reverse();

    const toolStats = db.prepare(`
      SELECT toolName, COUNT(*) AS calls,
             SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS ok
      FROM tool_calls WHERE sessionId = ?
      GROUP BY toolName ORDER BY calls DESC LIMIT 12
    `).all(sid);

    return {
      sessionId:    meta.sessionId,
      startTime:    meta.startTime,
      turns:        meta.turns,
      topic:        meta.topic,
      tags:         meta.tags ? JSON.parse(String(meta.tags)) : [],
      intent:       meta.intent,
      copilotVersion: meta.copilotVersion,
      topFiles,
      recentCmds,
      commits,
      recentMessages: recentMsgs,
      toolStats,
    };
  } finally { db.close(); }
}

function toolSearch(query: string, limit: number): unknown[] {
  const db = openDB();
  try {
    return db.prepare(`
      SELECT m.sessionId, m.role, m.turn,
             DATETIME(m.ts/1000,'unixepoch') AS time,
             snippet(fts_messages, 3, '▸', '◂', '…', 30) AS excerpt
      FROM fts_messages f
      JOIN messages m ON m.rowid = f.rowid
      WHERE fts_messages MATCH ?
      ORDER BY rank
      LIMIT ?
    `).all(query, limit);
  } finally { db.close(); }
}

function toolMessages(sessionId: string, limit: number): unknown[] {
  const db = openDB();
  try {
    return db.prepare(`
      SELECT role, turn,
             DATETIME(ts/1000,'unixepoch') AS time,
             SUBSTR(content, 1, 500) AS preview,
             toolRequestCount
      FROM messages
      WHERE sessionId = ?
      ORDER BY turn ASC
      LIMIT ?
    `).all(sessionId, limit);
  } finally { db.close(); }
}

function toolHotFiles(limit: number): unknown[] {
  const db = openDB();
  try {
    return db.prepare(`
      SELECT filePath, editCount, sessionCount
      FROM hot_files
      LIMIT ?
    `).all(limit);
  } finally { db.close(); }
}

function toolToolFreq(limit: number): unknown[] {
  const db = openDB();
  try {
    return db.prepare(`
      SELECT toolName,
             COUNT(*)                                          AS calls,
             SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END)    AS successes,
             SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END)    AS failures,
             SUM(CASE WHEN success IS NULL THEN 1 ELSE 0 END) AS unknown,
             COUNT(DISTINCT sessionId)                        AS sessions
      FROM tool_calls
      GROUP BY toolName
      ORDER BY calls DESC
      LIMIT ?
    `).all(limit);
  } finally { db.close(); }
}

function toolStats(): unknown[] {
  const db = openDB();
  try {
    const tables = [
      "sessions","session_restarts","file_edits","terminal_cmds",
      "code_blocks","tool_calls","commit_refs","memory_snapshots","messages"
    ];
    const rows: Array<{ table: string; rows: number }> = [];
    for (const t of tables) {
      const r = db.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get() as { n: number };
      rows.push({ table: t, rows: r.n });
    }
    return rows;
  } finally { db.close(); }
}

function toolSQL(sql: string): unknown[] {
  // Strict SELECT-only sandbox
  const trimmed = sql.trim().toUpperCase();
  if (!trimmed.startsWith("SELECT") && !trimmed.startsWith("WITH")) {
    throw new Error("Only SELECT / WITH queries are allowed.");
  }
  for (const kw of ["DROP","DELETE","INSERT","UPDATE","CREATE","ALTER","ATTACH","PRAGMA","VACUUM"]) {
    if (new RegExp(`\\b${kw}\\b`).test(trimmed)) {
      throw new Error(`Blocked keyword: ${kw}`);
    }
  }
  const db = openDB();
  try {
    return db.prepare(sql).all();
  } finally { db.close(); }
}

function toolToolResult(callId: string): unknown {
  const db = openDB();
  try {
    const row = db.prepare(`
      SELECT tc.callId, tc.toolName, tc.success, tc.turn,
             DATETIME(tc.ts/1000,'unixepoch')           AS startTime,
             DATETIME(tc.tsComplete/1000,'unixepoch')   AS endTime,
             tc.argsJson,
             tc.resultContent,
             tc.resultSnippet,
             tc.sessionId
      FROM tool_calls tc
      WHERE tc.callId = ?
      LIMIT 1
    `).get(callId);
    if (!row) throw new Error(`No tool call found with callId: ${callId}`);
    return row;
  } finally { db.close(); }
}

// ─── G4 write tools ───────────────────────────────────────────

function toolAnnotate(
  sessionId: string,
  fields: { topic?: string; tags?: string[]; note?: string }
): { sessionId: string; updated: number } {
  const db = openDBWrite();
  try {
    // Resolve prefix
    let sid = sessionId;
    if (sid.length < 36) {
      const row = db.prepare(
        "SELECT sessionId FROM sessions WHERE sessionId LIKE ? LIMIT 1"
      ).get(sid + "%") as { sessionId: string } | undefined;
      if (!row) throw new Error(`No session matching prefix: ${sid}`);
      sid = row.sessionId;
    }

    const setParts: string[] = [];
    const values: unknown[]  = [];

    if (fields.topic !== undefined) { setParts.push("topic = ?"); values.push(fields.topic); }
    if (fields.tags  !== undefined) { setParts.push("tags  = ?"); values.push(JSON.stringify(fields.tags)); }
    if (fields.note  !== undefined) { setParts.push("note  = ?"); values.push(fields.note); }

    if (setParts.length === 0)
      throw new Error("At least one of topic, tags, or note must be provided.");

    values.push(sid);
    const stmt = db.prepare(`UPDATE sessions SET ${setParts.join(", ")} WHERE sessionId = ?`);
    const r = stmt.run(...(values as [unknown, ...unknown[]]));
    return { sessionId: sid, updated: (r as { changes: number }).changes };
  } finally { db.close(); }
}

function toolMemoryWrite(
  sessionId: string,
  filename:  string,
  content:   string
): { sessionId: string; filename: string; inserted: boolean } {
  const db = openDBWrite();
  try {
    const capturedAt = new Date().toISOString();
    db.prepare(
      "INSERT INTO memory_snapshots (sessionId, filename, content, capturedAt) VALUES (?, ?, ?, ?)"
    ).run(sessionId, filename, content, capturedAt);
    return { sessionId, filename, inserted: true };
  } finally { db.close(); }
}

function toolMemories(sessionId: string | null, limit: number): unknown[] {
  const db = openDB();
  try {
    const sql = sessionId
      ? `SELECT sessionId, filename, SUBSTR(content, 1, 600) AS preview, capturedAt
         FROM memory_snapshots
         WHERE sessionId = ? OR sessionId = '_global_'
         ORDER BY capturedAt DESC LIMIT ?`
      : `SELECT sessionId, filename, SUBSTR(content, 1, 600) AS preview, capturedAt
         FROM memory_snapshots
         ORDER BY capturedAt DESC LIMIT ?`;
    return sessionId
      ? db.prepare(sql).all(sessionId, limit)
      : db.prepare(sql).all(limit);
  } finally { db.close(); }
}

// ─────────────────────────────────────────────────────────────
// MCP server
// ─────────────────────────────────────────────────────────────

const server = new Server(
  { name: "corpus", version: "2.2.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "corpus_timeline",
      description: "List all Copilot Chat sessions ordered by start time. Returns session IDs, timestamps, turn counts, workspaceHash, workspaceName, edit/cmd stats, and a brief intent summary.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit:          { type: "number", description: "Max sessions to return (default 20)" },
          workspace_hash: { type: "string", description: "Filter by workspace hash (optional)" }
        }
      }
    },
    {
      name: "corpus_search",
      description: "Full-text search across all assistant and user messages in the corpus. Returns session context, role, turn, timestamp, and a highlighted excerpt.",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string", description: "FTS5 search query (e.g. 'flash_attn' or 'vulkan AND compute')" },
          limit: { type: "number", description: "Max results (default 20)" }
        },
        required: ["query"]
      }
    },
    {
      name: "corpus_messages",
      description: "Return conversation messages for a specific session. Provides role, turn index, timestamp, and first 500 chars of each message.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID (8+ chars prefix is sufficient)" },
          limit: { type: "number", description: "Max messages (default 100)" }
        },
        required: ["sessionId"]
      }
    },
    {
      name: "corpus_hot_files",
      description: "Return the most frequently edited files across all sessions, ranked by edit count.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit: { type: "number", description: "Max files (default 30)" }
        }
      }
    },
    {
      name: "corpus_tool_freq",
      description: "Return tool usage frequency ranking: calls, successes, failures, unknown, and session spread for each tool.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit: { type: "number", description: "Max tools to return (default 30)" }
        }
      }
    },
    {
      name: "corpus_stats",
      description: "Return row counts per table in the corpus (sessions, messages, tool_calls, file_edits, etc.).",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "corpus_sql",
      description: "Execute a read-only SELECT (or WITH) SQL query against corpus.sqlite. Only SELECT/WITH are permitted — all write keywords are blocked.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sql: { type: "string", description: "SQL query (SELECT or WITH only)" }
        },
        required: ["sql"]
      }
    },
    {
      name: "corpus_classify",
      description: "Return all sessions grouped by topic (vulkan, tabby-inference, corpus-builder, mas-mcp, extension, theme-system, ssot-governance, ruby-zjit, game, ci-gates, or unclassified). Each group includes session IDs, turn counts, tags, and intent summaries. Run session:corpus --classify to refresh classifications.",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "corpus_session_context",
      description: "Return full resume-packet context for a single session: metadata (topic/tags/intent), top edited files, recent terminal commands, commit refs, most recent messages, and tool usage stats. Use this when an agent needs to pick up where a previous session left off.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID or 8+ char prefix" }
        },
        required: ["sessionId"]
      }
    },
    {
      name: "corpus_tool_result",
      description: "Fetch details + result snippet for a specific tool call by callId. Returns toolName, args, success flag, timing, and the first 400 chars of the assistant message that followed (result proxy).",
      inputSchema: {
        type: "object" as const,
        properties: {
          callId: { type: "string", description: "Tool call ID (e.g. toolu_bdrk_01...)" }
        },
        required: ["callId"]
      }
    },
    {
      name: "corpus_memories",
      description: "Return Copilot memory snapshots — session-scoped and global. These are the files written by the memory-tool across sessions. Filter by sessionId to scope to a specific session, or omit to see all recent memories.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID to scope results (optional — omit for all)" },
          limit:     { type: "number", description: "Max memories to return (default 30)" }
        }
      }
    },
    {
      name: "corpus_annotate",
      description: "Write observations or labels to a session record. Mutable fields: topic (string), tags (string[]), note (free text). All other session fields are read-only. Use this to classify sessions, add research notes, or record insights discovered after the session ended.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID or 8+ char prefix" },
          topic:     { type: "string", description: "Session topic label (e.g. 'vulkan', 'tabby-inference')" },
          tags:      { type: "array",  items: { type: "string" }, description: "Tag array to replace current tags" },
          note:      { type: "string", description: "Free-text note about the session" }
        },
        required: ["sessionId"]
      }
    },
    {
      name: "corpus_memory_write",
      description: "Inject a memory snapshot into the corpus programmatically. Use sessionId='_global_' for cross-session memories. filename should match the source file (e.g. 'user-preferences.md'). Useful for recording agent-derived insights back into the corpus.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID, prefix, or '_global_' for cross-session scope" },
          filename:  { type: "string", description: "Memory file name (e.g. 'session-notes.md')" },
          content:   { type: "string", description: "Memory content to store" }
        },
        required: ["sessionId", "filename", "content"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  const a = (args ?? {}) as Record<string, unknown>;

  try {
    let result: unknown;

    if (name === "corpus_timeline") {
      result = toolTimeline(Number(a.limit ?? 20), a.workspace_hash ? String(a.workspace_hash) : undefined);
    } else if (name === "corpus_search") {
      if (!a.query) throw new Error("query is required");
      result = toolSearch(String(a.query), Number(a.limit ?? 20));
    } else if (name === "corpus_messages") {
      if (!a.sessionId) throw new Error("sessionId is required");
      // Support prefix match — find full session ID
      const db = openDB();
      let sid = String(a.sessionId);
      if (sid.length < 36) {
        const row = db.prepare(
          "SELECT sessionId FROM sessions WHERE sessionId LIKE ? LIMIT 1"
        ).get(sid + "%") as { sessionId: string } | undefined;
        db.close();
        if (!row) throw new Error(`No session matching prefix: ${sid}`);
        sid = row.sessionId;
      } else { db.close(); }
      result = toolMessages(sid, Number(a.limit ?? 100));
    } else if (name === "corpus_hot_files") {
      result = toolHotFiles(Number(a.limit ?? 30));
    } else if (name === "corpus_tool_freq") {
      result = toolToolFreq(Number(a.limit ?? 30));
    } else if (name === "corpus_stats") {
      result = toolStats();
    } else if (name === "corpus_sql") {
      if (!a.sql) throw new Error("sql is required");
      result = toolSQL(String(a.sql));
    } else if (name === "corpus_classify") {
      result = toolClassify();
    } else if (name === "corpus_session_context") {
      if (!a.sessionId) throw new Error("sessionId is required");
      result = toolSessionContext(String(a.sessionId));
    } else if (name === "corpus_tool_result") {
      if (!a.callId) throw new Error("callId is required");
      result = toolToolResult(String(a.callId));
    } else if (name === "corpus_memories") {
      result = toolMemories(a.sessionId ? String(a.sessionId) : null, Number(a.limit ?? 30));
    } else if (name === "corpus_annotate") {
      if (!a.sessionId) throw new Error("sessionId is required");
      result = toolAnnotate(String(a.sessionId), {
        topic: a.topic  !== undefined ? String(a.topic)  : undefined,
        tags:  Array.isArray(a.tags) ? (a.tags as string[]) : undefined,
        note:  a.note   !== undefined ? String(a.note)   : undefined,
      });
    } else if (name === "corpus_memory_write") {
      if (!a.sessionId) throw new Error("sessionId is required");
      if (!a.filename)  throw new Error("filename is required");
      if (!a.content)   throw new Error("content is required");
      result = toolMemoryWrite(String(a.sessionId), String(a.filename), String(a.content));
    } else {
      throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
    };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
      isError: true
    };
  }
});

// ─────────────────────────────────────────────────────────────
// Start
// ─────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
