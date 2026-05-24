# Epistemograph Schema Design Document

**Version:** 1.0.0  
**Date:** 2026-01-04  
**Architect:** Hybrid (User guidance + AI implementation)  
**Status:** Ready for implementation

---

## Design Philosophy

### Core Principle: **Respect Existing Lineage**

This schema treats existing DCRP artifacts (`dependency_graph_production.json`, `CROSS_REFERENCE_TRIPTYCH.md`, `ankh_index.json`) as **authoritative inputs**, not secondary data sources.

The epistemograph is not a replacement—it is a **query layer** over established knowledge.

---

## Schema Architecture

### 1. **Provenance-First Design**

```sql
CREATE TABLE artifact_provenance (
  artifact_name TEXT UNIQUE NOT NULL,
  sha256 TEXT NOT NULL,
  authority_level TEXT
);
```

**Why:** Every query result must be traceable to its source. DCRP data is marked `authority_level='primary'`. Gap-filled data is `secondary`.

**Operational Benefit:** Future incremental scans can skip re-processing DCRP-covered files.

---

### 2. **DCRP Integration (Not Duplication)**

```sql
CREATE TABLE files (
  path TEXT UNIQUE NOT NULL,
  dcrp_spectral_freq TEXT,  -- RED/ORANGE/GOLD/etc.
  dcrp_role TEXT,           -- FORTRESS/GARDEN/OBSERVATORY
  dcrp_essence TEXT,        -- ML-synthesized theatrical identity
  source TEXT               -- 'dcrp' or 'gap_scan'
);
```

**Why:** The DCRP already computed:
- Spectral frequency (PRISM ROGBIV)
- Architectural role (tri-modal structure)
- Theatrical essence (ML synthesis)

These are **imported**, not recomputed.

**Intentional Exclusion:** We do not re-run ML synthesis. DCRP's judgments are final.

---

### 3. **Minimal Content Sampling**

```sql
content_preview TEXT,
preview_method TEXT CHECK(preview_method IN ('none', 'head_tail', 'dcrp', 'skipped_large'))
```

**Why:** Only read content where:
1. DCRP has no coverage (gap files)
2. Signal extraction requires it (governance docs)
3. File is governance-critical (SSOT, session artifacts)

**Constraint:** Never read >1MB text files unless explicitly flagged.

**Privacy:** Token redaction (`ghp_*`, JWT patterns) applied automatically.

---

### 4. **Bidirectional Dependencies**

```sql
CREATE TABLE dependencies (
  source_file_id INTEGER,
  target_path TEXT,
  dep_type TEXT,  -- 'import', 'reference', 'link'
  source TEXT     -- 'dcrp' or 'gap_scan'
);
```

**Why:** DCRP already extracted most dependencies. This table:
- Imports DCRP edges (marked `source='dcrp'`)
- Adds gap-filled edges (marked `source='gap_scan'`)
- Enables graph queries without recomputing

**Operational Benefit:** Incremental updates only add new edges.

---

### 5. **Repo-Specific Signals**

```sql
INSERT INTO signal_categories VALUES
  ('ssot_marker', 'SSOT/Codex references', 1),
  ('tier_marker', 'Tier notation', 1),
  ('triumvirate', 'CRC-AS/GAR/MEDAT', 1),
  ('protocol_ref', 'DCRP/TPEF/T³-MΨ', 1),
  ('ankh_marker', 'ANKH/⚓', 1);
```

**Why:** Generic signals (TODO, MUST, assert) are useful, but this repo has domain-specific epistemic markers:
- SSOT references indicate governance lineage
- Tier markers indicate hierarchical position
- Protocol refs indicate operational frameworks

**Scoring Impact:** Files with high governance signal density rank higher.

---

### 6. **Composite Epistemic Scoring**

```sql
CREATE TABLE file_scores (
  signal_density REAL,        -- signals per 100 lines
  topology_centrality REAL,   -- Normalized degree
  governance_weight REAL,     -- SSOT/tier/protocol mentions
  lineage_depth REAL,         -- Distance from SSOT
  
  epistemic_score REAL GENERATED ALWAYS AS (
    (signal_density * 0.25) +
    (topology_centrality * 0.25) +
    (governance_weight * 0.35) +
    (lineage_depth * 0.15)
  )
);
```

**Weights Rationale:**
- **35% governance_weight:** SSOT proximity is highest priority
- **25% topology_centrality:** Hub files are important
- **25% signal_density:** High epistemic content matters
- **15% lineage_depth:** Closer to SSOT = more authoritative

**Tunable:** Weights can be adjusted via `UPDATE` without schema change.

---

### 7. **Precomputed Views**

```sql
CREATE VIEW v_top_artifacts AS
SELECT path, epistemic_score, ...
FROM files JOIN file_scores
ORDER BY epistemic_score DESC
LIMIT 50;
```

**Why:** Common queries (top artifacts, orphans, hubs) precomputed as views for instant access.

**Performance:** Views are logical—no storage cost, computed on-demand.

---

## Intentional Exclusions

