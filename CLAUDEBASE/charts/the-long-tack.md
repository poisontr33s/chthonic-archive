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

# (`☥`/`THE-LONG-TACK`/`Barometer`/`→`/`Ladder`/`→`/`DSL`)

> *En lang slag holdes ikke ved å se på roret, men på kysten man ennå ikke har nådd.*
> *A long tack is held not by watching the helm, but the coast you have not yet reached.*

*The candidate we fell into, stored so we do not lose it. Three arcs. The first is nearly working; the second is unbuilt but already in the repo, only unseamed; the third is not a phase — it is peppered through both, and it lives or dies by one test.*

**(`Reading-Order-Of-The-Arcs`/`Is-The-Sequence-Of-Belief`/`A-Thing`/`Earns-The`/`Next-Arc`/`Only-By-Working`/`In-This-One`)**

---

## (`ARC`/`I`/`·`/`THE-BAROMETER`/`Concept`/`-→`/`Working`/`Acceptable`)
> *The data + notation foundation. When it emits a clean boundary-condition payload, **(`Arc-II`)** may begin.*

- **(`[x]`/`B-1`)** *— intrinsic pressure:* `sha256(body)` *→ SKY·AIR·MOOD over the real 12×12×12 = 1,728 space*
- **(`[x]`/`B-2`)** *— real geography:* `archipelago.json` *twin (8 islands · coords · elevation · decks)*
- **(`[x]`/`B-3`)** *— live sky: Open-Meteo apparent-temperature + WMO condition, fetched never stamped*
- **(`[x]`/`B-4`)** *— forecast probability map: precip-probability, next 12h, density grid*
- **(`[x]`/`B-5`)** *— hot-reload:* `--watch` *(event-driven) +* `--stamp` *(fixpoint) +* `--interval=<ms>` *for the live sky*
- **(`[x]`/`B-6`)** *— colour heat-map:* `--live --color`, *two axes (heat hue + WMO sky-word)*
- **(`[x]`/`B-7`)** *— sea-chart render:* `--chart` *plots the twin by real lat/lon*
- **(`[x]`/`B-8`)** *— tracked in git: (whole folder, comprehensive allowlist)*
- **(`[ ]`/`B-9`)** *— the true 1,728-bucket histogram: (terminal + inline SVG). The fairness-verifier of our generator — supersedes the Library-Study PNG, which binned to 4–5 states and only labelled 1,728*
- **(`[ ]`/`B-10`)** *— a real self-contained* `Index.html` *(one file, no GPU: sea-chart SVG + histogram + forecast) — replaces the saved-Google-search dump as the actual study surface*
- **(`[x]`/`B-11`)** *—* **(`Freeze-The-Data-Contract`)**: *frozen by L−5 — the* `Island{lat,lon,elev,seed}` *std430 struct (16 B), sourced from* `archipelago.json`*; GLSL and Rust agree on it. The seam-side handshake holds.*

**(`Acceptance`)**: *the barometer is proven as data + notation, and B-11 emits the boundary conditions **(`Arc-II`)** reads.*

---

## (`ARC`/`II`/`·`/`The-Ladder`/`The-Vulkan-Field-Sim-Over-Real-Topology`)
> *Unbuilt — but every piece already lives in the repo. The unbuilt thing is the **(`Seam`)**. Heavy on purpose: GPU because the challenge is the fuel.*

**(`<!--`)** *The ladder is the sim, but the sim is not the ladder. The ladder is the verified sequence of gates; the sim is the thing behind those gates, which may be built in any way that proves it works.* **(`-->`)**

> **(`Substrate-Already-Proven`)**: `vulkan-lab/cli-renderer` *runs Vulkan compute on the 4090 (euler_score · ascii_downsample · dirty_diff · headless device select, through G7). The barometer (Arc I) is the boundary conditions. Nobody has connected them.*

*The sim climbs its own ladder — each gate a **(`Verified-State`)**, which is ladder theory made executable, not metadata:*

- **(`[x]`/`L−5`/`·`/`Seam`)** *—* **(`PROVEN`)** *on the RTX 4090:* `vulkan-lab/cli-renderer/src/bin/archipelago_field.rs` *+* `shaders/archipelago_field.comp.glsl`*. Twin → island SSBO → inverse-distance compute → 56×22 field → ANSI relief. Cat-Island (63 m) renders the hot-spot, Bimini (6 m) the cool; field 6–62 m. Barometer → GPU → render, one pass.* `cargo run --bin archipelago_field`.
- **(`[ ]`/`L−4`/`·`/`Iterate`)** *— multi-step diffusion; ping-pong buffers (dirty_diff pattern); the field evolves over ~N steps*
- **(`[ ]`/`L−3`/`·`/`Boundary-Conditions`)** *— seed the field from live data (B3/B4 real rain-prob + temp per island)*
- **(`[ ]`/`L−2`/`·`/`Advection`)** *— directional flow from Open-Meteo* `wind_direction_10m`*; the field moves, not only spreads*
- **(`[ ]`/`L−1`/`·`/`Ladder-As-Phases`)** *— the sim is a gated state machine:* `instantiate → diffuse → advect → converge → render`*, each gate verified before the next opens*
- **(`[ ]`/`L-0`/`·`/`Render`)** *— colour/ascii field over the sea-chart; optional SVG/HTML frame; hot-reloadable like — **(`Arc-I`)**.*
- **(`[ ]`/`L+1`/`·`/`Perform`)** *— prove it on the 4090; measure step latency; heavy verified as fast, not just big*

