#!/usr/bin/env bun
// @SID: VAMPIRE_TERMINAL_HISTORY_V1_SATELLITE
/**
 * vampire-terminal-history — sidecar satellite drain
 *
 * Drains manifest/terminal_session.jsonl (written by chthonic-shell-hook.ps1)
 * into manifest/terminal-history.db (sidecar SQLite for G9 federation).
 *
 * Schema:
 *   terminal_sessions(pid INTEGER PK, start_ts TEXT, cwd TEXT)
 *   terminal_commands(seq INTEGER PK, pid INTEGER, ts TEXT,
 *                     command TEXT, cwd TEXT, exit_code INTEGER, duration_ms INTEGER)
 *   terminal_pids(pid INTEGER PK, start_ts TEXT, cwd TEXT, shell TEXT)
 *
 * Usage:
 *   bun run scripts/vampire-terminal-history.ts          # one-shot drain
 *   bun run scripts/vampire-terminal-history.ts --watch  # hot-reload (Bun fs.watch)
 *   bun run scripts/vampire-terminal-history.ts --stats  # row counts
 *   bun run scripts/vampire-terminal-history.ts --stub-corpus  # in-memory DB for testing
 */

import { Database } from "bun:sqlite";
import { existsSync, readFileSync, watch } from "fs";
import { join, resolve } from "path";

// ─────────────────────────────────────────────────────────────
// Paths
// ─────────────────────────────────────────────────────────────

const REPO_ROOT    = resolve(import.meta.dir, "..");
const MANIFEST_DIR = join(REPO_ROOT, "manifest");
const JSONL_PATH   = join(MANIFEST_DIR, "terminal_session.jsonl");
const PIDS_PATH    = join(MANIFEST_DIR, "terminal_pids.json");
const DB_PATH      = join(MANIFEST_DIR, "terminal-history.db");

// ─────────────────────────────────────────────────────────────
// DDL
// ─────────────────────────────────────────────────────────────

const DDL = `
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS terminal_sessions (
  pid       INTEGER PRIMARY KEY,
  start_ts  TEXT,
  cwd       TEXT,
  shell     TEXT
);

CREATE TABLE IF NOT EXISTS terminal_commands (
  seq         INTEGER PRIMARY KEY,
  pid         INTEGER,
  ts          TEXT    NOT NULL,
  command     TEXT    NOT NULL,
  cwd         TEXT,
  exit_code   INTEGER,
  duration_ms INTEGER,
  FOREIGN KEY (pid) REFERENCES terminal_sessions(pid)
);

CREATE INDEX IF NOT EXISTS idx_tc_pid ON terminal_commands(pid);
CREATE INDEX IF NOT EXISTS idx_tc_ts  ON terminal_commands(ts);

CREATE TABLE IF NOT EXISTS terminal_pids (
  pid       INTEGER PRIMARY KEY,
  start_ts  TEXT,
  cwd       TEXT,
  shell     TEXT
);

-- Last watermark for incremental drains
CREATE TABLE IF NOT EXISTS _drain_state (
  key   TEXT PRIMARY KEY,
  value TEXT
);
`;

// ─────────────────────────────────────────────────────────────
// Types matching chthonic-shell-hook.ps1 JSONL output
// ─────────────────────────────────────────────────────────────

interface TerminalEvent {
  seq?:         number;
  pid?:         number;
  ts?:          string;
  type?:        string;   // "command" | "session_start" | "session_end"
  command?:     string;
  cwd?:         string;
  exit_code?:   number;
  duration_ms?: number;
  shell?:       string;
}

// ─────────────────────────────────────────────────────────────
// DB helpers
// ─────────────────────────────────────────────────────────────

function openDB(stub: boolean): Database {
  const db = stub
    ? new Database(":memory:")
    : new Database(DB_PATH);
  db.exec(DDL);
  return db;
}

// ─────────────────────────────────────────────────────────────
// Drain logic
// ─────────────────────────────────────────────────────────────

