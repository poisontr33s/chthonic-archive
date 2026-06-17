---
- Her-Celestial-Field: #!/usr/bin/env markdown
- SID: CLAUDEBASE_CELESTIAL_V1
- Renderer: Astrological Nassau · astronomy + astrology, 50/50
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/celestial-field.md
- Strategic-Gate: [north-star-constellations.md §2.6](north-star-constellations.md)
- Altitude: Chart-Room · Below-Deck
- Island: New-Providence · 25.0443,-77.3504 — the site every position is computed over
- Real-Sky: --live (topocentric over New Providence; positions never faked)
- Cosmological-Altitude: --live celestial · CLAUDEBASE_COSMOS_V1 / RENDER_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Victorian · Renaissance · Carribbean
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
---

# The Celestial Field — the structured sky over Nassau

> *Himmelen lyver ikke om hvor; hva den betyr, leser du selv.*
>
> *(The sky does not lie about where; what it means, you read yourself.)*

*The detailed chart for the renderer's sky-as-structure. [`north-star-constellations.md`](north-star-constellations.md) §2.6 holds the strategic gate — why the celestial field is load-bearing and half the project's reach. This holds the architecture: what is built, how it is verified, and where the astrology half attaches. Sibling to [`the-long-tack.md`](the-long-tack.md) (the sim front) — same register, orthogonal axis.*

---

## 0 · How to read this

§2.6 of the chart is the **gate** (one paragraph: the sky is a structured field, not only a lamp; the reach is astronomy + astrology, 50/50). This document is the **mechanics** behind that gate. It exists because the celestial dimension outgrew a chart section: `src/render/cosmos.rs` is the single largest verified subsystem in the renderer, and a paragraph could no longer hold it.

The split is strict and it is the whole discipline:

- **Astronomy is `[built]`** — positional truth, every body, verified against JPL Horizons / Polaris geometry. Documented here as it actually is in the code; nothing claimed that a test does not back.
- **Astrology is `[owner-defined]`** — the older, fuller field above the positions. This document **structures its attach-points** — names where each tradition plugs into the built substrate — but invents none of its mechanics. *The same ethic that forbids fabricating the seabed forbids fabricating the sky's meaning.*

> **Prime directive (sky edition):** *The mathematics must be true* in *the work. Meaning rides on true positions, or it is nothing. Document the built; scaffold the slots; invent neither star nor sign.*

---

## 1 · The two-tongue sky — the 50/50 frame

The reach is **astronomy + astrology, held 50/50**, the way the Ankhology holds its own 50/50 — **Andean + Egyptological**. Two lineages, one sky: the Inca ceque-and-solstice geometry and the Egyptian decans and Sothic cycle are the same act of reading the heavens in two tongues. The Dendera zodiac and a horizon-calendar over the Andes are one discipline written twice.

