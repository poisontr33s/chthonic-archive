# SSOT-ification Strategic Blueprint — Phase 0.1 → 1.0

> **Baseline Epoch:** 2026-03-19 · Commit `c3ce99e2` (Phase 0.1 landed)
> **SSOT Holder:** `.github/copilot-instructions.archive.md` — 9,208 lines · §0–§XVII + App A–E
> **SSOT Pointer:** `.github/copilot-instructions.md` — ~85 lines (75× compression routing surface)
> **Manifest:** `mas_mcp/logic/ssot_manifest.py` (`LOGIC_SSOT_MANIFEST_V1`) — 15-entry cascade register
> **Bridge:** `scripts/lib/ssot_paths.py` — thin re-export for scripts/ tree
> **Governance:** WPTG "Every file is gold" · No-Destroy · Upcycle-only

---

## 0. Current State (Phase 0.1 — Anno Baseline)

### What Was Done
- Created `scripts/lib/ssot_paths.py` bridge (re-exports `SSOT_HOLDER`, `SSOT_POINTER`, `SSOT_PROTO` + `resolve_ssot_paths()`)
- Expanded CASCADE_REGISTER from 4 → 15 entries covering all role/relation categories
- Wired **18 Python scripts** to resolve SSOT paths through the manifest chain
- Fixed 2 REPO_ROOT bugs + 1 CWD dependency bug
- Added `--quiet` to `uv run` in MCP config
- 16/16 binding tests passing

### What Remains (Full Inventory)

| Category | Wired (Phase 0.1) | Remaining | Total |
|----------|-------------------|-----------|-------|
| Python scripts (scripts/) | 18 | ~18 more | ~36 |
| Python (mas_mcp/) | 2 | ~5 more | ~7 |
| TypeScript (scripts/) | 0 | 6 | 6 |
| PowerShell (scripts/) | 0 | 6+ | 6+ |
| Config (.vscode/) | 1 (mcp.json noise) | 2 (mcp.json SSOT_PATH, settings.json) | 3 |
| Agent docs (root md) | 0 | 4 (AGENTS, AGENT_COMMON, CLAUDE, GEMINI) | 4 |
| .github/instructions/ | 0 | 20 files | 20 |
| .temple/protocols/ | 0 | 24 files | 24 |
| docs/ | 0 | 116 files | 116 |

### Critical Drift (Broken Now)
1. `scripts/ssot_loremaster.py` — references DELETED path `.temple/architecture/copilot-instructions.archive.md`
2. `scripts/debug_code_blocks.py` — hardcodes absolute path `C:\Users\erdno\...` (wrong username)
3. Three `.ps1` scripts resolve SSOT via `$PSScriptRoot\..` → repo root (missing `.github/` prefix)
4. `.ankhrc` (bidirectional SSOT hub defined in methodology) — never created

---

## 1. Architectural Principle: The Cascade Spine

Everything in this codebase either **IS** the SSOT or **SERVES** the SSOT. There is no third category.

```
                    ┌─────────────────────────────────┐
                    │   HOLDER (archive.md · 9208 ln)  │
                    │   The FROZEN MONOLITHIC LABYRINTHE│
                    │   §0–§XVII + Appendices A–E       │
                    └──────────────┬──────────────────┘
                                   │ authoritative
                    ┌──────────────┴──────────────────┐
                    │                                   │
            ┌───────▼───────┐               ┌──────────▼──────────┐
            │  POINTER (.md) │               │  PROTO (copy.md)     │
            │  85-ln router  │               │  historizing fork    │
            │  summarizing   │               │  pre-freeze snapshot │
            └───────┬───────┘               └─────────────────────┘
                    │
        ┌───────────┼───────────┬───────────────┐
        │           │           │               │
   ┌────▼────┐ ┌───▼────┐ ┌───▼────┐     ┌────▼─────┐
   │MANIFEST │ │BINDING │ │BRIDGE  │     │EXTRACTOR │
   │(ssot_   │ │(ssot_  │ │(ssot_  │     │(ssot_    │
   │manifest)│ │binding)│ │paths)  │     │extractor)│
   └────┬────┘ └───┬────┘ └───┬────┘     └────┬─────┘
        │           │          │               │
        ▼           ▼          ▼               ▼
   ┌─────────────────────────────────────────────────┐
   │            CONSUMER LAYER                        │
   │  170 Python · 92 PowerShell · 30 TypeScript      │
   │  116 docs · 20 instructions · 24 protocols       │
   └─────────────────────────────────────────────────┘
```

