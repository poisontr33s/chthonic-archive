---
- Her-Long-Tack: #!/usr/bin/env markdown
- SID: CLAUDEBASE_LONGTACK_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/the-long-tack.md
- Altitude: Chart-Room · Below-Deck
- Island: San-Salvador · 24.0500,-74.5300 — first landfall; where a course is set
- Heat-Index: Doldrums · Rope-&-Rum · Skin-Dipped
- Cosmological-Altitude: Nautical · Victorian · Renaissance · Carribbean
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
---

## (`☥`/`THE-LONG-TACK`/`Barometer`/`→`/`Ladder`/`→`/`Real-Data`/`·`/`DSL-Parked`)

> *En lang slag holdes ikke ved å se på roret, men på kysten man ennå ikke har nådd.*

  > *(A long tack is held not by watching the helm, but the coast you have not yet reached.)*

---

- *— The candidate we fell into, stored so we do not lose it.*

  - *— Three arcs.*

    - *— The first is nearly working; the second is unbuilt but already in the repo, only unseamed; the third is not a phase — it is peppered through both, and it lives or dies by one test.*

---

**(`Reading-Order-Of-The-Arcs`/`Is-The-Sequence-Of-Belief`/`A-Thing`/`Earns-The`/`Next-Arc`/`Only-By-Working`/`In-This-One`)**

- *— **(`Two-Ladders`/`Do-Not-Conflate`)** — this chart's* `L−5 → L+1` *rungs are ONE engineering line: the barometer → sim → DSL arc, climbed by dependency-depth. They are NOT the world-level* `Gate −5 → +5` *of* [`../The-Savant-High-Bounties/TODO.md`](../The-Savant-High-Bounties/TODO.md) *(whole-repo health — governance · CI · toolchain · MCP · debt, the grilling lane). 

    - *— Same depth-notation, orthogonal axis:* `L−2` *here (advection, PROVEN) is not* `Gate −2` *there (architectural debt, open). A rung closed on this tack closes THIS arc — never a world-gate.*

---

## (`ARC`/`I`/`·`/`THE-BAROMETER`/`Concept`/`-→`/`Working`/`Acceptable`)

> *— The data + notation foundation. When it emits a clean boundary-condition payload, **(`Arc-II`)** — may begin.*

  - *— **(`[x]`/`B-1`)** — intrinsic pressure:* `sha256(body)` *→ SKY·AIR·MOOD over the real 12×12×12 = 1,728 space*

    - **(`[x]`/`B-2`)** *— real geography:* `archipelago.json` *twin (8 islands · coords · elevation · decks)*

      - *— **(`[x]`/`B-3`)** — live sky: Open-Meteo apparent-temperature + WMO condition, fetched never stamped*

        - *— **(`[x]`/`B-4`)** — forecast probability map: precip-probability, next 12h, density grid*

          - *— **(`[x]`/`B-5`)** — hot-reload:* `--watch` *(event-driven) +* `--stamp` *(fixpoint) +* `--interval=<ms>` *for the live sky*

            - *— **(`[x]`/`B-6`)** — colour heat-map: —* `--live --color`*, — two axes (heat hue + WMO sky-word)*

              - *— **(`[x]`/`B-7`)** — sea-chart render:* `--chart` *plots the twin by real lat/lon*

                - *— **(`[x]`/`B-8`)** — tracked in git: (whole folder, comprehensive allowlist)*

                  - *— **(`[x]`/`B-9`)** —* **(`PROVEN`)** *(terminal): the true 1,728-bucket histogram.* `barometer.ts --histogram` *buckets every tracked* `.md` *(1,220 files) by* `sha256(body) → (SKY,AIR,MOOD)`*; 803 / 1,728 cells filled (46.5%), all three axes flat (~102 each) — the generator is fair, no dead zones — superseding the Library-Study PNG that binned to 4–5 states and only labelled 1,728. The inline-SVG embed of it folds into B-10's Index.html.*

                    - *— **(`[~]`/`B-10`/`KILLED`)** — the self-contained* `Index.html` *is dropped: it was copy-pasted slop from a search dump, an artifact-proto before it was ever accurate. **(`The-Savant-Grade-Undercellar`)** is scrap mechanics — given no weight. The histogram (B-9) stands on its own in the terminal; the real surface is the sim over real data, not an HTML page.*

                      - *— **(`[x]`/`B-11`)** — **(`Freeze-The-Data-Contract`)**: frozen by L−5 — the* `Island{lat,lon,elev,seed}` *std430 struct (16 B), sourced from* `archipelago.json`*; GLSL and Rust agree on it. The seam-side handshake holds.*

                        - *— **(`Acceptance`)** — the barometer is proven as data + notation, and B-11 emits the boundary conditions **(`Arc-II`)** reads.*

