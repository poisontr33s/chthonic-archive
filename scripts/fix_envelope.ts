#!/usr/bin/env bun
// @SID: SCRIPT_FIX_ENVELOPE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: scripts/fix_envelope.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * scripts/fix_envelope.ts — narrow auto-fixers for two pre-commit gates, so they self-heal
 * (via ci/run.ts --heal) instead of merely rebuking.
 *
 *   --shebang : relocate a DISPLACED shebang (on line 2 instead of line 1) back to line 1 in
 *               staged .ts / .sh / .rb files. (.py shebang+encoding is owned by the
 *               python-headers fixer, scripts/fix_headers.py — not duplicated here.)
 *
 *   --uv-run  : prepend `uv run` to line-leading bare `python`/`python3` (and `& python`) in
 *               staged .sh / .ps1 SHELL files only — the safe subset. Bare python inside
 *               .py/.ts (docstring usage examples, spawn/subprocess arg arrays) is deliberately
 *               NOT rewritten (mechanical edits would corrupt docs or need restructuring);
 *               those stay manual.
 *
 * Scope: --staged (git ACM) | --all (tracked) | explicit paths. Non-destructive + idempotent;
 * does NOT auto-stage (the --heal flow / conductor re-stages).
 */

import { execSync } from "child_process";
import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");
const SHEBANG = process.argv.includes("--shebang");
const UV_RUN = process.argv.includes("--uv-run");
const STAGED = process.argv.includes("--staged");
const ALL = process.argv.includes("--all");
const EXPLICIT = process.argv.slice(2).filter((a) => !a.startsWith("--"));

const TS_SHEBANG = "#!/usr/bin/env bun";
const RB_SHEBANG = "#!/usr/bin/env ruby";
const SH_SHEBANGS = new Set(["#!/usr/bin/env bash", "#!/bin/bash", "#!/usr/bin/env sh", "#!/bin/sh"]);

const SHEBANG_EXTS = new Set([".ts", ".sh", ".rb"]);
const UVRUN_EXTS = new Set([".sh", ".ps1"]);

function ext(f: string): string {
  return f.slice(f.lastIndexOf("."));
}

function inScope(f: string): boolean {
  const e = ext(f);
  if (SHEBANG && SHEBANG_EXTS.has(e)) return true;
  if (UV_RUN && UVRUN_EXTS.has(e)) return true;
  return false;
}

function gitList(args: string): string[] {
  try {
    return execSync(args, { encoding: "utf8", cwd: REPO_ROOT }).split("\n").filter(Boolean).filter(inScope);
  } catch {
    return [];
  }
}

/** Move a shebang sitting on line 2 up to line 1. Returns true if it changed anything. */
function relocateShebang(lines: string[], e: string): boolean {
  const l1 = (lines[0] ?? "").trimEnd();
  const l2 = (lines[1] ?? "").trimEnd();
  const displaced =
    (e === ".ts" && l1 !== TS_SHEBANG && l2 === TS_SHEBANG) ||
    (e === ".rb" && l1 !== RB_SHEBANG && l2 === RB_SHEBANG) ||
    (e === ".sh" && !SH_SHEBANGS.has(l1) && SH_SHEBANGS.has(l2));
  if (!displaced) return false;
  const shebang = lines[1];
  lines.splice(1, 1);
  lines.unshift(shebang);
  return true;
}

/** Prepend `uv run` to line-leading bare python invocations in shell files. */
function fixUvRun(lines: string[]): boolean {
  let changed = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const s = line.trimStart();
    if (!s || s.startsWith("#") || /\buv\b/.test(line)) continue;
    if (/^\s*python3?\s+\S/.test(line)) {
      lines[i] = line.replace(/^(\s*)(python3?)\b/, "$1uv run $2");
      changed = true;
    } else if (/&\s+python3?\b/.test(line)) {
      lines[i] = line.replace(/&\s+(python3?)\b/, "& uv run $1");
      changed = true;
    }
  }
  return changed;
}

type Action = { file: string; kind: "fixed" | "ok" | "unreadable" };

function fixFile(rel: string): Action {
  const absPath = resolve(REPO_ROOT, rel);
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return { file: rel, kind: "unreadable" };
  }
  const eol = content.includes("\r\n") ? "\r\n" : "\n";
  const lines = content.split(/\r?\n/);
  const e = ext(rel);

  let changed = false;
  if (SHEBANG && SHEBANG_EXTS.has(e)) changed = relocateShebang(lines, e) || changed;
  if (UV_RUN && UVRUN_EXTS.has(e)) changed = fixUvRun(lines) || changed;

  if (!changed) return { file: rel, kind: "ok" };
  writeFileSync(absPath, lines.join(eol));
  return { file: rel, kind: "fixed" };
}

if (!SHEBANG && !UV_RUN) {
  console.error("[fix-envelope] specify a mode: --shebang and/or --uv-run");
  process.exit(2);
}

const targets = (
  EXPLICIT.length > 0
    ? EXPLICIT
    : ALL
      ? gitList("git ls-files")
      : STAGED
        ? gitList("git diff --cached --name-only --diff-filter=ACM")
        : []
).filter(inScope);

if (targets.length === 0) {
  console.log("[fix-envelope] no in-scope targets. Pass --staged, --all, or explicit paths.");
  process.exit(0);
}

const actions = targets.map(fixFile);
let fixed = 0;
for (const a of actions) {
  if (a.kind === "fixed") {
    fixed++;
    console.log(`[fix-envelope] fixed  ${a.file}`);
  } else if (a.kind === "unreadable" && (ALL || EXPLICIT.length > 0)) {
    console.log(`[fix-envelope] skip   ${a.file} (unreadable)`);
  }
}
console.log(`\n[fix-envelope] ${fixed} file(s) fixed. Review + re-stage.`);
process.exit(0);
