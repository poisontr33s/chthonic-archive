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

# (`The-North-Star-Constellations`)
 
*A navigation document for the world renderer. Written for Claude Code (Opus 4.8) to orient by at the start of each session — and for the human who owns the work.*
 
---
 
## (`0`/`·`/`How-To-Read-This`)
 
This is a star chart, not a roadmap. A roadmap assumes fixed dates and a single road; a chart assumes you already know how to walk and only need to know where you are and which way is up.
 
Each session, two moves, in order:
 
1. **Locate.** Determine the current position by reading the repository against the state signals in §5 — not by trusting §6. §6 is only the last-known fix and may be stale.
2. **Compound.** Take the single step that most advances the nearest-incomplete *invariant* (§2) before touching any *fork* (§4). Extend what exists. Do not restart, and do not rebuild a working subsystem in order to switch stars.
The document is **descriptive** about the design space (§§1–4) and **executable** about navigation (§5). Read the first four sections once to hold the shape; run §5 every time.
 
> **Prime directive:** *Advance the nearest-incomplete invariant. Defer every fork until its gate is met. Migrate, never rewrite.*
 
---
 
## (`1`/`·`/`The-North-Star`)
 
One world, rendered from the floor.
 
The project is a real-time renderer of a real place — Nassau, New Providence, and the surrounding Bahama Banks — under live weather, built from scratch in Rust on Vulkan (`ash`), with no engine and no middleware beneath it. The renderer is not a means to a game. **The renderer is the work.** Its name is **Astrological Nassau**: astronomy and astrology, held 50/50, over a real place (§2.6) — the astronomy is the positional-accuracy layer nested *inside* the older and fuller field the name points to, never a competitor to it.

**(`Amended`/`2026-06-27`/`Scope`)** The renderer is the first instrument. The larger work is a **(`CryEngine-Lineage`/`Matter-And-Myth-Native`)** meta-game-simulation engine: Rust/Ash/Vulkan native, CUDA/C++ compute, Streamline DLAA/Reflex-ready, bathymetry/weather/marine/geology/celestial substrates, and **(`Astrology-Core`/`Cosmology-Glue`/`Astronomy-Shell`)** as the symbolic/scale/observational architecture. CryEngine is the nearest cultural silhouette — terrain, water, real-time world, sandbox ambition — but this is not a clone lineage; it owns the water, and that ownership is the difference. This does not move the gate: the bathymetric shader is still the proof; the renderer proves the engine can hold what matters.
 
Its reason for existing — the single thing that justifies refusing every off-the-shelf engine — is one shader: the **bathymetric shallow-water model** that turns depth data into the unmistakable turquoise-over-sand-to-navy gradient of the Banks. Every engine on Earth would force that shader to be written by hand anyway, so hosting one buys nothing and costs control. The North Star is the moment that shader reads correct under a sky that is reading Nassau's actual weather.
 
The ethic — non-negotiable, because it is the reason the project is worth doing at all:
 
- **In-house.** Built, not piggybacked. Custom is the point, not a cost.
- **From the floor.** Tools evaluated upward from raw Vulkan, never adopted downward from convenience.
- **Constraints as discipline.** A deliberately mismatched, hand-owned pipeline is the design space, not a limitation to escape.
- **Hardware floor (soft-locked):** Win11 native (no WSL), RTX 4090 / Vulkan, 64 GB RAM / 24 GB VRAM; dev display AG276QZD 1440p 240 Hz QD-OLED — zero-persistence, which makes it the *unforgiving temporal-validation surface* (§2.4). Revisable on technical cause, not on hype.
---
 
## (`2`/`·`/`The-Shared-Sky-Invariants`)
 
Roughly seventy percent of this project is the same regardless of which star you steer toward. These are shared infrastructure. They are not optional and they are not where the decisions live. Build them in dependency order; mark each `[built] / [partial] / [absent]` from the actual repo as you go.
 
**2.1 Foundation.** `ash` (Vulkan), `gpu-allocator` (device memory — do not hand-roll a VK allocator), `winit` (window/input), `glam` (math; `DVec*` paths reserved for the ellipsoid fork), `tokio` (the IO plane only). The render loop presents a frame; the IO plane never touches the GPU.
 
**2.2 The hero subsystem — ocean.** Two parts.
 
