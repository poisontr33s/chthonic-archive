#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: run_queries.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
run_queries.py — Script logic for run_queries.py.

@SID:           TOOL_RUN_QUERIES_V1
@Shabti:        CLI Script
@Purpose:       Script logic for run_queries.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3
import json

db = sqlite3.connect(r"C:\Users\erdno\chthonic-archive\scripts\test_epistemograph.sqlite")
cur = db.cursor()

print("=" * 80)
print("VALIDATION QUERY 1: Distribution by Spectral Frequency")
print("=" * 80)
result = cur.execute("""
SELECT dcrp_spectral_freq, COUNT(*) as count,
       GROUP_CONCAT(path, ', ') as sample_files
FROM files
GROUP BY dcrp_spectral_freq
ORDER BY count DESC
""").fetchall()

for row in result:
    freq, count, samples = row
    sample_list = samples.split(', ')[:3]  # First 3
    print(f"{freq:12s} | {count:3d} files | e.g., {', '.join(sample_list)}")

print("\n" + "=" * 80)
print("VALIDATION QUERY 2: Distribution by Architectural Role")
print("=" * 80)
result = cur.execute("""
SELECT dcrp_role, COUNT(*) as count
FROM files
GROUP BY dcrp_role
ORDER BY count DESC
""").fetchall()

for role, count in result:
    print(f"{role:40s} | {count:3d} files")

print("\n" + "=" * 80)
print("VALIDATION QUERY 3: Files with High Export Count (Hubs)")
print("=" * 80)
result = cur.execute("""
SELECT path, dcrp_spectral_freq, dcrp_role, dcrp_exports_count, dcrp_essence
FROM files
WHERE dcrp_exports_count > 0
ORDER BY dcrp_exports_count DESC
LIMIT 10
""").fetchall()

for path, freq, role, exports, essence in result:
    print(f"{path:60s} | {freq:8s} | {exports:3d} exports")
    print(f"  Role: {role}")
    print(f"  Essence: {essence[:80]}")
    print()

print("=" * 80)
print("VALIDATION QUERY 4: GOLD Documentation Files")
print("=" * 80)
result = cur.execute("""
SELECT path, dcrp_essence
FROM files
WHERE dcrp_spectral_freq = 'GOLD' AND dcrp_role LIKE '%DOCUMENTATION%'
ORDER BY dcrp_exports_count DESC
LIMIT 10
""").fetchall()

for path, essence in result:
    print(f"{path:60s}")
    print(f"  {essence[:100]}")
    print()

print("=" * 80)
print("VALIDATION QUERY 5: Schema Metadata")
print("=" * 80)
result = cur.execute("""
SELECT key, value FROM metadata ORDER BY key
""").fetchall()

for key, value in result:
    print(f"{key:20s} : {value}")

db.close()
