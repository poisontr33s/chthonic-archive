---
- Her-North-Star: #!/usr/bin/env markdown
- SID: CLAUDEBASE_NORTHSTAR_V1
- Renderer: Astrological Nassau · astronomy + astrology, 50/50 (§2.6)
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/north-star-constellations.md
- Altitude: Chart-Room · Below-Deck
- Island: San-Salvador · 24.0500,-74.5300 — first landfall; where a course is set
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Storm-Wrack · Sun-Bleached · Lee-Of-The-Law
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Victorian · Renaissance · Carribbean
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
---

# The North Star Constellations
 
*A navigation document for the world renderer. Written for Claude Code (Opus 4.8) to orient by at the start of each session — and for the human who owns the work.*
 
---
 
## 0 · How to read this
 
This is a star chart, not a roadmap. A roadmap assumes fixed dates and a single road; a chart assumes you already know how to walk and only need to know where you are and which way is up.
 
Each session, two moves, in order:
 
1. **Locate.** Determine the current position by reading the repository against the state signals in §5 — not by trusting §6. §6 is only the last-known fix and may be stale.
2. **Compound.** Take the single step that most advances the nearest-incomplete *invariant* (§2) before touching any *fork* (§4). Extend what exists. Do not restart, and do not rebuild a working subsystem in order to switch stars.
The document is **descriptive** about the design space (§§1–4) and **executable** about navigation (§5). Read the first four sections once to hold the shape; run §5 every time.
 
> **Prime directive:** *Advance the nearest-incomplete invariant. Defer every fork until its gate is met. Migrate, never rewrite.*
 
---
 
## 1 · The North Star
 
One world, rendered from the floor.
 
The project is a real-time renderer of a real place — Nassau, New Providence, and the surrounding Bahama Banks — under live weather, built from scratch in Rust on Vulkan (`ash`), with no engine and no middleware beneath it. The renderer is not a means to a game. **The renderer is the work.** Its name is **Astrological Nassau**: astronomy and astrology, held 50/50, over a real place (§2.6) — the astronomy is the positional-accuracy layer nested *inside* the older and fuller field the name points to, never a competitor to it.
 
Its reason for existing — the single thing that justifies refusing every off-the-shelf engine — is one shader: the **bathymetric shallow-water model** that turns depth data into the unmistakable turquoise-over-sand-to-navy gradient of the Banks. Every engine on Earth would force that shader to be written by hand anyway, so hosting one buys nothing and costs control. The North Star is the moment that shader reads correct under a sky that is reading Nassau's actual weather.
 
The ethic — non-negotiable, because it is the reason the project is worth doing at all:
 
- **In-house.** Built, not piggybacked. Custom is the point, not a cost.
- **From the floor.** Tools evaluated upward from raw Vulkan, never adopted downward from convenience.
- **Constraints as discipline.** A deliberately mismatched, hand-owned pipeline is the design space, not a limitation to escape.
- **Hardware floor (soft-locked):** Win11 native (no WSL), RTX 4090 / Vulkan, 64 GB RAM / 24 GB VRAM; dev display AG276QZD 1440p 240 Hz QD-OLED — zero-persistence, which makes it the *unforgiving temporal-validation surface* (§2.4). Revisable on technical cause, not on hype.
---
 
## 2 · The Shared Sky — invariants
 
Roughly seventy percent of this project is the same regardless of which star you steer toward. These are shared infrastructure. They are not optional and they are not where the decisions live. Build them in dependency order; mark each `[built] / [partial] / [absent]` from the actual repo as you go.
 
**2.1 Foundation.** `ash` (Vulkan), `gpu-allocator` (device memory — do not hand-roll a VK allocator), `winit` (window/input), `glam` (math; `DVec*` paths reserved for the ellipsoid fork), `tokio` (the IO plane only). The render loop presents a frame; the IO plane never touches the GPU.
 
**2.2 The hero subsystem — ocean.** Two parts.
 
- *Surface:* cascaded FFT (Tessendorf spectral model) — inverse-FFT on compute into displacement + slope maps, 2–3 cascades at different tile sizes so swell and ripple never share a visible period. On a 4090 the transform is free; the craft is spectrum tuning.
- *Shallow water (the gate):* depth = water-plane height − bathymetry heightfield; march the view ray to the seabed; Beer–Lambert attenuation with wavelength-dependent extinction (red dies first, blue-green carries); bright carbonate-sand bottom showing through the transmittance; Fresnel sky/sun on the surface; subsurface tint in the shallows. **This shader is the project. Until it reads correct, nothing downstream matters.**
**2.3 Sky + weather spine.** Hillaire precomputed atmosphere LUTs (physically-based scattering; correct dusk for free) and raymarched volumetric clouds above. The spine that fuses them into one world rather than three effects bolted together:
 