- *Surface:* cascaded FFT (Tessendorf spectral model) — inverse-FFT on compute into displacement + slope maps, 2–3 cascades at different tile sizes so swell and ripple never share a visible period. On a 4090 the transform is free; the craft is spectrum tuning.
- *Shallow water (the gate):* depth = water-plane height − bathymetry heightfield; march the view ray to the seabed; Beer–Lambert attenuation with wavelength-dependent extinction (red dies first, blue-green carries); bright carbonate-sand bottom showing through the transmittance; Fresnel sky/sun on the surface; subsurface tint in the shallows. **This shader is the project. Until it reads correct, nothing downstream matters.**
**2.3 Sky + weather spine.** Hillaire precomputed atmosphere LUTs (physically-based scattering; correct dusk for free) and raymarched volumetric clouds above. The spine that fuses them into one world rather than three effects bolted together:
 
- the **single live wind vector** (Open-Meteo) is *both* the wind input to the ocean spectrum *and* the cloud advection vector;
- the **timestamp + Nassau coordinates** give the true sun position driving the atmosphere.
One data feed; three subsystems; physically coupled. A front over Nassau thickens the sea and the sky together because they read the same numbers. Keep the wind single-sourced — this coupling is a design invariant, not a coincidence to be refactored apart. But here the sky is spent only as *light* — a sun to scatter, a wind to advect. It is also a structured field in its own right, and that field is half the project's reach: see §2.6.
 
**2.4 Temporal resolve.** Sub-pixel camera jitter → real motion-vector buffer → Streamline → **DLAA, not upscaling** (the card is paid for; spend it on stability). Ocean specular is the textbook TAA failure — a field of crawling sub-pixel highlights — so the MV-fed resolve is load-bearing here, not polish. Streamline has no first-party Rust binding; use **manual-hooking mode**, which is tractable precisely because `ash` already loads Vulkan entry points dynamically. Tag color + depth + motion-vectors + a storage-capable output target, then present through the Streamline Vulkan proxies. Note: NGX needs a valid application id or it silently disables DLSS; the frame-generation plugin is precompiled-only (and frame-gen is not part of the hero path regardless).

*Field-tested lesson — KCD1 forensics (2026-06, `../Mythic-Contract/engine-era-collision-KCD1.md`).* A live diagnosis of Kingdom Come: Deliverance on this exact rig isolated the failure this subsystem exists to avoid. An engine compositing several temporal accumulators (GI, TAA history, screen-space AO, shadow cache) at *independent* update rates leans on display persistence to hide their phase disagreement; on a zero-persistence 240 Hz OLED the seams surface as ghosting / "catching-up" in motion that no single per-effect setting removes — the cause is the *composition*, not any one pass. Two invariants carry straight over: (1) **single temporal authority** — every temporal pass (the DLAA resolve, any cloud or reflection reprojection) keys off ONE jitter sequence and ONE motion-vector buffer, the same discipline §2.3 applies to the wind; one clock or it disagrees in motion. (2) **the OLED is the acceptance surface, not a liability** — it hides nothing, so temporal stability that reads clean here is genuinely clean.

*Sealed as of 2026-06-25 — the semantic path and cold-start handoff both hold.* One *Halton* **(`Jitter-Authority`/`+`/`A-Real`/`RG16F`/`Motion-Vector-Buffer`)** ([`src/render/temporal.rs`](../../src/render/temporal.rs)) feed Streamline DLAA through a C++ bridge and *Rust-FFI:* (`src/render/streamline_bridge.cpp`, `src/render/streamline_ffi.rs`). The DLAA output writes into a dedicated `R8G8B8A8_UNORM` storage-capable history target, then blits to the swapchain, avoiding the fragile swapchain-storage path. Motion vectors are current→previous, UV-scaled to pixels at the FFI boundary, and generated from **(`Unjittered`)** current/previous view-projection matrices while rasterization keeps the jittered projection. The correctness smoke catches *Vulkan*, *NGX*, and *present-hook failures*. The *performance gate is now sealed by async readiness:* `chthonic_sl_init` and `chthonic_sl_set_vulkan_info` run on a background worker while TAA presents immediately; the render loop flips to DLAA only after an atomic ready signal and a main-thread `chthonic_sl_set_dlaa_options` call.
 
**(`2.5`/`RT-Lane`/`Optional`)** `VK_KHR_ray_tracing` for ray-traced water reflections in place of SSR — fixes the off-screen-reflection failure SSR always has over open water. A clean way to spend the RT cores *after* the raster path is solid. Not a gate.
 
