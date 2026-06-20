---
# ☥ CHTHONIC ARCHIVE — GRILLING PACKET
# SID: GRILLING_PACKET_V1
# Lifecycle: permanently-living-document
# Execution plan: see TODO.md
# Grilled: 2026-06-05 · Rounds: 2 · Files read: 40+ · Subsystems mapped: 10
# Compile errors found: 0 · CI failures found: 2 · Advisory items found: 7
---

## (`PURPOSE`)

- *— This file is not a summary. It is the — **(`Evidence-Base`)** — for every gate and task in [TODO.md (The-Savant-High-Bounties)](TODO.md).*

  - *— Each finding below is keyed to the — **(`TODO-Gate`)** — it feeds. When a gate's acceptance criteria seem arbitrary, the grilling observation is the reason. When a task says "CI-FAILED" or "advisory", the specifics are here.*

    - *— Begin executing from — [TODO.md (The-Savant-High-Bounties)](TODO.md) — return here when a task needs justification or deeper context.*

---

## (`ARCHITECTURE-TOPOLOGY`)

### (`STACK-OVERVIEW`)

| *Layer* | *Technology* | *Root-path* |
|---|---|---|
| *Game engine* | *Rust / ash 0.38 (Vulkan raw)* / *Bevy ECS 0.18.1* / *winit 0.30* | `src/` |
| *Vulkan renderer* | *Rust / ash / shaderc 0.10 / GLSL→SPIR-V* | `vulkan-lab/cli-renderer/` |
| *DSL toolkit* | *Rust / pest_vm (runtime) / pest_meta* | `tools/dsl-iteration-toolkit/` |
| *WPTG accelerator* | *Rust / ankh-forge CLI* | `tools/ankh-forge/` |
| *Copilot SDK server* | *Rust / github-copilot-sdk 1.0.0-beta.9* | `tools/chthonic-mcp/` |
| *Game logic binary* | *Rust / game-cli.exe* | `game/core/` |
| *VS Code extension* | *TypeScript / Bun / vscode API 1.100* | `extensions/chthonic-archive/` |
| *ML pipeline* | *Python 3.14.5* / *uv* / *torch 2.11.0+cu128* / *CUDA 12.8+* | `apps/flux-satellite/`, `mas_mcp/` |
| *Intelligence server* | *Python 3.14.5* / *FastMCP* / *numpy* | `mas_mcp/` |
| *Next.js app* | *Next.js 16.2.3* / *Bun* | `apps/chthonic-next/` |
| *CI system* | *TypeScript* / *Bun* / *21 checks* | `ci/` |
| *Governance* | *Markdown* / *SHA-256* / *DCRP* | `.github/`, `.dcrp_state.json` |

### (`Satellite Registry`/`8-Repos`/`NTFS-Junctions`/`In-Repo-Root`)

```
csb-live/     → Claudine_Supreme-Polyglot (ASC Framework SSOT)
eoai-live/    → EOAI-PII-My-AI-IDEA (FrostGuard ML)
git-dump-live/→ git-dump-lfs-holder (ore/artifacts)
pnk-lfh-live/ → psychonoir-kontrapunkt-large-file-holder
pnk-live/     → PsychoNoir-Kontrapunkt (entity lore SSOT, 9,224-file corpus)
poisontr33s-live/ → poisontr33s (GitHub profile satellite)
rmco-live/    → Restructure-MCP-Orchestration (19 open issues)
```

- *— Managed by —* `scripts/polyrepo-runner.ps1`*. — all junctions are read-only mounts; commits target each satellite's own remote. The —* `spread-freshness` *— CI check gates on all satellites being within 24h of expected SHA.*

---

## (`SECTION-1`/`·`/`GOVERNANCE-SUBSTRATE`)

