#!/usr/bin/env bun
// @SID: SCRIPT_SPOTIFY_CONTROL_V1
/**
 * spotify_control.ts — Spotify playback controller for the Claudine autoloop.
 *
 * Reads credentials from .env.local (Bun loads it natively):
 *   SPOTIFY_CLIENT_ID
 *   SPOTIFY_CLIENT_SECRET
 *   SPOTIFY_REFRESH_TOKEN
 *
 * Usage (CLI):
 *   bun run scripts/spotify_control.ts status
 *   bun run scripts/spotify_control.ts pause
 *   bun run scripts/spotify_control.ts play
 *   bun run scripts/spotify_control.ts play <spotify:track:uri>
 *
 * Usage (import):
 *   import { SpotifyControl } from "./spotify_control.ts";
 *   const spotify = new SpotifyControl();
 *   await spotify.pause();
 *   await spotify.resume();
 *
 * Autoloop semantics:
 *   pre-query  → resume()   (agent starting work → music ON)
 *   agentStop  → pause()    (agent done, user reading → music OFF)
 */

const API_BASE = "https://api.spotify.com/v1";
const TOKEN_URL = "https://accounts.spotify.com/api/token";

export interface PlaybackState {
  isPlaying: boolean;
  progressMs: number;
  trackUri: string | null;
  trackName: string | null;
  artist: string | null;
}

// NOTE: Spotify's /audio-features endpoint was deprecated 2024-11-27 (403 for new apps) and
// only ever returned one static vector per track. Real affective signal now comes from WASAPI
// loopback (sonic-daemon → manifest/sonic_window.json). This client keeps only identity +
// transport, which remain supported: /me/player and play/pause.

export class SpotifyControl {
  private readonly clientId: string;
  private readonly clientSecret: string;
  private readonly refreshToken: string;
  private accessToken: string | null = null;

  constructor() {
    // Primary: env vars (set via api_pool -Load in a terminal, or explicitly in MCP env block)
    // Fallback: read $HOME/.chthonic/api_pool.json directly (used when spawned by VS Code's MCP host)
    const pool = SpotifyControl.readPool();
    this.clientId     = process.env.SPOTIFY_CLIENT_ID     ?? pool.SPOTIFY_CLIENT_ID     ?? "";
    this.clientSecret = process.env.SPOTIFY_CLIENT_SECRET ?? pool.SPOTIFY_CLIENT_SECRET ?? "";
    this.refreshToken = process.env.SPOTIFY_REFRESH_TOKEN ?? pool.SPOTIFY_REFRESH_TOKEN ?? "";
  }

  private static readPool(): Record<string, string> {
    try {
      const os = require("os") as typeof import("os");
      const path = require("path") as typeof import("path");
      const fs = require("fs") as typeof import("fs");
      const poolPath = path.join(os.homedir(), ".chthonic", "api_pool.json");
      if (!fs.existsSync(poolPath)) return {};
      const raw = JSON.parse(fs.readFileSync(poolPath, "utf8"));
      return (raw?.env ?? {}) as Record<string, string>;
    } catch {
      return {};
    }
  }

  private configured(): boolean {
    return Boolean(this.clientId && this.clientSecret && this.refreshToken);
  }

  private async refreshAccessToken(): Promise<string> {
    const creds = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString("base64");
    const res = await fetch(TOKEN_URL, {
      method: "POST",
      headers: {
        Authorization: `Basic ${creds}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        refresh_token: this.refreshToken,
      }),
    });
    if (!res.ok) throw new Error(`Token refresh failed: ${res.status} ${await res.text()}`);
    const data = (await res.json()) as { access_token: string };
    this.accessToken = data.access_token;
    return this.accessToken;
  }

  private async request(
    path: string,
    options: RequestInit = {},
  ): Promise<unknown | null> {
    if (!this.accessToken) await this.refreshAccessToken();

    const doFetch = () =>
      fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${this.accessToken}`,
        },
      });

    let res = await doFetch();

    if (res.status === 401) {
      await this.refreshAccessToken();
      res = await doFetch();
    }

    if (res.status === 204 || res.status === 202) return null;
    if (!res.ok) {
      // 403 = premium required or no active device — soft fail
      if (res.status === 403) return null;
      throw new Error(`Spotify API error ${res.status}: ${await res.text()}`);
    }
    return res.json();
  }

