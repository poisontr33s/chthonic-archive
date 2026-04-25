#!/usr/bin/env bun
// @SID: TERMINAL_SESSION_QUERY_V2

// ╔════════════════════════════════════════════════════════════════════════════
// ║ scripts/terminal_session_query.ts
// ║ Query tool for chthonic terminal session JSONL log.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Reads manifest/terminal_session.jsonl + manifest/terminal_pids.json
// ║ and produces structured output — no terminal buffer scraping needed.
// ║
// ║ Flags:
// ║   --list-pids              List all live (currently running) PIDs
// ║   --pid <n>                Filter to entries from PID n
// ║   --sid <id>               Filter to session ID (8-char prefix)
// ║   --last <n>               Last N command entries (default: 20)
// ║   --minutes <n>            Entries from last N minutes
// ║   --grep <pattern>         Case-insensitive substring filter on command
// ║   --exit-code <n>          Only entries with this exit code
// ║   --failed                 Only failed commands (exit_code != 0)
// ║   --cwd <path>             Only entries with this cwd substring
// ║   --json                   Output raw JSON array (default: table)
// ║   --summary                One-line summary per PID
// ║   --report                 Full structured JSON report (pids + entries)
// ║   --snapshot               Emit compact tracked artifact to
// ║                            manifest/terminal_session_snapshot.json
// ║                            (persists session data across JSONL wipes;
// ║                            run at trainstop time or pre-commit)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");
const SESSION_LOG = resolve(REPO_ROOT, "manifest", "terminal_session.jsonl");
const PID_REGISTRY = resolve(REPO_ROOT, "manifest", "terminal_pids.json");

// ── Arg parsing ───────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const flag = (name: string) => args.includes(name);
const opt = (name: string): string | null => {
  const i = args.indexOf(name);
  return i !== -1 && i + 1 < args.length ? args[i + 1] : null;
};

const LIST_PIDS = flag("--list-pids");
const PID_FILTER = opt("--pid") ? Number(opt("--pid")) : null;
const SID_FILTER = opt("--sid");
const LAST_N = opt("--last") ? Number(opt("--last")) : 20;
const MINUTES = opt("--minutes") ? Number(opt("--minutes")) : null;
const GREP = opt("--grep");
const EXIT_CODE = opt("--exit-code") ? Number(opt("--exit-code")) : null;
const FAILED = flag("--failed");
const CWD_FILTER = opt("--cwd");
const JSON_OUT = flag("--json");
const SUMMARY = flag("--summary");
const REPORT = flag("--report");
const SNAPSHOT = flag("--snapshot");

// ── Types ─────────────────────────────────────────────────────────────────────

interface SessionEntry {
  ts: string;
  pid: number;
  sid: string;
  cwd: string;
  command: string;
  exit_code: number | null;
  success?: boolean;
  duration_ms?: number | null;
  seq: number;
  _patch?: boolean;
}

interface PidInfo {
  pid: number;
  session_id: string;
  start_ts: string;
  cwd: string;
  title?: string;
  term?: string;
  vscode_pid?: number | null;
}

// ── Readers ───────────────────────────────────────────────────────────────────

function readPidRegistry(): Record<string, PidInfo> {
  if (!existsSync(PID_REGISTRY)) return {};
  try {
    return JSON.parse(readFileSync(PID_REGISTRY, "utf-8"));
  } catch {
    return {};
  }
}

function readSessionLog(): SessionEntry[] {
  if (!existsSync(SESSION_LOG)) return [];
  const lines = readFileSync(SESSION_LOG, "utf-8")
    .split("\n")
    .filter((l) => l.trim());

  // Merge patch entries: last entry for each seq wins
  const bySeq = new Map<number, SessionEntry>();
  for (const line of lines) {
    try {
      const entry: SessionEntry = JSON.parse(line);
      const existing = bySeq.get(entry.seq);
      // Patch entries (with exit_code filled in) supersede the initial entry
      if (!existing || entry._patch) {
        // Clear _patch flag on the winner so it doesn't get filtered downstream
        bySeq.set(entry.seq, { ...entry, _patch: false });
      }
    } catch {
      // skip malformed lines
    }
  }
  return Array.from(bySeq.values()).sort((a, b) => a.seq - b.seq);
}