**(`2.6`/`The-Celestial-Field`/`The-sky-as-structure`/`Not-Only-Light`)** Placed last in the Shared Sky, but it is *not* a deferred-optional like §2.5 — it is a foundational dimension the first draft of this chart simply omitted, and the omission under-read the project. §2.3 spends the sky as a *light source*: a sun to drive the atmosphere, a wind to advect sea and cloud. That is the sky's **astronomy** — its positional truth — and it is already real and already verified (*CLAUDEBASE_COSMOS_V1* / `src/render/cosmos.rs`; solar position checked against *JPL Horizons*). But the sky over this island is not only a lamp. The renderer's reach is **astronomy + astrology, 50/50**, held the way the Ankhology holds its own 50/50 — **(`Andean`/`+`/`Egyptologic`)** Two lineages, one sky: the Inca ceque-and-solstice geometry and the Egyptian decans and Sothic cycle are the same act of reading the heavens in two tongues; the Dendera zodiac and a horizon-calendar over the Andes are one discipline written twice.
 
Astrology here is neither ornament nor divination-by-default. It is the older and fuller field in which the advanced mathematics first lived — Babylonian ephemerides; Ptolemy's *Almagest* and *Tetrabiblos* from a single hand; spherical trigonometry; the ascendant and the houses as geometry on the celestial sphere. Astronomy is its **(`Positional-Accuracy-Layer`)** fewer layers, exactly true. Astrology is the layer above — the structure and the meaning the positions carry — and it has *more* layers, not fewer. So the ethic that governs the water governs the sky without exception: **(`Accuracy`/`Not-Fiction`)** The mathematics must be true *in* the work; meaning rides on true positions or it is nothing.
 
- *Astronomy half — `[built]`, and now far past first light.* Sun, Moon (with phase), the five naked-eye planets, 24 bright stars, and the ecliptic / celestial-equator / galactic-equator reference circles — all topocentric over the island's coordinates, JPL-Horizons / Polaris-verified. The full architecture, the verification authority, and the astrology-half attach-points now have a structured home of their own: **[`celestial-field.md`](celestial-field.md)** (this §2.6 is the strategic gate; that chart holds the mechanics). This is what `cosmos.rs` already is.
- *Astrology half — `[absent]`.* The structured field above the positions — the layered mathematics and meaning the two-lineage Ankhology reads in the sky. Its specific mechanics are **(`The-Owner's`/`+`/`Claude`/`Code`/`To-Set`/`Not-The-Chart's-To-Invent`)** the same accuracy ethic that forbids fabricating the seabed forbids fabricating this. This entry exists to mark the dimension as load-bearing and currently unbuilt — the half of the sky the renderer does not yet hold — and it deliberately does *not* appear as a rung in §5.2, because a navigation rung needs detectable mechanics and these are not yet set.
 
This does not move the gate. The bathymetric shallow-water shader (§2.2) is still the one thing that proves the project. What §2.6 corrects is **(`Scope`)** the renderer of Nassau is also the renderer of its real sky as a structured field — half the project's depth, not a backdrop hung behind the water.
 
**(`2.7`/`The-View`/`Compounding-Lenses`/`Not-One`/`Chosen-Camera`)** How we look at this world is itself a *set* that compounds, never a single pick. Two lenses are live now and **(`Combine-Into-One-Better-Prototype`)** rather than competing for it:
 
- *Isometric* — the c-RPG inheritance (orthographic, Y 45° / X 35.264°). Kept first-class: with no perspective foreshortening it reads bathymetry and layout honestly — the clearest lens for *what the depth is doing*.
- *Perspective* — true FOV, the view from a plane: the curved-water horizon (the §4 tell), the sun-glint streak stretching toward the eye, the recession of the Banks into haze — the lens for *what the place feels like*.
 
Neither is a debug afterthought. They switch at runtime through one small view abstraction the renderer holds, so further lenses slot in without rework — chief among them the **(`Celestial-Lens`)** that looks *up* at the §2.6 sky rather than down at the water. This is migrate-never-rewrite applied to *seeing*: views compound the way subsystems do.
 
---
 
## (`3`/`·`/`The-Three-Stars-Candidates`)
 
All three inherit the Shared Sky unchanged. They differ only on the two forks of §4. For each: what it commits to, what it buys, what it costs, and the **(`Repo-Signature`)** that tells you whether the project is currently standing on it.
 