- the **single live wind vector** (Open-Meteo) is *both* the wind input to the ocean spectrum *and* the cloud advection vector;
- the **timestamp + Nassau coordinates** give the true sun position driving the atmosphere.
One data feed; three subsystems; physically coupled. A front over Nassau thickens the sea and the sky together because they read the same numbers. Keep the wind single-sourced — this coupling is a design invariant, not a coincidence to be refactored apart. But here the sky is spent only as *light* — a sun to scatter, a wind to advect. It is also a structured field in its own right, and that field is half the project's reach: see §2.6.
 
**2.4 Temporal resolve.** Sub-pixel camera jitter → real motion-vector buffer → Streamline → **DLAA, not upscaling** (the card is paid for; spend it on stability). Ocean specular is the textbook TAA failure — a field of crawling sub-pixel highlights — so the MV-fed resolve is load-bearing here, not polish. Streamline has no first-party Rust binding; use **manual-hooking mode**, which is tractable precisely because `ash` already loads Vulkan entry points dynamically. Tag color + depth + motion-vectors + exposure. Note: NGX needs a valid application id or it silently disables DLSS; the frame-generation plugin is precompiled-only (and frame-gen is not part of the hero path regardless).

*Field-tested lesson — KCD1 forensics (2026-06, `../Mythic-Contract/engine-era-collision-KCD1.md`).* A live diagnosis of Kingdom Come: Deliverance on this exact rig isolated the failure this subsystem exists to avoid. An engine compositing several temporal accumulators (GI, TAA history, screen-space AO, shadow cache) at *independent* update rates leans on display persistence to hide their phase disagreement; on a zero-persistence 240 Hz OLED the seams surface as ghosting / "catching-up" in motion that no single per-effect setting removes — the cause is the *composition*, not any one pass. Two invariants carry straight over: (1) **single temporal authority** — every temporal pass (the DLAA resolve, any cloud or reflection reprojection) keys off ONE jitter sequence and ONE motion-vector buffer, the same discipline §2.3 applies to the wind; one clock or it disagrees in motion. (2) **the OLED is the acceptance surface, not a liability** — it hides nothing, so temporal stability that reads clean here is genuinely clean.

*Built as of 2026-06-17 — the scaffold the lesson demands now exists.* One Halton **jitter authority** + a real **RG16F motion-vector buffer** ([`src/render/temporal.rs`](../../src/render/temporal.rs)), and **true per-pixel motion vectors** on the ocean surface — jitter-free (the static camera makes the jitter cancel), exactly zero on static geometry, self-verified by painting the motion buffer (`CHTHONIC_SHOW_MOTION`). The single-temporal-authority invariant is satisfied by construction: one jitter sequence, one motion buffer. What remains is the *consumer* — Streamline / DLAA.
 
**2.5 RT lane (deferred, optional).** `VK_KHR_ray_tracing` for ray-traced water reflections in place of SSR — fixes the off-screen-reflection failure SSR always has over open water. A clean way to spend the RT cores *after* the raster path is solid. Not a gate.
 
**2.6 The celestial field — the sky as structure, not only light.** Placed last in the Shared Sky, but it is *not* a deferred-optional like §2.5 — it is a foundational dimension the first draft of this chart simply omitted, and the omission under-read the project. §2.3 spends the sky as a *light source*: a sun to drive the atmosphere, a wind to advect sea and cloud. That is the sky's **astronomy** — its positional truth — and it is already real and already verified (CLAUDEBASE_COSMOS_V1 / `src/render/cosmos.rs`; solar position checked against JPL Horizons). But the sky over this island is not only a lamp. The renderer's reach is **astronomy + astrology, 50/50**, held the way the Ankhology holds its own 50/50 — **Andean + Egyptologic**. Two lineages, one sky: the Inca ceque-and-solstice geometry and the Egyptian decans and Sothic cycle are the same act of reading the heavens in two tongues; the Dendera zodiac and a horizon-calendar over the Andes are one discipline written twice.
 
