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
> *(The structure carries the chronology; read down and you stand where we left off.)*

---

## (`§0`/`What-This-Domain-Is`)

The from-scratch Rust/Vulkan **(`Astrological-Nassau`)** engine, built on the **(`A-C-A`)** gradient, read inside-out core→glue→shell: **`Astrology`** (the core — free, the meaning, the purpose) → **`Cosmology`** (the glue — the computed binding) → **`Astronomy`** (the shell — forced, verifiable, the skin that touches reality).

This folder is the engine's own clean domain, kept apart from the wider multi-project sprawl. This file is the chronological index, so the work resumes at full leverage after any compaction — read it top to bottom and you are caught up.

**(`The-One-Law`/`Over-All-Of-It`):** where math governs (shell + glue) it is absolute and test-backed — no free knob smuggled in. Meaning (the core) stays the owner's, drawn from lived/cultural truth, never fabricated by the engine. Constraint on the outside, freedom at the centre.

---

## (`§1`/`The-Map`/`Where-Each-Thing-Lives`)

- Astronomy shell (verified vs JPL Horizons) — [cosmos.rs](../../../src/render/cosmos.rs)
- Cosmology glue, the socket — [correspondence.rs](../../../src/render/correspondence.rs)
- Cosmology glue, the origin + zodiac — [zodiac.rs](../../../src/render/zodiac.rs)
- The view-set (lenses) — [lens.rs](../../../src/render/lens.rs)
- Temporal (jitter + motion vectors) — [temporal.rs](../../../src/render/temporal.rs)
- The renderer that draws it all — [renderer.rs](../../../src/render/renderer.rs)
- Charts — [celestial-field.md](../../charts/celestial-field.md) · [north-star-constellations.md](../../charts/north-star-constellations.md) · [the-long-tack.md](../../charts/the-long-tack.md)
- Logbook — [03-celestial-field.md](../../logbook/03-celestial-field.md) · [04-structurize-submerge.md](../../logbook/04-structurize-submerge.md)
- Self-verify — [render-smoke.ps1](../../../scripts/render-smoke.ps1) (build + bounded run + a PNG the agent reads) and `cargo test render::`

---

## (`§2`/`The-Rung-Ladder`/`Chronological-With-Commits`)

**(`Phase-0`/`The-Astronomy-Shell`)** — forced; verified vs Horizons ≤0.1°, Polaris=latitude, galactic-centre=Sagittarius