**(`Where-We-Stand-Now`/`ANNO 2026-06-10`/`And-Why-These-Are-No-Longer`/`Three-Open-Bets`)** The project has already compounded onto concrete ground: a flat-plane prototype (f32 Cartesian, no geodetic), with the hero shallow-water shader proven on real *GEBCO* (a first cut, self-verified) and the real sun grounded over it. That *is* **(`★`/`Lagoon`)** — standing and load-bearing, not a candidate still to be chosen but the floor we actually built. So read the three below as **(`Trajectory`/`Not-An-Open-Fork`)**: we are *on* Lagoon; **(`★`/`Ellipsoid`)** is the known *next milestone* (the curvature + floating-origin retrofit, now legitimately addressable — §4); **(`★`/`Monolang`)** stays layerable per-shader whenever single-language purity outweighs cribbing from a reference. The descriptions are kept because the *reasons* still teach — not because the choice is still pending.
 
### (`★`/`Lagoon`/`Flat-Plane-Pragmatic-Shaders`)
Treat New Providence and the Banks as one Cartesian East-North-Up patch; ignore curvature. Shaders in HLSL/WGSL → SPIR-V. CDLOD heightfield over a quadtree of NOAA/GEBCO bathymetry tiles.
 
- **(`Buys`)** the shortest road to proving the hero shader. Fewest moving parts; still wholly yours and Vulkan-native.
- **(`Costs`)** no curved ocean horizon (a real perceptual cue over open water); no path to planetary scale without retrofit.
- **(`Repo-Signature`)** world coordinates are f32 Cartesian; no `DVec`/geodetic types; no floating-origin rebasing; shaders are `.hlsl`/`.wgsl`.
### (`★`/`Ellipsoid`/`WGS84-Floating-Origin-Pragmatic-Shaders`)
Global coordinates in f64 on the WGS84 ellipsoid; render-space rebased near the camera so f32 never jitters far from origin. Same shaders-in-HLSL/WGSL as Lagoon.
 
- **(`Buys`)** the honest digital twin — real coordinates, correct horizon, expandable past the Bahamas. A small, focused, hand-rolled Cesium core — but you own the water, so you get geometric truth *and* the turquoise.
- **(`Costs`)** time-to-first-pixel. The floating-origin discipline is pervasive — camera, culling, precision everywhere carry it.
- **(`Repo-Signature`)** geodetic/ECEF types present; an explicit origin-rebasing step in the camera/transform path; f64 in the world layer.
### (`★`/`Monolang`/`Rust-GPU-Maximal-On-Either-World`)
Shaders authored in Rust via `rust-gpu` → SPIR-V; minimal crates beyond `ash` + `gpu-allocator`; you own the FFT, the LOD morph, the synchronization, the barriers. CPU and GPU share one language, one vector type, one noise function.
 
- **(`Buys`)** total ownership; a single-language codebase with no shader-language seam — the engine-as-the-artwork reading, matched to evaluating from the floor.
- **(`Costs`)** the most time; `rust-gpu` is community-owned and experimental (nightly-tracking), so you will meet sharp edges no tutorial has sanded.
- **(`Repo-Signature`)** shaders are `.rs` compiled with the `rust-gpu` backend; shared crates between CPU and GPU code.
---
 
## (`4`/`·`/`The-Two-Forks`/`Where-The-Decisions`/`Actually-Live`)
 
**(`Fork-I`/`World-Representation`)** flat ENU plane ⟷ WGS84 ellipsoid + floating origin. *The tell is the horizon.* **(`Gate-Now-MET`/`2026-06-10`)** the hero shader reads correct on flat ground (first cut, self-verified), so for the first time this fork is legitimately open — and the standing answer is the one we built: *flat plane* (Lagoon). **(`Ellipsoid-Is-Next-Milestone`)** — the curvature + floating-origin retrofit, taken when the open-water horizon (a real perceptual cue the §2.7 perspective lens now makes its absence visible) and planetary reach are worth the floating-origin tax. Deferral was correct until the gate; deferring further would be procrastination. The ocean/sky/cloud/temporal spine does not care where its coordinates came from, so this stays a contained (if deep) retrofit, never a foundation rewrite.
 
**(`Fork-II`/`Shader-Authorship`)** HLSL/WGSL → SPIR-V ⟷ `rust-gpu`. **Always available, never big-bang.** SPIR-V is source-language-agnostic, so `rust-gpu` is adopted one shader at a time. Start a shader in HLSL, migrate it to Rust later, touch nothing else. This fork is reversible per-shader; it is the cheapest fork to change your mind on.
 
So the genuine first decision is not *which star*. It is one question: **(`Pay-Floating-Origin-Tax-Up-Front`)** pay the floating-origin tax up front (open at Ellipsoid), or prove the hero on flat ground and rebase later (open at Lagoon, with Ellipsoid as a known second milestone)? Monolang layers onto either, shader by shader, whenever single-language purity outweighs having a reference implementation to crib from.
 
