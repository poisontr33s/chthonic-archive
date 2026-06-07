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

## (`☥`/`THE-LONG-TACK`/`Barometer`/`→`/`Ladder`/`→`/`DSL`)

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

            - *— **(`[x]`/`B-6`)** — colour heat-map:* `--live --color`, *two axes (heat hue + WMO sky-word)*

              - *— **(`[x]`/`B-7`)** — sea-chart render:* `--chart` *plots the twin by real lat/lon*

                - *— **(`[x]`/`B-8`)** — tracked in git: (whole folder, comprehensive allowlist)*

                  - *— **(`[ ]`/`B-9`)** — the true 1,728-bucket histogram: (terminal + inline SVG). The fairness-verifier of our generator — supersedes the Library-Study PNG, which binned to 4–5 states and only labelled 1,728*

                    - *— **(`[ ]`/`B-10`)** — a real self-contained* `Index.html` *(one file, no GPU: sea-chart SVG + histogram + forecast) — replaces the saved-Google-search dump as the actual study surface*

                      - *— **(`[x]`/`B-11`)** — **(`Freeze-The-Data-Contract`)**: frozen by L−5 — the* `Island{lat,lon,elev,seed}` *std430 struct (16 B), sourced from* `archipelago.json`*; GLSL and Rust agree on it. The seam-side handshake holds.*

                        - **(`Acceptance`)**: *the barometer is proven as data + notation, and B-11 emits the boundary conditions **(`Arc-II`)** reads.*

---

## (`ARC`/`II`/`·`/`The-Ladder`/`The-Vulkan-Field-Sim-Over-Real-Topology`)

