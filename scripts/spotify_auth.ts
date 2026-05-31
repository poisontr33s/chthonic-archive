#!/usr/bin/env bun
// @SID: SCRIPT_SPOTIFY_AUTH_V1
/**
 * spotify_auth.ts — One-shot OAuth2 Authorization Code flow.
 * Exchanges your CLIENT_ID + CLIENT_SECRET for a REFRESH_TOKEN.
 * Run this ONCE, copy the refresh_token to .env.local, never run again.
 *
 * Prerequisites:
 *   SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET already in .env.local
 *   Redirect URI registered in Spotify dashboard: http://localhost:3000/callback
 *
 * Usage:
 *   bun run scripts/spotify_auth.ts
 *
 * Will open your browser, wait for the callback, print the refresh_token.
 */

const PORT = 3000;
const REDIRECT_URI = `http://localhost:3000/callback`;
const SCOPES = [
  "user-read-playback-state",
  "user-modify-playback-state",
  "user-read-currently-playing",
].join(" ");

const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID ?? "";
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET ?? "";

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.error(
    "[spotify-auth] Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env.local\n" +
      "Create .env.local with those two values first, then re-run.",
  );
  process.exit(1);
}

// ─── Auth URL ─────────────────────────────────────────────────────────────────
const state = Math.random().toString(36).slice(2);
const authUrl =
  `https://accounts.spotify.com/authorize?` +
  new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    scope: SCOPES,
    redirect_uri: REDIRECT_URI,
    state,
  });

console.log("\n[spotify-auth] Opening browser for Spotify login...");
console.log(`\n  ${authUrl}\n`);

// Open browser (Windows)
Bun.spawn(["cmd", "/c", "start", authUrl.replace(/&/g, "^&")]);

// ─── Local callback server ────────────────────────────────────────────────────
let resolveCode!: (code: string) => void;
const codePromise = new Promise<string>((res) => { resolveCode = res; });

const server = Bun.serve({
  port: PORT,
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/callback") {
      const code = url.searchParams.get("code");
      const returnedState = url.searchParams.get("state");

      if (returnedState !== state) {
        return new Response("State mismatch — possible CSRF. Try again.", { status: 400 });
      }

      if (!code) {
        const error = url.searchParams.get("error");
        return new Response(`Auth denied: ${error}`, { status: 400 });
      }

      resolveCode(code);
      return new Response(
        "<html><body><h2>✅ Authorized.</h2><p>You can close this tab. Return to your terminal.</p></body></html>",
        { headers: { "Content-Type": "text/html" } },
      );
    }
    return new Response("Not found", { status: 404 });
  },
});

console.log(`[spotify-auth] Waiting for callback on http://localhost:${PORT}/callback ...`);

const code = await codePromise;
server.stop();

// ─── Exchange code for tokens ─────────────────────────────────────────────────
const creds = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
const tokenRes = await fetch("https://accounts.spotify.com/api/token", {
  method: "POST",
  headers: {
    Authorization: `Basic ${creds}`,
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: REDIRECT_URI,
  }),
});

if (!tokenRes.ok) {
  console.error("[spotify-auth] Token exchange failed:", await tokenRes.text());
  process.exit(1);
}

const tokens = (await tokenRes.json()) as {
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

console.log("\n✅ Authorization complete.\n");
console.log(`SPOTIFY_REFRESH_TOKEN=${tokens.refresh_token}\n`);
console.log("Add that line to your .env.local file (alongside CLIENT_ID + CLIENT_SECRET).");
console.log("Then run: bun run scripts/spotify_control.ts status\n");