---
 
## (`5`/`·`/`Navigation`/`Run-This-Every-Session`)
 
**(`5.1`/`Compounding-Principle`)** Walk the invariant ladder (2.1 → 2.3) in dependency order. The first rung that is `absent` or `partial` is the session's focus. Do not skip a rung to reach a more interesting one; do not open a fork whose gate (§4) is unmet. *(Amended ANNO 2026-06-10: this ladder is **(`Referential-Not-Gospel`)**. We deliberately leapt it to prove the hero shader — the project's existential gate — early, and that was sound judgment, not a violation. The principle holds as the default; leaping is sanctioned when the gate **(`Is`)** the question and the leap is reversible. §6 records where the leap landed.)*
 
**(`5.2`/`State-Detection-Checklist`)** — read against the actual repo, top to bottom; stop at the first unmet:
 
| # | Invariant | Met when… |
|---|-----------|-----------|
| 1 | Foundation (2.1) | an `ash` instance/device/swapchain + `gpu-allocator` present a cleared frame through a `winit` loop |
| 2 | Temporal resolve (2.4) | one Halton jitter authority + one motion-vector buffer feed Streamline DLAA; proxied Vulkan submit/present path works; NGX cold-start performance is profiled and no longer blocks first presentation |
| 3 | Terrain + data plane | bathymetry tiles load off the render thread (`tokio`); a CDLOD/clipmap heightfield renders |
| 4 | Ocean surface (2.2 surface) | a cascaded FFT compute pass produces displacement + slope |
| 5 | **(`Hero-Shader-2.2-Shallow-Water`)** | depth-driven Beer–Lambert + sand bottom + Fresnel reads as correct Bahamas color — **(`The-Gate`)** |
| 6 | Atmosphere (2.3) **`[SEALED]`** | Hillaire LUTs render; sun position derives from real time + Nassau coords |
| 7 | Clouds + weather (2.3) **`[SEALED]`** | volumetric clouds raymarch; an Open-Meteo poller drives the single wind vector into both sea and clouds |
 
**(`5.3`/`Decision-Procedure`)**
 
1. Find the first unmet rung in 5.2. That is the focus. Advance only it.
2. **(`Reuse-Before-Building`)** rungs 1–2 substantially overlap the existing c-RPG renderer skeleton — verify and lift that infrastructure; do not rebuild it.
3. Do not approach **(`Fork-I`)** until rung 5 is met. Until then the project is correctly star-agnostic on world representation.
4. Apply **(`Fork-II`)** opportunistically and per-shader at any time; never as a rewrite.
**(`5.4`/`Guardrails`)**
 
- No engine, no middleware. `ash`-native, always.
- IO never on the render thread — data is IO-bound; the GPU sees finished buffers only.
- DLAA, not upscaling.
- Never switch stars by rewriting a working subsystem. Migrate.
- `rust-gpu` per-shader, never big-bang.
- The wind vector stays single-sourced (one live value → sea + clouds).
- One temporal authority: all temporal passes (DLAA, any cloud/reflection reprojection) share a single jitter + motion-vector source — independent temporal clocks disagree in motion and the OLED exposes it (KCD1 lesson, §2.4).
- Render increments self-verify via `scripts/render-smoke.ps1` (build + bounded run + PASS/FAIL on VUIDs/panics, validation layers on) **(`And-The-Agent`/`Reads-Its-Own-Render`)** — `CHTHONIC_SCREENSHOT` dumps frame ≥5 to a PNG the agent `Read`s, and `CHTHONIC_SHOW_MOTION` paints the motion buffer for inspection. A **(`Load-Bearing-Acceptance-Gate`)**, not a footnote: compile + runtime + *visual*, with no human screenshot needed.
- Respect the hardware floor (Win11 native, no WSL, 4090 / Vulkan).
- **(`Main-Is-The-Stable-Road`)** Branches only when explicitly ordered. All other work happens on `main` with scoped staging and a smoke gate before push. Agents do not create branches autonomously.
- **(`No-DR-Fog`)** Every research pass must produce one of: a source-ledger row, a code delta, or an explicit named rejection. A neutral synthesis cloud with no artifact is not a research pass.
---
 
## (`6`/`·`/`Current-Position`/`Last-Known-Fix`/`Verify-Before-Trusting`)
 
