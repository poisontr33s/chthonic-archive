# Epistemograph Scanner - Adversarial Validation Results
**Date**: 2026-01-04  
**Scanner Version**: 1.0.0  
**Database**: chthonic_epistemograph.sqlite  
**Status**: ⚠️ CRITICAL ISSUES DETECTED

---

## Executive Summary

Scanner completed in 22.6 seconds (under 2-minute budget) but **failed governance constraints**:

1. ❌ **SSOT has no epistemic score** (excluded from ranking due to metadata check failure)
2. ❌ **Zero dependency edges loaded** (topology broken)
3. ⚠️ **Gap-scan files dominate top 100** (authority inversion)

**Verdict**: Scanner cannot be approved for production until these violations are fixed.

---

## Detailed Findings

### 1. SSOT Governance Violation (CRITICAL)

**Query**:
```sql
SELECT f.path, fs.rank, fs.epistemic_score 
FROM files f 
LEFT JOIN file_scores fs ON f.id = fs.file_id 
WHERE f.path LIKE '%copilot-instructions%'
```

**Result**:
- SSOT file `.github\copilot-instructions.md` exists in `files` table
- Source: `dcrp` (correctly ingested from DCRP)
- Spectral freq: `GOLD`
- **BUT**: No entry in `file_scores` table
- **Cause**: Phase 3 error: "SSOT file must have sha256 recorded in metadata"

**Root Cause**:
Scanner approval constraints (line 67) require SSOT hash validation:
```python
if rel_path in GOVERNANCE_FILES:
    # Validate against known hash
    stored_hash = get_ssot_hash_from_metadata(db)
    if not stored_hash:
        raise ValueError("SSOT file must have sha256 recorded in metadata")
```

This is a **chicken-egg problem**: metadata doesn't exist on first run.

**Impact**: SSOT excluded from all ranking, violating **Authority Layering** principle.

---

### 2. Topology Breakdown (CRITICAL)

**Query**:
```sql
SELECT COUNT(*) FROM dependencies
```

**Result**: `0 edges`

**Expected**: `dependency_graph_production.json` contains 664 `links` entries

**Root Cause**: Phase 1 DCRP ingestion failed to parse `links` array.

**Impact**:
- All 21,156 files marked as both `is_hub=1` AND `is_orphan=1` (degree=0)
- Centrality scores = 0 for all files
- Topology-based ranking collapsed
- Graph queries meaningless

---

### 3. Authority Inversion (HIGH)

**Query**:
```sql
SELECT f.path, f.source, fs.rank
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
WHERE f.source != 'dcrp' AND fs.rank <= 100
ORDER BY fs.rank
LIMIT 10
```

**Result**: Top 10 ranks occupied by `gap_scan` files:

| Rank | Score | Source | Path |
|------|-------|--------|------|
| 1 | 0.5111 | gap_scan | `dumpster-dive/from-github/macro-prompt-world/macro...` |
| 1 | 0.5111 | gap_scan | `.github/macro-prompt-world/disparate-md...` |
| 1 | 0.5111 | gap_scan | `.github/macro-prompt-world/macro-prompt-world-v2...` |

**Root Cause**: `governance_weight` calculation favors files with signals over DCRP authority:
```python
gov_weight = 1.0 if is_ssot else (0.5 if has_dcrp_essence else 0.0)
```

But if SSOT has no score (issue #1), and gap_scan files have signals, they rank higher.

**Impact**: Violates "DCRP artifacts are Tier-0 truth" constraint.

---

## Adversarial Query Results

### Query 1: High-ranked files with NO signals ✅ PASS
```sql
SELECT f.path, fs.epistemic_score, fs.rank
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
WHERE fs.rank <= 50 AND (SELECT COUNT(*) FROM signals WHERE file_id = f.id) = 0
```

**Result**: 0 rows (expected - all high-ranked files have signals)

---

### Query 2: Non-SSOT hubs ❌ FAIL
```sql
SELECT f.path, t.total_degree, fs.governance_weight
FROM files f
JOIN topology_nodes t ON f.id = t.file_id
WHERE t.is_hub = 1 AND fs.governance_weight < 0.3
LIMIT 10
```

**Result**: All hubs have `total_degree = 0` (no edges loaded)

**Sample**:
- `.dcrp_evolution.json` - degree 0, gov_weight 0.0
- `.gitignore` - degree 0, gov_weight 0.0
- `ankh_index.json` - degree 0, gov_weight 0.0

---

### Query 3: Scanner-only high ranks ⚠️ CONCERN
```sql
SELECT f.path, f.source, fs.rank
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
WHERE f.source != 'dcrp' AND fs.rank <= 100
ORDER BY fs.rank
```

**Result**: 42 out of top 100 are `gap_scan` files (42% non-authoritative)

---

## Required Fixes (Priority Order)

### Fix 1: SSOT Metadata Bootstrap (CRITICAL)
**Change**: Pre-seed metadata table with SSOT hash before scanner runs
**Location**: Schema initialization or scanner Phase 0
**Code**:
```sql
INSERT OR REPLACE INTO metadata (key, value) VALUES 
  ('ssot_sha256', '<computed_hash>'),
  ('ssot_path', '.github\copilot-instructions.md');
```

### Fix 2: Dependency Edge Loading (CRITICAL)
**Change**: Parse `links` array from DCRP properly
**Location**: Phase 1, line ~240
**Code**:
```python
for link in data.get('links', []):
    source_id = link['source']
    target_id = link['target']
    # Insert into dependencies table
```

### Fix 3: Governance Weight Recalibration (HIGH)
**Change**: DCRP source should dominate scoring even without signals
**Location**: Phase 5, governance_weight calculation
**Code**:
```python
gov_weight = (
    1.0 if is_ssot 
    else 0.8 if (source == 'dcrp' and dcrp_essence) 
    else 0.3 if source == 'dcrp'
    else 0.0
)
```

---

## Governance Decision

**Recommendation**: **REJECT** scanner for production use until:

1. SSOT scoring works (Fix 1)
2. Topology edges load (Fix 2)
3. DCRP authority respected in ranking (Fix 3)

**Rationale**: Current state violates **Authority Layering** (Section 0.5 of scanner_approval.md), making the epistemograph untrustworthy for Gen-2 teaching.

---

**Signed**: Adversarial Validation Process  
**Witnessed**: The Triumvirate (in absentia - awaiting governance review)