- *— *Feeds —* [TODO.md (The-Savant-High-Bounties)](TODO.md#gate--5--governance-integrity-substrate-health)*.*

### (`SSOT-Structure`)

> *— **(`Causal-Direction`)** — the macro-prompt-world came first. The codebase was manifested FROM it — not documented BY it.*

  > *— This is not a description of an existing system. It is the system; the code is its implementation.*

- *— **(`Macro-Prompt-World`/`Tthe world-document`)** —* `.chthonic/SSOT.md` *— 10,500+ lines, lifecycle —* `ssot-canon`*. — also known as the — **(`Codex-Brahmanica-Perfectus`)** — and the — **(`Unabridged`/`SSOT/``L-H`)** — this file was written BEFORE most of the codebase existed. Everything else — the game-engine —*`CI-system`*, — the —* `MCP-servers`*, — the —* `agent-court` *— was created as an implementation of what this document describes, the —* **(`SSOT.md`)** *— suffix and `—* .chthonic/` *— location are naming artifacts from its origin; the name is legacy. It is NOT an —* `instruction file`*. — It is the — * `living world-document` *— from which all —* `doctrine` *— descends.*
- **Branch instruction files:** `.github/instructions/*.instructions.md` — downstream vessels. Translate semantic lineage into operational doctrine. Do not replicate world-document content.
- **Internal sections (world-document):** §I–§XVII internally. §XIV = Development Conventions, §XV = DCRP (Decorator's Cross-Reference Protocol), §XVI = APCR (Agent Priority & Conflict Resolution). Navigate by section title.
- **⚠ FA⁵ Addressability constraint:** Line-number ranges are **rejected** per FA⁵ (Ornamental Integrity supersedes machine convenience). Navigate by section title only. Any reference using line numbers is wrong and will drift.
- **Enforcement chain:** T0.5 Decorator → T1 Triumvirate → T2 Prime Factions → T3 Branch instructions → T4 Tools
- **Drift detection:** `.dcrp_state.json` — SHA-256 hash registry. Every branch instruction file has a registered hash. `canon-drift` CI check compares live SHA against registered SHA on every CI run.

---

### (`DSL-System`)

- **(`Grammar`)** `.chthonic/grammar/chthonic.peg` — PEG grammar for the SSOT annotation language
- **(`Parser`)** `tools/dsl-iteration-toolkit/src/` — uses `pest_vm` (runtime interpreter, no compile-time macros) + `pest_meta`
- **(`Coverage-Ledger`)** `manifest/dsl_iteration_history.ndjson` — each iteration keyed by grammar SHA-256
- **(`Rule-Inventory`)**
  - `identifier` — uppercase ASCII compound tokens (`FA⁵`, `ANKH-MGBP`, `K-CUP`)
  - `ticked_id` — backtick-wrapped abbreviations: `` `FA⁵` ``
  - `ticked_phrase` — backtick-wrapped title-case concept names: `` `The-Savant` ``
  - `ticked_any` — catch-all for possessives, embedded spaces, section refs (`§XIV.3`), paths
  - `titlecase_concept` — bare concept names: `The-Savant`
  - `parenthetical_*` — 1,510 parenthetical abbreviations in the `SSOT`
- **(`⚠-CI-FAILURE`)** `dsl-conformance` check FAILED as of `2026-05-31`. Active grammar decisions were made that same day — most likely cause: a new rule narrowed coverage of existing `SSOT` content. Fix path: `uv run scripts/dsl_iteration_check.py` (without `--dry-run`) → new ledger entry → recheck.

---

### (`Branch-Instruction-Files`/`·`/`Operational-Doctrine-Vessels`)

- `technical-directives.instructions.md` — operational conventions, toolchain constraints
- `python-scripting.instructions.md` — `uv run` mandate, PEP 723 → pyproject.toml migration
- `autopsy-protocol.instructions.md` — post-mortem format
- `ankh-workflow.instructions.md` — ANKH traversal workflow
- `ssot-toolbox.instructions.md` — SSOT tooling reference
- `project-workflow.instructions.md` — sprint/gate workflow
- `pattern-nursery.instructions.md` (`applyTo: "**"`) — pre-canon pattern holding ground

---

## (`SECTION-2`/`·`/`CI-SYSTEM`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate--4--ci-system-integrity-enforcement-health)*

---

### (`CI-Architecture`)

- **(`Orchestrator`)** `ci/run.ts` — SID: `CI_RUNNER_V1` — registry-driven parallel execution
- **(`Check count`)** 21 checks
- **(`Autofix-capable`)** `python-headers`, `blessing-gate`, `pathfinder`
- **(`Pre-commit hook`)** `scripts/pre-commit-hook.sh`

### Check Results (2026-05-31, from `manifest/black_smoke_report.json`)

| Check | Status | Detail |
|---|---|---|
| `shebang` | ✅ PASS | — |
| `python-headers` | ⚠ advisory | 5/436 non-canonical headers |
| `sid-envelope` | ⚠ advisory | 5 missing, 30 malformed (266/301 valid) |
| `uv-guard` | ⚠ advisory | 62 violations — `python script.py` instead of `uv run` |
| **`bun-audit`** | **❌ FAILED** | Unaddressed JS dep vulnerabilities |
| **`dsl-conformance`** | **❌ FAILED** | Coverage regression in PEG grammar |
| `gh-runs` | 🔶 degraded | 25% success rate — 5 dispatch failures |
| `blessing-gate` | ✅ PASS | — |
| `pathfinder` | ✅ PASS | — |
| `inference-gate-smoke` | ✅ PASS | G1–G6 ladder all admitted |
| `lore-canon` | ✅ PASS | — |
| `character-schema` | ✅ PASS | — |
| `spread-freshness` | ✅ PASS | — |
| `terminal-hook-smoke` | ✅ PASS | — |
| `canon-drift` | ✅ PASS | — |

---

### (`GitHub-Actions`/`Found-In`/`.github/workflows/`)

- 3 workflows **active** (`.yml` extension): `claudine-cloud-dispatch.yml`, `pentea-cloud-dispatch.yml`, `dependabot-auto-merge.yml`
- 5 workflows **disabled** (`.yml.off` extension): `blessing-gate.yml.off`, `claude.yml.off`, `gemini-dispatch.yml.off` + 2 others
- The 25% success rate on `gh-runs` explains itself: 3 active, 5 intentionally dead, failures are from trigger/token drift on the active ones

---

## (`SECTION-3`/`·`/`TOOLCHAIN`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate--3--toolchain-coherence-runtime-health)*

---

### (`Rust-Workspace`)

- **(`Root workspace members`)** `chthonic-archive` (src/), `chthonic-mcp` (tools/chthonic-mcp/), `ankh-forge` (tools/ankh-forge/), `dsl-iteration-toolkit` (tools/dsl-iteration-toolkit/), `chthonic-cai` (tools/chthonic-cai/)
- **(`Isolated workspaces`)** `vulkan-lab/cli-renderer/` (`[workspace]` table prevents root absorption), `game/core/`
- **(`Root crate deps`)** `winit 0.30`, `ash 0.38`, `gpu-allocator 0.28`, `bevy_ecs 0.18.1`, `glam 0.32`, `tokio 1.52`, `github-copilot-sdk 1.0.0-beta.9`; build dep `shaderc 0.10`
- **(`Planned`)** `anchor-lang 0.28` (Solana — not yet active)
- **(`Compile health`)** 0 errors at time of grilling (confirmed via `get_errors` toolcheck)

---

### (`Python Environment`)

- **(`Manager`)** `uv` — strict, `pyproject.toml` SSOT
- **(`Python version bump`)** ≥ 3.14.5 (required explicitly)
- **(`ML stack`)** `torch 2.11.0+cu128` (via pytorch-cu128 index), `flash_attn 2.8.3` (built from source, wheel cached in uv store), `triton-windows 3.6.0.post26` (cp314-win_amd64, not `triton` PyPI), `xformers 0.0.35`, `transformers 5.4.x`, `onnxruntime-gpu 1.25.x`
- **(`GPU`)** RTX 4090 (Ada Lovelace, CUDA 12.8, 16GB in mas_mcp probe — note: mas_mcp reports "Laptop GPU" variant at 7424 CUDA cores)
- **(`⚠ quarantined`)** `optimum` — caps transformers below active lane
- **(`Gate proof`)** (from `manifest/inference-gate-smoke.ts` + probe manifests):
  - G1 resolver_coherence: admitted L4
  - G2 pydantic_pyO3_abi: admitted L4
  - G3 torch_cuda: admitted L4 (torch 2.11.0+cu128, RTX 4090, cap [8,9])
  - G4 exllamav2_cp314: impossible_currently (highest wheel = cp313)
  - G5 exllamav3_cp314: admitted L4 (exllamav3 0.0.30)
  - G6 flash_attn_build: admitted L4 (source build + CUDA kernel verified 81b36b71)
  - triton: admitted L4 (triton-windows 3.6.0.post26)
  - xformers: admitted L4 (MEA [1,64,8,64] CUDA)
  - formatron: admitted L4 (0.5.0 + patch applied)

---

### (`TypeScript / Bun`)

- `bun` handles all TS execution (scripts/, ci/, apps/)
- `extensions/chthonic-archive/` has its own `package.json` + `tsconfig.json`
- `apps/chthonic-next/` is Next.js 16.2.3
- Shell hook writes per-command JSONL: `manifest/terminal_session.jsonl`

---

## (`SECTION-4`/`·`/`ARCHITECTURAL DEBT`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate--2--architectural-debt-reduction-structure-health)*

---

### (`Dumpster-Dive Ore`/`Critical`)
- **(`Location`)** `dumpster-dive/` — git-tracked via explicit `!dumpster-dive/**` allowlist in `.gitignore`
- **(`Inventory`)** 96 ore files, **all `status: "pending"`**
- **(`Highest-grade item`)** `asc.py` — 4083 lines, rated ⚗️ HIGH-GRADE, destination: `mas_mcp/lib/asc_toolchain.py`
- **(`Second highest`)** `abbr-system.json` — rated HIGH-GRADE, destination: `game/lore/abbr-system.json`
- **(`Processing tools`)** `uv run scripts/dumpster_upcycler.py`, `uv run .agents/skills/corpse-reviver/scripts/revive.py`
- **(`Strategic significance`)** `asc.py` contains the callable API that `mas_mcp/server.py` needs — currently it's unreachable dead weight. Every day it sits in dumpster-dive, the MAS MCP server has a hollow core.

### (`Extension Hallucinatory Ladderization`)
- **(`Diagnosed in`)** `docs/extension-modernization-grill-packet.md`
- **(`Pattern name`)** "hallucinatory ladderization" — metadata claims exceed actual implementation
- **(`The 3 root problems`)**
  1. `src/activation/activateSidecars.ts` — sidecars block extension host startup (should be lazy)
  2. `src/runtime/statusReport.ts` — still checks for `chthonic-statusbar` extension, which is quarantined
  3. `test/` — E2E tests mutate real workspace paths (not sandboxed in `test-fixtures/`)
- **(`Legacy extensions found`/`extensions/`)** `chthonic-statusbar/`, `chthonic-mandala/`, `Chtonic-rendered-ai-markdown-paste-flavoured/`, `context-compressor/`, `milfological/`, `reflex-guard/`, `vampire-corpus/` — all legacy, should be quarantined to `.deprecated/extensions/`
- **(`Preservation policy` WPTG axiom)** quarantine, never delete. The hallucinatory ladderization is itself evidence — file it, name it, keep it.
- **(`vampire-corpus/`)** contains `.vsix` files (`vampire-corpus-0.1.0.vsix`, `vampire-corpus-insiders.vsix`) that may be stale

### (`Solana-Integration`/`Unknown-State`)
- **(`Evidence`)** `src/entropy/entropyConfig.ts` reads `solanaRpcUrl`, `autostartValidator`, `walletPath`, `idlPath`
- **(`Status`)** unknown — either real incomplete integration or dead config reads
- **(`Decision gate`)** T-2.4 must classify before T+1.1 (Anchor program bootstrap) can proceed
- **(`Cargo.toml`)** `anchor-lang = "0.28"` listed as planned dep (commented or not yet activated — verify)

### (`REM Phase 3`/`Deferred`)
- **(`Tools/ankh-forge LIFECYCLE.md`)** Phase 1 complete, Phase 2 complete (18/18 tests), Phase 3 deferred
- **(`Phase 3 requirement`)** GPU-compressed stones — requires Vulkan compute dispatch from `vulkan-lab/cli-renderer`
- **(`Unlocks when`)** V9 Vulkan renderer (`VULKAN_CLI_RENDERER_V9`) has a compute pipeline that can accept stone payloads

---

## (`SECTION-5`/`MCP-ECOSYSTEM`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate--1--mcp-ecosystem-modernization-intelligence-layer)*

---

### (`Registered-MCP-Servers`/`From-.mcp.json`)

| Server | Implementation | Transport | Scope |
|---|---|---|---|
| `game` | `scripts/mcp-game.ts` | stdio/Bun | Wraps `game-cli.exe`; tools: `game_new`, `game_observe`, `game_act` |
| `sourcer` | `scripts/mcp-sourcer.ts` | stdio/Bun | Session intelligence extraction |
| `sonic` | `scripts/mcp-sonic.ts` | stdio/Bun | Audio processing (sonic-lake) |
| `corpus` | `scripts/corpus-mcp.ts` | stdio/Bun | 18 tools; corpus.sqlite; semantic search via sqlite-vec |
| `cocoindex-code` | `.local/bin/ccc.exe` | local binary | Semantic code search |
| `github` | `api.githubcopilot.com/mcp/` | HTTPS Bearer | GitHub API |
| `huggingface` | `huggingface.co/mcp` | HTTPS Bearer | HF Hub |
| `mas-mcp` | `mas_mcp/server.py` | FastMCP | GPU-backed entity analysis + SSOT drift |

---

### (`corpus-mcp`/`Gate-State`)

- **(`Current gate`)** G9 — `corpus_federation_query` (cross-satellite ATTACH) + `corpus_semantic_search` (Qwen3-Embedding-0.6B vectors via sqlite-vec) both live
- **(`Session inventory`)** 15 sessions in `manifest/sessions/`; `manifest/session_ranked_index.json` composite scores
- **(`Top session`)** `2b2dfd13` (composite 0.6882, 6,328 turns, 578 file edits — ruby/uv rebuild drift)
- **(`Next-Gate`/`G10`)** cross-satellite semantic search — single query returns from chthonic-archive + pnk-live + csb-live simultaneously via `ATTACH DATABASE` across three corpus.sqlite paths

---

### (`chthonic-mcp`/`Copilot-SDK-Server`)

- **(`SID`)** `TOOL_CHTHONIC_MCP_V1`
- **(`Last updated`)** 2026-05-28 (github-copilot-sdk bump to beta.9)
- **(`Tools`)** `query_corpus`, `get_session_warmstart`, `gpu_gate_status`, `lens_query`, `todo_roulette_next`
- **(`Hooks`)** `PreToolUse` gate on `todo_roulette_next` (Claudine CET approval); `SystemMessageTransform` injecting warmstart context from `manifest/session_ranked_index.json`
- **(`Claudine CET mode`)** 24-hour mood-based mode selection (hour-based UTC → CET match)
- **(`Pentea agentStop queue`)** `scripts/pentea_autoloop.ts` — reads `Pentea-Next:` git trailer after each turn; if trailer changed, injects next task via `{ decision: "block", reason: "..." }`. **0 live runs as of grilling.**
- **(`Beta.9 gap`)** verify all new hooks in beta.9 (vs beta.8) are implemented; `meta-ide/copilot-sdk/sdk/index.d.ts` is the changelog source

### (`mas_mcp`/`GPU-Intelligence-Server`)

- **(`SID`)** `SERVER_MPW_ROUTER_V1`
- **(`GPU backend enum`)** `NONE | CUPY | NUMBA | VULKAN | ONNX_GPU`
- **(`RTX 4090 probe`)** 16GB, Ada Lovelace, 7424 CUDA cores (Laptop GPU variant)
- **(`Scoring operations`)** novelty / redundancy / safety as `np.ndarray` batch scores
- **(`Tools`)** `narrative_scan`, `qualia_check`, `scan`, `entity_deep`, `pulse`, `validate_entity`, `pid_reader`, `policy_check`, `probe_gpu_capabilities`
- **(`⚠ Gap`)** active backend not verified — `--probe` flag exists but result not committed to manifest

### (`Birdcage`/`birdcage/`)

- **(`Stage`)** 0 only — first agentic chamber, plumbing verification
- **(`Probes`)** Azure-for-GitHub models, Windows AI Foundry Local, VS Code Copilot Chat
- **(`Output`)** `birdcage/runs.jsonl`
- **(`Stage 1`)** undefined — the next probe in the chain after auth connectivity is confirmed

---

## (`SECTION 6`/`·`/`GAME`/`+`/`LORE LAYER`)
*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#t-23--character-schema--full-lore-validation-pass-auto), [Gate +4](TODO.md#gate-4--game-engine--v2-architecture-living-world)*

---

### (`Game Engine`/`src/`)

- **(`SID`)** `GAME_MAIN_ENTRY_V1` — "The Chthonic Archive: Triumvirate Ascension"
- **(`ECS`)** Bevy ECS 0.18.1 — entities have bundles of components, not inheritance
- **(`Data modules`)** `src/data/types.rs`, `src/data/loader.rs`, `src/data/persistence.rs`, `src/data/factions.rs`, `src/data/game_tree.rs`, `src/data/game_schemas.rs`, `src/data/lore_loader.rs`, `src/data/verifier.rs`
- **(`Entity model`)**:
  - `PhysicsData`: WHR, body measurements, physical descriptors
  - `GameStats`: health / power / defense / conceptual_capacity
  - `LoreData`: scent, word_count, EDFA excerpt
  - `FactionRegistry`: factions + matriarchs + districts + `tsrp_state`
- **(`Planned`)** Solana on-chain entropy (`anchor-lang 0.28`) — see Section 4

### (`Lore-Hierarchy`/`game/lore/`)
```
game/lore/
  characters/
    character.schema.json   ← validation schema
    heart/
      T1/
        orackla.json        ← T1 Triumvirate member (only file found at heart/T1/)
    archetypes/
    species/
  factions/
    triumvirate.json
    prime_factions.json
  archetypes/
  abbr-system.json          ← TARGET for dumpster-dive HIGH-GRADE ore migration
```
- `orackla.json` is the only character confirmed under `heart/T1/` — implies other T1 characters may be missing, pending, or in satellites
- `triumvirate.json` and `prime_factions.json` must cross-ref existing character IDs — this is what `lore-canon` CI check validates

### (`game/core`/`game/core/src/`)

- `lib.rs` + `main.rs` — the game logic binary (`game-cli.exe`)
- Wrapped by `scripts/mcp-game.ts` for MCP tool access
- Game state persisted to `.chthonic/game/active_run.json`

---

## (`SECTION 7`/`·`/`VULKAN RENDERER`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate-1--solana--gpu-compute-integration-frontier-engineering), [Gate +4](TODO.md#gate-4--game-engine--v2-architecture-living-world)*

---

### (`Gate Walk`/`vulkan-lab/cli-renderer/`)

- **(`Current SID`)** `VULKAN_CLI_RENDERER_V9`

| Gate | Status | What it proved |
|---|---|---|
| G1 | ✅ | Headless Vulkan instance + RTX 4090 device selection (`1c073231`) |
| G2 | ✅ | EulerTask SSBO → `euler_score.comp.spv` → sorted output (`d135e3a1`) |
| G3 | ✅ | `transition_image_layout()` + VkImage 480×80 + `ascii_downsample.comp.spv` + ANSI block-char stdout (`cb8be770`) |
| G4 | ✅ | `dirty_diff.comp.glsl` + 33ms loop + `prev_buf`/`dirty_buf` + `RESET_COMMAND_BUFFER` + `--live` mode in `todo_roulette.ts` (`34a7a947`) |
| G5 | ✅ | `SpinState ≡ RoomState` — same FSM written once (`{Idle,Spinning,Decelerating,Landed}` = `{Locked,Unlocked,Visited,Cleared}`) |
| G6 | ✅ | `--mode=polar` (roulette) vs `--mode=dungeon` (Urca de Lima synthesis — see Section 9) |
| G7 | ✅ | crossterm integration (V9) |

- **(`Reads`)** `manifest/todo_roulette.json` (8 entries, mostly completed)
- **(`IPC`)** stdin JSON `{"cmd":"quit"}` → TS orchestrator sends SIGINT cleanly
- **(`Next gate`)** full dungeon cRPG loop — rooms persist cleared state; traversal emits entropy hashes → Solana V10

### (`Build-Notes`)
- `build.rs` compiles `.comp.glsl` → `.comp.spv` via shaderc; stage must be explicit (`-fshader-stage=compute`)
- HOST_COHERENT buffers (no staging) at manifest scale; QF=2 COMPUTE-only selected
- Isolated `[workspace]` in `vulkan-lab/cli-renderer/Cargo.toml` — run cargo from this directory, not repo root

---

## (`SECTION 8`/`·`/`VS CODE EXTENSION`)
*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#t-22--extension-hallucinatory-ladderization-remediation-decision)*

### (`Architecture`/`extensions/chthonic-archive/`)
- **(`SID`)** `EXT_EXTENSION_V1`
- **(`Activation lanes`)** (LaneRegistry states: READY|LIVE|PARKED|DISABLED|DEGRADED|UNAVAILABLE|MISSING):

| Lane | Key file | Notes |
|---|---|---|
| `dev-reload` | `src/runtime/devAutoReload.ts` | — |
| `webview-hmr` | `src/runtime/webviewHmrWatcher.ts` | — |
| `markdown-paste` | `src/activation/activateMarkdownPaste.ts` | — |
| `statusbar` | `src/activation/activateStatus.ts` | ⚠ still refs quarantined `chthonic-statusbar` |
| `sidecars` | `src/activation/activateSidecars.ts` | ⚠ blocks host startup |
| `views` | `src/activation/activateViews.ts` | — |
| `commands` | `src/activation/activateCommands.ts` | — |
| `flux` | `src/flux/fluxService.ts` | FLUX1 DiT image generation |
| `status` | `src/activation/activateStatus.ts` | — |
| `cockpit` | `src/activation/activateCockpit.ts` | — |

- **(`Sidecar-Components`)** `entropyClient`, `polyglotOrchestrator`, `selfHealingLoop`, `annoClient`, `cockpitLayout`, `synapseBridge`
- **(`View-Vomponents`)** `ActivityBarMorph`, `DesignFrameProvider`, `DeepFocusLayout`, `RestoreOrderLayout`, `LoomViewProvider`, `StylusInputProvider`, `ThemeTreeProvider`, `StatusTreeProvider`
- **(`computeRustificationReport()`)** watches toolchain files (uv.lock, Cargo.toml, mise.toml, etc.) → surfaces toolchain completeness score in status bar
- **(`Solana-Config-Reads`)** in `src/entropy/entropyConfig.ts`: `solanaRpcUrl`, `autostartValidator`, `walletPath`, `idlPath` — status unknown (see Section 4)

---

### (`FLUX Pipeline`/`Zero-Copy-CUDA-IPC`)

- The deepest engineering surface in the extension layer:

```
VS Code FluxService (TS)
  → named pipe \\.\pipe\chthonic-flux-dit
  → apps/chthonic-tensor-bridge (C++ N-API addon, CMake, Win32 only)
    - Secure master-secret slot
    - NVML/registry hardware fingerprint
    - CreateProcessW stdin redirection
    - Zero-copy MMF image transport
  → apps/flux-satellite (Python 3.14)
    - T5-XXL + CLIP-L text encoding
    - Scheduler + latent + VAE decode
    - CUDA IPC handles for DiT input tensors
  → TrtEngine::RunDitIpc (TensorRT FP8 SM89 engine)
    - Result lands in VRAM without copy
    - No tensorrt Python import (bypass for Python 3.14)
```

- This architecture is designed but needs an end-to-end run to confirm latency. The `apps/chthonic-tensor-bridge` N-API addon requires MSVC (not MinGW) and CMake — same toolchain as flash_attn builds.

---

## (`SECTION-9`/`·`/`CORPUS`/`+`/`SESSION INTELLIGENCE`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate-2--corpus-intelligence-upgrade-semantic-memory-deepening)*

---


### (`corpus.sqlite`)

- 15 sessions archived in `manifest/sessions/<id>/`
- `session_ranked_index.json` — composite scores, editCount, turnCount, tool_freq
- **(`Top session`)** `2b2dfd13` (0.6882 composite, 6,328 turns, 578 edits — ruby/uv rebuild drift session)
- **(`sqlite-vec integration`)** Qwen3-Embedding-0.6B vectors; `corpus_semantic_search` live at G9
- **(`FTS5 full-text search`)** across all session turns

---

### (`Session Vampire`)

- `uv run .agents/skills/session-vampire/scripts/vampire.py` — drains JSONL transcripts
- Outputs: per-session `drain.json` + cross-session `session_blood.json`
- Extracts: file_edits (by path), terminal_commands, code_blocks, commit_refs, memory_files
- **Status:** not run against all 15 sessions — `session_blood.json` may be stale or absent

---
### (`Overnight Archaeology`)
- Daemon runs against satellites (primarily pnk-live's 9,224-file corpus)
- Outputs ore files to `dumpster-dive/`
- All 96 current ore files are `status: "pending"` — daemon has run but upcycling has not

---

## (`SECTION-10`/`·`/`AGENT COURT`)

*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate-3--agent-court-modernization-intelligence-surface)*

### (`Court Structure`)

- **`.claude/agents/`** — 50+ named agent `.md` files (Claude Code invocable)
- **`.github/agents/`** — VS Code picker surface (flat PascalCase `*.agent.md`); `_index.md` is the naming registry
- **`.agents/skills/`** — shared skills (api-manager, corpse-reviver, imagegen, sora, dumpster-upcycler, session-vampire, etc.)
- **`.codex/skills/`** — Codex-side skill lane (mirrors `.claude/skills/`)
- **`.claude/skills/`** — Claude-side skill lane
- **`.off` variants** — alt-mode agents disabled by extension (`*.uniform.off`, `*.one-trick.off`, `*.standardized.off`)

---

### (`Parity State`)

- `tech-debt-triage` — exists in `.claude/skills/`, NOT in `.codex/skills/`
- `industrious-workiq` — exists in `.claude/skills/`, NOT in `.codex/skills/`
- `dumpster-upcycler` — likely asymmetric (Claude-only)
- **Parity auditor** (`parity-auditor.agent.md`) can produce `manifest/parity_audit.json` — has not been run since last skill additions

---

### (`Pentea Queue Chain`)

- `scripts/pentea_autoloop.ts` — agentStop hook reads `Pentea-Next:` git trailer; chains tasks without user
- **Status: 0 live runs.** Script is written, never invoked. First run recommend: T-4.3 → T-4.4 → T-4.5 (mechanical, low-risk, autofix-capable)

---

## (`SECTION-11`/`·`/`THE URCA DE LIMA SEAM`)
*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#gate-0--structural-synthesis-architecture-convergence)*

### (`Known-Isomorphism`/`Todo-Roulette`/`≡`/`Dungeon`)

- `manifest/todo_roulette.json` — 8 task entries with: `id`, `weight`, `status`, `verify_condition`, `TAG_COLOR`, `description`
- **Polar projection (--mode=polar):** weight → Euler arc span; tag → compass bearing degrees; status → spin phase
- **Dungeon projection (--mode=dungeon):** weight → room area; tags → biome; status → room state; verify_condition → locked door trigger
- **The FSM identity:** `SpinState{Idle, Spinning, Decelerating, Landed}` ≡ `RoomState{Locked, Unlocked, Visited, Cleared}` — same 4-state transition graph; written once in `StatePhase` enum, serves both render modes
- **Pattern origin:** documented in `.github/instructions/pattern-nursery.instructions.md` as `Urca-de-Lima Synthesis` (`novel`)

---

### (`Next-Isomorphism-Candidates`/`Not-Yet-Confirmed`)

- **(`session_ranked_index.json`)** — consumed by: chthonic-mcp (warmstart injection), session-vampire (re-ranking), corpus-mcp (timeline). Three projections from one manifest.
- **(`todo_roulette.json`)** — consumed by: cli-renderer (Vulkan display), CI runner (task gate), ankh-forge (trail breadcrumbs). Already three projections — is there a fourth?
- **(`Detection-Heuristic`/`From-Pattern-Nursery`)** — if ≥80% of fields in system A map cleanly to system B, they are one system with two projection functions, not two systems.

---

## (`SECTION-12`/`·`/`HEALTH-SUMMARY-AT-GRILLING-DATE`)

*Direct feed for [TODO.md (The-Savant-High-Bounties)](TODO.md#acceptance-criteria--the-1010-run)*

| Criterion | State at grilling | TODO gate |
|---|---|---|
| CI all-pass | ❌ 2 FAILED, 4 advisory, 1 degraded | Gate -4 |
| Rust compile | ✅ 0 errors (confirmed) | Gate -3 |
| DSL coverage | ❌ FAILED (regression, date unknown) | Gate -5 |
| Dumpster ore processed | ❌ 96/96 pending | Gate -2 T-2.1 |
| Corpus G10 live | ❌ G9 only | Gate -1 T-1.1 |
| Urca isomorphism documented | ✅ 1 (todo_roulette≡dungeon); next TBD | Gate 0 T0.1 |
| Solana devnet entry | ❌ Not started | Gate +1 T+1.1 |
| Pentea queue chain run | ❌ 0 live runs | Gate +3 T+3.3 |
| ECS entity pass | ❌ Not verified | Gate +4 T+4.1 |
| Accurate map committed | ❌ Not created | Gate +5 T+5.1 |

**(`Score-At-Grilling`/`1/10`)** The one passing criterion (Rust compile) is the floor. Everything else is work.

---

## (`SECTION-13`/`·`/`CLAUDEBASE`)
*Feeds: [TODO.md (The-Savant-High-Bounties)](TODO.md#t04--claudebase-harbor--charts-bootstrap-auto)*

### (`What-It-Is`/`Description`)
- **(`Location`/`Path`)**: `CLAUDEBASE/` — a clean sub-codebase within the chthonic-archive polyrepo. Not a satellite. Not a junction.
- **(`SID`/`Identifier`)**: `CLAUDEBASE_ROOT_V1`
- **(`Commissioned`/`Date`)**: 2026-06-05 — all 6 directories empty at commissioning
- **(`Governance-Chain`/`Path`)**: `CLAUDEBASE/README.md` → `.chthonic/SSOT.md` → world-document
- **(`Register`/`Theme`)**: Nautical · Victorian · Renaissance — themed for the T1 matriarch whose operational arm this is

---

### (`Directory-Map`/`Contents`)

| Directory | Nautical role | Contents when commissioned |
|---|---|---|
| `harbor/` | Entry — where sessions dock | Warmstart packets, recent arrivals, active session context |
| `logbook/` | Record — captain's log | Session retrospectives, post-mortems, what was learned |
| `charts/` | Navigation — sea charts | Gate maps, sprint boards, cross-refs to TODO.md |
| `hold/` | Cargo — ship's hold | Skills, agents, tools stowed for this base |
| `watch/` | Sentinels — crow's nest | Probes, health artifacts, CI gate results |
| `quarterdeck/` | Command — ship's wheel | Dispatch protocols, routing config, orchestration |

---

### (`What-Does-NOT-Live-Here`/`·`/`Exclusions`)
- Raw session JSONL → `manifest/sessions/`
- Corpus SQLite → `manifest/corpus.sqlite`
- CI artifacts → `manifest/`
- World-document → `.github/copilot-instructions.archive.md` (the world-document is never duplicated)
- RootDIR SSOT pointer → `.chthonic/SSOT.md`

---

### (`Population-Protocol`/`·`/`Guidelines`)
- A directory is **commissioned** when it contains ≥1 non-`.gitkeep` file with an SID annotation
- Commissioning order: `harbor/` → `charts/` → `hold/` → `quarterdeck/` → `watch/` → `logbook/`
- `logbook/` fills last — it records what the others have done

---

## (`HOW-TO-USE-THIS-FILE`)

```
You are executing TODO.md.
A task's evidence is in the GRILLING.md section number listed in the gate header.
A finding's task is in the TODO gate number listed in each section header.
When a task says [DECISION]: read the relevant GRILLING section first.
When a task says [AUTO]: the grilling already confirmed the command path — execute it.
All probe outputs go to manifest/. Never to terminal. Never in here.
```

---

*SID: GRILLING_PACKET_V1 · Execution plan: TODO.md · 2 rounds · 40+ files · 13 sections*
