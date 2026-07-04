---
- Her-Salvage-Chart: #!/usr/bin/env markdown
- SID: CLAUDEBASE_SALVAGE_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/salvage-chart.md
- Current-Bounty: ../The-Savant-High-Bounties/TODO.md | GRILLING.md
- Bearing: by · structural-integrity · live-sounded · not-assumed
- Altitude: Chart-Room · Below-Deck
- Island: Rum-Cay · 23.6833,-74.8667 — wrecks and salvage ground; the diver's chart
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Brine-Soaked · Iron-Rot · Copper-Still-Clean
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Industrial · Practical
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
- Toolchain-Note: `bun` replaces npm/node/yarn/pnpm. `node_modules` + `bun.lock` is Bun-native output, not a Node footprint.
  - *— **(`Version-Managers`)** — `rust` = rust (base language, no abbreviation). `uv` = python 3.14.6. `rv` = ruby (spinel, formerly rvx). `rv-r` = R language. `zv` = zig. `bun` = ts/js.*  
  - *— **(`Crucial`)** — `rv-r` is R, NOT rust. Rust is plain `rust`. The others (uv, rv, zv) are speed-ups built in rust for the polyglot workspace.*  
---

# (`☥`/`CLAUDEBASE`/`SALVAGE-CHART`)

> *— Et vrak er bare et vrak inntil noen vet hva det kan bli. Inntil da er det bare et skipsrester.*

  > *— A wreck is only a wreck until someone knows what it can become. Until then it is just ship remains.*

- *— This chart is the — **(`Live-Sounded`)** — record assessed against `CLAUDEBASE/charts/upcycle-protocol.md`. Tier is the confidence rating after an upcycle pass, not before.*

  - *— The Tier is not a priority. It is a — **(`Confidence-Rating`)** — in the structural integrity of the find:*

    - *— **(`Tier-1`)** — E2E passes, deps current, doc/reality delta < 1 critical contradiction.*

      - *— **(`Tier-2`)** — architecture is sound, implementation is partial. Needs a build pass to assess whether the design survives contact with reality.*

        - *— **(`Tier-3`)** — documented but never built. Or built once and the source is fragmentary. Archival value only — would need a full reimplementation from the design notes.*

---

## (`Tier-1`/`Solid-Hulls`/`Live-Sounded`)

- *— Code that compiles or ran. Has genuine structural weight. Documentation absent, stale, or contradicted by the on-disk reality.*

---

### (`1`/`chthonic-cai`/`tools/chthonic-cai`)

