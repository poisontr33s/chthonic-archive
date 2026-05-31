#!/usr/bin/env bun
// @SID: SCRIPT_SONIC_WATCHER_V1
/**
 * sonic_watcher.ts — Turn-boundary Spotify resume for regular Copilot Chat sessions.
 *
 * Watches the active session JSONL transcript for `assistant.turn_end` events.
 * When a turn_end is NOT followed by a turn_start within DEBOUNCE_MS (3s), the
 * agent has truly finished — resume Spotify playback.
 *
 * That's the ONLY action. No pause logic. Music plays the whole time you wait;
 * the resume fires as a "done" signal in case playback drifted or was manually
 * paused mid-session.
 *
 * Prerequisites:
 *   .\scripts\api_pool.ps1 -Load   (sets SPOTIFY_* env vars in shell)
 *   Then start this watcher in the same shell session.
 *
 * Usage:
 *   bun run scripts/sonic_watcher.ts                  # auto-find latest transcript
 *   bun run scripts/sonic_watcher.ts --session <id>   # explicit session ID
 *   bun run scripts/sonic_watcher.ts --poll 1         # poll interval in seconds (default: 1)
 *   bun run scripts/sonic_watcher.ts --debounce 3     # silence window in seconds (default: 3)
 *   bun run scripts/sonic_watcher.ts --verbose
 */

import { existsSync, statSync, openSync, readSync, closeSync, readdirSync } from "fs";
import { join } from "path";
import * as os from "os";
import { SpotifyControl } from "./spotify_control.ts";

// ──────────────────────────────────────────────────────────────
//  Args
// ──────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
function argVal(flag: string): string | null {
  const i = argv.indexOf(flag);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : null;
}
const verbose = argv.includes("--verbose");
const POLL_MS   = parseInt(argVal("--poll")     ?? "1",  10) * 1000;
const DEBOUNCE_MS = parseInt(argVal("--debounce") ?? "3",  10) * 1000;
const explicitSession = argVal("--session");

// ──────────────────────────────────────────────────────────────
//  Paths
// ──────────────────────────────────────────────────────────────
const appdata = process.env["APPDATA"] ?? join(os.homedir(), "AppData", "Roaming");
const wsRoot  = join(appdata, "Code - Insiders", "User", "workspaceStorage");

function findLatestTranscript(): string | null {
  if (!existsSync(wsRoot)) return null;

  let newest: { path: string; mtime: number } | null = null;

  for (const ws of readdirSync(wsRoot)) {
    const transcriptsDir = join(wsRoot, ws, "GitHub.copilot-chat", "transcripts");
    if (!existsSync(transcriptsDir)) continue;
    for (const f of readdirSync(transcriptsDir)) {
      if (!f.endsWith(".jsonl")) continue;
      const p = join(transcriptsDir, f);
      try {
        const mtime = statSync(p).mtimeMs;
        if (!newest || mtime > newest.mtime) newest = { path: p, mtime };
      } catch { /* skip */ }
    }
  }
  return newest?.path ?? null;
}

function resolveTranscriptPath(): string | null {
  if (explicitSession) {
    // Search for a transcript file whose name contains the session ID
    for (const ws of readdirSync(wsRoot)) {
      const transcriptsDir = join(wsRoot, ws, "GitHub.copilot-chat", "transcripts");
      if (!existsSync(transcriptsDir)) continue;
      for (const f of readdirSync(transcriptsDir)) {
        if (f.includes(explicitSession) && f.endsWith(".jsonl")) {
          return join(transcriptsDir, f);
        }
      }
    }
    console.error(`[sonic_watcher] Session not found: ${explicitSession}`);
    return null;
  }
  return findLatestTranscript();
}

// ──────────────────────────────────────────────────────────────
//  Spotify
// ──────────────────────────────────────────────────────────────
const spotify = new SpotifyControl();

async function onAgentDone(): Promise<void> {
  if (verbose) console.log("[sonic_watcher] agent done → resume()");
  await spotify.resume();
  console.log(`[sonic_watcher] ♪ resumed — ${new Date().toLocaleTimeString()}`);
}

// ──────────────────────────────────────────────────────────────
//  Tail logic — byte-offset polling
// ──────────────────────────────────────────────────────────────
let byteOffset = 0;
let partial = "";

function readNewLines(filePath: string): string[] {
  const size = statSync(filePath).size;
  if (size <= byteOffset) return [];

  const chunkLen = size - byteOffset;
  const buf = Buffer.alloc(chunkLen);
  const fd = openSync(filePath, "r");
  const read = readSync(fd, buf, 0, chunkLen, byteOffset);
  closeSync(fd);
  byteOffset += read;

  const text = partial + buf.toString("utf8", 0, read);
  const parts = text.split("\n");
  partial = parts.pop() ?? ""; // last incomplete line
  return parts.filter(l => l.trim().length > 0);
}

// ──────────────────────────────────────────────────────────────
//  Main loop
// ──────────────────────────────────────────────────────────────
const transcriptPath = resolveTranscriptPath();
if (!transcriptPath) {
  console.error("[sonic_watcher] No transcript found. Is a Copilot Chat session active?");
  process.exit(1);
}

// Seek to end — only watch new events from here
byteOffset = existsSync(transcriptPath) ? statSync(transcriptPath).size : 0;
console.log(`[sonic_watcher] watching → ${transcriptPath}`);
console.log(`[sonic_watcher] poll=${POLL_MS}ms  debounce=${DEBOUNCE_MS}ms`);
console.log(`[sonic_watcher] ready — will resume Spotify on agent completion`);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function armDebounce() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    debounceTimer = null;
    await onAgentDone();
  }, DEBOUNCE_MS);
  if (verbose) console.log(`[sonic_watcher] debounce armed (${DEBOUNCE_MS}ms)`);
}

function cancelDebounce() {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
    if (verbose) console.log("[sonic_watcher] debounce cancelled (mid-chain turn_start)");
  }
}

async function poll() {
  if (!existsSync(transcriptPath)) return;

  let lines: string[];
  try { lines = readNewLines(transcriptPath); } catch { return; }

  for (const raw of lines) {
    let entry: { type: string } | null = null;
    try { entry = JSON.parse(raw); } catch { continue; }

    const t = entry?.type ?? "";
    if (verbose) console.log(`[sonic_watcher] event: ${t}`);

    if (t === "assistant.turn_end") {
      armDebounce();
    } else if (t === "assistant.turn_start") {
      // Mid-chain: another tool cycle is starting — cancel pending resume
      cancelDebounce();
    }
  }
}

// Kick off polling loop
setInterval(poll, POLL_MS);
