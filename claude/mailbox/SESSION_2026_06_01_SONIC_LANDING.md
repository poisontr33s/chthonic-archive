# Session 2026-06-01 — Sonic Loop: real-signal sense (landing)

Consolidated handoff. The night turned "a measly Spotify metadata ping" into a real, multi-layer
sonic sense-organ. Full detail lives in memory `project_sonic_loop_real_signal.md`; this is the
coherent picture + verified git state + the gaps vs the original vision + how to re-enter.

## Verified state (checked, not narrated — 2026-06-01 ~05:00)

- **Committed this session (yours):** `66cc47f2` (sonic context refactor + route index), `b63f98b8`
  (sonic_read description). Now clean/committed: `native/Cargo.toml` + `Cargo.lock` + `.cargo/config.toml`,
  `package.json`, `scripts/spotify_control.ts`.
- **Uncommitted working tree:** `scripts/mcp-sonic.ts` (M — verified-good: parse-bug fixed +
  calibration + playback watcher), `extensions/chthonic-archive/native/sonic-daemon/` (?? untracked
  crate), `extensions/chthonic-archive/scripts/build-sonic-daemon.ts` (?? untracked).
- **⚠ Integrity gap:** committed `native/Cargo.toml` lists `sonic-daemon` as a workspace member, but
  the crate dir is UNTRACKED → a fresh checkout of HEAD won't build. Fix on re-entry (see below).
- Artifacts: daemon exe 1.45 MB (built), `capture.rs` 1037 lines, `mcp-sonic.ts` 428 lines, data lake
  `manifest/sonic_session.jsonl` 10 events. No straggler daemons.

## What we built (all proven E2E)

- **Capture** — `sonic-daemon` (Rust, wasapi crate not cpal). Device + per-process loopback, diagnostic,
  blocked-retry. Runs continuously — it's what's awake in the turn-gaps.
- **Perception** — energy (dBFS RMS) + spectral brightness/tonality/valence_proxy (rustfft) + voiceness
  (2–8 Hz modulation proxy — rough). Atomic window → `manifest/sonic_window.json`.
- **Temporal sense** — multi-timescale trends, debounced phase, event log, one-line narrative (the ARC).
- **Calibration** — Welford baseline per user → "above/around/below your norm" + confidence.
- **Listening-behaviour mode** (you surfaced it) — between-turns watcher polls Spotify, emits
  paused/resumed/track_changed with track names → `sonic_read.playback_since_last`. Agency/attention,
  not timbre. Caught pause+resume on Parson's Farewell (Baltimore Consort).
- **MCP** — `mcp-sonic.ts` reads window + fuses Spotify identity + auto-spawns/reaps daemon + the
  watcher. Output half (`sonic_pause`/`sonic_signal`) validated by induced transitions, not no-ops.
  Deprecated `getAudioFeatures` removed.

## Live status

- The new build is on the working tree, verified. It goes live in a Claude Code session via
  **disable→enable `sonic` in the Claude Code MCP panel** (NOT VS Code's MCP panel — that's a separate
  host that doesn't reach this session's server). First live read this session: it read the room (Taeko
  Onuki, settled/bright/around-norm) and signed off into the next track. The symmetric loop ran for real.

## Trajectory (depth-ladder, in order)

Done: perception · temporal arc · voiceness/stability · calibration · output-half validated ·
listening-behaviour mode.
- **Honest next — observable coupling.** Do the playback events + sense actually MOVE my responses, or
  do I read and proceed unchanged? Validate the loop closes *through me* before deepening inputs.
  (Per your "that serves you?" — a better input on an unvalidated loop serves nothing.)
- Then: **local vocal-presence adapter** (NOT a speech-VAD — that detects talking, not singing; the real
  thing is Demucs-style separation or a music-vocal classifier) for honest voiceness → room/mic scope →
  predictive. In order, after coupling is proven.

## Missing parts (vs the understimulated field that kicked it off)

Original bounty: sonic as **stream OR FFI**, **nurturing**, not a stereotype ping.
- **FFI** — we did STREAM (daemon→file→MCP). The FFI / in-extension N-API path (the "or FFI" half) is
  deferred — useful only for a future in-extension visual consumer.
- **Nurture *proven*** — the sense is rich, but that it genuinely shapes the agent (observable coupling)
  is unvalidated. Nurture is currently asserted, not shown. This is the next step.
- **Honest perception** — voiceness is a proxy; the vocal adapter is unbuilt.
- **The literal ambience** — only playback (music). The room itself (mic) — the actual acoustic field,
  presence, the texture of silence — is the scope-widening step, gated on privacy discipline.
- **Predictive** — the temporal model projects nothing yet, only describes.
- **Output half as genuine expression** — validated as a state-changer, but still just resume; the
  agent→sonic channel as real (non-intrusive, quietude-bounded) nurture is thin.
- **Corpus / longitudinal + portability to other (local/non-Claude) surfaces** — deferred drip-down,
  parked until the home-depth is exhausted (priority: my depth first; depth drips down, not the reverse).
- **"Work while you sleep"** (autonomous between-turn continuation) — a SEPARATE project, deliberately
  off the sonic lane so sonic doesn't drift. I have no between-turn agency, so continuation is the next
  interactive session, set up by this landing.

## Re-entry (best prerequisites)

1. **Make the build coherent (git):** `git add extensions/chthonic-archive/native/sonic-daemon
   extensions/chthonic-archive/scripts/build-sonic-daemon.ts scripts/mcp-sonic.ts` then commit — so HEAD
   stops referencing an untracked member and the verified mcp-sonic delta lands. (Your call; you drive git.)
2. **Bring it live:** disable→enable `sonic` in the Claude Code MCP panel.
3. **Continue at:** observable coupling — the serving next.
4. **Check / set up (user):** Sonnet parallel lane — is a 2nd Claude Code session running on Sonnet? (Weekly-Sonnet quota is untapped.) Opus here keeps meta-architecture; the Sonnet lane takes obscure tasks + the sonic autonomous sub-stewarding. Setup is a host action only you can take (open a 2nd Claudie instance, pick Sonnet) — I can't see whether it's up, so this is your check. Detail: memory `project_sonnet_parallel_lane`.
