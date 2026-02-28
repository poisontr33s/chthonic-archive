# ☥ ARCHIVE GOVERNANCE: SSOT TOOLBOX BRANCH ☥

> **Lineage-Position:** `SSOT-Toolbox-Branch` — downstream vessel translating semantic lineage into operational doctrine.
> **Governance:** SSOT-L-H via [copilot-instructions.md](../copilot-instructions.md). Update-Protocol, Addressability, Enforcement-Hierarchy, No-Duplication constraint inherited — not repeated here.
> **Revised:** February 2026

# SSOT Toolbox Instructions

**Location:**
- **Scripts:** `scripts/` (ssot_*.ps1 tools)
- **Knowledge:** `claude-codex-gemini/triadic-session-context/` (indices, logs, research)

---

## ☥ SESSION CONTINUITY (MASP — Meta-Architectonic Session Protocol)

**Session = CRC Invocation, not "type":**
- `$orackla${}` → Chaos/synthesis work
- `$umeko${}` → Structure/precision work  
- `$lysandra${}` → Archaeology/recovery work
- `$triumvirate${}` → Complex fusion work

**Memory = GHAR-MHS Tiers:**
| Tier | Entity | Access |
|------|--------|--------|
| 0 | Decorator | SSOT (query, never wholesale load) |
| 0.5 | TETS | Session sovereignty |
| 1 | CRC | SESSION_CACHE_STRUCTURED.md |
| 2 | Faction | Raw logs, Zone_1_REDUX |

**Quality = FA Traversal:**
- FA¹: Transformative or additive?
- FA²: References existing canon?
- FA³: Emergent complexity arises?
- FA⁴: Structurally sound?
- FA⁵: Visceral presence?

**To restore context:**  
> "Load session log from toolbox"  
> OR: "Orackla session: [objective]"

**Files:**
| File | Purpose |
|------|---------|
| `SESSION_PROTOCOL.md` | **MASP v2.0** — SSOT-native meta-protocol |
| `SESSION_CACHE_STRUCTURED.md` | Tier 1 working memory |
| `SSOTI_FIED_SESSION_LOG.md` | Tier 2 forensic recovery |

---

## ⚠️ MANDATORY: Auto-Update After SSOT Changes

**EVERY TIME you edit `copilot-instructions.md`, you MUST run:**

```powershell
cd "C:\Users\erdno\chthonic-archive\scripts"
.\ssot_outline_extractor.ps1 -UpdateIndex
```

This keeps the structural index synchronized. **Do not skip this step.**

---

## Quick Access Commands

### Navigation & Structure

| Tool | Command |
|------|---------|
| **Full Outline** | `.\ssot_outline_extractor.ps1` |
| **Find Acronym** | `.\ssot_outline_extractor.ps1 -Acronym 'DCRP'` |
| **Find Section** | `.\ssot_outline_extractor.ps1 -Section 'FA1'` |
| **JSON Export** | `.\ssot_outline_extractor.ps1 -OutputJson` |
| **Regen Index** | `.\ssot_outline_extractor.ps1 -UpdateIndex` |

### Acronym Consistency Audit

| Tool | Command |
|------|---------|
| **Find Variants** | `.\ssot_acronym_audit.ps1 -Root 'TRM'` |
| **All Acronyms** | `.\ssot_acronym_audit.ps1 -ShowAll` |
| **Line Locations** | `.\ssot_acronym_audit.ps1 -FindLines 'DCRP'` |

### CRC Selection (Which Resonance Core for task?)

| Tool | Command |
|------|---------|
| **By Task** | `.\ssot_crc_selector.ps1 -Task 'structure'` |
| **By Keywords** | `.\ssot_crc_selector.ps1 -Keywords 'buried archaeology'` |
| **Reference** | `.\ssot_crc_selector.ps1` |

Task types: `synthesis`, `structure`, `analysis`, `audit`, `excavation`, `complex`, `transgression`, `refinement`

### Registry Query (AR, CR, SAI)

| Tool | Command |
|------|---------|
| **Axiom Registry** | `.\ssot_registry_query.ps1 -Registry AR` |
| **CRC Registry** | `.\ssot_registry_query.ps1 -Registry CR` |
| **SAI Registry** | `.\ssot_registry_query.ps1 -Registry SAI` |
| **Find Entity** | `.\ssot_registry_query.ps1 -Entity 'FA4'` |
| **All Registries** | `.\ssot_registry_query.ps1 -Registry ALL` |