  /** Fetch current playback state. Returns null if nothing active. */
  async getState(): Promise<PlaybackState> {
    if (!this.configured()) return { isPlaying: false, progressMs: 0, trackUri: null, trackName: null };
    try {
      const data = (await this.request("/me/player")) as any;
      if (!data?.item) return { isPlaying: false, progressMs: 0, trackUri: null, trackName: null, artist: null };
      const artists: string = (data.item.artists as Array<{ name: string }> | undefined)
        ?.map((a) => a.name).join(", ") ?? null;
      return {
        isPlaying: data.is_playing,
        progressMs: data.progress_ms ?? 0,
        trackUri: data.item.uri ?? null,
        trackName: data.item.name ?? null,
        artist: artists ?? null,
      };
    } catch {
      return { isPlaying: false, progressMs: 0, trackUri: null, trackName: null, artist: null };
    }
  }

  /** Pause playback. No-op if nothing playing or not configured. */
  async pause(): Promise<void> {
    if (!this.configured()) return;
    try {
      await this.request("/me/player/pause", { method: "PUT" });
    } catch {
      // No active device — silent
    }
  }

  /** Resume playback. Optionally resume a specific track+position. */
  async resume(trackUri?: string, positionMs?: number): Promise<void> {
    if (!this.configured()) return;
    try {
      const body =
        trackUri
          ? JSON.stringify({ uris: [trackUri], position_ms: positionMs ?? 0 })
          : undefined;
      await this.request("/me/player/play", {
        method: "PUT",
        headers: body ? { "Content-Type": "application/json" } : {},
        body,
      });
    } catch {
      // No active device — silent
    }
  }

}

// ─── Sonic snapshot — shared between pre/post hooks ───────────────────────────
let _sonicSnapshot: { trackUri: string | null; progressMs: number } = {
  trackUri: null,
  progressMs: 0,
};

const _spotify = new SpotifyControl();

/**
 * Call before sdk.query fires.
 * Snapshots current track, then resumes (agent starting work → music ON).
 */
export async function sonicPreQuery(): Promise<void> {
  const state = await _spotify.getState();
  _sonicSnapshot = { trackUri: state.trackUri, progressMs: state.progressMs };
  if (_sonicSnapshot.trackUri && !state.isPlaying) {
    await _spotify.resume(_sonicSnapshot.trackUri, _sonicSnapshot.progressMs);
  } else if (!_sonicSnapshot.trackUri) {
    // Nothing was playing — just resume whatever was queued
    await _spotify.resume();
  }
}

/**
 * Call when agentStop fires with decision:"allow" (agent truly done).
 * Pauses playback at current position (user reading → music OFF).
 */
export async function sonicPostQuery(): Promise<void> {
  const state = await _spotify.getState();
  _sonicSnapshot = { trackUri: state.trackUri, progressMs: state.progressMs };
  await _spotify.pause();
}

// ─── CLI ───────────────────────────────────────────────────────────────────────
const cmd = process.argv[2];
if (cmd) {
  const ctl = new SpotifyControl();
  switch (cmd) {
    case "status": {
      const s = await ctl.getState();
      if (!s.trackUri) {
        console.log("[spotify] No active playback.");
      } else {
        console.log(`[spotify] ${s.isPlaying ? "▶" : "⏸"} ${s.trackName ?? s.trackUri} @ ${s.progressMs}ms`);
      }
      break;
    }
    case "pause":
      await ctl.pause();
      console.log("[spotify] ⏸ paused.");
      break;
    case "play":
    case "resume": {
      const uri = process.argv[3];
      await ctl.resume(uri);
      console.log("[spotify] ▶ resumed.");
      break;
    }
    default:
      console.error(`[spotify] Unknown command: ${cmd}. Use: status | pause | play | resume`);
      process.exit(1);
  }
}
