#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build_epistemograph.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Epistemograph Hybrid Scanner
Version: 1.0.0
Date: 2026-01-04

Implements approved scanner constraints from scanner_approval.md.
Respects DCRP authority, fills gaps, extracts signals, computes topology.

Usage:
    uv run python build_epistemograph.py --root "C:\Users\erdno\chthonic-archive"

@SID:           TOOL_BUILD_EPISTEMOGRAPH_V1
@Shabti:        CLI Script
@Purpose:       Script logic for build_epistemograph.py.
"""

import os
import sys
import json
import sqlite3
import hashlib
import re
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONSTANTS (from approval document)
# ============================================================================

VERSION = "1.0.0"

PROTECTED_FIELDS = [
    'dcrp_spectral_freq',
    'dcrp_role', 
    'dcrp_essence',
    'dcrp_exports_count'
]

SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp',
    '.zip', '.7z', '.gz', '.tar',
    '.exe', '.dll', '.so', '.bin',
    '.db', '.sqlite',
    '.pptx', '.docx', '.pdf',
    '.mp4', '.mov', '.mkv'
}

SKIP_DIRECTORIES = {
    '.git', 'node_modules', '__pycache__',
    'dist', 'build', 'target', '.venv'
}

TEXT_EXTENSIONS = {
    '.md', '.py', '.json', '.yaml', '.yml', '.txt', '.rst',
    '.toml', '.csv', '.rs', '.java', '.ts', '.tsx', '.js', '.jsx'
}

REPO_SPECIFIC = {
    'ssot_marker', 'tier_marker', 'triumvirate',
    'protocol_ref', 'ankh_marker'
}

SIGNAL_PATTERNS = {
    'ssot_marker': re.compile(r'\b(SSOT|Codex-Brahmanica-Perfectus|FA[¹²³⁴⁵])\b'),
    'tier_marker': re.compile(r'\b(Tier\s*[0-9.]+|T-[0-9]+)\b'),
    'triumvirate': re.compile(r'\b(CRC-AS|CRC-GAR|CRC-MEDAT|Orackla|Umeko|Lysandra)\b'),
    'protocol_ref': re.compile(r'\b(DCRP|TPEF|T³-MΨ|MMPS|MSP-RSG)\b'),
    'ankh_marker': re.compile(r'\b(ANKH|Ankhological|⚓)\b'),
    'contract': re.compile(r'\b(MUST|SHALL|REQUIRED|MANDATORY|FORBIDDEN)\b', re.I),
    'agent': re.compile(r'\b(TODO|FIXME|HACK|NOTE|WARNING|DEPRECATED)\b', re.I),
}

GOVERNANCE_FILES = {
    '.github/copilot-instructions.md',
    'ANKHOLOGY.md',
    'ANKH_README.md',
}

MAX_PREVIEW_BYTES = 8192
MAX_TEXT_SIZE = 1_048_576  # 1MB

# ============================================================================
# UTILITIES
# ============================================================================

def log(msg: str, level: str = "INFO"):
    """Simple logging."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {msg}")