// ── Filters ───────────────────────────────────────────────────────────────────

function applyFilters(entries: SessionEntry[]): SessionEntry[] {
  let result = entries.filter((e) => !e._patch); // never show patch markers directly

  if (PID_FILTER !== null) result = result.filter((e) => e.pid === PID_FILTER);
  if (SID_FILTER) result = result.filter((e) => e.sid.startsWith(SID_FILTER));
  if (MINUTES !== null) {
    const cutoff = new Date(Date.now() - MINUTES * 60 * 1000).toISOString();
    result = result.filter((e) => e.ts >= cutoff);
  }
  if (GREP) {
    const pat = GREP.toLowerCase();
    result = result.filter((e) => e.command.toLowerCase().includes(pat));
  }
  if (EXIT_CODE !== null) result = result.filter((e) => e.exit_code === EXIT_CODE);
  if (FAILED) result = result.filter((e) => e.exit_code !== null && e.exit_code !== 0);
  if (CWD_FILTER) {
    const pat = CWD_FILTER.toLowerCase();
    result = result.filter((e) => e.cwd.toLowerCase().includes(pat));
  }

  return result.slice(-LAST_N);
}

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtDuration(ms: number | null | undefined): string {
  if (ms == null) return "  -  ";
  if (ms < 1000) return `${ms}ms`.padStart(6);
  return `${(ms / 1000).toFixed(1)}s`.padStart(6);
}

function fmtExitCode(ec: number | null): string {
  if (ec === null) return " ?  ";
  if (ec === 0) return " ✓  ";
  return ` ✗${ec}`.padStart(4);
}

function fmtTs(ts: string): string {
  // Show HH:MM:SS only
  return ts.substring(11, 19);
}

