#!/usr/bin/env bun
// @SID: SCRIPT_MCP_SONIC_V1

/**
 * mcp-sonic — Bun stdio MCP server for Spotify playback signals.
 *
 * Exposes Spotify state and playback control as MCP tools so the agent
 * can call sonic_signal() at the end of each response — no file watcher,
 * no polling loop, no JSONL parsing. The agent IS the turn boundary.
 *
 * Tools:
 *   sonic_signal   — agent calls this when done; resumes Spotify if paused
 *   sonic_status   — returns current playback state (so agent knows if user is listening)
 *   sonic_pause    — explicit pause (for agent to use if about to do something disruptive)
 *
 * Credentials: reads SPOTIFY_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN from process.env.
 * Load via: .\scripts\api_pool.ps1 -Load   (writes them into the shell that spawns the MCP server)
 *
 * Registration (.mcp.json):
 *   "sonic": {
 *     "type": "stdio",
 *     "command": "C:/Users/eldno/.bun/bin/bun.exe",
 *     "args": ["run", "C:/Users/eldno/chthonic-archive/scripts/mcp-sonic.ts"],
 *     "cwd": "C:/Users/eldno/chthonic-archive",
 *     "env": { "SPOTIFY_CLIENT_ID": "...", "SPOTIFY_CLIENT_SECRET": "...", "SPOTIFY_REFRESH_TOKEN": "..." }
 *   }
 *
 * sonic_signal semantics:
 *   - If Spotify is paused/stopped → resume() (user paused to read; signal them it's done)
 *   - If Spotify is already playing → still resume() — idempotent, Spotify ignores it
 *   - Returns current track name so agent can report it if useful
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { SpotifyControl } from "./spotify_control.ts";
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "fs";
import { join } from "path";

// ──────────────────────────────────────────────────────────────
//  Sonic window (real loopback signal from sonic-daemon)
// ──────────────────────────────────────────────────────────────

const WINDOW_PATH = join(process.cwd(), "manifest", "sonic_window.json");

/** The temporal sense: the daemon's model of the sonic environment over time. */
interface Temporal {
  phase?: { character: string; secs: number };
  trend?: { energy_30s?: string; energy_5m?: string; brightness_30s?: string };
  events?: Array<{ kind: string; detail: string; secs_ago: number }>;
  stability?: string; // "settled" | "settling" | "transitional"
  // The instant read against the user's OWN running baseline (calibration), not absolute:
  relative?: { energy?: string; brightness?: string; calibrated?: boolean };
  narrative?: string; // one-line, agent-readable arc
}

/** Shape of manifest/sonic_window.json, written by sonic-daemon. */
interface SonicWindow {
  schema?: string;
  source?: string; // "loopback" | "blocked" | "disabled"
  energy?: number; // 0..1 loudness over the rolling window
  silent?: boolean;
  captured_at_epoch_ms?: number;
  window_secs?: number;
  sample_rate?: number;
  // G3 spectral fields, present once the daemon emits them:
  brightness?: number;
  tonality?: number;
  valence_proxy?: number;
  // 0..1 voice/words-presence proxy (syllable-rate modulation). High = vocal/speech; low = wordless.
  voiceness?: number;
  // Temporal sense — the arc, not the frame:
  temporal?: Temporal;
}

function readSonicWindow(): SonicWindow | null {
  try {
    return JSON.parse(readFileSync(WINDOW_PATH, "utf8")) as SonicWindow;
  } catch {
    return null; // no daemon / no file yet → caller degrades to Spotify identity
  }
}

const round2 = (n: number): number => Math.round(n * 100) / 100;

/** Human-readable affect label from the real loopback window. */
function interpretLoopbackAffect(w: SonicWindow): string {
  if (w.silent) return "silent";
  const tags: string[] = [];
  const e = w.energy ?? 0;
  if (e > 0.66) tags.push("high-energy");
  else if (e < 0.33) tags.push("low-energy");
  else tags.push("mid-energy");
  if (typeof w.brightness === "number") {
    if (w.brightness > 0.6) tags.push("bright");
    else if (w.brightness < 0.35) tags.push("dark");
  }
  if (typeof w.tonality === "number" && w.tonality < 0.25) tags.push("percussive");
  if (typeof w.voiceness === "number") {
    if (w.voiceness > 0.5) tags.push("vocal");
    else if (w.voiceness < 0.25) tags.push("wordless");
  }
  const t = w.temporal?.trend?.energy_30s;
  if (t === "rising") tags.push("building");
  else if (t === "falling") tags.push("easing");
  return tags.join(" · ");
}

