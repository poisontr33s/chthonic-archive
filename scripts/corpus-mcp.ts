#!/usr/bin/env bun
// @SID: SCRIPT_CORPUS_MCP_V2

/**
 * corpus-mcp — Bun stdio MCP server for manifest/corpus.sqlite
 *
 * Exposes the Copilot Chat session corpus as MCP tools so agents can
 * query session history, search messages, inspect tool usage, etc.
 * without any manual CLI invocations.
 *
 * Tools (18):
 *   corpus_timeline          — session list ordered by time
 *   corpus_search            — FTS5 full-text search across all messages
 *   corpus_messages          — messages for a specific session
 *   corpus_hot_files         — most-edited files across all sessions
 *   corpus_tool_freq         — tool usage frequency ranking
 *   corpus_stats             — row counts per table
 *   corpus_sql               — raw SELECT-only SQL (sandboxed)
 *   corpus_classify          — sessions grouped by topic
 *   corpus_session_context   — full resume-packet for one session
 *   corpus_tool_result       — G2: tool call details + full result content (lossless) by callId
 *   corpus_memories          — G2: memory snapshots (session + global)
 *   corpus_annotate          — G4: write topic/tags/note to a session record
 *   corpus_memory_write      — G4: inject a memory snapshot programmatically
 *   corpus_gate_ladder       — G5: read or persist the pipeline gate state into corpus memory
 *   corpus_resources_list    — G5: list all sessions as MCP Resources URIs
 *   corpus_semantic_search   — G7: vector similarity search across session embeddings (Qwen3-Embedding-0.6B)
 *   corpus_federation_status — G9: list registered satellites + drain DB existence check
 *   corpus_federation_query  — G9: cross-satellite SELECT via ATTACH DATABASE
 *
 * Resources:
 *   corpus://session/<sessionId>  — full session context as JSON (MCP Resources protocol)
 *
 * Registration: .mcp.json → "corpus" → "command": "bun run scripts/corpus-mcp.ts"
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Database } from "bun:sqlite";
import { existsSync, readdirSync, readFileSync } from "fs";
import { join, resolve } from "path";
import { load as loadSqliteVec } from "sqlite-vec";

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

function toolTimeline(limit: number, workspaceHash?: string, ranked = false): unknown[] {
  const db = openDB();
  try {
    const view = ranked ? "session_ranked" : "session_timeline";
    const orderBy = ranked
      ? "ORDER BY (0.6 * recencyScore + 0.4 * signalScore) DESC"
      : "";
    if (workspaceHash) {
      return db.prepare(`
        SELECT * FROM ${view}
        WHERE workspaceHash = ?
        ${orderBy}
        LIMIT ?
      `).all(workspaceHash, limit);
    }
    return db.prepare(`
      SELECT * FROM ${view}
      ${orderBy}
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
    // fts_messages is a standalone FTS5 table (NOT content=); join on sessions for
    // workspace name, NOT on messages.rowid (rowids don't align).
    return db.prepare(`
      SELECT f.sessionId,
             s.workspaceName,
             f.role,
             CAST(f.turn AS INTEGER)                        AS turn,
             s.startTime,
             snippet(fts_messages, 3, '▸', '◂', '…', 30)  AS excerpt
      FROM fts_messages f
      JOIN sessions s ON s.sessionId = f.sessionId
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

// ─── G5 gate ladder ──────────────────────────────────────────

// ─── G6 recency ranking ──────────────────────────────────────

function toolRecencyRank(
  limit: number,
  alpha: number,
  halfLifeDays: number,
  workspaceHash?: string
): unknown[] {
  const db = openDB();
  try {
    const base = workspaceHash
      ? db.prepare(
          "SELECT * FROM session_ranked WHERE workspaceHash = ? ORDER BY startTime DESC"
        ).all(workspaceHash) as Array<Record<string, unknown>>
      : db.prepare(
          "SELECT * FROM session_ranked ORDER BY startTime DESC"
        ).all() as Array<Record<string, unknown>>;

    const k = Math.log(2) / halfLifeDays;
    const results = base.map(r => {
      const daysSince = Number(r.daysSince ?? 0);
      const recencyScore = Math.exp(-daysSince * k);
      const signalScore  = Number(r.signalScore ?? 0);
      const compositeScore = alpha * recencyScore + (1 - alpha) * signalScore;
      return {
        sessionId:      r.sessionId,
        startTime:      r.startTime,
        topic:          r.topic,
        tags:           r.tags,
        turns:          r.turns,
        daysSince:      Math.round(daysSince * 10) / 10,
        recencyScore:   Math.round(recencyScore  * 10000) / 10000,
        signalScore:    Math.round(signalScore   * 10000) / 10000,
        compositeScore: Math.round(compositeScore * 10000) / 10000,
      };
    });
    results.sort((a, b) => b.compositeScore - a.compositeScore);
    return results.slice(0, limit);
  } finally { db.close(); }
}

// ─── G8b entity tools ─────────────────────────────────────────

function toolEntities(
  kind?: string,
  name?: string,
  limit = 50
): unknown[] {
  const db = openDB();
  try {
    const wheres: string[] = [];
    const params: unknown[] = [];
    if (kind) { wheres.push("kind = ?"); params.push(kind); }
    if (name) { wheres.push("name LIKE ?"); params.push(name.includes("%") ? name : `%${name}%`); }
    const where = wheres.length ? "WHERE " + wheres.join(" AND ") : "";
    params.push(limit);
    return db.prepare(
      `SELECT id, kind, name, occurrenceCount, firstSeenAt, lastSeenAt, source
       FROM entities ${where}
       ORDER BY occurrenceCount DESC LIMIT ?`
    ).all(...(params as [unknown, ...unknown[]]));
  } finally { db.close(); }
}

function toolEntityGraph(
  entityId: string,
  depth: number,
  limit: number
): unknown {
  const db = openDB();
  try {
    const root = db.prepare(
      "SELECT id, kind, name, occurrenceCount, firstSeenAt, lastSeenAt FROM entities WHERE id = ?"
    ).get(entityId) as Record<string, unknown> | undefined;
    if (!root) throw new Error(`Entity not found: ${entityId}`);

    const neighbors = db.prepare(`
      SELECT e.id, e.kind, e.name, e.occurrenceCount, ec.coSessions
      FROM entity_cooccurrence ec
      JOIN entities e ON e.id = ec.toId
      WHERE ec.fromId = ?
      UNION
      SELECT e.id, e.kind, e.name, e.occurrenceCount, ec.coSessions
      FROM entity_cooccurrence ec
      JOIN entities e ON e.id = ec.fromId
      WHERE ec.toId = ?
      ORDER BY coSessions DESC
      LIMIT ?
    `).all(entityId, entityId, limit) as Array<Record<string, unknown>>;

    let level2: Array<{ via: string; entity: Record<string, unknown>; coSessions: number }> = [];
    if (depth >= 2 && neighbors.length > 0) {
      const top5 = neighbors.slice(0, 5);
      for (const n of top5) {
        const nid = String(n.id);
        if (nid === entityId) continue;
        const l2rows = db.prepare(`
          SELECT e.id, e.kind, e.name, e.occurrenceCount, ec.coSessions
          FROM entity_cooccurrence ec
          JOIN entities e ON e.id = ec.toId
          WHERE ec.fromId = ? AND ec.toId != ?
          UNION
          SELECT e.id, e.kind, e.name, e.occurrenceCount, ec.coSessions
          FROM entity_cooccurrence ec
          JOIN entities e ON e.id = ec.fromId
          WHERE ec.toId = ? AND ec.fromId != ?
          ORDER BY coSessions DESC LIMIT 5
        `).all(nid, entityId, nid, entityId) as Array<Record<string, unknown>>;
        for (const r of l2rows) {
          level2.push({ via: nid, entity: r, coSessions: Number(r.coSessions) });
        }
      }
      // Deduplicate by entity id
      const seen = new Set([entityId, ...neighbors.map(n => String(n.id))]);
      level2 = level2.filter(r => !seen.has(String(r.entity.id)));
    }

    return { root, neighbors, level2 };
  } finally { db.close(); }
}

function toolRelated(
  sessionId: string,
  limit: number,
  scoreFn: "jaccard" | "weighted"
): unknown[] {
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

    // Get entity ids for target session
    const myEntities = new Set(
      (db.prepare("SELECT DISTINCT entityId FROM entity_occurrences WHERE sessionId = ?").all(sid) as Array<{ entityId: string }>)
        .map(r => r.entityId)
    );
    if (myEntities.size === 0) return [];

    // Find other sessions sharing at least one entity
    const candidates = db.prepare(`
      SELECT DISTINCT sessionId FROM entity_occurrences
      WHERE entityId IN (${[...myEntities].map(() => "?").join(",")})
        AND sessionId != ?
    `).all(...([...myEntities, sid] as [unknown, ...unknown[]])) as Array<{ sessionId: string }>;

    const scored: Array<{ sessionId: string; topic: unknown; sharedEntities: number; score: number; topShared: unknown[] }> = [];
    for (const c of candidates) {
      const theirEntities = new Set(
        (db.prepare("SELECT DISTINCT entityId FROM entity_occurrences WHERE sessionId = ?").all(c.sessionId) as Array<{ entityId: string }>)
          .map(r => r.entityId)
      );
      const shared = [...myEntities].filter(e => theirEntities.has(e));
      const union  = new Set([...myEntities, ...theirEntities]);

      let score: number;
      if (scoreFn === "jaccard") {
        score = shared.length / union.size;
      } else {
        // weighted: each shared entity contributes its occurrenceCount
        const weights = db.prepare(
          `SELECT SUM(occurrenceCount) AS w FROM entities WHERE id IN (${shared.map(() => "?").join(",")})`
        ).get(...(shared as [unknown, ...unknown[]])) as { w: number | null } | undefined;
        score = (weights?.w ?? shared.length) / (myEntities.size + theirEntities.size);
      }

      const meta = db.prepare(
        "SELECT topic FROM sessions WHERE sessionId = ?"
      ).get(c.sessionId) as { topic: string | null } | undefined;

      const topSharedRows = db.prepare(
        `SELECT e.id, e.kind, e.name FROM entities e
         WHERE e.id IN (${shared.slice(0, 10).map(() => "?").join(",")})
         ORDER BY e.occurrenceCount DESC LIMIT 5`
      ).all(...(shared.slice(0, 10) as [unknown, ...unknown[]]));

      scored.push({
        sessionId:      c.sessionId,
        topic:          meta?.topic ?? null,
        sharedEntities: shared.length,
        score:          Math.round(score * 10000) / 10000,
        topShared:      topSharedRows,
      });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit);
  } finally { db.close(); }
}

function toolGateLadder(persist: boolean): unknown {
  const db = openDB();
  let ladder: Array<{ gate: string; status: string; detail: string }>;
  try {
    const cols = (t: string) =>
      (db.prepare(`PRAGMA table_info(${t})`).all() as Array<{ name: string }>)
        .map(c => c.name);

    const count = (sql: string, ...p: unknown[]) =>
      (db.prepare(sql).get(...p) as { c: number }).c;

    const hasFts = db.prepare(
      "SELECT COUNT(*) AS c FROM sqlite_master WHERE type='table' AND name='fts_messages'"
    ).get() as { c: number };

    const sessionCols  = cols("sessions");
    const toolCols     = cols("tool_calls");

    ladder = [
      { gate: "G6",  status: (() => {
        const viewExists = db.prepare("SELECT COUNT(*) AS c FROM sqlite_master WHERE type='view' AND name='session_ranked'").get() as {c:number};
        return viewExists.c > 0 ? "admitted" : "open";
      })(), detail: "session_ranked view + corpus_recency_rank tool" },
      { gate: "G8b", status: (() => {
        const tableExists = db.prepare("SELECT COUNT(*) AS c FROM sqlite_master WHERE type='table' AND name='entities'").get() as {c:number};
        if (!tableExists.c) return "open";
        const rows = db.prepare("SELECT COUNT(*) AS c FROM entities").get() as {c:number};
        return rows.c > 0 ? "admitted" : "open";
      })(), detail: (() => {
        try { const r = db.prepare("SELECT COUNT(*) AS c FROM entities").get() as {c:number}; return `entities: ${r.c} rows`; }
        catch { return "entities table not present"; }
      })() },
      { gate: "G0",  status: "admitted", detail: "corpus.sqlite + session-watcher + session-corpus + corpus-mcp present" },
      { gate: "G1a", status: count("SELECT COUNT(*) AS c FROM sessions") > 0 ? "admitted" : "open",
        detail: `sessions: ${count("SELECT COUNT(*) AS c FROM sessions")} rows` },
      { gate: "G1b", status: count("SELECT COUNT(*) AS c FROM memory_snapshots") > 0 ? "admitted" : "open",
        detail: `memory_snapshots: ${count("SELECT COUNT(*) AS c FROM memory_snapshots")} rows` },
      { gate: "G2",  status: count("SELECT COUNT(*) AS c FROM tool_calls") > 0 ? "admitted" : "open",
        detail: `messages: ${count("SELECT COUNT(*) AS c FROM messages")} · tool_calls: ${count("SELECT COUNT(*) AS c FROM tool_calls")}` },
      { gate: "G3",  status: sessionCols.includes("workspaceName") ? "admitted" : "open",
        detail: sessionCols.includes("workspaceName") ? "workspaceName column present" : "MISSING workspaceName" },
      { gate: "G4",  status: sessionCols.includes("note") ? "admitted" : "open",
        detail: sessionCols.includes("note") ? "write-back columns present (topic/tags/note)" : "MISSING note column" },
      { gate: "G4.5",status: toolCols.includes("resultContent") ? "admitted" : "open",
        detail: toolCols.includes("resultContent")
          ? `resultContent column present · ${count("SELECT COUNT(*) AS c FROM tool_calls WHERE resultContent IS NOT NULL")} rows populated`
          : "MISSING resultContent" },
      { gate: "G5",  status: hasFts.c > 0 ? "admitted" : "open",
        detail: hasFts.c > 0 ? "fts_messages FTS5 index present · MCP Resources protocol active" : "FTS5 index not yet created" },
    ];
  } finally { db.close(); }

  if (!persist) return ladder;

  // Persist as memory snapshot
  const lines = [
    "# Corpus Pipeline — Gate Ladder",
    `\n_Updated: ${new Date().toISOString()}_\n`,
    "| Gate | Status | Detail |",
    "|------|--------|--------|",,
    ...ladder.map(r => `| ${r.gate.padEnd(5)} | ${r.status.padEnd(8)} | ${r.detail} |`),
  ].join("\n");

  const dbw = openDBWrite();
  try {
    dbw.prepare(
      "INSERT INTO memory_snapshots (sessionId, filename, content, capturedAt) VALUES (?, ?, ?, ?)"
    ).run("_global_", "gate-ladder.md", lines, new Date().toISOString());
  } finally { dbw.close(); }

  return { persisted: true, gates: ladder };
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
// G7 semantic search (vec0 KNN via sqlite-vec)
// ─────────────────────────────────────────────────────────────

async function toolSemanticSearch(query: string, limit: number): Promise<unknown[]> {
  const pyScript = resolve(import.meta.dir, "embed.py");

  // Embed the query text via embed.py subprocess
  const proc = Bun.spawn(["uv", "run", pyScript], {
    stdin:  "pipe",
    stdout: "pipe",
    stderr: "inherit",
  });
  const enc = new TextEncoder();
  proc.stdin.write(enc.encode(JSON.stringify({ id: "query", text: query }) + "\n"));
  proc.stdin.end();

  const rawOut = await new Response(proc.stdout).text();
  await proc.exited;

  let queryVec: number[] | null = null;
  for (const line of rawOut.split("\n")) {
    if (!line.trim()) continue;
    try {
      const parsed = JSON.parse(line) as { id: string; vec: number[] };
      if (parsed.id === "query") { queryVec = parsed.vec; break; }
    } catch { /* skip malformed lines */ }
  }
  if (!queryVec) throw new Error("Embedding failed — embed.py produced no vector for query. Run: bun run session:corpus --embed first.");

  const db = openDB();
  loadSqliteVec(db);
  try {
    const vecBytes = new Uint8Array(new Float32Array(queryVec).buffer);
    const rows = db.prepare(`
      SELECT v.session_id AS sessionId,
             v.distance,
             s.topic,
             s.startTime,
             s.workspaceName
      FROM vec_embeddings v
      LEFT JOIN sessions s ON s.sessionId = v.session_id
      WHERE v.content_embedding MATCH ?
      ORDER BY v.distance ASC
      LIMIT ?
    `).all(vecBytes, limit) as Array<Record<string, unknown>>;
    return rows;
  } finally { db.close(); }
}