- `55808797` — named the renderer + the celestial dimension (DR brief, verified digest)
- `b69d9f78` — the five naked-eye planets (Standish Keplerian, light-time + precession)
- `f06843e6` — the bright-star field (J2000 catalogue, Polaris-verified)
- `f779896c` — the ecliptic + celestial-equator reference circles (the zodiac's backbone)
- `b24636b0` — the Milky Way band (galactic equator, Sagittarius-verified)
- `27d57ea2` + `781fa16e` — temporal scaffold + true per-pixel motion vectors
- `4f359eb7` — structurize & submerge (the docs reconciled to the built architecture)

**(`Phase-1`/`The-Binding-And-The-Views`)**

- `3eea3788` — **(`Stage-0`)** the correspondence socket (the `Slot` trait; ships empty by design)
- `13b7f441` — **(`Stage-1-A`)** the lens-set (iso *so-below* + perspective), explicit selection, never auto-cycle
- `353bdbf4` — **(`Stage-1-B`)** the as-above/so-below horizon lens (`Lens::vantage` couples view + disc-facing; the Vulkan Y-flip lives only on the perspective arm; iso stays byte-identical)

**(`Phase-2`/`The-Spirit`/`On-The-Owner's-Origin`)**

- `d217ea49` — **(`Stage-2-A`)** the zodiac on the **(`Ankhological-Origin`)** (Sirius/Alcyone midpoint ayanamsa; `ZodiacSlot` reads the true Sun; semantics empty)
- `1dd39a82` — **(`Stage-2-B`)** the zodiac wheel made visible (twelve 30° boundaries on the true ecliptic; gold keystone at the origin + eleven lavender studs)
- `1d828505` — **(`Stage-2-C`)** the orientable lens — `CHTHONIC_LOOK=zodiac` aims the fixed as-above eye at the Ankhological origin on the true ecliptic; the eye never moves, only the heading turns (`Heading` = azimuth + up-tilt in the bodies' own alt/az frame). The wheel now frames in perspective (render-smoke logs `6/12 sign boundaries above the horizon`).
- `c93da928` — **(`Stage-2-D`)** the Moon + five planets in their signs — `cosmos::moon_apparent_longitude` + `planet_apparent_longitude` expose each body's of-date ecliptic longitude (extracted from the verified position fns, so the alt/az stays byte-identical); `zodiac::bodies_in_signs` places all seven on the one ayanamsa. The bodies were already drawn (celestial field) and the wheel already spoked; this is the placement, position only. Live: `Sun Pisces 26.5°` · `Moon Capricorn 12.3°` · `Mercury Aries 19.9°` · `Venus Taurus 3.2°` · `Mars Aquarius 23.8°` · `Jupiter Taurus 3.4°` · `Saturn Capricorn 20.6°`.

---

## (`§3`/`Current-Position`/`Status`)

- **(`Stages`/`1-B`/`2-A`/`2-B`/`2-C`/`2-D`)** shipped and pushed. The three aspects all stand: astronomy verified, cosmology computing the origin, astrology drawn with its meaning still empty for the owner.
- The **(`Ankhological`)** origin is real and independently confirmed by the engine's own star transform — Sirius locks to **+22.04°**, Alcyone to **−22.04°**, separation **44.0893°**, ayanamsa **≈82.05° at J2000**, precessing **1.3969712°/century**.
- All seven zodiacal bodies (Sun, Moon, the five visible planets) now report their Ankhological signs on that one ayanamsa — a pure shift of their true longitudes, never fabricated.
- The wheel reads in the iso dome, and the **(`Orientable`)** as-above lens turns to frame it in perspective (eye fixed, heading free).
- Remaining nicety: the aim is parallel to the origin's bearing, so a small eye-vs-dome parallax leaves the origin framed but not dead-centre.

---

## (`§4`/`Next-Rungs`/`Forward-Leverage`)

- **(`I.`/`The-Semantics`)** — owner-defined, from Andean/Egyptian lore; never invented by the engine. The slots are fixed by cosmology; the meaning is the core's freedom. This is the core (free) work — the shell + glue beneath it are now in place for all seven bodies.
- **(`II.`/`Exact-Centre-Aim`)** (optional) — aim the eye→dome-point rather than parallel-to-bearing, to centre the origin in the perspective frame. Pure framing polish; the math is already absolute.

---

## (`§5`/`Invariants`/`Must-Never-Regress`)

- **(`Accuracy-Not-Fiction`)** — every astronomy claim test-backed (Horizons / Polaris=latitude / galactic-centre=Sagittarius / the five zodiac invariants).
- **(`Iso-Lens-Stays-Byte-Identical`)** — the verified so-below view; any lens correction lives only on its own arm.
- **(`Reports-Position-Only`)** — the zodiac names where a body falls; meaning stays the owner's.
- **(`Main`/`Origin`/`Only`)** — no branches/worktrees; commits auto-push; the **(`SSOT`)** is never touched (it carries zero renderer content — **(`CLAUDEBASE`)** is canon-of-record).

---

## (`§6`/`Where-This-Meets-The-Mountain`/`One-Law-Not-Lanes`)

- This engine is **(`One-Thread`/`Not-The-Whole`)**. The mountain's authoritative map is [TODO.md](../TODO.md) (+ [GRILLING.md](../GRILLING.md)) — an 11-gate ladder (governance → CI → toolchain → debt → MCP → synthesis → Solana/GPU → corpus → agent-court → game-engine → world-synthesis). The A-C-A engine touches Gate +4 (game/Vulkan), +1 (GPU compute), −3 (Rust toolchain). Do **not** copy that ladder here — link it; copies rot (the MANIFEST law).
- The deeper meeting point is **(`One-Law`/`Not-A-List`)**: the engine's **(`Forced-Shell`/`Free-Core`)** is the same principle as the **(`CLAUDEBASE`)** [frontmatter standard](../../quarterdeck/frontmatter-standard.md) — substrate verifiable (forced), surface creative (free; the Ankh-DSL styling) — and as the **(`Ankh-DSL`)** transition itself. *Surface = creative practice; substrate = verifiable; neither depends on the other.*
- The work is not carried in separate lanes; it is one mountain moved and changed at once. Navigate the whole by that shared law — that is the point where the projects converge, and the isomorphism Gate 0 (Urca de Lima) is hunting.

---