> *Unbuilt — but every piece already lives in the repo. The unbuilt thing is the **(`Seam`)**. Heavy on purpose: GPU because the challenge is the fuel.*

  - *— **(`<!--`)** The ladder is the sim, but the sim is not the ladder. The ladder is the verified sequence of gates; the sim is the thing behind those gates, which may be built in any way that proves it works. **(`-->`)**.*

    - *— **(`Substrate-Already-Proven`)**:* `vulkan-lab/cli-renderer` *runs Vulkan compute on the 4090 (euler_score · ascii_downsample · dirty_diff · headless device select, through G7). The barometer (Arc I) is the boundary conditions. Nobody has connected them.*

      - *— The sim climbs its own ladder — each gate a **(`Verified-State`)**, which is ladder theory made executable, not metadata:*

        - **(`[x]`/`L−5`/`·`/`Seam`)** *—* **(`PROVEN`)** *on the RTX 4090:* `vulkan-lab/cli-renderer/src/bin/archipelago_field.rs` *+* `shaders/archipelago_field.comp.glsl`*. Twin → island SSBO → inverse-distance compute → 56×22 field → ANSI relief. Cat-Island (63 m) renders the hot-spot, Bimini (6 m) the cool; field 6–62 m. Barometer → GPU → render, one pass.* `cargo run --bin archipelago_field`.

          - **(`[x]`/`L−4`/`·`/`Iterate`)** *—* **(`PROVEN`)** *on the 4090:* `archipelago_diffuse.rs` *+* `shaders/archipelago_diffuse.comp.glsl`*. Islands pinned as Dirichlet sources; field relaxes over N ping-pong steps, memory-barrier between each. 240 steps → a diffusion plume from Cat-Island, the central cluster blends, Great-Inagua stays isolated (topology respected). It evolves, not interpolates.* `cargo run --bin archipelago_diffuse -- --steps N`.

            - **(`[x]`/`L−3`/`·`/`Boundary-Conditions`)** *—* **(`PROVEN`)** *on the 4090:* `barometer.ts --boundary=<file>` *fetches Open-Meteo* `apparent_temperature` *per island → live seeds. A failed fetch falls back to the mean of the resolved islands, never elevation — the field stays in °C, never mixes a metre value in. The diffuse bin reads* `seed` *as the Dirichlet value and warm-starts the open sea at the mean seed, so 240 ping-pong steps converge to a true* `27.6–30.2 °C` *field — Great-Inagua the southern warm-bloom, San-Salvador the cool note. The sim breathes the real sky, not a hash.* `bun barometer.ts --boundary=live_boundary.json && cargo run --bin archipelago_diffuse -- ../../live_boundary.json`.

              - **(`[x]`/`L−2`/`·`/`Advection`)** *—* **(`PROVEN`)** *on the 4090:* `archipelago_advect.rs` *+* `shaders/archipelago_advect.comp.glsl`*. The barometer now fetches* `wind_speed_10m` *+* `wind_direction_10m` *per island (vector-mean fallback — averaging compass degrees directly is wrong). The bin builds a velocity field by inverse-distance weighting and carries a seeded warm blob downwind by semi-Lagrangian backtrace (Stam's stable advection — unconditionally stable, no CFL limit). The live easterly trades (from ~92°) drift the New-Providence blob ~9 cells WEST off its origin: the origin cools, the trail warms. It MOVES, it doesn't merely spread — the asymmetry is the proof.* `cargo run --bin archipelago_advect -- ../../live_boundary.json`.

                - **(`[x]`/`L−1`/`·`/`Ladder-As-Phases`/`—`/`PROVEN`)** *on the 4090:* `archipelago_sim.rs`*, composing the two existing rungs (NO new shader — the rungs ARE the operators). The four phases run as one gated state machine:* `instantiate → (diffuse ⋈ advect)* → converge → render`*. Instantiate seeds temperature sources (L−3) + a wind velocity field (L−2); each OUTER iteration relaxes 30 diffusion steps then transports 8 advection steps; the* **(`converge`)** *gate reads the field back and halts on* `max|Δ| < ε`*. Operator-split advection-diffusion ran to a verified fixpoint — steady state at outer 21,* `max|Δ|` *falling monotonically* `1.20 → 0.019 °C`*. Verified non-decorative against pure diffuse (`--advect 0` settles at outer 9): advection measurably stirs the system, more than doubling the outers to balance — it is in the equation, not on top of it.* `cargo run --bin archipelago_sim -- ../../live_boundary.json`.

                  - **(`[x]`/`L-0`/`·`/`Render`/`—`/`PROVEN`)** *(render):* `archipelago_sim --html=<file>` *emits a self-contained SVG heat-map of the steady field — a SMOOTH blue→red gradient (the terminal can only band into 5 ANSI colours), island overlay, live caption — openable in any browser, zero dependencies. Live-derived, so it is a view, never committed (like* `live_boundary.json`*). Modular enough to drop into* **(`The-Savant-Grade-Undercellar_Library_Study`)** *as an Index.html/png.* `cargo run --bin archipelago_sim -- ../../live_boundary.json --html=sim_render.html`*. Deferred (optional): hot-reload — the* **(`Arc-I`)** `--watch` *machinery already exists in the barometer; not yet wired into a sim loop.*

                    - **(`[x]`/`L+1`/`·`/`Perform`/`—`/`PROVEN`)** *on the 4090:* `archipelago_sim` *wall-clocks its own run. The full advection-diffusion convergence — 24 outers × 38 dispatches =* `912` *GPU dispatches to a verified steady state — costs* `3.5 ms` *of GPU submit→wait (`3.9 µs/step`),* `4.8 ms` *wall including the 24 CPU readbacks the converge gate needs. The whole heavy sim is a* `~5 ms` *operation: heavy verified as FAST, not just big.* `cargo run --bin archipelago_sim -- ../../live_boundary.json`.

                      - **(`Acceptance`)**: *a real field simulation over real archipelago topology — GPU-accelerated, ladder-gated, fed live by the barometer.*

---

## (`ARC`/`III`/`·`/`THE-DSL`/`Peppered`/`Not-Phased`)
> *Not a discrete stage. Woven into Arc I and II incrementally — the barometer's twin and the ladder's gate-sequence are its first real sentences. It carries **(`One-Law-And-One-Kill-Switch`)**.*

- **(`[ ]`/`D-0`/`·`/`Observe`)** *— extract the grammar already in use (Phase 0). First sentences: the* `archipelago.json` *shape + the ladder gate-sequence.*

  - **(`[ ]`/`D-1`/`·`/`Parser`)** *— Rust (pest/chumsky) over the observed grammar; PyO3/TS bindings as the seam needs them.*

    - **(`[ ]`/`D-2`/`·`/`Execute`)** *— AST + minimal interpreter. **(`First-Executable load`):** express the barometer's twin *or the ladder's gate-chain in the DSL and *run it.*

      - **(`[ ]`/`D-3`/`·`/`Translation-Boundary`)** *— quarantine pretrained bias at the edge **(`Phase-3`)**.*

---

### (`Design-Law`/`Spelling`/`VS`/`Format`/`The-Question`/`Settled`)

- *The **(`PEG`)** parses by **(`Structure`/`Shape`/`Never-By-Dictionary-Correctness`)**.*

  - *A misspelled ticked-id is still a valid ticked-id.* `` `inherance` ``*,* `` `occured` ``*,* `` `privilaged` `` *parse identically to their "correct" forms — the grammar matches backtick-wrapped · Title-Case · arrow-chained · slash-tokened shape, and spelling is; — **(`Orthogonal-To-Validity`)**.

    - *Spelling mistakes are neither good nor bad to the parser; they are invisible to it.*

      - **(`Format-Consistency`/`IS`/`The-Grammar's-Concern`)** *Separators **(`-`/`VS`/`·`/`VS`/`/`)**, wrapping, casing convention, arrow syntax — that is what the PEG pins.*

        - *So: **(`Tolerate-Spelling`/`Enforce-Structural-Format`)** It is the inverse of natural-language linting — we lint shape, never spelling. The project's idiosyncratic spellings are therefore safe; only format drift is a defect.*

---

### (`Kill-Switch`/`The-Test`/`Not-The-Artifact`)

- *The DSL earns continuation **(`Only-By-Executing`)**.*

  - *If after D1 it parses nothing real, or after D2 it runs nothing plain code couldn't already do — **(`Kill-It`)**.*
    - *It is forbidden from becoming a second monolith-to-worship.*
    
      - *Belief is in the test, not the notation. *(This clause exists because the **(`SSOT`)** itself is the warning: revered, dense, and so far inert.)*

---

## (`Cross-Cutting-Laws`/`Apply-To-Every-Arc`)

- *1. — **(`Live`/`=`/`View`/`Never-Stamped`/`.`/`Stable`/`=`/`File`)** — The forecast and the sky are summoned, not frozen; geography and pressure are written. (The honesty rule Arc I proved.)*

  - *2. — **(`Every-Claim-Ships-A-Verifier-Or-Is-Named-Residual`).** — No "done" without a way to falsify it.*

    - *3. — **(`Lore-That-Works`)** — the metaphor and the utility are the same gesture. Nothing decorative survives.*

      - *4. — **(`Heavy-Is-The-Fuel`/`—`/`Inverted`).** — The challenge is the lightness; piecemeal is the drain. When unsure, take the harder cut.*

        - *5. — **(`Compound-Don't-Replace`)** Barometer feeds ladder feeds DSL. The Library-Study dumps are buffer to build on, not slop to discard — wrong answers are still scaffold.*

---

## (`Where-We-Are`/`Now`)

- — **(`Arc-I`)**: *through **(`B8`)** + **(`B-11`)** (the contract, frozen by the seam). Remaining: **(`B9`)** (true histogram) → **(`B10`)** (real Index.html).*

  - *— **(`Arc-II`/`COMPLETE`/`L−5`/`…`/`L+1`)** all PROVEN on the 4090. The ladder runs end to end: a hash-seeded field became a live-weather GPU advection-diffusion sim that interpolates, evolves, breathes the real sky, moves with the wind, composes into one gated machine, converges to a verified steady state in* `~5 ms`*, and renders to a self-contained browser artifact.*

    - *— Only optional tails remain (L0 hot-reload via Arc-I's* `--watch`*).*

      - *— **(`Arc-III`)**: at **(`D0`)** — observing. The design law is settled.*

        - *— Next move: **(`Arc-III`)** (D0 — the DSL, observing; the kill-switch holds) or **(`B9`/`B10`)** compound the barometer into the Library Study.*

          - *— Arc-II is closed: the seam ran, breathed, moved, settled, rendered, and proved itself fast — seven rungs from a claim to a* `~5 ms` *verified sim.*

---

*SID: CLAUDEBASE_LONGTACK_V1 · live · the course, not the helm · 2026-06-06*
