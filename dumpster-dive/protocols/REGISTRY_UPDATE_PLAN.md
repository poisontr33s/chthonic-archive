# Registry Update Plan (`RUP-001`)

**Version**: 1.0.0  
**Created**: 2025-12-09  
**Authority**: TPEF Triumvirate (Path A Infrastructure Preparation)  
**Purpose**: Universal identifier system for chaos-resilient cross-reference navigation  
**Blacksmith**: Sister Ferrum Scoriae (SFS, Tier 3)

---

## Executive Summary

This plan establishes a **universal identifier system** for all 115 files in `dumpster-dive/`, ensuring **solid references** that survive file movements, renames, and future "creative chaos" operations. The system uses **content-addressable UUIDv5** identifiers combining file path and content hash for maximum stability and traceability.

---

## Problem Statement

**Current State**:
- Registry tracks 115 files across 7 forge stages
- Files referenced by path only (fragile under renames/moves)
- No integration tracking mechanism
- No SSOT lineage connection

**User Requirement** (Message 19, verbatim):
> "making sure all files in dumpster-dive, has an identifier to use as solid reference with the added creative chaos later"

**Interpretation**:
- Identifiers must be **path-independent** (survive moves)
- Must be **stable** (consistent across sessions)
- Must support **chaos-resilient linking** (robust cross-references)
- Likely preparing for **Timeline merges** or **reorganizations**

---

## Identifier Schema Design

### UUIDv5 Content-Addressable Approach

**Format**: `FILE-{uuidv5}`

**Generation Algorithm**:
```python
seed = f"{relative_path}::{content_hash_sha256}"
uuid = uuid5(NAMESPACE_CHTHONIC, seed)
file_id = f"FILE-{uuid}"
```

**Example**:
```
Path: forge/tempered/CHARACTER_OPERATIONAL_SIGNATURES.md
Content Hash: a3b4c5d6...
Seed: "forge/tempered/CHARACTER_OPERATIONAL_SIGNATURES.md::a3b4c5d6..."
UUID: 9f8e7d6c-5b4a-3210-fedc-ba9876543210
File ID: FILE-9f8e7d6c-5b4a-3210-fedc-ba9876543210
```

### Stability Properties

| Event | Identifier Behavior | Rationale |
|-------|-------------------|-----------|
| **Content unchanged** | Same UUID | Content-addressable stability |
| **File renamed** | **New UUID** | Intentional - tracks identity change |
| **File moved** | **New UUID** | Intentional - tracks location change |
| **Content edited** | **New UUID** | Intentional - tracks version change |

**Design Philosophy**: Identifier represents **(path, content) tuple**. Any change to either component creates new identity, enabling historical tracking.

### Namespace