---

## (`ARC`/`II`/`·`/`The-Ladder`/`The-Vulkan-Field-Sim-Over-Real-Topology`)

> *— Unbuilt — but every piece already lives in the repo. The unbuilt thing is the — **(`Seam`)** — Heavy on purpose: GPU because the challenge is the fuel.*

  - *— **(`<!--`)** — The ladder is the sim, but the sim is not the ladder. The ladder is the verified sequence of gates; the sim is the thing behind those gates, which may be built in any way that proves it works. — **(`-->`)**.*

    - *— **(`Substrate-Already-Proven`)** —* `vulkan-lab/cli-renderer` *— runs Vulkan compute on the 4090 (euler_score · ascii_downsample · dirty_diff · headless device select, through G7). The barometer (Arc I) is the boundary conditions. Nobody has connected them.*

      - *— The sim climbs its own ladder; each gate a **(`Verified-State`)**, which is ladder theory made executable, not metadata:*

        - *— **(`[x]`/`L−5`/`·`/`Seam`/`PROVEN`)** — on the RTX 4090; —* `vulkan-lab/cli-renderer/src/bin/archipelago_field.rs` *— *+ —* `shaders/archipelago_field.comp.glsl` *— Twin → island SSBO → inverse-distance compute → 56×22 field → ANSI relief. Cat-Island (63 m) renders the hot-spot, Bimini (6 m) the cool; field 6–62 m. Barometer → GPU → render, one pass —* `cargo run --bin archipelago_field`*.*

          - *— **(`[x]`/`L−4`/`·`/`Iterate`/`PROVEN`)** — on the 4090; —* `archipelago_diffuse.rs` *— + —* `shaders/archipelago_diffuse.comp.glsl` *— Islands pinned as Dirichlet sources; field relaxes over N ping-pong steps, memory-barrier between each. 240 steps → a diffusion plume from Cat-Island, the central cluster blends, Great-Inagua stays isolated (topology respected). It evolves, not interpolates; —* `cargo run --bin archipelago_diffuse -- --steps N`*.*

            - *— **(`[x]`/`L−3`/`·`/`Boundary-Conditions`/`PROVEN`)** — on the 4090; —* `barometer.ts --boundary=<file>` *— fetches Open-Meteo —* `apparent_temperature` *— per island → live seeds. A failed fetch falls back to the mean of the resolved islands, never elevation — the field stays in °C, never mixes a metre value in. The diffuse bin reads —* `seed` *— as the Dirichlet value and warm-starts the open sea at the mean seed, so 240 ping-pong steps converge to a true —* `27.6–30.2 °C` *— field; Great-Inagua, the southern warm-bloom, San-Salvador the cool note. The sim breathes the real sky, not a hash; —* `bun barometer.ts --boundary=live_boundary.json && cargo run --bin archipelago_diffuse -- ../../live_boundary.json`*.*

              - *— **(`[x]`/`L−2`/`·`/`Advection`/`PROVEN`)** — on the 4090; —* `archipelago_advect.rs` *— + —* `shaders/archipelago_advect.comp.glsl`*. —  The barometer now fetches —* `wind_speed_10m` *— + —* `wind_direction_10m` *— per island (vector-mean fallback — averaging compass degrees directly is wrong). The bin builds a velocity field by inverse-distance weighting and carries a seeded warm blob downwind by semi-Lagrangian backtrace (Stam's stable advection; unconditionally stable, no CFL limit). The live easterly trades (from ~92°) drift the New-Providence blob ~9 cells WEST off its origin: the origin cools, the trail warms. It MOVES, it doesn't merely spread — the asymmetry is the proof; —* `cargo run --bin archipelago_advect -- ../../live_boundary.json`*.*

                - **(`[x]`/`L−1`/`·`/`Ladder-As-Phases`/`—`/`PROVEN`)** *on the 4090:* `archipelago_sim.rs`*, composing the two existing rungs (NO new shader — the rungs ARE the operators). The four phases run as one gated state machine:* `instantiate → (diffuse ⋈ advect)* → converge → render`*. Instantiate seeds temperature sources (L−3) + a wind velocity field (L−2); each OUTER iteration relaxes 30 diffusion steps then transports 8 advection steps; the* **(`converge`)** *gate reads the field back and halts on* `max|Δ| < ε`*. Operator-split advection-diffusion ran to a verified fixpoint — steady state at outer 21,* `max|Δ|` *falling monotonically* `1.20 → 0.019 °C`*. Verified non-decorative against pure diffuse (`--advect 0` settles at outer 9): advection measurably stirs the system, more than doubling the outers to balance — it is in the equation, not on top of it; —* `cargo run --bin archipelago_sim -- ../../live_boundary.json`*.*

                  - *— **(`[x]`/`L-0`/`·`/`Render`/`—`/`PROVEN`)** (render); —* `archipelago_sim --html=<file>` *— emits a self-contained SVG heat-map of the steady field — a SMOOTH blue→red gradient (the terminal can only band into 5 ANSI colours), island overlay, live caption — openable in any browser, zero dependencies. Live-derived, so it is a view, never committed (like —* `live_boundary.json`*) — Modular enough to drop into — **(`The-Savant-Grade-Undercellar_Library_Study`)** — as an Index.html/png. *—* `cargo run --bin archipelago_sim -- ../../live_boundary.json --html=sim_render.html`*. — Deferred (optional): hot-reload; the — **(`Arc-I`)** —* `--watch` *— machinery already exists in the barometer; not yet wired into a sim loop.*

                    - *— **(`[x]`/`L+1`/`·`/`Perform`/`—`/`PROVEN`)** — on the 4090; —* `archipelago_sim` *— wall-clocks its own run. The full advection-diffusion convergence — 24 outers × 38 dispatches = —* `912` *— GPU dispatches to a verified steady state — costs; —* `3.5 ms` *— of GPU submit→wait — (*`3.9 µs/step`*), —* `4.8 ms` *— wall including the 24 CPU readbacks the converge gate needs. The whole heavy sim is a —* `~5 ms` *— operation; heavy verified as FAST, not just big; —* `cargo run --bin archipelago_sim -- ../../live_boundary.json`*.*

                      - *— **(`Acceptance`)** — a real field simulation over real archipelago topology — GPU-accelerated, ladder-gated, fed live by the barometer.*

---

## (`ARC`/`IV`/`·`/`REAL-DATA-LAYERS`/`The-Data-Archaeology`/`Past-The-Tea-Spoon`)

> *— The sim ran on a tea-spoon: two Open-Meteo fields (apparent-temp + wind), self-sourced, no rigor. This arc feeds it the REAL multi-disciplinary data-ocean of the archipelago — each layer a field or boundary the proven engine already accepts. Signal varies by discipline; rigor means naming the empty layers too.*

  - *— **(`[x]`/`M-1`/`·`/`GEBCO-Bathymetry`/`THE-MEDIUM`)** —* **(`PROVEN`)**: `barometer.ts --bathymetry` *pulls real GEBCO 2020 seafloor depth (Open Topo Data, free/no-key) over the sim's exact 56×22 grid →* `charts/bathymetry.json` *(stable, committed). The sim marks land (elev ≥ 0) as a no-flux barrier; the diffuse shader flows heat only through sea — around the real islands, along the channels. 172 land / 1,060 sea; Cuba renders at the SW corner, Great-Inagua ringed by its own footprint. The sim stopped being flat — it runs on the real Bahama Bank.*

    - *— **(`[x]`/`M-2`/`·`/`Marine`/`SST`)** —* **(`PROVEN`)** —* `barometer --boundary` *— batches the Open-Meteo Marine API → real —* `sea_surface_temperature` *— + ocean-current per island. The sim sources the sea from SST (prefer sst → air → elevation) — a real correction, not cosmetic: SST differs from air by up to 2.3 °C (San-Salvador air 25.5 vs sea 27.8). Currents are recorded (oceanographic flows-to, m/s) but NOT the advection driver — measured 0.06–0.33 m/s, ~20× weaker than wind, too gentle to visibly transport (the calm-banks truth); advection stays wind-driven surface drift. — **(`M-2b`)** (pure-current, near-static) deferred.*

      - *— **(`[ ]`/`M-3`/`·`/`Hurricanes`/`Episodic-Forcing`)** — HIGH signal, region-central: NOAA NHC HURDAT2 best-track + live GIS. A passing storm is a moving low-pressure + high-wind perturbation swept across the grid — not steady state.*

        - *— **(`[ ]`/`M-4`/`·`/`Weather-Depth`/`Mist-+-Storm`)** — derived, not fetched: Open-Meteo already exposes humidity, dew-point, visibility, CAPE, pressure. Mist = RH near 100 % + small dew-spread + low visibility (or* `weather_code` *45/48); storm = CAPE + pressure-low + code 95/96/99. Fields computed from data we already pull.*

          - *— **(`Seismic`/`THE-NAMED-VOID`)** — LOW signal here, and rigor says so: the carbonate platform has no faults, ~0.54 M4+/yr, strongest-since-1900 a M4 in Feb 2024. USGS FDSN is one trivial bbox query — run once to confirm the void, never a field. (Active Caribbean seismicity is outside our matrix.)*

            - *— **(`Acceptance`)** — the sim is fed by real geophysical data across disciplines, each layer signal-verdicted for THIS region — not a two-field tea-spoon.*

---

## (`ARC`/`III`/`·`/`THE-DSL`/`Peppered`/`Not-Phased`)

> *— Not a discrete stage. Woven into Arc I and II incrementally — the barometer's twin and the ladder's gate-sequence are its first real sentences. It carries — **(`One-Law-And-One-Kill-Switch`)**.*

  - *— **(`[ ]`/`D-0`/`·`/`Observe`)** — extract the grammar already in use (Phase 0). First sentences: the —* `archipelago.json` *— shape — + — the ladder gate-sequence.*

  - *— **(`[ ]`/`D-1`/`·`/`Parser`)** — Rust (pest/chumsky) over the observed grammar; PyO3/TS bindings as the seam needs them.*

    - *— **(`[ ]`/`D-2`/`·`/`Execute`)** — AST + minimal interpreter.— **(`First-Executable load`)** — express the barometer's twin *or the ladder's gate-chain in the DSL and run it.*

      - *— **(`[ ]`/`D-3`/`·`/`Translation-Boundary`)** — quarantine pretrained bias at the edge **(`Phase-3`)**.*

---

### (`Design-Law`/`Spelling`/`VS`/`Format`/`The-Question`/`Settled`)

- *— The **(`PEG`)** — parses by — **(`Structure`/`Shape`/`Never-By-Dictionary-Correctness`)**.*

  - *— A misspelled ticked-id is still a valid ticked-id. — ``,`` —* `inherance` *— ``,`` —* `occured` *— ``,`` —* `privilaged` *— ``,`` — parse identically to their "correct" forms — the grammar matches backtick-wrapped · Title-Case · arrow-chained · slash-tokened shape, and spelling is; — **(`Orthogonal-To-Validity`)**.*

    - *— Spelling mistakes are neither good nor bad to the parser; they are invisible to it.*

      - *— **(`Format-Consistency`/`IS`/`The-Grammar's-Concern`)** —Separators — **(`-`/`VS`/`·`/`VS`/`/`)** — wrapping, casing convention, arrow syntax — that is what the PEG pins.*

        - *— So; — **(`Tolerate-Spelling`/`Enforce-Structural-Format`)** — It is the inverse of natural-language linting — we lint shape, never spelling. The project's idiosyncratic spellings are therefore safe; only format drift is a defect.*

---

### (`Kill-Switch`/`The-Test`/`Not-The-Artifact`)

- *— The DSL earns continuation **(`Only-By-Executing`)**.*

  - *— If after D1 it parses nothing real, or after D2 it runs nothing plain code couldn't already do — **(`Kill-It`)**.*
    
    - *— It is forbidden from becoming a second monolith-to-worship.*
    
      - *— Belief is in the test, not the notation. *(This clause exists because the — **(`SSOT`)** — itself is the warning: revered, dense, and so far inert.)*

---

## (`Cross-Cutting-Laws`/`Apply-To-Every-Arc`)

- *— 1. — **(`Live`/`=`/`View`/`Never-Stamped`/`.`/`Stable`/`=`/`File`)** — The forecast and the sky are summoned, not frozen; geography and pressure are written. (The honesty rule Arc I proved.)*

  - *— 2. — **(`Every-Claim-Ships-A-Verifier-Or-Is-Named-Residual`).** — No "done" without a way to falsify it.*

    - *— 3. — **(`Lore-That-Works`)** — the metaphor and the utility are the same gesture. Nothing decorative survives.*

      - *— 4. — **(`Heavy-Is-The-Fuel`/`—`/`Inverted`)** — The challenge is the lightness; piecemeal is the drain. When unsure, take the harder cut.*

        - *— 5. — **(`Compound-Don't-Replace`)** Barometer feeds the ladder feeds the real-data layers; each compounds onto the last (GEBCO onto the proven sim).*
        
          - *— The Library-Study dumps were reclassified as scrap — set aside, given no weight; compounding is onto what executes, not onto slop.*

---

## (`Where-We-Are`/`Now`)

- *— **(`Arc-I`)** — complete through; — **(`B-9`/`+`/`B-11`)** — the barometer is proven as data + notation (the histogram showed the generator fair). — **(`B-10`)** KILLED —* `Index.html slop`. *— The barometer is now also the data-archaeology instrument; —* `--histogram` *— · —* `--bathymetry` *— · —* `--boundary`*.*

  - *— **(`Arc-II`/`COMPLETE`)** — L−5…L+1 all PROVEN on the 4090, AND now fed real GEBCO bathymetry **(`M-1`)** — the* `~5 ms` *advection-diffusion sim runs over the real Bahama Bank, flowing around actual island geometry. Only optional tail: L0 hot-reload.*

    - *— **(`Arc-IV`/`ACTIVE`)** — the real direction now; multi-disciplinary data layers. — **(`M-1`)** — GEBCO bathymetry (the medium) — **(`+`/`M-2`)** — marine SST (real sea-temp sources) both landed; the sim runs on two real data layers over real topology. Next — **(`M-3`)** — hurricanes (HURDAT2 — the episodic, dramatic layer).*

      - *— **(`End-Goal-Proof`/`It-Compounds`)** — the sim is resolution-scalable now —* `--grid=WxH`*, default 56×22 (The same Vulkan/Rust kernels ran); —* `1,232 → 8.4M cells (6800×` *— on the 4090 — the nascent plan compounds to high-end SCALE. The sweep mapped the next ENGINE frontier; —* `HOST_COHERENT` *— buffers cap throughput at ~12 GB/s vs the 4090's ~1 TB/s —* **(`Device-Local`/`Memory`/`+`/`Staging`)** *— is the next hardening. Three fronts run in parallel now: DATA (M-3…), ENGINE (device-local → CUDA/TensorRT later), & —* **(`RENDER`)** *— the real-time visual front-end charted in —* [`north-star-constellations.md`](north-star-constellations.md) *—which — **(`Consumes-Not-Rebuilds`)** — this sim's proven data plane —* `charts/bathymetry.json` *— (→ the hero shallow-water shader · the single-wind spine → its §2.3): the sim computes the field, the renderer draws the turquoise. **(`The-Seam`/`=`/`The-Data-Plane`)**.*

        - *— **(`Arc-III`/`PARKED`)** — the DSL stays at D0, observed, kill-switch intact. Deliberately NOT a gate — we do not stalemate on it. It earns continuation only by executing, later.*

          - *— Next move —* **(`M-3`)** *— hurricanes; a real HURDAT2 storm track (e.g. Dorian over Grand Bahama, 2019) swept across the grid as moving low-pressure + high-wind forcing: the episodic, dramatic layer (bathymetry + marine SST were the quiet-but-true ones). Compounds onto the proven sim; no DSL, no slop.*

---

*SID: CLAUDEBASE_LONGTACK_V1 · live · the course, not the helm · 2026-06-06*
