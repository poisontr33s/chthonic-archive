---
# ☥ CHTHONIC ARCHIVE — WORLD-LEVEL STRATEGIC TODO
# SID: TODO_MASTER_GRILL_V1
# Lifecycle: permanently-living-document
# Methodology: Blocker-as-Can-Opener · Probe-Manifest-CI-Membrane · Urca-de-Lima Synthesis
# Evidence base: GRILLING.md
# Last grilled: 2026-06-05 · rounds 2 · files 40+ · subsystems 10 · compile errors 0
---

## (`READING-THIS-FILE`)

**(`Every-Task-In-This-File-Has-Evidence`/`Evidence`)** The evidence lives in [GRILLING.md](GRILLING.md).
- Before executing a `[DECISION]` task: read the corresponding `GRILLING`-section.  
- **(`Before-Disputing-Acceptance-Criterion`/`Reason`)** Before disputing an acceptance criterion: the grilling observation is the reason it exists.

- Gates are ordered by **(`Dependency-Depth`)** — earlier gates unlock later ones.  
- Each gate has an **(`Acceptance-Criteria`)** — section. A gate is CLOSED until ALL criteria are met.  
- `-n` prefix = foundational (must precede `+n`). `+n` prefix = emergent (can open after `-n` closes).  
- Sub-tasks marked `[AUTO]` can be autonomously executed — command paths verified during grilling.  
- Sub-tasks marked `[DECISION]` require a judgment call — read the `GRILLING`-section first.  
- Sub-tasks marked `[BLOCKED-BY: GN]` cannot start until gate N is closed.

**(`All-Probe-Outputs-Go-To-Manifest`/`Reason`)** All probe outputs go to `manifest/`. Never to terminal. The **(`CI-Membrane`)** — reads manifests — not scrollback.

---

## (`GATE`/`-5`/`·`/`GOVERNANCE-INTEGRITY`/`Substrate-Health`)

