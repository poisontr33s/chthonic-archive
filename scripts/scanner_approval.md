# Scanner Implementation Approval

**Date:** 2026-01-04  
**Status:** APPROVED WITH CONSTRAINTS  
**Approval Authority:** User (The Savant) + AI validation  
**Schema Version:** 1.0.0

---

## Approval Scope

This approval authorizes implementation of a **hybrid epistemograph scanner** that:

1. Ingests existing DCRP artifacts as authoritative
2. Fills gaps in coverage (new files, missing metadata)
3. Extracts repo-specific epistemic signals
4. Computes topology metrics and scoring
5. Generates SQLite index + optional JSON export

---

## Hard Constraints (Non-Negotiable)

### 1. DCRP Authority Preservation

**NEVER overwrite these DCRP-derived fields:**

```python
PROTECTED_FIELDS = [
    'dcrp_spectral_freq',    # ROGBIV classification
    'dcrp_role',             # FORTRESS/GARDEN/OBSERVATORY
    'dcrp_essence',          # ML-synthesized theatrical identity
    'dcrp_exports_count'     # Reference count from graph analysis
]
```

**Enforcement:** Scanner MUST check `source='dcrp'` before any write operation.

**Violation Response:** Abort scan, log error, do not commit transaction.

---

### 2. Provenance Annotation

**Every inserted fact MUST be traceable:**

```sql
-- Required fields for new rows
INSERT INTO files (path, ..., source, indexed_at)
VALUES (?, ..., 'gap_scan', datetime('now'))

INSERT INTO signals (file_id, category, ..., detected_by, confidence)
VALUES (?, ?, ..., 'scanner_v1.0', 0.85)

INSERT INTO dependencies (source_file_id, target_path, ..., source, confidence)
VALUES (?, ?, ..., 'import_detection', 'medium')
```

**Enforcement:** Database triggers validate `source` field is never NULL.

---

### 3. Ingestion Order (Phase Discipline)

**Phase 1: DCRP Full Ingestion (REQUIRED FIRST)**

```python
def phase1_ingest_dcrp():
    """
    Load dependency_graph_production.json completely.
    Mark all rows with source='dcrp'.
    Record provenance in artifact_provenance table.
    """
    # Load graph
    graph = json.load(open('dependency_graph_production.json'))
    
    # Insert provenance
    cur.execute("""
        INSERT INTO artifact_provenance 
        (artifact_name, artifact_path, sha256, size_bytes, authority_level)
        VALUES (?, ?, ?, ?, 'primary')
    """, ('dependency_graph_production.json', 'dependency_graph_production.json', 
          compute_sha256('dependency_graph_production.json'), 
          os.path.getsize('dependency_graph_production.json')))
    
    # Ingest nodes
    for node in graph['nodes']:
        cur.execute("""
            INSERT OR IGNORE INTO files 
            (path, sha256, size_bytes, extension, 
             dcrp_spectral_freq, dcrp_role, dcrp_essence, dcrp_exports_count,
             is_text, source, preview_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'dcrp', 'dcrp')
        """, (node['id'], 'placeholder', 0, extract_ext(node['id']),
              node['spectral_freq'], node['role'], node['essence'], 
              node['exports_count'], 1))
    
    # Ingest edges
    for edge in graph['links']:
        # ... (see full implementation)
    
    db.commit()
```

**Enforcement:** Scanner refuses to run Phase 2-5 until Phase 1 commit confirmed.

---

### 4. Gap Detection (Conservative)

**Only scan files that:**

1. Are NOT in `files` table (filesystem walk comparison)
2. Have `source='dcrp'` but missing critical metadata (sha256, size_bytes)
3. Are governance-critical (SSOT, session logs) requiring signal extraction

**Skip these file types:**

```python
SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp',  # Images
    '.zip', '.7z', '.gz', '.tar',              # Archives
    '.exe', '.dll', '.so', '.bin',             # Binaries
    '.db', '.sqlite',                          # Databases (don't scan self)
    '.pptx', '.docx', '.pdf',                  # Office docs
    '.mp4', '.mov', '.mkv'                     # Video
}

SKIP_DIRECTORIES = {
    '.git', 'node_modules', '__pycache__', 
    'dist', 'build', 'target', '.venv'
}
```

**Enforcement:** Pre-flight validation against exclusion lists.

---

### 5. Content Sampling Limits

**Never read:**

- Files >1MB unless explicitly allowlisted (SSOT, major session logs)
- Binary files (detected via magic bytes + extension)
- Files without text MIME type

