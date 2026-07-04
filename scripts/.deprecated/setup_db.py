#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: setup_db.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
setup_db.py — Script logic for setup_db.py.

@SID:           TOOL_SETUP_DB_V1
@Shabti:        CLI Script
@Purpose:       Script logic for setup_db.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent

db_path = _SCRIPTS_DIR / "test_epistemograph.sqlite"
schema_path = _SCRIPTS_DIR / "epistemograph_schema.sql"

# Create database
db = sqlite3.connect(db_path)
cur = db.cursor()

# Execute schema
with open(schema_path, 'r', encoding='utf-8') as f:
    schema_sql = f.read()
    cur.executescript(schema_sql)

db.commit()

# Verify tables
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("Tables created:")
for table in tables:
    print(f"  - {table[0]}")

db.close()
print("\nSchema initialized successfully")