// ─────────────────────────────────────────────────────────────
// G9 federation tools (ATTACH DATABASE multi-satellite)
// ─────────────────────────────────────────────────────────────

const SATELLITES_DIR = resolve(import.meta.dir, "..", "scripts", "satellites");

function toolFederationStatus(): unknown {
  const results: Array<Record<string, unknown>> = [];
  if (!existsSync(SATELLITES_DIR)) {
    return { satellites: [], scanned_at: new Date().toISOString(), warning: `satellites dir not found: ${SATELLITES_DIR}` };
  }
  for (const entry of readdirSync(SATELLITES_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const jsonPath = resolve(SATELLITES_DIR, entry.name, "satellite.json");
    if (!existsSync(jsonPath)) continue;
    let contract: Record<string, unknown>;
    try { contract = JSON.parse(readFileSync(jsonPath, "utf8")); }
    catch { results.push({ name: entry.name, error: "satellite.json parse failed" }); continue; }
    const df = contract.drain_format as Record<string, unknown> | undefined;
    const drainRelPath = (typeof df?.path === "string") ? df.path : null;
    const drainAbsPath = drainRelPath ? resolve(import.meta.dir, "..", drainRelPath) : null;
    results.push({
      satellite_id:      contract.satellite_id,
      version:           contract.version,
      drain_path:        drainRelPath,
      drain_exists:      drainAbsPath ? existsSync(drainAbsPath) : null,
      tables:            df?.tables,
      federation_keys:   contract.federation_keys,
      outbound_network:  contract.outbound_network,
      license:           contract.license,
      corpus_schema_min: contract.corpus_schema_min,
    });
  }
  return { satellites: results, count: results.length, scanned_at: new Date().toISOString() };
}

function toolFederationQuery(satelliteId: string, sql: string): unknown[] {
  // Same SELECT-only sandbox as corpus_sql
  const trimmed = sql.trim().toUpperCase();
  if (!trimmed.startsWith("SELECT") && !trimmed.startsWith("WITH")) {
    throw new Error("Only SELECT / WITH queries are allowed.");
  }
  for (const kw of ["DROP","DELETE","INSERT","UPDATE","CREATE","ALTER","PRAGMA","VACUUM"]) {
    if (new RegExp(`\\b${kw}\\b`).test(trimmed)) throw new Error(`Blocked keyword: ${kw}`);
  }

  const jsonPath = resolve(SATELLITES_DIR, satelliteId, "satellite.json");
  if (!existsSync(jsonPath)) throw new Error(`Satellite not registered: ${satelliteId}`);

  const contract = JSON.parse(readFileSync(jsonPath, "utf8")) as Record<string, unknown>;
  const df = contract.drain_format as Record<string, unknown> | undefined;
  if (!df?.path) throw new Error(`satellite.json missing drain_format.path for satellite: ${satelliteId}`);

  const drainPath = resolve(import.meta.dir, "..", df.path as string);
  if (!existsSync(drainPath)) {
    throw new Error(`Satellite DB not found: ${df.path}. Run the satellite drain script first.`);
  }

  const alias = satelliteId.replace(/-/g, "_");
  const db = openDB();
  try {
    db.exec(`ATTACH DATABASE '${drainPath.replace(/'/g, "''")}' AS ${alias}`);
    return db.prepare(sql).all();
  } finally { db.close(); }
}

// ─────────────────────────────────────────────────────────────
// MCP server
// ─────────────────────────────────────────────────────────────

const server = new Server(
  { name: "corpus", version: "2.7.0" },
  { capabilities: { tools: {}, resources: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "corpus_timeline",
      description: "List all Copilot Chat sessions ordered by start time. Returns session IDs, timestamps, turn counts, workspaceHash, workspaceName, edit/cmd stats, and a brief intent summary. Set ranked=true to order by composite recency+signal score instead.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit:          { type: "number",  description: "Max sessions to return (default 20)" },
          workspace_hash: { type: "string",  description: "Filter by workspace hash (optional)" },
          ranked:         { type: "boolean", description: "If true, order by composite recency+signal score (default false)" }
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
      }    },
    {
      name: "corpus_recency_rank",
      description: "G6: Return sessions ranked by a composite of recency and signal density. alpha=0.6 weights recency vs signal. halfLifeDays controls decay speed. Returns daysSince, recencyScore, signalScore, compositeScore per session.",
      inputSchema: {
        type: "object" as const,
        properties: {
          limit:        { type: "number",  description: "Max sessions to return (default 20)" },
          alpha:        { type: "number",  description: "Recency weight 0..1 (default 0.6)" },
          halfLifeDays: { type: "number",  description: "Recency half-life in days (default 7)" },
          workspaceHash:{ type: "string",  description: "Filter to a specific workspace hash" }
        }
      }
    },
    {
      name: "corpus_entities",
      description: "G8b: List extracted entities (files, tools, commits, gates, agents, concepts) sorted by occurrence frequency.",
      inputSchema: {
        type: "object" as const,
        properties: {
          kind:  { type: "string", description: "Filter by kind: file|tool|commit|gate|agent|concept" },
          name:  { type: "string", description: "Substring match on entity name" },
          limit: { type: "number", description: "Max results (default 50)" }
        }
      }
    },
    {
      name: "corpus_entity_graph",
      description: "G8b: Return the co-occurrence graph for an entity — which other entities appear in the same sessions. depth=2 expands one hop further.",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: { type: "string",  description: "Entity id in kind:name format (e.g. 'file:scripts/corpus-mcp.ts')" },
          depth:    { type: "number",  description: "Graph depth: 1 or 2 (default 1)" },
          limit:    { type: "number",  description: "Max neighbors (default 20)" }
        },
        required: ["entityId"]
      }
    },
    {
      name: "corpus_related",
      description: "G8b: Find sessions related to a target session by shared entity overlap. scoreFn: 'jaccard' (set ratio) or 'weighted' (occurrence-weighted). Returns ranked list with sharedEntities count and topShared entities.",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: { type: "string", description: "Session UUID or 8+ char prefix" },
          limit:     { type: "number", description: "Max results (default 10)" },
          scoreFn:   { type: "string", description: "'jaccard' or 'weighted' (default 'weighted')" }
        },
        required: ["sessionId"]
      }
    },
    {
      name: "corpus_gate_ladder",
      description: "G5: Read or persist the corpus pipeline gate-ladder. Returns the current gate state derived live from the DB schema. Pass persist=true to write the result to corpus memory as 'gate-ladder.md' (replacing any external gate doc).",
      inputSchema: {
        type: "object" as const,
        properties: {
          persist: { type: "boolean", description: "If true, write gate-ladder.md to memory_snapshots (default false)" }
        }
      }
    },
    {
      name: "corpus_resources_list",
      description: "G5: List all sessions as MCP Resources URIs (corpus://session/<sessionId>). Thin wrapper over ListResources for agent callers that prefer tool interface.",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "corpus_semantic_search",
      description: "G7: Vector similarity search across session embeddings. Encodes the query via Qwen3-Embedding-0.6B (1024d), then runs a KNN cosine-distance search against vec_embeddings. Returns sessions ranked by semantic similarity with distance, topic, and startTime. Requires G7 embeddings to be present (run: bun run session:corpus --embed).",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string",  description: "Natural language search query" },
          limit: { type: "number",  description: "Max results (default 10)" }
        },
        required: ["query"]
      }
    },
    {
      name: "corpus_federation_status",
      description: "G9: List all registered satellites under scripts/satellites/. For each satellite shows: satellite_id, version, drain_path, drain_exists (whether the sidecar DB file is present), federation_keys, and license.",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "corpus_federation_query",
      description: "G9: Run a SELECT query against a satellite's sidecar SQLite DB (ATTACH DATABASE federation). The corpus tables are available as-is; the satellite's tables are available under the <satellite_id_underscored> alias (e.g. 'vampire_terminal_history.terminal_commands'). Only SELECT/WITH are permitted.",
      inputSchema: {
        type: "object" as const,
        properties: {
          satellite_id: { type: "string", description: "Satellite ID (kebab-case, e.g. 'vampire-terminal-history')" },
          sql:          { type: "string", description: "SELECT query. Reference satellite tables as <alias>.<table> where alias = satellite_id with dashes replaced by underscores." }
        },
        required: ["satellite_id", "sql"]
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
      result = toolTimeline(Number(a.limit ?? 20), a.workspace_hash ? String(a.workspace_hash) : undefined, Boolean(a.ranked ?? false));
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
    } else if (name === "corpus_recency_rank") {
      result = toolRecencyRank(
        Number(a.limit ?? 20),
        Math.min(1, Math.max(0, Number(a.alpha ?? 0.6))),
        Number(a.halfLifeDays ?? 7),
        a.workspaceHash ? String(a.workspaceHash) : undefined
      );
    } else if (name === "corpus_entities") {
      result = toolEntities(
        a.kind ? String(a.kind) : undefined,
        a.name ? String(a.name) : undefined,
        Number(a.limit ?? 50)
      );
    } else if (name === "corpus_entity_graph") {
      if (!a.entityId) throw new Error("entityId is required");
      result = toolEntityGraph(String(a.entityId), Math.min(2, Number(a.depth ?? 1)), Number(a.limit ?? 20));
    } else if (name === "corpus_related") {
      if (!a.sessionId) throw new Error("sessionId is required");
      result = toolRelated(
        String(a.sessionId),
        Number(a.limit ?? 10),
        (a.scoreFn === "jaccard" ? "jaccard" : "weighted") as "jaccard" | "weighted"
      );
    } else if (name === "corpus_gate_ladder") {
      result = toolGateLadder(Boolean(a.persist ?? false));
    } else if (name === "corpus_resources_list") {
      const db = openDB();
      try {
        result = db.prepare(
          "SELECT sessionId, workspaceName, startTime, topic FROM sessions ORDER BY startTime DESC"
        ).all();
      } finally { db.close(); }
    } else if (name === "corpus_semantic_search") {
      if (!a.query) throw new Error("query is required");
      result = await toolSemanticSearch(String(a.query), Number(a.limit ?? 10));
    } else if (name === "corpus_federation_status") {
      result = toolFederationStatus();
    } else if (name === "corpus_federation_query") {
      if (!a.satellite_id) throw new Error("satellite_id is required");
      if (!a.sql)         throw new Error("sql is required");
      result = toolFederationQuery(String(a.satellite_id), String(a.sql));
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
// MCP Resources — corpus://session/<sessionId>
// ─────────────────────────────────────────────────────────────

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const db = openDB();
  try {
    const rows = db.prepare(
      "SELECT sessionId, workspaceName, startTime, topic FROM sessions ORDER BY startTime DESC"
    ).all() as Array<{ sessionId: string; workspaceName: string | null; startTime: string; topic: string | null }>;
    return {
      resources: rows.map(s => ({
        uri:         `corpus://session/${s.sessionId}`,
        name:        s.workspaceName ?? s.sessionId.slice(0, 8),
        description: [s.topic, s.startTime].filter(Boolean).join(" · "),
        mimeType:    "application/json",
      }))
    };
  } finally { db.close(); }
});

server.setRequestHandler(ReadResourceRequestSchema, async (req) => {
  const uri = req.params.uri as string;
  const match = uri.match(/^corpus:\/\/session\/(.+)$/);
  if (!match) throw new Error(`Unsupported resource URI: ${uri}`);
  const sessionId = match[1];
  const content   = toolSessionContext(sessionId);
  return {
    contents: [{
      uri,
      mimeType: "application/json",
      text:     JSON.stringify(content, null, 2),
    }]
  };
});

// ─────────────────────────────────────────────────────────────
// Start
// ─────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