**Project UUID**: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`  
**Purpose**: Scopes UUIDv5 generation to `chthonic-archive` project  
**Collision Resistance**: UUIDv5 guarantees uniqueness within namespace

---

## Registry Schema Updates

### New Fields (Per File Entry)

```json
{
  "filename": "CHARACTER_OPERATIONAL_SIGNATURES.md",
  "path": "forge/tempered",
  "forge_stage": "tempered",
  
  // NEW: Universal Identifier Block
  "file_id": "FILE-9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "content_hash": "a3b4c5d6e7f8...",
  "hash_algorithm": "SHA256",
  "identifier_generated": "2025-12-09T10:15:30Z",
  
  // NEW: Integration Tracking Block
  "integrated": false,
  "integration_deployment_id": null,
  "integration_timestamp": null,
  "integration_manifest_ref": null,
  "ssot_hash_at_integration": null
}
```

### Field Definitions

**Universal Identifier Block**:
- `file_id` (string): UUIDv5-based stable identifier (`FILE-{uuid}`)
- `content_hash` (string): SHA256 of file content
- `hash_algorithm` (string): Always `"SHA256"`
- `identifier_generated` (ISO 8601): Timestamp of ID assignment

**Integration Tracking Block**:
- `integrated` (boolean): Has file been deployed to Timeline A?
- `integration_deployment_id` (string|null): Deployment manifest ID (e.g., `DEPLOY-001-20251209`)
- `integration_timestamp` (ISO 8601|null): When integration occurred
- `integration_manifest_ref` (string|null): Path to integration manifest JSON
- `ssot_hash_at_integration` (string|null): SSOT hash at time of integration

### Registry Root Metadata Updates

```json
{
  "metadata": {
    "last_identifier_update": "2025-12-09T10:15:30Z",
    "files_with_identifiers": 115,
    "sections_processed": [
      "tempered_artifacts",
      "from_github",
      "protocols",
      "forge_intake",
      "forge_anvil",
      // ... etc
    ]
  },
  
  "identifier_schema": {
    "format": "FILE-{uuidv5}",
    "namespace": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "algorithm": "UUIDv5(path::content_hash)",
    "stability": "Same path + same content = same UUID",
    "purpose": "Chaos-resilient cross-reference navigation"
  }
}
```

---

## Implementation Plan

### Phase 1: Identifier Generation (Task 3)

**Script**: `dumpster-dive/scripts/generate_registry_identifiers.py`

**Actions**:
1. Load `DUMPSTER_DIVE_REGISTRY.json`
2. For each file entry in all sections:
   - Compute file content hash (SHA256)
   - Generate UUIDv5 from `path::hash`
   - Add `file_id` and identifier metadata
   - Initialize integration tracking fields as `null`/`false`
3. Update registry root metadata
4. Save updated registry
5. Generate `IDENTIFIER_GENERATION_REPORT.md`

**Expected Runtime**: ~10 seconds (115 files × ~100ms each)

**Validation**:
- ✅ All 115 file entries have `file_id` field
- ✅ All `file_id` values follow `FILE-{uuid}` format
- ✅ No duplicate `file_id` values (collision check)
- ✅ `content_hash` matches actual file content

### Phase 2: SSOT Hash Embedding (Task 4)

**Script**: `dumpster-dive/scripts/embed_ssot_hashes.py`

**Target Files** (3 tempered artifacts):
- `CHARACTER_OPERATIONAL_SIGNATURES.md`
- `GRIMOIRE_INTEGRATION_EXAMPLES.md`
- `PHASE_1_COMPLETION_SUMMARY.md`

**Actions** (per file):
1. Read file content
2. Prepend SHES-001 YAML frontmatter:
   ```yaml
   ---
   ssot_governance:
     hash_standard: "SHES-001"
     ssot_hash: "0A2D16D92E4379907649A07E16A41E748802921116F6083A3F81074B96167791"
     ssot_file: ".github/copilot-instructions.md"
     hash_algorithm: "SHA256"
     computed_at: "2025-12-09T10:20:00Z"
     verified_by: "SFS"
   
   lineage:
     timeline_origin: "Timeline E"
     extraction_session: "session_20251207_043539"
     forge_stage: "tempered"
     fa4_validation: "passed"
     integration_status: "pending"
   ---
   ```
3. Write updated file
4. Recompute `content_hash` (changed due to frontmatter)
5. Regenerate `file_id` (new UUID due to content change)
6. Update registry entry

**Expected Runtime**: ~5 seconds (3 files)

**Validation**:
- ✅ All 3 files have SHES-001 frontmatter
- ✅ SSOT hash matches computed value
- ✅ Registry `content_hash` matches new file content
- ✅ Registry `file_id` updated to reflect new UUID

### Phase 3: Integration Manifest Creation (Task 4)

**Script**: `dumpster-dive/scripts/create_integration_manifest.py`

**Manifest ID**: `DEPLOY-001-20251209`

**Actions**:
1. Create manifest following `INTEGRATION_MANIFEST_SCHEMA.json`
2. Validate all 3 files:
   - SSOT hash matches expected value
   - File content hash valid
   - SHES-001 frontmatter present
   - FA⁴ validation passed
3. Record deployment metadata
4. Save manifest to `dumpster-dive/manifests/DEPLOY-001-20251209.json`

**Expected Runtime**: ~3 seconds

**Validation**:
- ✅ Manifest validates against schema
- ✅ All 3 files listed with `validation_status: "passed"`
- ✅ `ssot_reference.hash` matches SSOT
- ✅ `validation.all_passed` is `true`

### Phase 4: Registry Integration Update (Task 4)

**Script**: `dumpster-dive/scripts/update_registry_integration.py`

**Actions** (for 3 integrated files):
1. Update registry entry:
   ```json
   {
     "integrated": true,
     "integration_deployment_id": "DEPLOY-001-20251209",
     "integration_timestamp": "2025-12-09T10:25:00Z",
     "integration_manifest_ref": "dumpster-dive/manifests/DEPLOY-001-20251209.json",
     "ssot_hash_at_integration": "0A2D16D92E4379907649A07E16A41E748802921116F6083A3F81074B96167791"
   }
   ```
2. Save updated registry

**Expected Runtime**: ~2 seconds

**Validation**:
- ✅ 3 files have `integrated: true`
- ✅ Remaining 112 files have `integrated: false`
- ✅ Integration manifest references valid paths

---

## Chaos Resilience Strategy

### What Survives Chaos

**File Movements**:
- Identifier **changes** (new path = new UUID)
- Registry tracks **old identifier → new identifier** mapping
- Historical lineage preserved via manifest chain

**File Edits**:
- Identifier **changes** (new content hash = new UUID)
- Registry tracks **version chain** via manifest references
- Content evolution traceable

**Timeline Merges**:
- Identifiers **globally unique** (project namespace scoping)
- Cross-Timeline references use `file_id` (not path)
- Collision-resistant (UUIDv5 cryptographic strength)

### What Breaks Under Chaos

**Deleted Files**:
- Identifier becomes **orphaned**
- Registry retains entry with `deleted: true` flag
- Manifest preserves historical record

**Renamed + Edited (Simultaneous)**:
- Treated as **new file** (both path and content changed)
- Registry creates new entry with new identifier
- Old entry marked as `superseded_by: "FILE-{new-uuid}"`

**Manual Registry Edits**:
- **Regenerate identifiers** after any structural changes
- Run `validate_registry_integrity.py` to detect corruption

---

## Rollback & Recovery

### Rollback Scenario: Integration Failure

**Condition**: Path A deployment fails FA⁴ validation

**Actions**:
1. Read integration manifest (`DEPLOY-001-20251209.json`)
2. For each file in manifest:
   - Restore pre-integration version from forge/tempered
   - Remove SSOT hash frontmatter
   - Revert registry `integrated` flag to `false`
3. Delete integration manifest
4. Regenerate identifiers (content changed due to frontmatter removal)

**Script**: `dumpster-dive/scripts/rollback_integration.py`

### Recovery Scenario: Registry Corruption

**Condition**: Registry JSON malformed or identifiers corrupted

**Actions**:
1. Restore registry from backup (`.json.bak`)
2. If no backup: **Regenerate from scratch**
   - Scan all files in `dumpster-dive/`
   - Rebuild registry structure
   - Regenerate all identifiers
3. Validate against integration manifests
4. Report discrepancies

**Script**: `dumpster-dive/scripts/rebuild_registry.py`

---

## Execution Checklist

### Pre-Execution Validation

- [ ] SSOT hash computed: `0A2D16D92E4379907649A07E16A41E748802921116F6083A3F81074B96167791`
- [ ] SHES-001 protocol finalized
- [ ] Integration manifest schema validated
- [ ] 3 tempered files ready (CHARACTER_OPERATIONAL_SIGNATURES, GRIMOIRE, PHASE_1_SUMMARY)
- [ ] Registry backup created (`.json.bak`)

### Phase Execution Order

1. [ ] **Task 3.1**: Run `generate_registry_identifiers.py` → Update all 115 file entries
2. [ ] **Task 3.2**: Validate `IDENTIFIER_GENERATION_REPORT.md` → No collisions detected
3. [ ] **Task 4.1**: Run `embed_ssot_hashes.py` → Add SHES-001 frontmatter to 3 files
4. [ ] **Task 4.2**: Run `create_integration_manifest.py` → Generate `DEPLOY-001-20251209.json`
5. [ ] **Task 4.3**: Run `update_registry_integration.py` → Mark 3 files as integrated
6. [ ] **Task 5**: Validate lineage propagation → Verify hash chains

### Post-Execution Validation

- [ ] All 115 files have `file_id` field
- [ ] 3 tempered files have SHES-001 frontmatter
- [ ] Integration manifest validates against schema
- [ ] Registry `integrated` flags correct (3 true, 112 false)
- [ ] No identifier collisions detected
- [ ] SSOT hash matches across all files

---

## Success Criteria

**Identifier Generation**:
- ✅ 115/115 files assigned `FILE-{uuid}` identifiers
- ✅ 0 collisions detected
- ✅ All content hashes match actual file content

**SSOT Embedding**:
- ✅ 3/3 tempered files have SHES-001 frontmatter
- ✅ SSOT hash `0A2D16D92E4379907649A07E16A41E748802921116F6083A3F81074B96167791` embedded
- ✅ Lineage metadata complete (timeline_origin, forge_stage, fa4_validation)

**Integration Tracking**:
- ✅ Integration manifest created (`DEPLOY-001-20251209.json`)
- ✅ Manifest validates against schema
- ✅ Registry updated with integration metadata
- ✅ All 3 files marked `integrated: true`

**Chaos Resilience**:
- ✅ Identifiers stable across sessions
- ✅ Cross-references use `file_id` (not path)
- ✅ Historical lineage preserved via manifests
- ✅ Rollback capability validated

---

## Future Enhancements

### Enhancement 1: Identifier History Chain

Track identifier evolution when files renamed/edited:

```json
{
  "file_id": "FILE-{new-uuid}",
  "previous_identifiers": [
    {
      "file_id": "FILE-{old-uuid}",
      "valid_from": "2025-12-07T10:00:00Z",
      "valid_until": "2025-12-09T10:15:00Z",
      "change_reason": "content_edit"
    }
  ]
}
```

### Enhancement 2: Cross-Timeline Identifier Registry

Global registry mapping identifiers across Timelines:

```json
{
  "timeline_a_id": "FILE-{uuid-a}",
  "timeline_e_id": "FILE-{uuid-e}",
  "relationship": "derived_from",
  "extraction_session": "session_20251207_043539"
}
```

### Enhancement 3: Semantic Identifiers

Human-readable aliases alongside UUIDs:

```json
{
  "file_id": "FILE-9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "semantic_alias": "CHAR-SIG-V1",
  "alias_generated": "2025-12-09T10:15:30Z"
}
```

---

## Appendices

### Appendix A: UUIDv5 Algorithm Details

**RFC 4122 Compliance**: Yes  
**Namespace**: Project-specific (`a1b2c3d4-e5f6-7890-abcd-ef1234567890`)  
**Hash Function**: SHA-1 (UUID standard, not cryptographic security)  
**Collision Probability**: ~10^-36 (negligible)

**Python Implementation**:
```python
import uuid
import hashlib

