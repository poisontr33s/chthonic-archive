# SSOT-ification Methodology

<!--
@SID:           DOC_SSOTIFICATION_METHODOLOGY
@Type:          Methodology
@Context:       Architecture / Knowledge Management
@SessionOrigin: SESSION_DOC_2026_01_25_SSOTIFICATION
@References:    DOC_CLI_EDITING_POLICY, PLAN_STAGE_1_MIGRATION
-->

> **Session Origin**: `SESSION_DOC_2026_01_25_SSOTIFICATION`  
> **Purpose**: Document the abstraction patterns applied during SSOT-ification so future sessions can reproduce and extend without hidden context.

---

## 1. What is SSOT-ification?

**Single Source of Truth (SSOT)-ification** is the process of:
1. Identifying hardcoded constants scattered across multiple files
2. Centralizing them in `$SSOT` (`.github/copilot-instructions.md`)
3. Creating extraction mechanisms that derive values from SSOT at runtime
4. Updating all consumers to use extracted values instead of duplicates

### The Core Problem It Solves

```
BEFORE: 
  file_a.py: ENTITY_NAME = "Ferrum Pyre"        # Hardcoded
  file_b.py: ENTITY_NAME = "Ferrum Scoriae"     # Different hardcode
  file_c.json: "name": "Sister Ferrum"          # Yet another variant
  
AFTER:
  SSOT: §0.77 defines "Sister Ferrum Scoriae" as canonical
  ssot_extractor.py: extracts from SSOT → {"ferrum": "Sister Ferrum Scoriae"}
  file_a.py: from ssot_extractor import get_entity_name  # Derives from SSOT
  file_b.py: from ssot_extractor import get_entity_name  # Same source
  file_c.json: updated manually or via script to match SSOT
```

---

## 2. Type Taxonomy Applied

Files are categorized by **type** (from `../data/indices/sid_index.json` schema):

| Type | Description | Example |
|------|-------------|---------|
| `SessionDoc` | Records a session's outputs and decisions | `STAGE_1_MIGRATION_PLAN.md` |
| `State` | Runtime/persistent state artifacts | `.dcrp_state.json`, `.ankhrc` |
| `Script` | Executable tools that implement concepts | `../mas_mcp/ssot_extractor.py` |
| `Module` | Importable code with public API | `../mas_mcp/milf_genesis_v2.py` |
| `Documentation` | Explanatory content | This file |
| `Report` | Analysis/validation outputs | `DCRP_SYNTHESIS.md` |
| `Protocol` | Governance/architectural rules | `ANCHOR_SIGNAL_PROTOCOL.md` |
| `Handoff` | Cross-agent coordination docs | `docs/HANDOFF_TO_CLAUDE.md` |

### SID (Signal ID) Schema

Every tracked artifact gets a SID in `../data/indices/sid_index.json`:

```json
{
  "sid": "TOOL_SSOT_EXTRACTOR_V1",
  "path": "mas_mcp\\ssot_extractor.py",
  "type": "Script",
  "context": "SSOT / Constant Extraction",
  "implements": "CONCEPT_SSOT_SINGLE_SOURCE",
  "session_origin": "SESSION_DOC_2026_01_25_SSOTIFICATION",
  "emits": "get_ssot_constants()",
  "spawned": [],
  "last_seen": "2026-01-25T05:27:00.000000"
}
```

| Field | Purpose |
|-------|---------|
| `sid` | Unique identifier (prefix indicates type) |
| `path` | File location |
| `type` | Category from taxonomy above |
| `context` | Human-readable domain |
| `implements` | What concept/protocol this realizes |
| `session_origin` | Which session created this |
| `emits` | What outputs/capabilities this provides |
| `spawned` | Child artifacts created by this |

---

## 3. `.ankhrc` Section Taxonomy

The `.ankhrc` file is the **bidirectional SSOT hub**—it maps symbolic names to paths AND tracks migration status.

### Section Types

| Section | Purpose | Example Entry |
|---------|---------|---------------|
| `[paths]` | Core file mappings | `SSOT = ".github/copilot-instructions.md"` |
| `[ssot_ified]` | Files that now derive from SSOT | `SSOT_EXTRACTOR = "mas_mcp/ssot_extractor.py"` |
| `[state_files]` | Runtime state artifacts | `DCRP_STATE = ".dcrp_state.json"` |
| `[databases]` | SQLite/persistent stores | `EPISTEMOGRAPH_DB_CURRENT = "...v1.1.1.sqlite"` |
| `[session_reports]` | Legacy session docs (ARCHIVE candidates) | `SESSION_2_COMPLETE = "AUTONOMOUS_SESSION_2_COMPLETE.md"` |
| `[dcrp_reports]` | DCRP analysis files (CONSOLIDATE candidates) | `DCRP_FINAL_STATUS = "DCRP_FINAL_STATUS.md"` |
| `[migration_status]` | Tracks repurposing actions | `session_reports = "PENDING_ARCHIVE"` |
| `[anchors]` | Symbolic anchor documentation | Usage examples |