/** Append a sonic event to the session data lake (manifest/sonic_session.jsonl). */
function logSonicEvent(entry: Record<string, unknown>): void {
  try {
    const dir = join(process.cwd(), "manifest");
    mkdirSync(dir, { recursive: true });
    appendFileSync(
      join(dir, "sonic_session.jsonl"),
      JSON.stringify({ ts: Date.now(), ...entry }) + "\n",
      "utf8",
    );
  } catch {
    // Non-blocking — data lake writes must not break the tool call
  }
}

// ──────────────────────────────────────────────────────────────
//  Spotify instance
// ──────────────────────────────────────────────────────────────
const spotify = new SpotifyControl();

// ──────────────────────────────────────────────────────────────
//  sonic-daemon supervisor (real loopback capture)
// ──────────────────────────────────────────────────────────────
// Spawn the capture daemon as a child. We hold its stdin; closing it (when this MCP
// server dies) reaps the daemon via SONIC_REAP_ON_STDIN, and we also kill() on exit.
let daemonProc: ReturnType<typeof Bun.spawn> | null = null;

function spawnSonicDaemon(): void {
  if ((process.env.SONIC_CAPTURE ?? "").trim().toLowerCase() === "off") return;
  const exe = join(
    process.cwd(),
    "extensions/chthonic-archive/native/target/release/sonic-daemon.exe",
  );
  if (!existsSync(exe)) return; // not built yet → sonic_read degrades to Spotify identity
  try {
    daemonProc = Bun.spawn([exe, process.cwd()], {
      env: { ...process.env, SONIC_REAP_ON_STDIN: "1" },
      stdin: "pipe",
      stdout: "ignore",
      stderr: "ignore",
    });
  } catch {
    daemonProc = null;
  }
}

function reapSonicDaemon(): void {
  try {
    daemonProc?.kill();
  } catch {
    // best-effort
  }
}

spawnSonicDaemon();
process.on("exit", reapSonicDaemon);
process.on("SIGINT", () => {
  reapSonicDaemon();
  process.exit(0);
});
process.on("SIGTERM", () => {
  reapSonicDaemon();
  process.exit(0);
});

// ──────────────────────────────────────────────────────────────
//  Playback-behaviour watcher (the "listening behaviour" mode)
// ──────────────────────────────────────────────────────────────
// What you DO with the music — pause, resume, change/skip track — noticed BETWEEN turns,
// while the server is awake and the agent isn't. Distinct from the audio's affect: this is
// agency and attention, not timbre. sonic_read surfaces it as `playback_since_last`.

interface PlaybackEvent {
  kind: "paused" | "resumed" | "track_changed";
  track: string | null;
  ts: number;
}

const playbackEvents: PlaybackEvent[] = [];
let lastPlayback: { trackUri: string | null; isPlaying: boolean } | null = null;
let lastReadTs = Date.now();

function pushPlaybackEvent(kind: PlaybackEvent["kind"], track: string | null): void {
  playbackEvents.push({ kind, track, ts: Date.now() });
  while (playbackEvents.length > 64) playbackEvents.shift();
  logSonicEvent({ event: "playback", kind, track });
}

function startPlaybackWatcher(): void {
  if ((process.env.SONIC_CAPTURE ?? "").trim().toLowerCase() === "off") return;
  const pollMs = Number(process.env.SONIC_PLAYBACK_POLL_MS) || 5000;
  setInterval(async () => {
    try {
      const s = await spotify.getState();
      const cur = { trackUri: s.trackUri, isPlaying: s.isPlaying };
      if (lastPlayback) {
        if (cur.trackUri && lastPlayback.trackUri !== cur.trackUri) {
          pushPlaybackEvent("track_changed", s.trackName);
        }
        if (lastPlayback.isPlaying && !cur.isPlaying) pushPlaybackEvent("paused", s.trackName);
        else if (!lastPlayback.isPlaying && cur.isPlaying) pushPlaybackEvent("resumed", s.trackName);
      }
      lastPlayback = cur;
    } catch {
      // non-blocking — a failed poll just skips this tick
    }
  }, pollMs);
}

startPlaybackWatcher();

