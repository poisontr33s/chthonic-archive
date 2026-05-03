#!/usr/bin/env bun
// @SID: session-watcher — interval poller: AppData transcripts → repo → GitHub
// Polls workspaceStorage/*/GitHub.copilot-chat/transcripts/*.jsonl on a timer.
// On each tick: if a file grew, copy it. With --push: debounced commit + push.
//
// Strategy: mirrors how the JSONL itself fills in — periodic check, copy if grown.
// No fs.watch, no event plumbing, no Windows ReadDirectoryChangesW edge cases.
//
// Usage:
//   bun run scripts/session-watcher.ts                       # poll every 10s (local mirror)
//   bun run scripts/session-watcher.ts --push                # poll + auto-commit + push (30s debounce)
//   bun run scripts/session-watcher.ts --interval 5          # custom poll interval in seconds
//   bun run scripts/session-watcher.ts --once                # one poll pass, then exit
//   bun run scripts/session-watcher.ts --once --push         # one pass + commit + push, then exit
//
// VS Code task "Session: Watch + Push" has runOn: folderOpen — starts automatically.

import { readFileSync, existsSync, writeFileSync, statSync, readdirSync, mkdirSync, copyFileSync } from "fs";
import { join, basename } from "path";
import * as os from "os";

// ──────────────────────────────────────────────────────────────
//  Config
// ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const onceMode = args.includes("--once");
const pushMode = args.includes("--push");
const verbose = args.includes("--verbose");

const intervalArg = args.indexOf("--interval");
const POLL_MS = (intervalArg >= 0 ? parseInt(args[intervalArg + 1] ?? "10", 10) : 10) * 1000;
const PUSH_DEBOUNCE_MS = 30_000;

const appdata = process.env["APPDATA"] ?? join(os.homedir(), "AppData", "Roaming");
const wsRoot = join(appdata, "Code - Insiders", "User", "workspaceStorage");
const manifestDir = join(import.meta.dir, "..", "manifest");
const sessionsDir = join(manifestDir, "sessions");
const indexPath = join(manifestDir, "sessions_index.json");
const logPath = join(manifestDir, "session_watcher.log");

// ──────────────────────────────────────────────────────────────
//  Types
// ──────────────────────────────────────────────────────────────
interface JEntry {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}
interface MetaEntry {
  sessionId: string; startTime: string; archivedAt: string; lastSyncedAt: string;
  sourcePath: string; workspaceHash: string; workspaceName: string;
  vscodeVersion: string; copilotVersion: string;
  turns: number; lines: number; isLive?: boolean;
}

// ──────────────────────────────────────────────────────────────
//  Logging
// ──────────────────────────────────────────────────────────────
function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  try { writeFileSync(logPath, line + "\n", { flag: "a" }); } catch { /* ignore log write failures */ }
}

function vlog(msg: string) { if (verbose) log(msg); }

// ──────────────────────────────────────────────────────────────
//  Index helpers
// ──────────────────────────────────────────────────────────────
function readIndex(): MetaEntry[] {
  if (!existsSync(indexPath)) return [];
  try { return JSON.parse(readFileSync(indexPath, "utf8")); } catch { return []; }
}

function writeIndex(index: MetaEntry[]) {
  index.sort((a, b) =>
    new Date(b.startTime || b.archivedAt).getTime() - new Date(a.startTime || a.archivedAt).getTime()
  );
  writeFileSync(indexPath, JSON.stringify(index, null, 2), "utf8");
}

// ──────────────────────────────────────────────────────────────
//  Mirror auxiliary artifacts: debug-logs + memory-tool memories
// ──────────────────────────────────────────────────────────────
function mirrorAuxiliaries(tPath: string, sessionId: string, sessionDir: string) {
  // Derive GitHub.copilot-chat base from transcript path
  const copilotChatBase = tPath.replace(/[/\\]transcripts[/\\][^/\\]+\.jsonl$/, "");

  // debug-logs/<sessionId>/main.jsonl → debug.jsonl, models.json → models.json
  const debugDir = join(copilotChatBase, "debug-logs", sessionId);
  if (existsSync(debugDir)) {
    const debugMain = join(debugDir, "main.jsonl");
    const debugModels = join(debugDir, "models.json");
    try { if (existsSync(debugMain)) copyFileSync(debugMain, join(sessionDir, "debug.jsonl")); } catch { /* skip */ }
    try { if (existsSync(debugModels)) copyFileSync(debugModels, join(sessionDir, "models.json")); } catch { /* skip */ }
  }

  // memory-tool/memories/<base64(sessionId)>/*.md → memories/*.md
  const b64Id = Buffer.from(sessionId).toString("base64");
  const memoriesDir = join(copilotChatBase, "memory-tool", "memories", b64Id);
  if (existsSync(memoriesDir)) {
    const memOut = join(sessionDir, "memories");
    mkdirSync(memOut, { recursive: true });
    for (const f of readdirSync(memoriesDir)) {
      if (f.endsWith(".md") || f.endsWith(".json")) {
        try { copyFileSync(join(memoriesDir, f), join(memOut, f)); } catch { /* skip */ }
      }
    }
  }
}