> *This section is a hypothesis about the repo, not ground truth. Confirm it against the actual tree in step 5.1, then update it.*
 
- **(`Inherited/`+`/Lifted-Substrate`/`Verify-And-Lift`/`Never-Rebuild`)**
  - *From the c-RPG vertical slice (`src/render/`):* `ash` init, swapchain, `gpu-allocator`, `winit`, `cmd_draw` + present — **rung 1, built and verified**, and now extended far past it (see the ledger below).
  - *From [`the-long-tack.md`](the-long-tack.md) — PROVEN on the 4090:* the real archipelago twin (`archipelago.json`); the **(`GEBCO-Bathymetry-Pipeline`)** (real seafloor depth — the literal input to the hero shader, §2.2); the **(`Single-Live-Wind-Vector-Weather-Spine`)** (Open-Meteo, physically coupled — §2.3); Vulkan compute proven to 8.4M cells. This chart is the render front-end of the world the long-tack simulates.
- **(`Rung-Ledger`/`ANNO-2026-06-10`/`Amended-2026-06-17`/`And-2026-06-25-×3`)** (we leapt the §5.2 ladder to prove the gate early — §5.1; the 2026-06-17 amendment submerges the temporal base + the full celestial field into the chart — see [`../logbook/03-celestial-field.md`](../logbook/03-celestial-field.md) and [`../logbook/04-structurize-submerge.md`](../logbook/04-structurize-submerge.md); the first 2026-06-25 amendment seals the Streamline DLAA bridge, temporal-authority relay, and async cold-start handoff; the second 2026-06-25 amendment seals Hillaire LUTs + GPU-baked cloud noise + volumetric cloud raymarcher, closing the Shared Sky invariant §2.3; the third 2026-06-25 amendment records the GPU profiling gate + Ellipsoid bootstrap):
  - **(`1`/`·`/`Foundation`/`[built]`)**
  - **(`2`/`·`/`Temporal-Resolve`/`[sealed]`/`·`/`Streamline-DLAA-Live`/`·`/`[Async-Cold-Start]`)** One Halton jitter authority + a real RG16F motion-vector buffer (`src/render/temporal.rs`) now feed Streamline DLAA through the live bridge. The Vulkan/Streamline bridge (`src/render/streamline_bridge.cpp` + `src/render/streamline_ffi.rs`) runs manual-hooking mode, caches the proxied `vkQueueSubmit` / `vkQueuePresentKHR`, tags color/depth/MV/output resources per frame, and resolves into a dedicated `R8G8B8A8_UNORM` storage-capable history image before blitting to the swapchain. Motion vectors are semantically aligned: current→previous, UV-scaled to pixels via `mvecScale`, and computed from unjittered current/previous view-projection matrices while the raster path keeps its jittered projection. The NGX cold-start cost is removed from the first-present path: `slInit` and `slSetVulkanInfo` run on a background worker, TAA remains active until an atomic ready signal, then the render loop calls `slDLSSSetOptions` and switches to DLAA with reset semantics. Self-verified with strict DLAA smoke: no VUIDs, no NGX failures, no `presentCommon()` warning, no `slEvaluateFeature` error.
  - **(`3`/`·`/`Terrain`/`+`/`Data-Plane`/`[IO Fixed`/·/`CDLOD-Geometry-Clipmap`/`[BUILT]`)** Real GEBCO renders, depth-correct. IO guardrail holds. **CDLOD geometry clipmap sealed 2026-06-23:** 4-level ring mesh (`clipmap_grid(4, 32)`) — 79,872 vertices / 26,624 triangles; cell size doubles per level, finest at centre; `src/render/ocean.rs` + `src/render/renderer.rs:166`. Self-verified: `renders/cdlod-clipmap.png`. Remaining: T-junction stitching (sub-pixel seams accepted at static camera).
  - **(`4`/`·`/`Ocean-Surface`/`[4.2d IFFT live`/`·`/` Dual-Cascade`/`·`/`TAA-Sealed]`)** `OceanCascade` inner struct extracted; `OceanCompute` holds `[OceanCascade; 2]` + shared compiled pipelines (h0 / evolve / fft). **C0** (ripple/chop): patch=5m, wind=3.8 m/s. **C1** (swell): patch=60m, wind=8.0 m/s. `water.vert` sums both displacement fields at bindings 0+1 (set 0); normals derived from the summed height gradient. Pool upsized to 13 sets (12 compute + 1 graphics). Self-verified: `renders/4-2d-dual-cascade.png`. **TAA Gates 1–4 all sealed 2026-06-23**: offscreen target + history ping-pong (`R16G16B16A16_SFLOAT`, gpu-allocator) + resolve pass + visual gate. The later DLAA path adds its own dedicated `R8G8B8A8_UNORM` storage-capable output/history image before swapchain blit. Fixed: startup-resize destroyed descriptors (re-write in `handle_resize`), history ping-pong binding inversion (binding 1 = prev = `(i+1)%2`), pipeline output format mismatch. Self-verified: `renders/render-smoke.png`.
  - **(`5`/`·`/`Hero`/`Shallow-Water-Shader`/`[First-Cut]`/`·`/`[Self-Verified]`/`THE-GATE`/`Met`)** Per-channel Beer–Lambert + carbonate-sand floor + in-scatter to navy + Fresnel + sun glint, reading correct turquoise over real GEBCO. A first cut, not final polish — but the one thing the whole project hinged on is proven.
  - **(`6`/`·`/`Atmosphere/`/`[SEALED]`/`·`/`[2026-06-25]`)** Hillaire precomputed LUTs fully built and dispatched on frame 0: transmittance → multi-scatter → sky-view (`src/render/atmosphere_compute.rs`). Sun position real, Nassau-grounded, Horizons-verified (`src/render/cosmos.rs`). Sky-view LUT sampled in `water.frag` (set 1 binding 1) for the celestial and ocean-surface Fresnel paths. The sky **as structure** (§2.6) has gone far past the sun — Moon, the five planets, 24 stars, ecliptic / equator / galactic circles all render topocentric and verified; its architecture lives in **[`celestial-field.md`](celestial-field.md)**.
  - **(`7`/`·`/`Clouds`/`+`/`Weather`/`[SEALED]`/`·`/`[2026-06-25]`)** Full volumetric cloud pipeline: GPU-baked Perlin-Worley noise (128³ base + 32³ detail + 512² coverage map, `src/render/cloud_noise_compute.rs` / `assets/shaders/cloud_noise.comp`); raymarched cloud volume (`src/render/cloud_raymarch_compute.rs` / `assets/shaders/cloud_raymarch.comp`) — Beer–Lambert extinction (view + light), Henyey-Greenstein phase (g=0.85), powder-sugar silver lining, 6-sample light cone shadow, Hillaire transmittance LUT sampling, 64 view steps. Wind advection feeds from the same Open-Meteo weather spine driving the ocean spectrum — **the single live wind vector**, preserved as the §2.3 invariant requires. Cloud target (rgba16f, full-res) dispatched before the geometry pass; composited into `water.frag` over sky background (celestial path, binding 2) and blended into the ocean-surface Fresnel sky term. No separate temporal pass — cloud output feeds directly into Streamline DLAA, preserving the §2.4 single-temporal-authority invariant.