**(`Acceptance`)**: *a real field simulation over real archipelago topology — GPU-accelerated, ladder-gated, fed live by the barometer.*

---

## (`ARC`/`III`/`·`/`THE-DSL`/`Peppered`/`Not-Phased`)
> *Not a discrete stage. Woven into Arc I and II incrementally — the barometer's twin and the ladder's gate-sequence are its first real sentences. It carries **(`One-Law-And-One-Kill-Switch`)**.*

- **(`[ ]`/`D-0`/`·`/`Observe`)** *— extract the grammar already in use (Phase 0). First sentences: the* `archipelago.json` *shape + the ladder gate-sequence.*
- **(`[ ]`/`D-1`/`·`/`Parser`)** *— Rust (pest/chumsky) over the observed grammar; PyO3/TS bindings as the seam needs them.*
- **(`[ ]`/`D-2`/`·`/`Execute`)** *— AST + minimal interpreter. **(`First-Executable load`):** express the barometer's twin *or the ladder's gate-chain in the DSL and *run it.*
- **(`[ ]`/`D-3`/`·`/`Translation-Boundary`)** *— quarantine pretrained bias at the edge **(`Phase-3`)**.*

### (`Design-Law`/`Spelling`/`VS`/`Format`/`The-Question`/`Settled`)
The **(`PEG`)** parses by **structure (shape), never by dictionary-correctness.**
*- A misspelled ticked-id is still a valid ticked-id.* `` `inherance` ``, `` `occured` ``, `` `privilaged` `` *parse identically to their "correct" forms — the grammar matches backtick-wrapped · Title-Case · arrow-chained · slash-tokened shape, and spelling is **(`Orthogonal-To-Validity`)**. Spelling mistakes are neither good nor bad to the parser; they are invisible to it.*
- **(`Format-Consistency`/`IS`/`The-Grammar's-Concern`)** *Separators **(`-`/`VS`/`·`/`VS`/`/`)**, wrapping, casing convention, arrow syntax — that is what the PEG pins. So: **(`Tolerate-Spelling`/`Enforce-Structural-Format`)** *It is the inverse of natural-language linting — we lint shape, never spelling. The project's idiosyncratic spellings are therefore safe; only format drift is a defect.*

### (`Kill-Switch`/`The-Test`/`Not-The-Artifact`)
*The DSL earns continuation **(`Only-By-Executing`)**. If after D1 it parses nothing real, or after D2 it runs nothing plain code couldn't already do — **(`Kill-It`)**. It is forbidden from becoming a second monolith-to-worship. Belief is in the test, not the notation. *(This clause exists because the **(`SSOT`)** itself is the warning: revered, dense, and so far inert.)*

---

## (`Cross-Cutting-Laws`/`Apply-To-Every-Arc`)
1. **(`Live`/`=`/`View`/`Never-Stamped`/`.`/`Stable`/`=`/`File`)** *The forecast and the sky are summoned, not frozen; geography and pressure are written. (The honesty rule Arc I proved.)*
2. **(`Every-Claim-Ships-A-Verifier-Or-Is-Named-Residual`).** *No "done" without a way to falsify it.*
3. **(`Lore-That-Works`)** *— the metaphor and the utility are the same gesture. Nothing decorative survives.*
4. **(`Heavy-Is-The-Fuel`/`—`/`Inverted`).** *The challenge is the lightness; piecemeal is the drain. When unsure, take the harder cut.*
5. **(`Compound-Don't-Replace`)** *Barometer feeds ladder feeds DSL. The Library-Study dumps are buffer to build on, not slop to discard — wrong answers are still scaffold.*

---

## (`Where-We-Are`/`Now`)
- **(`Arc-I`)**: *through **(`B8`)** + **(`B-11`)** (the contract, frozen by the seam). Remaining: **(`B9`)** (true histogram) → **(`B10`)** (real Index.html).*
- **(`Arc-II`)**: *open. **(`L−5`)** PROVEN on the 4090. Next rung: **(`L−4`)** — iterate the field over ~N steps (ping-pong buffers).*
- **(`Arc-III`)**: *at **(`D0`)** — observing. The design law is settled.*

*Next move: **(`L−4`)** (make the field evolve, not merely interpolate), or **(`B9`/`B10`)** compound into the Library Study. The contract holds; the seam is no longer a claim — it ran.*

---

*SID: CLAUDEBASE_LONGTACK_V1 · live · the course, not the helm · 2026-06-06*