Astrology here is neither ornament nor divination-by-default. It is the older and fuller field in which the advanced mathematics first lived — Babylonian ephemerides; Ptolemy's *Almagest* and *Tetrabiblos* from a single hand; spherical trigonometry; the ascendant and the houses as geometry on the celestial sphere. Astronomy is its **positional-accuracy layer**: fewer layers, exactly true. Astrology is the layer above — the structure and the meaning the positions carry — and it has *more* layers, not fewer. So the ethic that governs the water governs the sky without exception: **accuracy, not fiction.** The mathematics must be true *in* the work; meaning rides on true positions or it is nothing.
 
- *Astronomy half — `[built]`, and now far past first light.* Sun, Moon (with phase), the five naked-eye planets, 24 bright stars, and the ecliptic / celestial-equator / galactic-equator reference circles — all topocentric over the island's coordinates, JPL-Horizons / Polaris-verified. The full architecture, the verification authority, and the astrology-half attach-points now have a structured home of their own: **[`celestial-field.md`](celestial-field.md)** (this §2.6 is the strategic gate; that chart holds the mechanics). This is what `cosmos.rs` already is.
- *Astrology half — `[absent]`.* The structured field above the positions — the layered mathematics and meaning the two-lineage Ankhology reads in the sky. Its specific mechanics are **the owner's to set, not the chart's to invent**: the same accuracy ethic that forbids fabricating the seabed forbids fabricating this. This entry exists to mark the dimension as load-bearing and currently unbuilt — the half of the sky the renderer does not yet hold — and it deliberately does *not* appear as a rung in §5.2, because a navigation rung needs detectable mechanics and these are not yet set.
 
This does not move the gate. The bathymetric shallow-water shader (§2.2) is still the one thing that proves the project. What §2.6 corrects is **scope**: the renderer of Nassau is also the renderer of its real sky as a structured field — half the project's depth, not a backdrop hung behind the water.
 
**2.7 The view — compounding lenses, not one chosen camera.** How we look at this world is itself a *set* that compounds, never a single pick. Two lenses are live now and **combine into one better prototype** rather than competing for it:
 
- *Isometric* — the c-RPG inheritance (orthographic, Y 45° / X 35.264°). Kept first-class: with no perspective foreshortening it reads bathymetry and layout honestly — the clearest lens for *what the depth is doing*.
- *Perspective* — true FOV, the view from a plane: the curved-water horizon (the §4 tell), the sun-glint streak stretching toward the eye, the recession of the Banks into haze — the lens for *what the place feels like*.
 
Neither is a debug afterthought. They switch at runtime through one small view abstraction the renderer holds, so further lenses slot in without rework — chief among them the **celestial lens** that looks *up* at the §2.6 sky rather than down at the water. This is migrate-never-rewrite applied to *seeing*: views compound the way subsystems do.
 
---
 
## 3 · The Three Stars — candidates
 
All three inherit the Shared Sky unchanged. They differ only on the two forks of §4. For each: what it commits to, what it buys, what it costs, and the **repo signature** that tells you whether the project is currently standing on it.
 
**Where we stand now — ANNO 2026-06-10 — and why these are no longer three open bets.** The project has already compounded onto concrete ground: a flat-plane prototype (f32 Cartesian, no geodetic), with the hero shallow-water shader proven on real GEBCO (a first cut, self-verified) and the real sun grounded over it. That *is* **★ Lagoon** — standing and load-bearing, not a candidate still to be chosen but the floor we actually built. So read the three below as **trajectory, not an open fork**: we are *on* Lagoon; **★ Ellipsoid** is the known *next milestone* (the curvature + floating-origin retrofit, now legitimately addressable — §4); **★ Monolang** stays layerable per-shader whenever single-language purity outweighs cribbing from a reference. The descriptions are kept because the *reasons* still teach — not because the choice is still pending.
 
### ★ Lagoon — flat plane, pragmatic shaders
Treat New Providence and the Banks as one Cartesian East-North-Up patch; ignore curvature. Shaders in HLSL/WGSL → SPIR-V. CDLOD heightfield over a quadtree of NOAA/GEBCO bathymetry tiles.
 
- **Buys:** the shortest road to proving the hero shader. Fewest moving parts; still wholly yours and Vulkan-native.
- **Costs:** no curved ocean horizon (a real perceptual cue over open water); no path to planetary scale without retrofit.
- **Repo signature:** world coordinates are f32 Cartesian; no `DVec`/geodetic types; no floating-origin rebasing; shaders are `.hlsl`/`.wgsl`.
### ★ Ellipsoid — WGS84 + floating origin, pragmatic shaders
Global coordinates in f64 on the WGS84 ellipsoid; render-space rebased near the camera so f32 never jitters far from origin. Same shaders-in-HLSL/WGSL as Lagoon.
 