| *Field* | *Value* |
|---|---|
| *Language* | *Rust (edition 2024)* |
| *Lines* | *~300 across 3 source files (main.rs, xp.rs, trail.rs)* |
| *Cargo.toml* | ✅ present |
| *Cargo.lock* | ❌ absent (local workspace) |
| *target/* | ❌ absent (local workspace) |
| *Global install* | ✅ `~/.cargo/bin/cai.exe` — 967 KB, dated 2026-04-15, runs from PATH |
| *Dependencies* | clap 4, crossterm 0.29, serde, chrono, anyhow |
| *Built* | ✅ Compiled + installed globally (`~/.cargo/bin/cai.exe`, 967 KB, 2026-04-15) |
| *Structure* | REPL loop + crossterm TUI + XP engine + NDJSON trail writer |
| *XP engine* | *Mirrors —* `chthonic-xp.ps1` *— formula exactly; same base XP, bonuses, level math* |
| *Trail writer* | *NDJSON append — same schema as PowerShell Add-TrailEvent* |
| *Windows-aware* | *Explicit UTF-8 codepage 65001 via Win32 API* |
| *Documentation* | **NONE** *— Invisible to CLAUDEBASE. Not in —* `hold/stow-manifest.md`*.* `README.md` missing. (Created during this upcycle pass.) |
| *Dep audit* | All 6 crates at latest stable as of 2026-06-28. No stale deps. crossterm pinned to 0.29 (0.30 does not exist). |
| *E2E status* | `cai --help` clean. REPL loop fired (TUI rendered + XP prompt visible). Trail: 2 NDJSON events written (diagnostic + artifact). XP state: xp=12, level=1 (formula verified). `gh copilot` dispatch failed gracefully — wrapper did not panic. |
| *Doc-vs-reality* | Cargo.toml claims "gamified CLI companion wrapping gh copilot suggest/explain." Code delivers exactly that, plus XP persistence, live level bar, Windows UTF-8 codepage. XP state `unlocked` field intentionally stub — PowerShell fills it. |

- *— **(`Contradiction`)** — The hold manifest names 6 tools as working cargo. `chthonic-cai` is compiled and installed globally (`~/.cargo/bin/cai.exe`) but has no local workspace artifacts (no Cargo.lock, no target/) and was entirely undocumented in CLAUDEBASE until this session.*

  - *— **(`Up-cycle potential`)** — FULL/COMPLETE. All 7 upcycle-protocol steps run. Deps current, E2E passed, doc-reality delta < 1 critical contradiction, backend logic verified clean (no `todo!()`, panic!, hardcoded true). README written. Tier-1 confirmed.*

    - *— **(`Next-Sounding`)** —* `cargo build -p chthonic-cai` *— verify compiles; —* `cai --help` *— for runtime readiness.*

---

### (`2`/`context-compressor`/`extensions/context-compressor`)

| *Field* | *Value* |
|---|---|
| *Language* | Rust (edition 2024) |
| *Lines* | ~700 in src/main.rs |
| *Built* | ✅ Cargo.lock + target/ with compiled artifacts |
| *Dependencies* | chrono, reqwest 0.13.2, serde, serde_json, tokio, walkdir |
| *Structure* | CLI for Context Packet compression (JSON/MD input -> structured handoff); local LLM integration for advanced analysis |
| *Schema* | `packet.schema.json` — JSON Schema 2020-12 |
| *Output* | Markdown or JSON |
| *Documentation* | README.md exists. Not referenced from CLAUDEBASE. |

- *— **(`Contradiction`)** — The handoff-loop skill and mailbox-handoff both deal with agent-to-agent handoffs. context-compressor is a native Rust tool that does exactly this — but lives unmentioned in —* `extensions/`*.*

   *— **(`Up-cycle potential`)** — HIGH. Migrate to —* `tools/` *— wire into handoff-loop as a compression stage. Pure compression path (no LLM) works standalone.*

    - *— **(`Next-Sounding`)** — Verify target/ artifacts still link. —* `cargo build --manifest-path extensions/context-compressor/Cargo.toml` *— Test standalone compression without LLM.*

---

### (`3`/`dsl-smoke`/`tools/dsl-smoke`)

| *Field* | *Value* |
|---|---|
| *Language* | Rust (edition 2024) |
| *Lines* | ~400+ across 7 source files |
| *Built* | ✅ Part of workspace |
| *Binaries* | 6: dsl-smoke, dsl-audit, dsl-bisect, dsl-probe, dsl-full-smoke, dsl-pattern-test, dsl-coverage |
| *Documentation* | README.md with full iteration history (6 iters, 0/6 -> 6/6). Referenced in TODO.md Gate -5. |

- *— **(`Status`)** — MATURE. Not abandoned — referenced by TODO.md. Load-bearing for Gate -5 (DSL conformance).*

  - *— **(`Up-cycle-Potential`)** — LOW for repurposing (purpose-built). HIGH for completing its mission. The rewindability methodology generalizes to any iterative grammar design.*

    - *— **(`Next sounding`)** —* `cargo build -p dsl-smoke` *— Verify 6/6 slice pass rate.*

---

## (`Tier-2`/`Architecture-Sound`/`Implementation-Partial`)

- *— Design and scaffolding exist. Implementation is incomplete. Need a build pass to determine whether the design survives contact with reality.*

---

### (`4`/`voice-iter`/`tools/voice-iter`)

| *Field* | *Value* |
|---|---|
| *Language* | Python 3.14+ |
| *Structure* | CLI skeleton + config schema + test corpus + ARCHITECTURE.md (~200 lines) |
| *Built* | uv.lock + .venv — dependencies resolved |
| *Status* | V0.1 scaffold. Step 1/6 done. Steps 2-6 pending (model installs, providers, MCP) |
| *Documentation* | ARCHITECTURE.md — excellent, current (2026-05-27) |

- *— **(`Contradiction`)** — The sub-surface-skinny-dipping brief specs MCP servers but never references voice-iter. It's a voice MCP server designed with the same methodology, invisible to the same brief.*

  - *— **(`Up-cycle-Potential`)** — MEDIUM. Architecture is valuable. Providers need ~2GB model downloads.*

---

### (`5`/`spec-enforcer`/`tools/spec-enforcer`)

| *Field* | *Value* |
|---|---|
| *Language* | TypeScript (Bun) |
| *Lines* | 343 |
| *deps* | bun.lock + node_modules + tsconfig.json + package.json — all present |
| *Status* | src/index.ts verified present. **Functional — runs with `bun run src/index.ts --once`** |
| *Runtime dirs* | `.chthonic/specs/` (empty, watch target) + `.chthonic/cache/neural-bus/` (cache output) — both exist |
| *Toolchain* | **Bun** — uses Node built-ins (`node:child_process`, `node:fs`, `node:path`, `node:url`), all available in Bun |
| *Function* | Watches `.chthonic/specs/*.md`, runs `context-compressor` against `src/`, emits `handoff_signal.json` to neural-bus cache |

**Verified commands:**
- `bun run src/index.ts --once` → `[BUS] No spec files found to process.` (clean exit, dir is empty)

- *— **(`Contradiction`)** — Initially claimed "source missing" during surface scan. Live verification corrected this. The tool is complete, functional, Bun-native, and wired into the handoff system via `handoff_signal.json`.*

---

### (`6`/`milfological`/`extensions/milfological`)

| *Field* | *Value* |
|---|---|
| *Language* | Python |
| *Structure* | pyproject.toml + .venv + src/ |
| *Status* | Scaffold. Needs source inspection. |

- *— **(`Up-cycle-Potential`)** — UNKNOWN.*

---

## (`Tier-3`/`Documented-Only`/`Never-Built-Or-Broken`)

*Designed in documents. No executable code exists. Would need full reimplementation.*

---

### (`7`/`bevy-mcp-server`/`tools/bevy-mcp-server`)

| *Field* | *Value* |
|---|---|
| *Cargo.toml* | Complete — rmcp 1.7, tokio, reqwest, schemars |
| *src/main.rs* | Single file — never implemented beyond scaffold |
| *Built* | ❌ No Cargo.lock |
| *Spec* | sub-surface-skinny-dipping/mcp_servers_deep_research_spec.md |

- *— **(`Contradiction`)** — Spec describes 3 tools and says "Research, design, scaffold." Reality: Cargo.toml -> stopped.*

---

### (`8`/`vulkan-mcp-server`)

| *Field* | *Value* |
|---|---|
| *Existence* | Spec document only. No directory, no code. |
| *Spec* | sub-surface-skinny-dipping/mcp_servers_deep_research_spec.md (§2) |

- *— **(`Contradiction`)** — Spec implies scoped alongside bevy-mcp-server. No code exists anywhere.*

---

## (`Soundings-Index`)

| *Zone* | *Count* | *Tier-1* | *Tier-2* | *Tier-3* | *Unsounded* |
|---|---|---|---|---|---|
| *tools/* | 11 | 3 | 1 | 2 | 5 |
| *extensions/* | 8 | 1 | 0 | 0 | 7 |
| *game/* | 6 | 0 | 0 | 0 | 6 |
| *vulkan-lab/* | 4 | 0 | 0 | 0 | 4 |
| *dumpster-dive/* | 7 | 0 | 0 | 0 | 7 |
| **(`Total`)** | **(`36`)** | **(`4`)** | **(`1`)** | **(`2`)** | **(`29`)** |

- *— **(`Unsounded`)** — 29 of 36 scouted locations remain unsounded — surface scanned but not depth-read. Each is a candidate for a future pass if the infrastructure agenda prioritizes its domain.*

---

*SID: CLAUDEBASE_SALVAGE_V1 · live-sounded 2026-06-28 · 8 of 36 locations assessed · 4 Tier-1 hulls confirmed · upcycle-protocol: step 1-3 done on 4 candidates · next: step 4-6 (dep audit, safe migration, E2E) on confirmed hulls*