def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of file."""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        log(f"Hash error for {path}: {e}", "WARN")
        return "error_" + str(hash(str(path)))

def sample_content(path: Path, max_bytes: int = MAX_PREVIEW_BYTES) -> Tuple[str, str]:
    """
    Conservative content sampling per approval constraints.
    
    Returns: (content_text, sample_method)
    Schema-compliant methods: 'none', 'head_tail', 'dcrp', 'skipped_large'
    """
    try:
        size = path.stat().st_size
        
        if size == 0:
            return "", "none"
        
        if size > MAX_TEXT_SIZE:
            # Check allowlist for governance files
            if str(path).replace('\\', '/') not in GOVERNANCE_FILES:
                return "[SKIPPED_LARGE]", "skipped_large"
        
        if size <= max_bytes:
            with open(path, 'rb') as f:
                data = f.read()
            try:
                text = data.decode('utf-8')
                return text, "head_tail"  # Changed from "full" to "head_tail"
            except:
                text = data.decode('latin-1', errors='replace')
                return text, "head_tail"  # Changed from "full_fallback"
        
        # Head + tail
        with open(path, 'rb') as f:
            head = f.read(4096)
            f.seek(max(0, size - 4096))
            tail = f.read(4096)
        
        head_text = head.decode('utf-8', errors='replace')
        tail_text = tail.decode('utf-8', errors='replace')
        
        return f"{head_text}\n\n--TAIL--\n\n{tail_text}", "head_tail"
        
    except Exception as e:
        log(f"Content read error for {path}: {e}", "WARN")
        return f"[ERROR: {e}]", "none"  # Changed from "error"

def detect_signals(text: str, file_path: str) -> List[Tuple[str, int, str, float]]:
    """
    Extract epistemic signals from text.
    
    Returns: [(category, line_num, snippet, confidence), ...]
    """
    if not text or text.startswith("["):
        return []
    
    signals = []
    for i, line in enumerate(text.splitlines(), 1):
        for category, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(line):
                confidence = 1.0 if category in REPO_SPECIFIC else 0.8
                snippet = line.strip()[:600]
                signals.append((category, i, snippet, confidence))
    
    return signals

# ============================================================================
# PHASE 1: DCRP INGESTION
# ============================================================================

def phase1_ingest_dcrp(db: sqlite3.Connection, root: Path):
    """
    Load dependency_graph_production.json as authoritative source.
    Mark all data with source='dcrp'.
    """
    log("PHASE 1: DCRP Ingestion")
    start = time.time()
    
    cur = db.cursor()
    
    # Load graph
    graph_path = root / "dependency_graph_production.json"
    if not graph_path.exists():
        log("dependency_graph_production.json not found - skipping DCRP ingestion", "WARN")
        return
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    
    # Record provenance
    cur.execute("""
        INSERT INTO artifact_provenance 
        (artifact_name, artifact_path, sha256, size_bytes, authority_level)
        VALUES (?, ?, ?, ?, 'primary')
    """, (
        'dependency_graph_production.json',
        str(graph_path.relative_to(root)),
        compute_sha256(graph_path),
        graph_path.stat().st_size
    ))
    
    # Ingest nodes
    node_count = 0
    for node in graph.get('nodes', []):
        try:
            node_id = node['id']
            ext = '.' + node_id.split('.')[-1] if '.' in node_id else ''
            
            cur.execute("""
                INSERT OR IGNORE INTO files 
                (path, sha256, size_bytes, extension, 
                 dcrp_spectral_freq, dcrp_role, dcrp_essence, dcrp_exports_count,
                 is_text, source, preview_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'dcrp', 'dcrp')
            """, (
                node_id,
                'dcrp_placeholder',  # Will update in gap phase if needed
                0,  # Will update in gap phase
                ext,
                node.get('spectral_freq', 'UNKNOWN'),
                node.get('role', 'UNKNOWN'),
                node.get('essence', 'Unknown'),
                node.get('exports_count', 0),
                1 if ext in TEXT_EXTENSIONS else 0
            ))
            node_count += 1
        except Exception as e:
            log(f"Error ingesting node {node.get('id', 'unknown')}: {e}", "ERROR")
    
    # Ingest edges
    edge_count = 0
    for edge in graph.get('links', []):
        try:
            source_path = edge['source']
            target_path = edge['target']
            
            # Get source file_id
            source_row = cur.execute("SELECT id FROM files WHERE path = ?", (source_path,)).fetchone()
            if not source_row:
                continue
            source_id = source_row[0]
            
            # Get target file_id (may be None if external)
            target_row = cur.execute("SELECT id FROM files WHERE path = ?", (target_path,)).fetchone()
            target_id = target_row[0] if target_row else None
            
            cur.execute("""
                INSERT OR IGNORE INTO dependencies 
                (source_file_id, target_path, target_file_id, dep_type, confidence, source)
                VALUES (?, ?, ?, 'reference', 'high', 'dcrp')
            """, (source_id, target_path, target_id))
            edge_count += 1
        except Exception as e:
            log(f"Error ingesting edge: {e}", "ERROR")
    
    # db.commit() removed - single transaction
    
    elapsed = time.time() - start
    log(f"PHASE 1 COMPLETE: {node_count} files, {edge_count} edges in {elapsed:.1f}s")

# ============================================================================
# PHASE 2: GAP DETECTION
# ============================================================================

def phase2_detect_gaps(db: sqlite3.Connection, root: Path) -> List[Path]:
    """
    Find files not in DCRP coverage.
    Update missing metadata (sha256, size) for DCRP files.
    """
    log("PHASE 2: Gap Detection")
    start = time.time()
    
    cur = db.cursor()
    
    # Get all files in database
    db_files = set(row[0] for row in cur.execute("SELECT path FROM files").fetchall())
    
    # Walk filesystem
    gap_files = []
    updated_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRECTORIES]
        
        for filename in filenames:
            filepath = Path(dirpath) / filename
            relpath = str(filepath.relative_to(root)).replace('\\', '/')
            
            # Skip excluded extensions
            if filepath.suffix.lower() in SKIP_EXTENSIONS:
                continue
            
            if relpath not in db_files:
                # New file not in DCRP
                gap_files.append(filepath)
            else:
                # File in DCRP - update metadata if placeholder
                row = cur.execute("""
                    SELECT id, sha256, size_bytes 
                    FROM files 
                    WHERE path = ? AND source = 'dcrp'
                """, (relpath,)).fetchone()
                
                if row and row[1] == 'dcrp_placeholder':
                    file_id, _, _ = row
                    cur.execute("""
                        UPDATE files 
                        SET sha256 = ?, size_bytes = ?
                        WHERE id = ?
                    """, (compute_sha256(filepath), filepath.stat().st_size, file_id))
                    updated_count += 1
    
    # db.commit() removed - single transaction
    
    elapsed = time.time() - start
    log(f"PHASE 2 COMPLETE: {len(gap_files)} gaps, {updated_count} updated in {elapsed:.1f}s")
    
    return gap_files

# ============================================================================
# PHASE 3: SIGNAL EXTRACTION
# ============================================================================

def phase3_extract_signals(db: sqlite3.Connection, root: Path, gap_files: List[Path]):
    """
    Extract repo-specific signals from:
    1. SSOT and governance files
    2. Gap files
    """
    log("PHASE 3: Signal Extraction")
    start = time.time()
    
    cur = db.cursor()
    
    # Get governance files
    gov_files = []
    for gov_path in GOVERNANCE_FILES:
        full_path = root / gov_path.replace('/', os.sep)
        if full_path.exists():
            gov_files.append(full_path)
    
    # Combine governance + gaps
    files_to_scan = set(gov_files + gap_files)
    
    total_signals = 0
    for filepath in files_to_scan:
        try:
            relpath = str(filepath.relative_to(root)).replace('\\', '/')
            
            # Get or create file_id
            row = cur.execute("SELECT id FROM files WHERE path = ?", (relpath,)).fetchone()
            if row:
                file_id = row[0]
            else:
                # Insert gap file
                ext = filepath.suffix.lower()
                cur.execute("""
                    INSERT INTO files 
                    (path, sha256, size_bytes, extension, is_text, source, preview_method)
                    VALUES (?, ?, ?, ?, ?, 'gap_scan', 'none')
                """, (relpath, compute_sha256(filepath), filepath.stat().st_size, 
                      ext, 1 if ext in TEXT_EXTENSIONS else 0))
                file_id = cur.lastrowid
            
            # Sample content
            content, method = sample_content(filepath)
            
            # Update preview
            cur.execute("""
                UPDATE files 
                SET content_preview = ?, preview_method = ?
                WHERE id = ?
            """, (content[:MAX_PREVIEW_BYTES], method, file_id))
            
            # Extract signals
            signals = detect_signals(content, relpath)
            for category, line_num, snippet, confidence in signals:
                cur.execute("""
                    INSERT OR IGNORE INTO signals 
                    (file_id, category, line_number, snippet, detected_by, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (file_id, category, line_num, snippet, f'scanner_v{VERSION}', confidence))
                total_signals += 1
        
        except Exception as e:
            log(f"Error processing {filepath}: {e}", "ERROR")
    
    # db.commit() removed - single transaction
    
    elapsed = time.time() - start
    log(f"PHASE 3 COMPLETE: {total_signals} signals from {len(files_to_scan)} files in {elapsed:.1f}s")