- **Buys:** the honest digital twin — real coordinates, correct horizon, expandable past the Bahamas. A small, focused, hand-rolled Cesium core — but you own the water, so you get geometric truth *and* the turquoise.
- **Costs:** time-to-first-pixel. The floating-origin discipline is pervasive — camera, culling, precision everywhere carry it.
- **Repo signature:** geodetic/ECEF types present; an explicit origin-rebasing step in the camera/transform path; f64 in the world layer.
### ★ Monolang — rust-gpu maximal, on either world
Shaders authored in Rust via `rust-gpu` → SPIR-V; minimal crates beyond `ash` + `gpu-allocator`; you own the FFT, the LOD morph, the synchronization, the barriers. CPU and GPU share one language, one vector type, one noise function.
 
- **Buys:** total ownership; a single-language codebase with no shader-language seam — the engine-as-the-artwork reading, matched to evaluating from the floor.
- **Costs:** the most time; `rust-gpu` is community-owned and experimental (nightly-tracking), so you will meet sharp edges no tutorial has sanded.
- **Repo signature:** shaders are `.rs` compiled with the `rust-gpu` backend; shared crates between CPU and GPU code.
---
 
## 4 · The Two Forks — where the decisions actually live
 
**Fork I — world representation:** flat ENU plane ⟷ WGS84 ellipsoid + floating origin. *The tell is the horizon.* **Gate now MET (2026-06-10):** the hero shader reads correct on flat ground (first cut, self-verified), so for the first time this fork is legitimately open — and the standing answer is the one we built: *flat plane* (Lagoon). **Ellipsoid is therefore the next milestone, not a question** — the curvature + floating-origin retrofit, taken when the open-water horizon (a real perceptual cue the §2.7 perspective lens now makes its absence visible) and planetary reach are worth the floating-origin tax. Deferral was correct until the gate; deferring further would be procrastination. The ocean/sky/cloud/temporal spine does not care where its coordinates came from, so this stays a contained (if deep) retrofit, never a foundation rewrite.
 
**Fork II — shader authorship:** HLSL/WGSL → SPIR-V ⟷ `rust-gpu`. **Always available, never big-bang.** SPIR-V is source-language-agnostic, so `rust-gpu` is adopted one shader at a time. Start a shader in HLSL, migrate it to Rust later, touch nothing else. This fork is reversible per-shader; it is the cheapest fork to change your mind on.
 
So the genuine first decision is not *which star*. It is one question: **pay the floating-origin tax up front (open at Ellipsoid), or prove the hero on flat ground and rebase later (open at Lagoon, with Ellipsoid as a known second milestone)?** Monolang layers onto either, shader by shader, whenever single-language purity outweighs having a reference implementation to crib from.
 
---
 
## 5 · Navigation — run this every session
 
**5.1 Compounding principle.** Walk the invariant ladder (2.1 → 2.3) in dependency order. The first rung that is `absent` or `partial` is the session's focus. Do not skip a rung to reach a more interesting one; do not open a fork whose gate (§4) is unmet. *(Amended ANNO 2026-06-10: this ladder is **referential, not gospel.** We deliberately leapt it to prove the hero shader — the project's existential gate — early, and that was sound judgment, not a violation. The principle holds as the default; leaping is sanctioned when the gate **is** the question and the leap is reversible. §6 records where the leap landed.)*
 
**5.2 State-detection checklist** — read against the actual repo, top to bottom; stop at the first unmet:
 
| # | Invariant | Met when… |
|---|-----------|-----------|
| 1 | Foundation (2.1) | an `ash` instance/device/swapchain + `gpu-allocator` present a cleared frame through a `winit` loop |
| 2 | Temporal-resolve scaffold (2.4) | camera jitter + a motion-vector buffer exist; Streamline is hooked (manual-hooking) and DLAA resolves |
| 3 | Terrain + data plane | bathymetry tiles load off the render thread (`tokio`); a CDLOD/clipmap heightfield renders |
| 4 | Ocean surface (2.2 surface) | a cascaded FFT compute pass produces displacement + slope |
| 5 | **Hero shader (2.2 shallow water)** | depth-driven Beer–Lambert + sand bottom + Fresnel reads as correct Bahamas color — **the gate** |
| 6 | Atmosphere (2.3) | Hillaire LUTs render; sun position derives from real time + Nassau coords |
| 7 | Clouds + weather (2.3) | volumetric clouds raymarch; an Open-Meteo poller drives the single wind vector into both sea and clouds |
 