function drain(db: Database, verbose = false): { inserted: number; skipped: number } {
  if (!existsSync(JSONL_PATH)) {
    if (verbose) console.log(`[vampire-terminal-history] JSONL not found: ${JSONL_PATH}`);
    return { inserted: 0, skipped: 0 };
  }

  // Load watermark (last processed seq)
  const wmRow = db.prepare("SELECT value FROM _drain_state WHERE key = 'last_seq'").get() as { value: string } | undefined;
  const lastSeq = wmRow ? Number(wmRow.value) : -1;

  const lines = readFileSync(JSONL_PATH, "utf8").split("\n").filter(l => l.trim());

  const insSession = db.prepare(
    "INSERT OR IGNORE INTO terminal_sessions(pid, start_ts, cwd, shell) VALUES (?, ?, ?, ?)"
  );
  const insCmd = db.prepare(
    "INSERT OR REPLACE INTO terminal_commands(seq, pid, ts, command, cwd, exit_code, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?)"
  );
  const insPid = db.prepare(
    "INSERT OR REPLACE INTO terminal_pids(pid, start_ts, cwd, shell) VALUES (?, ?, ?, ?)"
  );

  let inserted = 0;
  let skipped  = 0;
  let newMaxSeq = lastSeq;

  db.transaction(() => {
    for (const line of lines) {
      let evt: TerminalEvent;
      try { evt = JSON.parse(line); }
      catch { skipped++; continue; }

      const seq = evt.seq ?? -1;
      if (seq <= lastSeq) { skipped++; continue; }
      if (seq > newMaxSeq) newMaxSeq = seq;

      const evtType = evt.type ?? "command";

      if (evtType === "session_start" && evt.pid != null) {
        insSession.run(evt.pid, evt.ts ?? null, evt.cwd ?? null, evt.shell ?? null);
        insPid.run(evt.pid, evt.ts ?? null, evt.cwd ?? null, evt.shell ?? null);
        inserted++;
        continue;
      }

      if (evtType === "command" && evt.command) {
        // Ensure session row exists for this pid (may arrive before session_start)
        if (evt.pid != null) {
          insSession.run(evt.pid, evt.ts ?? null, evt.cwd ?? null, null);
        }
        insCmd.run(
          seq,
          evt.pid ?? null,
          evt.ts ?? new Date().toISOString(),
          evt.command,
          evt.cwd ?? null,
          evt.exit_code ?? null,
          evt.duration_ms ?? null
        );
        inserted++;
        if (verbose) console.log(`  [seq=${seq}] ${evt.command?.slice(0, 60)}`);
        continue;
      }

      skipped++;
    }
  })();

  // Persist watermark
  if (newMaxSeq > lastSeq) {
    db.prepare("INSERT OR REPLACE INTO _drain_state(key, value) VALUES ('last_seq', ?)")
      .run(String(newMaxSeq));
  }

  return { inserted, skipped };
}

// ─────────────────────────────────────────────────────────────
// Ingest terminal_pids.json (PID registry from shell hook)
// ─────────────────────────────────────────────────────────────

function drainPids(db: Database): void {
  if (!existsSync(PIDS_PATH)) return;
  let pids: Array<{ pid: number; start_ts?: string; cwd?: string; shell?: string }>;
  try { pids = JSON.parse(readFileSync(PIDS_PATH, "utf8")); }
  catch { return; }
  if (!Array.isArray(pids)) return;

  const ins = db.prepare(
    "INSERT OR REPLACE INTO terminal_pids(pid, start_ts, cwd, shell) VALUES (?, ?, ?, ?)"
  );
  db.transaction(() => {
    for (const p of pids) {
      if (p.pid == null) continue;
      ins.run(p.pid, p.start_ts ?? null, p.cwd ?? null, p.shell ?? null);
    }
  })();
}

// ─────────────────────────────────────────────────────────────
// Stats
// ─────────────────────────────────────────────────────────────

function stats(db: Database): void {
  const tables = ["terminal_sessions", "terminal_commands", "terminal_pids"];
  console.log("[vampire-terminal-history] DB stats:");
  for (const t of tables) {
    const r = db.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get() as { n: number };
    console.log(`  ${t.padEnd(25)} ${r.n} rows`);
  }
  const wm = db.prepare("SELECT value FROM _drain_state WHERE key = 'last_seq'").get() as { value: string } | undefined;
  console.log(`  ${"watermark (last_seq)".padEnd(25)} ${wm?.value ?? "none"}`);
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const watchMode  = args.includes("--watch");
const statsMode  = args.includes("--stats");
const stubCorpus = args.includes("--stub-corpus");
const verbose    = args.includes("--verbose");

const db = openDB(stubCorpus);

if (statsMode) {
  stats(db);
  db.close();
  process.exit(0);
}

// Initial drain
drainPids(db);
const result = drain(db, verbose);
console.log(`[vampire-terminal-history] drained: ${result.inserted} new rows, ${result.skipped} skipped`);
if (!stubCorpus) console.log(`  → ${DB_PATH}`);

if (watchMode) {
  if (!existsSync(JSONL_PATH)) {
    console.warn(`[vampire-terminal-history] --watch: JSONL not found, watching parent dir: ${MANIFEST_DIR}`);
  }
  const watchTarget = existsSync(JSONL_PATH) ? JSONL_PATH : MANIFEST_DIR;
  console.log(`[vampire-terminal-history] --watch active on: ${watchTarget}`);

  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  watch(watchTarget, { persistent: true }, (event, filename) => {
    if (filename && !filename.endsWith("terminal_session.jsonl") && watchTarget !== JSONL_PATH) return;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      drainPids(db);
      const r = drain(db, verbose);
      if (r.inserted > 0) {
        console.log(`[vampire-terminal-history] [${new Date().toISOString()}] hot-reload: ${r.inserted} new rows`);
      }
    }, 250); // 250ms debounce — coalesce rapid writes
  });

  // Keep alive
  process.on("SIGINT",  () => { db.close(); process.exit(0); });
  process.on("SIGTERM", () => { db.close(); process.exit(0); });
} else {
  db.close();
}