### The Cascade Contract (immutable)
1. **Filenames live in ONE place:** `ssot_manifest.py` lines 41–45
2. **If a filename changes, the manifest changes FIRST** — everything else resolves through it
3. **No consumer ever hardcodes a SSOT path as a literal string** — they import from the cascade chain
4. **Role taxonomy is closed:** holder, pointer, projection, validator, journal, artifact, bridge
5. **Relation taxonomy is closed:** authoritative, summarizing, indexing, validating, projecting, caching, historizing

---

## 2. Phase Hierarchy: 0.1 → 1.0

### Phase 0.2 — Complete the Python Cascade (P0/P1 priority)
**Goal:** Zero hardcoded SSOT paths in any `.py` file.

#### Stage 01: Fix Critical Drift
| Target | Issue | Fix |
|--------|-------|-----|
| `scripts/ssot_loremaster.py` L45 | References deleted `.temple/architecture/...` path | Already partially wired in 0.1 — verify the secondary reference is gone |
| `scripts/debug_code_blocks.py` L29 | Absolute path `C:\Users\erdno\...` | Replace with `resolve_ssot_paths()` |
| `get_hash.py` (root) | Root-level utility with hardcoded path | Wire to bridge OR relocate to `scripts/` |

#### Stage 02: Wire Remaining scripts/*.py (~15 files)
| Script | Current Hardcoded Path |
|--------|----------------------|
| `build_epistemograph_v1.1.py` | `.github/copilot-instructions.md` (×4) |
| `build_epistemograph.py` | `.github/copilot-instructions.md` (×2) |
| `governance_test.py` | `copilot-instructions.md` |
| `path_naming_audit.py` | Both filenames |
| `scan_delete_language.py` | `.github/copilot-instructions.md` |
| `ssot_hash.py` | `.github/copilot-instructions.md` (default arg) |
| `ssot_immunity.py` | `.github/copilot-instructions.md` |
| `test_narrative_scan.py` | `.github/copilot-instructions.md` |
| `unified_topology.py` | `.github/copilot-instructions.md` |
| `quick_validation.py` | `copilot-instructions.md` |

#### Stage 03: Wire Remaining mas_mcp/**/*.py (~5 files)
| Script | Current Hardcoded Path |
|--------|----------------------|
| `mas_mcp/scripts/run_cycle.py` | `.github/copilot-instructions.md` |
| `mas_mcp/scripts/probe_gpu_compatibility.py` | `.github/copilot-instructions.md` (×3) |
| `mas_mcp/scripts/milf_activator.py` | `.github/copilot-instructions.md` |
| `mas_mcp/genesis_scheduler.py` | `.github/copilot-instructions.md` |
| `mas_mcp/abbreviation_system/parser.py` | `copilot-instructions.md` |

#### Stage 04: Tests
- Expand `test_cascade_register_all_relpaths_exist` to verify new entries
- Add integration test: import ssot_paths from every wired script module → assert non-None

**Exit Gate:** `grep -r "copilot-instructions" scripts/*.py mas_mcp/**/*.py` returns ZERO hits outside of comments and the manifest itself.

---

### Phase 0.3 — TypeScript Bridge
**Goal:** Create `scripts/lib/ssot-paths.ts` equivalent, wire all 6 TS consumers.

#### Stage 01: Create Bridge
```typescript
// scripts/lib/ssot-paths.ts
// Thin bridge — reads from a shared config, not hardcoded
export const SSOT_HOLDER = ".github/copilot-instructions.archive.md";
export const SSOT_POINTER = ".github/copilot-instructions.md";
export const SSOT_PROTO = ".github/copilot-instructions-copy.md";
```

**Design choice:** TS bridge can't import from Python manifest directly. Two options:
- **A) Static re-declaration** (simplest — duplicate but centralized in one TS file)
- **B) Generated from manifest** (a build step that reads ssot_manifest.py → emits ssot-paths.ts)
- **Recommendation:** Start with (A), evolve to (B) if the filename set grows beyond 3.

#### Stage 02: Wire TS Consumers
| File | Current Hardcoded |
|------|-------------------|
| `scripts/overnight_daemon.ts` | `.github/copilot-instructions.md` |
| `scripts/mcp-chthonic-server.ts` | `.github/copilot-instructions.md` |
| `scripts/mcp-asc-injector.ts` | `.github/copilot-instructions.md` |
| `scripts/cross-critique.ts` | `.github/copilot-instructions.archive.md` |
| `extensions/chthonic-archive/src/extension.ts` | `.github/copilot-instructions.md` |
| `extensions/.../ankhReferenceView.ts` | `copilot-instructions.archive.md` |

**Exit Gate:** `grep -r "copilot-instructions" scripts/*.ts extensions/**/*.ts` returns ZERO hits outside the bridge and comments.