| **Excluded** | **Reason** |
|--------------|------------|
| Full file contents | Map, not backup |
| AST parsing | DCRP already did semantic analysis |
| Git history | Single-point-in-time snapshot |
| External dependencies | Internal topology only |
| ML embeddings | Deterministic signals preferred |
| Compression | SQLite is already compact |

---

## Incremental Operation

### Phase 1: DCRP Ingestion (One-Time)

```python
# Import dependency_graph_production.json
for node in graph['nodes']:
    INSERT INTO files (path, dcrp_spectral_freq, dcrp_role, dcrp_essence, source)
    VALUES (node['id'], node['spectral_freq'], node['role'], node['essence'], 'dcrp')

for edge in graph['links']:
    INSERT INTO dependencies (source_file_id, target_path, dep_type, source)
    VALUES (resolve(edge['source']), edge['target'], 'reference', 'dcrp')
```

### Phase 2: Gap Detection

```python
# Find files not in DCRP
SELECT path FROM files WHERE source = 'gap_scan'
UNION
SELECT path FROM filesystem WHERE path NOT IN (SELECT path FROM files)
```

### Phase 3: Targeted Signal Extraction

```python
# Only process gap files + governance docs
for file in gap_files + governance_files:
    extract_signals(file)
    INSERT INTO signals (file_id, category, line_number, snippet)
```

### Phase 4: Topology Computation

```python
# Compute metrics only once
UPDATE topology_nodes SET
  in_degree = (SELECT COUNT(*) FROM dependencies WHERE target_file_id = file_id),
  out_degree = (SELECT COUNT(*) FROM dependencies WHERE source_file_id = file_id)
```

### Phase 5: Scoring

```python
# Score computation (single pass)
for file_id in files:
    signal_density = count_signals(file_id) / line_count
    centrality = normalize(total_degree)
    governance = count_governance_signals(file_id)
    lineage = dijkstra_distance(ssot_file_id, file_id)
    
    INSERT INTO file_scores VALUES (file_id, signal_density, centrality, governance, lineage)
```

---

## Query Examples

### Top 30 Epistemic Artifacts

```sql
SELECT * FROM v_top_artifacts LIMIT 30;
```

### SSOT Lineage Chain

```sql
SELECT * FROM v_ssot_lineage;
```

### Find Files Referencing Protocol X

```sql
SELECT DISTINCT f.path
FROM files f
JOIN signals s ON f.id = s.file_id
WHERE s.category = 'protocol_ref' AND s.snippet LIKE '%DCRP%';
```

### Detect Orphans (Deletion Candidates)

```sql
SELECT * FROM v_orphans WHERE size_bytes > 1048576;
```

### Graph: Dependencies of File X

```sql
WITH RECURSIVE deps(path, depth) AS (
  SELECT path, 0 FROM files WHERE path = 'target.py'
  UNION ALL
  SELECT f.path, d.depth + 1
  FROM deps d
  JOIN dependencies dep ON dep.source_file_id = (SELECT id FROM files WHERE path = d.path)
  JOIN files f ON dep.target_file_id = f.id
  WHERE d.depth < 5
)
SELECT * FROM deps;
```

---

## Schema Evolution

### Version 1.1.0 (Future)

Potential additions:
- `file_versions` table for temporal snapshots
- `signal_confidence` ML scoring
- `cluster_themes` automated labeling

### Backward Compatibility

All future versions preserve:
- Core tables (`files`, `dependencies`, `signals`)
- DCRP source attribution
- SSOT provenance tracking

---

## Implementation Strategy

### Script Structure

```
epistemograph_builder.py
├── phase1_ingest_dcrp()      # Import existing artifacts
├── phase2_detect_gaps()      # Find uncovered files
├── phase3_extract_signals()  # Targeted regex scanning
├── phase4_compute_topology() # Graph metrics
├── phase5_score_files()      # Epistemic ranking
└── export_json()             # Optional JSON view
```

### Execution Time (Estimate)

- Phase 1: ~5 seconds (JSON parsing)
- Phase 2: ~10 seconds (filesystem walk)
- Phase 3: ~60 seconds (targeted content reading)
- Phase 4: ~15 seconds (graph computation)
- Phase 5: ~5 seconds (scoring)

**Total:** ~2 minutes for full hybrid scan

---

## Output Artifacts

1. **Primary:** `chthonic_epistemograph.sqlite` (~5-10MB)
2. **Optional:** `epistemograph_top50.json` (curated view)
3. **Optional:** `epistemograph_browser.html` (D3.js visualization)

---

## Governance Alignment

This schema complies with:
- **§XIV.3:** Hash verification protocol (artifact provenance table)
- **§XV (DCRP):** Respects existing cross-reference system
- **FA⁴:** Architectonic integrity (SSOT constraints, triggers)
- **FA⁵:** Visual integrity (DCRP theatrical essence preserved)

---

## Next Steps

1. **Review schema** (You approve/modify)
2. **Implement scanner** (Python script using this schema)
3. **Execute hybrid scan** (Phases 1-5)
4. **Validate output** (Query top 30 artifacts)
5. **Generate JSON export** (For upload/analysis)

---

**Schema Status:** ✅ Ready for implementation  
**Awaiting:** User approval to proceed with scanner implementation

