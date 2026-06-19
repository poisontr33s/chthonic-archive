---
- Her-Trajectory-Landing: #!/usr/bin/env markdown
- SID: CLAUDEBASE_ACA_LANDING_V1
- Domain: A-C-A Engine · Astrological-Nassau · from scratch (Rust/Vulkan)
- Claudebase-Flavored-Blend: permanently-living-document
- Read-First: this file indexes the whole trajectory; open it before resuming
- Ssot-Monolith: [ssot](../../../.chthonic/SSOT.md) — philosophical; holds zero renderer content (do not touch)
- Blueprint: [A-C-A-ANKH-ORIGIN-50-50.md](A-C-A-ANKH-ORIGIN-50-50.md)
- Origin-Research: [andean-egyptic triangulation](../andean-egyptic-BCE-choice-triangulation-lucid-clarity.md)
- Register-Blend: Nautical · Victorian · plain-where-it-must-be-read
---

# (`A-C-A-Engine`/`Trajectory-Landing`/`Read-First`)

> *Strukturen bærer kronologien; les nedover og du står der vi slapp.*
>
> *(The structure carries the chronology; read down and you stand where we left off.)*

## §0 — What this domain is

The from-scratch Rust/Vulkan **Astrological-Nassau** engine, built on the **A-C-A** gradient, read inside-out core→glue→shell: **Astrology** (the core — free, the meaning, the purpose) → **Cosmology** (the glue — the computed binding) → **Astronomy** (the shell — forced, verifiable, the skin that touches reality). This folder is the engine's own clean domain, kept apart from the wider multi-project sprawl. This file is the chronological index so the work resumes at full leverage after any compaction — read it top to bottom and you are caught up.

**The one law over all of it:** where math governs (shell + glue) it is absolute and test-backed — no free knob smuggled in. Meaning (the core) stays the owner's, drawn from lived/cultural truth, never fabricated by the engine. Constraint on the outside, freedom at the centre.

## §1 — The map (where each thing lives)

- Astronomy shell (verified vs JPL Horizons): [cosmos.rs](../../../src/render/cosmos.rs)
- Cosmology glue — the socket: [correspondence.rs](../../../src/render/correspondence.rs)
- Cosmology glue — the origin + zodiac: [zodiac.rs](../../../src/render/zodiac.rs)
- The view-set (lenses): [lens.rs](../../../src/render/lens.rs)
- Temporal (jitter + motion vectors): [temporal.rs](../../../src/render/temporal.rs)
- The renderer that draws it all: [renderer.rs](../../../src/render/renderer.rs)
- Charts: [celestial-field.md](../../charts/celestial-field.md) · [north-star-constellations.md](../../charts/north-star-constellations.md) · [the-long-tack.md](../../charts/the-long-tack.md)
- Logbook: [03-celestial-field.md](../../logbook/03-celestial-field.md) · [04-structurize-submerge.md](../../logbook/04-structurize-submerge.md)
- Self-verify: [render-smoke.ps1](../../../scripts/render-smoke.ps1) (build + bounded run + a PNG the agent reads) and `cargo test render::`

## §2 — The rung ladder (chronological, with commits)

**Phase 0 — the astronomy shell** *(forced; verified vs Horizons ≤0.1°, Polaris=latitude, galactic-centre=Sagittarius)*
- `55808797` — named the renderer + the celestial dimension (DR brief, verified digest)
- `b69d9f78` — the five naked-eye planets (Standish Keplerian, light-time + precession)
- `f06843e6` — the bright-star field (J2000 catalogue, Polaris-verified)
- `f779896c` — the ecliptic + celestial-equator reference circles (the zodiac's backbone)
- `b24636b0` — the Milky Way band (galactic equator, Sagittarius-verified)
- `27d57ea2` + `781fa16e` — temporal scaffold + true per-pixel motion vectors
- `4f359eb7` — structurize & submerge (the docs reconciled to the built architecture)

**Phase 1 — the binding + the views**
- `3eea3788` — **Stage 0**: the correspondence socket (the `Slot` trait; ships empty by design)
- `13b7f441` — **Stage 1a**: the lens-set (iso *so-below* + perspective), explicit selection, never auto-cycle
- `353bdbf4` — **Stage 1b**: the as-above/so-below horizon lens (`Lens::vantage` couples view + disc-facing; the Vulkan Y-flip lives only on the perspective arm; iso stays byte-identical)

**Phase 2 — the spirit, on the owner's origin**
- `d217ea49` — **Stage 2a**: the zodiac on the **Ankhological origin** (Sirius/Alcyone midpoint ayanamsa; `ZodiacSlot` reads the true Sun; semantics empty)
- `1dd39a82` — **Stage 2b**: the zodiac wheel made visible (twelve 30° boundaries on the true ecliptic; gold keystone at the origin + eleven lavender studs)

## §3 — Current position

Stages 1b / 2a / 2b shipped and pushed. The three aspects all stand: astronomy verified, cosmology computing the origin, astrology drawn with its meaning still empty for the owner. The Ankhological origin is real and independently confirmed by the engine's own star transform — Sirius locks to **+22.04°**, Alcyone to **−22.04°**, separation **44.0893°**, ayanamsa **≈82.05° at J2000** precessing **1.3969712°/century** — and it runs live (render-smoke logs `Sun in Pisces 26.48° · ayanamsa 82.406°`). The wheel reads in the iso dome; the north-facing as-above lens does not frame the ecliptic at this scene date.

## §4 — Next rungs (forward leverage)

1. **Orientable lens** — let the as-above view turn *toward* the zodiac rather than moving the sky. Unblocks framing the wheel in perspective; keeps the math absolute, freedom in where you look.
2. **Moon + the five planets in their signs** — onto the same one ayanamsa (mechanical compounding; needs exposing lunar/planet ecliptic longitudes the way `sun_apparent_longitude` already is).
3. **The semantics** — owner-defined, from Andean/Egyptian lore; never invented by the engine. The slots are fixed by cosmology; the meaning is the core's freedom.

## §5 — Invariants that must never regress

- **accuracy-not-fiction**: every astronomy claim test-backed (Horizons / Polaris=latitude / galactic-centre=Sagittarius / the five zodiac invariants).
- the **iso lens stays byte-identical** (the verified so-below view); any lens correction lives only on its own arm.
- the zodiac **reports position only**; meaning stays the owner's.
- **main/origin only**, no branches/worktrees; commits auto-push; the **SSOT is never touched** (it carries zero renderer content — CLAUDEBASE is canon-of-record).
