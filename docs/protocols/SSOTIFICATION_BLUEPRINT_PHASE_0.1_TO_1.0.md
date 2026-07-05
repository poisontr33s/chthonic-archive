# SSOT-ification Strategic Blueprint — Phase 0.1 → 1.0

> **Baseline Epoch:** 2026-03-19 · Commit `c3ce99e2` (Phase 0.1 landed)
> **Phase 0.2 Epoch:** 2026-03-19 · Commit `fa4a6120` (Python cascade complete)
> **Last Updated:** 2026-03-27 · Phases 0.3–0.9.1 complete. Phase 0.9.2 active. Phases 0.9.3/0.9.4 ratified (12 amendments, 178 files consumed). Phase 1.0 next.
> **SSOT Holder:** `.github/copilot-instructions.archive.md` — 9,208 lines · §0–§XVII + App A–E
> **SSOT Pointer:** `.github/copilot-instructions.md` — ~85 lines (75× compression routing surface)
> **Manifest:** `mas_mcp/logic/ssot_manifest.py` (`LOGIC_SSOT_MANIFEST_V1`) — 28-entry cascade register
> **Bridge:** `scripts/lib/ssot_paths.py` — thin re-export for scripts/ tree
> **Governance:** WPTG "Every file is gold" · No-Destroy · Upcycle-only
>
> **Cross-references:**
> - Structural audit: [`claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md`](../../claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md) — Phase 4 maps back here; Phase 1.5 → Forge Dev Plan
> - Forge pipeline plan: [`claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md`](../../claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md) — L0–L6 ✅ complete (2026-03-25), ~85% compliance
> - Session context: [`claude-codex-gemini/triadic-session-context/`](../../claude-codex-gemini/triadic-session-context/) — entropy survey, Zone_1 provenance, nascent ANKH archaeology, Redux source nucleus (`COMPREHENSIVE IMPROVEMENT PLAN PROPOSAL.md`)

---

## 0. Current State (Phase 0.2 — Python Cascade Complete)

