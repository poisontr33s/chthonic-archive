-- Epistemograph SQLite Schema
-- Purpose: Unified index respecting DCRP lineage + incremental signal extraction
-- Design: Hybrid (existing artifacts authoritative + gap-filling)
-- Version: 1.0.0
-- Date: 2026-01-04

-- =============================================================================
-- METADATA: Provenance & Governance
-- =============================================================================

CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Initialize core metadata
INSERT OR REPLACE INTO metadata (key, value) VALUES 
  ('schema_version', '1.0.0'),
  ('scanner_type', 'hybrid'),
  ('ssot_governance', 'enabled');

-- =============================================================================
-- PROVENANCE: Existing Artifact Lineage
-- =============================================================================

CREATE TABLE IF NOT EXISTS artifact_provenance (
  id INTEGER PRIMARY KEY,
  artifact_name TEXT UNIQUE NOT NULL,  -- e.g., 'dependency_graph_production.json'
  artifact_path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER,
  ingested_at TEXT DEFAULT (datetime('now')),
  authority_level TEXT CHECK(authority_level IN ('primary', 'secondary', 'reference'))
);

-- Index for hash lookups
CREATE INDEX IF NOT EXISTS idx_artifact_sha ON artifact_provenance(sha256);

-- =============================================================================
-- FILES: Core File Index
-- =============================================================================

CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,           -- Relative to repo root
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  extension TEXT,
  
  -- DCRP Integration
  dcrp_spectral_freq TEXT,             -- RED/ORANGE/GOLD/BLUE/WHITE/INDIGO/VIOLET
  dcrp_role TEXT,                      -- FORTRESS/GARDEN/OBSERVATORY
  dcrp_essence TEXT,                   -- ML-synthesized theatrical identity
  dcrp_exports_count INTEGER DEFAULT 0,
  
  -- Content Sampling (only for gap-filling)
  content_preview TEXT,
  preview_method TEXT CHECK(preview_method IN ('none', 'head_tail', 'dcrp', 'skipped_large')),
  line_count INTEGER,
  
  -- Metadata
  is_text INTEGER DEFAULT 0,
  indexed_at TEXT DEFAULT (datetime('now')),
  source TEXT DEFAULT 'hybrid_scan'    -- 'dcrp' or 'gap_scan'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_files_sha ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_spectral ON files(dcrp_spectral_freq);
CREATE INDEX IF NOT EXISTS idx_files_role ON files(dcrp_role);

-- =============================================================================
-- DEPENDENCIES: Bidirectional Graph (from DCRP + imports)
-- =============================================================================

CREATE TABLE IF NOT EXISTS dependencies (
  id INTEGER PRIMARY KEY,
  source_file_id INTEGER NOT NULL,
  target_path TEXT NOT NULL,           -- May not resolve to file_id (external deps)
  target_file_id INTEGER,              -- NULL if external/unresolved
  dep_type TEXT NOT NULL,              -- 'import', 'reference', 'link'
  line_number INTEGER,
  confidence TEXT CHECK(confidence IN ('high', 'medium', 'low')),
  source TEXT DEFAULT 'dcrp',          -- 'dcrp' or 'gap_scan'
  
  FOREIGN KEY(source_file_id) REFERENCES files(id)
);

-- Indexes for graph traversal
CREATE INDEX IF NOT EXISTS idx_deps_source ON dependencies(source_file_id);
CREATE INDEX IF NOT EXISTS idx_deps_target_path ON dependencies(target_path);
CREATE INDEX IF NOT EXISTS idx_deps_target_id ON dependencies(target_file_id);

-- =============================================================================
-- SIGNALS: Epistemic Markers
-- =============================================================================

CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL,
  category TEXT NOT NULL,              -- 'contract', 'agent', 'verification', etc.
  line_number INTEGER,
  snippet TEXT,                        -- Max 600 chars
  detected_by TEXT DEFAULT 'gap_scan', -- 'dcrp' or 'gap_scan'
  confidence REAL DEFAULT 1.0,         -- 0.0-1.0
  
  FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Repository-specific signal categories
