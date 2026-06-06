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

# ☥ THE LONG TACK — Barometer → Ladder → DSL

> *En lang slag holdes ikke ved å se på roret, men på kysten man ennå ikke har nådd.*
> *A long tack is held not by watching the helm, but the coast you have not yet reached.*

*The candidate we fell into, stored so we do not lose it. Three arcs. The first is nearly working; the second is unbuilt but already in the repo, only unseamed; the third is not a phase — it is peppered through both, and it lives or dies by one test.*

**Reading order of the arcs is the sequence of belief: a thing earns the next arc only by working in this one.**

---

## ARC I · THE BAROMETER — concept → working, *acceptable*
> The data + notation foundation. When it emits a clean boundary-condition payload, Arc II may begin.

- [x] **B1** — intrinsic pressure: `sha256(body)` → SKY·AIR·MOOD over the real 12×12×12 = 1,728 space
- [x] **B2** — real geography: `archipelago.json` twin (8 islands · coords · elevation · decks)
- [x] **B3** — live sky: Open-Meteo apparent-temperature + WMO condition, fetched never stamped
- [x] **B4** — forecast probability map: precip-probability, next 12h, density grid
- [x] **B5** — hot-reload: `--watch` (event-driven) + `--stamp` (fixpoint) + `--interval=<ms>` for the live sky
- [x] **B6** — colour heat-map: `--live --color`, two axes (heat hue + WMO sky-word)
- [x] **B7** — sea-chart render: `--chart` plots the twin by real lat/lon
- [x] **B8** — tracked in git (whole folder, comprehensive allowlist)
- [ ] **B9** — the **true 1,728-bucket histogram** (terminal + inline SVG). The fairness-verifier of *our* generator — supersedes the Library-Study PNG, which binned to 4–5 states and only *labelled* 1,728
- [ ] **B10** — a real self-contained **`Index.html`** (one file, no GPU: sea-chart SVG + histogram + forecast) — replaces the saved-Google-search dump as the actual study surface
- [ ] **B11** — **freeze the data contract**: the stable payload the ladder consumes — per-island `{lat, lon, elev, seed, live?}`, SSBO-shaped. *This is the seam-side handshake.*

**Acceptance:** the barometer is proven as data + notation, and B11 emits the boundary conditions Arc II reads.

---

## ARC II · THE LADDER — the Vulkan field-sim over real topology
> Unbuilt — but every piece already lives in the repo. The unbuilt thing is the **seam**. Heavy on purpose: GPU because the challenge is the fuel.
>
> **Substrate already proven:** `vulkan-lab/cli-renderer` runs Vulkan compute on the 4090 (euler_score · ascii_downsample · dirty_diff · headless device select, through G7). The barometer (Arc I) is the boundary conditions. Nobody has connected them.

The sim climbs its own ladder — each gate a *verified state*, which is ladder theory made executable, not metadata:

- [ ] **L−5 · Seam** — islands → SSBO `{lat,lon,elev,seed}`; one `.comp` shader diffuses a field by inverse-distance; result → existing `ascii_downsample` → terminal. *Proves barometer → GPU → render in one pass.*
- [ ] **L−4 · Iterate** — multi-step diffusion; ping-pong buffers (dirty_diff pattern); the field evolves over N steps
- [ ] **L−3 · Boundary conditions** — seed the field from live data (B3/B4 real rain-prob + temp per island)
- [ ] **L−2 · Advection** — directional flow from Open-Meteo `wind_direction_10m`; the field *moves*, not only spreads
- [ ] **L−1 · Ladder-as-phases** — the sim is a gated state machine: `instantiate → diffuse → advect → converge → render`, each gate verified before the next opens
- [ ] **L0 · Render** — colour/ascii field over the sea-chart; optional SVG/HTML frame; hot-reloadable like Arc I
- [ ] **L+1 · Perform** — prove it on the 4090; measure step latency; heavy verified as *fast*, not just big

**Acceptance:** a real field simulation over real archipelago topology — GPU-accelerated, ladder-gated, fed live by the barometer.

---

## ARC III · THE DSL — peppered, not phased
> Not a discrete stage. Woven into Arc I and II incrementally — the barometer's twin and the ladder's gate-sequence are its first real sentences. It carries **one law and one kill-switch.**

- [ ] **D0 · Observe, don't invent** — extract the grammar already in use (Phase 0). First sentences: the `archipelago.json` shape + the ladder gate-sequence.
- [ ] **D1 · Parser** — Rust (pest/chumsky) over the observed grammar; PyO3/TS bindings as the seam needs them.
- [ ] **D2 · Execute** — AST + minimal interpreter. **First executable load:** express the barometer's twin *or* the ladder's gate-chain in the DSL and *run it*.
- [ ] **D3 · Translation boundary** — quarantine pretrained bias at the edge (Phase 3).

### Design law — spelling vs format *(the question, settled)*
The PEG parses by **structure (shape), never by dictionary-correctness.**
- A misspelled ticked-id is still a valid ticked-id. `` `inherance` ``, `` `occured` ``, `` `privilaged` `` parse identically to their "correct" forms — the grammar matches *backtick-wrapped · Title-Case · arrow-chained · slash-tokened shape*, and spelling is **orthogonal to validity.** Spelling mistakes are neither good nor bad to the parser; they are invisible to it.
- **Format consistency IS the grammar's concern.** Separators (`-` vs `·` vs `/`), wrapping, casing convention, arrow syntax — that is what the PEG pins. So: **tolerate spelling, enforce structural format.** It is the inverse of natural-language linting — we lint shape, never spelling. The project's idiosyncratic spellings are therefore *safe*; only format drift is a defect.

### Kill-switch — the test, not the artifact
The DSL earns continuation **only by executing.** If after D1 it parses nothing real, or after D2 it runs nothing plain code couldn't already do — **kill it.** It is forbidden from becoming a second monolith-to-worship. Belief is in the test, not the notation. *(This clause exists because the SSOT itself is the warning: revered, dense, and so far inert.)*

---

## CROSS-CUTTING LAWS — apply to every arc
1. **Live = view, never stamped. Stable = file.** The forecast and the sky are summoned, not frozen; geography and pressure are written. (The honesty rule Arc I proved.)
2. **Every claim ships a verifier, or is named residual.** No "done" without a way to falsify it.
3. **Lore that works** — the metaphor and the utility are the same gesture. Nothing decorative survives.
4. **Heavy is the fuel (inverted).** The challenge is the lightness; piecemeal is the drain. When unsure, take the harder cut.
5. **Compound, don't replace.** Barometer feeds ladder feeds DSL. The Library-Study dumps are buffer to build on, not slop to discard — wrong answers are still scaffold.

---

## WHERE WE ARE NOW
- **Arc I:** through **B8**. Next: **B9** (true histogram) → **B10** (real Index.html) → **B11** (freeze the contract).
- **Arc II:** unbuilt. First cut is **L−5** — the seam, proven in one compute pass.
- **Arc III:** at **D0** — observing. The design law above is already settled.

*Next move on the table: B9/B10 compound into the Library Study now, or jump the seam at L−5. The Savant goes vertical on the L−5 kernel if dispatched; the architecture is held here.*

---

*SID: CLAUDEBASE_LONGTACK_V1 · live · the course, not the helm · 2026-06-06*