> **(`Grilling-Evidence`)** [GRILLING.md §1 Governance Substrate](GRILLING.md#section-1--governance-substrate)

> **(`Can-Opener`/`→`/`Gate`/`-4`)** *Clean governance means every downstream agent operates on verified schema.* 

> *If DCRP is drifting, all SID annotations built on it are suspect.*

---

### (`T-5.1/·/DCRP Hash Drift Audit`/`[AUTO]`)

- [ ] Run `bun run ci/checks/canon-drift.ts --report` and capture output to `manifest/dcrp_audit.json`
- [ ] For any hash mismatches: trace the delta to the originating diff in git log
- [ ] If mismatch is intentional (purposeful edit to SSOT): update `.dcrp_state.json` hash with new SHA-256
- [ ] If mismatch is accidental drift: revert the drifted file to match SSOT
- [ ] **(`Acceptance`)** — `canon-drift` CI check exits 0 with zero mismatches

---

### (`T-5.2`/·/`SSOT-Section-Map-Verification`/`[AUTO]`)

- [ ] Read `.chthonic/SSOT.md` — confirm it accurately describes the frozen monolith's section inventory (§I–§XVII)
- [ ] Read the section titles in `.github/copilot-instructions.archive.md` — confirm §XIV (Dev Conventions), §XV (DCRP), §XVI (APCR) exist as section titles (not line numbers — FA⁵ forbids line-number addressing)
- [ ] Audit `.github/instructions/*.instructions.md` — find any §-refs that cite sections not present in the frozen monolith
- [ ] Verify all skill `<file>` paths listed in `.chthonic/SSOT.md` resolve to actual files on disk
- [ ] File findings as `manifest/ssot_section_audit.json`
- [ ] **(`Acceptance`)** — zero dangling §-refs in any branch instruction file; all `<file>` paths in `.chthonic/SSOT.md` resolve

---

### (`T-5.3/·/Chthonic DSL PEG Coverage Regression Fix`/`[DECISION]`)

> **Status: CI FAILED** (`dsl-conformance` check failing as of 2026-05-31)
- [ ] Run `uv run scripts/dsl_iteration_check.py --dry-run` — identify which grammar rule regressed
- [ ] Inspect `manifest/dsl_iteration_history.ndjson` — find the last passing iteration key
- [ ] Compare grammar snapshot at last-pass SHA vs current grammar
- [ ] `[DECISION]` Determine if regression is from: (a) narrowed rule too aggressively, (b) new SSOT content not covered, (c) ledger SHA out of sync
- [ ] Apply fix (expand rule / add alternation / reset ledger SHA)
- [ ] Run `uv run scripts/dsl_iteration_check.py` (without --dry-run) — verifies + writes new ledger entry
- [ ] Run `bun run ci/checks/dsl-conformance.ts` — must exit 0
- [ ] **(`Acceptance`)** — `dsl-conformance` CI check exits 0; coverage ≥ last-pass baseline

---

### (`T-5.4`/`·`/`Active`/`.github/instructions`/`Pointer Integrity`/`[AUTO]`)

- [ ] Run `bun run .agents/skills/link-path-guard/scripts/validate_links.ts` (or uv equivalent) against all `.github/instructions/*.instructions.md`
- [ ] Fix any broken `c:\...` absolute paths → repo-relative equivalents
- [ ] Verify all skill `<file>` tags listed in `.chthonic/SSOT.md` resolve to actual files on disk
- [ ] **(`Acceptance`)** — link-path-guard exits 0 on all instruction files; zero broken `<file>` paths in `.chthonic/SSOT.md`

---

## (`GATE`/`-4`/`CI SYSTEM INTEGRITY`/`Enforcement Health`)
> **(`Grilling-Evidence`)** [GRILLING.md §2 CI System](GRILLING.md#section-2--ci-system)

> **(`Can-Opener`/`→`/`Gate`/`-3`)** — *Once CI is clean and enforcing, every subsequent code change is gatekept automatically.*

---

### (`T-4.1`/`·`/`Fix`/``bun-audit``/`FAILED`/`[AUTO]`)

> **(`Status`/`CI FAILED`)** *— unaddressed JS dependency vulnerabilities*
- [ ] Run `bun audit` in repo root — capture full vulnerability report
- [ ] For each vulnerability: check if a non-breaking patch version exists
- [ ] Run `bun update --filter <package>` for patchable vulnerabilities
- [ ] For major-breaking vulnerabilities: open a `manifest/security_advisory_<pkg>.json` with impact assessment
- [ ] For each irreducible vulnerability: add it to `bunfig.toml` audit exception with justification comment
- [ ] Re-run `bun audit` — must exit 0 or have only explicitly excepted items
- [ ] **(`Acceptance`)** — `bun-audit` CI check exits 0

---

### (`T-4.2`/`·`/`Fix`/`GitHub Actions Dispatch`/`25% success rate`/`[DECISION]`)

> **(`Status`/`Degraded`)** — 5 dispatch failures, only 3 active workflows
- [ ] Enumerate `.github/workflows/` — identify the 3 active vs 5 disabled (`.yml.off`)
- [ ] For each active workflow (`claudine-cloud-dispatch.yml`, `pentea-cloud-dispatch.yml`, `dependabot-auto-merge.yml`):
  - [ ] Inspect last 5 runs in `manifest/gh_runs_audit.json` (or via `bun run ci/checks/gh-runs.ts --report`)
  - [ ] Identify failure type: token expiry / event trigger mismatch / missing env secret / runner OS mismatch
- [ ] Fix or disable each failing workflow
- [ ] `[DECISION]` Assess which of the 5 disabled workflows should be re-enabled for the current codebase state
- [ ] **(`Acceptance`)** — `gh-runs` CI check exits 0; all active workflows showing ≥90% success rate

---

### (`T-4.3`/`·`/`Resolve`/`62 uv-guard Violations`/`[AUTO]`)

> **(`Status`/`Advisory`)** — 62 Python scripts not using `uv run` invocation pattern
- [ ] Run `bun run ci/checks/uv-guard.ts --report` → get list of violating scripts
- [ ] Group by violation type: (a) `python script.py` invocations, (b) `#!/usr/bin/env python3` without uv wrapper, (c) subprocess calls not routing through uv
- [ ] Apply `uv run` wrapper to all Type-A violations that are direct invocations
- [ ] For Type-B: headers are fine; only shebang + invocation context matters
- [ ] **(`Acceptance`)** — `uv-guard` advisory count ≤ 5 (irreducible edge cases are excepted with comments)

---

### (`T-4.4`/`·`/`Resolve`/`35 SID Envelope Issues`/`[AUTO]`)

> **(`Status`/`Advisory`)** — 5 missing SIDs, 30 malformed SID annotations
- [ ] Run `bun run ci/checks/sid-envelope.ts --report` → export `manifest/sid_audit.json`
- [ ] For 5 missing SIDs: assign canonical SID names (format: `DOMAIN_NAME_VN`, e.g., `SCRIPT_SESSION_WATCHER_V1`)
- [ ] For 30 malformed: inspect pattern failures — likely `@SID:` prefix missing, or wrong format (should be `# @SID: IDENTIFIER_V1`)
- [ ] Apply fixes in batch (autofix mode if available: `bun run ci/checks/sid-envelope.ts --fix`)
- [ ] **(`Acceptance`)** — `sid-envelope` check exits 0; 0 missing, 0 malformed

---

### (`T-4.5`/`·`/`Resolve`/`5 Non-Canonical Python Headers`/`[AUTO]`)

> **(`Status`/`Advisory`)** — 5/436 Python files missing canonical header
- [ ] Run `bun run ci/checks/python-headers.ts --fix` (autofix mode supported)
- [ ] Verify each fixed file still passes `ruff check` (no introduced syntax issues)
- [ ] **(`Acceptance`)** — `python-headers` check exits 0

---

### (`T-4.6`/`·`/`CI Gate 0`/`Full Clean Run`/`[AUTO]`)

> **(`BLOCKED-BY`)**: T-4.1 through T-4.5
- [ ] Run `bun run ci/run.ts --full` against main
- [ ] Capture output to `manifest/ci_gate0_baseline.json`
- [ ] All 21 checks must exit 0 or advisory (no FAILED, no degraded)
- [ ] **(`Acceptance`)** — CI full run exits 0; this is the new clean baseline

---

## (`GATE`/`-3`/`·`/`TOOLCHAIN COHERENCE`/`Runtime Health`)

> **(`Grilling-Evidence`)**: [GRILLING.md §3 Toolchain](GRILLING.md#section-3--toolchain)

> **(`Can-Opener`/`→`/`Gate`/`-2`)**: Once toolchain is coherent, source code changes compile predictably.

---

### (`T-3.1`/`·`/`Rust Workspace Compile Verification`/`[AUTO]`)
- [ ] Run `cargo check --workspace` from repo root — capture errors to `manifest/cargo_check.json`
- [ ] Run `cargo check --workspace` from `vulkan-lab/cli-renderer/` (isolated workspace)
- [ ] Run `cargo check` from `game/core/`
- [ ] Resolve any compile errors surfaced (type mismatches, missing impls, unused imports flagged as errors)
- [ ] **(`Acceptance`)** — `cargo check --workspace` exits 0 across all three workspace roots

---

### (`T-3.2`/`TypeScript Type Coverage`/`[AUTO]`)

- [ ] Run `bun run tsc --noEmit` from `extensions/chthonic-archive/`
- [ ] Run `bun run tsc --noEmit` from repo root (covers scripts + ci + apps/chthonic-next)
- [ ] Capture errors to `manifest/tsc_audit.json`
- [ ] Fix type errors in order: (a) null/undefined guards, (b) missing return types, (c) any-typed params
- [ ] **(`Acceptance`)** — `tsc --noEmit` exits 0 on both roots

---

### (`T-3.3`/`·`/`Python Environment Verification (uv)`/`[AUTO]`)

- [ ] Run `uv sync --all-extras --dev` — verify `pyproject.toml` resolves cleanly
- [ ] Run `uv run python -c "import torch; print(torch.cuda.is_available())"` — CUDA verification
- [ ] Run `uv run python -c "import flash_attn; print(flash_attn.__version__)"` — flash_attn gate
- [ ] Run `uv run python -c "import triton; print(triton.__version__)"` — triton-windows gate
- [ ] File gate results to `manifest/py_toolchain_gate.json`
- [ ] **(`Acceptance`)** — all 4 imports succeed; `py_toolchain_gate.json` shows all gates admitted

---

### (`T-3.4`/`·`/`Satellite Polyrepo Freshness`/`[AUTO]`)

- [ ] Run `pwsh scripts/polyrepo-runner.ps1 -Quick -NoFetch` — quick sweep of 8 satellites
- [ ] For any satellite showing uncommitted changes: assess if intentional or drift
- [ ] Run `pwsh scripts/polyrepo-runner.ps1 -Report` — emit `manifest/polyrepo_gate.json`
- [ ] **(`Acceptance`)** — `spread-freshness` CI check exits 0; `polyrepo_gate.json` shows all satellites at expected SHAs

---

### (`T-3.5`/`·`/`Bun + Node Module Audit`/`[AUTO]`)
- [ ] Run `bun install` from repo root — verify lockfile consistency
- [ ] Run `bun install` from `extensions/chthonic-archive/`
- [ ] Run `bun install` from `apps/chthonic-next/`
- [ ] Verify no postinstall scripts that download external binaries without pinned hashes
- [ ] **(`Acceptance`)** — all `bun install` exits 0; no lockfile drift

---

## (`GATE`/`-2`/`·`/`ARCHITECTURAL DEBT REDUCTION`/`Structure Health`)

> **Grilling evidence:** [GRILLING.md §4 Architectural Debt](GRILLING.md#section-4--architectural-debt)

> **Can-opener → Gate -1:** Cleared debt means the architecture is describable; the map matches the territory.

---

### (`T-2.1`/`·`/`Dumpster-Dive Ore Processing — ASC Toolchain Migration`/`[DECISION]`)

> **(`Status`/`96-Ore-Files`/`All`/`Status`/`"Pending"`/`Highest-Value-Item`/`asc.py`/`4083-Lines`/`Rated`/`⚗️`/`HIGH-GRADE`)**
- [ ] Read `dumpster-dive/ORE_MANIFEST.json` — enumerate all 96 items by rating (HIGH-GRADE / MID / LOW)
- [ ] For `asc.py` (4083 lines): run the corpse-reviver skill to extract callable modules
  - [ ] Identify public API surface (functions/classes used by other scripts)
  - [ ] Extract to `mas_mcp/lib/asc_toolchain.py` with preserved docstrings
  - [ ] Update `mas_mcp/server.py` imports to use new path
  - [ ] Write `uv run python -m pytest mas_mcp/lib/test_asc_toolchain.py` tests for extracted API
- [ ] For `abbr-system.json` (rated HIGH-GRADE): migrate to `game/lore/abbr-system.json` with schema validation
- [ ] For remaining HIGH-GRADE items: process via `uv run scripts/dumpster_upcycler.py` batch mode
- [ ] Update each processed item's `ORE_MANIFEST.json` entry to `status: "processed"` + destination path
- [ ] **(`Acceptance`)**: all HIGH-GRADE ore items are `processed`; `asc.py` callable API lives in `mas_mcp/lib/`

---

### (`T-2.2`/`·`/`Extension Hallucinatory Ladderization Remediation`/`[DECISION]`)

> **(`Diagnosed-In`/`docs/extension-modernization-grill-packet.md`/`3-Root-Problems`)**
- [ ] Problem 1 — Activation coupling: decouple sidecar setup from extension activation sequence
  - [ ] Audit `src/activation/activateSidecars.ts` — identify which sidecars block extension host startup
  - [ ] Move blocking sidecars to lazy-activate (on first use, not on activation)
  - [ ] Verify extension activation time < 200ms with sidecars deferred
- [ ] Problem 2 — Status report references folded extension:
  - [ ] Find all references to `chthonic-statusbar` in `src/runtime/statusReport.ts`
  - [ ] Replace with direct status bridge calls (chthonic-statusbar is quarantined, not installed)
  - [ ] Verify status bar renders correctly without the folded extension
- [ ] Problem 3 — E2E tests mutate real workspace:
  - [ ] Audit `test/` — find all tests that write to real workspace paths
  - [ ] Replace with `vscode.Uri.joinPath(context.extensionUri, 'test-fixtures/')` sandbox
  - [ ] Add `afterEach` cleanup in all mutating tests
- [ ] Quarantine legacy extensions (not delete): move to `.deprecated/extensions/` with a README explaining the hallucinatory-ladderization diagnosis
- [ ] **(`Acceptance`)**: extension activates in < 200ms; `bun run test` in extensions/ exits 0; no real workspace mutations in tests

---

### (`T-2.3`/`·`/`Character Schema — Full Lore Validation Pass`/`[AUTO]`)
- [ ] Run `bun run ci/checks/character-schema.ts --report` → get list of all characters and their schema compliance
- [ ] Run `bun run ci/checks/lore-canon.ts --report` → get lore canon issues
- [ ] For any character JSON failing schema: identify which fields are missing/wrong-typed
- [ ] Apply fixes (add missing required fields with empty/placeholder values; correct type mismatches)
- [ ] Special case `game/lore/characters/heart/T1/orackla.json` — verify it fully models the T1 Triumvirate member contract:
  - Required: `id`, `name`, `tier`, `organ`, `prism`, `physics_data`, `game_stats`, `lore_data`, `faction_affiliation`
- [ ] Verify `game/lore/factions/triumvirate.json` and `prime_factions.json` cross-ref to existing character IDs
- [ ] **(`Acceptance`)**: `character-schema` + `lore-canon` CI checks both exit 0; zero schema violations

---

### (`T-2.4`/`·`/`Solana Integration Surface Audit`/`[DECISION]`)
> **Extension reads `solanaRpcUrl`, `autostartValidator`, `walletPath`, `idlPath` — are these wired?**
- [ ] Audit `src/entropy/entropyConfig.ts` — list all Solana config fields read
- [ ] Search for actual Solana program calls in `src/` — are there IDL files, anchor types, or just config reads?
- [ ] `[DECISION]` Classify: (a) Solana integration is real and incomplete — mark as NEXT-GATE work; (b) config reads are dead code — remove them cleanly
- [ ] If real: file `manifest/solana_integration_audit.json` with required work
- [ ] If dead: remove Solana config fields and add a comment: `// Solana integration deferred — see TODO.md T-2.4`
- [ ] **(`Acceptance`)**: no orphaned Solana config reads; either fully wired or explicitly deferred

---

### (`T-2.5`/`·`/`REM Phase 3 Gate (GPU-Compressed Stones)`/`[DECISION]`)
> **Status: Phase 2 complete (18/18 tests pass), Phase 3 deferred — requires Vulkan compute integration**
- [ ] Read `tools/ankh-forge/LIFECYCLE.md` and `tools/ankh-forge/src/trail/` to understand Phase 3 contract
- [ ] Identify the specific Vulkan compute operation needed for GPU-compressed stones:
  - Likely: `vulkan-lab/cli-renderer` provides the compute pipeline; `ankh-forge` provides the stone API
- [ ] `[DECISION]` Assess if the V9 Vulkan renderer already has a compute pipeline that can accept stone payloads
- [ ] If yes: wire `ankh-forge` Phase 3 stone API to the compute dispatch in cli-renderer
- [ ] Write integration test: `cargo test --test stone_gpu_integration` — must pass with RTX 4090 available
- [ ] Update `tools/ankh-forge/LIFECYCLE.md` Phase 3 → COMPLETE
- [ ] **Acceptance:** `cargo test --test stone_gpu_integration` exits 0; LIFECYCLE.md Phase 3 marked COMPLETE

---

## (`GATE -1`/`·`/`MCP ECOSYSTEM MODERNIZATION (Intelligence Layer)`/`[AUTO]`)

> **Grilling evidence** — [GRILLING.md §5 MCP Ecosystem](GRILLING.md#section-5--mcp-ecosystem)
> **Can-opener → Gate 0:** — A live, clean MCP layer means every agent and extension call has correct, fast tool resolution.

---

### (`T-1.1`/`·`/`corpus-mcp G9 → G10: Semantic Federation`/`[AUTO]`)

> **(`Status`/`G9-Complete`/`corpus_federation_query`/`+`/`semantic_search`/`Live`)**
- [ ] Define G10: cross-satellite semantic search (single query → returns from chthonic-archive + pnk-live + csb-live simultaneously)
- [ ] Extend `scripts/corpus-mcp.ts`: add `corpus_semantic_federation` tool
  - [ ] Opens all three corpus.sqlite paths via `ATTACH DATABASE`
  - [ ] Runs vector similarity query against all three `embeddings` tables
  - [ ] Returns merged, re-ranked results with `source_satellite` field
- [ ] Write smoke test: `bun run scripts/corpus-mcp-test.ts --semantic-federation "Claudine entropy Rustbelt"` — must return results from ≥2 satellites
- [ ] Update `manifest/corpus_gates.json` → `G10: admitted`
- [ ] **(`Acceptance`)** — `corpus_semantic_federation` returns cross-satellite results; G10 marked admitted

---

### (`T-1.2`/`·`/`chthonic-mcp Beta.9 API Surface Verification`/`[AUTO]`)
> **Updated 2026-05-28 — verify beta.9 contract changes are fully implemented**
- [ ] Read `tools/chthonic-mcp/src/main.rs` — identify all SDK hooks currently implemented
- [ ] Compare against `meta-ide/copilot-sdk/sdk/index.d.ts` beta.9 changelog
- [ ] Identify any new hooks in beta.9 not yet implemented (e.g., new `agentStep` or `toolResult` hooks)
- [ ] Implement missing hooks if they improve warmstart context injection
- [ ] Run `cargo build -p chthonic-mcp` — exits 0
- [ ] **(`Acceptance`)** — all beta.9 hooks relevant to warmstart + tool routing are implemented; build passes

---

### (`T-1.3`/`·`/`mas_mcp — GPU Backend Elevation`/`[DECISION]`)
> **Current: CUPY|NUMBA|VULKAN|ONNX_GPU backends wired; NONE is fallback**
- [ ] Run `uv run mas_mcp/server.py --probe` → identify which backend is currently active on RTX 4090
- [ ] If ONNX_GPU: verify CUDA execution provider is selected (not CPU)
- [ ] `[DECISION]` Assess: should scoring (novelty/redundancy/safety) use CuPy batch ops or ONNX GPU?
- [ ] Whichever is faster: benchmark both with `uv run mas_mcp/gpu_orchestrator.py --benchmark`
- [ ] Lock the winning backend as default in `mas_mcp/config.py`
- [ ] **(`Acceptance`)** — `mas_mcp/server.py` starts with non-NONE GPU backend; benchmark result documented in `manifest/mas_mcp_gpu_benchmark.json`

---

### (`T-1.4`/`·`/`game MCP — Wire game-cli.exe Loop`/`[AUTO]`)
> **`scripts/mcp-game.ts` wraps `game/core/src/main.rs` (`game-cli.exe`)**
- [ ] Run `cargo build -p game-core --release` — verify binary builds
- [ ] Run `bun run scripts/mcp-game.ts` — verify game MCP server starts
- [ ] Test `game_new` → `game_observe` → `game_act` tool sequence manually
- [ ] Verify game state is persisted between turns (`.chthonic/game/active_run.json`)
- [ ] **(`Acceptance`)** — full `game_new → game_observe → game_act` loop works; active_run.json updates on each act

---

### (`T-1.5`/`·`/`Birdcage Probe Sequence Completion`/`[AUTO]`)
> **Stage 0 only — 3 probes exist, no Stage 1**
- [ ] Read `birdcage/README.md` — define what Stage 1 requires
- [ ] Run the 3 existing Stage 0 probes to establish baseline auth connectivity:
  - [ ] Azure-for-GitHub models probe
  - [ ] Windows AI Foundry Local probe
  - [ ] VS Code Copilot Chat probe
- [ ] File results to `birdcage/runs.jsonl`
- [ ] `[DECISION]` Define Stage 1: what is the next probe in the chain? (First agentic call with working auth)
- [ ] **(`Acceptance`)** — 3/3 Stage 0 probes pass; Stage 1 defined and at least one probe written

---

## (`GATE-0`/`·`/`STRUCTURAL-SYNTHESIS`/`Architecture-Convergence`)
> **Grilling evidence:** [GRILLING.md §11 Urca de Lima Seam](GRILLING.md#section-11--the-urca-de-lima-seam) · [GRILLING.md §12 Health Summary](GRILLING.md#section-12--health-summary-at-grilling-date) · [GRILLING.md §13 CLAUDEBASE](GRILLING.md#section-13--claudebase)

> **Can-opener → Gate +1:** Synthesis happens when the architecture map exactly matches the territory.
> This is the Urca de Lima gate — find the hidden isomorphisms.

### T0.1 · Urca de Lima Expansion — Identify Next Isomorphism `[DECISION]`
> **Known isomorphism: todo_roulette ≡ dungeon (same data, two projections). Find the next one.**
- [ ] Enumerate all manifest/*.json files that are consumed by more than one subsystem
- [ ] For each shared manifest: document which subsystems consume it and what projection they apply
- [ ] Candidate: `session_ranked_index.json` — consumed by chthonic-mcp (warmstart) + session-vampire + corpus-mcp (timeline). Is this a three-way isomorphism?
- [ ] Candidate: `todo_roulette.json` — consumed by cli-renderer (Vulkan display) + CI runner (task gate) + ankh-forge (trail breadcrumbs). Is this a three-way isomorphism?
- [ ] `[DECISION]` If a new isomorphism is found: document in pattern-nursery as `novel` + implement `--mode=<third_projection>` in the consuming binary
- [ ] **(`Acceptance`)** — at least one new isomorphism documented in pattern-nursery; implementation PR drafted

### (`T0.2 · NEXT.md — Living Sprint Board Update `[AUTO]`)
- [ ] Locate `NEXT.md` (root or .chthonic/) — the active sprint planning document
- [ ] Update it to reflect the gate structure in this TODO
- [ ] For each gate: add a one-line sprint entry with blockers listed
- [ ] Pin the current "most valuable next action" at the top
- [ ] **(`Acceptance`)** — NEXT.md accurately reflects the gate sequence; first sprint entry is actionable today

### (`T0.3 · dumpster-dive/LESSONS.md — Extract Pattern Promotions `[AUTO]`)
- [ ] Read `dumpster-dive/LESSONS.md` (if exists) or scan `dumpster-dive/*.md` for pattern candidates
- [ ] For each candidate that meets promotion criteria from `pattern-nursery.instructions.md`:
  - [ ] If `familiar` and used in ≥3 sessions: promote to relevant branch instruction file
  - [ ] If `tested` and cross-platform verified: promote to `technical-directives.instructions.md`
- [ ] Update pattern-nursery: mark promoted patterns, add new `novel` candidates from this grilling session
- [ ] **(`Acceptance`)** — pattern-nursery has ≤2 stale items; all `tested` patterns are in the promotion queue

### (`T0.4`/`·`/`CLAUDEBASE-Harbor`/`+`/`Charts-Bootstrap`/`[AUTO]`/`·`)
> **(`Status`/`Commissioned-2026-06-05`/`6-Directories-Empty`/`·`/`Evidence`)**[GRILLING.md §13](GRILLING.md#section-13--claudebase)
- [ ] Populate `CLAUDEBASE/harbor/` — create `harbor/warmstart.md` linking to `manifest/session_ranked_index.json`; assign SID `CLAUDEBASE_HARBOR_V1`
- [ ] Populate `CLAUDEBASE/charts/` — create `charts/gate-map.md` as a lightweight mirror of TODO.md's 11 gate titles with status tracking; assign SID `CLAUDEBASE_CHARTS_V1`
- [ ] Verify both files reference `.chthonic/SSOT.md` as governance chain root (not the world-document directly)
- [ ] **(`Acceptance`)** — `harbor/` and `charts/` each contain ≥1 non-`.gitkeep` file with SID annotation; both reference `.chthonic/SSOT.md`

---

## (`GATE`/`+1`/`·`/`SOLANA`/`+`/`GPU-COMPUTE-INTEGRATION`/`Frontier-Engineering`)
> **Grilling evidence:** [GRILLING.md §7 Vulkan Renderer](GRILLING.md#section-7--vulkan-renderer) · [GRILLING.md §8 VS Code Extension](GRILLING.md#section-8--vs-code-extension)

> **BLOCKED-BY: Gate -2 (T-2.4 Solana audit, T-2.5 REM Phase 3)**  
> **Can-opener → Gate +2:** Live on-chain entropy means the game has real cryptographic stakes.

### T+1.1 · Solana Integration — Anchor Program Bootstrap `[DECISION]`
- [ ] `[DECISION]` Based on T-2.4 outcome: if Solana is real, proceed here
- [ ] Define the minimal Anchor program: single instruction `record_entropy(entropy_hash: [u8; 32])` on devnet
- [ ] Bootstrap: `anchor init chthonic-entropy-program` in `game/solana/`
- [ ] Wire `entropyConfig.idlPath` to the built IDL
- [ ] Write an entropy event in `src/data/game_tree.rs` that produces a hash when a game branch is traversed
- [ ] Submit the hash to devnet via the Anchor client in the entropy worker
- [ ] **Acceptance:** `solana-test-validator` starts; `anchor test` passes on devnet; one entropy hash recorded on-chain

### T+1.2 · Vulkan Renderer V10 — SpinState → Solana Event Feed `[AUTO]`
> **BLOCKED-BY: T+1.1**
- [ ] When a spin lands (`StatePhase::Landed`): extract the selected task's entropy hash
- [ ] Emit it via stdin IPC to the TS orchestrator
- [ ] TS orchestrator calls `record_entropy` via Anchor client
- [ ] Display on-chain confirmation receipt in the ANSI terminal output (SID bump: V10)
- [ ] **Acceptance:** spin → on-chain receipt visible in terminal within 5 seconds; V10 SID committed

### T+1.3 · FLUX DiT — CUDA IPC Zero-Copy Pipeline Stabilization `[DECISION]`
> **Architecture designed; stabilization needed**
- [ ] Run an end-to-end FLUX generation test from VS Code extension FluxService
- [ ] Measure latency: extension command → pipe send → C++ bridge → TRT inference → result back
- [ ] `[DECISION]` If latency > 5s per step: profile TensorRT FP8 engine; check if SM89 channels are fully saturated
- [ ] Add `manifest/flux_pipeline_benchmark.json` with step latency per token
- [ ] Wire FluxService status to the statusbar via the status bridge lane
- [ ] **Acceptance:** FluxService generates a 512×512 image in < 30s; status bridge shows step progress

---

## GATE +2 · CORPUS INTELLIGENCE UPGRADE (Semantic Memory Deepening)
> **Grilling evidence:** [GRILLING.md §9 Corpus + Session Intelligence](GRILLING.md#section-9--corpus--session-intelligence)

> **BLOCKED-BY: Gate -1 (corpus G10)**  
> **Can-opener → Gate +3:** Full semantic memory means every agent call is grounded in cross-session intelligence.

### T+2.1 · Session Vampire — Full Drain Pass on All 15 Sessions `[AUTO]`
- [ ] Run `uv run .agents/skills/session-vampire/scripts/vampire.py --all` against all 15 sessions in `manifest/sessions/`
- [ ] Emit per-session `drain.json` + cross-session `session_blood.json`
- [ ] Verify `session_blood.json` has: file_edits (by path), terminal_commands, code_blocks, commit_refs, memory_files
- [ ] Update `manifest/session_ranked_index.json` composite scores with fresh drain data
- [ ] **Acceptance:** all 15 sessions drained; `session_blood.json` present with ≥500 file_edits extracted

### T+2.2 · Corpus — Embed All Sessions into sqlite-vec `[AUTO]`
> **BLOCKED-BY: T+2.1**
- [ ] Run `uv run scripts/corpus_embed.py --all` — embed all session turns into corpus.sqlite using Qwen3-Embedding-0.6B
- [ ] Verify `corpus.sqlite` has vector table with ≥5,000 embedded turns
- [ ] Run `bun run scripts/corpus-mcp-test.ts --semantic "Vulkan compute shader barrier"` — must return turn from a vulkan session
- [ ] **Acceptance:** `corpus_semantic_search` returns relevant results; sqlite-vec table has ≥5000 rows

### T+2.3 · Overnight Archaeology — Full Ore Extraction Pass `[AUTO]`
- [ ] Run the overnight archaeology daemon against pnk-live satellite
- [ ] Verify `dumpster-dive/` receives new ore files from pnk-live's 9,224-file corpus
- [ ] Run `bun run ci/checks/spread-freshness.ts` — satellites must be within 24h
- [ ] **Acceptance:** overnight report shows ≥ 50 new ore entries from pnk-live; freshness check passes

---

## GATE +3 · AGENT COURT MODERNIZATION (Intelligence Surface)
> **Grilling evidence:** [GRILLING.md §10 Agent Court](GRILLING.md#section-10--agent-court)

> **BLOCKED-BY: Gate 0 (T0.2 NEXT.md current), Gate -4 (CI clean)**  
> **Can-opener → Gate +4:** A clean, tested, well-routed agent court means every dispatch is reliable.

### T+3.1 · parity-auditor — Full Codex ↔ Claude Skill Sync Pass `[AUTO]`
- [ ] Run `bun run .agents/skills/parity-auditor/scripts/audit.ts` — emit `manifest/parity_audit.json`
- [ ] For each skill that exists in `.claude/skills/` but NOT in `.codex/skills/`: create the Codex-side mirror
- [ ] For each skill that has content drift between lanes: sync the drifted fields
- [ ] Priority: `tech-debt-triage`, `industrious-workiq`, `dumpster-upcycler` (these are Claude-only, not in Codex lane)
- [ ] **Acceptance:** parity-auditor exits 0; zero asymmetric skills

### T+3.2 · Agent Court Freshness — Top 10 Agents `[DECISION]`
- [ ] Read the `audit.agent.md` findings — last court audit date
- [ ] For each of the top 10 most-invoked agents (by corpus_tool_freq): verify their SKILL.md matches current repo state
- [ ] `[DECISION]` For any agent whose SKILL.md references a path or tool that no longer exists: update or quarantine
- [ ] Re-run `bun run .agents/skills/skill-polisher/scripts/polish.ts` — integrity sweep
- [ ] **Acceptance:** all top-10 agents pass skill-polisher integrity check; zero broken paths

### T+3.3 · Pentea Queue Chain — First Autonomous End-to-End Run `[DECISION]`
> **`scripts/pentea_autoloop.ts` written but 0 live runs**
- [ ] `[DECISION]` Choose a 3-task queue for the first live run (recommend: T-4.3 → T-4.4 → T-4.5 as they're mechanical fixes)
- [ ] Set `Pentea-Next:` trailer on a seed commit pointing to first task
- [ ] Run `bun run scripts/pentea_autoloop.ts` — verify agentStop hook fires and chains tasks
- [ ] Capture run to `manifest/pentea_run_001.json`
- [ ] **Acceptance:** ≥2 tasks complete without user intervention; `pentea_run_001.json` shows successful chain

---

## GATE +4 · GAME ENGINE — V2 ARCHITECTURE (Living World)
> **Grilling evidence:** [GRILLING.md §6 Game + Lore Layer](GRILLING.md#section-6--game--lore-layer) · [GRILLING.md §7 Vulkan Renderer](GRILLING.md#section-7--vulkan-renderer)

> **BLOCKED-BY: Gate +1 (Solana), Gate -2 (character schema clean)**  
> **Can-opener → Gate +5:** A v2 game engine means the lore and compute are unified.

### T+4.1 · Bevy ECS — Full Entity Population Pass `[AUTO]`
- [ ] Enumerate all characters in `game/lore/characters/` → count total JSON entities
- [ ] For each character JSON: ensure a corresponding `Entity` is spawned with the correct ECS bundle in `src/data/loader.rs`
- [ ] Verify `FactionRegistry` in `src/data/factions.rs` has all factions from `game/lore/factions/`
- [ ] Write a system `verify_all_entities_loaded()` that panics in debug if any lore entity is missing an ECS counterpart
- [ ] Run `cargo test -p chthonic-archive -- entity_load` — must pass
- [ ] **Acceptance:** entity loader test passes; all lore characters have ECS entities

### T+4.2 · TSRP State Machine — T1 Triumvirate Phase Logic `[DECISION]`
> **`tsrp_state` is present in FactionRegistry — is the state machine implemented?**
- [ ] Locate `tsrp_state` field in `src/data/types.rs` and `src/data/factions.rs`
- [ ] `[DECISION]` Assess: is TSRP (Triumvirate State Rotation Protocol) a full FSM, a placeholder, or a passive read?
- [ ] If placeholder: implement the minimal FSM: `Neutral → Active → Apex → Collapse → Neutral` with transition conditions
- [ ] Wire TSRP transitions to game events in `src/data/game_tree.rs` (e.g., a player choice at a T1 node triggers TSRP state change)
- [ ] **Acceptance:** TSRP transitions fire on game events; state is persisted to `.chthonic/game/active_run.json`

### T+4.3 · Vulkan Renderer V10 → V11: Dungeon cRPG Full Playthrough Loop `[AUTO]`
> **BLOCKED-BY: Gate +1 (T+1.2 Solana event feed)**
- [ ] G8 target: full dungeon loop — rooms unlock on task completion, cleared rooms persist
- [ ] Implement `RoomState::Cleared` trigger: when `status: "completed"` in todo_roulette.json, set room to cleared
- [ ] Add `--mode=dungeon-loop` that runs a continuous room-to-room session
- [ ] Wire dungeon traversal to emit entropy hashes (leading into Solana V10 integration)
- [ ] SID bump: V11
- [ ] **Acceptance:** dungeon-loop mode plays ≥3 rooms before session end; cleared rooms persist across restarts

---

## GATE +5 · WORLD-LEVEL SYNTHESIS (Maximum Coherence)
> **Grilling evidence:** [GRILLING.md §12 Health Summary](GRILLING.md#section-12--health-summary-at-grilling-date) — score at grilling: 1/10

> This gate has no deadline. It opens when all prior gates are closed.  
> **This is the final acceptance gate for the 10/10 exploration run.**

### T+5.1 · Full Architectural Map (Urania Cartograph Audit) `[DECISION]`
- [ ] Generate the three Urania maps: accurate (current state), aspirational (post-TODO), apocalyptic (worst drift)
- [ ] Verify the accurate map matches the territory — every described subsystem has a confirmed implementation
- [ ] File as `docs/architecture/ACCURATE_MAP.md`, `ASPIRATIONAL_MAP.md`
- [ ] **Acceptance:** accurate map has zero hallucinatory overclaims; aspirational map has ≥20 resolved TODO items

### T+5.2 · CI Gate 1 — World-Level Clean Run `[AUTO]`
> **BLOCKED-BY: All prior gates**
- [ ] Run `bun run ci/run.ts --full` — all 21 checks must exit 0 (no advisory, no degraded, no FAILED)
- [ ] Capture to `manifest/ci_gate1_world_level.json`
- [ ] If any check is non-zero: do not mark this task complete — loop back to the relevant gate
- [ ] **Acceptance:** CI exits 0 across all 21 checks; composite score ≥ 9.5/10; `ci_gate1_world_level.json` committed

### T+5.3 · Grilling Session Handoff Packet `[AUTO]`
- [ ] Run `uv run .agents/skills/git-snapshot/scripts/snapshot.py` → emit handoff packet
- [ ] Run `uv run .agents/skills/dumpster-upcycler/scripts/upcycle.py` → compact session into resume packet
- [ ] File resume packet to `Codex/mailbox/TODO_GRILLING_HANDOFF.md`
- [ ] Update pattern-nursery with any new patterns learned during this grilling
- [ ] **Acceptance:** handoff packet exists; pattern-nursery has ≥2 new entries; session blood updated

---

## ACCEPTANCE CRITERIA — THE 10/10 RUN

The exploration run is complete when:

1. **CI is clean**: `bun run ci/run.ts --full` exits 0 — all 21 checks passing (Gates -4 through -1)
2. **Compile is clean**: `cargo check --workspace` exits 0 on all 3 Rust roots; `tsc --noEmit` exits 0 (Gate -3)
3. **DSL coverage is above baseline**: `dsl-conformance` check exits 0 with coverage ≥ last-pass (Gate -5)
4. **Dumpster ore processed**: all HIGH-GRADE ore items have `status: "processed"` (Gate -2)
5. **Corpus G10 live**: `corpus_semantic_federation` returns cross-satellite results (Gate -1)
6. **At least one new isomorphism documented**: pattern-nursery has new Urca de Lima entry (Gate 0)
7. **Solana devnet entry recorded**: one entropy hash on-chain (Gate +1)
8. **Pentea queue chain ran once**: ≥2 autonomous tasks without intervention (Gate +3)
9. **All lore entities loaded**: ECS entity pass complete with verify test passing (Gate +4)
10. **Accurate architectural map committed**: zero hallucinatory overclaims (Gate +5)

**Score: [0/10] — Begin at Gate -5.**

---

## META-METHODOLOGY

**This file and [GRILLING.md](GRILLING.md) are a packet.** One without the other is incomplete.
- `TODO.md` = what to do and in what order
- `GRILLING.md` = why each task exists and what was found

The ordering in this file is not arbitrary. It follows the **Blocker-as-Can-Opener** pattern:

```
Gate -5 (governance clean)
  ↓ unlocks: downstream agents operate on verified schema
Gate -4 (CI enforcing)
  ↓ unlocks: every subsequent code change is gatekept
Gate -3 (toolchain coherent)
  ↓ unlocks: source changes compile predictably
Gate -2 (debt reduced)
  ↓ unlocks: architecture map matches territory
Gate -1 (MCP live)
  ↓ unlocks: every agent call has correct tool resolution
Gate 0 (synthesis)
  ↓ unlocks: isomorphisms visible, sprint board current
Gate +1 (frontier compute)
  ↓ unlocks: live on-chain entropy, real cryptographic stakes
Gate +2 (corpus deep)
  ↓ unlocks: every agent grounded in cross-session intelligence
Gate +3 (agent court clean)
  ↓ unlocks: dispatch reliable, Pentea autonomous
Gate +4 (game engine v2)
  ↓ unlocks: lore and compute unified
Gate +5 (world-level synthesis)
  ↓ THE ACCEPTANCE GATE
```

**The probe-manifest-CI membrane is the enforcement mechanism.**  
Every task that produces output MUST write to `manifest/` — not to terminal.  
Every check that validates output MUST read from `manifest/` — never scrape terminal.  
This is not optional. This is the pattern that makes automation compositional.

**The WPTG axiom governs all remediation decisions.**  
When in doubt: quarantine over delete. Transmute over discard.  
Evidence of hallucinatory ladderization is itself an artifact — file it, name it, learn from it.

---

*SID: TODO_MASTER_GRILL_V1 · Generated: 2026-06-05 · Score: 1/10 · Evidence: GRILLING.md · Rounds: 2 · Files: 40+ · Gates: 11 (−5 → +5)*
