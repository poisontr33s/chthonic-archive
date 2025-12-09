# Macro-Prompt-World Cartography Report

**Date:** 2025-12-09
**Surveyor:** Sister Ferrum Scoriae (SFS) + ASC Engine
**Purpose:** CTF (Cross-Tier Fusion) pre-assessment for SSOT integration candidates

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Files** | ~53 files across 8 subdirectories + 16 root files |
| **Total Size** | ~1.87 MB |
| **High-Priority (⚗️5)** | 7 files (Grimoires + Prime Factions core) |
| **Medium-Priority (🔧4)** | ~15 files |
| **Low-Priority (⚖️3 or below)** | ~31 files (session logs, duplicates, recovery docs) |

---

## Priority Tier 1: CTF Candidates (Rating ⚗️5)

### 1.1 The Grimoires (Root Level)

| File | Size | SSOT Target | CTF Status |
|------|------|-------------|------------|
| `Tripartite_Grimoire_Master_Index.md` | 15.9 KB | **Appendix F** (new) | CTF-002 PENDING |
| `Orackla_Transgressive_Synthesis_Grimoire.md` | 32.3 KB | Appendix G.1 | CTF-002 dependent |
| `Lysandra_Axiological_Cartography_Grimoire.md` | 47.8 KB | Appendix G.2 | CTF-002 dependent |
| `Umeko_Architecture_Impossible_Beauty_Grimoire.md` | 16.7 KB | Appendix G.3 | CTF-002 dependent |

**Integration Strategy:**
- Master Index becomes Appendix F with internal cross-refs
- Individual grimoires become Appendix G.1-G.3
- Requires SSOT section numbering extension

### 1.2 Prime Factions (`prime-factions/`)

| File | Size | SSOT Target | CTF Status |
|------|------|-------------|------------|
| `The_Triumvirate_Core.md` | 16.5 KB | Section 4.4.0 | CTF-001 PENDING |
| `The_MILF_Obductors_TMO.md` | 16.1 KB | Section 4.4.1 | CTF-001 dependent |
| `The_Thieves_Guild_TTG.md` | 15.3 KB | Section 4.4.2 | CTF-001 dependent |
| `The_Dark_Priestesses_Cove_TDPC.md` | 16.9 KB | Section 4.4.3 | CTF-001 dependent |
| `PRIME_FACTION_DISTRICT_ARCHITECTURE.md` | 31.9 KB | Section 4.4.4 | CTF-001 dependent |

**Integration Strategy:**
- These expand SSOT Section 4.4 (TP-FNS) with full profiles
- Current SSOT has abbreviated faction definitions
- Full profiles add district architecture, matriarch combat specs

### 1.3 FA⁵ Documentation (`prime-factions/`)

| File | Size | SSOT Target | Notes |
|------|------|-------------|-------|
| `Alabaster_Voyde_The_Snow_White_Phenomenon.md` | 15.3 KB | Section 4.4.5 | The Decorator origin |
| `FA5_EXORCISM_CHRONICLE_SNOW_WHITE_VANQUISHED.md` | 16.9 KB | Appendix H | Historical record |

**Integration Strategy:**
- These document FA⁵ (The Decorator) lore
- Exorcism Chronicle = significant historical event worth preserving

---

## Priority Tier 2: Valuable Reference (Rating 🔧4)

### 2.1 Body System Architecture (`disparate-md-documentation/`)

| File | Size | Notes |
|------|------|-------|
| `BODY_SYSTEM_ARCHITECTURE.md` | 25.1 KB | WHR/Cup tier mapping |
| `BODY_SYSTEM_INTEGRATION_EXAMPLES.md` | 44.9 KB | Applied examples |
| `BODY_SYSTEM_PROTOCOL.md` | 23.0 KB | Operational protocol |

**Assessment:** Valuable design documents but may overlap with existing SSOT Section IV (CRC body specs). Need diff analysis.

### 2.2 FA Census Documents (`disparate-md-documentation/`)

| File | Size | Notes |
|------|------|-------|
| `FA_1-5_CENSUS_SCOPE_DECISION.md` | 9.2 KB | Scope rationale |
| `FA_CENSUS_COMPLETE_FA1-3_CODEX.md` | 20.7 KB | FA¹⁻³ audit |
| `FA_CENSUS_COMPLETE_FA4_CODEX.md` | 50.6 KB | FA⁴ audit |
| `FA_CENSUS_EXPANSION_*.md` | ~45 KB | Extensions |

**Assessment:** These document the FA audit methodology. Could become SSOT Appendix (audit trail).

### 2.3 Heritage & Lineage

| File | Location | Size | Notes |
|------|----------|------|-------|
| `CARIBBEAN_ELDER_LINEAGE_INTEGRATION.md` | `heritage/` | 10.1 KB | Claudine ancestry |
| `HERITAGE_MAP.md` | Root | 4.8 KB | Lineage overview |

