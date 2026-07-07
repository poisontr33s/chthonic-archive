---
type: session-handoff
session: 02c617a7-9a08-476d-92cd-0effad967dd1
date: 2026-07-07
author: claude
lane: aca-engine-live-correspondence
context: autonomous continuation while user slept
---

# A-C-A Engine — Autonomous Continuation Summary

You asked for a nightly on the A-C-A engine question mark, same shape as `SESSION_2026_05_27_DSL_AUTONOMOUS_NIGHT.md` — PROTO out, bias toward starting over more planning. Read the philosophy memory first (`project_aca_engine_philosophy`, `project_ankhological_origin`), then read the actual live code before touching anything, because the memory's claims needed checking against what's really there before I could trust them.

## What I found

The triad is real and already good: Astrology (core, meanings deliberately empty — your domain, didn't touch it), Cosmology (glue, Sirius/Alcyone midpoint ayanamsa in `src/render/zodiac.rs`, 8 passing unit tests), Astronomy (shell, `src/render/cosmos.rs`, 20+ tests genuinely checked against Skyfield/JPL Horizons/DE421 — verified this claim by reading the tests, not just trusting the memory that asserted it).

But the actual runtime wiring wasn't alive. `renderer.rs`'s "Stage 2a/2b/2c" block computed the whole correspondence reading exactly once, at `Renderer::new()`, from the **frozen verification epoch** (`scene_julian_day()`, pinned to 2026-06-09 17:00 UTC so the celestial-field mesh renders consistently for the smoke-test pixel baseline). It logged the ayanamsa once and stored `zodiac_bodies` on the Renderer struct — I grepped the whole codebase and confirmed **nothing else ever reads that field**. Applying the engine's own governing criterion ("forced by a substrate you can check, or a free parameter wearing the costume of truth") to its own integration rather than its math: this was the ornamental case. Fully verified physics terminating in a write-only field and a log line nobody was watching.

The code had already left the exact breadcrumb pointing at the fix — `main.rs:250`: "swap to `SystemTime::now()`→JD for the live sky."

## What landed

- `src/render/cosmos.rs` — added `julian_day_now()`: a one-line Unix-epoch→JD conversion. Tested two ways: a sane-decade bounds check, and an anchor against `julian_day()`'s own calendar formula at a known instant (2026-01-01T00:00Z), rather than hand-rolling a second calendar implementation just to test a unit conversion — first draft of that test did exactly that and I cut it, wasn't worth the surface area for what it was proving.
- `src/render/renderer.rs` — Stage 2a (correspondence-socket log) and Stage 2b/2c (`zodiac_bodies`) now read `julian_day_now()` instead of the frozen epoch. **Deliberately did not touch** `celestial_field_vertices` — that one produces real pixels the render-smoke baseline depends on, so it stays pinned. Verified the isolation actually held, not just assumed it: `render-smoke.ps1` screenshot came back byte-identical (163308 bytes, matching the pre-change run) while the log line changed from the frozen ayanamsa to a live one — 82.407° tonight vs the old test-epoch value. That diff (pixels unchanged, log changed) is the actual proof this reached exactly the intended surface.
- `cargo test --lib`: 51/51 passing (was 49; added 2).

## The architectural fork I did not decide for you

`zodiac_bodies` is still a construction-time snapshot — live JD now, but computed once, not per-frame. Making it recompute every frame means running the Sun + Moon + five-planet series every frame, uncached, on the render loop's hot path. That's a real perf-relevant choice, not a mechanical one, so I left it exactly where it was (snapshot at construction) rather than deciding it at 2am. Same discipline as the DSL nightly's L45 question — I have an opinion (build a cheap staleness check — recompute only if the stored JD is more than, say, a game-minute old — rather than either "never" or "every frame") but didn't act on it autonomously.

## Recommended next moves (pick by appetite)

| Option | What | Cost |
|---|---|---|
| A | Decide the per-frame-recompute question above | 1 small iteration once decided |
| B | The bigger gap underneath both of tonight's finds and the DSL thread: there is no text/HUD rendering anywhere in the Rust engine at all (confirmed via grep before I scoped tonight's work) — so even a live correspondence reading has nowhere to actually surface in-game beyond the log. That's foundational work, not a nightly. |
| C | Leave it as-is — the log line is arguably enough for now; the field exists for whenever the game layer wants it |

## Tone note

No postscript drift, no chunked surgery, no novelization. This is all the autonomous work I did — one bounded, tested, verified fix, not padded out to look busier. The bigger FLUX/DSL/ocean-BLAS items from tonight's frontier atlas (`CLAUDEBASE/charts/frontier-atlas.md`) stayed untouched on purpose — they're foundational, not nightly-sized, and deserve your call on when to open them.

Sleep well.
