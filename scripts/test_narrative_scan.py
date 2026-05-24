#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: test_narrative_scan.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: TEST_NARRATIVE_SCAN_V1
@Shabti: Utility Script
@Context: Test script for Narrative Scan logic
@Purpose:       Script logic for test_narrative_scan.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mas_mcp.logic.tools import mas_narrative_scan_logic
from scripts.lib.ssot_paths import resolve_ssot_paths

_SSOT = resolve_ssot_paths(PROJECT_ROOT)
SSOT_PATH = _SSOT.pointer

def test_narrative():
    print("--- Running Narrative Scan (Cultural Drift) ---")
    results = mas_narrative_scan_logic(".", PROJECT_ROOT, SSOT_PATH)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print(f"Drift Score: {results['drift_score']}")
    print(f"Vocabulary Coverage: {results['vocabulary_coverage']}")
    print(f"Used Terms: {results['used_terms_count']} / {results['lexicon_size']}")
    print("\nTop Terms in Code:")
    for term, count in results['top_terms']:
        print(f"  - {term}: {count}")
        
    print("\nCollisions:")
    if not results['collisions']:
        print("  None detected.")
    for c in results['collisions']:
        print(f"  ! {c['file']}: {c['entity']} (Expected {c['expected']}, Actual {c['actual']})")

if __name__ == "__main__":
    test_narrative()
