#!/usr/bin/env bun
// @SID: session-watcher — real-time mirror of Copilot Chat transcripts → repo
// Watches all workspaceStorage/*/GitHub.copilot-chat/transcripts/*.jsonl
// and copies every write event to manifest/sessions/<sessionId>/transcript.jsonl
//
// Usage:
//   bun run scripts/session-watcher.ts           # watch + mirror forever
//   bun run scripts/session-watcher.ts --once    # snapshot all known sessions now, then exit
//
// VS Code task: "Chthonic: Session Watcher (auto-start)" — runOn: folderOpen

import { readFileSync, existsSync, writeFileSync, statSync, readdirSync, mkdirSync, copyFileSync, watch } from "fs";
import { join, basename } from "path";
import * as os from "os";

// ──────────────────────────────────────────────────────────────
//  Config
// ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const onceMode = args.includes("--once");
const verbose = args.includes("--verbose");

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
  sourcePath: string; workspaceHash: string;
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
//  Mirror a single JSONL file to the repo
// ──────────────────────────────────────────────────────────────
const lastSizeMap = new Map<string, number>(); // path → last synced size

function mirrorSession(tPath: string, isLive: boolean) {
  if (!existsSync(tPath)) return;

  const currentSize = (() => { try { return statSync(tPath).size; } catch { return -1; } })();
  if (currentSize < 0) return;

  // Skip if nothing changed (for polling)
  const lastSize = lastSizeMap.get(tPath);
  if (lastSize === currentSize) { vlog(`  skip (unchanged) ${basename(tPath)}`); return; }
  lastSizeMap.set(tPath, currentSize);

  // Parse for metadata
  const raw = (() => { try { return readFileSync(tPath, "utf8"); } catch { return null; } })();
  if (!raw) return;

  const lines = raw.split("\n").filter(l => l.trim());
  const entries: JEntry[] = [];
  for (const line of lines) { try { entries.push(JSON.parse(line) as JEntry); } catch { /* skip */ } }

  const sd = entries.find(e => e.type === "session.start")?.data as
    { sessionId?: string; startTime?: string; vscodeVersion?: string; copilotVersion?: string } | undefined;

  const sessionId = (sd?.sessionId ?? basename(tPath).replace(".jsonl", "")).trim();
  if (!sessionId) return;

  const wHash = tPath.match(/workspaceStorage[\/\\]([^\/\\]+)[\/\\]/)?.[1] ?? "";
  const turnCount = entries.filter(e => e.type === "user.message" || e.type === "assistant.message").length;

  // Copy JSONL
  const sessionDir = join(sessionsDir, sessionId);
  mkdirSync(sessionDir, { recursive: true });
  copyFileSync(tPath, join(sessionDir, "transcript.jsonl"));

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
    workspaceHash: wHash,
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
function snapshotAll() {
  const files = allTranscripts();
  if (files.length === 0) { log("No transcripts found."); return; }
  const livePath = files[0].path;
  for (const { path: tPath } of files) {
    mirrorSession(tPath, tPath === livePath);
  }
  log(`Snapshot complete. ${files.length} sessions mirrored.`);
}

// ──────────────────────────────────────────────────────────────
//  --once: snapshot and exit
// ──────────────────────────────────────────────────────────────
if (onceMode) {
  log("session-watcher: snapshot mode");
  snapshotAll();
  process.exit(0);
}

// ──────────────────────────────────────────────────────────────
//  Watch mode: initial sync + fs.watch on each transcripts dir
// ──────────────────────────────────────────────────────────────
log("session-watcher: starting — watching for transcript changes");
log(`  Source: ${wsRoot}`);
log(`  Target: ${sessionsDir}`);

// Initial sync of all known sessions
snapshotAll();

// Watch each transcripts directory (recursive watch on Windows works via fs.watch)
const watchedDirs = new Set<string>();

function watchTranscriptsDir(tDir: string) {
  if (watchedDirs.has(tDir)) return;
  watchedDirs.add(tDir);
  vlog(`  watching: ${tDir}`);
  try {
    watch(tDir, { persistent: true }, (_event, filename) => {
      if (!filename || !filename.endsWith(".jsonl")) return;
      const tPath = join(tDir, filename);

      // Determine if live (most recently modified)
      const files = allTranscripts();
      const isLive = files.length > 0 && files[0].path === tPath;
      mirrorSession(tPath, isLive);
    });
  } catch (err) {
    log(`  watch error on ${tDir}: ${err}`);
  }
}

// Watch existing dirs now
if (existsSync(wsRoot)) {
  for (const hash of readdirSync(wsRoot)) {
    const tDir = join(wsRoot, hash, "GitHub.copilot-chat", "transcripts");
    if (existsSync(tDir)) watchTranscriptsDir(tDir);
  }
}

// Also watch the workspaceStorage root for new workspace hashes appearing
// (new workspace opened = new hash dir with transcripts subdir)
if (existsSync(wsRoot)) {
  watch(wsRoot, { persistent: true }, (_event, hash) => {
    if (!hash) return;
    const tDir = join(wsRoot, hash, "GitHub.copilot-chat", "transcripts");
    if (existsSync(tDir)) watchTranscriptsDir(tDir);
  });
}

log("session-watcher: ready — Ctrl+C to stop");
// Process stays alive via persistent watchers
