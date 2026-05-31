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
import type { AudioFeatures } from "./spotify_control.ts";
import { appendFileSync, mkdirSync } from "fs";
import { join } from "path";

// ──────────────────────────────────────────────────────────────
//  Affective helpers
// ──────────────────────────────────────────────────────────────

/** Derive a human-readable affect label from Spotify audio features. */
function interpretAffect(f: AudioFeatures): string {
  const tags: string[] = [];
  if (f.energy > 0.7) tags.push("high-energy");
  else if (f.energy < 0.35) tags.push("low-energy");
  if (f.valence > 0.65) tags.push("bright");
  else if (f.valence < 0.35) tags.push("melancholic");
  if (f.instrumentalness > 0.6) tags.push("instrumental");
  else if (f.speechiness > 0.33) tags.push("spoken-word");
  if (f.tempo > 145) tags.push("fast-paced");
  else if (f.tempo < 80) tags.push("slow");
  tags.push(f.mode === 0 ? "minor" : "major");
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
        "AGENT INTAKE CONTRACT: Call this at the START of every turn, before processing the user's request. Reads the sonic context of the user's environment — what was playing while they formulated this message. Returns audio features (energy, valence, instrumentalness, tempo, mode) plus a pre-interpreted affect label. The user's sonic state is affective context: high instrumentalness + low valence = deep-focus melancholic register; high energy + high valence = active bright mode. Calibrate your response register accordingly. Logs to manifest/sonic_session.jsonl (session data lake).",
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
      const state = await spotify.getStateWithFeatures();
      const trackLine = state.trackName
        ? `${state.trackName}${state.artist ? ` — ${state.artist}` : ""}`
        : null;
      const af = state.audioFeatures;
      const affect = af ? interpretAffect(af) : null;

      logSonicEvent({
        event: "sonic_read",
        turn_label: turnLabel || undefined,
        track: state.trackName,
        artist: state.artist,
        is_playing: state.isPlaying,
        ...(af ?? {}),
        affect,
      });

      const payload: Record<string, unknown> = {
        is_playing: state.isPlaying,
        track: state.trackName ?? null,
        artist: state.artist ?? null,
        progress_ms: state.progressMs,
      };
      if (af) {
        payload.energy = af.energy;
        payload.valence = af.valence;
        payload.instrumentalness = af.instrumentalness;
        payload.tempo = Math.round(af.tempo);
        payload.danceability = af.danceability;
        payload.mode = af.mode === 0 ? "minor" : "major";
        payload.affect = affect;
      }
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
