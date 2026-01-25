# Stage 1 Migration Plan: Root-Level Repurposing

> **Session Origin**: 2026-01-25 SSOT-ification Session  
> **Status**: GENERATED  
> **SSOT Reference**: `$ANKHRC` → `.ankhrc` (bidirectional hub)

---

## Executive Summary

This plan addresses **root-level entropy** accumulated through iterative development sessions. Files are categorized into three action buckets:

| Action | Count | Description |
|--------|-------|-------------|
| **ARCHIVE** | 15 | Move to `docs/sessions/` or `docs/reports/` |
| **CONSOLIDATE** | 10 | Merge into synthesis documents |
| **KEEP** | 12 | Essential root files |
| **REGISTERED** | 3 | Newly SSOT-ified files tracked in `.ankhrc` |

---

## 1. ARCHIVE Candidates

### 1.1 Session Reports → `docs/sessions/`

These files document autonomous session completions. Value preserved through archival.

```powershell
# Create target directory
New-Item -ItemType Directory -Force -Path "docs/sessions"

# Move session reports
$sessions = @(
    "AUTONOMOUS_SESSION_2026-01-01.md",
    "AUTONOMOUS_SESSION_2_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md",
    "AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md",
    "AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_MISSION_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_MISSION_REPORT.md",
    "AUTONOMOUS_SESSION_4_COMPLETE.md",
    "AUTONOMOUS_SESSION_5_COMPLETE.md",
    "AUTONOMOUS_SESSION_5_MISSION_REPORT.md",
    "AUTONOMOUS_SESSION_7_COMPLETE.md",
    "AUTONOMOUS_SESSION_STATUS.md",
    "SESSION_2026_01_04_EPISTEMOGRAPH_COMPLETE.md",
    "session_resumption_chthonic_progress.md"
)

foreach ($f in $sessions) {
    if (Test-Path $f) { Move-Item $f "docs/sessions/" -Force }
}
```

| File | Current Location | Target | Status |
|------|------------------|--------|--------|
| `AUTONOMOUS_SESSION_2026-01-01.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_2_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_MISSION_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_3_MISSION_REPORT.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_4_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_5_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_5_MISSION_REPORT.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_7_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `AUTONOMOUS_SESSION_STATUS.md` | root | `docs/sessions/` | PENDING |
| `SESSION_2026_01_04_EPISTEMOGRAPH_COMPLETE.md` | root | `docs/sessions/` | PENDING |
| `session_resumption_chthonic_progress.md` | root | `docs/sessions/` | PENDING |

### 1.2 Quickref/Framework Files → `docs/frameworks/`

```powershell
New-Item -ItemType Directory -Force -Path "docs/frameworks"

$frameworks = @(
    "AUTONOMOUS_COORDINATOR_QUICKREF.md",
    "AUTONOMOUS_ORCHESTRATION_FRAMEWORK.md",
    "SESSION_3_ORCHESTRATION_QUICKREF.md",
    "SESSION_3_TYPESCRIPT_QUICKREF.md"
)

foreach ($f in $frameworks) {
    if (Test-Path $f) { Move-Item $f "docs/frameworks/" -Force }
}
```

---

## 2. CONSOLIDATE Candidates

### 2.1 DCRP Reports → `docs/DCRP_SYNTHESIS.md`

10 DCRP-related files contain overlapping information. Consolidate into single synthesis.

| File | Type | Consolidate Into |
|------|------|------------------|
| `DCRP_DEPLOYMENT_SUMMARY.md` | Summary | `DCRP_SYNTHESIS.md` |
| `DCRP_ENHANCED_ANALYSIS.md` | Analysis | `DCRP_SYNTHESIS.md` |
| `DCRP_FINAL_STATUS.md` | Status | `DCRP_SYNTHESIS.md` |
| `DCRP_MERGE_REPORT.txt` | Report | `DCRP_SYNTHESIS.md` |
| `DCRP_OBSERVABILITY_UPGRADE.md` | Upgrade | `DCRP_SYNTHESIS.md` |
| `DCRP_OBSERVABILITY_VALIDATION_COMPLETE.md` | Validation | `DCRP_SYNTHESIS.md` |
| `DCRP_PRODUCTION_ANALYSIS.md` | Analysis | `DCRP_SYNTHESIS.md` |
| `DCRP_REFACTOR_COMPLETE.md` | Complete | `DCRP_SYNTHESIS.md` |
| `DCRP_REFACTORING_SESSION_SUMMARY.md` | Summary | `DCRP_SYNTHESIS.md` |
| `DCRP_UNIFIED_REFACTOR.md` | Unified | `DCRP_SYNTHESIS.md` |

**Action**: Extract key insights from each, create unified `docs/DCRP_SYNTHESIS.md`, then archive originals to `dumpster-dive/consolidated/dcrp/`.

### 2.2 Handoff Documents → `docs/handoffs/`

```powershell
New-Item -ItemType Directory -Force -Path "docs/handoffs"