function printTable(entries: SessionEntry[]): void {
  if (entries.length === 0) {
    console.log("[terminal-session-query] No matching entries.");
    return;
  }
  const header = `${"TIME".padEnd(10)}${"PID".padEnd(8)}${"EC".padEnd(6)}${"DUR".padEnd(8)}${"CWD".padEnd(30)}COMMAND`;
  console.log(header);
  console.log("─".repeat(header.length));
  for (const e of entries) {
    const cwd = (e.cwd.length > 28 ? "…" + e.cwd.slice(-27) : e.cwd).padEnd(30);
    const cmd = e.command.length > 80 ? e.command.substring(0, 79) + "…" : e.command;
    console.log(
      `${fmtTs(e.ts).padEnd(10)}${String(e.pid).padEnd(8)}${fmtExitCode(e.exit_code).padEnd(6)}${fmtDuration(e.duration_ms).padEnd(8)}${cwd}  ${cmd}`
    );
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

const pids = readPidRegistry();

if (LIST_PIDS) {
  const entries = Object.values(pids);
  if (entries.length === 0) {
    console.log("[terminal-session-query] No PIDs registered. Source chthonic-shell-hook.ps1 first.");
    process.exit(0);
  }
  if (JSON_OUT) {
    console.log(JSON.stringify(entries, null, 2));
  } else {
    console.log(`${"PID".padEnd(8)}${"SID".padEnd(12)}${"TERM".padEnd(12)}${"START".padEnd(22)}CWD`);
    console.log("─".repeat(80));
    for (const p of entries) {
      const started = p.start_ts.substring(0, 19).replace("T", " ");
      const term = (p.term ?? "?").substring(0, 10).padEnd(12);
      const cwd = p.cwd.length > 30 ? "…" + p.cwd.slice(-29) : p.cwd;
      console.log(`${String(p.pid).padEnd(8)}${p.session_id.substring(0, 8).padEnd(12)}${term}${started.padEnd(22)}${cwd}`);
    }
  }
  process.exit(0);
}

const allEntries = readSessionLog();
const filtered = applyFilters(allEntries);

if (REPORT) {
  const report = {
    generated: new Date().toISOString(),
    log_path: SESSION_LOG,
    total_entries: allEntries.length,
    filtered_entries: filtered.length,
    pids: Object.values(pids),
    entries: filtered,
  };
  console.log(JSON.stringify(report, null, 2));
  process.exit(0);
}

if (SUMMARY) {
  // Group by PID, show last command per PID
  const groups = new Map<number, SessionEntry[]>();
  for (const e of allEntries) {
    const group = groups.get(e.pid) ?? [];
    group.push(e);
    groups.set(e.pid, group);
  }
  for (const [pid, es] of groups) {
    const pidInfo = pids[String(pid)];
    const last = es[es.length - 1];
    const count = es.length;
    const failed = es.filter((x) => x.exit_code !== null && x.exit_code !== 0).length;
    console.log(`PID ${pid} [${pidInfo?.session_id?.substring(0, 8) ?? "?"}] ${count} cmds, ${failed} failed — last: ${last.command.substring(0, 60)}`);
  }
  process.exit(0);
}

if (JSON_OUT) {
  console.log(JSON.stringify(filtered, null, 2));
} else {
  printTable(filtered);
}

// ── Snapshot ──────────────────────────────────────────────────────────────────
// Emits a compact, tracked artifact to manifest/terminal_session_snapshot.json.
// Run at trainstop time or pre-commit to persist session archaeology across
// JSONL wipes. The JSONL is gitignored (ephemeral); the snapshot is tracked.
//
// Schema: session stats + per-PID summary + last 30 complete entries (commands only).
// Designed to be small enough to commit without noise.

if (SNAPSHOT) {
  const SNAPSHOT_PATH = resolve(REPO_ROOT, "manifest", "terminal_session_snapshot.json");
  const complete = allEntries.filter((e) => e.exit_code !== null);
  const failed = complete.filter((e) => e.exit_code !== 0);
  const durations = complete.map((e) => e.duration_ms).filter((d): d is number => d != null);
  const avgDur = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : null;
  const maxDur = durations.length ? Math.max(...durations) : null;

  // Per-PID summary
  const pidSummary: Record<string, object> = {};
  for (const [pidStr, info] of Object.entries(pids)) {
    const pidNum = Number(pidStr);
    const pidEntries = complete.filter((e) => e.pid === pidNum);
    const pidFailed = pidEntries.filter((e) => e.exit_code !== 0);
    pidSummary[pidStr] = {
      session_id: info.session_id,
      start_ts: info.start_ts,
      term: info.term ?? null,
      cwd: info.cwd,
      commands: pidEntries.length,
      failed: pidFailed.length,
      success_rate: pidEntries.length ? Math.round((1 - pidFailed.length / pidEntries.length) * 10000) / 10000 : null,
    };
  }

  // Last 30 complete entries — compact form (command, exit_code, duration_ms, ts, pid)
  const recentEntries = complete.slice(-30).map((e) => ({
    seq: e.seq,
    ts: e.ts,
    pid: e.pid,
    sid: e.sid,
    cwd: e.cwd,
    command: e.command.length > 120 ? e.command.substring(0, 119) + "…" : e.command,
    exit_code: e.exit_code,
    duration_ms: e.duration_ms ?? null,
  }));

  const snapshot = {
    schema_version: "1.0",
    snapshot_ts: new Date().toISOString(),
    source: "manifest/terminal_session.jsonl",
    stats: {
      total_complete: complete.length,
      succeeded: complete.length - failed.length,
      failed: failed.length,
      success_rate: complete.length ? Math.round((1 - failed.length / complete.length) * 10000) / 10000 : null,
      avg_duration_ms: avgDur,
      max_duration_ms: maxDur,
    },
    pid_summary: pidSummary,
    recent_entries: recentEntries,
  };

  writeFileSync(SNAPSHOT_PATH, JSON.stringify(snapshot, null, 2), "utf-8");
  console.log(`[terminal-session-query] Snapshot written: ${SNAPSHOT_PATH}`);
  console.log(`  complete=${complete.length}  failed=${failed.length}  pids=${Object.keys(pids).length}  recent=${recentEntries.length}`);
  process.exit(0);
}