**Preview strategy:**

```python
def sample_content(file_path, max_bytes=8192):
    """
    Conservative content sampling.
    
    Returns:
        - head (4KB) + tail (4KB) for files >8KB
        - full content for files <8KB
        - "[SKIPPED_LARGE]" for files >1MB
    """
    size = os.path.getsize(file_path)
    
    if size > 1_048_576:  # 1MB
        if file_path not in ALLOWLIST:
            return "[SKIPPED_LARGE]", "skipped_large"
    
    if size <= max_bytes:
        with open(file_path, 'rb') as f:
            data = f.read()
        try:
            text = data.decode('utf-8')
            return text, "full"
        except:
            text = data.decode('latin-1', errors='replace')
            return text, "full_fallback"
    
    # Head + tail
    with open(file_path, 'rb') as f:
        head = f.read(4096)
        f.seek(max(0, size - 4096))
        tail = f.read(4096)
    
    head_text = head.decode('utf-8', errors='replace')
    tail_text = tail.decode('utf-8', errors='replace')
    
    return f"{head_text}\n\n--TAIL--\n\n{tail_text}", "head_tail"
```

**Enforcement:** File size checked before read attempt.

---

### 6. Signal Extraction (Targeted Only)

**Extract repo-specific signals from:**

1. **SSOT:** `.github/copilot-instructions.md`
2. **Session logs:** `AUTONOMOUS_SESSION_*.md`
3. **Gap files:** Files not in DCRP coverage
4. **Governance docs:** `ANKHOLOGY.md`, `ANKH_README.md`, etc.

**Use conservative regex patterns:**

```python
SIGNAL_PATTERNS = {
    'ssot_marker': re.compile(r'\b(SSOT|Codex-Brahmanica-Perfectus|FA[¹²³⁴⁵])\b'),
    'tier_marker': re.compile(r'\b(Tier\s*[0-9.]+|T-[0-9]+)\b'),
    'triumvirate': re.compile(r'\b(CRC-AS|CRC-GAR|CRC-MEDAT|Orackla|Umeko|Lysandra)\b'),
    'protocol_ref': re.compile(r'\b(DCRP|TPEF|T³-MΨ|MMPS|MSP-RSG)\b'),
    'ankh_marker': re.compile(r'\b(ANKH|Ankhological|⚓)\b'),
    'contract': re.compile(r'\b(MUST|SHALL|REQUIRED|MANDATORY|FORBIDDEN)\b', re.I),
    'agent': re.compile(r'\b(TODO|FIXME|HACK|NOTE|WARNING|DEPRECATED)\b', re.I),
}
```

**Record confidence scores:**

```python
def detect_signals(text, file_path):
    """Returns list of (category, line_num, snippet, confidence)"""
    signals = []
    for i, line in enumerate(text.splitlines(), 1):
        for category, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(line):
                confidence = 1.0 if category in REPO_SPECIFIC else 0.8
                signals.append((category, i, line.strip()[:600], confidence))
    return signals
```

---

### 7. Topology Computation (From DCRP Edges)

**Use existing dependency graph, don't recompute:**

```python
def phase4_compute_topology():
    """
    Compute in_degree, out_degree from dependencies table.
    Identify hubs (high in_degree), entry points, orphans.
    """
    # Update in_degree
    cur.execute("""
        UPDATE topology_nodes
        SET in_degree = (
            SELECT COUNT(*) 
            FROM dependencies 
            WHERE target_file_id = topology_nodes.file_id
        )
    """)
    
    # Update out_degree
    cur.execute("""
        UPDATE topology_nodes
        SET out_degree = (
            SELECT COUNT(*) 
            FROM dependencies 
            WHERE source_file_id = topology_nodes.file_id
        )
    """)
    
    # Compute total_degree
    cur.execute("""
        UPDATE topology_nodes
        SET total_degree = in_degree + out_degree
    """)
    
    # Mark hubs (top 10%)
    threshold = cur.execute("""
        SELECT total_degree 
        FROM topology_nodes 
        ORDER BY total_degree DESC 
        LIMIT 1 OFFSET (SELECT COUNT(*)/10 FROM topology_nodes)
    """).fetchone()[0]
    
    cur.execute("""
        UPDATE topology_nodes
        SET is_hub = 1
        WHERE total_degree >= ?
    """, (threshold,))
    
    db.commit()
```

---

### 8. Scoring Weights (Governance-First)