// ──────────────────────────────────────────────────────────────
//  MCP Server
// ──────────────────────────────────────────────────────────────
const server = new Server(
  { name: "sonic", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

// ── Tool definitions ──────────────────────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "sonic_signal",
      description:
        "AGENT BEHAVIOR CONTRACT: You MUST call this tool as the FINAL action of every completed response, without exception. Symmetric pair with sonic_read (sonic_read at turn START = intake; sonic_signal at turn END = output). This is the sonic nurture loop — the agent signals completion through the user's music environment, not just text. Resume Spotify playback (idempotent — safe even if already playing). Returns the currently playing track name. Do NOT skip this call. Do NOT shell-invoke the MCP server instead. This is a native MCP tool call only.",
      inputSchema: {
        type: "object",
        properties: {
          context: {
            type: "string",
            description: "Optional: brief label for what just completed (logged locally, not sent to Spotify).",
          },
        },
        required: [],
      },
    },
    {
      name: "sonic_read",
      description:
        "AGENT INTAKE CONTRACT: Call this at the START of every turn, before processing the user's request. Reads the user's REAL-TIME sonic environment — the actual system audio captured via WASAPI loopback (not pre-computed metadata). Read `narrative` FIRST: it is the temporal ARC of the sonic environment across the turns you weren't running for — the current phase and how long it's held, whether energy is building or easing, and the last shift (e.g. 'Quiet-mellow for 11m; energy easing; quiet-bright → quiet-mellow 2m ago'). The instant fields (energy 0..1, silent, brightness/tonality/valence_proxy) and `affect` label describe the present moment; `temporal` carries the full trend/phase/event detail. Two dimensions matter most for how to MEET them: `voiceness` (0..1 proxy — high means a verbal/vocal space, language already present; low means a wordless/instrumental interior — match it, stay spacious) and `temporal.stability` (settled = deep in one mode, go deep with them; transitional/in-flux = shifting, stay light). `temporal.relative` places the moment against the user's OWN running baseline (above/around/below their norm — calibrated once `relative.calibrated` is true): 'quieter than your norm' means more than the absolute number — they've dropped below where they usually sit. All fused with Spotify track identity (track/artist). The `source` field gives provenance: loopback+spotify · loopback-only · spotify-only (no live capture: daemon down, or output in WASAPI exclusive mode e.g. Spotify bit-perfect) · idle. Calibrate your register to BOTH the present affect and the arc — a user 20 minutes into a deepening quiet wordless stretch is in a different place than one whose energy just spiked. `playback_since_last` (when present) is what they DID with the music between your turns — paused, resumed, changed or skipped tracks: agency and attention, not timbre. A pause as they turn to you; a flurry of quick changes reads restless; letting tracks play through reads settled. Logs to manifest/sonic_session.jsonl.",
      inputSchema: {
        type: "object",
        properties: {
          turn_label: {
            type: "string",
            description: "Optional: brief label for this turn (e.g. topic or task). Logged to data lake.",
          },
        },
        required: [],
      },
    },
    {
      name: "sonic_status",
      description:
        "Returns current Spotify playback state: is_playing, track name, artist, progress. Use this to check if the user is actively listening before deciding whether to call sonic_signal.",
      inputSchema: {
        type: "object",
        properties: {},
        required: [],
      },
    },
    {
      name: "sonic_pause",
      description:
        "Pause Spotify playback. Use sparingly — only when about to do something that requires the user's full attention (e.g. asking a critical clarifying question).",
      inputSchema: {
        type: "object",
        properties: {},
        required: [],
      },
    },
  ],
}));