### What Was Done (Phase 0.1 · `c3ce99e2`)
- Created `scripts/lib/ssot_paths.py` bridge (re-exports `SSOT_HOLDER`, `SSOT_POINTER`, `SSOT_PROTO` + `resolve_ssot_paths()`)
- Expanded CASCADE_REGISTER from 4 → 15 entries covering all role/relation categories
- Wired **16 Python consumer scripts** + 4 infra files (20 total) through the manifest chain
  - **14 scripts/**: ankh_theme_reference, asc_entity_generator, background_services, decorator_cross_ref_{enhanced,maximum,production}, generate_readable_ssot, run_cycle, run_narrative_scan, scan_redundancy, sfa_cross_reference, ssot_loremaster, ssot_structural_extractor, synthesis_cross_reference
  - **2 mas_mcp/**: abbreviation_system/cli, ssot_extractor
  - **4 infra**: ssot_manifest (source of truth), ssot_paths (bridge), test_ssot_binding (tests), lib/__init__
- Fixed 2 REPO_ROOT bugs + 1 CWD dependency bug
- Added `--quiet` to `uv run` in MCP config
- 16/16 binding tests passing

### What Was Done (Phase 0.2 · `fa4a6120`)
Wired **13 additional Python scripts** through the manifest→bridge cascade (29 consumer scripts total):

**Critical drift fixes (3):**
- `scripts/ssot_loremaster.py` — dead `.temple/architecture/copilot-instructions.archive.md` → `_SSOT.proto`
- `scripts/debug_code_blocks.py` — absolute `C:\Users\eldno\...` path → `resolve_ssot_paths()` bridge
- `scripts/ssot_immunity.py` — `PROJECT_ROOT` bug (`.parent` → `.parent.parent`) + `SSOT_FILES[0]` → `SSOT_POINTER`

**Direct filesystem wiring (4):**
- `scripts/ssot_hash.py` — argparse default → lazy bridge resolve at runtime
- `scripts/test_narrative_scan.py` — `SSOT_PATH` → `resolve_ssot_paths()`
- `mas_mcp/scripts/run_cycle.py` — `SSOT_PATH` → `SSOT_POINTER_RELPATH` from manifest
- `mas_mcp/genesis_scheduler.py` — `mpw_path` default → manifest import

**Structural references (5):**
- `scripts/build_epistemograph.py` — `GOVERNANCE_FILES` set + SQL LIKE pattern
- `scripts/build_epistemograph_v1.1.py` — `GOVERNANCE_FILES` list + `ssot_primary` + 2× SQL LIKE patterns
- `scripts/scan_delete_language.py` — `AGENT_READABLE_GLOBS[0]` → `SSOT_POINTER`
- `scripts/governance_test.py` — absolute sqlite path fix + SQL LIKE → f-string with bridge
- `scripts/quick_validation.py` — SQL LIKE → f-string with `Path(SSOT_POINTER).name`
- `scripts/unified_topology.py` — `infer_tier` `p.name` bug fix (was comparing `p.name` against `.github/copilot-instructions.md`) + bridge wiring

### What Remains (Full Inventory)

> ⚠️ **Audit note:** The Phase 0.2 grep used PowerShell's `mas_mcp/**/*.py` glob which only
> recurses one level. Directories at depth ≥3 (`scripts/abbrev/`, `scripts/ssot_abbrev/`,
> `lib/asc/`) were missed. The corrected audit below uses `grep -rn --include="*.py"`.

| Category | Wired (0.1+0.2) | Remaining | Notes |
|----------|-----------------|-----------|-------|
| Python (scripts/) | 25 | 27 lines / 14 files — **0 functional** | Docstrings, content-match, metadata literals |
| Python (mas_mcp/) | 4 | 26 lines / 15 files — **6/6 wired** | ✅ **Phase 0.2.1 COMPLETE** |
| TypeScript (scripts/) | 0 | ~6 | **Phase 0.3** |
| PowerShell (scripts/) | 0 | 6+ | **Phase 0.4** |
| Config (.vscode/) | 1 (mcp.json noise) | 2 (mcp.json SSOT_PATH, settings.json) | **Phase 0.5** |
| Agent docs (root md) | 0 | 4 (AGENTS, AGENT_COMMON, CLAUDE, GEMINI) | **Phase 0.6** |
| .github/instructions/ | 0 | 20 files | **Phase 0.6** |
| .temple/protocols/ | 0 | 24 files | **Phase 0.6** |
| docs/ | 0 | 116 files | **Phase 0.6** |

**Remaining Python detail (53 lines across 29 files):**

#### scripts/ — 27 lines / 14 files (0 functional path construction)
| File | Line(s) | Count | Kind | Risk |
|------|---------|-------|------|------|
| `ankh_theme_reference.py` | 10, 18, 33 | 3 | Comment + docstring | None |
| `asc_entity_generator.py` | 65 | 1 | Docstring | None |
| `background_services.py` | 195 | 1 | Content-match (`in str(path)`) | Low |
| `check_python_policy.py` | 45 | 1 | Literal in `PROTO_GLOBS` list | **Medium** |
| `decorator_cross_ref_enhanced.py` | 429 | 1 | Content-match (`in path.name`) | Low |
| `decorator_cross_ref_maximum.py` | 447 | 1 | Content-match (`in path.name`) | Low |
| `decorator_cross_ref_production.py` | 866 | 1 | Content-match (`in path.name`) | Low |
| `generate_readable_ssot.py` | 130 | 1 | Derivative output path (`.readable.md`) | **Medium** — derives from SSOT name |
| `path_naming_audit.py` | 123–124 | 2 | Audit exception set (bare filenames) | **Medium** |
| `regenerate_triptych.py` | 288 | 1 | Content-match (`in p`) | Low |
| `ssot_hash.py` | 57, 120 | 2 | Docstring + usage example | None |
| `ssot_loremaster.py` | 90, 130–254 | 10 | 1 deliverable desc + 9× `source=` metadata | **Medium** — stale on rename |
| `ssot_structural_extractor.py` | 16 | 1 | Docstring | None |
| `synthesis_cross_reference.py` | 19 | 1 | Docstring | None |

#### mas_mcp/ — 26 lines / 15 files (5 functional + 1 dead ref)
| File | Line(s) | Count | Kind | Risk |
|------|---------|-------|------|------|
| `abbreviation_system/__init__.py` | 8 | 1 | Docstring | None |
| `abbreviation_system/parser.py` | 25, 37 | 2 | Docstring + example | None |
| ~~`lib/asc/cli.py`~~ | ~~41~~ | ~~1~~ | ~~DEAD REF~~ → wired through `SSOT_HOLDER_RELPATH` | ✅ **Fixed (2026-03-25)** |
| `lib/asc/extractor.py` | 38 | 1 | Docstring | None |
| `lib/asc/models.py` | 45 | 1 | Docstring | None |
| `logic/tools.py` | 70 | 1 | Content-match skip filter | Low |
| `milf_genesis_v2.py` | 174, 1335 | 2 | 1 comment + 1 **FUNCTIONAL** `mpw_path` default | **High** |
| `scripts/abbrev/cli.py` | 48, 151 | 2 | 1 **FUNCTIONAL** `SSOT_PATH` constant + 1 backup name | **High** |
| `scripts/abbrev/generator.py` | 56 | 1 | Docstring | None |
| `scripts/milf_activator.py` | 17, 232 | 2 | Docstring + cosmetic print | None |
| `scripts/probe_gpu_compatibility.py` | 18, 397, 416 | 3 | Docstring + `ssot_ref=` kwarg + print | **Medium** |
| `scripts/run_cycle.py` | 28 | 1 | Docstring | None |
| `scripts/ssot_abbrev/cli.py` | 42, 47, 48, 178 | 4 | 3 **FUNCTIONAL** (1 has wrong absolute `eldno` path!) + 1 backup | **Critical** |
| `scripts/ssot_abbrev/generator.py` | 37, 160 | 2 | Source metadata strings | **Medium** |
| `ssot_extractor.py` | 16, 132 | 2 | Docstring | None |
1. ~~`scripts/ssot_loremaster.py` — references DELETED path `.temple/architecture/copilot-instructions.archive.md`~~ ✅ Fixed (Phase 0.2)
2. ~~`scripts/debug_code_blocks.py` — hardcodes absolute path `C:\Users\eldno\...` (wrong username)~~ ✅ Fixed (Phase 0.2)
3. Three `.ps1` scripts resolve SSOT via `$PSScriptRoot\..` → repo root (missing `.github/` prefix) — **Phase 0.4**
4. `.ankhrc` (bidirectional SSOT hub defined in methodology) — never created — **Phase 0.6**
5. `.temple/methodology/AGENT_COMMON.md` replaced with redirect pointer to root `AGENT_COMMON.md` — **2026-03-25** (user elaborated with Root Documentation Index + Triadic Session Context)
6. `docs/PWSH_RULES.md` diverged from root: root=v1.1 (2026-01-29), docs/=v1.2 (2026-02-01). Reconciliation needed, not deletion. — **Phase 0 pending** (audit finding I)

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

### Phase 0.2 — Complete the Python Cascade (P0/P1 priority) ✅ `fa4a6120` (scripts/) · ⚠️ mas_mcp/ incomplete
**Goal:** Zero hardcoded SSOT paths in any `.py` file.

#### Stage 01: Fix Critical Drift ✅
| Target | Issue | Fix | Status |
|--------|-------|-----|--------|
| `scripts/ssot_loremaster.py` L45 | References deleted `.temple/architecture/...` path | Dead ref → `_SSOT.proto` | ✅ |
| `scripts/debug_code_blocks.py` L29 | Absolute path `C:\Users\eldno\...` | Replaced with `resolve_ssot_paths()` | ✅ |
| `get_hash.py` (root) | Root-level utility with hardcoded path | Wired on disk but **gitignored** — not in any commit. See Phase 0.7 "Relocate to scripts/" | ⚠️ |

#### Stage 02: Wire Remaining scripts/*.py ✅
| Script | Current Hardcoded Path | Status |
|--------|----------------------|--------|
| `build_epistemograph_v1.1.py` | `.github/copilot-instructions.md` (×4) | ✅ GOVERNANCE_FILES + ssot_primary + 2× SQL LIKE |
| `build_epistemograph.py` | `.github/copilot-instructions.md` (×2) | ✅ GOVERNANCE_FILES set + SQL LIKE |
| `governance_test.py` | `copilot-instructions.md` | ✅ sqlite path + SQL LIKE + print |
| `path_naming_audit.py` | Both filenames | ⚠️ Cosmetic — bare filenames in audit-exception set, not path construction |
| `scan_delete_language.py` | `.github/copilot-instructions.md` | ✅ AGENT_READABLE_GLOBS → SSOT_POINTER |
| `ssot_hash.py` | `.github/copilot-instructions.md` (default arg) | ✅ argparse default → lazy resolve |
| `ssot_immunity.py` | `.github/copilot-instructions.md` | ✅ PROJECT_ROOT bug fix + SSOT_FILES wiring |
| `test_narrative_scan.py` | `.github/copilot-instructions.md` | ✅ SSOT_PATH → resolve_ssot_paths() |
| `unified_topology.py` | `.github/copilot-instructions.md` | ✅ infer_tier p.name bug fix + bridge |
| `quick_validation.py` | `copilot-instructions.md` | ✅ SQL LIKE → f-string with bridge |

#### Stage 03: Wire Remaining mas_mcp/**/*.py ✅ (functional) / ⚠️ (cosmetic)
| Script | Current Hardcoded Path | Status |
|--------|----------------------|--------|
| `mas_mcp/scripts/run_cycle.py` | `.github/copilot-instructions.md` | ✅ → SSOT_POINTER_RELPATH |
| `mas_mcp/scripts/probe_gpu_compatibility.py` | `.github/copilot-instructions.md` (×3) | ⚠️ Cosmetic — 1 docstring + 1 `ssot_ref=` kwarg + 1 print |
| `mas_mcp/scripts/milf_activator.py` | `.github/copilot-instructions.md` | ⚠️ Cosmetic — 1 docstring + 1 print |
| `mas_mcp/genesis_scheduler.py` | `.github/copilot-instructions.md` | ✅ mpw_path default → manifest import |
| `mas_mcp/abbreviation_system/parser.py` | `copilot-instructions.md` | ⚠️ Cosmetic — docstring + example (caller-provided path) |

#### Stage 04: Tests ✅
- 16/16 SSOT binding tests passing (unchanged — Phase 0.2 changed no test contracts)
- All bridge imports validated at runtime (`SSOT_POINTER` resolves to `.github/copilot-instructions.md`)
- `Path(SSOT_POINTER).name` correctly yields `copilot-instructions.md` for SQL LIKE derivation
- Pre-existing broken tests (`test_gpu_integration.py`, `test_logic_qualia.py`) are unrelated import errors

**Exit Gate:** `grep -rn --include="*.py" "copilot-instructions" scripts/ mas_mcp/` (excluding infra + imports):
- **scripts/**: ✅ ZERO functional path-construction hits. 27 non-functional references (docstrings, content-match, metadata).
- **mas_mcp/**: ✅ **All 5 functional path constructions + 1 dead ref WIRED** (2026-03-25). All now import from `mas_mcp.logic.ssot_manifest`. Wrong-username absolute path removed.
- 53 total non-import lines across 29 files (21 non-functional remainder acceptable per cascade contract §3).

---

### Phase 0.2.1 — Complete mas_mcp/ Deep Audit ✅ COMPLETE (2026-03-25)
**Goal:** Wire the 5 functional path constructions + 1 dead ref that were missed by the Phase 0.2 shallow glob.

**Root cause:** PowerShell glob `mas_mcp/**/*.py` only recursed one level. Directories at depth ≥3 were invisible.

| File | Line | Current | Fix | Status |
|------|------|---------|-----|--------|
| `milf_genesis_v2.py:1335` | `mpw_path = Path(...) / ".github" / "copilot-instructions.md"` | Hardcoded default in `__main__` | → `SSOT_POINTER_RELPATH` import | ✅ Done |
| `scripts/abbrev/cli.py:48` | `SSOT_PATH = PROJECT_ROOT / ".github" / "copilot-instructions.md"` | Module-level constant | → `SSOT_POINTER_RELPATH` import | ✅ Done |
| `scripts/ssot_abbrev/cli.py:42` | `ssot_path = project_root / ".github" / "copilot-instructions.md"` | In `get_ssot_path()` | → `SSOT_POINTER_RELPATH` import | ✅ Done |
| `scripts/ssot_abbrev/cli.py:47` | `Path("c:/Users/eldno/chthonic-archive/...")` | **Wrong absolute path** (`eldno` ≠ `eldno`) | → removed entirely | ✅ Done |
| `scripts/ssot_abbrev/cli.py:48` | `Path(".github/copilot-instructions.md")` | Fallback in `get_ssot_path()` | → cascade handles this | ✅ Done |
| ~~`lib/asc/cli.py:41`~~ | ~~`LORE_MD = ... / "mas_mcp" / "lib" / "copilot-instructions.md"`~~ | ~~Dead ref~~ | ~~bridge import~~ | ✅ **Fixed** (2026-03-25, wired via `SSOT_HOLDER_RELPATH`) |

**Progress:** 6/6 fixed. **EXIT GATE PASSED** — `grep -rn "copilot-instructions" mas_mcp/` returns ZERO functional path-construction hits (only imports and comments).

**Exit Gate:** `grep -rn --include="*.py" "copilot-instructions" mas_mcp/` (excluding infra + imports) returns ZERO functional path-construction hits.

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

### Phase 0.5 — Config Cascade + Shadow Purge
**Goal:** All IDE/MCP config SSOT references traceable to the cascade. Shadow copies resolved.

**Partial progress (2026-03-25):**
- ✅ `.temple/methodology/AGENT_COMMON.md` → redirect pointer to root `AGENT_COMMON.md`
- ❌ `docs/PWSH_RULES.md` v1.1/v1.2 reconciliation — pending (see [Steward Audit finding I](../../claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md))
- ✅ `.temple/skills/` (9 stale skills) — embalm-before-edit CLI now shipped ([Dev Plan L0](../../claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md)), embalm gate available for deletion

| Config File | Current State | Target |
|-------------|---------------|--------|
| `.vscode/mcp.json` `SSOT_PATH` env var | Hardcoded literal | Source from bridge or document as config-boundary exception |
| `.vscode/settings.json` | 2 SSOT path refs (validation ignore + chat location) | Document as IDE-boundary — VS Code requires literals here |
| `.mcp.json` (root) | May have references | Audit and document |

**Design decision:** IDE config files (settings.json, mcp.json) are **config-boundary endpoints** — they cannot import from code. The cascade contract is: *the manifest is the first place to update, and config files are documented as downstream mirrors that must be updated manually*. The cascade register should include a `config_boundary` relation type for these.

---

### Phase 0.6 — Documentation Cascade + .ankhrc Genesis
**Goal:** The SSOT metadata/governance docs reference the cascade, not hardcoded paths.

> **Note:** Phase 0.6 was downstream of the forge pipeline work ([FORGE_PIPELINE_DEV_PLAN.md](../../claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md)). All forge dependencies resolved: L0–L6 complete (2026-03-25), Phase 0.9.1 corpus verification complete (2026-03-27).

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

## 3. Relationship to Forge Pipeline

This blueprint wires the **SSOT cascade** — the Python/TS/PS1 import chain ensuring no consumer hardcodes a path. The forge pipeline ([FORGE_PIPELINE_DEV_PLAN.md](../../claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md)) built the **SFS×NOV-CAD×Bridge code** that the cascade serves. Both are now substantially complete (L0–L6 ✅, ~85% compliance):

| This Blueprint | Forge Dev Plan |
|---|---|
| Wires `ssot_manifest.py` → consumer imports | Builds forge stage transforms (`quench`, `slag`, `tea-vault`) |
| Phases 0.3–0.4: TS/PS1 bridges for `zombie_forge_bridge.py`, `novia_cadaveris_embalmer.ps1` | L2: Unifies intake paths in `zombie_forge_bridge.py` |
| Phase 0.5: Config boundary docs for `.vscode/mcp.json` | L3: Extends PATHWAY_REGISTRY schema with provenance |
| Phase 0.6: `.ankhrc` must include forge paths | L0–L1: Ships embalm-before-edit + STITCH (code that `.ankhrc` will index) |

**Sequencing (resolved):** All blueprint phases 0.2.1–0.9.1 and forge L0–L6 are complete. Phase 1.0 (bidirectional amendment protocol) is the remaining structural work.

**Steward Audit:** [BOUNTY_00000031_STEWARD_AUDIT.md](../../claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md) — canon-first gap analysis. Phase 4 → this blueprint (0.2.1–0.4). Phase 1.5 → forge dev plan (L0–L6, all complete). Addendum A → SFS/NOV-CAD compliance matrix validated by Phase 0.9.1.

---

### Phase 0.9 — Cascade Register Expansion (✅ 2026-03-26)
**Goal:** Every SSOT-adjacent file in the codebase has a cascade register entry.

Register expanded from 20 → 28 entries. 8 entries added:

| Identity | Role | Relation | Relpath | Status |
|----------|------|----------|---------|--------|
| `ssot_hash` | validator | validating | `scripts/ssot_hash.py` | ✅ Added |
| `ssot_immunity` | validator | validating | `scripts/ssot_immunity.py` | ✅ Added |
| `check_python_policy` | validator | validating | `scripts/check_python_policy.py` | ✅ Added |
| `wptg_methodology` | validator | validating | `WET_PAPER_TO_GOLD_METHODOLOGY.md` | ✅ Added |
| `ankhrc` | bridge | indexing | `.ankhrc` | ✅ Added |
| `pathstofiles` | bridge | indexing | `pathstofiles.md` | ✅ Added |
| `ssotification_methodology` | projection | projecting | `docs/SSOTIFICATION_METHODOLOGY.md` | ✅ Added |
| `ssotification_blueprint` | projection | projecting | `docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md` | ✅ Added |

Previously listed candidates already covered:
- `ts_bridge` → already `ssot_paths_ts_bridge` (Phase 0.3)
- `ps1_bridge` → already `ssot_paths_ps1_bridge` (Phase 0.4)
- `pointer_instructions` → already `pointer` (Phase 0.1)
- `pre_commit_guardian` → deferred to Phase 0.9 candidate (file exists: `scripts/hooks/pre-commit-guardian.ps1`, Gate 5 wired via Phase 2.1)

---

### Phase 0.9.1 — Corpus Integrity Verification (✅ 2026-03-27)
**Goal:** Verify the SSOT's downstream ANKH framework corpus is structurally sound after cascade wiring — fix corruption, stale drift, and wire missing envelope tooling.

**Provenance:** KCP gap analysis → FA⁵ discovery → entropy topology quantification → autonomous execution (Phases A–F).

| Finding | Severity | Fix | Status |
|---------|----------|-----|--------|
| `docs/frameworks/ankh/ankh.md` — 12× UTF-8 mojibake (FAÔü┤→FA⁴, FAÔüÁ→FA⁵, ÔåÆ→→, ÔÇö→—) | 💀 Corrupted | 9× multi_replace_string_in_file | ✅ Verified: 0 Ô chars remaining |
| `docs/frameworks/ankh/ankh.md` §8.2 — FA(1-4) missing FA⁵ | 🔴 Stale | Updated to FA(1-5) | ✅ |
| `docs/standards/LAT_CANONICAL_SPEC.md` — 7× FA¹-FA⁴ (excluded FA⁵) | 🔴 Stale | 7× replaced to FA¹-FA⁵ | ✅ Verified: 0 stale refs |
| `docs/standards/templates/kcp_template.ts` — bare `@SID` Phase 5 damage above shebang | 💀 Corrupted | Removed bare stamp, shebang restored to L1 | ✅ |
| `scripts/overnight_daemon.ts` — suspected bare `@SID` damage | Audit | False positive — @SID at L3 is inside proper KCP header | ✅ No action |
| `docs/standards/ANKH_CRC_REGISTRY.md` — suspected FA⁵ absence | Audit | 🟡 Integrated — uses specific axioms per CRC role (correct by design) | ✅ No action |
| `scripts/envelope_census.py` — `--kcp-stamp` flag phantom (argparse existed, not wired) | 🔴 Gap | Wired to `kcp_stamp_files()` | ✅ `--kcp-stamp --dry-run --ext .rs` |
| `scripts/envelope_census.py` — `--kcp-audit` flag phantom (argparse existed, not wired) | 🔴 Gap | Wired to `print_kcp_audit()` | ✅ `--kcp-audit --ext .rs` (39 files, tier breakdown + heat map) |

**Entropy topology (new framework, not a phase deliverable — observational):**
- 6 gradient classes defined: 🟢 Saturated, 🟡 Integrated, 🟠 Skewed, 🔴 StaleDrift, 💀 Corrupted, ⬛ Pre-axiomatic
- Axiom entropy measured per cascade layer (L0–L4), KCP envelope entropy per language (.py/.ts/.ps1/.rs)
- Triadic-session-context directory surveyed (19 files): 4×🟢, 4×🟡, 4×🟠, 3×🔴, 1×⬛

**FA⁵ closure confirmed:** FA⁵ ("Visual/Ornamental Integrity") formally CLOSED at L2 via `ANKH_FOUNDATIONAL_AXIOMS.md` ("Pentadic Heart"). 40+ references across SSOT. Not new — was always implicit in the canon, now explicit and auditable via `--kcp-audit`.

**Exit Gate:** `grep -rn "Ô" docs/frameworks/ankh/ankh.md` = 0 matches. `grep -rn "FA¹-FA⁴" docs/standards/LAT_CANONICAL_SPEC.md` = 0 matches. `envelope_census.py --help` shows both `--kcp-stamp` and `--kcp-audit`.

---

### Phase 0.9.2 — Triadic Session Context Upcycle (✅ active lock 2026-03-27)
**Goal:** Convert triadic-session-context from mixed historical dump state into an active governance substrate for dumpster-dive × zombie-loop operations, without deletion.

**Source nucleus:** `claude-codex-gemini/triadic-session-context/COMPREHENSIVE IMPROVEMENT PLAN PROPOSAL.md`

| File / Cluster | Current State | Action (Upcycle, not purge) | Target Outcome |
|---|---|---|---|
| `SESSION_PROTOCOL.md` | 🟢 Canon runtime playbook | Keep authoritative; treat as operational contract | Stable invocation doctrine for current loops |
| `SESSION_CACHE_STRUCTURED.md` | 🟠 Path drift (`.github/Claude_Opus_4_5...`) | Refresh paths to current triadic-session-context topology | Warm-start memory without stale coordinates |
| `SSOT_NAVIGATION_INDEX.md` + `SSOT_STRUCTURAL_INDEX.json` | 🟡 Healthy, generated artifacts | Keep regen-only discipline; do not hand-edit | Fast SSOT navigation and provenance lookup |
| `Zone_1_REDUX_implementation_ripe_for_SSOT_canon.md` | 🟢 Read-only research pool | Keep frozen; cite as source-of-truth provenance only | No lore drift in Appendix A-E integrations |
| `COMPREHENSIVE IMPROVEMENT PLAN PROPOSAL.md` | 🟠 Raw transcript nucleus | Repurpose as Redux ledger: add concise frontmatter/status block and index to derived governance decisions | Single high-level origin document for iterative cleanup direction |
| `SSOTI_FIED_SESSION_LOG.md` + `Claude_Code_Session_Dump_0001` + ad-hoc session dumps | 🔴 High-entropy historical transcript mass | Route through forge intake classification (EMBALM -> PROWL/HARVEST -> route) and reference from nucleus, not direct day-to-day consumption | Preserved forensic history with low operational noise |
| Point-fix snapshots (`BUN_SEGFAULT...`, `OpenAI_Codex...`, `Accurate_PEP...`, `Python_Metabolic_Standard...`, `gemini-cli-session-fix-too-large.md`) | 🟠 Useful but fragmented | Reclassify into either "active doctrine" or "historical incident" buckets using intake metadata | Explicit keep/park semantics per file |

**Execution discipline (matches existing forge canon):**
1. EMBALM all high-entropy transcript files before structural edits/moves.
2. Route repurpose candidates through forge intake metadata (PATHWAY_REGISTRY-aware), not ad-hoc relocation.
3. Keep one active narrative entrypoint (the nucleus file) and demote raw dumps to referenced evidence.

**Exit Gate:** Every file in `triadic-session-context/` has one of three explicit states: `active_doctrine`, `active_index`, or `historical_evidence`.

**Current state (lock achieved):**
- Lane variant `ZD-XB-LV1` recorded in session nucleus
- Full classification stamp complete
- Warm-start coordinates refreshed
- Embalm-first + route-visibility verification logged in nucleus (`4/4` embalmed; bridge summary `50/50/0`)

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
| **Python** (scripts/) | ~170 | CLIs, validators, extractors — implements §XIV-XV | ✅ 0.2 (landed) |
| **Python** (mas_mcp/) | ~40 | MCP server — implements operational governance | ✅ 0.2 (landed) |
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

| Priority | Phase | Scope | Effort | Dependencies | Status |
|----------|-------|-------|--------|-------------|--------|
| **P0** | 0.2 Stage 01 | Fix 3 critical broken references | Small | None | ✅ `fa4a6120` |
| **P0** | 0.2.1 | Wire 5 functional refs + 1 dead ref in mas_mcp/ deep dirs | Small | None | ⭐ **Now** |
| **P1** | 0.2 Stage 02-03 | Wire remaining ~20 Python scripts | Medium | Stage 01 | ✅ `fa4a6120` |
| **P1** | 0.2 Stage 04 | Tests for Python cascade completion | Small | Stage 02-03 | ✅ 16/16 passing |
| **P2** | 0.3 | TypeScript bridge + wire 6 files | Medium | None (parallel with 0.2) | ✅ 2026-03-26 |
| **P2** | 0.4 | PowerShell bridge + wire 4 files | Medium | None (parallel with 0.3) | ✅ 2026-03-26 |
| **P3** | 0.5 | Config cascade documentation | Small | 0.3 + 0.4 | ✅ 2026-03-26 |
| **P3** | 0.6 | .ankhrc genesis + doc cascade | Medium | 0.5 | ✅ 2026-03-26 |
| **P4** | 0.7 | Root hygiene (WPTG upcycle) | Medium | None (parallel) | ✅ 2026-03-26 |
| **P4** | 0.8 | Full cascade test suite (21 tests) | Medium | 0.2-0.6 | ✅ 2026-03-26 |
| **P5** | 0.9 | Register expansion (20 → 28) | Small | 0.8 | ✅ 2026-03-26 |
| **P5** | 0.9.1 | Corpus integrity verification | Medium | 0.9 | ✅ 2026-03-27 |
| **P5** | 0.9.2 | Triadic session context upcycle lane | Medium | 0.9.1 | ✅ Active (Cycle 1 lock + S7 supplement, 2026-03-27) |
| **P5** | 0.9.3 | Zone 1 research escalation to amendment candidates | Medium | 0.9.2 | ✅ Ratified (5 amendments: 4 APPROVE, 1 MODIFY applied, 2026-03-27) |
| **P5** | 0.9.4 | Zombie × Dumpster-Bridge operational governance escalation | Medium | 0.9.2 | ✅ Ratified (7 amendments: 4 APPROVE, 2 MODIFY applied, 1 DEFER; 178 files consumed, 2026-03-27) |
| **P5** | 1.0 | Bidirectional amendment protocol (formalized in Phase 0.9.3/0.9.4) | Large | All prior phases | 🟡 Next (amendment integration to governance tiers) |

---

## 5. Success Metrics (Phase 1.0 Exit Gate)

| Metric | Phase 0.1 | Current (0.9) | Target (1.0) |
|--------|-----------|---------------|---------------|
| Cascade register entries | 15 | 28 ✅ | 26+ ✅ |
| Python scripts wired | 16 | 29 (+13) | ALL (~36+) |
| Python cosmetic refs remaining | ~40 | 53 lines / 29 files (mas_mcp/ Phase 0.2.1 ✅ complete) | 0 (outside config boundary) |
| TypeScript files wired | 0 | 6 ✅ | ALL (~6) ✅ |
| PowerShell files wired | 0 | 4 ✅ | ALL (~6) ✅ |
| Hardcoded SSOT paths (functional) | ~20 | 0 ✅ | 0 ✅ |
| Test coverage (binding suite) | 16 tests | 21 tests ✅ | 24+ tests |
| `.ankhrc` exists | No | Yes ✅ | Yes ✅ |
| Critical drift items | 4 | 0 ✅ | 0 ✅ |
| HARVEST_REGISTRY current | Stale (2 months) | Stale | Current |
| Root stale artifacts | ~22 | 0 ✅ (12 relocated) | 0 ✅ |
| Corpus integrity (mojibake/FA⁵ drift) | Unknown | 0 ✅ (8 fixes, Phase 0.9.1) | 0 ✅ |
| Envelope CLI tooling (--kcp-stamp/--kcp-audit) | Phantom | Wired ✅ (Phase 0.9.1) | Operational ✅ |
| Triadic session context classification | Mixed entropy | 100% classified ✅ + v3 verified ✅ + zombie governance escalated ✅ + lane kickoff ✅ + ratified ✅ + 178 consumed ✅ (Phase 0.9.2–0.9.4 S7–S10) | 100% maintained per cycle |
| Bidirectional amendment protocol | None | Draft (12 amendments ratified, 3 MODIFY deltas applied, integration pending) | Draft operational |

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
| SSOT Manifest | [mas_mcp/logic/ssot_manifest.py](../../mas_mcp/logic/ssot_manifest.py) | Pre-0.1 (V5) |
| SSOT Binding | [mas_mcp/logic/ssot_binding.py](../../mas_mcp/logic/ssot_binding.py) | Pre-0.1 (V5) |
| Python Bridge | [scripts/lib/ssot_paths.py](../../scripts/lib/ssot_paths.py) | 0.1 |
| Binding Tests | [mas_mcp/tests/test_ssot_binding.py](../../mas_mcp/tests/test_ssot_binding.py) | Pre-0.1, expanded 0.1 |
| WPTG Methodology | [WET_PAPER_TO_GOLD_METHODOLOGY.md](../../WET_PAPER_TO_GOLD_METHODOLOGY.md) | Pre-0.1 |
| SSOTIFICATION Methodology | [SSOTIFICATION_METHODOLOGY.md](SSOTIFICATION_METHODOLOGY.md) | Pre-0.1 |
| This Blueprint | [docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md](SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md) | 0.1 (Anno Baseline) |
| Codekiller Anti-Pattern | [anti-patterns/codekiller.md](../../anti-patterns/codekiller.md) | Pre-0.1 |
| Harvest Registry | [HARVEST_REGISTRY.md](../../HARVEST_REGISTRY.md) | Pre-0.1 |

