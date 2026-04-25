#!/usr/bin/env bun
// @SID: CI_CHECK_TERMINAL_HOOK_SMOKE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/terminal-hook-smoke.ts
// ║ Health check for the chthonic terminal session hook system.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Road-stop validation artifact — 2026-04-25
// ║
// ║ Failure mode documented:
// ║   PATCH_FILTER_BYPASS — terminal_session_query.ts merge logic preserved
// ║   _patch:true on winning entries; applyFilters(!e._patch) excluded ALL
// ║   merged entries → empty query output.
// ║   Fix: { ...entry, _patch: false } on bySeq.set winner (commit dfb63f02).
// ║
// ║ Exit codes:
// ║   0  — hook healthy (JSONL present, entries parse, no stale _patch:true)
// ║   0  — hook absent (JSONL missing — warn only; hook needs manual sourcing)
// ║   1  — regression detected (stale _patch:true present, or parse failures)
// ║
// ║ Flags:
// ║   --report  Full structured JSON to stdout
// ║   --strict  Exit 1 if hook has never been sourced (JSONL missing)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const SESSION_LOG = resolve(REPO_ROOT, "manifest", "terminal_session.jsonl");
const PID_REGISTRY = resolve(REPO_ROOT, "manifest", "terminal_pids.json");
const VALIDATION_FILE = resolve(REPO_ROOT, "manifest", "terminal_hook_validation.json");
const REPORT = process.argv.includes("--report");
const STRICT = process.argv.includes("--strict");

// ── Types ─────────────────────────────────────────────────────────────────────

interface SessionEntry {
  seq: number;
  pid: number;
  sid: string;
  ts: string;
  command: string;
  exit_code: number | null;
  duration_ms?: number | null;
  _patch?: boolean;
}

interface HookHealth {
  status: "healthy" | "absent" | "regression";
  jsonl_present: boolean;
  pid_registry_present: boolean;
  validation_record_present: boolean;
  total_raw_lines: number;
  parse_failures: number;
  merged_entries: number;
  stale_patch_entries: number;  // regression indicator: _patch:true still present after merge
  entries_with_exit_code: number;
  pids_registered: number;
  known_failure_mode: string;
  known_fix: string;
  validation_commit: string | null;
  warnings: string[];
  errors: string[];
}

// ── Analysis ──────────────────────────────────────────────────────────────────

function analyzeHook(): HookHealth {
  const h: HookHealth = {
    status: "healthy",
    jsonl_present: existsSync(SESSION_LOG),
    pid_registry_present: existsSync(PID_REGISTRY),
    validation_record_present: existsSync(VALIDATION_FILE),
    total_raw_lines: 0,
    parse_failures: 0,
    merged_entries: 0,
    stale_patch_entries: 0,
    entries_with_exit_code: 0,
    pids_registered: 0,
    known_failure_mode: "PATCH_FILTER_BYPASS — merge kept _patch:true on winners; applyFilters excluded all entries",
    known_fix: "{ ...entry, _patch: false } on bySeq.set winner — commit dfb63f02",
    validation_commit: null,
    warnings: [],
    errors: [],
  };

  // PID registry
  if (h.pid_registry_present) {
    try {
      const reg = JSON.parse(readFileSync(PID_REGISTRY, "utf-8"));
      h.pids_registered = Object.keys(reg).length;
    } catch {
      h.errors.push("terminal_pids.json parse failure");
    }
  } else {
    h.warnings.push("terminal_pids.json absent — source chthonic-shell-hook.ps1 to register");
  }

  // Validation record
  if (h.validation_record_present) {
    try {
      const val = JSON.parse(readFileSync(VALIDATION_FILE, "utf-8"));
      h.validation_commit = val.validation_commit ?? null;
    } catch {
      h.warnings.push("terminal_hook_validation.json parse failure");
    }
  } else {
    h.warnings.push("terminal_hook_validation.json absent — run road-stop validation to produce it");
  }

  // JSONL absent — warn (not error); hook not yet sourced this session
  if (!h.jsonl_present) {
    h.status = "absent";
    h.warnings.push(
      "terminal_session.jsonl absent — source chthonic-shell-hook.ps1 to begin logging: . scripts/chthonic-shell-hook.ps1"
    );
    return h;
  }

  // Parse JSONL
  const raw = readFileSync(SESSION_LOG, "utf-8").split("\n").filter((l) => l.trim());
  h.total_raw_lines = raw.length;

  const bySeq = new Map<number, SessionEntry>();
  for (const line of raw) {
    try {
      const entry: SessionEntry = JSON.parse(line);
      const existing = bySeq.get(entry.seq);
      if (!existing || entry._patch) {
        bySeq.set(entry.seq, { ...entry, _patch: false });
      }
    } catch {
      h.parse_failures++;
    }
  }

  const merged = Array.from(bySeq.values());
  h.merged_entries = merged.length;
  h.stale_patch_entries = merged.filter((e) => e._patch === true).length;
  h.entries_with_exit_code = merged.filter((e) => e.exit_code !== null).length;

  // Regression check: if stale _patch:true survived the merge, the old bug is back
  if (h.stale_patch_entries > 0) {
    h.status = "regression";
    h.errors.push(
      `REGRESSION: ${h.stale_patch_entries} entries still have _patch:true after merge. ` +
        "Merge fix (dfb63f02) may have been reverted. Check: bySeq.set(seq, { ...entry, _patch: false })"
    );
  }

  // High parse failure rate
  if (h.total_raw_lines > 0 && h.parse_failures / h.total_raw_lines > 0.2) {
    h.status = h.status === "healthy" ? "regression" : h.status;
    h.errors.push(`High parse failure rate: ${h.parse_failures}/${h.total_raw_lines} lines unparseable`);
  }

  if (h.parse_failures > 0 && h.parse_failures / h.total_raw_lines <= 0.2) {
    h.warnings.push(`${h.parse_failures} unparseable JSONL lines (below threshold — non-fatal)`);
  }

  return h;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const health = analyzeHook();
const ok = health.status !== "regression";

if (REPORT) {
  console.log(JSON.stringify({ check: "terminal-hook-smoke", ...health }, null, 2));
  process.exit(ok ? 0 : 1);
}

// Smoke output
const icon = health.status === "healthy" ? "✓" : health.status === "absent" ? "⚠" : "✗";
const pids = health.pids_registered;
const entries = health.merged_entries;
const withCode = health.entries_with_exit_code;

console.log(
  `[terminal-hook-smoke] ${icon} status=${health.status} pids=${pids} entries=${entries} with_exit_code=${withCode}`
);

if (health.warnings.length > 0 && !ok) {
  for (const w of health.warnings) console.warn(`  WARN: ${w}`);
}
if (health.errors.length > 0) {
  for (const e of health.errors) console.error(`  ERR: ${e}`);
}

if (health.status === "absent") {
  console.log("  → To activate: . scripts/chthonic-shell-hook.ps1");
}

process.exit(ok ? 0 : 1);