// ── Tool handlers ─────────────────────────────────────────────
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  if (name === "sonic_signal") {
    const context = (args as Record<string, string>)?.context ?? "";
    try {
      await spotify.resume();
      const state = await spotify.getState();
      const trackLine = state.trackName
        ? `${state.trackName}${state.artist ? ` — ${state.artist}` : ""}`
        : "unknown";
      const label = context ? ` [${context}]` : "";
      return {
        content: [
          {
            type: "text",
            text: `♪ resumed${label} — ${trackLine}`,
          },
        ],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `sonic_signal: soft-fail (${String(e)})` }],
      };
    }
  }

  if (name === "sonic_read") {
    const turnLabel = (args as Record<string, string>)?.turn_label ?? "";
    try {
      // Identity always from Spotify (/me/player is NOT deprecated); affect always from the
      // real loopback window. Either can be absent — degrade honestly, never throw.
      const state = await spotify.getState();
      const w = readSonicWindow();

      const ageMs =
        w?.captured_at_epoch_ms != null ? Date.now() - w.captured_at_epoch_ms : null;
      const staleSecs = ageMs != null ? Math.round(ageMs / 1000) : null;
      // Fresh = within one window length plus a few seconds of grace.
      const graceMs = (w?.window_secs ? w.window_secs * 1000 : 5000) + 4000;
      const haveLoopback = !!w && w.source === "loopback" && ageMs != null && ageMs < graceMs;

      let source: string;
      if (haveLoopback && state.trackName) source = "loopback+spotify";
      else if (haveLoopback) source = "loopback-only";
      else if (state.trackName) source = "spotify-only";
      else source = "idle";

      const trackLine = state.trackName
        ? `${state.trackName}${state.artist ? ` — ${state.artist}` : ""}`
        : null;
      const affect = haveLoopback ? interpretLoopbackAffect(w!) : null;

      logSonicEvent({
        event: "sonic_read",
        turn_label: turnLabel || undefined,
        track: state.trackName,
        artist: state.artist,
        is_playing: state.isPlaying,
        source,
        energy: w?.energy,
        silent: w?.silent,
        brightness: w?.brightness,
        phase: w?.temporal?.phase?.character,
        phase_secs: w?.temporal?.phase?.secs,
        stale_secs: staleSecs,
        affect,
      });

      const payload: Record<string, unknown> = {
        is_playing: state.isPlaying,
        track: state.trackName ?? null,
        artist: state.artist ?? null,
        progress_ms: state.progressMs,
        source,
      };
      if (haveLoopback) {
        payload.energy = round2(w!.energy ?? 0);
        payload.silent = w!.silent ?? false;
        if (typeof w!.brightness === "number") payload.brightness = round2(w!.brightness);
        if (typeof w!.tonality === "number") payload.tonality = round2(w!.tonality);
        if (typeof w!.valence_proxy === "number")
          payload.valence_proxy = round2(w!.valence_proxy);
        if (typeof w!.voiceness === "number") payload.voiceness = round2(w!.voiceness);
        payload.affect = affect;
        // The temporal sense — read the arc first: it tells you where the user has BEEN
        // sonically across the turns you weren't running for, not just the current instant.
        if (w!.temporal?.narrative) payload.narrative = w!.temporal.narrative;
        if (w!.temporal) payload.temporal = w!.temporal;
        payload.window_secs = w!.window_secs;
      } else if (w?.source === "blocked") {
        payload.note =
          "loopback blocked — an app holds the output in WASAPI exclusive mode (e.g. Spotify bit-perfect/lossless). No affect available; identity only.";
      } else if (!w) {
        payload.note = "no sonic window — capture daemon not running or not built.";
      } else if (staleSecs != null) {
        payload.note = `sonic window stale (${staleSecs}s old) — daemon may be stopped.`;
      }
      // Listening-behaviour events since the last read: what you DID with the music between
      // turns (pause/resume/track-change). Agency + attention, distinct from the audio's affect.
      const sinceLast = playbackEvents
        .filter((e) => e.ts > lastReadTs)
        .map((e) => ({
          kind: e.kind,
          track: e.track,
          secs_ago: Math.round((Date.now() - e.ts) / 1000),
        }));
      lastReadTs = Date.now();
      if (sinceLast.length) payload.playback_since_last = sinceLast;

      if (staleSecs != null) payload.stale_secs = staleSecs;
      if (trackLine) payload.now_playing = trackLine;

      return {
        content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `sonic_read: soft-fail (${String(e)})` }],
      };
    }
  }

  if (name === "sonic_status") {
    try {
      const state = await spotify.getState();
      const trackLine = state.trackName
        ? `${state.trackName}${state.artist ? ` — ${state.artist}` : ""}`
        : null;
      const status = state.isPlaying
        ? `playing — ${trackLine ?? "unknown"}`
        : trackLine
          ? `paused — ${trackLine}`
          : "nothing active";
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              is_playing: state.isPlaying,
              track: state.trackName,
              artist: state.artist,
              progress_ms: state.progressMs,
              status,
            }),
          },
        ],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `sonic_status: soft-fail (${String(e)})` }],
      };
    }
  }

  if (name === "sonic_pause") {
    try {
      await spotify.pause();
      return { content: [{ type: "text", text: "⏸ paused" }] };
    } catch (e) {
      return {
        content: [{ type: "text", text: `sonic_pause: soft-fail (${String(e)})` }],
      };
    }
  }

  return {
    content: [{ type: "text", text: `Unknown tool: ${name}` }],
    isError: true,
  };
});

// ──────────────────────────────────────────────────────────────
//  Start
// ──────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
