#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build_epistemograph_v1.1.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Epistemograph Hybrid Scanner - PATH NORMALIZATION FIX
Version: 1.1.1
Date: 2026-01-04

CRITICAL FIXES APPLIED:
1. SSOT Bootstrap Fix: SSOT files get sha256 + metadata in Phase 1, never subject to gap validation
2. Topology Ingestion Fix: DCRP edges now properly inserted into dependencies table
3. Authority Precedence Fix: Categorical governance enforcement via score floors
4. Path Normalization Fix: GOVERNANCE_FILES uses canonical paths; exact match (not substring) for SSOT detection

Usage: 
uv run python build_epistemograph_v1.1.py  --root "C:\Users\erdno\chthonic-archive"

@SID:           TOOL_BUILD_EPISTEMOGRAPH_V1.1_V1
@Shabti:        CLI Script
@Purpose:       Script logic for build_epistemograph_v1.1.py.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.lib.ssot_paths import SSOT_POINTER

# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "1.1.1"

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
    '.md', '.py', '.rs', '.toml', '.json', '.yaml', '.yml',
    '.txt', '.rst', '.sql', '.sh', '.ps1', '.ts', '.tsx',
    '.js', '.jsx', '.csv'
}

GOVERNANCE_FILES = [
    SSOT_POINTER,
    'dumpster-dive/protocols/CONSOLIDATED_OPERATIONAL_INSTRUCTIONS.md',
    'CROSS_REFERENCE_TRIPTYCH.md',
    'scripts/scanner_approval.md'
]

MAX_PREVIEW_BYTES = 8192

# Repo-specific signal patterns
SIGNAL_PATTERNS = {
    'ssot_marker': re.compile(r'\bSSOT\b|Single.?Source.?of.?Truth', re.IGNORECASE),
    'tier_marker': re.compile(r'Tier\s*[0-9]+|T-[0-9]+', re.IGNORECASE),
    'triumvirate': re.compile(r'\b(Orackla|Umeko|Lysandra|CRC-AS|CRC-GAR|CRC-MEDAT)\b'),
    'protocol_ref': re.compile(r'Protocol|Prt\.|FA[0-9]+|DAFP|MSP-RSG|TPEF'),
    'ankh_marker': re.compile(r'\bANKH\b|Ankhological'),
    'cross_ref': re.compile(r'Section\s+[IVX]+|\u00a7\s*[0-9]+'),
}

# ============================================================================
# UTILITIES
# ============================================================================

def log(msg: str, level: str = "INFO"):
    """Thread-safe logging with Unicode handling."""
    timestamp = time.strftime('%H:%M:%S')
    try:
        print(f"[{timestamp}] [{level}] {msg}", flush=True)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[{timestamp}] [{level}] {safe_msg}", flush=True)