$handoffs = @(
    "CLAUDE_HANDOFF_CHROMA_GENESIS.md",
    "GEMINI_HANDOFF_CACHE.md",
    "GEMINI_HANDOFF_PHASE_11_5.md"
)

foreach ($f in $handoffs) {
    if (Test-Path $f) { Move-Item $f "docs/handoffs/" -Force }
}
```

---

## 3. KEEP (Essential Root Files)

These files **MUST remain at root**:

| File | Reason |
|------|--------|
| `.ankhrc` | **Bidirectional SSOT hub** |
| `ankh_index.json` | Signal index (SSOT-referenced) |
| `sid_index.json` | Session ID tracking |
| `Cargo.toml` | Rust build manifest |
| `Cargo.lock` | Dependency lock |
| `build.rs` | Build script |
| `pyproject.toml` | Python project config |
| `package.json` | Node/Bun config |
| `.gitignore` | Git exclusions |
| `CLAUDE.md` | Claude agent configuration |
| `ankh.md` | Core ankh documentation |
| `ANKHOLOGY.md` | Ankh reference |

---

## 4. REGISTERED (This Session)

Files newly tracked in `.ankhrc[ssot_ified]`:

| File | Section | Key |
|------|---------|-----|
| `mas_mcp/ssot_extractor.py` | `[ssot_ified]` | `SSOT_EXTRACTOR` |
| `mas_mcp/milf_genesis_v2.py` | `[ssot_ified]` | `MILF_GENESIS_V2` |
| `mas_mcp/lib/asc_toolchain.py` | `[ssot_ified]` | `ASC_TOOLCHAIN` |
| `dumpster-dive/.../milf_genesis_v1_deprecated.py` | `[ssot_ified]` | `MILF_GENESIS_V1_DEPRECATED` |

---

## 5. Execution Checklist

- [x] Create `docs/sessions/` directory
- [x] Move 15 session report files (actual: 18)
- [x] Create `docs/frameworks/` directory
- [x] Move 4 framework/quickref files (actual: 8 incl. ankh/)
- [x] Create `docs/handoffs/` directory
- [x] Move 3 handoff files
- [x] Generate `docs/DCRP_SYNTHESIS.md` from 10 DCRP files
- [x] Archive DCRP originals to `dumpster-dive/consolidated/dcrp/` (9 files)
- [x] Update `.ankhrc[migration_status]` entries to COMPLETE
- [x] Document SSOT-ification methodology (`docs/SSOTIFICATION_METHODOLOGY.md`)
- [x] Commit: `7433a56` Stage 1 root-level repurposing complete
- [x] Commit: `5affab9` Stage 1.5 actual reduction

**STATUS: COMPLETE** (2026-01-25)

### Stage 1.5 Additional Reductions:
- Root .md: 29 → 1 (CLAUDE.md only)
- Root .json: 11 → 5
- Untracked: .next/ (113), genesis logs (16), daemon classifications (123)
- Organized: data/epistemograph/, data/graphs/
- Git-tracked: 1,351 → 1,221 (130 file reduction)

---

## 6. Post-Migration Verification

```powershell
# Verify no orphaned AUTONOMOUS_SESSION_*.md at root
Get-ChildItem -Filter "AUTONOMOUS_SESSION_*.md" | Should -BeNullOrEmpty

# Verify no orphaned DCRP_*.md at root
Get-ChildItem -Filter "DCRP_*.md" | Should -BeNullOrEmpty

# Verify .ankhrc resolves all paths
# TODO: Create ankhrc_validator.py
```

---

## 7. Session Capture Mechanism (TODO #6)

**Problem Statement**: This session's full context, progression, and decisions are not automatically captured. Manual copy/paste is required to reconstruct session value.

**Proposed Solution**: 
1. Create `scripts/session_extractor.py` that parses GitHub Copilot chat logs
2. Generate structured session summary with:
   - Files created/modified
   - Key decisions made
   - SSOT sections touched
   - Anchor resolutions used
3. Output to `docs/sessions/SESSION_YYYY_MM_DD_<TOPIC>.md`

**Dependencies**:
- Access to chat log format (investigate `github-copilot-chat-log` at root)
- JSON/Markdown parser for structured extraction

---

*Generated by SSOT-ification Session 2026-01-25*