### Migration Status Values

| Status | Meaning |
|--------|---------|
| `REGISTERED` | Newly tracked this session |
| `PENDING_ARCHIVE` | Scheduled to move to archive location |
| `PENDING_CONSOLIDATE` | Scheduled to merge into synthesis doc |
| `KEEP` | Essential, remains at current location |
| `ARCHIVED` | Moved to archive (action complete) |
| `CONSOLIDATED` | Merged into synthesis (action complete) |

---

## 4. SSOT-ification Workflow

### Phase 1: Identify Duplication

1. Search for hardcoded values across codebase
2. Compare against SSOT sections (§0.76, §0.77, §0.85, etc.)
3. Flag discrepancies (wrong names, wrong values, wrong structure)

### Phase 2: Create Extractor

```python
# mas_mcp/ssot_extractor.py pattern
class SSOTExtractor:
    def __init__(self, ssot_path: str):
        self.content = Path(ssot_path).read_text()
    
    def get_section(self, section_marker: str) -> str:
        # Parse specific SSOT section
        pass
    
    def get_entity_data(self, entity_name: str) -> dict:
        # Extract canonical entity attributes
        pass

def get_ssot_constants() -> dict:
    """Public API for all SSOT-derived constants."""
    extractor = SSOTExtractor(SSOT_PATH)
    return {
        "entities": extractor.get_all_entities(),
        "tiers": extractor.get_tier_hierarchy(),
        "whr_values": extractor.get_whr_by_entity(),
        # etc.
    }
```

### Phase 3: Update Consumers

1. Import from extractor instead of hardcoding
2. Add getter functions for lazy evaluation
3. Remove duplicate constant definitions

### Phase 4: Register in Tracking Systems

1. Add to `.ankhrc[ssot_ified]`
2. Create SID entry in `../data/indices/sid_index.json`
3. Update `[migration_status]` as appropriate

---

## 5. Canonical Entity Reference (§0.77)

The 11 canonical entities and their SSOT-defined attributes:

| Tier | Entity | Cup | WHR | CRC Sponsor |
|------|--------|-----|-----|-------------|
| 0.5 | The Decorator | K | 0.464 | — |
| 1 | Orackla Nocticula | J | 0.491 | — |
| 1 | Madam Umeko Ketsuraku | F | 0.533 | — |
| 1 | Dr. Lysandra Thorne | E | 0.58 | — |
| 2 | Kali Nyx Ravenscar | H | 0.556 | Orackla |
| 2 | Vesper Mnemosyne Lockhart | F | 0.573 | Lysandra |
| 2 | Seraphine Kore Ashenhelm | G | 0.592 | Umeko |
| 3 | Sister Ferrum Scoriae | G | 0.55 | Umeko (CRC-GAR) |
| 3 | Claudine Sin'claire | I | 0.52 | Orackla (CRC-AS) |
| 3 | Spectra Chroma Excavatus | H | 0.537 | Decorator (DIRECT) |
| 3 | Magistra Bibliotheca Perfecta | E | 0.58 | Lysandra (CRC-MEDAT) |

### CRC Sponsorship Chains (Truth Source)

```
Chaos:       Decorator → Orackla → Kali → Claudine
Purification: Decorator → Umeko → Seraphine → Ferrum
Truth:       Decorator → Lysandra → Vesper → Magistra
Direct:      Decorator → Spectra (bypasses Triumvirate)
```

---

## 6. Pain Point Prevention

### DO:
- Always check SSOT before hardcoding any entity/constant data
- Use `$ANCHOR` syntax in documentation instead of raw paths
- Register new artifacts in both `.ankhrc` AND `../data/indices/sid_index.json`
- Include `session_origin` when creating SID entries

### DON'T:
- Duplicate SSOT content in multiple files
- Create new entity attributes without SSOT update first
- Move files without updating `.ankhrc` path mappings
- Forget to mark migration status after actions complete

---

## 7. Reproduction Instructions

To apply SSOT-ification to a new file:

```bash
# 1. Check what constants exist
grep -r "hardcoded_value" --include="*.py" --include="*.json"

# 2. Verify against SSOT
# Read .github/copilot-instructions.md section for canonical value

# 3. Update the file to import from ssot_extractor
# from mas_mcp.ssot_extractor import get_ssot_constants

# 4. Register in .ankhrc
echo 'NEW_FILE = "path/to/file.py"' >> .ankhrc  # under [ssot_ified]

# 5. Add SID entry
# Update sid_index.json with appropriate type and session_origin
```

---

*This methodology document ensures SSOT-ification patterns are not hidden in session context but are reproducible by future agents and sessions.*