// ──────────────────────────────────────────────────────────────
//  Mirror a single JSONL file to the repo
// ──────────────────────────────────────────────────────────────
const lastSizeMap = new Map<string, number>(); // path → last synced size

function mirrorSession(tPath: string, isLive: boolean): boolean {
  if (!existsSync(tPath)) return false;

  const currentSize = (() => { try { return statSync(tPath).size; } catch { return -1; } })();
  if (currentSize < 0) return false;

  const lastSize = lastSizeMap.get(tPath);
  if (lastSize === currentSize) { vlog(`  skip (unchanged) ${basename(tPath)}`); return false; }
  lastSizeMap.set(tPath, currentSize);

  // Parse for metadata
  const raw = (() => { try { return readFileSync(tPath, "utf8"); } catch { return false; } })();
  if (!raw) return false;

  const lines = raw.split("\n").filter(l => l.trim());
  const entries: JEntry[] = [];
  for (const line of lines) { try { entries.push(JSON.parse(line) as JEntry); } catch { /* skip */ } }

  const sd = entries.find(e => e.type === "session.start")?.data as
    { sessionId?: string; startTime?: string; vscodeVersion?: string; copilotVersion?: string } | undefined;

  const sessionId = (sd?.sessionId ?? basename(tPath).replace(".jsonl", "")).trim();
  if (!sessionId) return false;

  const wHash = tPath.match(/workspaceStorage[\/\\]([^\/\\]+)[\/\\]/)?.[1] ?? "";
  const turnCount = entries.filter(e => e.type === "user.message" || e.type === "assistant.message").length;

  // Derive workspace name from workspace.json
  let workspaceName = "";
  try {
    const wjPath = join(wsRoot, wHash, "workspace.json");
    if (existsSync(wjPath)) {
      const wj = JSON.parse(readFileSync(wjPath, "utf8")) as Record<string, unknown>;
      const uri = String(wj["folder"] ?? wj["workspace"] ?? "");
      const decoded = decodeURIComponent(uri.replace(/^file:\/\/\//i, ""));
      const parts = decoded.replace(/\\/g, "/").split("/");
      const last = parts[parts.length - 1] ?? "";
      workspaceName = last.replace(/\.code-workspace$/i, "") || wHash.slice(0, 8);
    }
  } catch { /* ok */ }

  // Copy JSONL
  const sessionDir = join(sessionsDir, sessionId);
  mkdirSync(sessionDir, { recursive: true });
  copyFileSync(tPath, join(sessionDir, "transcript.jsonl"));

  // Mirror auxiliary artifacts (debug-logs + memory-tool memories)
  mirrorAuxiliaries(tPath, sessionId, sessionDir);

  // Write / update meta.json
  const metaPath = join(sessionDir, "meta.json");
  const existingMeta: Partial<MetaEntry> = existsSync(metaPath)
    ? (() => { try { return JSON.parse(readFileSync(metaPath, "utf8")); } catch { return {}; } })()
    : {};

  const meta: MetaEntry = {
    sessionId,
    startTime: existingMeta.startTime ?? sd?.startTime ?? new Date(statSync(tPath).birthtime).toISOString(),
    archivedAt: existingMeta.archivedAt ?? new Date().toISOString(),
    lastSyncedAt: new Date().toISOString(),
    sourcePath: tPath,
    workspaceHash:  wHash,
    workspaceName:  workspaceName || existingMeta.workspaceName || "",
    vscodeVersion: sd?.vscodeVersion ?? existingMeta.vscodeVersion ?? "",
    copilotVersion: sd?.copilotVersion ?? existingMeta.copilotVersion ?? "",
    turns: turnCount,
    lines: lines.length,
    ...(isLive ? { isLive: true } : {}),
  };
  if (!isLive && existingMeta.isLive) delete (meta as Partial<MetaEntry>).isLive;

  writeFileSync(metaPath, JSON.stringify(meta, null, 2), "utf8");

  // Upsert index
  const index = readIndex();
  const ei = index.findIndex(s => s.sessionId === sessionId);
  if (ei >= 0) index[ei] = meta; else index.push(meta);
  writeIndex(index);

  const status = isLive ? "🔴 live" : "✅ closed";
  log(`${status}  ${sessionId}  (${lines.length} lines, ${turnCount} turns)`);
  return true;
}

// ──────────────────────────────────────────────────────────────
//  Discover all transcript files
// ──────────────────────────────────────────────────────────────
function allTranscripts(): Array<{ path: string; mtime: number }> {
  if (!existsSync(wsRoot)) return [];
  const files: Array<{ path: string; mtime: number }> = [];
  for (const hash of readdirSync(wsRoot)) {
    const tDir = join(wsRoot, hash, "GitHub.copilot-chat", "transcripts");
    if (!existsSync(tDir)) continue;
    for (const f of readdirSync(tDir)) {
      if (!f.endsWith(".jsonl")) continue;
      const p = join(tDir, f);
      try { files.push({ path: p, mtime: statSync(p).mtime.getTime() }); } catch { /* skip */ }
    }
  }
  return files.sort((a, b) => b.mtime - a.mtime);
}

// ──────────────────────────────────────────────────────────────
//  Snapshot all (--once mode or initial sync)
// ──────────────────────────────────────────────────────────────
function snapshotAll(): number {
  const files = allTranscripts();
  if (files.length === 0) { log("No transcripts found."); return 0; }
  const livePath = files[0].path;
  let changed = 0;
  for (const { path: tPath } of files) {
    if (mirrorSession(tPath, tPath === livePath)) changed++;
  }
  if (changed > 0) log(`Poll: ${changed} session(s) updated (${files.length} total).`);
  else vlog(`Poll: no changes (${files.length} sessions checked).`);
  return changed;
}

// ──────────────────────────────────────────────────────────────
//  Git siphon helpers (--push mode)
// ──────────────────────────────────────────────────────────────
const repoRoot = join(import.meta.dir, "..");

async function runGit(...gitArgs: string[]): Promise<{ ok: boolean; out: string }> {
  const proc = Bun.spawn(["git", "-C", repoRoot, ...gitArgs], {
    stdout: "pipe",
    stderr: "pipe",
  });
  const out = await new Response(proc.stdout).text();
  const err = await new Response(proc.stderr).text();
  const code = await proc.exited;
  return { ok: code === 0, out: (out + err).trim() };
}

async function siphonToGitHub() {
  log("  siphon: staging sessions...");
  const stage = await runGit("add", "-f",
    join("manifest", "sessions"),
    join("manifest", "sessions_index.json"),
  );
  if (!stage.ok) { log(`  siphon: stage failed: ${stage.out}`); return; }

  const status = await runGit("diff", "--cached", "--name-only");
  if (!status.out.trim()) {
    vlog("  siphon: nothing new to commit");
    if (onceMode) process.exit(0);
    return;
  }

  const msg = `chore(sessions): auto-siphon ${new Date().toISOString()}\n\nCo-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>`;
  const commit = await runGit("commit", "--no-verify", "-m", msg);
  if (!commit.ok) { log(`  siphon: commit failed: ${commit.out}`); if (onceMode) process.exit(1); return; }

  log("  siphon: pushing to origin...");
  const push = await runGit("push");
  if (push.ok) {
    log(`  siphon: ✅ pushed — ${status.out.trim().split("\n").length} file(s)`);
  } else {
    log(`  siphon: ⚠️ push failed: ${push.out}`);
  }
  if (onceMode) process.exit(push.ok ? 0 : 1);
}

// ──────────────────────────────────────────────────────────────
//  --once: one pass, then exit (with optional push)
// ──────────────────────────────────────────────────────────────
if (onceMode) {
  log(`session-watcher: one-shot pass${pushMode ? " + push" : ""}`);
  snapshotAll();
  if (pushMode) {
    await siphonToGitHub(); // exits inside siphonToGitHub when onceMode=true
  }
  process.exit(0);
}

// ──────────────────────────────────────────────────────────────
//  Poll loop: tick every POLL_MS, mirror any grown files
//  Push debounce: after a tick with changes, push 30s later
//  (reset on each tick that finds more changes)
// ──────────────────────────────────────────────────────────────
log(`session-watcher: polling every ${POLL_MS / 1000}s${pushMode ? ` — push debounce ${PUSH_DEBOUNCE_MS / 1000}s` : ""}`);
log(`  Source: ${wsRoot}`);
log(`  Target: ${sessionsDir}`);

let pushTimer: ReturnType<typeof setTimeout> | null = null;

function armPush() {
  if (pushTimer) clearTimeout(pushTimer);
  pushTimer = setTimeout(() => { pushTimer = null; siphonToGitHub(); }, PUSH_DEBOUNCE_MS);
}

async function tick() {
  const changed = snapshotAll();
  if (pushMode && changed > 0) armPush();
}

// Initial tick immediately, then on interval
await tick();
setInterval(tick, POLL_MS);