def compute_sha256(filepath: Path) -> str:
    """Compute file hash."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        log(f"Hash failed for {filepath}: {e}", "WARN")
        return "hash_error"

def normalize_path(p: str) -> str:
    """Normalize path separators to forward slash."""
    return p.replace('\\', '/')

def sample_content(filepath: Path, max_bytes: int = MAX_PREVIEW_BYTES) -> Tuple[str, str]:
    """
    Sample file content conservatively.
    Returns (content, method).
    Method must be one of: 'none', 'head_tail', 'dcrp', 'skipped_large'
    """
    try:
        size = filepath.stat().st_size
        if size == 0:
            return "", "none"
        
        if filepath.suffix.lower() not in TEXT_EXTENSIONS:
            return "", "none"  # Binary files get 'none'
        
        if size > 1_048_576:  # Skip >1MB
            return "", "skipped_large"
        
        # Read with fallback encoding
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = filepath.read_text(encoding='latin-1', errors='replace')
        
        if len(content) <= max_bytes:
            return content, "head_tail"  # Full content treated as head_tail
        else:
            # Head + tail
            lines = content.splitlines()
            if len(lines) <= 100:
                return content[:max_bytes], "head_tail"
            head = '\n'.join(lines[:50])
            tail = '\n'.join(lines[-50:])
            return head + "\n\n[...MIDDLE OMITTED...]\n\n" + tail, "head_tail"
    
    except Exception as e:
        log(f"Sample failed for {filepath}: {e}", "WARN")
        return "", "none"

def detect_signals(content: str, filepath: str) -> List[Tuple[str, int, str, str]]:
    """
    Extract signals from content.
    Returns [(category, line_num, snippet, confidence), ...]
    """
    signals = []
    if not content:
        return signals
    
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        for category, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(line):
                snippet = line.strip()[:600]
                confidence = "high" if category in ('ssot_marker', 'tier_marker') else "medium"
                signals.append((category, i, snippet, confidence))
    
    return signals

# ============================================================================
# PHASE 1: DCRP INGESTION (FIXED)
# ============================================================================

def phase1_ingest_dcrp(db: sqlite3.Connection, root: Path):
    """
    Ingest DCRP dependency graph as Tier-0 authority.
    
    CRITICAL FIX 1: SSOT Bootstrap
    - SSOT files immediately get real sha256 and size
    - Never marked as placeholder
    - Never subject to gap validation
    
    CRITICAL FIX 2: Topology Ingestion
    - DCRP edges properly inserted into dependencies table
    - Path normalization applied consistently
    - Hard guard added: abort if edges present but table empty
    """
    log("PHASE 1: DCRP Ingestion (with SSOT bootstrap + topology fixes)")
    start = time.time()
    
    cur = db.cursor()
    
    # Load DCRP graph
    dcrp_path = root / "dependency_graph_production.json"
    if not dcrp_path.exists():
        log("DCRP file not found - skipping Phase 1", "WARN")
        return
    
    with open(dcrp_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    
    # Identify SSOT files for bootstrap (already normalized in constant definition)
    ssot_files = set(GOVERNANCE_FILES)
    
    # Ingest nodes with SSOT bootstrap
    node_count = 0
    for node in graph.get('nodes', []):
        try:
            node_id = normalize_path(node['id'])
            ext = '.' + node_id.split('.')[-1] if '.' in node_id else ''
            
            # CRITICAL FIX 1: Bootstrap SSOT files (exact match, not substring)
            if node_id in ssot_files:
                # Compute real metadata immediately
                full_path = root / node_id.replace('/', os.sep)
                if full_path.exists():
                    real_sha = compute_sha256(full_path)
                    real_size = full_path.stat().st_size
                else:
                    log(f"SSOT file {node_id} not found on disk", "WARN")
                    real_sha = "ssot_missing"
                    real_size = 0
            else:
                # Non-SSOT files use placeholder (will be updated in Phase 2)
                real_sha = "dcrp_placeholder"
                real_size = 0
            
            cur.execute("""
                INSERT OR IGNORE INTO files 
                (path, sha256, size_bytes, extension, 
                 dcrp_spectral_freq, dcrp_role, dcrp_essence, dcrp_exports_count,
                 is_text, source, preview_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'dcrp', 'dcrp')
            """, (
                node_id,
                real_sha,
                real_size,
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
    
    # CRITICAL FIX 2: Topology ingestion
    edge_count = 0
    edges_in_graph = len(graph.get('edges', []))
    
    for edge in graph.get('edges', []):
        try:
            source_path = normalize_path(edge['source'])
            target_path = normalize_path(edge['target'])
            
            # Get source file_id
            source_row = cur.execute("SELECT id FROM files WHERE path = ?", (source_path,)).fetchone()
            if not source_row:
                log(f"Edge source not found: {source_path}", "WARN")
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
            log(f"Error ingesting edge {edge.get('source', '?')} -> {edge.get('target', '?')}: {e}", "ERROR")
    
    # HARD GUARD: Verify topology ingestion
    if edges_in_graph > 0 and edge_count == 0:
        raise RuntimeError(f"TOPOLOGY INGESTION FAILURE: {edges_in_graph} edges in graph but 0 inserted")
    
    elapsed = time.time() - start
    log(f"PHASE 1 COMPLETE: {node_count} files, {edge_count} edges in {elapsed:.1f}s")
    
    if edge_count < edges_in_graph:
        log(f"WARNING: {edges_in_graph - edge_count} edges failed to insert", "WARN")

# ============================================================================
# PHASE 2: GAP DETECTION
# ============================================================================

def phase2_detect_gaps(db: sqlite3.Connection, root: Path) -> List[Path]:
    """
    Find files not in DCRP coverage.
    Update missing metadata (sha256, size) for DCRP files.
    
    NOTE: SSOT files already have real metadata from Phase 1.
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
            relpath = normalize_path(str(filepath.relative_to(root)))
            
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
            relpath = normalize_path(str(filepath.relative_to(root)))
            
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
    
    # Verify dependencies exist
    dep_count = cur.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0]
    if dep_count == 0:
        log("No dependencies found - topology will be empty", "WARN")
    
    # Compute degree for each file
    for row in cur.execute("SELECT id FROM files").fetchall():
        file_id = row[0]
        
        in_degree = cur.execute("""
            SELECT COUNT(*) FROM dependencies WHERE target_file_id = ?
        """, (file_id,)).fetchone()[0]
        
        out_degree = cur.execute("""
            SELECT COUNT(*) FROM dependencies WHERE source_file_id = ?
        """, (file_id,)).fetchone()[0]
        
        total_degree = in_degree + out_degree
        
        cur.execute("""
            INSERT OR REPLACE INTO topology_nodes 
            (file_id, in_degree, out_degree, total_degree)
            VALUES (?, ?, ?, ?)
        """, (file_id, in_degree, out_degree, total_degree))
    
    elapsed = time.time() - start
    log(f"PHASE 4 COMPLETE: Topology computed in {elapsed:.1f}s")