- **(`Fork-I-World`/`Ellipsoid-Retrofit-Sites-1-5-Sealed`/`2026-06-26`)** GPU profiling gate: cloud=0.28ms, frame=0.82ms → full-res sealed. WGS84 substrate `src/render/geodesy.rs` built + 7 tests. Camera `GeoAnchor` bridge + `project_ecef_to_render` (East→X, Up/elevation→Y, North→Z) built + 4 tests (48 total). **(`All-Five-Sites-Sealed-2026-06-26`)**: Site 1 — camera Nassau ENU anchor; Site 2 — bathymetry geodetic LLA→ENU mesh (`bbox` parsed, metric central-diff normals, `50f6e15e`); Site 3 — ocean + `water.vert` X_HALF/Z_HALF=200 km ENU (same commit); Site 4 — `HORIZON_EYE` ENU-local (0m E, 0.45m Up, 2.6m N), perspective near/far tagged for Site 6 (`01421da3`); Site 5 — Y_SCALE=1.0 (`render.y` IS ENU metres, depth_m = −v_world_pos.y direct, same commit). Site 6 (f64 world layer + perspective clip-plane scale to ≥400 km) deferred; ELLIPSOID-RETROFIT tags planted in `lens.rs` and `water.frag`.
- **(`Fork-II-Shaders`)** the live path is **GLSL `#version 450` → SPIR-V** — the pragmatic option (note: GLSL, not the earlier HLSL/WGSL guess); `rust-gpu` stays opportunistic, per-shader.
- **(`View`/`§2.7`):** isometric is live (inherited); **perspective is the next lens** — the two combine into the better prototype. A lens-set, never a swap.
- **(`Cosmos-Dimension`/`§2.6`)** astronomy half built and now structured in its own chart — **[`celestial-field.md`](celestial-field.md)** (Sun / Moon / planets / stars + the reference circles, all verified); astrology half `[absent]`, the owner's to define — its attach-points are now named there.
- **(`Honest-Next-Compounding-Work`/`Ellipsoid-Sites-1-5-Complete`/`2026-06-26`)** Fork-I ENU pipeline sealed: bathymetry in WGS84 metres, ocean surface at ±200 km ENU, Y_SCALE=1.0, HORIZON_EYE ENU-local (beach level at Nassau), depth_m = −v_world_pos.y direct. SIGMA calibrated from measured Jerlov IB IOPs (Williamson & Hollins 2022, `38283a7c`). Shared-Sky invariant §2.3 complete (Hillaire + clouds, sealed 2026-06-25). **(`DR-Calibrated-2026-06-27`/`b8b7f60a`)**: SAND → vec3(0.150, 0.172, 0.097) (70% T.testudinum canopy + 30% carbonate sand; CoBOP/Voss 2003 Lee Stocking Island, Hill 2014, Mobley 2005 LUT, cover from Moritsch 2025 PMC12084626). WATER → vec3(0.006, 0.060, 0.185) (Jerlov IB R_inf ∝ b_b/a midpoint; Williamson-Hollins 2022 IOPs + Morel & Maritorena 2001 Case 1; G/B=0.32, R/B=0.032 — red near-zero at depth). **(`Shader-Source-Ledger`/`2026-06-27`/`af6838d5`)** Every numeric constant in the water rendering pipeline cited: `charts/shader-source-ledger.md` (SIGMA/SAND/WATER/Fresnel/lambert + WGS84 + Nassau anchor + lens + cascade patch sizes; atmospheric shader constants cited inline in the compute shaders separately). **(`Bathymetry-Gap3`/`merged-main`/`af6838d5`+`8369e8aa`)** NOAA NCEI ArcGIS ImageServer (DEM_all mosaic, ETOPO 2022 + GEBCO 2024 ~450 m native) via F32 GeoTIFF at 400×300=120,000 cells (~2 km/cell), 97× resolution increase over the OpenTopoData 56×22 sparse-sampling path. **(`Bathymetry-Composite`/`2026-06-27`)** NOAA base + GMRT topo-mask overlay (`--bathymetry-source=composite`): both fetched in parallel; 42.7% Bahamas cells (~51k/120k) replaced with GMRT ~100 m multibeam where valid; smoke PASS (screenshot 142 KB, richer depth variance). Production `charts/bathymetry.json` now composite source. **(`Remaining-Open`)**: Secchi-depth mix() scale (IB Secchi ≈25–30 m → floor_vis threshold tuning; open). Copernicus Marine `cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static` Sentinel-2 SDB 100 m — **the real turquoise candidate** (free+login at marine.copernicus.eu); needs `CMEMS_USER`/`CMEMS_PASS`. §2.6 astrology half (owner-defined, never invented). Rung 2.5 RT reflections (optional). Site 6 deferred (ELLIPSOID-RETROFIT tags planted).
 
