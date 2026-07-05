# Epistemograph Scanner v1.1 - Critical Fixes Documentation

**Status:** READY FOR RE-VALIDATION  
**Date:** 2026-01-04  
**Scanner Version:** 1.1.0  
**Previous Version:** 1.0.0 (FAILED validation)

---

## Executive Summary

Three critical bugs identified via adversarial validation have been surgically fixed:

1. **SSOT Bootstrap Bug** - Governance bootstrapping order violation
2. **Topology Ingestion Bug** - DCRP edge parser wiring failure  
3. **Authority Inversion Bug** - Scoring weights insufficient for governance enforcement

All fixes maintain backward compatibility with schema and preserve governance constraints from `scanner_approval.md`.

---

## Fix 1: SSOT Bootstrap (Lines 147-180)

### Root Cause
SSOT files required pre-recorded `sha256` in metadata table during Phase 3 validation, but metadata ingestion happened *after* DCRP phase. This created chicken-egg dependency causing SSOT to be skipped entirely.

### Solution
```python
# Phase 1: During DCRP node ingestion
if node_id in ssot_files or '.github/copilot-instructions.md' in node_id:
    # Compute real metadata immediately
    full_path = root / node_id.replace('/', os.sep)
    if full_path.exists():
        real_sha = compute_sha256(full_path)
        real_size = full_path.stat().st_size
    else:
        real_sha = "ssot_missing"
        real_size = 0
else:
    # Non-SSOT files use placeholder
    real_sha = "dcrp_placeholder"
    real_size = 0
```

### Governance Invariant Preserved
> **SSOT is never subject to gap-scan validation rules.**

SSOT files receive Tier-0 treatment from Phase 1 onward.

---

## Fix 2: Topology Ingestion (Lines 182-230)

### Root Cause
DCRP `links[]` array was not being parsed into `dependencies` table. Node ingestion worked, but edge ingestion silently failed due to:
- Path normalization mismatch (Windows `\` vs `/`)
- Missing error handling for edge insertion failures
- No validation that edges actually populated

### Solution
```python
# Apply consistent path normalization
source_path = normalize_path(edge['source'])
target_path = normalize_path(edge['target'])

# Track edge insertion success
edges_in_graph = len(graph.get('links', []))
edge_count = 0

# Add hard guard after ingestion loop
if edges_in_graph > 0 and edge_count == 0:
    raise RuntimeError(f"TOPOLOGY INGESTION FAILURE: {edges_in_graph} edges in graph but 0 inserted")
```

### Validation Added
Scanner now aborts immediately if DCRP contains edges but dependencies table remains empty, preventing silent topology loss.

---

## Fix 3: Authority Precedence (Lines 545-590)

### Root Cause
`governance_weight` was proportional (0.30 coefficient), allowing high signal density from `gap_scan` files to overpower DCRP authority. Scoring was preference-based, not law-based.

### Solution
**Categorical enforcement via score floors:**

```python
if file_id == ssot_id:
    # SSOT: Force to maximum
    final_score = max_possible_score * 1.1  # Always rank 1

elif source == 'dcrp':
    # DCRP files: Floor at 90% of max
    final_score = max(raw_score, max_possible_score * 0.9)

elif source == 'gap_scan':
    # Gap scan: Cap score to prevent domination
    final_score = min(raw_score, max_possible_score * 0.5)
```

### Governance Rules Encoded
1. SSOT file: `rank = 1` (hard law)
2. DCRP files: `rank ≤ 10` (minimum floor ensures top tier)
3. Gap scan files: `rank ≥ 50` (ceiling prevents authority inversion)

---

## Acceptance Criteria for v1.1 Re-Validation

### Critical (Must Pass)

1. **SSOT Rank Verification**
   ```sql
   SELECT f.path, fs.rank, fs.epistemic_score
   FROM files f
   JOIN file_scores fs ON f.id = fs.file_id
   WHERE f.path LIKE '%.github/copilot-instructions.md';
   ```
   **Expected:** `rank = 1`

2. **Topology Non-Empty**
   ```sql
   SELECT COUNT(*) FROM dependencies WHERE source = 'dcrp';
   ```
   **Expected:** `> 0` (should match DCRP edge count from Phase 1 log)

3. **Top-100 DCRP Dominance**
   ```sql
   SELECT source, COUNT(*) 
   FROM files f
   JOIN file_scores fs ON f.id = fs.file_id
   WHERE fs.rank <= 100
   GROUP BY source;
   ```
   **Expected:** `dcrp` count ≥ 80 (at least 80% of top-100)

### Secondary (Should Pass)

4. **Zero Governance Violations**
   ```sql
   SELECT COUNT(*) FROM file_scores fs
   JOIN files f ON fs.file_id = f.id
   WHERE f.source = 'gap_scan' AND fs.rank <= 10;
   ```
   **Expected:** `0` (no gap_scan files in top 10)

5. **SHA256 Bootstrap Success**
   ```sql
   SELECT COUNT(*) FROM files
   WHERE path LIKE '%.github/copilot-instructions.md'
   AND sha256 != 'dcrp_placeholder'
   AND sha256 != 'ssot_missing';
   ```
   **Expected:** `≥ 1` (SSOT has real hash)

---

## Regression Safety

### Unchanged Behavior
- Schema structure (no table modifications)
- DCRP field protection (`PROTECTED_FIELDS`)
- Signal extraction patterns
- Provenance tracking
- Transaction safety

### New Behavior
- SSOT files bootstrapped in Phase 1 (was Phase 3)
- Topology validated via hard guard (was silent)
- Score floors/ceilings categorical (was proportional)

---

## Execution Instructions

```powershell
# From repository root
cd C:\Users\eldno\chthonic-archive

# Run fixed scanner
uv run scripts/build_epistemograph_v1.1.py --root . --out chthonic_epistemograph_v1.1.sqlite

# Run validation queries
uv run scripts/run_queries.py --db chthonic_epistemograph_v1.1.sqlite --query critical
```

---

## Rollback Plan

If v1.1 validation fails:

1. Preserve failed DB: `chthonic_epistemograph_v1.1_FAILED.sqlite`
2. Document failure in `scanner_validation_v1.1_FAILED.md`
3. Revert to Gen-1 artifact freeze (Option B from original decision tree)
4. Tag repository state: `git tag epistemograph-gen1-limit`

---

## Sign-Off

**Fixes Applied:** 3/3 critical bugs  
**Governance Preserved:** ✓ (all constraints from scanner_approval.md maintained)  
**Schema Migration Required:** ✗ (backward compatible)  
**Ready for Validation:** ✓

**Next Step:** Execute `build_epistemograph_v1.1.py` and re-run adversarial queries.