**5.3 Decision procedure.**
 
1. Find the first unmet rung in 5.2. That is the focus. Advance only it.
2. **Reuse before building:** rungs 1–2 substantially overlap the existing c-RPG renderer skeleton — verify and lift that infrastructure; do not rebuild it.
3. Do not approach **Fork I** until rung 5 is met. Until then the project is correctly star-agnostic on world representation.
4. Apply **Fork II** opportunistically and per-shader at any time; never as a rewrite.
**5.4 Guardrails.**
 
- No engine, no middleware. `ash`-native, always.
- IO never on the render thread — data is IO-bound; the GPU sees finished buffers only.
- DLAA, not upscaling.
- Never switch stars by rewriting a working subsystem. Migrate.
- `rust-gpu` per-shader, never big-bang.
- The wind vector stays single-sourced (one live value → sea + clouds).
- One temporal authority: all temporal passes (DLAA, any cloud/reflection reprojection) share a single jitter + motion-vector source — independent temporal clocks disagree in motion and the OLED exposes it (KCD1 lesson, §2.4).
- Render increments self-verify via `scripts/render-smoke.ps1` (build + bounded run + PASS/FAIL on VUIDs/panics, validation layers on) **and the agent reads its own render** — `CHTHONIC_SCREENSHOT` dumps frame ≥5 to a PNG the agent `Read`s, and `CHTHONIC_SHOW_MOTION` paints the motion buffer for inspection. A **load-bearing acceptance gate**, not a footnote: compile + runtime + *visual*, with no human screenshot needed.
- Respect the hardware floor (Win11 native, no WSL, 4090 / Vulkan).
---
 
## 6 · Current Position — last-known fix (verify before trusting)
 
> This section is a hypothesis about the repo, not ground truth. Confirm it against the actual tree in step 5.1, then update it.
 
- **Inherited + lifted substrate (verify-and-lift, never rebuild):**
  - *From the c-RPG vertical slice (`src/render/`):* `ash` init, swapchain, `gpu-allocator`, `winit`, `cmd_draw` + present — **rung 1, built and verified**, and now extended far past it (see the ledger below).
  - *From [`the-long-tack.md`](the-long-tack.md) — PROVEN on the 4090:* the real archipelago twin (`archipelago.json`); the **GEBCO bathymetry pipeline** (real seafloor depth — the literal input to the hero shader, §2.2); the **single-live-wind-vector weather spine** (Open-Meteo, physically coupled — §2.3); Vulkan compute proven to 8.4M cells. This chart is the render front-end of the world the long-tack simulates.