*The gate is met, so the question the first draft turned on — "prove the hero on flat ground, or pay the floating-origin tax up front?" — is already answered by what we built: flat ground, gate proven, Ellipsoid next. We do not rebase that. We compound it.*
 
---
 
## (`7`/`·`/`Technique-Reference`/`Canonical-Names`/`So-Nothing-Gets`/`Reinvented`/`Or`/`Misremembered`)
 
| Concern | Canonical technique |
|---|---|
| Ocean surface | Tessendorf cascaded FFT (statistical spectrum, GPU inverse-FFT) |
| Shallow-water color | Beer–Lambert depth attenuation + bottom-albedo transmittance + Fresnel |
| Atmosphere | Hillaire scalable sky/atmosphere precomputed LUTs |
| Volumetric clouds | raymarched Worley–Perlin, coverage-map driven (Nubis lineage) |
| Terrain LOD | CDLOD or geometry clipmaps over a quadtree of DEM/bathymetry tiles |
| Planetary precision | floating-origin / camera-relative rendering, f64 world coords |
| Upscaling / AA | NVIDIA Streamline manual-hooking; DLAA path; tag color/depth/MV/output |
| VK memory | `gpu-allocator` (Traverse Research) |
| Data sources | bathymetry: NOAA / GEBCO · imagery: Sentinel-2 · weather: Open-Meteo |
 
---
 
*End of chart.*
