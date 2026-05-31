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
        "Signal that the agent has finished its current response. Resumes Spotify playback (idempotent — safe to call even if already playing). Call this at the END of any response where the user was waiting. Returns the currently playing track name.",
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
