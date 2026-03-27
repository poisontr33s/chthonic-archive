# Bounty 00000031 — Senior Steward Structural Audit

> **@SID:** SESSION_STEWARD_AUDIT_00000031
> **Date:** 2026-03-26 (revised)
> **Agent:** Claude (Dr. Lysandra Thorne — Truth Chain)
> **Scope:** Full-archive integrity audit + architectural roadmap
> **Framing:** Canon-first. The SSOT (`.github/copilot-instructions.archive.md`) is the generative origin. All code is downstream projection. Divergence = implementation drift, never canon drift.

---

## Executive Summary

The chthonic-archive is a polyglot (Rust/Python/TypeScript/PowerShell/Ruby/R/Zig/Go) mono-repo with ~307 scripts, 32 Claude skills, 28 Codex skills, 28 Gemini skills, and a 9100-line SSOT monolith. The core instrumentation (`chthonic.ps1` router, `link_audit.py`, SSOT cascade) is sound. The fragility is not in what exists — it's in what drifts unguarded between sync points.

**Overall health:** Structurally coherent core, accumulating shadow copies and temp debris at the periphery. The allowlist `.gitignore` prevents tracking pollution, but disk pollution is real. No pre-commit enforcement hooks are installed despite `scripts/hooks/` infrastructure existing.

---

## I. FINDINGS — Structural Inconsistencies

### A. Critical (Blocking)

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| **C1** | Unresolved git merge conflict | [docs/architecture/CLAUDE.md](../../docs/architecture/CLAUDE.md) | Unparseable file — any agent reading it gets garbage |
| ~~**C2**~~ | ~~Dead SSOT path ref in `mas_mcp`~~ | ~~`mas_mcp/lib/asc/cli.py:41`~~ | ✅ **RESOLVED** (Phase 0.2.1, 2026-03-25) — wired through `SSOT_HOLDER_RELPATH` |

### B. Drift (Stale Shadows)

| # | Issue | Stale Copy | Canonical Source |
|---|-------|-----------|-----------------|
| **D1** | `.temple/methodology/AGENT_COMMON.md` diverged | `.temple/methodology/AGENT_COMMON.md` (missing Triad, Linguistic Invariants, contains hardcoded path typo `erdno`) | Root `AGENT_COMMON.md` |
| **D2** | `.temple/skills/` (9 skills) frozen pre-Feb 2026 | `.temple/skills/*` | `.claude/skills/*` |
| **D3** | `docs/PWSH_RULES.md` exact duplicate | `docs/PWSH_RULES.md` | Root `PWSH_RULES.md` |
| ~~**D4**~~ | ~~Gemini skill mirror 53 days stale~~ | ~~`.gemini/extensions/.../skills/`~~ | ✅ **RESOLVED** (2026-03-26) — corpse-reviver SKILL.md, corpse_reviver.py, embalm_before_edit.py synced from `.codex/` canonical. `.claude/` also synced (was 2637 lines behind on corpse_reviver.py + had stale WIP gate on embalm_before_edit.py). Full triad parity: `.codex` = `.claude` = `.gemini`. |

### C. Parity Gaps (Cross-Agent)

| Skill | Claude | Codex | Gemini | Notes |
|-------|--------|-------|--------|-------|
| `git-snapshot` | ✅ | ❌ | ❌ | Codex/Gemini can't produce handoff snapshots |
| `handoff-loop` | ✅ | ❌ | ❌ | Codex/Gemini blind to handoff routing |
| `overnight-archaeology` | ✅ | ❌ | ❌ | Codex blind to daemon ore |
| `theme-system` | ✅ | ❌ | ❌ | Extension dev gated to Claude only |
| `link-path-guard` | ✅ | ? | ❌ | Link validation unavailable in Gemini |
| `sfa` | ✅ (stashed) | ❌ | ❌ | Low priority — aesthetic ref |
| `triad-velocity-lane` | ❌ | ❌ | ✅ | Gemini-exclusive velocity skill |

**No `AGENT_SKILL_PARITY_MANIFEST.md` exists to track this.**

### D. Envelope / @SID Compliance