# ============================================================================
# PHASE 4: TOPOLOGY COMPUTATION
# ============================================================================

def phase4_compute_topology(db: sqlite3.Connection):
    """
    Compute graph metrics from dependencies table.
    """
    log("PHASE 4: Topology Computation")
    start = time.time()
    
    cur = db.cursor()
    
    # Initialize topology_nodes
    cur.execute("""
        INSERT OR IGNORE INTO topology_nodes (file_id)
        SELECT id FROM files
    """)
    
    # Compute in_degree
    cur.execute("""
        UPDATE topology_nodes
        SET in_degree = (
            SELECT COUNT(*) 
            FROM dependencies 
            WHERE target_file_id = topology_nodes.file_id
        )
    """)
    
    # Compute out_degree
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
    total_nodes = cur.execute("SELECT COUNT(*) FROM topology_nodes").fetchone()[0]
    if total_nodes > 0:
        threshold_row = cur.execute("""
            SELECT total_degree 
            FROM topology_nodes 
            ORDER BY total_degree DESC 
            LIMIT 1 OFFSET ?
        """, (total_nodes // 10,)).fetchone()
        
        if threshold_row:
            threshold = threshold_row[0]
            cur.execute("""
                UPDATE topology_nodes
                SET is_hub = 1
                WHERE total_degree >= ?
            """, (threshold,))
    
    # Mark orphans
    cur.execute("""
        UPDATE topology_nodes
        SET is_orphan = 1
        WHERE total_degree = 0
    """)
    
    # db.commit() removed - single transaction
    
    hub_count = cur.execute("SELECT COUNT(*) FROM topology_nodes WHERE is_hub = 1").fetchone()[0]
    orphan_count = cur.execute("SELECT COUNT(*) FROM topology_nodes WHERE is_orphan = 1").fetchone()[0]
    
    elapsed = time.time() - start
    log(f"PHASE 4 COMPLETE: {hub_count} hubs, {orphan_count} orphans in {elapsed:.1f}s")

# ============================================================================
# PHASE 5: SCORING
# ============================================================================

def phase5_score_files(db: sqlite3.Connection):
    """
    Compute epistemic scores per approval weights.
    """
    log("PHASE 5: Scoring")
    start = time.time()
    
    cur = db.cursor()
    
    # Get SSOT file_id for lineage computation
    ssot_row = cur.execute("""
        SELECT id FROM files 
        WHERE path LIKE '%.github/copilot-instructions.md'
        ORDER BY dcrp_exports_count DESC
        LIMIT 1
    """).fetchone()
    ssot_id = ssot_row[0] if ssot_row else None
    
    # For each file, compute score components
    for row in cur.execute("SELECT id, path FROM files").fetchall():
        file_id, path = row
        
        # Signal density
        signal_count = cur.execute("""
            SELECT COUNT(*) FROM signals 
            WHERE file_id = ? AND category IN (?, ?, ?, ?, ?)
        """, (file_id, 'ssot_marker', 'tier_marker', 'triumvirate', 
              'protocol_ref', 'ankh_marker')).fetchone()[0]
        
        line_count = cur.execute("""
            SELECT content_preview FROM files WHERE id = ?
        """, (file_id,)).fetchone()
        
        if line_count and line_count[0]:
            lines = len(line_count[0].splitlines())
            signal_density = signal_count / max(lines, 1) if lines > 0 else 0.0
        else:
            signal_density = 0.0
        
        # Topology centrality
        degree_row = cur.execute("""
            SELECT total_degree FROM topology_nodes WHERE file_id = ?
        """, (file_id,)).fetchone()
        
        if degree_row:
            max_degree = cur.execute("SELECT MAX(total_degree) FROM topology_nodes").fetchone()[0] or 1
            centrality = degree_row[0] / max(max_degree, 1)
        else:
            centrality = 0.0
        
        # Governance weight
        total_signals = cur.execute("""
            SELECT COUNT(*) FROM signals WHERE file_id = ?
        """, (file_id,)).fetchone()[0]
        
        if total_signals > 0:
            governance_weight = signal_count / total_signals
        else:
            governance_weight = 0.0
        
        # Lineage depth (simplified: 1.0 if SSOT, 0.5 if references SSOT, 0.0 otherwise)
        if file_id == ssot_id:
            lineage_depth = 1.0
        else:
            # Check if references SSOT
            has_ssot_signal = cur.execute("""
                SELECT COUNT(*) FROM signals 
                WHERE file_id = ? AND category = 'ssot_marker'
            """, (file_id,)).fetchone()[0]
            lineage_depth = 0.5 if has_ssot_signal > 0 else 0.0
        
        # Insert score
        cur.execute("""
            INSERT OR REPLACE INTO file_scores 
            (file_id, signal_density, topology_centrality, governance_weight, lineage_depth)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, signal_density, centrality, governance_weight, lineage_depth))
    
    # db.commit() removed - single transaction
    
    # Compute ranks
    cur.execute("""
        UPDATE file_scores
        SET rank = (
            SELECT COUNT(*) 
            FROM file_scores fs2 
            WHERE fs2.epistemic_score > file_scores.epistemic_score
        ) + 1
    """)
    
    # db.commit() removed - single transaction
    
    elapsed = time.time() - start
    log(f"PHASE 5 COMPLETE: Scores computed in {elapsed:.1f}s")

# ============================================================================
# MAIN SCANNER
# ============================================================================

def run_scanner(root: Path, db_path: Path):
    """Execute all scanner phases with transaction safety."""
    log(f"Starting epistemograph scanner v{VERSION}")
    log(f"Root: {root}")
    log(f"Output: {db_path}")
    
    # Initialize database with schema
    schema_path = root / "scripts" / "epistemograph_schema.sql"
    if not schema_path.exists():
        log("Schema file not found", "ERROR")
        return
    
    db = sqlite3.connect(str(db_path))
    cur = db.cursor()
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        cur.executescript(f.read())
    
    # Record metadata
    cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                ("scan_timestamp", time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                ("scanner_version", VERSION))
    cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                ("root_path", str(root)))
    db.commit()
    
    try:
        # Don't use explicit BEGIN - autocommit off by default
        
        phase1_ingest_dcrp(db, root)
        gap_files = phase2_detect_gaps(db, root)
        phase3_extract_signals(db, root, gap_files)
        phase4_compute_topology(db)
        phase5_score_files(db)
        
        db.commit()  # Single commit at end
        log("✅ Scanner completed successfully")
        
        # Print summary
        cur = db.cursor()
        total_files = cur.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        total_deps = cur.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0]
        total_signals = cur.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        
        log(f"Summary: {total_files} files, {total_deps} deps, {total_signals} signals")
        
    except Exception as e:
        db.rollback()
        log(f"❌ Scanner failed: {e}", "ERROR")
        raise
    finally:
        db.close()

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Epistemograph Hybrid Scanner")
    parser.add_argument("--root", required=True, help="Repository root path")
    parser.add_argument("--out", default="chthonic_epistemograph.sqlite", 
                       help="Output SQLite file")
    
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    db_path = Path(args.out).resolve()
    
    if not root.exists():
        print(f"Error: Root path {root} does not exist")
        sys.exit(1)
    
    run_scanner(root, db_path)