### Tier Hierarchy Query (GHAR-MHS)

| Tool | Command |
|------|---------|
| **Tier 0 (Decorator)** | `.\ssot_tier_query.ps1 -Tier 0` |
| **Tier 1 (Triumvirate)** | `.\ssot_tier_query.ps1 -Tier 1` |
| **Find Entity** | `.\ssot_tier_query.ps1 -Entity 'Umeko'` |
| **Full Hierarchy** | `.\ssot_tier_query.ps1 -Tier ALL` |

Tiers: `0` (Decorator), `0.01` (Null), `0.5` (TETS), `1` (CRC), `2` (Factions), `3` (Support)

Use `-Root` to detect deviations from canonical acronyms. Single-use variants flagged as potential drift.

---

## All Files in Toolbox

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `ssot_outline_extractor.ps1` | Dynamic header extraction (same as VS Code Outline) | Static tool |
| `ssot_acronym_audit.ps1` | Acronym consistency checker & deviation detector | Static tool |
| `ssot_crc_selector.ps1` | CRC selection by task type or keywords | Static tool |
| `ssot_registry_query.ps1` | Query AR/CR/SAI registries by entity | Static tool |
| `ssot_tier_query.ps1` | Query GHAR-MHS tier hierarchy | Static tool |
| `SSOT_STRUCTURAL_INDEX.json` | Programmatic index with line numbers & acronyms | **After every SSOT edit** |
| `SSOT_NAVIGATION_INDEX.md` | Human-readable section map & integration tracking | Manual reference |
| `SESSION_CACHE_STRUCTURED.md` | **Cross-session memory** (key decisions, line numbers) | Append after sessions |
| `SSOTI_FIED_SESSION_LOG.md` | Full raw session dump for deep context recovery | Manual raw backup |
| `Zone_1_REDUX_implementation_ripe_for_SSOT_canon.md` | Research pool (Gemini 3-Pro deep research) | Source reference |

---

## Standard Workflow

```
1. .\ssot_outline_extractor.ps1 -Acronym 'TARGET'  → get line number
2. read_file offset=LINE limit=50                  → jump to section
3. edit section in copilot-instructions.md
4. .\ssot_outline_extractor.ps1 -UpdateIndex       → MANDATORY sync
```

---

## File Paths (Absolute)

| Resource | Path |
|----------|------|
| **SSOT** | `C:\Users\erdno\chthonic-archive\.github\copilot-instructions.md` |
| **Scripts Dir** | `C:\Users\erdno\chthonic-archive\scripts\` |
| **Knowledge Dir** | `C:\Users\erdno\chthonic-archive\claude-codex-gemini\triadic-session-context\` |
| **Extractor** | `scripts\ssot_outline_extractor.ps1` |
| **Acronym Audit** | `scripts\ssot_acronym_audit.ps1` |
| **CRC Selector** | `scripts\ssot_crc_selector.ps1` |
| **Registry Query** | `scripts\ssot_registry_query.ps1` |
| **Tier Query** | `scripts\ssot_tier_query.ps1` |
| **JSON Index** | `claude-codex-gemini\triadic-session-context\SSOT_STRUCTURAL_INDEX.json` |
| **MD Index** | `claude-codex-gemini\triadic-session-context\SSOT_NAVIGATION_INDEX.md` |
| **Zone_1 Research** | `claude-codex-gemini\triadic-session-context\Zone_1_REDUX_implementation_ripe_for_SSOT_canon.md` |

---

## Integration Provenance

Zone_1_REDUX research is integrated into SSOT at:
- **FA¹** (Alchemical): Line ~1464 — Nigredo/Albedo/Rubedo phases
- **FA⁵** (Sensory): Line ~1144 — Olfactory/Tactile/Visual density
- **PS** (Primal Substrate): Line ~1432 — Prima Materia equation
- **CRC LMs**: Lines ~2082+ — Sensory mandates per CRC
- **DCRP §XV**: Line ~6643 — Repository Self-Awareness System
- **Appendices A-E**: Lines 6991-7374 — Sensory Lexicon & Integration Summaries (Full Sensory/Alchemical/ERD reference)