CREATE TABLE IF NOT EXISTS signal_categories (
  category TEXT PRIMARY KEY,
  description TEXT,
  pattern TEXT,                        -- Regex pattern for reference
  is_repo_specific INTEGER DEFAULT 0
);

-- Initialize standard categories
INSERT OR IGNORE INTO signal_categories (category, description, is_repo_specific) VALUES
  ('contract', 'MUST/SHALL/REQUIRED language', 0),
  ('agent', 'TODO/FIXME/NOTE markers', 0),
  ('verification', 'validate/assert/check/test', 0),
  ('revision', 'version/changelog/updated', 0),
  ('coordinate', 'Section/Phase/Tier/Protocol', 0),
  ('topology', 'topology/graph/dag/map', 0),
  ('cross_ref', 'see/ref/link/goto references', 0),
  ('ssot_marker', 'SSOT/Codex references', 1),
  ('tier_marker', 'Tier notation (0.5, 1, 2, etc)', 1),
  ('triumvirate', 'CRC-AS/GAR/MEDAT references', 1),
  ('protocol_ref', 'DCRP/TPEF/T³-MΨ/MMPS protocols', 1),
  ('ankh_marker', 'ANKH/Ankhological/⚓ markers', 1);

-- Index for signal queries
CREATE INDEX IF NOT EXISTS idx_signals_category ON signals(category);
CREATE INDEX IF NOT EXISTS idx_signals_file ON signals(file_id);

-- =============================================================================
-- TOPOLOGY: Computed Graph Metrics
-- =============================================================================

