#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: test_ingest.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
test_ingest.py — Script logic for test_ingest.py.

@SID:           TOOL_TEST_INGEST_V1
@Shabti:        CLI Script
@Purpose:       Script logic for test_ingest.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json, sqlite3
from pathlib import Path

_HERE = Path(__file__).resolve().parent

db = sqlite3.connect(_HERE / "test_epistemograph.sqlite")
cur = db.cursor()

# Load dependency graph
with open(_HERE.parent / "dependency_graph_production.json", "r", encoding="utf-8") as f:
    graph = json.load(f)

# Insert provenance
cur.execute("""
INSERT INTO artifact_provenance (artifact_name, artifact_path, sha256, size_bytes, authority_level)
VALUES ('dependency_graph_production.json', 'dependency_graph_production.json',
        'placeholder_hash', 0, 'primary')
""")

# Sample first 100 nodes (for quick testing)
for node in graph['nodes'][:100]:
    try:
        cur.execute("""
        INSERT OR IGNORE INTO files
        (path, sha256, size_bytes, extension, dcrp_spectral_freq, dcrp_role, dcrp_essence,
         dcrp_exports_count, is_text, source, preview_method)
        VALUES (?, 'placeholder', 0, ?, ?, ?, ?, ?, 1, 'dcrp', 'dcrp')
        """, (
            node['id'],
            '.' + node['id'].split('.')[-1] if '.' in node['id'] else '',
            node.get('spectral_freq', 'UNKNOWN'),
            node.get('role', 'UNKNOWN'),
            node.get('essence', 'Unknown'),
            node.get('exports_count', 0)
        ))
    except Exception as e:
        print(f"Error inserting {node['id']}: {e}")

# Sample edges
for edge in graph.get('links', [])[:100]:
    try:
        source_id = cur.execute("SELECT id FROM files WHERE path = ?", (edge['source'],)).fetchone()
        target_id = cur.execute("SELECT id FROM files WHERE path = ?", (edge['target'],)).fetchone()

        if source_id:
            cur.execute("""
            INSERT OR IGNORE INTO dependencies
            (source_file_id, target_path, target_file_id, dep_type, confidence, source)
            VALUES (?, ?, ?, 'reference', 'high', 'dcrp')
            """, (source_id[0], edge['target'], target_id[0] if target_id else None))
    except Exception as e:
        print(f"Error inserting edge: {e}")

db.commit()
print(f"Inserted {cur.execute('SELECT COUNT(*) FROM files').fetchone()[0]} files")
print(f"Inserted {cur.execute('SELECT COUNT(*) FROM dependencies').fetchone()[0]} dependencies")
db.close()