| Language | Coverage | Gap |
|----------|----------|-----|
| Python (scripts/) | ~98% (162/164) | `_scm_classify.py` (temp), `_envelope_census.py` (no SID) |
| TypeScript | ~100% (24/24) | ✅ **RESOLVED** (2026-03-26 — all TS in scripts/ already compliant) |
| PowerShell | ~100% (97/97) | ✅ **RESOLVED** (2026-03-26 — 54 stamped by `scripts/lib/stamp_sid.py`, 43 already compliant via Decorator's Blessing or prior @SID) |
| Python (lib/) | 90% | `ssot_paths.py` missing @SID |

Automated stamper: `uv run scripts/lib/stamp_sid.py` (idempotent, detects both `@SID:` and `Semantic ID:` patterns). `script-envelope` skill remains STASHED — `stamp_sid.py` is the operational replacement.

### E. File Placement Violations

| Item | Current Location | Correct Location |
|------|-----------------|-----------------|
| `github-mcp-server.exe` | `scripts/aws/` AND `scripts/bin/` | `scripts/bin/` only |
| `silence-mcp-filesystem-warning.cjs` | `scripts/postinstall/` (compiled artifact beside `.ts` source) | `.gitignore` or `dist/` |
| Superseded scripts: `build_epistemograph.py`, `local_refiner.py`, `decorator_cross_ref_enhanced.py`, `decorator_cross_ref_production.py` | `scripts/` (live) | `scripts/.deprecated/` |
| `ssot_registry_query.ps1` (v1) | `scripts/` | `scripts/.deprecated/` (v2 exists) |

### F. Root-Level Debris

~~16 temp/session artifacts on disk at repo root.~~ **RESOLVED** — all 12 temp JSON files confirmed gone (2026-03-25 live check). Remaining on disk: `challenge_task_session_context_truncted.md_*`, `codexfailsessionDUMP.md`, `pathstofiles.md` (session artifacts, not tracked by git).

### G. Inert Lanes

| Lane | Tooling | Active Code | Status |
|------|---------|-------------|--------|
| **R** | `rv-r.ps1` + `rproject.toml` (empty deps) | 0 `.R` files | Scaffold only — no workload |
| **Zig** | `zv` path in chthonic.ps1 | 0 `.zig` files | Scaffold only |
| **Go** | `goup` path in chthonic.ps1 | 0 `.go` files | Scaffold only |
| **Brush** | `brush_repo.rc` | 1 `.rc` file | Minimal — POSIX compat layer |

### H. Hook Infrastructure Gap

~~`scripts/hooks/pre-commit-guardian.ps1` exists but is not wired.~~ **WORSE** — `pre-commit-guardian.ps1` itself is GONE. `.git/hooks/` contains only `.sample` files. No pre-commit enforcement exists at all.

### ~~I.~~ Drift Correction: PWSH_RULES.md

**Original audit said:** `docs/PWSH_RULES.md` is an "exact duplicate" of root. **Wrong.** Root is v1.1 (2026-01-29, verbose). `docs/` is v1.2 (2026-02-01, streamlined rewrite — PowerShell version refs normalized to "7+", new Profile Configuration section, large sections removed). They have diverged. Reconciliation needed, not deletion.

---

## ADDENDUM A — SSOT Canon-First Gap Analysis: SFS × NOV-CAD × Forge Pipeline

> **Framing correction (2026-03-25):** The original Addendum A treated the corpse-reviver as an "implementation gate" — a checkbox before file deletions. That framing was backwards. The SSOT (§10.3.2 SFS + §10.3.3 NOV-CAD, lines 4151–4393) IS the generative origin. The SFS/NOV-CAD/forge pipeline was defined first; the code is a downstream projection. What follows is a compliance audit: SSOT canon → implementation state.

### A.1 — SFS Forge Protocol (§10.3.2): 7-Stage Compliance

The SSOT mandates: **RECEIVE → ASSESS → HEAT → HAMMER → QUENCH → TEMPER → SLAG**

| SSOT Stage | Directory | Scripts | Verdict |
|---|---|---|---|
| **RECEIVE + ASSESS** | `forge/intake/` exists BUT `zombie_forge_bridge.py` routes through outer `dumpster-dive/intake/`, bypassing it | `zombie_forge_bridge.py` routes by pre-computed `ore_rating` — no assessment logic | **PARTIAL** — routing works, intake path drifted |
| **HEAT** (FURNACE) | `forge/furnace/` ✅ | `universal_forge.py` transmutes corpse-vault → furnace artifacts (implicit) | **PARTIAL** — no explicit `heat()` function |
| **HAMMER** (ANVIL) | `forge/anvil/` ✅ | Audit outputs (CODEBASE_ANOMALY_HARVEST, CORPSE_VAULT_DEEP_AUDIT) land here | **PARTIAL** — structural separation only |
| **QUENCH** | `forge/quench/` ✅ | `quench_artifacts()` at universal_forge.py — fast-tracks ore_rating 5 to tempered with validation | **COMPLETE** (L5, 2026-03-25) |
| **TEMPER** | `forge/tempered/` ✅ | `temper_artifacts()` at universal_forge.py:1405. Graduates furnace → tempered. | **COMPLETE** |
| **SLAG** | `forge/slag/` ✅ | `slag_artifacts()` at universal_forge.py — processes rejections, flags upcycle_pending items | **COMPLETE** (L5, 2026-03-25) |
| **TEA-VAULT** | `forge/tea-vault/` ✅ | `collapse_tea_vault()` at universal_forge.py — collapses superposition items to anvil | **COMPLETE** (L5, 2026-03-25) |

**SFS forge compliance: 4/7 COMPLETE, 3/7 PARTIAL.** *(Updated 2026-03-25 post-L5 execution — was 1/7 COMPLETE, 3/7 PARTIAL, 3/7 SHELL ONLY)*

Additional: `PROCESS_FLOW.md` documents the full protocol but models it as a DAG (parallel stage routing by ore_rating), diverging from the SSOT's linear cascade description.

### A.2 — NOV-CAD OSGTTLR Protocol (§10.3.3): Pipeline Compliance

The SSOT mandates a pipeline flow: **PROWL → EMBALM → VAULT → SUTURE → (optional return to INTAKE)**

| SSOT Mandate | Implementation | Verdict |
|---|---|---|
| PROWL → EMBALM → VAULT → SUTURE chain | Independent CLI subcommands, no enforced chaining, no state machine | **MISSING** — modes execute independently |
| **PROWL** mode | `cmd_prowl()` at corpse_reviver.py:776 | **COMPLETE** |
| **HARVEST** (all 8 graveyards) | 8 `harvest_*()` functions — commits, stashes, comments, reflog, dead-branches, orphans, gitignored, graffiti | **COMPLETE** |
| **HOARD** | Shared handler with harvest, `is_hoard=True` forces `--all` | **COMPLETE** |
| **CLASSIFY** | `cmd_classify()` at :962 | **COMPLETE** |
| **REANIMATE** | `cmd_reanimate()` at :1000 | **COMPLETE** |
| **SUTURE** | `cmd_suture()` at :823 (1 output: `stitched_rust.txt`) | **COMPLETE** |
| **MANIFEST** | `cmd_manifest()` at :1045 | **COMPLETE** |
| **EMBALM** (post-harvest internal) | `embalm()` at :887 — writes `.fragment` + `.provenance.json` sidecars | **COMPLETE** |
| **EMBALM-before-edit** (pre-mortem CLI) | `embalm_before_edit.py` — WIP gate removed, main() dispatch implemented | **COMPLETE** (L0, 2026-03-25) |
| **STITCH** (companion to EMBALM) | `cmd_stitch()` integrated into `corpse_reviver.py` CLI as `stitch` subcommand | **COMPLETE** (L1, 2026-03-25) |
| **VAULT** as explicit protocol step | Implicit in `embalm()` — no `cmd_vault()` | **MISSING** — embedded, not addressable |
| **Return path** (OSGTTLR → SFS INTAKE) | `cmd_suture()` accepts `--forge-eligible` flag, routes composites to `forge/intake/` with provenance sidecars | **COMPLETE** (L4, 2026-03-25) |

**NOV-CAD mode compliance: 9/9 modes COMPLETE as individual commands (was 7/9). 1/1 pipeline flow implemented (L6). 0/2 critical paths remaining (was 2/2).** *(Updated 2026-03-25 post-execution)*

### A.3 — Bridge: SFS ↔ NOV-CAD ↔ PATHWAY_REGISTRY

| SSOT Mandate | Implementation | Verdict |
|---|---|---|
| EMBALM provenance sidecars feed PATHWAY_REGISTRY.json | `zombie_forge_bridge.py` `_find_provenance_sidecar()` returns parsed provenance data. `route_file()` writes `provenance` field (sha256, source_file, git_head, snapshot_at, language) into registry entries. | **COMPLETE** (L3, 2026-03-25) |
| `dumpster-dive/intake/` routes to `forge/intake/` | `zombie_forge_bridge.py` dual-scans `forge/intake/` (primary) + `dumpster-dive/intake/` (legacy with deprecation warning) | **COMPLETE** (L2, 2026-03-25) |
| Bidirectional flow (forge → vault, vault → forge) | `cmd_suture()` `--forge-eligible` routes composites + provenance sidecars back to `forge/intake/` | **COMPLETE** (L4, 2026-03-25) |
| `dumpster-upcycler` ↔ `corpse-reviver` | Zero cross-references. Different domains (session transcripts vs dead code). | **NO CONNECTION** — confirmed separate pipelines |

### A.4 — `.temple/skills/` Verdict

The 9 skills in `.temple/skills/` (artifact-upcycle, conceptualize, gh-address-comments, gh-fix-ci, gh-mcp-autonomy, imagegen, openai-docs, script-envelope, sora) are **domain-expertise skills with zero architectural relation to PROWL/HARVEST/HOARD/CLASSIFY/REANIMATE/SUTURE/MANIFEST/EMBALM/STITCH**. The 9-count is coincidental. NOV-CAD's modes live within `.codex/skills/corpse-reviver/` and `.claude/skills/corpse-reviver/`.

### A.5 — 8-Graveyards vs 9-Graveyards

The SSOT §10.3.3 already addresses this in the D-cup post-EMBALM canonization passage: *"D = 8 graveyards + 1 pre-mortem source = 9 total capture channels compressed into 8-graveyard indexing — the 9th channel (EMBALM) overlays ALL 8 graveyards."* EMBALM as 9th capture channel is already canon. Formal rename to "The 9 Graveyards" in the heading is a presentation decision.

### A.6 — Aggregate Pipeline Compliance

| Domain | SSOT-Mandated | Implemented | Compliance |
|---|---|---|---|
| SFS 7-stage forge transforms | 7 stages | 4 complete + 3 partial | **~65%** |
| NOV-CAD 9 modes (individual) | 9 modes | 9 complete | **~100%** |
| NOV-CAD pipeline flow (OSGTTLR chain) | 1 pipeline | 1 (pipeline subcommand) | **~90%** |
| Bridge (bidirectional routing + provenance) | 3 bridge functions | 2 complete + 1 partial (dual-scan intake + provenance + return path) | **~80%** |
| **Overall SFS×NOV-CAD×Bridge pipeline** | — | — | **~85%** |

> *Updated 2026-03-25 post-execution of [Forge Pipeline Dev Plan](FORGE_PIPELINE_DEV_PLAN.md) L0–L6. Was ~35% pre-execution.*

---

## II. ARCHITECTURAL PLAN — Phased Invariance Progression

> **Reframed:** Phases 0–1 address immediate blockers and implementation drift. The SFS×NOV-CAD pipeline gap (~35% compliance) is the dominant structural debt and requires a dedicated forge-completion phase.

### Phase 0: Triage (Immediate) — ✅ PARTIALLY DONE

| Step | Action | Status |
|------|--------|--------|
| 0.1 | Resolve merge conflict in `docs/architecture/CLAUDE.md` | ✅ **DONE** (2026-03-25) — kept `../../` relative paths |
| 0.2 | Fix dead SSOT ref in `mas_mcp/lib/asc/cli.py:41` | ✅ **DONE** (2026-03-25) — wired through `SSOT_HOLDER_RELPATH` from `ssot_manifest.py` |
| 0.3 | Root temp JSON cleanup | ✅ **ALREADY GONE** — confirmed 2026-03-25 |
| 0.4 | `github-mcp-server.exe` in `scripts/aws/` | ✅ **ALREADY GONE** |
| 0.5 | Replace `.temple/methodology/AGENT_COMMON.md` with redirect pointer | ✅ **DONE** (2026-03-26) — 45-line partial redirect → 3-line pointer to root |
| 0.6 | Reconcile PWSH_RULES.md v1.1 (root) vs v1.2 (docs/) | ✅ **DONE** (2026-03-26) — root is canonical (CLAUDE.md references it); docs/ replaced with 3-line redirect pointer |

### Phase 1: Shadow Purge (Embalm-gated)

**Prerequisite:** PROWL → HARVEST → verify provenance sidecars for all targets.

| Step | Action | Risk |
|------|--------|------|
| 1.0 | **EMBALM GATE:** Run `corpse_reviver.py harvest` on all Phase 1 targets | Preserve before purge — non-negotiable |
| 1.1 | Delete `.temple/skills/` entirely (9 stale domain skills, NOT NOV-CAD modes) | Low — `.claude/skills/` is canonical |
| 1.2 | Retire superseded scripts to `scripts/.deprecated/` | Low — modern variants remain |

### Phase 1.5: Forge Completion (✅ COMPLETE — SSOT compliance)

**Objective:** Close the ~65% gap between SSOT-mandated SFS×NOV-CAD pipeline and implementation.
**Execution plan:** [FORGE_PIPELINE_DEV_PLAN.md](FORGE_PIPELINE_DEV_PLAN.md) — 6 work items (L0–L6), 3 sprints, 4 files. **All executed 2026-03-25.**

| Step | Action | SSOT Reference | Status |
|------|--------|----------------|--------|
| 1.5.1 | **Unify intake paths:** Dual-scan `forge/intake/` + legacy `dumpster-dive/intake/` | §10.3.2 SFS domain = `DSTR-DVE/` | ✅ L2 |
| 1.5.2 | **Integrate STITCH into corpse_reviver.py CLI** | §10.3.3 STITCH is a NOV-CAD mode | ✅ L1 |
| 1.5.3 | **Ship embalm-before-edit CLI** — WIP gate removed, main() dispatch wired | §10.3.3 EMBALM pre-mortem mandate | ✅ L0 |
| 1.5.4 | **Build return path:** SUTURE `--forge-eligible` → `forge/intake/` | §10.3.3 OSGTTLR Protocol diagram | ✅ L4 |
| 1.5.5 | **Bridge PATHWAY_REGISTRY with provenance:** EMBALM sidecar data in registry entries | §10.3.3 EMBALM mode description | ✅ L3 |
| 1.5.6 | **Implement QUENCH/SLAG/TEA-VAULT transforms** in `universal_forge.py` | §10.3.2 7-stage protocol | ✅ L5 |
| 1.5.7 | **Add OSGTTLR pipeline coordinator** — `corpse_reviver.py pipeline` command | §10.3.3 OSGTTLR flow diagram | ✅ L6 |

### Phase 2: Hook Gate (✅ COMPLETE)

**Objective:** Make file-move breakage impossible to commit silently.

| Step | Action | Status |
|------|--------|--------|
| 2.1 | Wire `link_audit.py renames --staged --dry-run` into `scripts/hooks/pre-commit-guardian.ps1` as Gate 5 | ✅ DONE (2026-03-26) |
| 2.2 | Add `install-hooks.ps1` call to `chthonic env` activation (opt-in, idempotent) | ✅ DONE (2026-03-26) |
| 2.3 | Create `scripts/envelope_census.py` — lightweight @SID header compliance auditor across `.py`, `.ps1`, `.ts` | ✅ DONE (2026-03-26) |
| 2.4 | Add envelope census as a `chthonic audit envelope` subcommand | ✅ DONE (2026-03-26) |

### Phase 3: Parity Manifesto (Cross-agent alignment)

**Objective:** Document + enforce skill parity across Claude/Codex/Gemini.

| Step | Action |
|------|--------|
| 3.1 | Create `.temple/methodology/AGENT_SKILL_PARITY_MANIFEST.md` documenting current gaps |
| 3.2 | Port `git-snapshot`, `handoff-loop`, `overnight-archaeology`, `theme-system` to `.codex/skills/` |
| 3.3 | Sync `.gemini/` skills to match `.claude/` (add 6 missing skills) |
| 3.4 | Add parity check to `trainstop-orchestrator` lane (automated gate) |
| 3.5 | Record Gemini `triad-velocity-lane` as intentionally exclusive (manifest annotation) |

### Phase 4: SSOT-ification Continuation (✅ COMPLETE through Phase 0.9)

**Objective:** Resume the SSOT cascade register from where it stalled.
**Master blueprint:** [`docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`](../../docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md) — phases, exit gates, and wiring tables live there. Updated 2026-03-26.

| Step | Phase | Action | Status |
|------|-------|--------|--------|
| 4.1 | 0.2.1 | Fix 5 unwired functional refs + 1 dead ref in `mas_mcp/` | ✅ DONE (2026-03-25) |
| 4.2 | 0.3 | TypeScript bridge + wire 6 files | ✅ DONE (2026-03-26) |
| 4.3 | 0.4 | PowerShell bridge + wire 4 files | ✅ DONE (2026-03-26) |
| 4.4 | 0.5 | Config boundary documentation (2 IDE configs) | ✅ DONE (2026-03-26) |
| 4.5 | 0.6 | .ankhrc genesis + methodology doc | ✅ DONE (2026-03-26) |
| 4.6 | 0.7 | Root hygiene — 12 artifacts → intake | ✅ DONE (2026-03-26) |
| 4.7 | 0.8 | Cascade testing expansion (21/21 tests) | ✅ DONE (2026-03-26) |
| 4.8 | 0.9 | Register expansion (20 → 28 entries) | ✅ DONE (2026-03-26) |

**Remaining:** Phase 1.0 (bidirectional amendment protocol) — tracked in blueprint

### Phase 5: Envelope Canonization (🔄 IN PROGRESS — bare stamp deployed, KCP upgrade pending)

**Objective:** Bring all executable files to KCP-compliant headers (two-stratum: Cartouche + Khipu).

| Step | Action | Status |
|------|--------|--------|
| 5.1 | Define `@SID` naming pattern (`{PREFIX}_{UPPER_STEM}_V1`) | ✅ 2026-03-27 |
| 5.2 | Build `envelope_census.py` with `--stamp`/`--dry-run` modes | ✅ 2026-03-27 |
| 5.3 | Bare-stamp `@SID` on 64 PS1 + 171 TS files | ✅ 2026-03-27 (Stratum 2 K1 only) |
| 5.4 | Upgrade stamper to full KCP (Cartouche + Khipu per-language encapsulation) | ❌ NOT STARTED |
| 5.5 | Re-stamp with Spectrum/Zone inference, @Shabti, @Purpose per file | ❌ NOT STARTED |
| 5.6 | Update compliance census to audit KCP field completeness (not just @SID presence) | ❌ NOT STARTED |

**Current state:** 235 files have bare `@SID` only (1/5 required KCP fields). Full KCP gold standard requires: Cartouche (Spectrum + Zone + Radiance), Khipu (@SID + @Shabti + @Purpose). Reference templates: `docs/standards/templates/kcp_template.{py,ps1,ts,rs}`. Protocol spec: `docs/standards/KCP_PROTOCOL_ONTOLOGY.md`.

### Phase 6: Inert Lane Decision (Strategic)

**Objective:** Either activate or formally park R/Zig/Go lanes.

| Lane | Recommendation |
|------|---------------|
| **R** (`rv-r`) | Park formally — add `# STATUS: PARKED (no active R workload)` to `rproject.toml`. Keep `rv-r.ps1` as infrastructure for when R analysis scripts materialize. |
| **Zig** (`zv`) | Park formally — no `.zig` source exists. Keep `zv` path registration in chthonic.ps1. |
| **Go** (`goup`) | Park formally — no `.go` source exists. Same treatment. |
| **Brush** | Keep active — POSIX compat layer serves a real purpose for CI/cross-platform scripts. |

---

## III. DEPENDENCY MAP (What blocks what)

```
SSOT Canon (§10.3.2 SFS + §10.3.3 NOV-CAD = generative origin)
  │
  ├── Phase 0 (triage — immediate blockers) ← ✅ MOSTLY DONE
  │     │
  │     ├── Phase 1 (shadow purge — embalm-gated deletions)
  │     │     └── Phase 3 (parity) ← requires knowing what is canonical
  │     │
  │     ├── Phase 1.5 (forge completion — SSOT compliance) ← DOMINANT STRUCTURAL DEBT
  │     │     ├── 1.5.1-1.5.3 (intake unify + STITCH + EMBALM CLI) ← unblocks Phase 1 automation
  │     │     ├── 1.5.4-1.5.5 (return path + provenance bridge) ← unblocks bidirectional pipeline
  │     │     ├── 1.5.6 (forge stage transforms) ← independent per-stage work
  │     │     └── 1.5.7 (OSGTTLR coordinator) ← depends on 1.5.1-1.5.5
  │     │
  │     ├── Phase 2 (hooks) ← independent, can run parallel
  │     │     └── Phase 5 (envelope blitz) ← needs census tool from 2.3
  │     │
  │     └── Phase 4 (SSOT cascade) ← independent, continues existing work
  │           └── Phase 6 (lane decisions) ← informed by cascade coverage
```

**Critical path:** 0 → 1.5.1-1.5.3 → 1.5.7 → 1 (forge completion unblocks safe automated purge)
**Parallel track:** 0 → 2 → 5 (hook infra + envelope enforcement)
**Independent:** 0 → 4 (SSOT cascade resumes from existing blueprint)
**Dominant debt:** ~~Phase 1.5 — the SFS×NOV-CAD pipeline is ~35% implemented against SSOT canon~~ ✅ **RESOLVED** (2026-03-25, ~85% post-execution). ~~D4 (Gemini stale copies)~~ ✅ **RESOLVED** (2026-03-26, full triad parity on corpse-reviver). ~~Phase 4 (SSOT cascade)~~ ✅ **RESOLVED** (2026-03-26, 0.2.1→0.9 complete, 28-entry register). ~~Phase 2 (hook infrastructure)~~ ✅ **RESOLVED** (2026-03-26, Gate 5 + env hook + envelope census + CLI subcommand). Remaining dominant debts: **Phase 5** (envelope canonization — bare @SID deployed, full KCP upgrade pending: Cartouche + Khipu encapsulation) + Phase 3 (agent parity) + Phase 1 (shadow purge).
**Phase 1.5 execution detail:** [FORGE_PIPELINE_DEV_PLAN.md](FORGE_PIPELINE_DEV_PLAN.md) (L0–L6 — all complete)

---

## IV. INVARIANCE CONTRACTS (What must never regress)

| Invariant | Guard | Current Status |
|-----------|-------|---------------|
| **SSOT is generative origin** | All code measures against `.github/copilot-instructions.archive.md` | ✅ Established |
| **SFS 7-stage forge protocol** | `universal_forge.py` + `PROCESS_FLOW.md` | ✅ ~65% — 4/7 complete (L5 shipped quench/slag/tea-vault) |
| **NOV-CAD OSGTTLR pipeline** | `corpse_reviver.py pipeline` mode | ✅ ~90% — [Dev Plan L6](FORGE_PIPELINE_DEV_PLAN.md) executed |
| **Embalm-before-delete** | `corpse_reviver.py` PROWL→HARVEST→verify | ✅ CLI shipped — [Dev Plan L0](FORGE_PIPELINE_DEV_PLAN.md) executed |
| **Bidirectional bridge** | `zombie_forge_bridge.py` + PATHWAY_REGISTRY | ✅ ~80% — [Dev Plan L2–L4](FORGE_PIPELINE_DEV_PLAN.md) executed |
| No raw `python`/`pip` invocations | `bun_compliance_audit.py` analog needed for Python | Enforced by convention only |
| Single SSOT copy | User directive (2026-03-14) | ✅ (one archive.md survives) |
| Commit lifecycle owned by user | AGENT_COMMON.md | ✅ |
| Codekiller salvage-first | AGENT_COMMON.md + AGENTS.md | ✅ |
| LF line endings | `.gitattributes` | ✅ |
| @SID on every script | No enforcement tool | ❌ 76 PS1 files non-compliant |
| Pre-commit link integrity | Hook gone entirely | ❌ |
| Skill parity across agents | No manifest | ❌ |

---

## V. POLYGLOT HEALTH SNAPSHOT

| Lane | Manager | Version Pin | Scripts | Active | Notes |
|------|---------|-------------|---------|--------|-------|
| **Python** | `uv` | ≥3.14 | ~164 | ✅ | Backbone — fully wired |
| **TypeScript** | `bun` | ≥1.3.11 | 23 | ✅ | MCP servers, daemon, extension |
| **PowerShell** | `pwsh` | 7.5.x | ~84 | ✅ | Router, probes, env — but @SID gap |
| **Rust** | `cargo` | stable | `src/` (Vulkan/ECS core) | ✅ | chthonic-archive binary |
| **Ruby** | `rv` | managed | 0 (tooling only) | ⚠️ | `rv` aliased for Ruby lane, no `.rb` source |
| **R** | `rv-r` | 4.5 | 0 | 🅿️ | Parked scaffold |
| **Go** | `goup` | managed | 0 | 🅿️ | Parked scaffold |
| **Zig** | `zv` | managed | 0 | 🅿️ | Parked scaffold |
| **Bash** | `brush` | managed | 1 (`.rc`) | ⚠️ | Minimal POSIX compat |

---

*Filed to `claude/mailbox/` per mailbox protocol. No commits made — user owns the commit lifecycle.*