---

### Phase 0.4 — PowerShell Bridge
**Goal:** Create `scripts/lib/ssot-paths.ps1`, wire all 6+ PS1 consumers.

#### Stage 01: Create Bridge
```powershell
# scripts/lib/ssot-paths.ps1
$Script:SSOT_HOLDER = ".github/copilot-instructions.archive.md"
$Script:SSOT_POINTER = ".github/copilot-instructions.md"
$Script:SSOT_PROTO = ".github/copilot-instructions-copy.md"
```

#### Stage 02: Wire PS1 Consumers
| File | Issue |
|------|-------|
| `scripts/ssot_registry_query_v2.ps1` | Wrong resolve path (`$PSScriptRoot\..`) |
| `scripts/ssot_outline_extractor.ps1` | Wrong resolve path |
| `scripts/ssot_acronym_audit.ps1` | Wrong resolve path |
| `scripts/novia_cadaveris_embalmer.ps1` | Hardcoded literal |
| `scripts/copilot_clean.ps1` | Comment reference |
| `.github/tools/indexing_commit.ps1` | Literal string |

**Exit Gate:** `Select-String "copilot-instructions" scripts/*.ps1` returns ZERO hits outside bridge and comments.

---

### Phase 0.5 — Config Cascade
**Goal:** All IDE/MCP config SSOT references traceable to the cascade.

| Config File | Current State | Target |
|-------------|---------------|--------|
| `.vscode/mcp.json` `SSOT_PATH` env var | Hardcoded literal | Source from bridge or document as config-boundary exception |
| `.vscode/settings.json` | 2 SSOT path refs (validation ignore + chat location) | Document as IDE-boundary — VS Code requires literals here |
| `.mcp.json` (root) | May have references | Audit and document |

**Design decision:** IDE config files (settings.json, mcp.json) are **config-boundary endpoints** — they cannot import from code. The cascade contract is: *the manifest is the first place to update, and config files are documented as downstream mirrors that must be updated manually*. The cascade register should include a `config_boundary` relation type for these.

---

### Phase 0.6 — Documentation Cascade + .ankhrc Genesis
**Goal:** The SSOT metadata/governance docs reference the cascade, not hardcoded paths.

#### Stage 01: Create `.ankhrc`
The SSOTIFICATION_METHODOLOGY.md defines `.ankhrc` as the "bidirectional SSOT hub" with `[paths]`, `[ssot_ified]`, `[state_files]` etc. — but **it was never created**. This is Phase 0.6's primary deliverable.

`.ankhrc` should be a TOML file that:
- Maps symbolic names to SSOT-relative paths (pulled from the manifest)
- Tracks migration status of each file category
- Provides the navigation index that `pathstofiles.md` currently serves manually

#### Stage 02: Update Agent Protocol Docs
- `AGENTS.md` — update SSOT reference links to use explicit section anchors
- `AGENT_COMMON.md` — same
- `CLAUDE.md` / `GEMINI.md` — verify SSOT pointers are current

#### Stage 03: Governance Docs
- `docs/SSOTIFICATION_METHODOLOGY.md` — update to reflect the cascade register architecture (Phases 0.1–0.5)
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — verify protected artifacts table includes the cascade register files
- `HARVEST_REGISTRY.md` — refresh with all unharvested work since 2026-01-29

---

### Phase 0.7 — Root Hygiene (WPTG-Compliant)
**Goal:** Upcycle or properly archive ~22 stale root-level artifacts.

**Per WPTG:** No file is deleted. Each is triaged into:

| Tier | Action | Candidates |
|------|--------|------------|
| Direct Gold | Keep in place, just `.gitignore` | `cargo_test.json`, `meta_cli_test.json`, `validate_test.json` (test outputs) |
| Structural Gold | Relocate to `dumpster-dive/intake/` | `broken-refs.json`, `scan_audit_tmp.json`, `stage2_1_*.json`, `server_debug.json` |
| Conceptual Gold | Relocate to `dumpster-dive/archive/` | `challenge_task_session_context_*.md`, `codexfailsessionDUMP.md` |
| Relocate to scripts/ | Move, update imports | `get_hash.py`, `purify_ssot.py`, `strip_ssot*.py`, `claude_test.py` |
| Device artifacts | `.gitignore` only | `$null`, `NUL`, `NUL.kcp_template.*`, `mkmf.log`, `_fidelity.txt` |

---

### Phase 0.8 — Cascade Testing Expansion
**Goal:** Comprehensive test coverage for the full cascade chain.