**Composite epistemic_score formula:**

```sql
epistemic_score = (
    (signal_density * 0.25) +
    (topology_centrality * 0.25) +
    (governance_weight * 0.35) +    -- HIGHEST WEIGHT
    (lineage_depth * 0.15)
)
```

**Where:**

- `signal_density` = repo-specific signals per 100 lines
- `topology_centrality` = normalized total_degree
- `governance_weight` = (ssot_signals + tier_signals + protocol_signals) / total_signals
- `lineage_depth` = shortest path distance from SSOT (inverted: 1.0 - normalized_distance)

**Rationale:** SSOT proximity matters more than connectivity or signal volume.

---

### 9. View Behavior Clarification

**Added to schema documentation:**

```sql
-- IMPORTANT: Views that depend on scanner-derived scores
-- (e.g., v_top_artifacts, v_ssot_lineage) will return
-- 0 rows or NULL values until scanner Phase 5 (Scoring) completes.
--
-- This is EXPECTED behavior, not a schema error.
--
-- To check if scoring is complete:
-- SELECT COUNT(*) FROM file_scores WHERE epistemic_score IS NOT NULL;
```

**Enforcement:** Scanner logs warning if views queried before scoring phase.

---

### 10. Transaction Safety

**All phases wrapped in transactions:**

```python
def run_scanner():
    try:
        db.execute("BEGIN TRANSACTION")
        
        phase1_ingest_dcrp()
        phase2_detect_gaps()
        phase3_extract_signals()
        phase4_compute_topology()
        phase5_score_files()
        
        db.execute("COMMIT")
        log("Scanner completed successfully")
        
    except Exception as e:
        db.execute("ROLLBACK")
        log(f"Scanner failed: {e}")
        raise
```

**Enforcement:** Any phase failure triggers full rollback.

---

## Output Artifacts

**Primary:**
- `chthonic_epistemograph.sqlite` (~5-15MB)

**Secondary (Optional):**
- `epistemograph_top50.json` (curated top artifacts)
- `epistemograph_summary.md` (human-readable report)

**Logs:**
- `scanner_execution.log` (phase timings, warnings, errors)

---

## Execution Constraints

**Time Budget:** 2 minutes maximum

**Phase Breakdown:**
1. DCRP Ingestion: 30 seconds
2. Gap Detection: 10 seconds
3. Signal Extraction: 60 seconds
4. Topology Computation: 15 seconds
5. Scoring: 5 seconds

**If any phase exceeds 2x expected time:** Abort with timeout error.

---

## Validation Checklist (Pre-Execution)

Before running scanner, verify:

- [ ] Schema version 1.0.0 loaded
- [ ] `dependency_graph_production.json` exists and readable
- [ ] Test database validation passed (from Option C)
- [ ] Exclusion lists defined
- [ ] Signal patterns compiled
- [ ] Scoring weights configured
- [ ] Transaction safety enabled
- [ ] Logging configured
- [ ] Output directory writable

---

## Post-Execution Validation

After scanner completes, verify:

- [ ] SSOT still ranked highest (export count + epistemic_score)
- [ ] No DCRP fields overwritten (spot check 10 random files)
- [ ] Provenance recorded for all new rows
- [ ] Signal categories populated
- [ ] Topology metrics computed
- [ ] Scoring phase completed (file_scores table non-empty)
- [ ] Views return expected results
- [ ] No orphaned foreign keys
- [ ] Log shows no errors/warnings

---

## Governance Alignment

This approval complies with:

- **§XIV.3:** Hash verification (provenance table)
- **§XV (DCRP):** Respects cross-reference authority
- **FA⁴:** Architectonic integrity (constraints, triggers)
- **FA⁵:** Visual integrity (DCRP essences preserved)
- **SSOT Governance:** Lineage preservation, no content duplication

---

## Approval Authority

**Approved by:** The Savant (User)  
**Validated by:** Query-based testing (Option C)  
**Date:** 2026-01-04  
**Schema Version:** 1.0.0  
**Constraint Version:** 1.0  

**Status:** ✅ APPROVED FOR IMPLEMENTATION

---

## Implementation Authorization

The scanner implementation is hereby **authorized** under the constraints documented above.

**Next Action:** Implement scanner script with phase structure.

**Signature (Metaphorical):**

```
THE SAVANT
User / Creator / Architect-Of-Apex-Synthesis-Core
Date: 2026-01-04
```

---

**End of Approval Document**