CREATE TABLE IF NOT EXISTS topology_nodes (
  file_id INTEGER PRIMARY KEY,
  in_degree INTEGER DEFAULT 0,         -- Number of files depending on this
  out_degree INTEGER DEFAULT 0,        -- Number of files this depends on
  total_degree INTEGER DEFAULT 0,      -- Sum (hub detection)
  is_entry_point INTEGER DEFAULT 0,    -- main/index/README at root
  is_orphan INTEGER DEFAULT 0,         -- degree == 0
  is_hub INTEGER DEFAULT 0,            -- high in_degree
  cluster_id INTEGER,                  -- Connected component ID
  
  FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Precomputed clusters for performance
CREATE TABLE IF NOT EXISTS topology_clusters (
  cluster_id INTEGER PRIMARY KEY,
  file_count INTEGER,
  coherence_signal TEXT,               -- 'shared_prefix', 'shared_imports', 'mutual_refs'
  representative_file_id INTEGER,      -- Highest degree node in cluster
  
  FOREIGN KEY(representative_file_id) REFERENCES files(id)
);

-- =============================================================================
-- SCORING: Epistemic Importance
-- =============================================================================

CREATE TABLE IF NOT EXISTS file_scores (
  file_id INTEGER PRIMARY KEY,
  
  -- Component scores (0.0-1.0)
  signal_density REAL DEFAULT 0.0,     -- signals per 100 lines
  topology_centrality REAL DEFAULT 0.0, -- Normalized degree
  governance_weight REAL DEFAULT 0.0,  -- SSOT/tier/protocol mentions
  lineage_depth REAL DEFAULT 0.0,      -- Distance from SSOT in dep graph
  
  -- Composite score
  epistemic_score REAL GENERATED ALWAYS AS (
    (signal_density * 0.25) +
    (topology_centrality * 0.25) +
    (governance_weight * 0.35) +
    (lineage_depth * 0.15)
  ) STORED,
  
  -- Ranking
  rank INTEGER,
  
  FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Index for ranking queries
CREATE INDEX IF NOT EXISTS idx_scores_epistemic ON file_scores(epistemic_score DESC);

-- =============================================================================
-- VIEWS: Convenience Queries
-- =============================================================================

-- Top epistemic artifacts
CREATE VIEW IF NOT EXISTS v_top_artifacts AS
SELECT 
  f.path,
  f.dcrp_spectral_freq,
  f.dcrp_role,
  f.dcrp_essence,
  fs.epistemic_score,
  fs.signal_density,
  fs.topology_centrality,
  tn.total_degree,
  tn.is_hub
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
LEFT JOIN topology_nodes tn ON f.id = tn.file_id
ORDER BY fs.epistemic_score DESC
LIMIT 50;

-- SSOT lineage chain
CREATE VIEW IF NOT EXISTS v_ssot_lineage AS
SELECT 
  f.path,
  f.dcrp_role,
  COUNT(s.id) as ssot_signals,
  fs.lineage_depth
FROM files f
LEFT JOIN signals s ON f.id = s.file_id AND s.category = 'ssot_marker'
LEFT JOIN file_scores fs ON f.id = fs.file_id
WHERE ssot_signals > 0 OR f.path LIKE '%.github/copilot-instructions.md'
GROUP BY f.id
ORDER BY fs.lineage_depth ASC, ssot_signals DESC;

-- Orphaned files (potential deletion candidates)
CREATE VIEW IF NOT EXISTS v_orphans AS
SELECT 
  f.path,
  f.size_bytes,
  f.dcrp_spectral_freq,
  f.dcrp_role
FROM files f
JOIN topology_nodes tn ON f.id = tn.file_id
WHERE tn.is_orphan = 1
ORDER BY f.size_bytes DESC;

-- Hub files (critical dependencies)
CREATE VIEW IF NOT EXISTS v_hubs AS
SELECT 
  f.path,
  f.dcrp_essence,
  tn.in_degree,
  tn.out_degree,
  tn.total_degree
FROM files f
JOIN topology_nodes tn ON f.id = tn.file_id
WHERE tn.is_hub = 1
ORDER BY tn.total_degree DESC;

-- =============================================================================
-- TRIGGERS: Automatic Metric Updates
-- =============================================================================

-- Update topology when dependencies change
CREATE TRIGGER IF NOT EXISTS trg_update_topology
AFTER INSERT ON dependencies
BEGIN
  UPDATE topology_nodes 
  SET out_degree = out_degree + 1,
      total_degree = in_degree + out_degree + 1
  WHERE file_id = NEW.source_file_id;
  
  UPDATE topology_nodes 
  SET in_degree = in_degree + 1,
      total_degree = in_degree + out_degree + 1
  WHERE file_id = NEW.target_file_id;
END;

-- =============================================================================
-- FUNCTIONS: Query Helpers (via application layer)
-- =============================================================================

-- Note: SQLite doesn't support UDFs directly in schema.
-- These queries would be implemented in Python scanner:
--
-- 1. compute_signal_density(file_id) -> REAL
-- 2. compute_centrality(file_id) -> REAL
-- 3. compute_governance_weight(file_id) -> REAL
-- 4. compute_lineage_depth(file_id, ssot_file_id) -> REAL
-- 5. detect_clusters() -> void (populates topology_clusters)

-- =============================================================================
-- INTEGRITY CONSTRAINTS
-- =============================================================================

-- Ensure SSOT hash is recorded
CREATE TRIGGER IF NOT EXISTS trg_enforce_ssot
BEFORE INSERT ON files
WHEN NEW.path = '.github/copilot-instructions.md'
BEGIN
  SELECT RAISE(ABORT, 'SSOT file must have sha256 recorded in metadata')
  WHERE NOT EXISTS (
    SELECT 1 FROM metadata WHERE key = 'ssot_sha256'
  );
END;

-- Prevent duplicate signal extraction
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_signal 
  ON signals(file_id, category, line_number, snippet);

-- =============================================================================
-- VACUUM & ANALYZE
-- =============================================================================

-- After bulk load, run:
-- VACUUM;
-- ANALYZE;