| Test | Scope | Status |
|------|-------|--------|
| `test_cascade_register_completeness` | All identities exist | ✅ Phase 0.1 |
| `test_cascade_register_all_relpaths_exist` | All code files resolve | ✅ Phase 0.1 |
| `test_ssot_paths_bridge_resolves_through_manifest` | Bridge re-exports | ✅ Phase 0.1 |
| `test_no_hardcoded_ssot_paths_in_python` | Grep validation | ❌ Phase 0.8 |
| `test_no_hardcoded_ssot_paths_in_typescript` | Grep validation | ❌ Phase 0.8 |
| `test_no_hardcoded_ssot_paths_in_powershell` | Grep validation | ❌ Phase 0.8 |
| `test_config_boundary_ssot_paths_documented` | IDE config audit | ❌ Phase 0.8 |
| `test_ankhrc_resolves_all_paths` | .ankhrc validity | ❌ Phase 0.8 |

---

### Phase 0.9 — Cascade Register Expansion
**Goal:** Every SSOT-adjacent file in the codebase has a cascade register entry.

Current register: 15 entries. Target additions:

| Identity | Role | Relation | Relpath |
|----------|------|----------|---------|
| `ssot_hash` | artifact | validating | `scripts/ssot_hash.py` |
| `ssot_immunity` | artifact | validating | `scripts/ssot_immunity.py` |
| `ts_bridge` | bridge | indexing | `scripts/lib/ssot-paths.ts` |
| `ps1_bridge` | bridge | indexing | `scripts/lib/ssot-paths.ps1` |
| `ankhrc` | bridge | indexing | `.ankhrc` |
| `pathstofiles` | bridge | indexing | `pathstofiles.md` |
| `pointer_instructions` | pointer | summarizing | `.github/copilot-instructions.md` (already exists as `pointer`) |
| `ssotification_methodology` | projection | projecting | `docs/SSOTIFICATION_METHODOLOGY.md` |
| `this_blueprint` | projection | projecting | `docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md` |
| `wptg` | validator | validating | `WET_PAPER_TO_GOLD_METHODOLOGY.md` |
| `pre_commit_guardian` | validator | validating | `scripts/hooks/pre-commit-guardian.ps1` |

---

### Phase 1.0 — Bidirectional Supplementation Lock
**Goal:** The SSOT is not just referenced BY everything — everything is referenced IN the SSOT.

This is the turning point where content flows both directions:
- **Outward:** The SSOT (holder) declares the canonical entities, axioms, protocols → cascade consumers resolve and apply
- **Inward:** New code, new protocols, new entities get **registered back** into the SSOT's section structure

#### The Bidirectional Contract
```
SSOT Holder (archive.md)
  §XIV Development Conventions
    → New conventions discovered by scripts → proposed back as §XIV amendments
  §XV DCRP
    → Cross-reference results → update DCRP section
  App D SEM Validation
    → Validation results → update SEM appendix
  
Consumer Layer
  → Reads from SSOT (already works via cascade)
  → Proposes amendments (NEW — requires amendment protocol)
```

#### Amendment Protocol (draft)
1. **Discovery:** Script/agent identifies content that should be canonical
2. **Proposal:** Creates a structured proposal in `.mas_mcp/amendments/` (JSONL)
3. **Review:** User reviews proposals during session
4. **Integration:** Approved amendments are written into the holder by the user
5. **Cascade:** `ssot_hash` detects drift → `hash_journal` records event → binding tests pass

---

## 3. The Polyglot Supplementation Matrix

Every file type in the codebase has a role in supplementing the SSOT. This matrix makes that explicit:

| File Kind | Count | SSOT Relationship | Cascade Phase |
|-----------|-------|-------------------|---------------|
| **Rust** (src/, tools/) | ~15 | Game engine — implements §X entity manifestation | Future (1.x) |
| **Python** (scripts/) | ~170 | CLIs, validators, extractors — implements §XIV-XV | 0.2 (completing) |
| **Python** (mas_mcp/) | ~40 | MCP server — implements operational governance | 0.2 (completing) |
| **TypeScript** (scripts/) | ~30 | MCP servers, overnight daemon — operational tools | 0.3 |
| **PowerShell** (scripts/) | ~92 | IDE integration, SSOT queries — operational tools | 0.4 |
| **Markdown** (docs/) | ~116 | Documentation projections of SSOT content | 0.6 |
| **Markdown** (.github/instructions/) | 20 | Copilot instruction fragments (SSOT decomposition) | 0.6 |
| **Markdown** (.temple/protocols/) | 24 | Agent behavioral protocols (SSOT enforcement) | 0.6 |
| **Markdown** (game/) | ~20 | cRPG lore — implements §0-§X entity canon | Future (1.x) |
| **JSON/TOML** (config) | ~15 | Build/IDE/MCP config | 0.5 |
| **GLSL** (shaders/) | ~5 | Visual rendering — implements §0.6 chromatic systems | Future (1.x) |