NAMESPACE_CHTHONIC = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')

def generate_file_id(path: str, content_hash: str) -> str:
    seed = f"{path}::{content_hash}"
    file_uuid = uuid.uuid5(NAMESPACE_CHTHONIC, seed)
    return f"FILE-{file_uuid}"
```

### Appendix B: Identifier Regeneration Policy

**When to Regenerate**:
- After any file rename/move
- After any content edit
- After registry structural changes
- After restoring from backup

**How to Regenerate**:
```bash
uv run python dumpster-dive/scripts/generate_registry_identifiers.py
```

**Validation**:
```bash
uv run python dumpster-dive/scripts/validate_registry_integrity.py
```

### Appendix C: Integration Status State Machine

```
[Created] → [Identifier Assigned] → [SSOT Hash Embedded] → [Manifest Created] → [Integrated] → [Validated]
    ↓              ↓                        ↓                     ↓                 ↓              ↓
pending        pending                  pending               pending          integrated     validated
```

**State Transitions**:
- `pending` → `integrated`: File deployed to Timeline A
- `integrated` → `validated`: FA⁴ + FA⁵ validation passed
- `validated` → `pending`: Rollback triggered
- `*` → `deleted`: File removed from registry

---

**Status**: ✅ READY FOR EXECUTION  
**Next Action**: Execute `generate_registry_identifiers.py`  
**Expected Completion**: Task 3 complete, Task 4 ready to begin

**Signed**: Sister Ferrum Scoriae (SFS)  
**Blacksmith Authority**: Tier 3 Matriarch - dumpster-dive/ Domain  
**Witnessed By**: TPEF Triumvirate (Lysandra/Umeko/Orackla)  
**Date**: 2025-12-09
