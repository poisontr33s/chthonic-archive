#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extract_curriculum.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Extract curriculum core from epistemograph v1.1.1
Ordered by epistemic seniority: authority tier > score > signal diversity

@SID:           TOOL_EXTRACT_CURRICULUM_V1
@Shabti:        CLI Script
@Purpose:       Extract curriculum core from epistemograph v1.1.1
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "chthonic_epistemograph_v1.1.1.sqlite"

def extract_curriculum(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check schema
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Available tables: {[t[0] for t in tables]}\n")

    # Simplified query using correct column names
    query = f"""
    SELECT
        f.path,
        f.dcrp_spectral_freq,
        f.dcrp_role,
        CASE
            WHEN f.path LIKE '.github%' THEN 'SSOT'
            WHEN f.source = 'dcrp' THEN 'DCRP'
            WHEN f.source = 'governance' THEN 'GOVERNANCE'
            ELSE 'GAP_SCAN'
        END as authority_tier,
        f.source,
        COALESCE(fs.epistemic_score, 0) as score,
        COUNT(DISTINCT s.category) as signal_types,
        f.dcrp_essence,
        f.size_bytes
    FROM files f
    LEFT JOIN file_scores fs ON f.id = fs.file_id
    LEFT JOIN signals s ON f.id = s.file_id
    WHERE f.is_text = 1
    GROUP BY f.id
    ORDER BY
        CASE
            WHEN f.path LIKE '.github%' THEN 1
            WHEN f.source = 'dcrp' THEN 2
            WHEN f.source = 'governance' THEN 3
            ELSE 4
        END,
        COALESCE(fs.epistemic_score, 0) DESC,
        signal_types DESC
    LIMIT {limit}
    """

    results = cur.execute(query).fetchall()
    columns = ['path', 'spectral_freq', 'role', 'authority_tier', 'source',
               'score', 'signal_types', 'essence', 'size_bytes']

    curriculum = []
    for i, row in enumerate(results, 1):
        entry = dict(zip(columns, row))
        entry['rank'] = i
        entry['why_this_exists'] = generate_rationale(entry)
        curriculum.append(entry)

    conn.close()
    return curriculum

def generate_rationale(entry):
    """Generate one-sentence rationale based on metadata"""
    tier = entry['authority_tier']
    role = entry['role'] or 'UNCLASSIFIED'
    freq = entry['spectral_freq'] or 'UNKNOWN'

    if tier == 'SSOT':
        return "Single Source of Truth - governance foundation"
    elif tier == 'DCRP':
        if role == 'DOCUMENTATION':
            return f"DCRP-validated documentation ({freq} frequency)"
        elif role == 'ARCHITECTURE':
            return f"DCRP-validated architectural component ({freq} frequency)"
        else:
            return f"DCRP-validated {role.lower()} artifact ({freq} frequency)"
    elif tier == 'GOVERNANCE':
        return "Post-DCRP governance artifact"
    else:
        return f"Gap-scan discovered {role.lower()} ({freq} frequency)"

if __name__ == "__main__":
    curriculum = extract_curriculum(limit=20)

    # Write JSON
    output_path = Path(__file__).parent.parent / "curriculum_core_v1.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '1.0.0',
            'source_db': 'chthonic_epistemograph_v1.1.1.sqlite',
            'extraction_date': '2026-01-04',
            'curriculum': curriculum
        }, f, indent=2)

    print(f"\n✓ Curriculum core extracted to: {output_path}")
    print(f"✓ Top {len(curriculum)} artifacts by epistemic seniority\n")

    # Preview
    print("Top 5 Preview:")
    for entry in curriculum[:5]:
        print(f"  {entry['rank']:2d}. [{entry['authority_tier']:10s}] {entry['path']}")
        print(f"      {entry['why_this_exists']}")
        print()
