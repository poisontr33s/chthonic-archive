#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: quick_validation.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════




import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

"""
@SID:           TOOL_QUICK_VALIDATION_V1
@Shabti:        CLI Script
@Purpose:       Quick validation queries for epistemograph v1.1
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.lib.ssot_paths import SSOT_POINTER

db_path = sys.argv[1] if len(sys.argv) > 1 else 'chthonic_epistemograph_v1.1.sqlite'
db = sqlite3.connect(db_path)
cur = db.cursor()

# Q1: SSOT rank
print('=== Q1: SSOT Rank ===')
ssot = cur.execute(f'''
SELECT f.path, fs.rank, fs.epistemic_score
FROM files f
LEFT JOIN file_scores fs ON f.id = fs.file_id
WHERE f.path LIKE '%{Path(SSOT_POINTER).name}'
''').fetchall()
for row in ssot:
    print(f'  {row[0]}: rank={row[1]}, score={row[2]}')

# Q2: Topology count
print('\n=== Q2: Dependencies ===')
deps = cur.execute('SELECT COUNT(*) FROM dependencies WHERE source = "dcrp"').fetchone()[0]
print(f'  DCRP edges: {deps}')

# Q3: Top 10 by source
print('\n=== Q3: Top 10 Sources ===')
top10 = cur.execute('''
SELECT f.source, COUNT(*) as cnt
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
WHERE fs.rank <= 10
GROUP BY f.source
''').fetchall()
for row in top10:
    print(f'  {row[0]}: {row[1]} files')

# Q4: Top 10 files
print('\n=== Q4: Top 10 Files ===')
topfiles = cur.execute('''
SELECT f.path, fs.rank, fs.epistemic_score, f.source
FROM files f
JOIN file_scores fs ON f.id = fs.file_id
ORDER BY fs.rank
LIMIT 10
''').fetchall()
for row in topfiles:
    print(f'  #{row[1]}: {row[0][:60]} (source={row[3]}, score={row[2]:.3f})')

db.close()
