#!/usr/bin/env bun
// @SID: SCRIPT_CORPUS_MCP_V1

/**
 * corpus-mcp — Bun stdio MCP server for manifest/corpus.sqlite
 *
 * Exposes the Copilot Chat session corpus as MCP tools so agents can
 * query session history, search messages, inspect tool usage, etc.
 * without any manual CLI invocations.
 *
 * Tools:
 *   corpus_timeline      — session list ordered by time
 *   corpus_search        — FTS5 full-text search across all messages
 *   corpus_messages      — messages for a specific session
 *   corpus_hot_files     — most-edited files across all sessions
 *   corpus_tool_freq     — tool usage frequency ranking
 *   corpus_stats         — row counts per table
 *   corpus_sql           — raw SELECT-only SQL (sandboxed)
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
  db.exec("PRAGMA journal_mode = DELETE; PRAGMA foreign_keys = ON;");
  return db;
}

// ─────────────────────────────────────────────────────────────
// Tool implementations
// ─────────────────────────────────────────────────────────────

function toolTimeline(limit: number): unknown[] {
  const db = openDB();
  try {
    return db.prepare(`
      SELECT sessionId, startTime, turns, copilotVersion,
             editCount, cmdCount, commitCount, userTurns, assistantTurns,
             SUBSTR(intent, 1, 150) AS intent
      FROM session_timeline
      LIMIT ?
    `).all(limit);
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

// ─────────────────────────────────────────────────────────────
// MCP server
// ─────────────────────────────────────────────────────────────

const server = new Server(
  { name: "corpus", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "corpus_timeline",
      description: "List all Copilot Chat sessions ordered by start time. Returns session IDs, timestamps, turn counts, edit/cmd stats, and a brief intent summary.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit: { type: "number", description: "Max sessions to return (default 20)" }
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
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  const a = (args ?? {}) as Record<string, unknown>;

  try {
    let result: unknown;

    if (name === "corpus_timeline") {
      result = toolTimeline(Number(a.limit ?? 20));
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