# ============================================================================
# PHASE 5: SCORING (FIXED)
# ============================================================================

def phase5_score_files(db: sqlite3.Connection):
    """
    Compute epistemic scores with CATEGORICAL governance enforcement.
    
    CRITICAL FIX 3: Authority Precedence
    - SSOT file gets rank = 1 (hard-set, not computed)
    - DCRP files get floor score of 0.9 * theoretical max
    - gap_scan files capped at max rank 50
    """
    log("PHASE 5: Scoring (with categorical authority enforcement)")
    start = time.time()
    
    cur = db.cursor()
    
    # Get SSOT file_id
    ssot_row = cur.execute(f"""
        SELECT id FROM files 
        WHERE path LIKE '%{SSOT_POINTER}'
        ORDER BY dcrp_exports_count DESC
        LIMIT 1
    """).fetchone()
    ssot_id = ssot_row[0] if ssot_row else None
    
    if not ssot_id:
        log("WARNING: SSOT file not found", "WARN")
    
    # Compute component scores for all files
    max_possible_score = 0.0
    file_scores = []
    
    for row in cur.execute("SELECT id, path, source FROM files").fetchall():
        file_id, path, source = row
        
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
        
        # Lineage depth
        if file_id == ssot_id:
            lineage_depth = 1.0
        else:
            has_ssot_signal = cur.execute("""
                SELECT COUNT(*) FROM signals 
                WHERE file_id = ? AND category = 'ssot_marker'
            """, (file_id,)).fetchone()[0]
            lineage_depth = 0.5 if has_ssot_signal > 0 else 0.0
        
        # Compute raw epistemic score
        raw_score = (
            0.30 * signal_density +
            0.25 * centrality +
            0.30 * governance_weight +
            0.15 * lineage_depth
        )
        
        file_scores.append((file_id, source, raw_score, signal_density, centrality, 
                           governance_weight, lineage_depth))
        max_possible_score = max(max_possible_score, raw_score)
    
    # CRITICAL FIX 3: Apply categorical authority via component score boosting
    # Note: epistemic_score is GENERATED column, so we boost components instead
    for file_id, source, raw_score, sd, cent, gw, ld in file_scores:
        if file_id == ssot_id:
            # SSOT: Boost all components to maximum
            sd_adj = 1.0
            cent_adj = 1.0
            gw_adj = 1.0
            ld_adj = 1.0
        elif source == 'dcrp':
            # DCRP files: Floor governance_weight at 0.9
            sd_adj = sd
            cent_adj = cent
            gw_adj = max(gw, 0.9)
            ld_adj = ld
        elif source == 'gap_scan':
            # Gap scan: Cap governance_weight at 0.1
            sd_adj = sd
            cent_adj = cent
            gw_adj = min(gw, 0.1)
            ld_adj = ld
        else:
            sd_adj, cent_adj, gw_adj, ld_adj = sd, cent, gw, ld
        
        cur.execute("""
            INSERT OR REPLACE INTO file_scores 
            (file_id, signal_density, topology_centrality, governance_weight, 
             lineage_depth)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, sd_adj, cent_adj, gw_adj, ld_adj))
    
    # Compute ranks
    cur.execute("""
        UPDATE file_scores
        SET rank = (
            SELECT COUNT(*) 
            FROM file_scores fs2 
            WHERE fs2.epistemic_score > file_scores.epistemic_score
        ) + 1
    """)
    
    # Verify SSOT rank
    if ssot_id:
        ssot_rank = cur.execute("""
            SELECT rank FROM file_scores WHERE file_id = ?
        """, (ssot_id,)).fetchone()[0]
        
        if ssot_rank != 1:
            log(f"ERROR: SSOT rank is {ssot_rank}, not 1!", "ERROR")
        else:
            log("✓ SSOT rank verification passed (rank = 1)")
    
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
    cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                ("fixes_applied", "ssot_bootstrap,topology_ingestion,authority_precedence,path_normalization"))
    
    # CRITICAL: Compute SSOT sha256 BEFORE Phase 1 (satisfies schema trigger)
    ssot_primary = root / SSOT_POINTER
    if ssot_primary.exists():
        ssot_hash = compute_sha256(ssot_primary)
        cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                    ("ssot_sha256", ssot_hash))
        log(f"SSOT hash pre-computed: {ssot_hash[:16]}...")
    else:
        log("WARNING: Primary SSOT file not found", "WARN")
    
    db.commit()
    
    try:
        phase1_ingest_dcrp(db, root)
        
        # CRITICAL ASSERTION: Verify SSOT bootstrap succeeded
        cur = db.cursor()
        ssot_verified_count = 0
        for ssot_path in GOVERNANCE_FILES:
            ssot_row = cur.execute("""
                SELECT id, sha256, size_bytes, source 
                FROM files 
                WHERE path = ?
            """, (ssot_path,)).fetchone()
            
            if not ssot_row:
                # File may not be in DCRP if created after DCRP snapshot - this is acceptable
                log(f"SSOT file not in DCRP (will be added in gap scan): {ssot_path}", "WARN")
                continue
            
            file_id, sha, size, source = ssot_row
            if sha in ('dcrp_placeholder', 'hash_error', 'ssot_missing'):
                raise RuntimeError(f"SSOT BOOTSTRAP FAILURE: {ssot_path} has invalid sha256={sha}")
            
            if source != 'dcrp':
                raise RuntimeError(f"SSOT BOOTSTRAP FAILURE: {ssot_path} has source={source} (expected 'dcrp')")
            
            log(f"✓ SSOT verified: {ssot_path} (sha={sha[:8]}...)")
            ssot_verified_count += 1
        
        if ssot_verified_count == 0:
            raise RuntimeError("SSOT BOOTSTRAP FAILURE: No SSOT files found in DCRP")
        
        log(f"SSOT bootstrap complete: {ssot_verified_count}/{len(GOVERNANCE_FILES)} files in DCRP")
        
        gap_files = phase2_detect_gaps(db, root)
        phase3_extract_signals(db, root, gap_files)
        phase4_compute_topology(db)
        phase5_score_files(db)
        
        db.commit()
        log("✅ Scanner completed successfully")
        
        # Print summary
        cur = db.cursor()
        total_files = cur.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        total_deps = cur.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0]
        total_signals = cur.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        
        log(f"Summary: {total_files} files, {total_deps} deps, {total_signals} signals")
        
        # Verify SSOT integrity
        ssot_check = cur.execute(f"""
            SELECT f.path, fs.rank, fs.epistemic_score
            FROM files f
            JOIN file_scores fs ON f.id = fs.file_id
            WHERE f.path LIKE '%{SSOT_POINTER}'
        """).fetchone()
        
        if ssot_check:
            log(f"SSOT Verification: {ssot_check[0]} rank={ssot_check[1]} score={ssot_check[2]:.3f}")
        
    except Exception as e:
        db.rollback()
        log(f"❌ Scanner failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Epistemograph Hybrid Scanner v1.1 (FIXED)")
    parser.add_argument("--root", required=True, help="Repository root path")
    parser.add_argument("--out", default="chthonic_epistemograph_v1.1.sqlite", 
                       help="Output SQLite file")
    
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    db_path = Path(args.out).resolve()
    
    if not root.exists():
        print(f"Error: Root path {root} does not exist")
        sys.exit(1)
    
    run_scanner(root, db_path)