- **Rung ledger — ANNO 2026-06-10, amended 2026-06-17** (we leapt the §5.2 ladder to prove the gate early — §5.1; the 2026-06-17 amendment submerges the temporal scaffold + the full celestial field into the chart — see [`../logbook/03-celestial-field.md`](../logbook/03-celestial-field.md) and [`../logbook/04-structurize-submerge.md`](../logbook/04-structurize-submerge.md)):
  - **1 · Foundation — `[built]`.**
  - **2 · Temporal-resolve — `[scaffold built]`.** One Halton jitter authority + a real RG16F motion-vector buffer (`src/render/temporal.rs`); **true per-pixel motion vectors** on the ocean surface — jitter-free, static-zero, self-verified via `CHTHONIC_SHOW_MOTION`. The §2.4 single-authority invariant holds by construction. Remaining: the consumer — Streamline / **DLAA**. (Was `[absent]`; the scaffold the §2.4 lesson demands now exists.)
  - **3 · Terrain + data plane — `[IO fixed · CDLOD geometry clipmap BUILT]`.** Real GEBCO renders, depth-correct. IO guardrail holds. **CDLOD geometry clipmap sealed 2026-06-23:** 4-level ring mesh (`clipmap_grid(4, 32)`) — 79,872 vertices / 26,624 triangles; cell size doubles per level, finest at centre; `src/render/ocean.rs` + `src/render/renderer.rs:166`. Self-verified: `renders/cdlod-clipmap.png`. Remaining: T-junction stitching (sub-pixel seams accepted at static camera).
  - **4 · Ocean surface — `[4.2d IFFT live · dual-cascade · TAA sealed]`.** `OceanCascade` inner struct extracted; `OceanCompute` holds `[OceanCascade; 2]` + shared compiled pipelines (h0 / evolve / fft). **C0** (ripple/chop): patch=5m, wind=3.8 m/s. **C1** (swell): patch=60m, wind=8.0 m/s. `water.vert` sums both displacement fields at bindings 0+1 (set 0); normals derived from the summed height gradient. Pool upsized to 13 sets (12 compute + 1 graphics). Self-verified: `renders/4-2d-dual-cascade.png`. **TAA Gates 1–4 all sealed 2026-06-23**: offscreen target + history ping-pong (R16G16B16A16_SFLOAT, gpu-allocator) + resolve pass + visual gate (zero VUID, screenshot clean with temporal blend visible). Fixed: startup-resize destroyed descriptors (re-write in `handle_resize`), history ping-pong binding inversion (binding 1 = prev = `(i+1)%2`), pipeline output format mismatch. Self-verified: `renders/render-smoke.png`.
  - **5 · Hero shallow-water shader — `[first cut · self-verified]` — THE GATE, met.** Per-channel Beer–Lambert + carbonate-sand floor + in-scatter to navy + Fresnel + sun glint, reading correct turquoise over real GEBCO. A first cut, not final polish — but the one thing the whole project hinged on is proven.
  - **6 · Atmosphere — `[partial]`.** The real **sun position** is grounded (`src/render/cosmos.rs`; NOAA/Meeus; Horizons-verified) and drives the shader; **Hillaire scattering LUTs are not built** — a true sun, not yet a scattered sky. But the sky **as structure** (§2.6) has gone far past the sun — Moon, the five planets, 24 stars, and the ecliptic / equator / galactic circles all render, topocentric and verified; its architecture now has a dedicated chart, **[`celestial-field.md`](celestial-field.md)**.
  - **7 · Clouds + weather — `[absent]` in the renderer** (the wind spine is proven in the long-tack sim, not yet wired into the draw).
- **Fork I (world):** gate met → **standing on Lagoon** (flat f32 Cartesian). **Ellipsoid = next milestone, not an open question** (§4).
- **Fork II (shaders):** the live path is **GLSL `#version 450` → SPIR-V** — the pragmatic option (note: GLSL, not the earlier HLSL/WGSL guess); `rust-gpu` stays opportunistic, per-shader.
- **View (§2.7):** isometric is live (inherited); **perspective is the next lens** — the two combine into the better prototype. A lens-set, never a swap.
- **Cosmos dimension (§2.6):** astronomy half built and now structured in its own chart — **[`celestial-field.md`](celestial-field.md)** (Sun / Moon / planets / stars + the reference circles, all verified); astrology half `[absent]`, the owner's to define — its attach-points are now named there.
- **Honest next compounding work:** rung 2 **DLAA** consumer (jitter + motion-vector scaffold built, needs Streamline); the §2.7 **perspective lens** (iso + perspective combined); §2.6 **astrology half** (owner-defined sign meanings for 7 bodies — attach-points in `celestial-field.md`, never invented by the agent).
 
*The gate is met, so the question the first draft turned on — "prove the hero on flat ground, or pay the floating-origin tax up front?" — is already answered by what we built: flat ground, gate proven, Ellipsoid next. We do not rebase that. We compound it.*
 
---
 
## 7 · Technique reference — canonical names, so nothing gets reinvented or misremembered
 
| Concern | Canonical technique |
|---|---|
| Ocean surface | Tessendorf cascaded FFT (statistical spectrum, GPU inverse-FFT) |
| Shallow-water color | Beer–Lambert depth attenuation + bottom-albedo transmittance + Fresnel |
| Atmosphere | Hillaire scalable sky/atmosphere precomputed LUTs |
| Volumetric clouds | raymarched Worley–Perlin, coverage-map driven (Nubis lineage) |
| Terrain LOD | CDLOD or geometry clipmaps over a quadtree of DEM/bathymetry tiles |
| Planetary precision | floating-origin / camera-relative rendering, f64 world coords |
| Upscaling / AA | NVIDIA Streamline manual-hooking; DLAA path; tag color/depth/MV/exposure |
| VK memory | `gpu-allocator` (Traverse Research) |
| Data sources | bathymetry: NOAA / GEBCO · imagery: Sentinel-2 · weather: Open-Meteo |
 
---
 
*End of chart.*