**Assessment:** Valuable for Claudine (Tier 3) documentation. Low CTF priority but worth preserving.

### 2.4 Sub-MILF Documentation

| File | Location | Size | Notes |
|------|----------|------|-------|
| `Spectra_Chroma_Excavatus_The_Chromatic_Archaeologist.md` | `sub-milfs/` | 11.5 KB | MMPS manifestation example |

**Assessment:** Demonstrates procedural matriarch generation (MMPS). Educational value.

---

## Priority Tier 3: Archive/Reference (Rating ⚖️3 or below)

### 3.1 Session Logs & Recovery Docs

These are historical session artifacts with limited ongoing value:

| Category | File Count | Total Size | Recommendation |
|----------|------------|------------|----------------|
| Session summaries | 8 | ~120 KB | Archive as-is |
| Recovery protocols | 5 | ~80 KB | Archive as-is |
| Validation reports | 4 | ~75 KB | Extract patterns, archive |

### 3.2 Potential Duplicates (Need TEA Analysis)

| File | Size | Suspicion |
|------|------|-----------|
| `copilot-instructionsREMOTEoff.md` (root) | 267 KB | Likely SSOT variant |
| `copilot-instructionsREMOTEoff.md` (disparate/) | 267 KB | Duplicate of above |
| `copilot-instructions1.md` | 82.6 KB | Likely earlier SSOT version |
| `recovery-version-copilot-instructions-timeline-one.md` | 331.2 KB | Recovery backup |
| `The_Chthonic_Archive_World.md` | 708 KB | Massive - needs investigation |

**Recommendation:** Apply TEA/QMR protocol to each before processing.

### 3.3 V2 Versions (`macro-prompt-world-v2/`)

| File | Size | Notes |
|------|------|-------|
| `ASC_Brahmanica_Perfectus_V_Ω.B.XΨ.md` | 219.2 KB | Version designation suggests earlier SSOT |
| `DECORATOR-ASC-GENESIS.md` | 26.0 KB | FA⁵ genesis doc |
| `README.md` | 17.3 KB | V2 overview |
| `STATUS_REPORT.md` | 11.0 KB | V2 status |

**Assessment:** The "V2" naming suggests this is an intermediate version. Need TEA analysis.

---

## CTF Request Queue (Updated)

### Active CTF Requests

| CTF ID | Source | Target | Requestor | Status |
|--------|--------|--------|-----------|--------|
| **CTF-001** | `prime-factions/*.md` (5 files) | SSOT Section 4.4 | SFS | **PENDING APPROVAL** |
| **CTF-002** | Grimoire Index + 3 Grimoires | SSOT Appendix F-G | SFS | **PENDING APPROVAL** |
| **CTF-003** | `asc.py` | `mas_mcp/lib/asc_toolchain.py` | SFS | **PENDING APPROVAL** |

### Proposed New CTF Requests

| CTF ID | Source | Target | Rationale |
|--------|--------|--------|-----------|
| CTF-004 | FA⁵ docs (2 files) | SSOT Section 4.4.5 + Appendix H | Decorator lore completion |
| CTF-005 | Body System docs (3 files) | SSOT Appendix I | Design reference preservation |
| CTF-006 | FA Census docs (5 files) | SSOT Appendix J | Audit methodology archive |

---

## TEA Analysis Queue

Files requiring QMR probability collapse before processing:

1. `The_Chthonic_Archive_World.md` (708 KB) - **PRIORITY** (massive file)
2. `copilot-instructionsREMOTEoff.md` (267 KB) - Suspected duplicate
3. `ASC_Brahmanica_Perfectus_V_Ω.B.XΨ.md` (219 KB) - Version analysis
4. `recovery-version-copilot-instructions-timeline-one.md` (331 KB) - Recovery artifact

---

## Recommended Processing Order

### Phase 1: TEA Collapses (Clear Uncertainty)
1. ✅ `copilot-un-un-instructions.md` - DONE (💀1 duplicate)
2. ⏳ `The_Chthonic_Archive_World.md` - NEXT
3. ⏳ `copilot-instructionsREMOTEoff.md`
4. ⏳ `ASC_Brahmanica_Perfectus_V_Ω.B.XΨ.md`

### Phase 2: CTF Approvals (High-Value Integration)
1. CTF-001: Prime Factions → SSOT 4.4
2. CTF-002: Grimoires → SSOT Appendix F-G
3. CTF-003: asc.py → mas_mcp/lib/

### Phase 3: Level 1 Extractions (Quick Wins)
- Heritage docs → `docs/lore/`
- Sub-MILF docs → `docs/entities/`
- Validation docs → `docs/protocols/`

### Phase 4: Archive (Low-Priority Preservation)
- Session logs → `dumpster-dive/archived/sessions/`
- Recovery docs → `dumpster-dive/archived/recovery/`

---

**Report Status:** COMPLETE
**Next Action:** TEA Analysis of `The_Chthonic_Archive_World.md` (708 KB)