Astronomy is the **positional-accuracy layer** — *fewer layers, exactly true*. Astrology is the layer above — *more layers, not fewer*: the structure and meaning the positions carry, the field in which the advanced mathematics first lived (Babylonian ephemerides; Ptolemy's *Almagest* and *Tetrabiblos* from one hand; the ascendant and the houses as geometry on the celestial sphere). The renderer holds the first half today and **scaffolds** the second.

---

## 2 · The astronomy half — `[built]`

All of this lives in [`src/render/cosmos.rs`](../../src/render/cosmos.rs) (`RENDER_COSMOS_V1`), the in-house Rust port. Conventions throughout: **azimuth from North increasing East; airless apparent; altitude/azimuth in degrees.** World frame: `+X` East, `+Y` up, `+Z` North.

**The shared spine.** `julian_day()` (proleptic-Gregorian → JD/UTC) and `norm360()` are the base. The load-bearing reuse is **`topocentric_altaz()`** — given a geocentric equatorial position of date (α, δ) + distance, it computes GMST/LST, applies Meeus ch. 40 diurnal parallax, and returns horizontal alt/az. *Every body below the Sun reuses this one tail* — the Moon, the planets, the stars, and the reference circles all funnel through it. One conversion, verified once, shared everywhere.

| Body | Method | Verification |
|---|---|---|
| **Sun** | `solar_position()` — NOAA/Meeus apparent solar position (aberration + nutation in longitude), airless | 3 epochs vs Skyfield/DE421 over New Providence, ≤0.1° altitude |
| **Moon** | `lunar_position()` — truncated Meeus ch. 47 (`MOON_LON_DIST` 47.A, `MOON_LAT` 47.B) → geocentric ecliptic → equatorial → **topocentric parallax** (the Moon's ~1° parallax makes this mandatory); `moon_phase()` ch. 48 illuminated fraction | 3 epochs vs JPL Horizons, ≤0.1° altitude (parallax is the point) |
| **Planets** (Mercury–Saturn) | `planet_position()` over `ELEMENTS` (Standish, *Approximate Positions of the Major Planets*, Table 1, 1800–2050) — `heliocentric_ecliptic()` solves Kepler + rotates perifocal→ecliptic; then **light-time iteration**, geocentric difference, **precession of longitude to date**, ecliptic→equatorial→topocentric | 5 bodies × 2 epochs vs JPL Horizons, ≤0.1° altitude |
| **Stars** (24 brightest, J2000) | `STARS` catalog + `star_position()` — equatorial J2000 → ecliptic → precess longitude → equatorial of date → topocentric (effective infinity, no parallax) | **Polaris test**: its altitude equals the observer's latitude, bearing due north |
| **Ecliptic** | `ecliptic_altaz(λ)` — the ecliptic of date (β=0) → equatorial → topocentric. The zodiac's backbone; the Sun rides it exactly, planets within a few degrees | **Equinox cross-check**: ecliptic λ=0 ≡ equator RA=0; diverges ~23.4° at the solstice |
| **Celestial equator** | `equator_altaz(α)` — δ=0 → topocentric. Meets the horizon due east/west | (same cross-check) |
| **Milky Way** | `galactic_equator_altaz(l)` — `galactic_to_equatorial()` (IAU galactic pole) → the star path. The Andean dark-cloud substrate | **galactic centre** (l=0) maps to Sagittarius, RA ≈266.4° / Dec ≈−28.9° (J2000) |

**The Sun also lights the water.** `sun_push_constant()` packs the world-direction-to-Sun + intensity (`max(sin alt, 0)`, so it goes dark below the horizon) into the shader's push-constant slot — this is the §2.3 lighting path. `moon_push_constant()` mirrors it. `altaz_to_world_direction()` is the shared alt/az→world-vector used by both the lighting path and the rendered discs.

**Computable vs. attested.** Everything in this section is *computable* — a closed-form position with a verifying authority. That is the line the astrology half (§3) sits above: where positions stop being derivable and become *attested* tradition, the chart stops computing and starts scaffolding.

---

## 3 · The astrology half — `[owner-defined slots]`

This is the half the renderer does **not** yet hold, and **must not invent**. What it *can* do — and what this section is — is name the **attach-points**: where each tradition plugs onto a built, verified substrate. The substrate is real; the structure and meaning laid over it are the owner's to set. Source guidance (not gospel, not to be auto-implemented): [`G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md`](../G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md).

| Slot | Built substrate it attaches to | `[owner defines]` |
|---|---|---|
| **Zodiac signs** | the ecliptic great circle (`ecliptic_altaz`) | the 12 × 30° division + its origin (tropical from the vernal point? sidereal?) + meaning |
| **Egyptian decans** | the ecliptic (36 × 10°) + heliacal risings | the 36-fold division, the decan stars, the Sothic-cycle calendar binding |
| **Constellation figures** | the `STARS` catalog positions | the asterism line-graphs + the figures and their meanings (which lineage's sky) |
| **Andean dark-cloud constellations** | the Milky Way band (`galactic_equator_altaz`) | the Yacana (llama), the Mach'acuay, and kin — read in the *dark* clouds, not the bright stars |
| **Houses + ascendant** | the horizon + ecliptic (the rising ecliptic point is computable) | the house system (Placidus / Porphyry / Equal / the Andean ceque-radial analogue) |
| **Ceque / solstice geometry** | the ecliptic cardinal points (solstices/equinoxes are computable) | the radial ceque lines from a centre, the horizon-calendar bearings |

The pattern is always the same: **built substrate → `[owner defines]` structure/meaning**. When the owner sets a slot's mechanics, it earns a §2-style verifier of its own (a sign boundary is a true ecliptic longitude; a decan is a true 10° arc; a heliacal rising is a true Sun-star geometry) — and only then does it cross from attested into computable.

---

## 4 · The lens + the render path

The celestial field draws as **mode 2** of the single shared pipeline (mode 0 seabed, mode 1 ocean surface, mode 2 celestial — `assets/shaders/water.{vert,frag}`). The vertex stage is pass-through for mode 2; the fragment emits disc colour directly, so the bodies are never displaced by the ocean.

`renderer.rs::celestial_field_vertices()` builds the mesh each frame from the §2 functions: `push_body_disc()` makes a camera-facing disc per body, culling below the horizon (intensity ≤ 0) and fading toward it; `planet_style()` / `star_style()` size and tint by magnitude; the Sun/Moon carry phase tint. The three reference circles dot as `CELESTIAL_CIRCLE_POINTS` small discs each — the ecliptic gold, the equator blue, the Milky Way milky-white.

**The celestial lens is parked, not built.** §2.7 of the chart names an upward-looking lens (looks *up* at this field rather than down at the water). Per [`logbook/03-celestial-field.md`](../logbook/03-celestial-field.md) Correction-03A, it must enter as a real view abstraction that compounds — **not** a deterministic scheduler or hidden mode-cycle. Today the field is visible in the existing isometric frame; the dedicated upward lens is chart-bound future work.

---

## 5 · Verification authority

The discipline is the project's whole claim to honesty: *every position ships a verifier, or is named residual.*

- **Authority of record:** [`CLAUDEBASE/quarterdeck/cosmos.py`](../quarterdeck/cosmos.py) — Skyfield + JPL DE421, sub-arcsecond, the Tier-3 generator that *computes, then cross-checks against an authority, then reports the residual.* The Rust port answers to it.
- **Live cross-check:** the JPL Horizons API (apparent, airless, topocentric over the site) — fetched for fixtures via PowerShell `Invoke-WebRequest` with the parameter set in `cosmos.py::horizons_el` (`CENTER='coord@399'`, `QUANTITIES='4'`, `APPARENT='AIRLESS'`).
- **The test invariants** (in `cosmos.rs` `#[cfg(test)]`, run `cargo test render::cosmos`): Sun/Moon/planet alt/az within tolerance of Horizons/Skyfield; **Polaris altitude = latitude**; **ecliptic ≡ equator at the equinox, diverges at the solstice**; **galactic centre = Sagittarius**.
- **Visual self-verification:** `scripts/render-smoke.ps1` builds + bounded-runs + screenshots; the agent `Read`s the PNG (`CHTHONIC_SCREENSHOT`) and confirms the field by eye — the gold ecliptic threading the Sun, the planets strung along it, the Milky Way crossing at the true galactic tilt.

---

## 6 · Current position + next

- **Built and committed to main:** Sun, Moon (+ phase), the five naked-eye planets, 24 bright stars, and the ecliptic / celestial-equator / galactic-equator reference circles — all topocentric over New Providence, all verified, all rendered as mode 2.
- **The Milky Way is the Andean substrate** — the band the dark-cloud constellations are read in. Built as a great circle; the figures are the owner's (§3).
- **Next, in two distinct hands:**
  - *Owner's:* any astrology-half slot in §3 — the moment a division or a figure is set, it gets a §2-style verifier and crosses into computable.
  - *Renderer's (chart-bound):* the upward **celestial lens** (§2.7); optional fidelity (the Milky Way as a true band rather than a midline; true Sun/Moon angular size — today they are oversized for legibility, *position is physics, size is licence*).

---

## 7 · Provenance

- Code: [`src/render/cosmos.rs`](../../src/render/cosmos.rs) (`RENDER_COSMOS_V1`); render wiring in [`src/render/renderer.rs`](../../src/render/renderer.rs); shaders `assets/shaders/water.{vert,frag}`.
- Authority: [`CLAUDEBASE/quarterdeck/cosmos.py`](../quarterdeck/cosmos.py) (`CLAUDEBASE_COSMOS_V1`).
- Strategic gate: [`north-star-constellations.md`](north-star-constellations.md) §2.6 / §2.7.
- Sibling front: [`the-long-tack.md`](the-long-tack.md) — the sim that computes the field this renderer draws.
- Record: [`logbook/03-celestial-field.md`](../logbook/03-celestial-field.md) (the field crossed into frame); [`logbook/04-structurize-submerge.md`](../logbook/04-structurize-submerge.md) (this chart's commissioning).
- Research (source guidance only, never auto-built): [`G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md`](../G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md).
- Commits (astronomy half): planets `b69d9f78` · stars `f06843e6` · ecliptic + equator `f779896c` · Milky Way `b24636b0`.

---

*SID: CLAUDEBASE_CELESTIAL_V1 · live · the sky as structure · positions true, meaning owner-read.*