### The Supplementation Principle
> *Nothing can be made without being a bidirectionally supplemental variant of the SSOT architecture.*
> *Every file either reads FROM the SSOT, writes TOWARD the SSOT, or does both.*
> *Files that do neither are drift — candidates for wiring (upcycle) or archival (dumpster-dive).*

---

## 4. Priority Queue (Execution Order)

| Priority | Phase | Scope | Effort | Dependencies |
|----------|-------|-------|--------|-------------|
| **P0** | 0.2 Stage 01 | Fix 3 critical broken references | Small | None |
| **P1** | 0.2 Stage 02-03 | Wire remaining ~20 Python scripts | Medium | Stage 01 |
| **P1** | 0.2 Stage 04 | Tests for Python cascade completion | Small | Stage 02-03 |
| **P2** | 0.3 | TypeScript bridge + wire 6 files | Medium | None (parallel with 0.2) |
| **P2** | 0.4 | PowerShell bridge + wire 6 files | Medium | None (parallel with 0.3) |
| **P3** | 0.5 | Config cascade documentation | Small | 0.3 + 0.4 |
| **P3** | 0.6 | .ankhrc genesis + doc cascade | Medium | 0.5 |
| **P4** | 0.7 | Root hygiene (WPTG upcycle) | Medium | None (parallel) |
| **P4** | 0.8 | Full cascade test suite | Medium | 0.2-0.6 |
| **P5** | 0.9 | Register expansion (15 → 26+) | Small | 0.8 |
| **P5** | 1.0 | Bidirectional amendment protocol | Large | All prior phases |

---

## 5. Success Metrics (Phase 1.0 Exit Gate)

| Metric | Phase 0.1 (now) | Target (1.0) |
|--------|----------------|--------------|
| Cascade register entries | 15 | 26+ |
| Python scripts wired | 18 | ALL (~36+) |
| TypeScript files wired | 0 | ALL (~6) |
| PowerShell files wired | 0 | ALL (~6) |
| Hardcoded SSOT paths (any language) | ~40 | 0 (outside config boundary) |
| Test coverage (binding suite) | 16 tests | 24+ tests |
| `.ankhrc` exists | No | Yes |
| HARVEST_REGISTRY current | Stale (2 months) | Current |
| Root stale artifacts | ~22 | 0 (upcycled/archived) |
| Bidirectional amendment protocol | None | Draft operational |

---

## 6. Non-Goals (Explicitly Out of Scope for 0.1→1.0)

- **Rewriting the SSOT holder content** — It's frozen. Content amends come through the amendment protocol in 1.0.
- **Refactoring the Rust game engine** — The `src/` tree is a separate development axis.
- **Creating new agent archetypes** — Agent triad (Claude/Codex/Gemini) is stable.
- **Migrating to a database backend** — Flat-file SSOT is deliberate. The epistemograph is a separate concern.
- **Compression/minification of the holder** — The 9,208-line monolith is canonical as-is.

---

## Appendix: File Reference

| Artifact | Path | Phase Created |
|----------|------|---------------|
| SSOT Manifest | [mas_mcp/logic/ssot_manifest.py](../mas_mcp/logic/ssot_manifest.py) | Pre-0.1 (V5) |
| SSOT Binding | [mas_mcp/logic/ssot_binding.py](../mas_mcp/logic/ssot_binding.py) | Pre-0.1 (V5) |
| Python Bridge | [scripts/lib/ssot_paths.py](../scripts/lib/ssot_paths.py) | 0.1 |
| Binding Tests | [mas_mcp/tests/test_ssot_binding.py](../mas_mcp/tests/test_ssot_binding.py) | Pre-0.1, expanded 0.1 |
| WPTG Methodology | [WET_PAPER_TO_GOLD_METHODOLOGY.md](../WET_PAPER_TO_GOLD_METHODOLOGY.md) | Pre-0.1 |
| SSOTIFICATION Methodology | [docs/SSOTIFICATION_METHODOLOGY.md](docs/SSOTIFICATION_METHODOLOGY.md) | Pre-0.1 |
| This Blueprint | [docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md](SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md) | 0.1 (Anno Baseline) |
| Codekiller Anti-Pattern | [anti-patterns/codekiller.md](../anti-patterns/codekiller.md) | Pre-0.1 |
| Harvest Registry | [HARVEST_REGISTRY.md](../HARVEST_REGISTRY.md) | Pre-0.1 |
